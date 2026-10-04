# Controlled RIL/TCS publishing

The local publisher is implemented and tested. The [initial live schema upgrade and access verification](SUPABASE_VERIFICATION.md) is complete. No real review is approved or production fact loaded. All 376 committed candidates remain pending; six conflict keys remain withheld. M2 and issue #14 remain open.

## Operator prerequisites

Authenticate the filings and reviewer independently. Complete source and per-observation decisions in a private review ledger; the committed template is not approval. Partial approved selections are supported. Resolve missing definitions separately; this publisher has no conflict override or inferred values.

Review the [migration preflight](PROVENANCE_SCHEMA.md), then apply all migrations in order through the trusted migration role, including `20261004072747_controlled_load_receipts.sql`. Check schema exposure, grants, RLS, Auth/PostgREST and Supabase advisors. The private `ingestion` schema must remain outside the Data API.

Use an intended-project database login with BYPASSRLS/superuser capability and permissions to SELECT/INSERT and lock all twelve affected tables. Existing service-role SELECT/INSERT grants alone do not establish permission for SHARE ROW EXCLUSIVE locks; use the trusted migration/table owner where appropriate. Keep credentials local. Use the [snapshot connection and certificate instructions](TARGET_SNAPSHOT.md): direct/session pooler on port 5432, explicit project reference and TLS `verify-full`. Install `pip install -e ".[database]"` locally.

Export a fresh complete snapshot and build the offline plan with actual reviews. Inspect the plan and its canonical SHA-256; a changed catalog, ledger, snapshot or plan requires a new review. The planner's 24-hour snapshot limit still applies. Store reviews, snapshots, plans and outputs in a protected local directory outside Git; receipts can contain internal UUIDs and hashes.

## Preview, inspect, apply

The default invocation is read-only and always rolls back:

```bash
PYTHONPATH=python python python/scripts/publish_ril_tcs.py \
  --reviews /trusted/local/reviews.json \
  --target-snapshot /trusted/local/ril-tcs.target-snapshot.json \
  --reviewed-plan /trusted/local/load-plan.json \
  --expected-plan-sha256 REVIEWED_PLAN_SHA256 \
  --expected-project-ref YOUR_20_CHARACTER_REF \
  --ssl-root-cert /trusted/local/ca.pem
```

Inspect the returned schema inventory and `schema_sha256`, fresh target summary and selected observation IDs. Inventory includes owners/grants, RLS/policies, constraints/indexes, defaults and trigger/function definitions. Structural checks and a hash do not replace review of those definitions or runtime verification. Apply uses the identical arguments plus `--expected-schema-sha256 INSPECTED_SCHEMA_SHA256 --apply`. An empty approved selection is rejected before connecting. A changed schema stops apply; do not copy a new hash without inspecting it.

Apply begins a READ COMMITTED write transaction and acquires SHARE ROW EXCLUSIVE locks on the seven public and five private tables before reading target state. Locks block ordinary writers and competing publishers while allowing normal SELECT. This deliberately coarse V1 import should run in a controlled maintenance window; lock timeout is five seconds and statement timeout thirty seconds. Do not run migrations or privileged schema changes concurrently. Preview uses repeatable-read read-only without write locks.

The fresh complete snapshot must still permit every reviewed selected observation. Existing unverified/conflicting sources or facts block the operation; nothing is silently promoted, replaced or deleted. Companies must already exist. Periods and source UUIDs are resolved by validated identity, with publication dates left NULL. New facts, catalog/review evidence, source/fact provenance and the receipt commit together, after deferred database guards and a second snapshot verify all selected facts as already present.

## Receipts and recovery

`ingestion.load_receipts` is private, hash-checked and append-only. It retains the request/import identities, reviewed input/schema hashes, before/after snapshot hashes, inserted UUIDs and observations already present. `recorded_at` is a transaction timestamp, not an independently measured commit time. A visible receipt attests the transaction committed. No browser role can read it.

Retrying the exact request checks fresh target state and returns its existing receipt without duplicate inserts. Changed inputs define a different request and require review. Pre-commit failures roll back all staged facts and evidence. If COMMIT loses its response, the CLI reports an **uncertain outcome** and import UUID; inspect that UUID in the private receipt table through the trusted connection before retrying. Do not assume failure, manually recreate records or discard the original request. A committed transaction remains recoverable even if terminal output is lost.

## Verification boundaries

Python tests exercise input/hash/apply gates and preview isolation. Integration tests drive the actual Python orchestration and SQL through ephemeral PostgreSQL, covering all 376 candidates, partial selection, duplicate-free receipt replay, fresh-target conflicts, schema mismatch, late rollback and lost-COMMIT-response recovery. Synthetic attestations are labelled test-only and are never saved as real reviews. The PostgreSQL test adapter simulates only the TLS observation; it does not authenticate a live endpoint.

Live Psycopg/TLS, Supabase Auth/PostgREST/advisors, multi-session lock contention/timeouts and target receipt recovery remain release gates. Local tests do not constitute a production load. Next: actual RIL/TCS reviews and remaining inputs, target preflight/runtime verification, controlled approved loading, validated derived outputs, then equivalent history for HDFC Bank, Tata Motors and L&T.

### Client TLS through a session pooler

The native snapshot and publisher require Psycopg/libpq to report active client TLS, effective `sslmode=verify-full`, and an explicit root certificate. Unknown or weaker client transport is rejected even if PostgreSQL reports backend TLS. `pg_stat_ssl` remains backend diagnostic information: through a session pooler it describes the pooler-to-PostgreSQL leg, not the operator-to-pooler connection. It is not used as a substitute for client certificate and hostname verification. Endpoint/project binding, port 5432, privileged session checks, transaction settings, review gates, locks and receipt checks remain enforced. This does not attest encryption of the pooler's internal backend leg.

On Windows, evidence text is read explicitly as UTF-8. Existing failed-run output directories cannot be reused; choose a fresh output directory.
