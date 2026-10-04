"""Explicit approval/plan/apply gates; no credentials or production writes."""

import copy
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from analyst_os_ingestion.planning import (
    Review,
    TargetSnapshot,
    build_load_plan,
    digest,
    empty_reviews,
)
from analyst_os_ingestion.publishing import PublishError, prepare_request, publish
from scripts.plan_ril_tcs_load import load_catalog

from scripts import publish_ril_tcs as cli

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "abcdefghijklmnopqrst"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT)


def inputs(catalog, approved=True):
    reviews = empty_reviews(catalog)
    if approved:
        entry = catalog["candidates"][0]
        review = Review(
            status="approved",
            reviewer="TEST ONLY",
            reviewed_at=datetime(2020, 1, 1, tzinfo=UTC),
            rationale="Synthetic attestation for isolated test",
        )
        reviews.sources[entry["source_key"]] = review
        reviews.facts[entry["observation"]["observation_id"]] = review
    target = TargetSnapshot(
        project_ref=PROJECT,
        captured_at=datetime.now(UTC),
        complete=True,
        company_slugs=["reliance-industries", "tcs"],
        sources=[],
        facts=[],
    )
    plan = build_load_plan(catalog, reviews, target=target, expected_project_ref=PROJECT)
    return reviews, target, plan


def test_pending_catalog_cannot_reach_database_writer(catalog):
    reviews, target, plan = inputs(catalog, approved=False)
    request = prepare_request(
        catalog, reviews, target, plan, expected_plan_sha256=digest(plan), project_ref=PROJECT
    )
    connection = Mock()
    with pytest.raises(PublishError, match="no approved"):
        publish(connection, request, expected_schema_sha256="a" * 64)
    connection.execute.assert_not_called()
    assert not request["selected"]


@pytest.mark.parametrize("change", ["plan", "digest", "catalog", "reviews"])
def test_changed_inputs_cannot_use_the_reviewed_plan(catalog, change):
    catalog = copy.deepcopy(catalog)
    reviews, target, plan = inputs(catalog)
    sha = digest(plan)
    if change == "plan":
        plan["proposed_facts"][0]["normalized_value"] = "1"
        sha = digest(plan)
    elif change == "digest":
        sha = "0" * 64
    elif change == "catalog":
        catalog["sha256"] = "0" * 64
    else:
        reviews.facts.clear()
    with pytest.raises(PublishError):
        prepare_request(
            catalog, reviews, target, plan, expected_plan_sha256=sha, project_ref=PROJECT
        )


def test_withheld_observation_cannot_be_approved_into_a_request(catalog):
    reviews, target, plan = inputs(catalog)
    key = catalog["withheld"][0]["observation"]["observation_id"]
    reviews.facts[key] = next(iter(reviews.facts.values()))
    with pytest.raises(ValueError, match="withheld"):
        prepare_request(
            catalog, reviews, target, plan, expected_plan_sha256=digest(plan), project_ref=PROJECT
        )


def cli_files(catalog, tmp_path, monkeypatch, *, approved=True):
    reviews, target, plan = inputs(catalog, approved=approved)
    values = {
        "reviews": reviews.model_dump(mode="json"),
        "target-snapshot": target.model_dump(mode="json"),
        "reviewed-plan": plan,
    }
    argv = ["publisher"]
    for name, value in values.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value))
        argv.extend([f"--{name}", str(path)])
    ca = tmp_path / "ca.pem"
    ca.write_text("TEST ONLY CA PATH")
    argv.extend(
        [
            "--expected-project-ref",
            PROJECT,
            "--expected-plan-sha256",
            digest(plan),
            "--ssl-root-cert",
            str(ca),
        ]
    )
    monkeypatch.setenv(
        "ANALYST_OS_DATABASE_URL",
        f"postgresql://postgres:TEST_ONLY@db.{PROJECT}.supabase.co:5432/postgres",
    )
    return argv


def test_cli_defaults_to_preview_and_cannot_call_publish(catalog, tmp_path, monkeypatch):
    import psycopg

    argv = cli_files(catalog, tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", argv)
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    connect = Mock(return_value=connection)
    monkeypatch.setattr(psycopg, "connect", connect)
    preview = Mock(return_value={"production_writes": 0})
    writer = Mock(side_effect=AssertionError("dry-run must never call publisher"))
    monkeypatch.setattr(cli, "preview", preview)
    monkeypatch.setattr(cli, "publish", writer)
    assert cli.main() == 0
    preview.assert_called_once()
    writer.assert_not_called()
    assert "default_transaction_read_only=on" in connect.call_args.kwargs["options"]


@pytest.mark.parametrize("approved", [True, False])
def test_apply_requires_approved_selection_and_schema_hash_before_connecting(
    catalog, tmp_path, monkeypatch, approved
):
    import psycopg

    argv = cli_files(catalog, tmp_path, monkeypatch, approved=approved) + ["--apply"]
    if not approved:
        argv += ["--expected-schema-sha256", "a" * 64]
    monkeypatch.setattr(sys, "argv", argv)
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)
    assert cli.main() == 1
    connect.assert_not_called()


def test_cli_preserves_uncertain_commit_diagnostic_when_close_fails(
    catalog, tmp_path, monkeypatch, capsys
):
    import psycopg

    argv = cli_files(catalog, tmp_path, monkeypatch) + [
        "--apply",
        "--expected-schema-sha256",
        "a" * 64,
    ]
    monkeypatch.setattr(sys, "argv", argv)
    connection = Mock()
    connection.close.side_effect = RuntimeError("TEST ONLY cleanup failure")
    monkeypatch.setattr(psycopg, "connect", Mock(return_value=connection))
    monkeypatch.setattr(
        cli, "publish", Mock(side_effect=PublishError("commit outcome uncertain; import_id=TEST"))
    )
    assert cli.main() == 1
    assert "commit outcome uncertain; import_id=TEST" in capsys.readouterr().err
    connection.close.assert_called_once()
