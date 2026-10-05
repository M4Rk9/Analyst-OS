"""Native, TLS verified, append-only AI publication with exact review contracts."""

import json
from uuid import UUID, uuid4

from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.publishing import PUBLIC_TABLES, SCHEMA_SQL, _context, canonical
from analyst_os_ingestion.snapshot import SETTINGS_SQL, SnapshotError

from .review import approved_rows

PRIVATE_TABLES = ("publication_requests", "insight_provenance", "load_receipts")
ROW_KEYS = (
    "id",
    "company_id",
    "source_document_id",
    "section",
    "title",
    "insight_text",
    "confidence",
    "evidence",
    "model_name",
    "prompt_version",
    "validation_status",
    "source_sha256",
    "review_sha256",
    "model_digest",
    "candidate_index",
)


def begin(connection, apply=False):
    connection.execute(
        "begin isolation level " + ("read committed" if apply else "repeatable read read only")
    )
    for sql in SETTINGS_SQL:
        connection.execute(sql)
    return _context(connection, apply=apply)


def source_record(connection, source_id):
    UUID(source_id)
    row = connection.execute(
        """select s.id::text,s.company_id::text,
        c.slug as company_slug,s.source_url,s.sha256,s.page_count,s.fiscal_year
        from public.source_documents s join public.companies c on c.id=s.company_id
        where s.id=%s and s.verification_status='verified' and c.is_active""",
        (source_id,),
    ).fetchone()
    if not row:
        raise SnapshotError("source is missing, inactive or unverified")
    # assert_source takes FOR SHARE locks and cannot run in a read-only preview.
    # Inspect the same original source approval without locks; the SQL insert
    # guard rechecks assert_source inside the locked publication transaction.
    proof = connection.execute(
        """select exists(select 1 from ingestion.source_provenance p
        join ingestion.review_ledgers r using(catalog_sha256,review_ledger_sha256)
        join ingestion.evidence_catalogs e using(catalog_sha256)
        join public.source_documents s on s.id=p.source_document_id
        join public.companies c on c.id=s.company_id
        cross join lateral jsonb_array_elements(e.payload->'source_manifest') m
        where s.id=%s and m->>'company_slug'=c.slug and m->>'sha256'=s.sha256
        and m->>'source_url'=s.source_url and m->>'title'=s.title
        and m->>'publisher'=s.publisher and (m->>'report_fiscal_year')::integer=s.fiscal_year
        and (m->>'page_count')::integer=s.page_count and s.document_type='annual_report'
        and s.fiscal_quarter is null and s.published_at is null
        and ingestion.approved_review(r.payload->'sources'->(c.slug||':'||s.sha256)))
        as approved""",
        (source_id,),
    ).fetchone()
    if not proof or not proof["approved"]:
        raise SnapshotError("source lacks matching original reviewed provenance")
    return row


def inventory(connection):
    parts = {}
    for schema, tables in (
        (
            "ingestion",
            (
                "evidence_catalogs",
                "review_ledgers",
                "source_provenance",
                "fact_provenance",
                "load_receipts",
            ),
        ),
        ("insights", PRIVATE_TABLES),
    ):
        parts[schema] = connection.execute(
            SCHEMA_SQL.replace("'ingestion'", "'" + schema + "'"),
            (list(PUBLIC_TABLES), list(tables)),
        ).fetchone()["inventory"]
    part = parts["insights"]
    private = [t for t in part["tables"] if t["schema"] == "insights"]
    if (
        len(private) != 3
        or part["private_browser_usage"]
        or any(not t["rls"] or t["browser_select_any"] or t["browser_write"] for t in private)
    ):
        raise SnapshotError("unsafe AI private schema")
    if len(part["functions"] or []) != 2 or any(
        f["definer"] or f["browser_execute"] for f in part["functions"]
    ):
        raise SnapshotError("unsafe AI publication functions")
    triggers = {
        x["name"] for t in part["tables"] for x in t["triggers"] if x["enabled"] in {"O", "A"}
    }
    if (
        not {
            "ai_reviewed_publication",
            "ai_insights_immutable",
            "ai_proofs_immutable",
            "ai_requests_immutable",
            "ai_receipts_immutable",
        }
        <= triggers
    ):
        raise SnapshotError("missing AI publication guards")
    for table in part["tables"]:
        if any(not x["valid"] for x in table["constraints"] + table["indexes"]):
            raise SnapshotError("unvalidated AI integrity constraint")
    return parts, digest(parts)


def contract(draft, review, project_ref):
    draft, review, rows = approved_rows(draft, review)
    payload = {
        "project_ref": project_ref,
        "draft": draft,
        "review": review,
        "rows": rows,
        "draft_canonical_json": canonical(draft),
        "review_canonical_json": canonical(review),
    }
    return payload, digest(payload)


def existing(connection, rows, request_sha):
    stored = connection.execute(
        "select * from public.ai_insights order by id limit 1001"
    ).fetchall()
    if len(stored) > 1000:
        raise SnapshotError("AI target exceeds bounded publication scope")
    found = []
    for wanted in rows:
        for actual in stored:
            same_key = all(
                str(actual[k]) == str(wanted[k])
                for k in (
                    "company_id",
                    "source_document_id",
                    "section",
                    "title",
                    "model_name",
                    "prompt_version",
                )
            )
            if str(actual["id"]) != wanted["id"] and not same_key:
                continue
            if any(str(actual[k]) != str(wanted[k]) for k in ROW_KEYS if k != "evidence"):
                raise SnapshotError("conflicting AI output; no overwrite permitted")
            if actual["evidence"] != wanted["evidence"]:
                raise SnapshotError("conflicting AI evidence")
            proof = connection.execute(
                """select request_sha256 from insights.insight_provenance
                where insight_id=%s""",
                (wanted["id"],),
            ).fetchone()
            if not proof or proof["request_sha256"] != request_sha:
                raise SnapshotError("AI row lacks the exact review provenance")
            found.append(wanted["id"])
    return sorted(found)


def plan_in_transaction(connection, payload, sha):
    if source_record(connection, payload["draft"]["source"]["id"]) != payload["draft"]["source"]:
        raise SnapshotError("live source differs from the pinned reviewed draft")
    schema, schema_sha = inventory(connection)
    present = existing(connection, payload["rows"], sha)
    return {
        "mode": "dry_run",
        "production_writes": 0,
        "project_ref": payload["project_ref"],
        "request_sha256": sha,
        "draft_sha256": digest(payload["draft"]),
        "review_sha256": digest(payload["review"]),
        "schema_sha256": schema_sha,
        "rows_to_insert": [r for r in payload["rows"] if r["id"] not in present],
        "already_present": present,
    }, schema


def preview(connection, payload, sha):
    try:
        begin(connection)
        result = plan_in_transaction(connection, payload, sha)
        connection.rollback()
        return result
    except BaseException:
        connection.rollback()
        raise


def verify_receipt(connection, row):
    receipt = json.loads(row["canonical_json"])
    if digest(receipt) != row["receipt_sha256"]:
        raise SnapshotError("durable AI receipt hash mismatch")
    request = connection.execute(
        "select canonical_json from insights.publication_requests where request_sha256=%s",
        (receipt["request_sha256"],),
    ).fetchone()
    if not request:
        raise SnapshotError("AI receipt request missing")
    payload = json.loads(request["canonical_json"])
    checked, sha = contract(payload["draft"], payload["review"], payload["project_ref"])
    if checked != payload or sha != receipt["request_sha256"]:
        raise SnapshotError("AI receipt request mismatch")
    if source_record(connection, payload["draft"]["source"]["id"]) != payload["draft"]["source"]:
        raise SnapshotError("AI receipt source no longer verified")
    ids = sorted(r["id"] for r in payload["rows"])
    if existing(connection, payload["rows"], sha) != ids or receipt["insight_ids"] != ids:
        raise SnapshotError("AI receipt does not match committed rows")
    return {"verified": True, "receipt": receipt, "receipt_sha256": row["receipt_sha256"]}


def inspect_receipt(connection, import_id):
    UUID(import_id)
    try:
        begin(connection)
        row = connection.execute(
            "select canonical_json,receipt_sha256 from insights.load_receipts where import_id=%s",
            (import_id,),
        ).fetchone()
        if not row:
            raise SnapshotError("no durable AI receipt for this import id")
        result = verify_receipt(connection, row)
        connection.rollback()
        return result
    except BaseException:
        connection.rollback()
        raise


def publish(
    connection, payload, sha, reviewed_plan, *, expected_plan_sha256, expected_schema_sha256
):
    if digest(reviewed_plan) != expected_plan_sha256:
        raise SnapshotError("reviewed AI plan hash mismatch")
    import_id = str(uuid4())
    commit_started = False
    try:
        context = begin(connection, apply=True)
        connection.execute("set local lock_timeout='5s'")
        connection.execute(
            "lock table public.companies,public.source_documents,public.ai_insights,"
            "ingestion.source_provenance,ingestion.review_ledgers,"
            "ingestion.evidence_catalogs,insights.publication_requests,"
            "insights.insight_provenance,insights.load_receipts "
            "in share row exclusive mode"
        )
        plan, _ = plan_in_transaction(connection, payload, sha)
        if plan["schema_sha256"] != expected_schema_sha256:
            raise SnapshotError("reviewed AI schema hash changed")
        prior = connection.execute(
            "select canonical_json,receipt_sha256 from insights.load_receipts "
            "where request_sha256=%s",
            (sha,),
        ).fetchone()
        if prior:
            result = verify_receipt(connection, prior)
            connection.rollback()
            return {"replayed": True, **result}
        if plan != reviewed_plan:
            raise SnapshotError("fresh AI plan changed; review a new preview")
        connection.execute(
            "insert into insights.publication_requests(request_sha256,canonical_json) "
            "values (%s,%s)",
            (sha, canonical(payload)),
        )
        for row in plan["rows_to_insert"]:
            values = [canonical(row[k]) if k == "evidence" else row[k] for k in ROW_KEYS]
            connection.execute(
                """insert into public.ai_insights
                (id,company_id,source_document_id,section,title,insight_text,confidence,evidence,
                 model_name,prompt_version,validation_status,source_sha256,review_sha256,
                 model_digest,candidate_index)
                values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)""",
                values,
            )
            connection.execute(
                "insert into insights.insight_provenance(insight_id,request_sha256) values (%s,%s)",
                (row["id"], sha),
            )
        connection.execute("set constraints all immediate")
        ids = sorted(r["id"] for r in payload["rows"])
        if existing(connection, payload["rows"], sha) != ids:
            raise SnapshotError("AI post-load verification failed")
        receipt = {
            "version": 1,
            "outcome": "committed",
            "project_ref": payload["project_ref"],
            "import_id": import_id,
            "request_sha256": sha,
            "schema_sha256": expected_schema_sha256,
            "plan_sha256": expected_plan_sha256,
            "insight_ids": ids,
            "recorded_at": context["captured_at"],
        }
        receipt_sha = digest(receipt)
        connection.execute(
            """insert into insights.load_receipts
            (request_sha256,import_id,receipt_sha256,canonical_json) values (%s,%s,%s,%s)""",
            (sha, import_id, receipt_sha, canonical(receipt)),
        )
        commit_started = True
        connection.commit()
        return {"replayed": False, "receipt": receipt, "receipt_sha256": receipt_sha}
    except BaseException:
        if commit_started:
            raise SnapshotError(
                f"AI COMMIT outcome uncertain; recover receipt import_id={import_id}"
            ) from None
        connection.rollback()
        raise
