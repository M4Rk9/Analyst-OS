# Privileged read-only target snapshots

The exporter supplies the complete target view required by the offline import planner. It does **not** apply migrations, approve evidence or publish financial data. No real target snapshot is committed or captured by this implementation PR.

## What it reads

`python/scripts/export_target_snapshot.py` reads the requested companies, reporting periods, source documents, financial facts and private provenance/catalogs in one PostgreSQL **repeatable-read, read-only transaction**. It checks TLS, database identity, a role with BYPASSRLS/superuser capability, `row_security=off` and transaction settings before reading evidence. It rolls back even on success. Use a trusted local database role with the minimum SELECT grants needed; this is not a browser or public application connection.

Scope defaults to Reliance Industries and TCS; explicit scope may contain any distinct subset of the five-company universe. The queries include inactive companies and pending, unverified, rejected and conflicting rows. They have no preferred-only, metric or fiscal-window filter. An anon REST export would conceal conflict-relevant rows and cannot attest completeness.

Stored numeric amounts are read as text and validated with Decimal; the exporter never recomputes a stored amount to replace it. Each fact must have matching full catalog-backed provenance, including basis, instant/duration semantics, measurement date and definition hash. Catalogs are revalidated using the same ingestion/catalog rules. All stored proof versions are inspected. Repeated identical evidence/definitions under different review ledgers are consistent; different companion evidence or definitions stop the export rather than selecting an arbitrary ledger. Quality/preference/source states remain exactly as stored and are not upgraded by exporting.

## Failures and limits

| Condition | Behavior |
|---|---|
| Wrong expected project, endpoint/login, port or TLS/session settings | Stop before issuing a snapshot |
| Missing company, source hash, fact provenance or referenced record | Stop; never omit legacy/unverifiable rows or infer definitions |
| Altered normalization, source identity, evidence, definition or measurement metadata | Stop; retain original target values for investigation |
| Ambiguous proof versions | Stop; review all versions explicitly |
| More than 10,000 rows per result, evidence/output over 5 MiB, timeout or count mismatch | Stop; never label a truncated export complete |
| Existing output file or symlink | Refuse replacement |

Measurements are bounded in SQL before transferring full rows, and fetched counts/serialized sizes are checked again. Output is created exclusively with mode `0600` on POSIX. It must end with `.target-snapshot.json`, which is ignored by Git. Store it in a trusted local directory; protect filesystem access separately on Windows. CLI logs contain counts and the canonical snapshot hash, never the database URL, password, raw server error or review text.

An empty target can yield a complete snapshot only if all requested company records exist and no uninspectable source/fact rows are present. Completeness covers the declared scope at the transaction snapshot, not subsequent database changes. The planner enforces expected project/scope and a maximum snapshot age; the [controlled publisher](CONTROLLED_PUBLISHING.md) performs a fresh transactional target check.

## Local use after target preflight

1. Review/apply the [provenance migration prerequisites](PROVENANCE_SCHEMA.md) and verify target grants/RLS. Missing private tables or unreviewed legacy facts block export; merging the migration is not applying it.
2. Install the optional pinned database driver locally:

   ```bash
   pip install -e ".[database]"
   ```

3. Obtain the direct or **session pooler** PostgreSQL connection string from the intended Supabase project's Connect dialog. Set `ANALYST_OS_DATABASE_URL` securely in the local process environment. It is a database login/password, not an anon/service-role API key. Do not put the URL in CLI arguments, commit it, paste it into chat or expose it in shell history/logs. Exporter accepts port 5432, database `postgres`, no URI query options, and binds the direct hostname or pooler login suffix to the explicit 20-character expected project reference. Transaction pooling on port 6543 is intentionally unsupported.
4. Obtain the appropriate trusted root CA certificate for that endpoint from its official provider/Supabase SSL configuration. The driver uses `sslmode=verify-full`; an untrusted or wrong-host certificate fails. There is no insecure TLS fallback.
5. With an existing trusted output directory, run:

   ```bash
   PYTHONPATH=python python python/scripts/export_target_snapshot.py \
     --expected-project-ref YOUR_20_CHARACTER_REF \
     --ssl-root-cert /trusted/local/ca.pem \
     --output /trusted/local/ril-tcs.target-snapshot.json
   ```

6. Feed that file into the existing zero-write planner with actual review decisions:

   ```bash
   PYTHONPATH=python python python/scripts/plan_ril_tcs_load.py \
     --reviews /trusted/local/reviews.json \
     --target-snapshot /trusted/local/ril-tcs.target-snapshot.json \
     --expected-project-ref YOUR_20_CHARACTER_REF \
     --output /trusted/local/load-plan.json
   ```

The committed review template is still pending: providing a snapshot does not approve any of the 376 candidates or resolve the six conflict keys. `apply_ready` remains false; the publisher is implemented, but actual reviews, target verification and loading remain pending.

## Verification status

Python tests cover connection binding, TLS/privilege/session rejection, complete/empty scopes, metadata and hash failures, ambiguous proof, limits, rollback, credential redaction and exclusive file handling. PostgreSQL tests execute the exporter queries and size/count measurements, compare privileged reads with hidden anon rows, round-trip actual database rows through the Python snapshot model, and reject writes in a read-only transaction.

These tests use ephemeral PostgreSQL plus a mocked Python connection adapter. They do not establish live Psycopg/TLS authentication, target configuration or concurrent multi-session behavior. Real Supabase export, project verification and the writer's multi-session concurrency tests remain release gates. No production credential is needed by CI.

References: [Supabase connection methods](https://supabase.com/docs/guides/database/connecting-to-postgres), [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [TLS verification](https://www.postgresql.org/docs/current/libpq-ssl.html).
