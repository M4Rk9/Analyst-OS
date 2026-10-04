"""Read-only export completeness, provenance, connection and file-safety tests."""

import copy
import json
import os
import sys
from pathlib import Path
from uuid import UUID

import pytest
from analyst_os_ingestion import snapshot as module
from analyst_os_ingestion.planning import build_load_plan, digest, empty_reviews
from analyst_os_ingestion.snapshot import (
    BEGIN_SQL,
    CONTEXT_SQL,
    DEFAULT_SCOPE,
    QUERIES,
    SETTINGS_SQL,
    SnapshotError,
    build_snapshot,
    collect_snapshot,
    connection_parameters,
    write_snapshot,
)
from pydantic import ValidationError
from scripts.export_target_snapshot import main
from scripts.plan_ril_tcs_load import load_catalog, read_json

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "abcdefghijklmnopqrst"
CAPTURED = "2026-10-04T07:00:00Z"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT)


@pytest.fixture
def rows(catalog):
    entry = next(e for e in catalog["candidates"] if e["observation"]["company_slug"] == "tcs")
    o = entry["observation"]
    company_id, period_id, source_id, fact_id = [str(UUID(int=n)) for n in range(1, 5)]
    return {
        "companies": [{"id": company_id, "slug": "tcs"},
                      {"id": str(UUID(int=5)), "slug": "reliance-industries"}],
        "periods": [{"id": period_id, "company_id": company_id,
                     **{k: o[k] for k in ("period_type", "fiscal_year", "period_start",
                                          "period_end", "currency")}}],
        "sources": [{"id": source_id, "company_id": company_id,
                     "title": o["source_title"], "document_type": o["source_document_type"],
                     "source_url": o["source_url"], "publisher": o["source_publisher"],
                     "published_at": None, "fiscal_year": o["source_fiscal_year"],
                     "fiscal_quarter": None, "sha256": o["source_sha256"],
                     "verification_status": "pending"}],
        "facts": [{"id": fact_id, "company_id": company_id,
                   "reporting_period_id": period_id, "source_document_id": source_id,
                   **{k: o[k] for k in ("metric_code", "raw_value_text", "raw_value",
                                        "normalized_value", "currency", "unit_scale",
                                        "source_page", "source_label")},
                   "quality_status": "unverified", "is_preferred": False}],
        "proofs": [{"fact_id": fact_id, "source_document_id": source_id,
                    "observation_id": o["observation_id"], "catalog_sha256": catalog["sha256"],
                    "review_ledger_sha256": "a" * 64,
                    "evidence_sha256": entry["evidence_sha256"],
                    "definition_sha256": entry["definition_sha256"],
                    "evidence_canonical_json": canonical(o),
                    "definition_canonical_json": canonical(entry["definition"])}],
        "catalogs": [{"catalog_sha256": catalog["sha256"],
                      "canonical_json": canonical(catalog["payload"])}],
    }


def convert(rows):
    return build_snapshot(rows, project_ref=PROJECT, scope=DEFAULT_SCOPE, captured_at=CAPTURED)


class Cursor:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return self.value

    def fetchall(self):
        return self.value


class Connection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
        self.rolled_back = False
        self.context = {
            "database_role": "analyst_snapshot", "database_name": "postgres",
            "captured_at": CAPTURED, "read_only": "on", "row_security": "off",
            "isolation": "repeatable read", "privileged": True, "ssl": True,
        }

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if query == CONTEXT_SQL:
            return Cursor(self.context)
        for name, sql in QUERIES.items():
            if query.startswith("select count(*)::integer as row_count,") and sql in query:
                return Cursor({"row_count": len(self.rows[name]),
                               "byte_count": len(json.dumps(self.rows[name]).encode())})
            if query == sql + " limit %s":
                return Cursor(self.rows[name])
        if query == BEGIN_SQL or query in SETTINGS_SQL:
            return Cursor(None)
        raise AssertionError("unexpected SQL")

    def rollback(self):
        self.rolled_back = True


def test_keeps_pending_unverified_and_conflict_rows_without_upgrades(rows):
    for status in ("unverified", "conflict"):
        rows["facts"][0]["quality_status"] = status
        target = convert(rows)
        assert target.facts[0].quality_status == status
        assert target.sources[0].verification_status == "pending"
        assert not target.facts[0].is_preferred
        assert target.complete and target.company_slugs == sorted(DEFAULT_SCOPE)


def test_empty_target_is_complete_only_when_all_companies_exist(rows, catalog):
    for key in rows:
        if key != "companies":
            rows[key] = []
    target = convert(rows)
    assert not target.sources and not target.facts
    plan = build_load_plan(catalog, empty_reviews(catalog), target=target,
                           expected_project_ref=PROJECT,
                           now=target.captured_at)
    assert plan["summary"]["proposed_inserts"] == 0
    assert plan["summary"]["blocked_candidates"] == 376
    rows["companies"].pop()
    with pytest.raises(SnapshotError, match="every company"):
        convert(rows)


@pytest.mark.parametrize("key", ["companies", "periods", "sources", "facts"])
def test_duplicate_database_identity_fails(rows, key):
    rows[key].append(copy.deepcopy(rows[key][0]))
    with pytest.raises(SnapshotError, match="duplicate"):
        convert(rows)


def test_legacy_fact_without_proof_is_not_omitted(rows):
    rows["proofs"] = []
    with pytest.raises(SnapshotError, match="lacks provenance"):
        convert(rows)


def test_null_source_hash_is_not_guessed(rows):
    rows["sources"][0]["sha256"] = None
    with pytest.raises(ValidationError):
        convert(rows)


@pytest.mark.parametrize("field,value", [
    ("normalized_value", "1"), ("raw_value", "NaN"), ("currency", "USD"),
    ("source_page", 1), ("source_label", "changed"), ("raw_value_text", "changed"),
])
def test_altered_core_fact_fails(rows, field, value):
    rows["facts"][0][field] = value
    with pytest.raises((SnapshotError, ValidationError)):
        convert(rows)


def test_cross_company_links_fail(rows):
    rows["periods"][0]["company_id"] = rows["companies"][1]["id"]
    with pytest.raises(SnapshotError, match="cross-company"):
        convert(rows)


def test_identical_evidence_under_multiple_ledgers_is_unambiguous(rows):
    rows["proofs"].append({**rows["proofs"][0], "review_ledger_sha256": "b" * 64})
    assert len(convert(rows).facts) == 1


def test_changed_companion_evidence_under_a_second_catalog_is_ambiguous(rows):
    proof = copy.deepcopy(rows["proofs"][0])
    payload = json.loads(rows["catalogs"][0]["canonical_json"])
    observation = next(o for o in payload["observations"]
                       if o["observation_id"] == proof["observation_id"])
    observation["extraction_correction"] = "A different retained annotation"
    text = canonical(payload)
    proof["catalog_sha256"] = digest(payload)
    proof["evidence_canonical_json"] = canonical(observation)
    proof["evidence_sha256"] = digest(observation)
    rows["catalogs"].append({"catalog_sha256": proof["catalog_sha256"], "canonical_json": text})
    rows["proofs"].append(proof)
    with pytest.raises(SnapshotError, match="ambiguous"):
        convert(rows)


@pytest.mark.parametrize("field", ["evidence_canonical_json", "definition_canonical_json"])
def test_tampered_hash_fails(rows, field):
    rows["proofs"][0][field] += " "
    with pytest.raises(SnapshotError, match="hash mismatch"):
        convert(rows)


def test_proof_source_and_catalog_must_match(rows):
    rows["proofs"][0]["source_document_id"] = str(UUID(int=99))
    with pytest.raises(SnapshotError, match="source mismatch"):
        convert(rows)
    rows["proofs"][0]["source_document_id"] = rows["sources"][0]["id"]
    rows["catalogs"] = []
    with pytest.raises(SnapshotError, match="validated catalog"):
        convert(rows)


def test_noncanonical_evidence_cannot_change_the_review_hash_contract(rows):
    import hashlib

    proof = rows["proofs"][0]
    proof["evidence_canonical_json"] = json.dumps(json.loads(proof["evidence_canonical_json"]),
                                                indent=2)
    proof["evidence_sha256"] = hashlib.sha256(
        proof["evidence_canonical_json"].encode()
    ).hexdigest()
    with pytest.raises(SnapshotError, match="not canonical"):
        convert(rows)


def test_export_uses_one_read_only_transaction_and_always_rolls_back(rows):
    connection = Connection(rows)
    assert len(collect_snapshot(connection, project_ref=PROJECT).facts) == 1
    assert connection.calls[0] == (BEGIN_SQL, None)
    assert connection.rolled_back
    query_calls = connection.calls[1 + len(SETTINGS_SQL) + 1:]
    assert len(query_calls) == 2 * len(QUERIES)
    assert all(params == (sorted(DEFAULT_SCOPE), module.MAX_ROWS + 1)
               for _, params in query_calls)


@pytest.mark.parametrize("field,value", [
    ("privileged", False), ("ssl", False), ("read_only", "off"),
    ("row_security", "on"), ("isolation", "read committed"), ("database_name", "other"),
    ("database_role", "anon"),
])
def test_unsafe_session_is_rejected_before_reading_rows(rows, field, value):
    connection = Connection(rows)
    connection.context[field] = value
    with pytest.raises(SnapshotError, match="require TLS"):
        collect_snapshot(connection, project_ref=PROJECT)
    assert connection.rolled_back
    assert len(connection.calls) == 2 + len(SETTINGS_SQL)


def test_caps_and_failed_queries_cannot_produce_partial_snapshots(rows, monkeypatch):
    monkeypatch.setattr(module, "MAX_ROWS", 1)
    connection = Connection(rows)
    with pytest.raises(SnapshotError, match="truncated"):
        collect_snapshot(connection, project_ref=PROJECT)
    assert connection.rolled_back
    monkeypatch.setattr(module, "MAX_ROWS", 10_000)
    monkeypatch.setattr(module, "MAX_BYTES", 10)
    with pytest.raises(SnapshotError, match="size limit"):
        collect_snapshot(Connection(rows), project_ref=PROJECT)


def test_partial_fetch_and_query_failure_always_rollback(rows):
    class Partial(Connection):
        def execute(self, query, params=None):
            result = super().execute(query, params)
            if query == QUERIES["companies"] + " limit %s":
                return Cursor(result.value[:1])
            return result

    connection = Partial(rows)
    with pytest.raises(SnapshotError, match="read count mismatch"):
        collect_snapshot(connection, project_ref=PROJECT)
    assert connection.rolled_back

    class Broken(Connection):
        def execute(self, query, params=None):
            if query == QUERIES["facts"] + " limit %s":
                raise RuntimeError("TEST ONLY connection failed")
            return super().execute(query, params)

    connection = Broken(rows)
    with pytest.raises(RuntimeError, match="connection failed"):
        collect_snapshot(connection, project_ref=PROJECT)
    assert connection.rolled_back


def test_connection_target_tls_and_options_are_fixed(tmp_path):
    ca = tmp_path / "trusted-ca.pem"
    ca.write_text("TEST ONLY CA PATH")
    for url in (f"postgresql://postgres:secret@db.{PROJECT}.supabase.co:5432/postgres",
                f"postgresql://analyst_snapshot.{PROJECT}:secret@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"):
        params = connection_parameters(url, PROJECT, ca)
        assert params["sslmode"] == "verify-full"
        assert params["hostaddr"] == "" and params["gssencmode"] == "disable"
        assert "default_transaction_read_only=on" in params["options"]


@pytest.mark.parametrize("url", [
    "postgresql://postgres:secret@db.wrongproject.supabase.co:5432/postgres",
    "postgresql://postgres.otherproject:secret@aws-0-ap-south-1.pooler.supabase.com:5432/postgres",
    f"postgresql://postgres:secret@db.{PROJECT}.supabase.co:6543/postgres",
    f"postgresql://postgres:secret@db.{PROJECT}.supabase.co:5432/postgres?sslmode=disable",
    f"postgresql://anon:secret@db.{PROJECT}.supabase.co:5432/postgres",
    f"postgresql://postgres:secret@db.{PROJECT}.supabase.co.evil.test:5432/postgres",
    "postgresql://postgres:secret@127.0.0.1:5432/postgres",
])
def test_unbound_connections_are_rejected_without_echoing_credentials(tmp_path, url):
    ca = tmp_path / "ca.pem"
    ca.write_text("TEST ONLY")
    with pytest.raises(SnapshotError) as error:
        connection_parameters(url, PROJECT, ca)
    assert "secret" not in str(error.value)


def test_private_exclusive_output_round_trips_to_planner(rows, tmp_path):
    target = convert(rows)
    path = tmp_path / "test.target-snapshot.json"
    assert write_snapshot(target, path) == digest(target.model_dump(mode="json"))
    assert read_json(path) == target.model_dump(mode="json")
    assert os.stat(path).st_mode & 0o777 == 0o600
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_snapshot(target, path)
    assert path.read_bytes() == before
    link = tmp_path / "link.target-snapshot.json"
    link.symlink_to(path)
    with pytest.raises(FileExistsError):
        write_snapshot(target, link)
    assert path.read_bytes() == before


def test_cli_redacts_driver_failures_and_leaves_no_export(rows, tmp_path, monkeypatch, capsys):
    import psycopg

    def fail(**kwargs):
        raise RuntimeError("SERVER_ERROR_PASSWORD=secret")

    monkeypatch.setattr(psycopg, "connect", fail)
    monkeypatch.setenv("ANALYST_OS_DATABASE_URL",
                      f"postgresql://postgres:secret@db.{PROJECT}.supabase.co:5432/postgres")
    ca = tmp_path / "ca.pem"
    ca.write_text("TEST ONLY")
    output = tmp_path / "test.target-snapshot.json"
    monkeypatch.setattr(sys, "argv", ["export", "--expected-project-ref", PROJECT,
                                    "--ssl-root-cert", str(ca), "--output", str(output)])
    assert main() == 1
    assert "secret" not in capsys.readouterr().err
    assert not output.exists()
