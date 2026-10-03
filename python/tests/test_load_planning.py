"""Review, provenance, target-conflict and retry behavior using the real evidence catalog."""

import copy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from analyst_os_ingestion.loader import _record_from_row
from analyst_os_ingestion.planning import (
    ExistingFact,
    ExistingSource,
    Review,
    TargetSnapshot,
    build_catalog,
    build_load_plan,
    empty_reviews,
)
from pydantic import HttpUrl
from scripts.plan_ril_tcs_load import load_catalog, read_json, review_index

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 3, 20, tzinfo=UTC)
PROJECT = "abcdefghijklmnopqrst"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT)


def approval():
    # Synthetic attestation for tests only; no production ledger receives it.
    return Review(
        status="approved",
        reviewer="Test reviewer",
        reviewed_at=NOW,
        rationale="Test attestation only",
    )


def approve_one(catalog, entry=None):
    entry = entry or catalog["candidates"][0]
    reviews = empty_reviews(catalog)
    reviews.sources[entry["source_key"]] = approval()
    reviews.facts[entry["observation"]["observation_id"]] = approval()
    return reviews, entry


def snapshot(**changes):
    return TargetSnapshot.model_validate(
        {
            "project_ref": PROJECT,
            "captured_at": NOW,
            "complete": True,
            "company_slugs": ["reliance-industries", "tcs"],
            "sources": [],
            "facts": [],
            **changes,
        }
    )


def record(entry):
    return _record_from_row(
        {k: str(v) if v is not None else "" for k, v in entry["observation"].items()}
    )


def existing(entry, **changes):
    o = entry["observation"]
    return ExistingFact.model_validate(
        {
            "id": UUID(int=1),
            "record": record(entry),
            "normalized_value": changes.get("record", record(entry)).normalized_value,
            "reporting_basis": o["reporting_basis"],
            "measurement_type": o["measurement_type"],
            "as_of": o["as_of"],
            "definition_sha256": entry["definition_sha256"],
            "quality_status": "verified",
            "is_preferred": True,
            **changes,
        }
    )


def source(entry, **changes):
    o = entry["observation"]
    return ExistingSource.model_validate(
        {
            "company_slug": o["company_slug"],
            "source_url": o["source_url"],
            "sha256": o["source_sha256"],
            "verification_status": "verified",
            **changes,
        }
    )


def plan(catalog, reviews, target):
    return build_load_plan(catalog, reviews, target=target, expected_project_ref=PROJECT, now=NOW)


def reasons(result, entry):
    return next(
        b["reasons"]
        for b in result["blocked"]
        if b["observation_id"] == entry["observation"]["observation_id"]
    )


def test_real_plan_matches_committed_artifacts_and_does_not_preapprove(catalog):
    reviews = empty_reviews(catalog)
    result = build_load_plan(catalog, reviews)
    path = ROOT / "data/m2/ril-tcs/review"
    assert result == read_json(path / "load_plan.json")
    assert review_index(catalog) == read_json(path / "catalog_index.json")
    assert reviews.model_dump(mode="json") == read_json(path / "review_template.json")
    assert TargetSnapshot.model_json_schema() == read_json(path / "target_snapshot_schema.json")
    assert result["summary"] == {
        "evidence_observations": 764,
        "candidate_facts": 376,
        "unresolved_conflicting_keys": 6,
        "withheld_current_year_facts": 6,
        "blocked_candidates": 376,
        "proposed_inserts": 0,
        "already_present": 0,
        "production_writes": 0,
    }
    assert result["apply_ready"] is False


def test_approved_fact_still_requires_approved_source_and_target(catalog):
    reviews, entry = approve_one(catalog)
    reviews.sources.clear()
    result = build_load_plan(catalog, reviews, now=NOW)
    assert reasons(result, entry) == ["source_review_pending", "target_snapshot_missing"]
    reviews.sources[entry["source_key"]] = approval()
    assert reasons(build_load_plan(catalog, reviews, now=NOW), entry) == ["target_snapshot_missing"]


def test_one_approved_insert_proposal_preserves_full_companion_metadata(catalog):
    entry = next(
        e for e in catalog["candidates"] if e["observation"]["measurement_type"] == "instant"
    )
    reviews, entry = approve_one(catalog, entry)
    result = plan(catalog, reviews, snapshot())
    proposed = result["proposed_facts"][0]
    assert result["summary"]["proposed_inserts"] == 1
    assert proposed["provenance"] == entry
    assert proposed["provenance"]["observation"]["as_of"] == entry["observation"]["period_end"]
    assert proposed["record"]["source"]["sha256"] == entry["observation"]["source_sha256"]
    assert proposed["quality_status"] == "verified" and proposed["is_preferred"] is True
    assert result["apply_ready"] is False  # Proposal cannot become an executable write.


def test_identical_existing_verified_preferred_observation_is_idempotent(catalog):
    reviews, entry = approve_one(catalog)
    target = snapshot(sources=[source(entry)], facts=[existing(entry)])
    result = plan(catalog, reviews, target)
    assert result["summary"]["proposed_inserts"] == 0
    assert result["already_present"] == [
        {
            "observation_id": entry["observation"]["observation_id"],
            "existing_fact_id": str(UUID(int=1)),
        }
    ]


@pytest.mark.parametrize("status", ["unverified", "conflict"])
def test_existing_fact_is_not_silently_upgraded(catalog, status):
    reviews, entry = approve_one(catalog)
    result = plan(
        catalog,
        reviews,
        snapshot(sources=[source(entry)], facts=[existing(entry, quality_status=status)]),
    )
    assert "target_existing_review_state_differs" in reasons(result, entry)
    assert result["proposed_facts"] == []


def test_existing_target_value_conflict_blocks_even_approved_input(catalog):
    reviews, entry = approve_one(catalog)
    old_record = record(entry).model_copy(update={"raw_value": record(entry).raw_value + 1})
    result = plan(
        catalog,
        reviews,
        snapshot(sources=[source(entry)], facts=[existing(entry, record=old_record)]),
    )
    assert "target_value_conflict" in reasons(result, entry)
    assert result["proposed_facts"] == []


@pytest.mark.parametrize("change", ["basis", "definition", "period", "measurement"])
def test_equal_values_do_not_hide_semantic_target_conflicts(catalog, change):
    reviews, entry = approve_one(catalog)
    updates = (
        {"reporting_basis": "standalone"}
        if change == "basis"
        else (
            {"definition_sha256": "0" * 64}
            if change == "definition"
            else {
                "record": record(entry).model_copy(
                    update={"period_start": record(entry).period_end}
                )
            }
        )
    )
    if change == "measurement":
        updates = {"measurement_type": "instant", "as_of": record(entry).period_end.isoformat()}
    result = plan(
        catalog, reviews, snapshot(sources=[source(entry)], facts=[existing(entry, **updates)])
    )
    assert "target_definition_or_period_conflict" in reasons(result, entry)


def test_same_source_url_cannot_silently_replace_pdf_hash(catalog):
    reviews, entry = approve_one(catalog)
    result = plan(catalog, reviews, snapshot(sources=[source(entry, sha256="0" * 64)]))
    assert "target_source_hash_conflict" in reasons(result, entry)


def test_pending_target_source_cannot_be_silently_promoted(catalog):
    reviews, entry = approve_one(catalog)
    result = plan(
        catalog, reviews, snapshot(sources=[source(entry, verification_status="pending")])
    )
    assert "target_source_not_verified" in reasons(result, entry)


def test_existing_preferred_source_is_not_automatically_demoted(catalog):
    reviews, entry = approve_one(catalog)
    previous = record(entry)
    other_source = previous.source.model_copy(
        update={"source_url": HttpUrl("https://example.com/other.pdf")}
    )
    previous = previous.model_copy(update={"source": other_source})
    target = snapshot(
        sources=[source(entry, source_url=str(other_source.source_url))],
        facts=[existing(entry, record=previous)],
    )
    assert "target_preferred_replacement_requires_review" in reasons(
        plan(catalog, reviews, target), entry
    )


def test_conflicting_source_keys_cannot_be_approved_through_candidate_ledger(catalog):
    reviews = empty_reviews(catalog)
    reviews.facts[catalog["withheld"][0]["observation"]["observation_id"]] = approval()
    with pytest.raises(ValueError, match="unknown or withheld"):
        build_load_plan(catalog, reviews)


def test_definition_changes_invalidate_previous_approvals(catalog):
    observations = read_json(ROOT / "data/m2/ril-tcs/batch1/observations.json")
    observations += read_json(ROOT / "data/m2/ril-tcs/batch2/observations.json")
    definitions = {
        e["observation"]["metric_code"]: copy.deepcopy(e["definition"])
        for e in [*catalog["candidates"], *catalog["withheld"]]
    }
    definitions["finance_costs"]["definition"] += " Changed definition."
    changed = build_catalog(
        observations,
        definitions,
        read_json(ROOT / "data/m2/ril-tcs/batch1/source_manifest.json"),
        set(range(2022, 2027)),
    )
    with pytest.raises(ValueError, match="stale"):
        build_load_plan(changed, empty_reviews(catalog))


@pytest.mark.parametrize("change", ["project", "stale", "future", "scope"])
def test_target_binding_freshness_and_scope_are_required(catalog, change):
    target = snapshot()
    expected = "project mismatch"
    if change == "project":
        target = snapshot(project_ref="tsrqponmlkjihgfedcba")
    elif change in {"stale", "future"}:
        target = snapshot(
            captured_at=NOW + (timedelta(days=-2) if change == "stale" else timedelta(seconds=1))
        )
        expected = "stale or future"
    elif change == "scope":
        target = snapshot(company_slugs=["tcs"])
        expected = "does not cover"
    with pytest.raises(ValueError, match=expected):
        plan(catalog, empty_reviews(catalog), target)


def test_future_review_or_incomplete_attestation_is_rejected(catalog):
    with pytest.raises(ValueError, match="require reviewer"):
        Review(status="approved")
    with pytest.raises(ValueError, match="timezone"):
        Review(
            status="approved",
            reviewer="Test",
            rationale="Test",
            reviewed_at=NOW.replace(tzinfo=None),
        )
    reviews, entry = approve_one(catalog)
    reviews.facts[entry["observation"]["observation_id"]] = Review(
        status="approved", reviewer="Test", rationale="Test", reviewed_at=NOW + timedelta(seconds=1)
    )
    with pytest.raises(ValueError, match="future"):
        build_load_plan(catalog, reviews, now=NOW)


def test_duplicate_target_observation_and_incomplete_export_are_rejected(catalog):
    entry = catalog["candidates"][0]
    old = existing(entry)
    with pytest.raises(ValueError, match="natural key"):
        snapshot(
            sources=[source(entry)],
            facts=[old, old.model_copy(update={"id": UUID(int=2), "is_preferred": False})],
        )
    with pytest.raises(ValueError):
        snapshot(complete=False)


def test_duplicate_json_review_keys_are_not_silently_overwritten(tmp_path):
    path = tmp_path / "reviews.json"
    path.write_text('{"facts": {}, "facts": {}}')
    with pytest.raises(ValueError, match="duplicate JSON"):
        read_json(path)


def test_rejected_fact_remains_blocked_with_approved_source(catalog):
    reviews, entry = approve_one(catalog)
    reviews.facts[entry["observation"]["observation_id"]] = Review(
        status="rejected", reviewer="Test", rationale="Test rejection", reviewed_at=NOW
    )
    result = plan(catalog, reviews, snapshot())
    assert reasons(result, entry) == ["fact_review_rejected"]
    assert result["proposed_facts"] == []


def test_snapshot_must_export_and_validate_actual_stored_normalized_value(catalog):
    entry = catalog["candidates"][0]
    with pytest.raises(ValueError, match="stored normalization"):
        existing(entry, normalized_value=record(entry).normalized_value + 1)
