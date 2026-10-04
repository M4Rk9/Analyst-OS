"""TEST ONLY: real publishers and SQL through the ephemeral PostgreSQL adapter."""

import json
import sys
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from analyst_os_analytics.preview import build_analytics_preview
from analyst_os_analytics.publishing import inspect_receipt, prepare_request, preview, publish
from analyst_os_ingestion import publishing as source
from analyst_os_ingestion.planning import (
    Review,
    ReviewLedger,
    build_load_plan,
    digest,
    empty_reviews,
)
from analyst_os_ingestion.snapshot import collect_snapshot
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as universe_catalog
from scripts.publisher_test_driver import PROTOCOL_STDOUT, Connection

PROJECT = "abcdefghijklmnopqrst"


def load_selected(connection, catalog, reviews, scope):
    target = collect_snapshot(connection, project_ref=PROJECT, scope=scope)
    plan = build_load_plan(catalog, reviews, target=target, expected_project_ref=PROJECT)
    request = source.prepare_request(
        catalog, reviews, target, plan, expected_plan_sha256=digest(plan), project_ref=PROJECT
    )
    dry = source.preview(connection, request)
    return source.publish(connection, request, expected_schema_sha256=dry["schema_sha256"])


def run(scenario):
    connection = Connection()
    repo = Path(__file__).resolve().parents[2]
    packets = []
    for loader, path in (
        (load_catalog, "data/m2/ril-tcs/review/marky_approved_reviews.json"),
        (universe_catalog, "data/m2/universe/marky_approved_reviews.json"),
    ):
        catalog = loader(repo)
        reviews = ReviewLedger.model_validate(read_json(repo / path))
        # Preserve the actual selected observation set; synthetic test reviewer.
        synthetic = Review(
            status="approved",
            reviewer="TEST ONLY SYNTHETIC REVIEW",
            reviewed_at=datetime(2020, 1, 1, tzinfo=UTC),
            rationale="Ephemeral analytics test; not a production approval",
        )
        for entries in (reviews.sources, reviews.facts):
            for key, review in entries.items():
                if review.status == "approved":
                    entries[key] = synthetic
        scope = sorted({o["company_slug"] for o in catalog["payload"]["observations"]})
        if scenario.startswith("staged") and loader is load_catalog:
            original = empty_reviews(catalog)
            pnl_codes = {
                "revenue",
                "other_income",
                "total_income",
                "total_expenses",
                "finance_costs",
                "profit_for_year",
            }
            for entry in catalog["candidates"]:
                o = entry["observation"]
                if (
                    o["metric_code"] in pnl_codes
                    and reviews.facts[o["observation_id"]].status == "approved"
                ):
                    original.facts[o["observation_id"]] = synthetic
                    original.sources[entry["source_key"]] = synthetic
            first = load_selected(connection, catalog, original, scope)
            assert len(first["receipt"]["inserted"]) == 56
        load_selected(connection, catalog, reviews, scope)
        packets.append((catalog, reviews))
    scope = sorted({o["company_slug"] for c, _ in packets for o in c["payload"]["observations"]})
    target = collect_snapshot(connection, project_ref=PROJECT, scope=scope)
    reviewed = build_analytics_preview(packets, target, project_ref=PROJECT)
    request = prepare_request(
        packets, target, reviewed, project_ref=PROJECT, expected_preview_sha256=digest(reviewed)
    )
    if scenario in {"staged_unselected_fact", "staged_unselected_source", "staged_wrong_catalog"}:
        # TEST ONLY hostile request: native evidence remains unchanged, but its
        # publication binding selects a different canonical ledger/catalog.
        catalog, reviews = packets[0]
        other = reviews.model_copy(deep=True)
        e = next(
            e
            for e in catalog["candidates"]
            if e["observation"]["metric_code"] == "profit_for_year"
            and other.facts[e["observation"]["observation_id"]].status == "approved"
        )
        if scenario == "staged_unselected_fact":
            other.facts[e["observation"]["observation_id"]] = Review(status="pending")
        else:
            other.sources[e["source_key"]] = Review(status="pending")
        payload = other.model_dump(mode="json")
        connection.execute(
            source.INSERT_LEDGER_SQL,
            (digest(payload), catalog["sha256"], source.canonical(payload)),
        )
        request["identity"] = deepcopy(request["identity"])
        request["identity"]["packet_bindings"][0]["review_ledger_sha256"] = digest(payload)
        if scenario == "staged_wrong_catalog":
            request["identity"]["packet_bindings"][0] = request["identity"]["packet_bindings"][1]
        request["request_sha256"] = digest(request["identity"])
    plan, _ = preview(connection, request)
    if scenario == "preview":
        return {"plan": plan}
    if scenario == "preview_tamper":
        reviewed["calculations"][0]["value"] = "42"
        prepare_request(
            packets, target, reviewed, project_ref=PROJECT, expected_preview_sha256=digest(reviewed)
        )
        raise AssertionError("tampered preview accepted")
    kwargs = {
        "expected_plan_sha256": digest(plan),
        "expected_schema_sha256": "0" * 64
        if scenario == "schema_mismatch"
        else plan["schema_sha256"],
    }
    if scenario == "commit_unknown":
        try:
            publish(connection, request, plan, **kwargs)
        except source.PublishError as error:
            if "outcome uncertain" not in str(error):
                raise
            row = connection.execute(
                "select count(*)::integer as n from analytics.load_receipts"
            ).fetchone()
            assert row["n"] == 1
        else:
            raise AssertionError("expected uncertain COMMIT")
    result = publish(connection, request, plan, **kwargs)
    replay = publish(connection, request, plan, **kwargs)
    assert replay["replayed"] and replay["receipt_sha256"] == result["receipt_sha256"]
    inspected = inspect_receipt(connection, result["receipt"]["import_id"], project_ref=PROJECT)
    assert inspected["verified"] and inspected["receipt_sha256"] == result["receipt_sha256"]
    return {
        "metrics": len(result["receipt"]["inserted_metrics"]),
        "flags": len(result["receipt"]["inserted_flags"]),
        "unavailable": plan["unavailable"],
        "replayed": replay["replayed"],
    }


if __name__ == "__main__":
    try:
        with redirect_stdout(sys.stderr):
            result = run(sys.argv[1])
        print(json.dumps({"result": result}), file=PROTOCOL_STDOUT, flush=True)
    except Exception as error:
        print(json.dumps({"result": {"error": str(error)}}), file=PROTOCOL_STDOUT, flush=True)
