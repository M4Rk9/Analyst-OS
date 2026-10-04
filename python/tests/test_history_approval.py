"""Ensure the recorded human decision covers only the exact reviewed packets."""

import re
from pathlib import Path

from analyst_os_ingestion.planning import ReviewLedger, build_load_plan, digest, source_key
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as load_universe

ROOT = Path(__file__).resolve().parents[2]


def test_history_approval_matches_packets_and_preserves_original_decision():
    receipt = read_json(ROOT / "docs/M2_HISTORY_APPROVAL.json")
    for name, loader, folder, packet, count in [
        ("ril-tcs", load_catalog, "data/m2/ril-tcs/review", "BS_CF_DECISION_PACKET.md", 318),
        ("universe", load_universe, "data/m2/universe", "DECISION_PACKET.md", 255),
    ]:
        directory = ROOT / folder
        catalog = loader(ROOT)
        ledger = ReviewLedger.model_validate(read_json(directory / "marky_approved_reviews.json"))
        ids = set(re.findall(r"^\| `([^`]+:report\d+)` \|",
                             (directory / packet).read_text(), re.M))
        assert len(ids) == count
        assert receipt["packets"][name]["review_ledger_sha256"] == digest(
            ledger.model_dump(mode="json")
        )
        approved = {oid for oid, review in ledger.facts.items() if review.status == "approved"}
        new = {oid for oid in approved if ledger.facts[oid].reviewed_at.isoformat()
               == "2026-10-04T14:06:27+00:00"}
        assert new == ids
        for oid in new:
            assert ledger.facts[oid].reviewer == "Marky"
            assert ledger.facts[oid].rationale == receipt["rationale"]
        assert not approved.intersection(
            e["observation"]["observation_id"] for e in catalog["withheld"]
        )
        plan = build_load_plan(catalog, ledger)
        assert digest(plan) == receipt["packets"][name]["offline_plan_sha256"]
        assert plan["summary"]["proposed_inserts"] == 0  # Native snapshot remains required.
        assert plan["summary"]["production_writes"] == 0
        if name == "ril-tcs":
            original = approved - new
            assert len(original) == 56
            previous = ReviewLedger(
                catalog_sha256=ledger.catalog_sha256,
                sources=ledger.sources,
                facts={oid: ledger.facts[oid] for oid in original},
            )
            assert digest(previous.model_dump(mode="json")) == receipt[
                "prior_review_ledger_sha256"
            ]
            for oid in original:
                review = ledger.facts[oid]
                assert review.reviewed_at.isoformat() == "2026-10-04T08:31:04+00:00"
                assert review.rationale == (
                    "I accept the cited evidence and definitions for these reported "
                    "consolidated figures."
                )
            assert all(ledger.facts.get(e["observation"]["observation_id"]) is None
                       for e in catalog["candidates"]
                       if e["observation"]["raw_value_text"] == "-")
        else:
            assert approved == ids
            sources = {source_key(o) for o in catalog["payload"]["observations"]}
            assert len(sources) == 15
            assert set(receipt["new_source_approvals"]) == sources
            assert all(r["status"] == "approved" and r["reviewer"] == "Marky"
                       for r in receipt["new_source_approvals"].values())
            assert len(ledger.sources) == 14
            assert set(ledger.sources) < sources
    assert receipt["withheld_conflict_keys"] == 46
    assert receipt["unavailable_dash_candidates"] == 2
