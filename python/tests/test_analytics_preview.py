"""Synthetic target UUIDs; real pinned approvals/definitions, no production writer."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from analyst_os_analytics.preview import build_analytics_preview
from analyst_os_ingestion.loader import _record_from_row
from analyst_os_ingestion.planning import ExistingFact, ExistingSource, ReviewLedger, TargetSnapshot
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as universe_catalog

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "abcdefghijklmnopqrst"
NOW = datetime(2026, 10, 4, 16, tzinfo=UTC)


@pytest.fixture(scope="module")
def loaded():
    packets = [
        (loader(ROOT), ReviewLedger.model_validate(read_json(ROOT / path)))
        for loader, path in (
            (load_catalog, "data/m2/ril-tcs/review/marky_approved_reviews.json"),
            (universe_catalog, "data/m2/universe/marky_approved_reviews.json"),
        )
    ]
    facts, sources = [], {}
    for catalog, reviews in packets:
        for e in catalog["candidates"]:
            o = e["observation"]
            review = reviews.facts.get(o["observation_id"])
            if not review or review.status != "approved":
                continue
            record = _record_from_row({k: str(v) if v is not None else "" for k, v in o.items()})
            facts.append(
                ExistingFact(
                    id=UUID(int=len(facts) + 1),
                    record=record,
                    normalized_value=record.normalized_value,
                    reporting_basis=o["reporting_basis"],
                    measurement_type=o["measurement_type"],
                    as_of=o["as_of"],
                    definition_sha256=e["definition_sha256"],
                    quality_status="verified",
                    is_preferred=True,
                )
            )
            sources[e["source_key"]] = ExistingSource(
                company_slug=o["company_slug"],
                source_url=o["source_url"],
                sha256=o["source_sha256"],
                verification_status="verified",
            )
    target = TargetSnapshot(
        project_ref=PROJECT,
        captured_at=NOW,
        complete=True,
        company_slugs=sorted({f.record.company_slug for f in facts}),
        sources=list(sources.values()),
        facts=facts,
    )
    return packets, target


def test_loaded_preview_matches_post_load_checks_and_preserves_input_ids(loaded):
    packets, target = loaded
    result = build_analytics_preview(packets, target, project_ref=PROJECT, now=NOW)
    assert result["production_writes"] == 0
    assert (result["approved_loaded_facts"], result["available"], result["unavailable"]) == (
        629,
        43,
        32,
    )
    actual = {
        (c["company_slug"], c["fiscal_year"], c["metric_code"]): c for c in result["calculations"]
    }
    for row in read_json(ROOT / "docs/M2_POST_LOAD_VERIFICATION.json")["calculations"]:
        code = "working_capital" if row["metric"] == "working_capital_inr" else row["metric"]
        calc = actual[(row["company_slug"], row["fiscal_year"], code)]
        assert calc["value"] == row["value"]
        assert [o["observation_id"] if o else None for o in calc["inputs"]] == row[
            "input_observation_ids"
        ]
        assert all(
            o is None or o["fact_id"] in {str(f.id) for f in target.facts} for o in calc["inputs"]
        )
    assert all(
        c["value"] is None for c in result["calculations"] if c["company_slug"] == "hdfc-bank"
    )
    assert all(
        c["value"] is None
        for c in result["calculations"]
        if c["company_slug"] == "tata-motors" and c["fiscal_year"] == 2024
    )


def test_missing_approved_fact_cannot_silently_reduce_preview(loaded):
    packets, target = loaded
    changed = target.model_copy(update={"facts": target.facts[1:]})
    with pytest.raises(ValueError, match="must already be loaded"):
        build_analytics_preview(packets, changed, project_ref=PROJECT, now=NOW)


@pytest.mark.parametrize("change", ["definition", "status", "value"])
def test_changed_loaded_evidence_blocks_calculations(loaded, change):
    packets, target = loaded
    fact = target.facts[0]
    updates = {
        "definition": {"definition_sha256": "0" * 64},
        "status": {"quality_status": "unverified"},
        "value": {
            "record": fact.record.model_copy(update={"raw_value": fact.record.raw_value + 1})
        },
    }
    changed = target.model_copy(
        update={"facts": [fact.model_copy(update=updates[change]), *target.facts[1:]]}
    )
    with pytest.raises(ValueError, match="must already be loaded"):
        build_analytics_preview(packets, changed, project_ref=PROJECT, now=NOW)


def test_stale_or_wrong_project_snapshot_blocks_preview(loaded):
    packets, target = loaded
    with pytest.raises(ValueError, match="project mismatch"):
        build_analytics_preview(packets, target, project_ref="x" * 20, now=NOW)
    with pytest.raises(ValueError, match="stale"):
        build_analytics_preview(packets, target, project_ref=PROJECT, now=NOW + timedelta(days=2))
