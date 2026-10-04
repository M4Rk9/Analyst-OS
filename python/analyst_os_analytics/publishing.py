"""Atomic, insert-only publication of the reviewed reported-input policy.

The database independently checks arithmetic and input approval provenance.
Unavailable calculations never become rows. Nothing here approves source facts.
"""

import json
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid4, uuid5

from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.publishing import (
    LOCK_SQL,
    PUBLIC_TABLES,
    SCHEMA_SQL,
    PublishError,
    _context,
    canonical,
)
from analyst_os_ingestion.publishing import (
    schema_inventory as source_schema_inventory,
)
from analyst_os_ingestion.snapshot import SETTINGS_SQL, read_snapshot

from .preview import build_analytics_preview

PRIVATE_TABLES = ("publication_requests", "metric_provenance", "flag_provenance", "load_receipts")
TITLE = "Operating cash flow is below reported group profit"
DESCRIPTION = (
    "CFO / reported consolidated group profit is below 0.7; investigate earnings-to-cash "
    "conversion. This is an investigation signal, not an investment recommendation."
)
FUNCTIONS_SQL = """select jsonb_agg(jsonb_build_object('name',p.proname,
 'definition',pg_get_functiondef(p.oid),'definer',p.prosecdef,'acl',p.proacl::text)
 order by p.proname) as functions from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname=any(%s)"""


def schema_inventory(connection):
    base, _ = source_schema_inventory(connection)
    derived = connection.execute(
        SCHEMA_SQL.replace("'ingestion'", "'analytics'"),
        (list(PUBLIC_TABLES), list(PRIVATE_TABLES)),
    ).fetchone()["inventory"]
    if derived["private_browser_usage"]:
        raise PublishError("private analytics schema is accessible to browser roles")
    private = [t for t in derived["tables"] or [] if t["schema"] == "analytics"]
    if len(private) != len(PRIVATE_TABLES) or any(
        not t["rls"] or t["browser_select_any"] or t["browser_write"] for t in private
    ):
        raise PublishError("missing or unsafe analytics provenance tables")
    if len(derived["functions"] or []) != 2 or any(
        f["definer"] or f["browser_execute"] for f in derived["functions"]
    ):
        raise PublishError("unsafe analytics function definitions or grants")
    for t in derived["tables"]:
        if any(not c["valid"] for c in t["constraints"] + t["indexes"]):
            raise PublishError("unvalidated analytics integrity constraints")
        if any(x["enabled"] not in {"O", "A"} for x in t["triggers"]):
            raise PublishError("disabled analytics integrity trigger")
    required = {
        "requests_immutable",
        "metric_provenance_immutable",
        "flag_provenance_immutable",
        "analytics_receipts_immutable",
        "metrics_immutable",
        "flags_immutable",
        "metrics_reviewed_publication",
        "flags_reviewed_publication",
    }
    if not required <= {x["name"] for t in derived["tables"] for x in t["triggers"]}:
        raise PublishError("analytics publication guards are missing")
    helpers = connection.execute(
        FUNCTIONS_SQL,
        (
            [
                "reported_decimal_quotient",
                "reported_metric_is_valid",
                "reported_flag_is_valid",
            ],
        ),
    ).fetchone()["functions"]
    if len(helpers or []) != 3 or any(f["definer"] for f in helpers):
        raise PublishError("analytics read guards are missing or elevated")
    for name, helper in (
        ("calculated_metrics", "reported_metric_is_valid"),
        ("red_flags", "reported_flag_is_valid"),
    ):
        table = next(t for t in derived["tables"] if t["table"] == name and t["schema"] == "public")
        if len(table["policies"]) != 1 or helper not in (table["policies"][0]["using"] or ""):
            raise PublishError("analytics read policy does not validate its inputs")
    inventory = {"source": base, "derived": derived, "read_helpers": helpers}
    return inventory, digest(inventory)


def prepare_request(
    packets, target, reviewed_preview, *, project_ref, expected_preview_sha256, now=None
):
    preview = build_analytics_preview(packets, target, project_ref=project_ref, now=now)
    # A native preview also binds the schema inspected at capture time.
    checked = {k: v for k, v in reviewed_preview.items() if k != "schema_sha256"}
    if preview != checked or digest(reviewed_preview) != expected_preview_sha256:
        raise PublishError("analytics preview does not match approved evidence and target snapshot")
    identity = {
        "project_ref": project_ref,
        "reviewed_preview_sha256": expected_preview_sha256,
        "policy_version": preview["policy_version"],
        "formula_version": preview["formula_version"],
        "packet_bindings": preview["packet_bindings"],
        "calculations": [c for c in preview["calculations"] if c["status"] == "available"],
    }
    if not identity["calculations"]:
        raise PublishError("no supported calculations to publish")
    return {
        "identity": identity,
        "request_sha256": digest(identity),
        "packets": packets,
        "scope": target.company_slugs,
        "preview": preview,
    }


def _rows(connection, request):
    metrics = []
    periods = connection.execute(
        """select c.id::text as company_id,c.slug,
        p.id::text as reporting_period_id,p.fiscal_year from public.companies c
        join public.reporting_periods p on p.company_id=c.id
        where c.slug=any(%s) and p.period_type='FY'""",
        (request["scope"],),
    ).fetchall()
    keys = {(p["slug"], p["fiscal_year"]): p for p in periods}
    flags = []
    for c in request["identity"]["calculations"]:
        p = keys[(c["company_slug"], c["fiscal_year"])]
        identifier = (
            f"analyst-os:reported-core-1:1.0:{c['company_slug']}:"
            f"{c['fiscal_year']}:{c['metric_code']}"
        )
        m = {
            "id": str(uuid5(NAMESPACE_URL, identifier)),
            "company_id": p["company_id"],
            "reporting_period_id": p["reporting_period_id"],
            "metric_code": c["metric_code"],
            "value": c["value"],
            "unit": c["unit"],
            "formula_version": "1.0",
            "policy_version": "reported-core-1",
            "input_facts": c["inputs"],
        }
        metrics.append((m, c))
        if c["metric_code"] == "cfo_to_reported_group_profit" and Decimal(c["value"]) < Decimal(
            "0.7"
        ):
            flags.append(
                {
                    "id": str(uuid5(NAMESPACE_URL, identifier + ":weak-reported-cash")),
                    "company_id": p["company_id"],
                    "reporting_period_id": p["reporting_period_id"],
                    "flag_code": "weak_reported_group_cash_conversion",
                    "title": TITLE,
                    "description": DESCRIPTION,
                    "severity": "high",
                    "rule_version": "1.0",
                    "evidence": {
                        "metric_id": m["id"],
                        "threshold": "0.7",
                        "policy_version": "reported-core-1",
                    },
                }
            )
    return metrics, flags


def _existing(connection, metrics, flags):
    existing_metrics = connection.execute("""select id::text,company_id::text,
        reporting_period_id::text,
        metric_code,value::text,unit,formula_version,policy_version,input_facts
        from public.calculated_metrics order by id""").fetchall()
    existing_flags = connection.execute("""select id::text,company_id::text,
        reporting_period_id::text,
        flag_code,title,description,severity,rule_version,evidence,is_active
        from public.red_flags order by id""").fetchall()
    expected_metrics = {m["id"]: m for m, _ in metrics}
    expected_flags = {f["id"]: f for f in flags}
    for row in existing_metrics:
        match = expected_metrics.get(row["id"])
        if (
            not match
            or Decimal(row["value"]) != Decimal(match["value"])
            or any(row[k] != match[k] for k in match if k != "value")
        ):
            raise PublishError(
                "existing calculated output requires review; no overwrite is allowed"
            )
        proof = connection.execute(
            "select metric_id from analytics.metric_provenance where metric_id=%s", (row["id"],)
        ).fetchone()
        if not proof:
            raise PublishError("existing metric has no publication provenance")
    for row in existing_flags:
        match = expected_flags.get(row["id"])
        if not match or not row["is_active"] or any(row[k] != match[k] for k in match):
            raise PublishError("existing signal requires review; no overwrite is allowed")
        if not connection.execute(
            "select flag_id from analytics.flag_provenance where flag_id=%s", (row["id"],)
        ).fetchone():
            raise PublishError("existing signal has no publication provenance")
    return {m["id"] for m in existing_metrics}, {f["id"] for f in existing_flags}


def _plan(connection, request, context):
    target = read_snapshot(
        connection,
        project_ref=request["identity"]["project_ref"],
        scope=request["scope"],
        captured_at=context["captured_at"],
    )
    fresh = build_analytics_preview(
        request["packets"], target, project_ref=request["identity"]["project_ref"]
    )
    if any(
        fresh[k] != request["preview"][k]
        for k in (
            "calculations",
            "packet_bindings",
            "policy_version",
            "formula_version",
            "approved_loaded_facts",
        )
    ):
        raise PublishError("fresh target differs from reviewed analytics inputs")
    inventory, sha = schema_inventory(connection)
    metrics, flags = _rows(connection, request)
    present_m, present_f = _existing(connection, metrics, flags)
    plan = {
        "mode": "dry_run",
        "production_writes": 0,
        "request_sha256": request["request_sha256"],
        "schema_sha256": sha,
        "project_ref": request["identity"]["project_ref"],
        "available": fresh["available"],
        "unavailable": fresh["unavailable"],
        "metrics_to_insert": [m for m, _ in metrics if m["id"] not in present_m],
        "flags_to_insert": [f for f in flags if f["id"] not in present_f],
        "already_present_metrics": sorted(present_m),
        "already_present_flags": sorted(present_f),
    }
    return plan, inventory, metrics, flags, target


def preview(connection, request):
    try:
        connection.execute("begin isolation level repeatable read read only")
        for sql in SETTINGS_SQL:
            connection.execute(sql)
        plan, inventory, _, _, _ = _plan(connection, request, _context(connection, apply=False))
        return plan, inventory
    finally:
        connection.rollback()


def publish(connection, request, reviewed_plan, *, expected_plan_sha256, expected_schema_sha256):
    if (
        digest(reviewed_plan) != expected_plan_sha256
        or reviewed_plan["request_sha256"] != request["request_sha256"]
    ):
        raise PublishError("reviewed publication plan digest mismatch")
    import_id, commit_started = str(uuid4()), False
    try:
        connection.execute("begin isolation level read committed read write")
        for sql in SETTINGS_SQL:
            connection.execute(sql)
        connection.execute("set local lock_timeout = '5s'")
        connection.execute(LOCK_SQL)
        connection.execute(
            "lock table "
            + ",".join("analytics." + t for t in PRIVATE_TABLES)
            + " in share row exclusive mode"
        )
        context = _context(connection, apply=True)
        plan, _, metrics, flags, target = _plan(connection, request, context)
        if (
            plan["schema_sha256"] != expected_schema_sha256
            or reviewed_plan["schema_sha256"] != expected_schema_sha256
        ):
            raise PublishError("target analytics schema differs from reviewed schema hash")
        prior = connection.execute(
            "select canonical_json,receipt_sha256 from analytics.load_receipts "
            "where request_sha256=%s",
            (request["request_sha256"],),
        ).fetchone()
        if prior:
            receipt = json.loads(prior["canonical_json"])
            if (
                digest(receipt) != prior["receipt_sha256"]
                or receipt["request_sha256"] != request["request_sha256"]
            ):
                raise PublishError("stored analytics receipt integrity mismatch")
            if len(plan["already_present_metrics"]) != len(metrics) or len(
                plan["already_present_flags"]
            ) != len(flags):
                raise PublishError("stored receipt does not match target publication")
            connection.rollback()
            return {"replayed": True, "receipt": receipt, "receipt_sha256": prior["receipt_sha256"]}
        if plan != reviewed_plan:
            raise PublishError("fresh publication plan changed; review a new dry run")
        connection.execute(
            "insert into analytics.publication_requests(request_sha256,canonical_json) "
            "values (%s,%s)",
            (request["request_sha256"], canonical(request["identity"])),
        )
        new_metrics = {m["id"] for m in plan["metrics_to_insert"]}
        for m, calculation in metrics:
            if m["id"] not in new_metrics:
                continue
            connection.execute(
                """insert into public.calculated_metrics
                (id,company_id,reporting_period_id,metric_code,value,unit,formula_version,policy_version,input_facts)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                tuple(
                    canonical(m[k]) if k == "input_facts" else m[k]
                    for k in (
                        "id",
                        "company_id",
                        "reporting_period_id",
                        "metric_code",
                        "value",
                        "unit",
                        "formula_version",
                        "policy_version",
                        "input_facts",
                    )
                ),
            )
            connection.execute(
                """insert into analytics.metric_provenance
                (metric_id,request_sha256,calculation_sha256,canonical_json)
                values (%s,%s,%s,%s)""",
                (m["id"], request["request_sha256"], digest(calculation), canonical(calculation)),
            )
        for f in plan["flags_to_insert"]:
            connection.execute(
                """insert into public.red_flags
                (id,company_id,reporting_period_id,flag_code,title,description,severity,rule_version,evidence)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                tuple(
                    canonical(f[k]) if k == "evidence" else f[k]
                    for k in (
                        "id",
                        "company_id",
                        "reporting_period_id",
                        "flag_code",
                        "title",
                        "description",
                        "severity",
                        "rule_version",
                        "evidence",
                    )
                ),
            )
            # A preexisting metric keeps its original immutable request binding.
            metric_request = connection.execute(
                "select request_sha256 from analytics.metric_provenance where metric_id=%s",
                (f["evidence"]["metric_id"],),
            ).fetchone()["request_sha256"]
            payload = {k: v for k, v in f.items() if k != "id"}
            connection.execute(
                """insert into analytics.flag_provenance
                (flag_id,request_sha256,flag_sha256,canonical_json) values (%s,%s,%s,%s)""",
                (f["id"], metric_request, digest(payload), canonical(payload)),
            )
        connection.execute("set constraints all immediate")
        verified_m, verified_f = _existing(connection, metrics, flags)
        if len(verified_m) != len(metrics) or len(verified_f) != len(flags):
            raise PublishError("post-publication verification failed")
        receipt = {
            "version": 1,
            "outcome": "committed",
            "import_id": import_id,
            "request_sha256": request["request_sha256"],
            **request["identity"],
            "schema_sha256": expected_schema_sha256,
            "reviewed_plan_sha256": expected_plan_sha256,
            "recorded_at": context["captured_at"],
            "input_snapshot_sha256": digest(target.model_dump(mode="json")),
            "inserted_metrics": sorted(new_metrics),
            "inserted_flags": [f["id"] for f in plan["flags_to_insert"]],
            "already_present_metrics": plan["already_present_metrics"],
            "already_present_flags": plan["already_present_flags"],
            "unavailable": plan["unavailable"],
        }
        sha = digest(receipt)
        connection.execute(
            """insert into analytics.load_receipts
            (request_sha256,import_id,receipt_sha256,canonical_json) values (%s,%s,%s,%s)""",
            (request["request_sha256"], import_id, sha, canonical(receipt)),
        )
        commit_started = True
        connection.commit()
        return {"replayed": False, "receipt": receipt, "receipt_sha256": sha}
    except BaseException:
        if commit_started:
            raise PublishError(
                "commit outcome uncertain; inspect analytics receipt "
                f"import_id={import_id} before retry"
            ) from None
        connection.rollback()
        raise


def inspect_receipt(connection, import_id, *, project_ref):
    """Read-only recovery, including after the original preview has expired."""
    try:
        connection.execute("begin isolation level repeatable read read only")
        for sql in SETTINGS_SQL:
            connection.execute(sql)
        _context(connection, apply=False)
        row = connection.execute(
            "select canonical_json,receipt_sha256 from analytics.load_receipts where import_id=%s",
            (import_id,),
        ).fetchone()
        if not row:
            raise PublishError(
                "no durable analytics receipt; inspect target before a fresh dry run"
            )
        receipt = json.loads(row["canonical_json"])
        if digest(receipt) != row["receipt_sha256"] or receipt["project_ref"] != project_ref:
            raise PublishError("stored analytics receipt integrity mismatch")
        request = {
            "identity": receipt,
            "scope": sorted({c["company_slug"] for c in receipt["calculations"]}),
        }
        metrics, flags = _rows(connection, request)
        present_m, present_f = _existing(connection, metrics, flags)
        if present_m != {m["id"] for m, _ in metrics} or present_f != {f["id"] for f in flags}:
            raise PublishError("durable receipt does not match current derived rows")
        invalid = connection.execute("""select
            (select count(*) from public.calculated_metrics m
              where not public.reported_metric_is_valid(m)) +
            (select count(*) from public.red_flags f
              where not public.reported_flag_is_valid(f)) as invalid""").fetchone()
        if invalid["invalid"]:
            raise PublishError("durable analytics inputs are no longer valid")
        return {"verified": True, "receipt": receipt, "receipt_sha256": row["receipt_sha256"]}
    finally:
        connection.rollback()
