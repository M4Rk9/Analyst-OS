# M3 reported analytics publication

This completes the repository's M3 publication path for the approved M2 history. Production completion requires applying the migration, running the native controlled publisher and retaining a verified live receipt. Implementation and ephemeral PostgreSQL tests are not a production load.

## Supported policy

Policy `reported-core-1`, formula/rule version `1.0`, uses only same-period approved consolidated INR inputs. It publishes current assets / current liabilities with a positive denominator, reported working capital in INR, and CFO / positive reported consolidated **group** profit. Group profit includes non-controlling interests; it is not owner PAT or recurring earnings. Quotients use Decimal precision 28 with half-even rounding, independently reproduced in PostgreSQL.

The verified 629-fact universe produces this coverage:

| Company | Available calculations | Unavailable calculations |
| --- | ---: | ---: |
| Reliance Industries | 15 | 0 |
| TCS | 15 | 0 |
| HDFC Bank | 0 | 15 |
| Larsen & Toubro | 10 | 5 |
| Tata Motors / TMPV | 3 | 12 |
| Total | 43 | 32 |

Unavailable calculations do not become database rows. HDFC Bank's owner profit and total income are not aliases for group profit or industrial liquidity inputs. L&T's withheld profit keys and Tata's withheld core history remain unavailable. The 46 conflict keys and two printed dashes remain excluded. Tata FY2026 keeps the approved original-entity/TMPV continuity and series break; the new CV entity stays separate.

One deterministic signal is supported by the current packet: Tata/TMPV FY2026 CFO / reported group profit is below **0.7**. Its code is `weak_reported_group_cash_conversion`, severity high. The description explicitly calls for investigation and makes no investment recommendation. No signal is emitted for a missing/nonpositive profit denominator, or when a supported ratio meets the threshold. The 0.7 threshold is a versioned investigation policy, not a financial fact or a reviewer statement.

## Rules intentionally unavailable

| Formula / signal family | Missing requirement |
| --- | --- |
| Revenue growth, CAGR, inventory/receivables growth comparisons | Approved comparable series and measurement definitions; bank total income and company-specific revenue codes are not interchangeable |
| Owner PAT margins, ROA/ROE, conventional CFO/PAT, recurring profit | Compatible approved owner-profit / earnings definitions and denominator policy |
| EBIT, EBITDA, interest coverage, deteriorating margins | Approved earnings and finance-cost definitions/inputs |
| Debt/equity, net debt, debt growth | Approved total-debt aggregation and cash definitions; bank borrowings are not an industrial debt proxy |
| Capex, FCF, CFO/capex | Approved capex definition/inputs; net investing cash flow is not capex |
| Receivables growth / collection-quality flags | Approved receivables inputs plus comparable revenue history |

The generic formula library remains tested, but these families are not published under this policy. Extending coverage requires reviewed source facts, definitions and a new controlled policy/version migration.

## Database and native publisher

Apply `20261004161801_controlled_reported_analytics.sql` after the existing migrations. Its preflight refuses any legacy derived rows; it does not delete or demote them. The live baseline before this PR is zero metrics/flags. The private `analytics` schema must stay excluded from Data API exposure alongside `ingestion`.

The four private tables retain canonical request JSON, per-metric/per-flag provenance and atomic receipts. Canonical UTF-8 SHA-256 checks protect artifacts. Constraints validate source fact IDs, company/period, values, units, approved catalog/ledger/evidence/definition hashes, positive denominators, exact arithmetic, threshold and flag text. There are no SECURITY DEFINER functions. Private functions/grants stay inaccessible to browser roles. Outputs and proofs are append-only; service_role cannot update, delete or truncate derived tables.

The native publisher requires verified TLS, an explicit privileged PostgreSQL session, exact pinned approvals, a complete fresh snapshot and reviewed preview/plan/schema hashes. It locks source/provenance/derived tables before refreshing its inputs, checks the entire existing derived universe, rejects mismatches without overwrite, and commits metrics, signals, proofs and receipt together. Lock timeout is five seconds. Repeating the same request returns the same durable receipt. A new preview after a successful load recognizes exact existing outputs and makes no duplicate output rows.

Browser RLS independently rechecks arithmetic and current verified preferred inputs. Demoted, missing or changed inputs hide affected metrics and signals. Public frontend cards select only the supported policy/version and latest loaded period, explain unavailable results and link both inputs to official PDF pages. Older calculations cannot fill a current-period gap.

## Operator workflow after merge and migration

Use the same Windows repository, Python environment and verified CA file used for M2. Do not paste a PostgreSQL password/URL into chat or commit it. The command prompts for the full connection URL with hidden input when `ANALYST_OS_DATABASE_URL` is not set. Use the direct connection or session pooler accepted by the M2 collector; transaction pooling is refused.

Run in `C:\Analyst-OS`; choose a new output directory every time:

```powershell
git pull --ff-only origin main
Set-Location python
py -m scripts.publish_reported_analytics --ssl-root-cert C:\AnalystOS-private\ca.pem --output-dir ..\data\processed\m3-publish-preview-01
```

The default is read-only. Review `analytics.preview.json`, `analytics.plan.json`, `analytics.schema-inventory.json` and `analytics.summary.json`. The initial plan should show **43 metrics to insert, one flag to insert, 32 unavailable, zero production writes**. Retain the full preview directory privately. The old PR29 preview is useful evidence but does not bind this new migration/publication plan; generate this fresh preview.

After reviewing those exact artifacts, use their three hashes for explicit apply within 24 hours. This block stops before apply if the summary is missing or is not a dry run. The hashes bind the reviewed files; do not edit files or regenerate them between review and apply.

```powershell
& {
    $previewDir = '..\data\processed\m3-publish-preview-01'
    $summary = Get-Content "$previewDir\analytics.summary.json" -Raw -ErrorAction Stop | ConvertFrom-Json
    if ($summary.mode -ne 'dry_run' -or $summary.production_writes -ne 0) { throw 'Review a complete dry-run summary first.' }
    py -m scripts.publish_reported_analytics --apply --ssl-root-cert C:\AnalystOS-private\ca.pem --preview-dir $previewDir --expected-preview-sha256 $summary.preview_sha256 --expected-plan-sha256 $summary.plan_sha256 --expected-schema-sha256 $summary.schema_sha256 --output-dir ..\data\processed\m3-publish-apply-01
    if ($LASTEXITCODE -ne 0) { throw 'Publication did not report success. Retain artifacts and inspect the durable receipt before retry.' }
}
```

Retain `analytics.receipt.json` and `analytics.summary.json`. Share those artifacts for independent live verification; never share connection credentials. A successful receipt does not prove deployed HTTP/browser behavior.

## Recovery and concurrency

If COMMIT response is lost, the safe error includes an `import_id`. Inspect that exact durable receipt first; this is read-only and does not depend on the original preview age:

```powershell
py -m scripts.publish_reported_analytics --receipt-import-id REPLACE_WITH_IMPORT_UUID --ssl-root-cert C:\AnalystOS-private\ca.pem --output-dir ..\data\processed\m3-recovery-01
```

A found receipt must pass its canonical hash, project and current row/input checks. If found and verified, the transaction committed; keep the recovered receipt. The same unexpired reviewed request can be replayed without duplicate rows. If no receipt exists, inspect target outputs before preparing a new dry run. Never infer rollback solely from a client error. An expired preview, schema change, source drift or different output requires a fresh dry run and review. Lock timeout and pre-COMMIT failure roll back the entire attempted transaction.

Ephemeral PostgreSQL tests exercise real constraints, transactions, full 629-fact ingestion, 43 metrics, supported signal, replay, readonly receipt inspection, late rollback, lost COMMIT response, preview tampering, schema mismatch, source drift, browser permissions, visibility demotion and half-even SQL arithmetic. TLS transport is synthetic only in those tests; real native TLS is enforced by the collector. Live contention/timeout exercises and actual HTTP/browser verification remain release evidence gates.

## Live completion checklist

- [ ] Migration applied; private analytics Data API exposure and grants checked
- [ ] Fresh native preview reviewed: 43 / 1 / 32 and exact hashes
- [ ] Native controlled apply and receipt retained
- [ ] Independent live audit: 43 metrics and one flag, complete provenance, zero arithmetic/provenance mismatches; source facts still 629
- [ ] Browser anon GET shows only supported rows; writes fail; company cards and both source links verified

M4 validated AI publication and M7 deployment/release remain separate milestones.
