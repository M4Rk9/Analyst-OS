"""Reproduce local PDF corroboration and a pending 56-fact P&L decision packet."""

import argparse
import json
from pathlib import Path

from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.source_review import audit_pnl_sources
from scripts.plan_ril_tcs_load import load_catalog, read_json


def decision_packet(catalog: dict, audit: dict) -> str:
    if audit["catalog_sha256"] != catalog["sha256"]:
        raise ValueError("P&L source audit belongs to a different catalog")
    checks = {r["observation_id"]: r for r in audit["pnl_observations"]}
    codes = {
        "revenue",
        "other_income",
        "total_income",
        "finance_costs",
        "total_expenses",
        "profit_for_year",
    }
    expected = {
        o["observation_id"]: o
        for o in catalog["payload"]["observations"]
        if o["metric_code"] in codes
    }
    if len(checks) != len(audit["pnl_observations"]) or set(checks) != set(expected):
        raise ValueError("P&L audit scope differs from catalog observations")
    if any(
        r["evidence_sha256"] != digest(expected[oid])
        or r["result"] != "label_row_and_dated_column_match"
        or r["raw_value"] != expected[oid]["raw_value"]
        or r["normalized_value"] != expected[oid]["normalized_value"]
        for oid, r in checks.items()
    ):
        raise ValueError("P&L audit differs from catalog evidence")
    rows = [e for e in catalog["candidates"] if e["observation"]["observation_id"] in checks]
    if len(rows) != 56:
        raise ValueError("expected the reviewed 56-candidate P&L scope")
    text = [
        "# First P&L load decision packet",
        "",
        "**Decision state: pending.** This is a source-backed proposal for 56 P&L observations, "
        "not an approved ledger, executable plan or production load.",
        "",
        f"Catalog SHA-256: `{catalog['sha256']}`. P&L audit SHA-256: `{digest(audit)}`.",
        "",
        "The official retrieval receipt and visual inspection notes accompany this packet. "
        "All 120 current/comparative observations passed "
        "label-row, dated-column and amount checks. Four FY2022 RIL P&L keys remain withheld; "
        "the other two catalog conflicts are cash-flow keys outside this packet.",
        "",
        "## Decisions to record",
        "",
        "1. Select each authenticated official PDF, including the reacquired TCS FY2026 "
        "copy rather than the different upload. Source keys are in `pnl_source_audit.json`.",
        "2. Accept or reject each exact observation ID below with its definition. "
        "Current-year statement selection is not an assertion of adjusted comparability.",
        "3. Copy the current pending `review_template.json` to a protected local path. "
        "Record actual reviewer identity, timezone-aware decision time and substantive rationale "
        "for approved/rejected source and fact entries. Leave other entries pending. "
        "Do not copy an audit result into an approval status.",
        "4. After target preflight/migrations, export a fresh privileged snapshot, build and "
        "inspect the plan, preview the publisher/schema inventory, then explicitly apply only "
        "the approved target-ready selection. Retain the atomic receipt.",
        "",
        "Merging this packet approves neither the sources nor the facts. "
        "An approved P&L subset can be loaded independently of pending balance-sheet/cash-flow "
        "decisions, but it does not complete M2 or establish all derived analytics inputs.",
        "",
        "## Exact review scope",
        "",
        "| Field | RIL fiscal years | TCS fiscal years | Candidates |",
        "|---|---|---|---:|",
        "| revenue | FY2023–2026 | FY2022–2026 | 9 |",
        "| other_income | FY2023–2026 | FY2022–2026 | 9 |",
        "| total_income | FY2023–2026 | FY2022–2026 | 9 |",
        "| finance_costs | FY2022–2026 | FY2022–2026 | 10 |",
        "| total_expenses | FY2023–2026 | FY2022–2026 | 9 |",
        "| profit_for_year | FY2022–2026 | FY2022–2026 | 10 |",
        "",
        "RIL: 26 candidates. TCS: 30 candidates. All decisions remain pending.",
        "",
        "## Definitions and limits",
        "",
    ]
    for code, definition in catalog["payload"]["definitions"].items():
        if code in {e["observation"]["metric_code"] for e in rows}:
            text += [f"- **{code}:** {definition['definition']}"]
    text += [
        "",
        "All values below are **INR crore** exactly as recorded in the statement; normalized "
        "INR is raw value × 10,000,000. Annual durations are April 1 to March 31. "
        "Finance costs are not interest expense; group profit includes NCI and is not owner PAT. "
        "Do not map these fields to EBIT, EBITDA, COGS, debt or generic PAT aliases.",
        "",
        "The current frontend only charts `revenue` from this six-field packet. "
        "Displaying the other fields needs explicit presentation labels; this packet does not "
        "silently rename them to existing chart aliases.",
        "",
    ]
    for company in ["reliance-industries", "tcs"]:
        text += [
            f"## {company}",
            "",
            "| Exact observation ID | INR crore | PDF page / printed page | Source row |",
            "|---|---:|---|---|",
        ]
        for entry in rows:
            o = entry["observation"]
            if o["company_slug"] != company:
                continue
            url = o["source_url"] + "#page=" + str(o["source_page"])
            text += [
                f"| `{o['observation_id']}` | {o['raw_value_text']} | "
                f"[{o['source_page']}]({url}) / {o['printed_pages']} | {o['source_label']} |"
            ]
        text += [""]
    text += [
        "## Withheld and remaining",
        "",
        "RIL FY2022 revenue, other income, total income and total expenses have competing "
        "demerger-era presentations. Retain both statements and resolve scope coherently in a "
        "separate resolution package. No value-selection override is introduced here.",
        "",
        "The other 320 candidates remain pending and are outside this row audit. "
        "Owner profit, interest/debt scope, EBIT/capex policy, RIL FY2022 equity and the two "
        "FY2024 cash-flow conflicts still require source/definition work. HDFC Bank, Tata "
        "Motors and L&T history remains unconfirmed. Target/RLS/concurrency, derived-output "
        "provenance and deployment verification remain release gates.",
        "",
    ]
    return "\n".join(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output_dir.resolve()
    if not output.is_dir():
        raise ValueError("output must be an existing directory")
    protected = (repo / "data/m2/ril-tcs").resolve()
    if output.is_relative_to(args.source_root.resolve()) or any(
        output.is_relative_to(protected / batch) for batch in ["batch1", "batch2"]
    ):
        raise ValueError("output cannot replace source/batch evidence")
    catalog = load_catalog(repo)
    audit = audit_pnl_sources(
        catalog,
        args.source_root,
        read_json(repo / "data/m2/ril-tcs/batch1/observations.json"),
    )
    packet = decision_packet(catalog, audit)
    (output / "pnl_source_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "PNL_DECISION_PACKET.md").write_text(packet, encoding="utf-8")
    print(json.dumps({**audit["summary"], "audit_sha256": digest(audit)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
