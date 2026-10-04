"""TEST ONLY: drive the real publisher through an ephemeral PostgreSQL RPC adapter.

No network credentials, files or production approvals. Parent process owns the test DB.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from analyst_os_ingestion.planning import (
    Review,
    TargetSnapshot,
    build_load_plan,
    digest,
    empty_reviews,
)
from analyst_os_ingestion.publishing import PublishError, prepare_request, preview, publish
from scripts.plan_ril_tcs_load import load_catalog


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class Connection:
    # TEST ONLY: synthetic client transport, never a live TLS attestation.
    pgconn = SimpleNamespace(ssl_in_use=True)
    info = SimpleNamespace(get_parameters=lambda: {"sslmode": "verify-full", "sslrootcert": "test-only-ca.pem"})

    def execute(self, sql, params=None):
        print(json.dumps({"sql": sql, "params": params}, default=str), flush=True)
        result = json.loads(sys.stdin.readline())
        if "error" in result:
            raise RuntimeError(result["error"])
        return Cursor(result["rows"])

    def commit(self):
        self.execute("commit")

    def rollback(self):
        self.execute("rollback")


def run(scenario):
    catalog = load_catalog(Path(__file__).resolve().parents[2])
    reviews = empty_reviews(catalog)
    if scenario != "pending":
        entries = catalog["candidates"] if scenario == "all" else catalog["candidates"][:1]
        for entry in entries:
            approval = Review(
                status="approved",
                reviewer="TEST ONLY SYNTHETIC REVIEW",
                reviewed_at=datetime(2020, 1, 1, tzinfo=UTC),
                rationale="Ephemeral publisher verification; not a human decision",
            )
            reviews.sources[entry["source_key"]] = approval
            reviews.facts[entry["observation"]["observation_id"]] = approval
    target = TargetSnapshot(
        project_ref="abcdefghijklmnopqrst",
        captured_at=datetime.now(UTC),
        complete=True,
        company_slugs=["reliance-industries", "tcs"],
        sources=[],
        facts=[],
    )
    plan = build_load_plan(catalog, reviews, target=target, expected_project_ref=target.project_ref)
    request = prepare_request(
        catalog,
        reviews,
        target,
        plan,
        expected_plan_sha256=digest(plan),
        project_ref=target.project_ref,
    )
    connection = Connection()
    dry = preview(connection, request)
    if scenario in {"pending", "preview"}:
        return {
            "dry_run": dry["mode"],
            "writes": dry["production_writes"],
            "selected": len(dry["selected"]),
        }
    schema_sha = "0" * 64 if scenario == "schema_mismatch" else dry["schema_sha256"]
    if scenario == "commit_unknown":
        try:
            publish(connection, request, expected_schema_sha256=schema_sha)
        except PublishError as error:
            if "outcome uncertain" not in str(error):
                raise
            # Inspect the durable receipt first; then exercise the SAME request replay.
            row = connection.execute(
                "select count(*)::integer as n from ingestion.load_receipts"
            ).fetchone()
            assert row["n"] == 1
        else:
            raise AssertionError("expected simulated lost COMMIT response")
        result = publish(connection, request, expected_schema_sha256=schema_sha)
        assert result["replayed"]
        return {"recovered": True, "inserted": len(result["receipt"]["inserted"])}
    result = publish(connection, request, expected_schema_sha256=schema_sha)
    again = publish(connection, request, expected_schema_sha256=schema_sha)
    assert again["replayed"] and again["receipt_sha256"] == result["receipt_sha256"]
    return {
        "inserted": len(result["receipt"]["inserted"]),
        "replayed": again["replayed"],
        "receipt_sha256": result["receipt_sha256"],
    }


if __name__ == "__main__":
    try:
        outcome = run(sys.argv[1])
        print(json.dumps({"result": outcome}), flush=True)
    except Exception as error:
        print(json.dumps({"result": {"error": str(error)}}), flush=True)
