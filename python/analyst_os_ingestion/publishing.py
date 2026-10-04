"""Reviewed insert-only publishing. Never approve evidence or overwrite target history."""

import json
from uuid import uuid4

from .planning import ReviewLedger, TargetSnapshot, build_catalog, build_load_plan, digest
from .snapshot import CONTEXT_SQL, SETTINGS_SQL, SnapshotError, client_tls_verified, read_snapshot

PUBLIC_TABLES = (
    "ai_insights",
    "calculated_metrics",
    "companies",
    "financial_facts",
    "red_flags",
    "reporting_periods",
    "source_documents",
)
PRIVATE_TABLES = (
    "evidence_catalogs",
    "fact_provenance",
    "load_receipts",
    "review_ledgers",
    "source_provenance",
)
LOCK_SQL = (
    "lock table "
    + ", ".join(["ingestion." + t for t in PRIVATE_TABLES] + ["public." + t for t in PUBLIC_TABLES])
    + " in share row exclusive mode"
)
SCHEMA_SQL = """
select jsonb_build_object(
 'tables', (select jsonb_agg(jsonb_build_object(
    'schema',n.nspname,'table',c.relname,'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,
    'owner',pg_get_userbyid(c.relowner),'acl',c.relacl::text,
    'browser_select',has_table_privilege('anon',c.oid,'SELECT')
        and has_table_privilege('authenticated',c.oid,'SELECT'),
    'browser_select_any',has_table_privilege('anon',c.oid,'SELECT')
        or has_table_privilege('authenticated',c.oid,'SELECT'),
    'browser_write',has_table_privilege('anon',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE')
        or has_table_privilege('authenticated',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE'),
    'constraints',(select coalesce(jsonb_agg(jsonb_build_object('name',x.conname,
        'definition',pg_get_constraintdef(x.oid),'valid',x.convalidated) order by x.conname),'[]')
        from pg_constraint x where x.conrelid=c.oid),
    'indexes',(select coalesce(jsonb_agg(jsonb_build_object('name',ci.relname,
        'definition',pg_get_indexdef(i.indexrelid),'valid',i.indisvalid) order by ci.relname),'[]')
        from pg_index i join pg_class ci on ci.oid=i.indexrelid where i.indrelid=c.oid),
    'triggers',(select coalesce(jsonb_agg(jsonb_build_object('name',t.tgname,
        'definition',pg_get_triggerdef(t.oid),'enabled',t.tgenabled) order by t.tgname),'[]')
        from pg_trigger t where t.tgrelid=c.oid and not t.tgisinternal),
    'policies',(select coalesce(jsonb_agg(jsonb_build_object('name',p.polname,'command',p.polcmd,
        'roles',(select jsonb_agg(coalesce(r.rolname,'PUBLIC') order by role_id)
                 from unnest(p.polroles) role_id left join pg_roles r on r.oid=role_id),
        'using',pg_get_expr(p.polqual,p.polrelid)) order by p.polname),'[]')
        from pg_policy p where p.polrelid=c.oid),
    'defaults',(select coalesce(jsonb_agg(jsonb_build_object('column',a.attname,
        'expression',pg_get_expr(d.adbin,d.adrelid)) order by a.attname),'[]')
        from pg_attrdef d join pg_attribute a on a.attrelid=d.adrelid and a.attnum=d.adnum
        where d.adrelid=c.oid)
 ) order by n.nspname,c.relname) from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where c.relkind='r' and (n.nspname='public' and c.relname=any(%s)
    or n.nspname='ingestion' and c.relname=any(%s))),
 'private_browser_usage',has_schema_privilege('anon','ingestion','USAGE')
    or has_schema_privilege('authenticated','ingestion','USAGE'),
 'functions',(select jsonb_agg(jsonb_build_object('name',p.proname,
    'definition',pg_get_functiondef(p.oid),'definer',p.prosecdef,
    'browser_execute',has_function_privilege('anon',p.oid,'EXECUTE')
        or has_function_privilege('authenticated',p.oid,'EXECUTE')) order by p.proname)
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='ingestion')
) as inventory
"""
INSERT_CATALOG_SQL = """insert into ingestion.evidence_catalogs(catalog_sha256,canonical_json)
 values (%s,%s) on conflict do nothing"""
INSERT_LEDGER_SQL = """insert into ingestion.review_ledgers
 (review_ledger_sha256,catalog_sha256,canonical_json) values (%s,%s,%s) on conflict do nothing"""
SELECT_PERIOD_SQL = """select id::text,period_start::text,currency,published_at::text
 from public.reporting_periods where company_id=%s and period_type=%s
 and fiscal_year=%s and period_end=%s"""
INSERT_PERIOD_SQL = """insert into public.reporting_periods
 (company_id,period_type,fiscal_year,period_start,period_end,currency)
 values (%s,%s,%s,%s,%s,%s) returning id::text"""
SELECT_SOURCE_SQL = """select id::text,title,document_type,publisher,fiscal_year,
 sha256,page_count,verification_status,published_at::text,fiscal_quarter
 from public.source_documents where company_id=%s and source_url=%s"""
INSERT_SOURCE_SQL = """insert into public.source_documents
 (company_id,title,document_type,fiscal_year,source_url,publisher,sha256,page_count,verification_status)
 values (%s,%s,%s,%s,%s,%s,%s,%s,'verified') returning id::text"""
INSERT_FACT_SQL = """insert into public.financial_facts
 (company_id,reporting_period_id,metric_code,raw_value_text,raw_value,normalized_value,
 currency,unit_scale,source_document_id,source_page,source_label,quality_status,is_preferred)
 values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'verified',true) returning id::text"""
INSERT_SOURCE_PROOF_SQL = """insert into ingestion.source_provenance
 (source_document_id,catalog_sha256,review_ledger_sha256)
 values (%s,%s,%s) on conflict do nothing"""
INSERT_FACT_PROOF_SQL = """insert into ingestion.fact_provenance
 (fact_id,source_document_id,catalog_sha256,review_ledger_sha256,observation_id,evidence_sha256,
 definition_sha256,evidence_canonical_json,definition_canonical_json)
 values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
SELECT_RECEIPT_SQL = """select canonical_json,receipt_sha256 from ingestion.load_receipts
 where request_sha256=%s"""
INSERT_RECEIPT_SQL = """insert into ingestion.load_receipts
 (import_id,request_sha256,project_ref,receipt_sha256,canonical_json) values (%s,%s,%s,%s,%s)"""


class PublishError(SnapshotError):
    """Safe actionable error; no financial amounts or credentials."""


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def prepare_request(
    catalog: dict,
    reviews: ReviewLedger,
    target: TargetSnapshot,
    reviewed_plan: dict,
    *,
    expected_plan_sha256: str,
    project_ref: str,
    now=None,
) -> dict:
    payload = catalog["payload"]
    checked = build_catalog(
        payload["observations"],
        payload["definitions"],
        payload["source_manifest"],
        set(payload["fiscal_years"]),
    )
    if checked["sha256"] != catalog["sha256"]:
        raise PublishError("catalog digest mismatch")
    plan = build_load_plan(
        checked, reviews, target=target, expected_project_ref=project_ref, now=now
    )
    if plan != reviewed_plan or digest(plan) != expected_plan_sha256:
        raise PublishError("reviewed plan does not match evidence, reviews and target snapshot")
    selected = sorted(p["observation_id"] for p in plan["proposed_facts"] + plan["already_present"])
    ledger = reviews.model_dump(mode="json")
    identity = {
        "project_ref": project_ref,
        "catalog_sha256": checked["sha256"],
        "review_ledger_sha256": digest(ledger),
        "reviewed_plan_sha256": digest(plan),
        "selected": selected,
    }
    return {
        **identity,
        "request_sha256": digest(identity),
        "catalog": checked,
        "reviews": reviews,
        "ledger": ledger,
        "original_plan": plan,
        "original_plan_scope": target.company_slugs,
    }


def schema_inventory(connection) -> tuple[dict, str]:
    inventory = connection.execute(
        SCHEMA_SQL, (list(PUBLIC_TABLES), list(PRIVATE_TABLES))
    ).fetchone()["inventory"]
    tables = inventory["tables"] or []
    if len(tables) != len(PUBLIC_TABLES) + len(PRIVATE_TABLES):
        raise PublishError("required migration tables are missing")
    if inventory["private_browser_usage"]:
        raise PublishError("private ingestion schema is accessible to browser roles")
    for t in tables:
        if (
            not t["rls"]
            or t["browser_write"]
            or (t["schema"] == "ingestion" and t["browser_select_any"])
        ):
            raise PublishError("unsafe table grants or missing RLS")
        if t["schema"] == "public" and not t["browser_select"]:
            raise PublishError("expected browser read grants are missing")
        if any(not c["valid"] for c in t["constraints"] + t["indexes"]):
            raise PublishError("unvalidated target integrity constraints")
        if any(p["command"] != "r" for p in t["policies"]):
            raise PublishError("unexpected target write policy")
        if any(trigger["enabled"] not in {"O", "A"} for trigger in t["triggers"]):
            raise PublishError("disabled target integrity trigger")
    functions = inventory["functions"] or []
    if len(functions) != 5 or any(f["definer"] or f["browser_execute"] for f in functions):
        raise PublishError("unexpected private function definitions or grants")
    facts = next(t for t in tables if t["table"] == "financial_facts")
    required = {
        "facts_exact_normalization",
        "facts_finite_values",
        "facts_preferred_verified",
        "facts_same_company_period",
        "facts_same_company_source",
    }
    if not required <= {c["name"] for c in facts["constraints"]}:
        raise PublishError("financial integrity constraints are missing")
    if "financial_facts_one_preferred" not in {i["name"] for i in facts["indexes"]}:
        raise PublishError("preferred-fact uniqueness is missing")
    if not any(
        d["column"] == "quality_status" and "'unverified'" in d["expression"]
        for d in facts["defaults"]
    ):
        raise PublishError("financial facts do not default to unverified")
    expected_triggers = {
        "facts_reviewed_publication",
        "sources_reviewed_publication",
        "periods_reviewed_publication",
        "companies_reviewed_publication",
        "catalogs_immutable",
        "ledgers_immutable",
        "source_provenance_immutable",
        "fact_provenance_immutable",
        "load_receipts_immutable",
    }
    if not expected_triggers <= {x["name"] for t in tables for x in t["triggers"]}:
        raise PublishError("required provenance or publication triggers are missing")
    return inventory, digest(inventory)


def _context(connection, *, apply: bool) -> dict:
    c = connection.execute(CONTEXT_SQL).fetchone()
    if not (
        c["privileged"] is True
        and client_tls_verified(connection)
        and c["database_name"] == "postgres"
        and c["row_security"] == "off"
        and c["read_only"] == ("off" if apply else "on")
        and c["isolation"] == ("read committed" if apply else "repeatable read")
    ):
        raise PublishError("unsafe privileged publishing session")
    return c


def _fresh_plan(connection, request: dict, context: dict) -> tuple[TargetSnapshot, dict]:
    target = read_snapshot(
        connection,
        project_ref=request["project_ref"],
        scope=request["original_plan_scope"],
        captured_at=context["captured_at"],
    )
    plan = build_load_plan(
        request["catalog"],
        request["reviews"],
        target=target,
        expected_project_ref=request["project_ref"],
    )
    eligible = {p["observation_id"] for p in plan["proposed_facts"] + plan["already_present"]}
    if not set(request["selected"]) <= eligible:
        raise PublishError("fresh target conflicts with the reviewed selection; review a new plan")
    return target, plan


def preview(connection, request: dict) -> dict:
    try:
        connection.execute("begin isolation level repeatable read read only")
        for sql in SETTINGS_SQL:
            connection.execute(sql)
        context = _context(connection, apply=False)
        inventory, sha = schema_inventory(connection)
        target, plan = _fresh_plan(connection, request, context)
        return {
            "mode": "dry_run",
            "production_writes": 0,
            "schema_sha256": sha,
            "schema_inventory": inventory,
            "fresh_snapshot_sha256": digest(target.model_dump(mode="json")),
            "selected": request["selected"],
            "fresh_summary": plan["summary"],
        }
    finally:
        connection.rollback()


def _period(connection, company_id: str, o: dict) -> str:
    key = (company_id, o["period_type"], o["fiscal_year"], o["period_end"])
    row = connection.execute(SELECT_PERIOD_SQL, key).fetchone()
    if row:
        if (row["period_start"], row["currency"], row["published_at"]) != (
            o["period_start"],
            o["currency"],
            None,
        ):
            raise PublishError("existing reporting period requires review")
        return row["id"]
    return connection.execute(
        INSERT_PERIOD_SQL,
        (
            company_id,
            o["period_type"],
            o["fiscal_year"],
            o["period_start"],
            o["period_end"],
            o["currency"],
        ),
    ).fetchone()["id"]


def _source(connection, company_id: str, o: dict, manifest: dict) -> str:
    row = connection.execute(SELECT_SOURCE_SQL, (company_id, o["source_url"])).fetchone()
    if row:
        if tuple(
            row[k]
            for k in (
                "title",
                "document_type",
                "publisher",
                "fiscal_year",
                "sha256",
                "page_count",
                "verification_status",
                "published_at",
                "fiscal_quarter",
            )
        ) != (
            o["source_title"],
            o["source_document_type"],
            o["source_publisher"],
            o["source_fiscal_year"],
            o["source_sha256"],
            manifest["page_count"],
            "verified",
            None,
            None,
        ):
            raise PublishError("existing source metadata requires review")
        return row["id"]
    return connection.execute(
        INSERT_SOURCE_SQL,
        (
            company_id,
            o["source_title"],
            o["source_document_type"],
            o["source_fiscal_year"],
            o["source_url"],
            o["source_publisher"],
            o["source_sha256"],
            manifest["page_count"],
        ),
    ).fetchone()["id"]


def publish(connection, request: dict, *, expected_schema_sha256: str) -> dict:
    if not request["selected"]:
        raise PublishError("no approved target-ready selection; nothing may be published")
    import_id = str(uuid4())
    commit_started = False
    try:
        connection.execute("begin isolation level read committed read write")
        for sql in SETTINGS_SQL:
            connection.execute(sql)
        connection.execute("set local lock_timeout = '5s'")
        connection.execute(LOCK_SQL)
        context = _context(connection, apply=True)
        _, schema_sha = schema_inventory(connection)
        if schema_sha != expected_schema_sha256:
            raise PublishError("target schema differs from the reviewed schema hash")
        before, plan = _fresh_plan(connection, request, context)
        prior = connection.execute(SELECT_RECEIPT_SQL, (request["request_sha256"],)).fetchone()
        if prior:
            receipt = json.loads(prior["canonical_json"])
            if (
                digest(receipt) != prior["receipt_sha256"]
                or receipt["project_ref"] != request["project_ref"]
            ):
                raise PublishError("stored receipt integrity mismatch")
            connection.rollback()
            return {"replayed": True, "receipt": receipt, "receipt_sha256": prior["receipt_sha256"]}
        catalog = request["catalog"]
        ledger_sha = request["review_ledger_sha256"]
        connection.execute(INSERT_CATALOG_SQL, (catalog["sha256"], canonical(catalog["payload"])))
        connection.execute(
            INSERT_LEDGER_SQL, (ledger_sha, catalog["sha256"], canonical(request["ledger"]))
        )
        companies = {
            r["slug"]: r["id"]
            for r in connection.execute(
                "select id::text,slug from public.companies where slug=any(%s)",
                (request["original_plan_scope"],),
            ).fetchall()
        }
        manifest = {
            (m["company_slug"], m["report_fiscal_year"]): m
            for m in catalog["payload"]["source_manifest"]
        }
        selected = set(request["selected"])
        inserted = []
        periods, sources = {}, {}
        for proposed in plan["proposed_facts"]:
            if proposed["observation_id"] not in selected:
                continue
            e = proposed["provenance"]
            o = e["observation"]
            company_id = companies[o["company_slug"]]
            period_key = (company_id, o["period_type"], o["fiscal_year"], o["period_end"])
            if period_key not in periods:
                periods[period_key] = _period(connection, company_id, o)
            period_id = periods[period_key]
            source_key = (company_id, o["source_url"])
            if source_key not in sources:
                sources[source_key] = _source(
                    connection,
                    company_id,
                    o,
                    manifest[(o["company_slug"], o["source_fiscal_year"])],
                )
                connection.execute(
                    INSERT_SOURCE_PROOF_SQL, (sources[source_key], catalog["sha256"], ledger_sha)
                )
            source_id = sources[source_key]
            fact_id = connection.execute(
                INSERT_FACT_SQL,
                (
                    company_id,
                    period_id,
                    o["metric_code"],
                    o["raw_value_text"],
                    o["raw_value"],
                    o["normalized_value"],
                    o["currency"],
                    o["unit_scale"],
                    source_id,
                    o["source_page"],
                    o["source_label"],
                ),
            ).fetchone()["id"]
            connection.execute(
                INSERT_FACT_PROOF_SQL,
                (
                    fact_id,
                    source_id,
                    catalog["sha256"],
                    ledger_sha,
                    o["observation_id"],
                    e["evidence_sha256"],
                    e["definition_sha256"],
                    canonical(o),
                    canonical(e["definition"]),
                ),
            )
            inserted.append(
                {
                    "observation_id": o["observation_id"],
                    "fact_id": fact_id,
                    "source_document_id": source_id,
                    "reporting_period_id": period_id,
                    "evidence_sha256": e["evidence_sha256"],
                    "definition_sha256": e["definition_sha256"],
                }
            )
        connection.execute("set constraints all immediate")
        after = read_snapshot(
            connection,
            project_ref=request["project_ref"],
            scope=request["original_plan_scope"],
            captured_at=context["captured_at"],
        )
        verified = build_load_plan(
            catalog, request["reviews"], target=after, expected_project_ref=request["project_ref"]
        )
        present = {p["observation_id"] for p in verified["already_present"]}
        if not selected <= present:
            raise PublishError("post-insert verification failed")
        receipt = {
            "version": 1,
            "outcome": "committed",
            "import_id": import_id,
            **{
                k: request[k]
                for k in (
                    "request_sha256",
                    "project_ref",
                    "catalog_sha256",
                    "review_ledger_sha256",
                    "reviewed_plan_sha256",
                )
            },
            "schema_sha256": schema_sha,
            "recorded_at": context["captured_at"],
            "before_snapshot_sha256": digest(before.model_dump(mode="json")),
            "after_snapshot_sha256": digest(after.model_dump(mode="json")),
            "inserted": inserted,
            "already_present": [
                p for p in plan["already_present"] if p["observation_id"] in selected
            ],
        }
        receipt_sha = digest(receipt)
        connection.execute(
            INSERT_RECEIPT_SQL,
            (
                import_id,
                request["request_sha256"],
                request["project_ref"],
                receipt_sha,
                canonical(receipt),
            ),
        )
        connection.execute("set constraints all immediate")
        commit_started = True
        connection.commit()
        return {"replayed": False, "receipt": receipt, "receipt_sha256": receipt_sha}
    except BaseException:
        if commit_started:
            raise PublishError(
                f"commit outcome uncertain; inspect receipt import_id={import_id} before retry"
            ) from None
        connection.rollback()
        raise
