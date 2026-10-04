"""Read-only calculations bound to approved, exactly matched loaded evidence."""

from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from analyst_os_ingestion.planning import build_load_plan, digest

from . import formulas

POLICY_VERSION = "reported-core-1"


def build_analytics_preview(packets, target, *, project_ref, now=None):
    """Fail closed if any approved input is missing, conflicting or changed.

    No aliases for bank income, owner profit, capex or debt are inferred. The
    existing arithmetic uses reported group profit; it is not owner PAT or a
    recurring-profit measure. This preview cannot write derived database rows.
    """
    bound = {}
    bindings = []
    companies, years = set(), set()
    for catalog, reviews in packets:
        plan = build_load_plan(
            catalog, reviews, target=target, expected_project_ref=project_ref, now=now
        )
        approved = {oid for oid, review in reviews.facts.items() if review.status == "approved"}
        present = {p["observation_id"]: p["existing_fact_id"] for p in plan["already_present"]}
        if set(present) != approved or plan["proposed_facts"]:
            raise ValueError("all approved inputs must already be loaded without conflicts")
        companies.update(o["company_slug"] for o in catalog["payload"]["observations"])
        years.update(catalog["payload"]["fiscal_years"])
        bindings.append(
            {
                "catalog_sha256": catalog["sha256"],
                "review_ledger_sha256": plan["review_ledger_sha256"],
            }
        )
        for entry in catalog["candidates"]:
            o = entry["observation"]
            oid = o["observation_id"]
            if oid not in approved:
                continue
            key = (o["company_slug"], o["fiscal_year"], o["metric_code"])
            if key in bound:
                raise ValueError("multiple approved inputs for a calculation key")
            bound[key] = {
                "fact_id": present[oid],
                "observation_id": oid,
                "evidence_sha256": entry["evidence_sha256"],
                "definition_sha256": entry["definition_sha256"],
                "normalized_value": o["normalized_value"],
                "currency": o["currency"],
            }
    if not bound or {str(f.id) for f in target.facts} != {o["fact_id"] for o in bound.values()}:
        raise ValueError("snapshot must contain exactly the approved loaded fact universe")
    calculations = []
    for company in sorted(companies):
        for year in sorted(years):
            cfo = "cash_from_operations" if company in {"reliance-industries", "tcs"} else "cfo"
            for code, label, unit, codes, function in (
                (
                    "current_ratio",
                    "Current ratio",
                    "ratio",
                    ["current_assets", "current_liabilities"],
                    formulas.current_ratio,
                ),
                (
                    "working_capital",
                    "Reported working capital",
                    "INR",
                    ["current_assets", "current_liabilities"],
                    formulas.working_capital,
                ),
                (
                    "cfo_to_reported_group_profit",
                    "CFO / reported consolidated group profit",
                    "ratio",
                    [cfo, "profit_for_year"],
                    formulas.cfo_to_pat,
                ),
            ):
                inputs = [bound.get((company, year, metric)) for metric in codes]
                if any(o and o["currency"] != "INR" for o in inputs):
                    raise ValueError("calculation requires consistent INR inputs")
                numbers = [Decimal(o["normalized_value"]) if o else None for o in inputs]
                with localcontext() as context:
                    context.prec = 28
                    context.rounding = ROUND_HALF_EVEN
                    value = function(*numbers)
                calculations.append(
                    {
                        "company_slug": company,
                        "fiscal_year": year,
                        "metric_code": code,
                        "label": label,
                        "unit": unit,
                        "value": str(value) if value is not None else None,
                        "status": "available" if value is not None else "unavailable",
                        "unavailable_reason": None
                        if value is not None
                        else (
                            "missing_approved_input"
                            if None in inputs
                            else "nonpositive_denominator"
                        ),
                        "input_metric_codes": codes,
                        "inputs": inputs,
                    }
                )
    return {
        "mode": "preview",
        "production_writes": 0,
        "project_ref": project_ref,
        "policy_version": POLICY_VERSION,
        "formula_version": formulas.FORMULA_VERSION,
        "target_snapshot_sha256": digest(target.model_dump(mode="json")),
        "target_snapshot_captured_at": target.captured_at.isoformat(),
        "packet_bindings": bindings,
        "approved_loaded_facts": len(bound),
        "available": sum(c["value"] is not None for c in calculations),
        "unavailable": sum(c["value"] is None for c in calculations),
        "calculations": calculations,
        "scope": "Reported same-period consolidated inputs only. No recurring-profit, "
        "bank industrial-ratio, capex/debt proxy or comparable-growth inference.",
    }
