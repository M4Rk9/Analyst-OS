# Supabase target verification — 2026-10-04

Observed target: **Analyst-OS**, project reference `swahxcccptpfxwvhgfxz`, region `ap-southeast-2`, active/healthy. This record describes actual connected-project checks, not a local test result. No financial history, approved ledger or load receipt has been inserted.

## Applied migrations

Applied the exact SQL bytes from merged `main` after a privileged read-only preflight. The Management API assigned the live migration versions below. The project already had separately timestamped foundation migrations; do not run an unreviewed `db push` or rewrite migration history to pretend local/live versions match.

| Repository file | Live version / name | SQL SHA-256 |
|---|---|---|
| `20261003201012_reviewed_provenance.sql` | `20261004081902` / `reviewed_provenance` | `c47db76cbea2a74fac6e563b394c2a05c8920e24256e3bb282030e1f94dbc2a4` |
| `20261004072747_controlled_load_receipts.sql` | `20261004081925` / `controlled_load_receipts` | `ae14c6b9dc06c3c6c4f3ac136f29be78d57543af495435dd9d5b9b2beb17772f` |

Pre-existing live migration versions: `20260927152955 core_schema`, `20260927153029 row_level_security`, `20260927153040 seed_companies`, `20260927153056 ai_insights`, `20260927153107 harden_auto_rls_helper`.

Preflight found all five expected company slugs. Sources/facts, verified assertions requiring demotion, invalid normalization/non-finite amounts, cross-company references, calculated metrics and red flags were all zero. Therefore no existing source/fact publication assertion was demoted. Both migrations reported success and appear in live migration history.

## Database and API checks

| Check | Actual result |
|---|---|
| RLS on seven public plus five private tables | Enabled on all 12 |
| `anon` / `authenticated` public table SELECT grants | Present on all seven public tables |
| Browser INSERT/UPDATE/DELETE/TRUNCATE grants | Absent on all 12 tables |
| Private schema usage, private table SELECT and private function EXECUTE for browser roles | Denied |
| Private functions | Five; none SECURITY DEFINER |
| Actual anon INSERT/UPDATE/DELETE attempts | All 21 denied with insufficient privilege |
| Actual authenticated INSERT/UPDATE/DELETE attempts | All 21 denied with insufficient privilege |
| Private SELECT attempts under each browser role | All five denied for each role |
| Public SELECT as each browser role | Five companies, zero facts |
| HTTPS Data API GET using enabled modern publishable key | HTTP 200 for all seven public tables; companies returns five, other tables zero |
| Data API request with `Accept-Profile: ingestion` | HTTP 406 / `PGRST106`, invalid schema |
| Publisher structural schema audit against live inventory | Passed |

Write/role probes ran in transactions that ended with ROLLBACK. They contained no fabricated financial rows or review approvals. UPDATE/DELETE probes used `where false` and nevertheless failed due to missing table privileges. No API keys or database passwords are included in this record.

Observed schema SHA-256: `de92ed7e64364b1150d198fa60d4ee40f570dddc66c36d0aa5ab31a8e8e65cc3`. This fingerprints that inventory only. It is **not** authorization to apply a future plan; obtain and inspect a fresh publisher preview before each import. The connected SQL inventory check does not verify the Python driver's live TLS/session behavior.

## Advisors

Security advisor: zero WARNING/ERROR findings; five informational [RLS-enabled/no-policy findings](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy), one per private ingestion table. These tables deliberately have no browser policies and deny schema/table access. Do not add browser policies to silence the finding.

Performance advisor: eight informational [unindexed foreign-key findings](https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys), plus six [unused-index findings](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index) on the empty application tables. No indexes were dropped or additional live DDL applied during this verification.

Missing covering indexes reported on:

- `ingestion.fact_provenance`: source-document/catalog/ledger foreign key.
- `ingestion.source_provenance`: catalog/ledger foreign key.
- `public.financial_facts`: same-company/source, reporting-period and source-document foreign keys.
- `public.calculated_metrics` and `public.red_flags`: reporting-period foreign keys.
- `public.ai_insights`: source-document foreign key.

These are retained as explicit performance follow-up rather than described as a fully clean advisor result. Reassess index usage after approved loading; the current empty database cannot establish production performance.

## Remaining gates

The [56-fact packet](../data/m2/ril-tcs/review/PNL_DECISION_PACKET.md) still requires actual source and fact decisions. All 376 candidates remain pending and all six conflict keys stay withheld. No merge or migration approval is a financial review decision.

Still required before claiming controlled loading verified:

- Live Python publisher connection using the intended endpoint and `verify-full` TLS; complete privileged snapshot and inspected plan/schema hashes.
- Real multi-session lock contention/timeouts, transaction/retry and uncertain-COMMIT recovery checks.
- Approved subset loading and retained atomic receipt; resulting source/fact/provenance inspection.
- Runtime verified/unverified row visibility and populated browser flows after data exists; the empty-table checks do not prove those paths.
- Reviewed input-linked derived outputs, remaining RIL/TCS definitions and the other three companies' authenticated history.
- Cloudflare deployment/headers, browser/accessibility and remaining release evidence.

M2 and issue #14 remain open. This verification completes the initial target schema upgrade and initial browser-role/API boundary checks only.
