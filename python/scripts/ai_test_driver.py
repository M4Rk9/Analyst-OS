"""TEST ONLY: real AI publisher over synthetic ephemeral PostgreSQL transport."""

import json
import sys
from contextlib import redirect_stdout

from analyst_os_ai.publishing import (
    begin,
    contract,
    inspect_receipt,
    preview,
    publish,
    source_record,
)
from analyst_os_ai.review import review_template
from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.publishing import canonical
from scripts.publisher_test_driver import PROTOCOL_STDOUT, Connection
from scripts.publisher_test_driver import run as load_source


def run(scenario):
    load_source("one")
    db = Connection()
    source_id = db.execute("select id::text from public.source_documents limit 1").fetchone()["id"]
    begin(db)
    source = source_record(db, source_id)
    db.rollback()
    quote = "TEST ONLY synthetic extracted text for ephemeral AI publication tests."
    draft = {
        "version": 1,
        "source": source,
        "model_digest": "b" * 64,
        "pages": [{"page": 1, "text": quote}],
        "bundle": {
            "company_slug": source["company_slug"],
            "model_name": "test-only:1",
            "insights": [
                {
                    "section": "business_brief",
                    "title": "TEST ONLY draft",
                    "text": "TEST ONLY synthetic interpretation.",
                    "confidence": "low",
                    "evidence": [{"source_url": source["source_url"], "page": 1, "quote": quote}],
                }
            ],
        },
    }
    review = review_template(draft)
    review["decisions"]["0"] = {
        "status": "approved",
        "reviewer": "TEST ONLY",
        "reviewed_at": "2020-01-01T00:00:00Z",
        "rationale": "Synthetic ephemeral approval; never production",
    }
    payload, sha = contract(draft, review, "abcdefghijklmnopqrst")
    if scenario in {"pending_guard", "quote_guard"}:
        # TEST ONLY: bypass the Python review boundary to challenge the SQL guard.
        if scenario == "pending_guard":
            payload["review"]["decisions"]["0"]["status"] = "pending"
        else:
            bad = "TEST ONLY quotation which never occurs on this extracted page."
            payload["draft"]["bundle"]["insights"][0]["evidence"][0]["quote"] = bad
            payload["rows"][0]["evidence"][0]["quote"] = bad
        payload["review"]["draft_sha256"] = digest(payload["draft"])
        payload["draft_canonical_json"] = canonical(payload["draft"])
        payload["review_canonical_json"] = canonical(payload["review"])
        payload["rows"][0]["review_sha256"] = digest(payload["review"])
        sha = digest(payload)
    plan, _ = preview(db, payload, sha)
    if scenario == "preview":
        return {"plan": plan}
    if scenario == "source_changed":
        db.execute(
            "update public.financial_facts set quality_status='unverified',is_preferred=false"
        )
        db.execute(
            "update public.source_documents set verification_status='pending' where id=%s",
            (source_id,),
        )
    kwargs = {
        "expected_plan_sha256": "0" * 64 if scenario == "plan_changed" else digest(plan),
        "expected_schema_sha256": "0" * 64
        if scenario == "schema_changed"
        else plan["schema_sha256"],
    }
    if scenario == "commit_unknown":
        try:
            publish(db, payload, sha, plan, **kwargs)
        except Exception as error:
            if "outcome uncertain" not in str(error):
                raise
            import_id = db.execute("select import_id::text from insights.load_receipts").fetchone()
            assert inspect_receipt(db, import_id["import_id"])["verified"]
        else:
            raise AssertionError("expected synthetic lost commit response")
    result = publish(db, payload, sha, plan, **kwargs)
    replay = publish(db, payload, sha, plan, **kwargs)
    assert replay["replayed"] and replay["receipt_sha256"] == result["receipt_sha256"]
    recovered = inspect_receipt(db, result["receipt"]["import_id"])
    assert recovered["verified"]
    return {"receipt": result["receipt"], "replayed": replay["replayed"]}


if __name__ == "__main__":
    try:
        with redirect_stdout(sys.stderr):
            outcome = run(sys.argv[1])
    except Exception as error:
        outcome = {"error": str(error)}
    print(json.dumps({"result": outcome}), file=PROTOCOL_STDOUT, flush=True)
