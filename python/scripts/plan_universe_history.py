"""Validate and plan the pinned HDFC/L&T/Tata history; never infer approval or write SQL."""

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from analyst_os_ingestion.planning import (
    ReviewLedger,
    TargetSnapshot,
    build_catalog,
    build_load_plan,
    digest,
    empty_reviews,
)
from scripts.plan_ril_tcs_load import read_json


def reconciliations(observations):
    groups = defaultdict(dict)
    for o in observations:
        key = (o["company_slug"], o["source_fiscal_year"], o["column_role"])
        groups[key][o["metric_code"]] = Decimal(o["raw_value"])
    checks = []
    for key, values in groups.items():
        company, report_year, role = key
        equations = []
        if company == "hdfc-bank":
            equations = [
                ("bank_income", ["bank_interest_earned", "bank_other_income"], "bank_total_income"),
                ("bank_cash_definition", ["bank_cash_rbi", "bank_balances_call_money"],
                 "bank_closing_cash"),
            ]
        else:
            revenue = (
                "lt_reported_revenue" if company == "larsen-toubro" else "tata_reported_revenue"
            )
            equations = [("income", [revenue, "other_income"], "total_income"),
                         ("balance_sheet", ["total_equity_liabilities"], "total_assets"),
                         ("closing_cash", ["closing_cash"], "cash_and_cash_equivalents")]
            if company == "larsen-toubro":
                equations.append(("equity_and_liabilities", ["total_equity", "total_liabilities"],
                                  "total_assets"))
        for name, lhs, rhs in equations:
            if not set([*lhs, rhs]).issubset(values):
                raise ValueError("configured reconciliation input unavailable")
            difference = sum(values[code] for code in lhs) - values[rhs]
            if difference != 0:
                raise ValueError(f"reconciliation differs: {company} {report_year} {role} {name}")
            checks.append({"company_slug": company, "report_fiscal_year": report_year,
                           "column_role": role, "check": name, "lhs": lhs, "rhs": rhs,
                           "difference_inr_crore": str(difference), "result": "pass"})
    return checks


def load_catalog(repo: Path):
    directory = repo / "data/m2/universe"
    evidence = read_json(directory / "history_evidence.json")
    manifest = read_json(directory / "source_manifest.json")
    configuration = read_json(directory / "extraction_configuration.json")
    if evidence["manifest"] != manifest or evidence["gaps"]:
        raise ValueError("evidence manifest differs or core extraction gaps remain")
    definitions = evidence["definitions"]
    expected_ids = {
        f"{s['company_slug']}:{s['report_fiscal_year'] - slot}:"
        f"{metric['metric_code']}:report{s['report_fiscal_year']}"
        for s in manifest for metric in configuration[s["company_slug"]]["metrics"]
        for slot in range(2)
    }
    if {o["observation_id"] for o in evidence["observations"]} != expected_ids:
        raise ValueError("configured history field coverage differs")
    catalog = build_catalog(evidence["observations"], definitions, manifest, set(range(2022, 2027)))
    if catalog["sha256"] != evidence["catalog_sha256"]:
        raise ValueError("history catalog hash differs")
    rows = evidence["row_evidence"]
    indexed = {row["observation_id"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) != {
        o["observation_id"] for o in evidence["observations"]
    }:
        raise ValueError("row evidence scope differs")
    for o in evidence["observations"]:
        row = indexed[o["observation_id"]]
        if row["evidence_sha256"] != digest(o) or row["source_page"] != o["source_page"]:
            raise ValueError("row evidence binding differs")
        if row["amount"]["text"].strip() != o["raw_value_text"]:
            raise ValueError("row display amount differs")
        if row["label"]["text"].strip() != o["source_label"]:
            raise ValueError("row label differs")
        settings = configuration[o["company_slug"]]
        metric = next(m for m in settings["metrics"] if m["metric_code"] == o["metric_code"])
        if o["source_page"] not in settings["pages"][str(o["source_fiscal_year"])][
            metric["statement"]
        ]:
            raise ValueError("row page differs from configured statement")
        if definitions[o["metric_code"]]["definition"] != metric["definition"]:
            raise ValueError("configured metric definition differs")
    checks = reconciliations(evidence["observations"])
    if checks != read_json(directory / "reconciliation_ledger.json"):
        raise ValueError("reconciliation ledger differs")
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--target-snapshot", type=Path)
    parser.add_argument("--expected-project-ref")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    catalog = load_catalog(repo)
    reviews = (
        ReviewLedger.model_validate(read_json(args.reviews))
        if args.reviews else empty_reviews(catalog)
    )
    target = (
        TargetSnapshot.model_validate(read_json(args.target_snapshot))
        if args.target_snapshot else None
    )
    result = build_load_plan(catalog, reviews, target=target,
                             expected_project_ref=args.expected_project_ref)
    if args.output.resolve().is_relative_to(repo / "data/m2/universe"):
        raise ValueError("private plan output cannot overwrite pinned history evidence")
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"plan_sha256": digest(result), **result["summary"]}))


if __name__ == "__main__":
    main()
