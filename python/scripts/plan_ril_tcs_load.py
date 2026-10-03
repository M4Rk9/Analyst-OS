"""Prepare an offline RIL/TCS import plan; no credentials, network calls or --apply mode."""

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from analyst_os_ingestion.loader import _record_from_row, load_financial_csv
from analyst_os_ingestion.planning import (
    ReviewLedger,
    TargetSnapshot,
    build_catalog,
    build_load_plan,
    digest,
)
from scripts.validate_m2_batch2 import validate_batch

MAX_JSON_BYTES = 5 * 1024 * 1024


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def read_json(path: Path):
    if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("input must be a bounded local JSON file")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)


def load_catalog(repo: Path) -> dict:
    evidence = repo / "data/m2/ril-tcs"
    receipt, reconciliations = validate_batch(evidence / "batch2")
    if receipt != read_json(evidence / "batch2/validation_receipt.json"):
        raise ValueError("batch2 validation receipt mismatch")
    if reconciliations != read_json(evidence / "batch2/reconciliation_ledger.json"):
        raise ValueError("batch2 reconciliation ledger mismatch")
    observations = read_json(evidence / "batch1/observations.json")
    groups = {}
    for o in observations:
        group = groups.setdefault(
            (o["company_slug"], o["source_fiscal_year"], o["fiscal_year"]), {}
        )
        if o["metric_code"] in group:
            raise ValueError("duplicate P&L metric in source column")
        group[o["metric_code"]] = Decimal(o["raw_value"])
    for group in groups.values():
        if group["revenue"] + group["other_income"] != group["total_income"]:
            raise ValueError("P&L income identity mismatch")
    observations += read_json(evidence / "batch2/observations.json")
    definitions = read_json(evidence / "review/pnl_metric_definitions.json")
    for definition in read_json(evidence / "batch2/metric_registry.json"):
        if definition["metric_code"] in definitions:
            raise ValueError("duplicate metric definition")
        definitions[definition["metric_code"]] = definition
    catalog = build_catalog(
        observations,
        definitions,
        read_json(evidence / "batch1/source_manifest.json"),
        set(range(2022, 2027)),
    )
    csv_ids = set()
    candidate_by_id = {
        e["observation"]["observation_id"]: e["observation"] for e in catalog["candidates"]
    }
    by_source_key = {
        (o["company_slug"], str(o["fiscal_year"]), o["metric_code"], o["source_url"]): oid
        for oid, o in candidate_by_id.items()
    }
    for batch in ["batch1", "batch2"]:
        directory = evidence / batch
        path = directory / "candidate_facts_validation_only.csv"
        expected_hash = read_json(directory / "validation_receipt.json")["candidate_csv_sha256"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError("candidate CSV hash mismatch")
        records = load_financial_csv(path.name, allowed_root=directory)
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [
            by_source_key[(r["company_slug"], r["fiscal_year"], r["metric_code"], r["source_url"])]
            for r in rows
        ]
        if any(row.get("observation_id", oid) != oid for row, oid in zip(rows, ids, strict=True)):
            raise ValueError("candidate CSV observation ID mismatch")
        if len(ids) != len(set(ids)) or csv_ids.intersection(ids):
            raise ValueError("duplicate candidate CSV observation ID")
        if len(records) != len(rows):
            raise ValueError("candidate model count mismatch")
        for oid, record in zip(ids, records, strict=True):
            o = candidate_by_id[oid]
            expected = _record_from_row({k: str(v) if v is not None else "" for k, v in o.items()})
            if record != expected:
                raise ValueError("candidate CSV record differs from evidence")
        csv_ids.update(ids)
    if csv_ids != {e["observation"]["observation_id"] for e in catalog["candidates"]}:
        raise ValueError("catalog candidates differ from merged evidence batches")
    return catalog


def review_index(catalog: dict) -> dict:
    sources = {}
    facts = []
    for entry in catalog["candidates"]:
        o = entry["observation"]
        sources[entry["source_key"]] = {
            "company_slug": o["company_slug"],
            "source_url": o["source_url"],
            "source_sha256": o["source_sha256"],
        }
        facts.append(
            {
                "observation_id": o["observation_id"],
                "evidence_sha256": entry["evidence_sha256"],
                "definition_sha256": entry["definition_sha256"],
                "metric_code": o["metric_code"],
                "fiscal_year": o["fiscal_year"],
                "source_key": entry["source_key"],
                "source_page": o["source_page"],
                "measurement_type": o["measurement_type"],
                "as_of": o["as_of"],
            }
        )
    return {
        "catalog_sha256": catalog["sha256"],
        "sources": sources,
        "candidates": facts,
        "withheld_conflicting_keys": catalog["conflicting_keys"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--target-snapshot", type=Path)
    parser.add_argument("--expected-project-ref")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = load_catalog(args.repo_root)
    reviews = ReviewLedger.model_validate(read_json(args.reviews))
    target = (
        TargetSnapshot.model_validate(read_json(args.target_snapshot))
        if args.target_snapshot
        else None
    )
    plan = build_load_plan(
        catalog, reviews, target=target, expected_project_ref=args.expected_project_ref
    )
    protected = {
        args.reviews.resolve(),
        (args.repo_root / "data/m2/ril-tcs/review/target_snapshot_schema.json").resolve(),
        (args.repo_root / "data/m2/ril-tcs/review/pnl_metric_definitions.json").resolve(),
        (args.repo_root / "data/m2/ril-tcs/review/catalog_index.json").resolve(),
        args.target_snapshot.resolve() if args.target_snapshot else args.reviews.resolve(),
    }
    evidence_root = (args.repo_root / "data/m2/ril-tcs").resolve()
    if args.output.suffix.lower() != ".json":
        raise ValueError("plan output must be a JSON file")
    if (
        args.output.resolve() in protected
        or args.output.resolve().is_relative_to(evidence_root / "batch1")
        or args.output.resolve().is_relative_to(evidence_root / "batch2")
    ):
        raise ValueError("output would overwrite review/source evidence")
    args.output.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps({**plan["summary"], "apply_ready": False, "plan_sha256": digest(plan)}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
