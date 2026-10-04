"""Privileged, bounded, repeatable-read target inspection. No database writer."""

import hashlib
import json
import os
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .loader import _record_from_row
from .models import FinancialFactRecord, SourceMetadata
from .planning import ExistingFact, ExistingSource, TargetSnapshot, build_catalog, digest

MAX_ROWS = 10_000
MAX_BYTES = 5 * 1024 * 1024
UNIVERSE = {"reliance-industries", "tcs", "hdfc-bank", "tata-motors", "larsen-toubro"}
DEFAULT_SCOPE = ("reliance-industries", "tcs")
BEGIN_SQL = "begin isolation level repeatable read read only"
SETTINGS_SQL = (
    "set local row_security = off",
    "set local statement_timeout = '30s'",
    "set local idle_in_transaction_session_timeout = '30s'",
    "set local search_path = pg_catalog",
)
CONTEXT_SQL = """
select current_user as database_role, current_database() as database_name,
    to_char(current_timestamp at time zone 'UTC',
        'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') as captured_at,
    current_setting('transaction_read_only') as read_only,
    current_setting('transaction_isolation') as isolation,
    current_setting('row_security') as row_security,
    (select rolbypassrls or rolsuper from pg_catalog.pg_roles where rolname=current_user)
        as privileged,
    (select ssl from pg_catalog.pg_stat_ssl where pid=pg_backend_pid()) as ssl
"""
# Each query includes ALL quality states and inactive companies. No public API pagination.
QUERIES = {
    "companies": "select id::text,slug from public.companies where slug=any(%s) order by id",
    "periods": """select p.id::text,p.company_id::text,p.period_type,p.fiscal_year,
        p.period_start::text,p.period_end::text,p.currency
        from public.reporting_periods p join public.companies c on c.id=p.company_id
        where c.slug=any(%s) order by p.id""",
    "sources": """select s.id::text,s.company_id::text,s.title,s.document_type,
        s.source_url,s.publisher,s.published_at::text,s.fiscal_year,s.fiscal_quarter,
        s.sha256,s.verification_status
        from public.source_documents s join public.companies c on c.id=s.company_id
        where c.slug=any(%s) order by s.id""",
    "facts": """select f.id::text,f.company_id::text,f.reporting_period_id::text,
        f.metric_code,f.raw_value_text,f.raw_value::text,f.normalized_value::text,
        f.currency,f.unit_scale::text,f.source_document_id::text,f.source_page,
        f.source_label,f.quality_status,f.is_preferred
        from public.financial_facts f join public.companies c on c.id=f.company_id
        where c.slug=any(%s) order by f.id""",
    "proofs": """select p.fact_id::text,p.source_document_id::text,p.observation_id,
        p.catalog_sha256,p.review_ledger_sha256,p.evidence_sha256,p.definition_sha256,
        p.evidence_canonical_json,p.definition_canonical_json
        from ingestion.fact_provenance p join public.financial_facts f on f.id=p.fact_id
        join public.companies c on c.id=f.company_id
        where c.slug=any(%s) order by p.fact_id,p.catalog_sha256,p.review_ledger_sha256""",
    "catalogs": """select e.catalog_sha256,e.canonical_json from ingestion.evidence_catalogs e
        where exists (select 1 from ingestion.fact_provenance p
            join public.financial_facts f on f.id=p.fact_id
            join public.companies c on c.id=f.company_id
            where p.catalog_sha256=e.catalog_sha256 and c.slug=any(%s))
        order by e.catalog_sha256""",
}
MEASURE_QUERIES = {
    name: (
        "select count(*)::integer as row_count, "
        "coalesce(sum(octet_length(row_to_json(q)::text)),0)::bigint as byte_count "
        "from (" + query + " limit %s) q"
    )
    for name, query in QUERIES.items()
}


class SnapshotError(ValueError):
    """Safe diagnostic: never include passwords, connection URLs or raw server errors."""


def validate_scope(scope) -> list[str]:
    values = list(scope)
    if not values or len(values) != len(set(values)) or not set(values) <= UNIVERSE:
        raise SnapshotError("scope must contain distinct companies from the five-company universe")
    return sorted(values)


def connection_parameters(url: str, project_ref: str, ca_path: Path) -> dict:
    """Bind TLS endpoint/login to the expected project before opening a socket."""
    if not re.fullmatch(r"[a-z0-9]{20}", project_ref):
        raise SnapshotError("invalid expected project reference")
    try:
        parsed = urlsplit(url)
        port = parsed.port
        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
    except ValueError:
        raise SnapshotError("invalid database connection URL") from None
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.path != "/postgres" or parsed.query or parsed.fragment
        or port != 5432 or not password or any(x in url for x in "\r\n\x00")
    ):
        raise SnapshotError("use a direct/session PostgreSQL URL on port 5432 without URL options")
    host = parsed.hostname or ""
    if host == f"db.{project_ref}.supabase.co":
        role = user
    elif re.fullmatch(r"aws-[0-9]+-[a-z0-9-]+\.pooler\.supabase\.com", host):
        if not user.endswith(f".{project_ref}"):
            raise SnapshotError("pooler login does not match the expected project")
        role = user[: -(len(project_ref) + 1)]
    else:
        raise SnapshotError("database endpoint does not match the expected Supabase project")
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", role) or role in {"anon", "authenticated"}:
        raise SnapshotError("invalid privileged database login")
    ca = ca_path.resolve(strict=True)
    if not ca.is_file() or ca.stat().st_size > MAX_BYTES:
        raise SnapshotError("provide a bounded trusted CA certificate file")
    return {
        "host": host, "hostaddr": "", "port": 5432, "dbname": "postgres",
        "user": user, "password": password, "sslmode": "verify-full", "sslrootcert": str(ca),
        "gssencmode": "disable", "connect_timeout": 10,
        "options": "-c default_transaction_read_only=on -c search_path=pg_catalog",
        "application_name": "analyst-os-read-only-snapshot",
    }


def _unique(rows: list[dict], key: str, label: str) -> dict:
    mapped = {row[key]: row for row in rows}
    if len(mapped) != len(rows):
        raise SnapshotError(f"duplicate {label} identity")
    return mapped


def _proof_semantics(proof: dict, record: FinancialFactRecord, catalogs: dict) -> tuple:
    """Require the stored proof to match the current row, including unverified rows."""
    for field in ("catalog_sha256", "review_ledger_sha256", "evidence_sha256", "definition_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", proof[field]):
            raise SnapshotError("invalid provenance digest")
    for text, sha in (("evidence_canonical_json", "evidence_sha256"),
                      ("definition_canonical_json", "definition_sha256")):
        if hashlib.sha256(proof[text].encode("utf-8")).hexdigest() != proof[sha]:
            raise SnapshotError("stored provenance hash mismatch")
    observation = json.loads(proof["evidence_canonical_json"])
    definition = json.loads(proof["definition_canonical_json"])
    if digest(observation) != proof["evidence_sha256"] or (
        digest(definition) != proof["definition_sha256"]
    ):
        raise SnapshotError("stored evidence or definition is not canonical JSON")
    catalog = catalogs.get(proof["catalog_sha256"])
    if catalog is None or (
        catalog["observations"].get(proof["observation_id"]) != observation
        or catalog["definitions"].get(record.metric_code) != definition
    ):
        raise SnapshotError("stored proof does not match its validated catalog")
    evidenced = _record_from_row(
        {k: str(v) if v is not None else "" for k, v in observation.items()}
    )
    if (evidenced != record or observation["observation_id"] != proof["observation_id"]
            or Decimal(observation["normalized_value"]) != record.normalized_value):
        raise SnapshotError("stored observation no longer matches the fact")
    basis, kind, as_of = (
        observation["reporting_basis"], observation["measurement_type"], observation["as_of"]
    )
    if (
        basis not in {"consolidated", "standalone"}
        or kind not in {"instant", "duration"}
        or as_of != (record.period_end.isoformat() if kind == "instant" else None)
        or definition["metric_code"] != record.metric_code
        or definition["measurement_type"] != kind or not definition.get("definition")
    ):
        raise SnapshotError("stored measurement or definition mismatch")
    return basis, kind, as_of, proof["definition_sha256"], proof["evidence_sha256"]


def build_snapshot(rows: dict, *, project_ref: str, scope, captured_at) -> TargetSnapshot:
    """Convert a complete privileged read; never omit or infer legacy facts."""
    scope = validate_scope(scope)
    companies = _unique(rows["companies"], "id", "company")
    if sorted(c["slug"] for c in companies.values()) != scope:
        raise SnapshotError("target does not contain every company in the requested scope")
    periods = _unique(rows["periods"], "id", "period")
    sources = _unique(rows["sources"], "id", "source")
    catalogs = {}
    for stored in rows["catalogs"]:
        text = stored["canonical_json"]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != stored["catalog_sha256"]:
            raise SnapshotError("stored catalog hash mismatch")
        payload = json.loads(text)
        checked = build_catalog(payload["observations"], payload["definitions"],
                                payload["source_manifest"], set(payload["fiscal_years"]))
        if checked["sha256"] != stored["catalog_sha256"]:
            raise SnapshotError("stored catalog validation mismatch")
        catalogs[stored["catalog_sha256"]] = {
            "observations": {o["observation_id"]: o for o in payload["observations"]},
            "definitions": payload["definitions"],
        }
    _unique(rows["facts"], "id", "fact")
    proofs = defaultdict(list)
    fact_ids = {f["id"] for f in rows["facts"]}
    for p in rows["proofs"]:
        if p["fact_id"] not in fact_ids:
            raise SnapshotError("provenance lies outside the fetched fact scope")
        proofs[p["fact_id"]].append(p)
    output_sources = []
    source_metadata = {}
    for s in sources.values():
        company_slug = companies[s["company_id"]]["slug"]
        metadata = SourceMetadata.model_validate(
            {k: s[k] for k in ("title", "document_type", "source_url", "publisher", "published_at",
                               "fiscal_year", "fiscal_quarter", "sha256")}
        )
        source_metadata[s["id"]] = metadata
        output_sources.append(ExistingSource(
            company_slug=company_slug, source_url=metadata.source_url,
            sha256=s["sha256"], verification_status=s["verification_status"],
        ))
    output_facts = []
    for f in rows["facts"]:
        period, source = periods[f["reporting_period_id"]], sources[f["source_document_id"]]
        if period["company_id"] != f["company_id"] or source["company_id"] != f["company_id"]:
            raise SnapshotError("cross-company target references")
        if f["currency"] != period["currency"]:
            raise SnapshotError("target fact and period currencies differ")
        record = FinancialFactRecord.model_validate({
            "company_slug": companies[f["company_id"]]["slug"],
            **{k: period[k] for k in ("period_type", "fiscal_year", "period_start", "period_end")},
            **{k: f[k] for k in ("metric_code", "raw_value", "raw_value_text", "currency",
                                 "unit_scale", "source_page", "source_label")},
            "source": source_metadata[source["id"]],
        })
        if not proofs[f["id"]]:
            raise SnapshotError("target fact lacks provenance; no complete snapshot can be issued")
        semantics = set()
        for proof in proofs[f["id"]]:
            if proof["source_document_id"] != f["source_document_id"]:
                raise SnapshotError("target fact/provenance source mismatch")
            semantics.add(_proof_semantics(proof, record, catalogs))
        if len(semantics) != 1:
            raise SnapshotError("ambiguous target fact provenance; review before exporting")
        basis, kind, as_of, definition_sha, _ = semantics.pop()
        output_facts.append(ExistingFact(
            id=f["id"], record=record, normalized_value=f["normalized_value"],
            reporting_basis=basis, measurement_type=kind, as_of=as_of,
            definition_sha256=definition_sha, quality_status=f["quality_status"],
            is_preferred=f["is_preferred"],
        ))
    return TargetSnapshot(
        project_ref=project_ref, captured_at=captured_at, complete=True,
        company_slugs=scope, sources=output_sources, facts=output_facts,
    )


def client_tls_verified(connection) -> bool:
    """Check the client transport; pg_stat_ssl describes the proxy's backend leg.

    Require both active TLS and certificate/hostname verification. Unknown
    transport information fails closed; never log connection parameters.
    """
    try:
        params = connection.info.get_parameters()
        return (
            connection.pgconn.ssl_in_use is True
            and params.get("sslmode") == "verify-full"
            and bool(params.get("sslrootcert"))
        )
    except (AttributeError, TypeError, ValueError):
        return False


def collect_snapshot(connection, *, project_ref: str, scope=DEFAULT_SCOPE) -> TargetSnapshot:
    """One read-only RR transaction; always rollback, including on success."""
    scope = validate_scope(scope)
    try:
        connection.execute(BEGIN_SQL)
        for statement in SETTINGS_SQL:
            connection.execute(statement)
        context = connection.execute(CONTEXT_SQL).fetchone()
        if not (
            context["privileged"] is True and client_tls_verified(connection)
            and context["database_name"] == "postgres"
            and context["database_role"] not in {"anon", "authenticated"}
            and context["read_only"] == "on" and context["row_security"] == "off"
            and context["isolation"] == "repeatable read"
        ):
            raise SnapshotError("require TLS and a privileged read-only repeatable-read session")
        return read_snapshot(connection, project_ref=project_ref, scope=scope,
                             captured_at=context["captured_at"])
    finally:
        connection.rollback()


def read_snapshot(connection, *, project_ref: str, scope, captured_at) -> TargetSnapshot:
    """Read inside a caller-verified transaction; do not begin, commit or rollback."""
    scope = validate_scope(scope)
    rows = {}
    total_bytes = 0
    for name, query in QUERIES.items():
        params = (scope, MAX_ROWS + 1)
        measure = connection.execute(MEASURE_QUERIES[name], params).fetchone()
        if measure["row_count"] > MAX_ROWS:
            raise SnapshotError("row limit exceeded; a truncated snapshot cannot be issued")
        total_bytes += int(measure["byte_count"])
        if total_bytes > MAX_BYTES:
            raise SnapshotError("target evidence exceeds snapshot size limit")
        rows[name] = connection.execute(query + " limit %s", params).fetchall()
        if len(rows[name]) != measure["row_count"]:
            raise SnapshotError("read count mismatch; no complete snapshot can be issued")
    if len(json.dumps(rows, default=str).encode("utf-8")) > MAX_BYTES:
        raise SnapshotError("target evidence exceeds snapshot size limit")
    return build_snapshot(rows, project_ref=project_ref, scope=scope, captured_at=captured_at)


def write_snapshot(snapshot: TargetSnapshot, path: Path) -> str:
    """Create a private file exclusively; never replace an existing export or symlink."""
    payload = snapshot.model_dump(mode="json")
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(data) > MAX_BYTES:
        raise SnapshotError("snapshot output exceeds planner size limit")
    if not path.name.endswith(".target-snapshot.json"):
        raise SnapshotError("output filename must end with .target-snapshot.json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return digest(payload)
