"""Recheck the RIL/TCS batch2 evidence and accounting bridges without database writes."""

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from analyst_os_ingestion.conflicts import find_conflicts
from analyst_os_ingestion.loader import _record_from_row, load_financial_csv


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source_number(text: str) -> Decimal:
    glyphs = str.maketrans("ϬϭϮϯϰϱϲϳϴϵ", "0123456789")
    compact = re.sub(r"[,\s]", "", text.translate(glyphs)).removesuffix("#")
    _require("*" not in compact and "@" not in compact, "Inexact source value")
    if compact in {"-", "–"}:
        return Decimal(0)  # Only a plain, visually reviewed reported-nil dash.
    _require(bool(re.fullmatch(r"\d+|\(\d+\)", compact)), "Invalid source value text")
    return Decimal("-" + compact[1:-1] if compact.startswith("(") else compact)


def _reconcile_group(company, report_year, year, group):
    checks = []

    def v(metric):
        return Decimal(group[metric]["raw_value"])

    def check(name, left_metrics, right_metrics, formula, right_value=None):
        left = sum((v(m) * sign for m, sign in left_metrics), Decimal(0))
        right = v(right_metrics[0]) if right_value is None else right_value
        _require(left == right, f"Accounting bridge failed: {company}/{report_year}/{year}/{name}")
        checks.append(
            {
                "company_slug": company,
                "report_fiscal_year": report_year,
                "fiscal_year": year,
                "check": name,
                "formula": formula,
                "unit": "INR crore",
                "left_value": str(left),
                "right_value": str(right),
                "difference": "0",
                "input_observation_ids": [
                    group[m]["observation_id"]
                    for m in dict.fromkeys([m for m, _ in left_metrics] + right_metrics)
                ],
            }
        )

    equity_components = [
        (m, 1) for m in ("share_capital", "other_equity", "noncontrolling_interest")
    ]
    equity = sum((v(m) for m, _ in equity_components), Decimal(0))
    check(
        "asset_components",
        [("noncurrent_assets", 1), ("current_assets", 1)],
        ["total_assets"],
        "noncurrent_assets + current_assets = total_assets",
    )
    if "total_equity" in group:
        check(
            "equity_components",
            equity_components,
            ["total_equity"],
            "share_capital + other_equity + noncontrolling_interest = total_equity",
        )
    check(
        "balance_sheet",
        equity_components + [("noncurrent_liabilities", 1), ("current_liabilities", 1)],
        ["total_assets"],
        "equity components + noncurrent/current liabilities = total_assets",
    )
    if "total_equity" not in group:
        checks.append(
            {
                "company_slug": company,
                "report_fiscal_year": report_year,
                "fiscal_year": year,
                "check": "derived_equity_only",
                "formula": "share_capital + other_equity + noncontrolling_interest",
                "unit": "INR crore",
                "derived_value": str(equity),
                "input_observation_ids": [group[m]["observation_id"] for m, _ in equity_components],
                "production_fact": False,
            }
        )
    check(
        "operating_cash",
        [("cash_generated_before_tax", 1), ("taxes_paid_net", 1)],
        ["cash_from_operations"],
        "cash_generated_before_tax + signed taxes_paid_net = CFO",
    )
    check(
        "cash_movement",
        [("cash_from_operations", 1), ("cash_from_investing", 1), ("cash_from_financing", 1)],
        ["cash_change"],
        "CFO + CFI + CFF = cash_change",
    )
    bridge = [("opening_cash", 1), ("cash_change", 1)]
    for metric, sign in [
        ("cash_fx_adjustment", 1),
        ("cash_subsidiary_additions", 1),
        ("cash_demerger_deduction", -1),
    ]:
        if metric in group:
            bridge.append((metric, sign))
    check(
        "closing_cash_bridge",
        bridge,
        ["closing_cash"],
        "opening_cash + cash_change + reported FX/subsidiary additions - reported demerger",
    )
    check(
        "cash_agrees_with_balance_sheet",
        [("closing_cash", 1)],
        ["cash_and_cash_equivalents"],
        "cash-flow closing cash = balance-sheet cash",
    )
    return checks


def validate_batch(batch: Path) -> tuple[dict, list[dict]]:
    """Validate committed evidence; original PDF authenticity remains a separate review."""
    observations = _json(batch / "observations.json")
    pages = _json(batch / "source_pages.json")
    manifest = _json(batch.parent / "batch1/source_manifest.json")
    source_by_report = {(m["company_slug"], m["report_fiscal_year"]): m for m in manifest}
    ids = [o["observation_id"] for o in observations]
    _require(len(ids) == len(set(ids)), "Duplicate observation IDs")
    _require(len(source_by_report) == 10, "Expected ten source reports")
    page_lookup = {}
    for page in pages:
        path = batch / page["text_file"]
        _require(path.resolve().parent == batch.resolve(), "Evidence path escapes batch")
        _require(
            hashlib.sha256(path.read_bytes()).hexdigest() == page["text_sha256"],
            "Evidence text hash mismatch",
        )
        key = (page["company_slug"], page["report_fiscal_year"], page["source_page"])
        _require(key not in page_lookup, "Duplicate page entry")
        page_lookup[key] = page

    notes = _json(batch / "supporting_notes.json")
    for note in notes:
        path = batch / note["text_file"]
        _require(path.resolve().parent == batch.resolve(), "Note path escapes batch")
        _require(
            hashlib.sha256(path.read_bytes()).hexdigest() == note["text_sha256"],
            "Supporting note text hash mismatch",
        )
        source = source_by_report[(note["company_slug"], note["report_fiscal_year"])]
        _require(note["source_sha256"] == source["sha256"], "Supporting note source mismatch")
        _require(note["source_url"] == source["source_url"], "Supporting note URL mismatch")

    groups = defaultdict(dict)
    models = []
    for o in observations:
        source_key = (o["company_slug"], o["source_fiscal_year"])
        source = source_by_report[source_key]
        _require(o["source_sha256"] == source["sha256"], "Source hash mismatch")
        _require(o["source_url"] == source["source_url"], "Source URL mismatch")
        _require(o["source_publisher"] == source["publisher"], "Source publisher mismatch")
        _require(
            o["quality_status"] == "unverified" and not o["is_preferred"],
            "Evidence must not imply production approval",
        )
        _require(o["reporting_basis"] == "consolidated", "Unexpected reporting basis")
        _require(o["column_role"] in {"current_year", "comparative"}, "Invalid column role")
        year = o["source_fiscal_year"] - (o["column_role"] == "comparative")
        _require(o["fiscal_year"] == year, "Incorrect source column year")
        _require(o["period_start"] == f"{year - 1}-04-01", "Incorrect period start")
        _require(o["period_end"] == f"{year}-03-31", "Incorrect period end")
        page = page_lookup[(*source_key, o["source_page"])]
        _require(o["evidence_text_file"] == page["text_file"], "Page reference mismatch")
        _require(o["printed_pages"] == page["printed_pages"], "Printed page mismatch")
        expected_type = "instant" if page["statement"] == "bs" else "duration"
        _require(o["measurement_type"] == expected_type, "Incorrect measurement type")
        _require(
            o["as_of"] == (o["period_end"] if expected_type == "instant" else None),
            "Incorrect as-of date",
        )
        lines = [
            line.strip()
            for line in (batch / page["text_file"]).read_text().splitlines()
            if line.strip()
        ]
        start = o["evidence_label_line"] - 1
        _require(0 <= start < len(lines), "Invalid evidence line")
        _require(o["raw_value_text"] in lines[start : start + 20], "Raw text missing near label")
        _require(
            _source_number(o["raw_value_text"]) == Decimal(o["raw_value"]),
            "Raw source value mismatch",
        )
        record = _record_from_row({k: str(v) if v is not None else "" for k, v in o.items()})
        _require(record.unit_scale == Decimal("10000000"), "Incorrect crore scaling")
        _require(record.currency == "INR", "Unexpected currency")
        _require(
            record.normalized_value == Decimal(o["normalized_value"]), "Normalization mismatch"
        )
        models.append(record)
        group = groups[(*source_key, o["fiscal_year"])]
        _require(o["metric_code"] not in group, "Duplicate metric within source column")
        group[o["metric_code"]] = o
    _require(len(groups) == 20, "Expected twenty statement columns")

    conflicts = find_conflicts(models)
    bad = {(c.key.company_slug, c.key.fiscal_year, c.key.metric_code) for c in conflicts}
    ledger = _json(batch / "conflict_ledger.json")
    ledger_keys = {(c["company_slug"], c["fiscal_year"], c["metric_code"]) for c in ledger}
    _require(bad == ledger_keys and len(ledger) == len(bad), "Conflict ledger mismatch")
    for conflict in ledger:
        key = (conflict["company_slug"], conflict["fiscal_year"], conflict["metric_code"])
        expected = [
            o
            for o in observations
            if (o["company_slug"], o["fiscal_year"], o["metric_code"]) == key
        ]
        _require(conflict["observations"] == expected, "Conflict evidence mismatch")
        _require(
            conflict["status"] == "unresolved" and not conflict["preference_selected"],
            "Conflict must remain unresolved",
        )

    csv_path = batch / "candidate_facts_validation_only.csv"
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_candidates = {
        o["observation_id"]: o
        for o in observations
        if o["column_role"] == "current_year"
        and (o["company_slug"], o["fiscal_year"], o["metric_code"]) not in bad
    }
    _require(len(rows) == len(expected_candidates), "Candidate row count mismatch")
    _require(
        {r["observation_id"] for r in rows} == set(expected_candidates),
        "Candidate selection mismatch",
    )
    for row in rows:
        expected = expected_candidates[row["observation_id"]]
        for field, actual in row.items():
            value = expected[field]
            wanted = "" if value is None else str(value)
            _require(actual == wanted, f"Candidate metadata mismatch: {field}")
    loaded = load_financial_csv(csv_path.name, allowed_root=batch)
    _require(len(loaded) == len(rows), "Loader row count mismatch")

    checks = []
    for (company, report_year, year), group in sorted(groups.items()):
        checks.extend(_reconcile_group(company, report_year, year, group))

    receipt = {
        "documents": len(source_by_report),
        "statement_text_pages": len(pages),
        "supporting_note_pages": len(notes),
        "observations": len(observations),
        "source_columns": len(groups),
        "current_year_observations": sum(o["column_role"] == "current_year" for o in observations),
        "conflicting_keys": len(bad),
        "validated_candidate_rows": len(loaded),
        "accounting_identity_checks": sum("difference" in c for c in checks),
        "derived_equity_entries_not_in_candidate_csv": sum("derived_value" in c for c in checks),
        "candidate_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "production_writes": 0,
        "limitations": [
            "Schema validation does not approve facts for production",
            "Original PDF hash/authenticity checks were performed during extraction",
            "This checker verifies committed page-text hashes, not remote official PDFs",
            "Companion metadata must survive any later publisher; CSV loader drops extras",
        ],
    }
    return receipt, checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="Trusted local batch2 directory")
    args = parser.parse_args()
    receipt, checks = validate_batch(args.batch)
    _require(_json(args.batch / "validation_receipt.json") == receipt, "Receipt mismatch")
    _require(_json(args.batch / "reconciliation_ledger.json") == checks, "Reconciliation mismatch")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
