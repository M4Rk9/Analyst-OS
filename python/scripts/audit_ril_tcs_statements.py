"""Corroborate pinned BS/CF statements and produce a pending decision packet."""

import argparse
import json
from pathlib import Path

from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.statement_review import audit_statement_sources
from scripts.plan_ril_tcs_load import load_catalog, read_json


def statement_packet(catalog: dict, audit: dict) -> str:
    if audit["catalog_sha256"] != catalog["sha256"]:
        raise ValueError("statement audit catalog differs")
    checks = {check["observation_id"]: check for check in audit["statement_observations"]}
    expected = {
        o["observation_id"]: o for o in catalog["payload"]["observations"]
        if o["metric_code"] not in {
            "revenue", "other_income", "total_income", "finance_costs",
            "total_expenses", "profit_for_year",
        }
    }
    if len(checks) != len(audit["statement_observations"]) or set(checks) != set(expected):
        raise ValueError("statement audit scope differs")
    for oid, observation in expected.items():
        if checks[oid]["evidence_sha256"] != digest(observation):
            raise ValueError("statement audit evidence differs")
    rows, gaps = [], []
    for entry in catalog["candidates"]:
        observation = entry["observation"]
        check = checks.get(observation["observation_id"])
        if check is None:
            continue
        if check["evidence_sha256"] != entry["evidence_sha256"]:
            raise ValueError("statement audit evidence differs")
        if check["result"] == "label_row_and_dated_column_match":
            if (
                check["normalized_value"] != observation["normalized_value"]
                or check["raw_value"] != observation["raw_value"]
            ):
                raise ValueError("statement audit amount differs")
            rows.append(entry)
        else:
            gaps.append(entry)
    if len(rows) + len(gaps) != 320:
        raise ValueError("statement packet differs from pending BS/CF scope")
    text = [
        "# RIL/TCS BS/CF decision packet", "",
        f"**Decision state: pending.** {len(rows)} explicit numeric candidates are corroborated; "
        f"{len(gaps)} dash-valued candidates remain unavailable. "
        "No new reviews or loads occur.", "",
        f"Catalog SHA-256: `{catalog['sha256']}`. Audit SHA-256: `{digest(audit)}`.", "",
        "The audit checks all 644 current/comparative BS/CF observations in the ten pinned "
        "official reports. It binds the exact label, repeated-label statement section, dated "
        "column, signed amount and INR-crore scale. Dashes and footnoted numeric text fail "
        "closed. The existing 56 P&L approvals remain unchanged.", "",
        "## Definitions and review limits", "",
        "Values are reported consolidated figures in INR crore, normalized by multiplying "
        "by 10,000,000. BS figures are instants at March 31; CF figures are April-March "
        "durations. Cash outflows retain their printed negative signs. Current-year selection "
        "does not establish adjusted cross-year comparability. Statement borrowing/lease "
        "components are not a complete debt definition. Cash interest paid is not accrual "
        "interest expense. Acquisition cash and ROU cash are not automatically conventional "
        "PPE capex. Total group equity is not owner equity. No new metric aliases are implied.", "",
    ]
    codes = {entry["observation"]["metric_code"] for entry in rows}
    for code in sorted(codes):
        definition = catalog["payload"]["definitions"][code]
        text.append(f"- **{code}:** {definition['definition']} "
                    f"Definition SHA-256: `{digest(definition)}`.")
    for company in ["reliance-industries", "tcs"]:
        selected = [entry for entry in rows if entry["observation"]["company_slug"] == company]
        text += ["", f"## {company}: {len(selected)} candidates", "",
                 "| Exact observation ID | INR crore | PDF / printed page | Printed row |",
                 "|---|---:|---|---|"]
        for entry in selected:
            o = entry["observation"]
            label = checks[o["observation_id"]]["label"]["text"].strip().replace("|", "\\|")
            label = " ".join(label.split())
            text.append(
                f"| `{o['observation_id']}` | {o['raw_value_text']} | "
                f"[{o['source_page']}]({o['source_url']}#page={o['source_page']}) / "
                f"{o['printed_pages']} | {label} |"
            )
    text += ["", "## Unavailable and withheld", ""]
    for entry in gaps:
        o = entry["observation"]
        text.append(f"- `{o['observation_id']}`: printed `{o['raw_value_text']}`. "
                    "The historical extraction encoded zero; numeric publication is blocked. "
                    "A separately reviewed source/definition correction is required.")
    text += ["", "The six existing conflict keys stay withheld under Marky's stated decision. "
             "No conflict preference or catalog rewrite is introduced.", "",
             "## Record actual decisions", "",
             "Review exact IDs, source rows and definitions before recording approvals in the "
             "protected ledger for this unchanged catalog. Unlisted IDs remain pending. Do not "
             "approve the two dash-valued candidates as zero. New decisions need reviewer, "
             "timezone-aware decision time and substantive rationale. The authenticated ten "
             "sources are already covered by the previous approval; additional fact decisions "
             "must be explicit.", "",
             "After decisions, export a fresh privileged RIL/TCS snapshot containing the "
             "existing 56 facts, regenerate the plan, inspect its/schema hashes and preview the "
             "controlled publisher before explicit apply. Preserve the atomic receipt. "
             "This packet alone does not complete the five-company M2 gate.", ""]
    return "\n".join(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output_dir.resolve(strict=True)
    if output.is_relative_to(args.source_root.resolve()) or any(
        output.is_relative_to(repo / "data/m2/ril-tcs" / batch) for batch in ["batch1", "batch2"]
    ):
        raise ValueError("output cannot replace source or batch evidence")
    catalog = load_catalog(repo)
    audit = audit_statement_sources(
        catalog, args.source_root, read_json(repo / "data/m2/ril-tcs/batch2/observations.json")
    )
    (output / "bs_cf_source_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "BS_CF_DECISION_PACKET.md").write_text(
        statement_packet(catalog, audit), encoding="utf-8"
    )
    print(json.dumps({**audit["summary"], "audit_sha256": digest(audit)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
