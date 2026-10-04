# Review-bound database provenance

`20261003201012_reviewed_provenance.sql` supplies storage and integrity checks for the offline planner. It is locally tested and now [applied to the Analyst-OS target with initial access verification](SUPABASE_VERIFICATION.md). It does not approve filings, resolve conflicts, export a snapshot or load history. The committed review template remains pending and the plan remains zero-write.

## Private records and hashes

Keep `ingestion` outside the Supabase Data API exposed schemas. Browser roles have no schema usage, table access or function execution. All five tables (including the subsequent receipt migration) have RLS, no browser policies and explicit service-role SELECT/INSERT grants. Functions run as the caller, with a fixed `pg_catalog` search path; none use `SECURITY DEFINER`. Privileged credentials remain local.

| Table | Retained evidence |
|---|---|
| `evidence_catalogs` | Source manifest, all observations including competing comparatives, fiscal window, selection policy and definitions |
| `review_ledgers` | Catalog-bound source/fact decisions, reviewer text, timestamp and rationale |
| `source_provenance` | Source UUID and the exact catalog/review-ledger pair |
| `fact_provenance` | Fact/source UUIDs, observation ID, complete observation/definition and their hashes |
| `load_receipts` | Atomic import/request identity, input/schema hashes and inserted/already-present observation evidence |

Hash UTF-8 text from Python `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` and store it verbatim. Generated JSONB columns provide query access; PostgreSQL checks hashes of the stored text bytes. Do not hash `jsonb::text`, reformat JSON or drop companion fields. `build_catalog()` now returns the full digest `payload`; existing catalog/plan digests are unchanged.

Full observation JSON preserves reporting basis, instant/duration semantics, `as_of`, printed/PDF-page references, column role, corrections and source identity. Review text is an attestation, **not** authenticated identity, a digital signature or proof of document authenticity. The trusted local workflow must authenticate filings and reviewers first.

Records are append-only. New decisions require a new ledger; the service role cannot edit, delete or truncate old proof. Foreign keys retain corresponding core records. The snapshot exporter inspects all provenance and rejects ambiguous matches rather than silently selecting a ledger.

## Publication and integrity

New facts default to `unverified`. Raw values, scales and normalized amounts must be finite and satisfy exact multiplication. Composite foreign keys prevent cross-company period/source links. Preferred facts must be verified, and a partial unique index permits one preferred observation per company/period/metric.

Deferred triggers validate the final transaction. Verified sources require a manifest match and approved source attestation; verified facts require an exact catalog observation, matching definition, approved source/fact decisions and verified source. Amounts, units, currency, periods, source identity, page/label and raw display text must match. Source/period/company identity changes trigger revalidation; source and fact demotion can occur together atomically. Public fact reads also require a verified source from the same company.

The initial contract accepts consolidated April–March annual-report current-year columns in the selected fiscal window, including instant balance-sheet and duration P&L/cash-flow values. All same-key catalog observations are checked for competing normalized values/currencies. The six RIL conflict keys remain blocked even with an approval entry; no resolution override exists. Publication dates remain NULL because the current catalogs do not establish them. Report-year labels and retrieval times do not establish publication dates.

SQL checks do not establish target completeness, authenticate PDF bytes independently or detect conflicts across separately submitted catalogs. The [controlled publisher](CONTROLLED_PUBLISHING.md) implements complete snapshots, UUID resolution, fresh transactional checks, conflict/idempotence handling and atomic receipts; actual target verification and loading remain pending. Legacy/unverified rows are not approval evidence.

## Upgrade preflight and effects

Run [the privileged read-only preflight](../supabase/preflight_reviewed_provenance.sql) against the intended project and retain its identity/results. The original implementation did not inspect a target; the later [live preflight and deployment record](SUPABASE_VERIFICATION.md) records the intended project.

| Result | Required action |
|---|---|
| Legacy verified/preferred facts or verified sources | Review the impact: migration demotes them to unverified/not-preferred and pending, without changing amounts or inferring reviews |
| Invalid normalization, non-finite values or cross-company references | Investigate original evidence; constraints fail instead of automatically repairing amounts |
| Existing calculated metrics or red flags | Migration stops before demotion; plan a reviewed upgrade for derived-output/input provenance so stale outputs cannot remain public after their inputs are demoted |

Apply migrations in order through the trusted migration role. A failure rolls back demotion and DDL together. Existing AI insights become unavailable when their source is demoted under the existing policy. Do not bypass triggers or invent backfilled reviews.

After applying to Supabase staging/target, verify PostgreSQL compatibility, service-role privileges/BYPASSRLS, schema exposure, grants, RLS and rejected browser INSERT/UPDATE/DELETE. Run the Supabase security/performance advisors and retain results. WASM PostgreSQL tests do not verify Supabase Auth, PostgREST or deployment configuration. Row locks and unique indexes are implemented; multi-session concurrency/retry testing remains required for the controlled writer. Initial target migrations, grants, SQL browser-role denials and Data API exposure were checked; this does not verify the live publisher.

## Local validation

After installing Python development dependencies:

```bash
npm ci --ignore-scripts
npm run test:db
npm audit --audit-level=high
```

Pinned PGlite is development-only; the static app and production Python stack do not depend on Node packages. Tests execute migrations in ephemeral PostgreSQL with pgcrypto and representative Supabase roles, using real observations and conspicuously labelled **test-only** synthetic attestations. No approved review ledger is saved and no target is contacted. Tests cover all 376 candidates, six conflicts, approval failures, hash/semantic tampering, RLS/grants, uniqueness and legacy demotion.
