"""Pending five-year evidence, statement bindings and explicit scope decisions."""

import copy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from analyst_os_ingestion.planning import (
    Review,
    TargetSnapshot,
    build_load_plan,
    digest,
    empty_reviews,
)
from analyst_os_ingestion.publishing import prepare_request
from analyst_os_ingestion.universe_review import extract_row
from scripts.plan_ril_tcs_load import read_json
from scripts.plan_universe_history import load_catalog, reconciliations

ROOT = Path(__file__).resolve().parents[2]


def test_three_company_history_is_pinned_reconciled_and_entirely_pending():
    catalog = load_catalog(ROOT)
    evidence = read_json(ROOT / "data/m2/universe/history_evidence.json")
    assert len(catalog["payload"]["source_manifest"]) == 15
    assert len(catalog["payload"]["observations"]) == 590
    assert len(catalog["candidates"]) == 255
    assert len(catalog["withheld"]) == catalog["conflicting_keys"] == 40
    assert len(reconciliations(evidence["observations"])) == 90
    assert all(o["quality_status"] == "unverified" and o["is_preferred"] is False
               for o in evidence["observations"])
    result = build_load_plan(catalog, empty_reviews(catalog))
    assert result["summary"]["proposed_inserts"] == 0
    assert result["summary"]["blocked_candidates"] == 255
    assert result == read_json(ROOT / "data/m2/universe/pending_load_plan.json")
    assert all(e["observation"]["source_fiscal_year"] == 2026
               for e in catalog["candidates"]
               if e["observation"]["company_slug"] == "tata-motors"
               and e["observation"]["fiscal_year"] == 2026)
    assert "PROPOSED ENTITY CONTINUITY" in next(
        s for s in evidence["manifest"]
        if s["company_slug"] == "tata-motors" and s["report_fiscal_year"] == 2026
    )["scope_note"]


def rows():
    def line(text, x, y, right):
        return {"text": text, "bbox": [x, y, right, y + 10]}
    return [line("March 31, 2026", 400, 20, 450),
            line("March 31, 2025", 500, 20, 550),
            line("Total Income", 40, 50, 150),
            line("1,234", 400, 50, 450), line("(999)", 500, 50, 550)]


@pytest.mark.parametrize("change", ["dash", "footnote", "date", "duplicate", "label"])
def test_ambiguous_and_unavailable_core_rows_fail_closed(change):
    lines = rows()
    if change == "dash":
        lines[3]["text"] = "-"
    elif change == "footnote":
        lines[3]["text"] = "1,234*"
    elif change == "date":
        lines[0]["text"] = "March 31, 2024"
    elif change == "duplicate":
        lines.append(copy.deepcopy(lines[3]))
    else:
        lines[2]["text"] = "Unrelated income"
    with pytest.raises(ValueError):
        extract_row(lines, ["Total Income"], 2026)


def test_source_signed_values_and_header_are_preserved():
    result = extract_row(rows(), ["Total Income"], 2026)
    assert result[0]["amount"]["text"] == "1,234"
    assert result[1]["amount"]["text"] == "(999)"
    assert result[1]["header"]["text"] == "March 31, 2025"


def test_mutated_universe_cannot_reuse_review_or_reconciliation(tmp_path):
    evidence = read_json(ROOT / "data/m2/universe/history_evidence.json")
    changed = copy.deepcopy(evidence["observations"])
    next(o for o in changed if o["metric_code"] == "bank_total_income")["raw_value"] = "1"
    with pytest.raises(ValueError, match="reconciliation differs"):
        reconciliations(changed)
    assert digest(changed) != digest(evidence["observations"])


@pytest.mark.parametrize("company", ["hdfc-bank", "larsen-toubro", "tata-motors"])
def test_existing_publisher_prepares_scoped_new_company_requests(company):
    catalog = load_catalog(ROOT)
    entry = next(e for e in catalog["candidates"] if e["observation"]["company_slug"] == company)
    reviews = empty_reviews(catalog)
    now = datetime(2026, 10, 4, 13, tzinfo=UTC)
    attestation = Review(status="approved", reviewer="TEST ONLY", reviewed_at=now,
                         rationale="Synthetic request test; no live financial approval")
    reviews.sources[entry["source_key"]] = attestation
    reviews.facts[entry["observation"]["observation_id"]] = attestation
    target = TargetSnapshot(project_ref="abcdefghijklmnopqrst", captured_at=now,
                            complete=True,
                            company_slugs=["hdfc-bank", "larsen-toubro", "tata-motors"],
                            sources=[], facts=[])
    plan = build_load_plan(catalog, reviews, target=target,
                           expected_project_ref=target.project_ref, now=now)
    request = prepare_request(catalog, reviews, target, plan, expected_plan_sha256=digest(plan),
                              project_ref=target.project_ref, now=now)
    assert request["selected"] == [entry["observation"]["observation_id"]]
    assert plan["proposed_facts"][0]["provenance"]["observation"]["scope_note"]
