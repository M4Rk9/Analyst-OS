# RIL/TCS balance-sheet and cash-flow evidence — batch 2

This batch extends [batch 1](../batch1/README.md) with selected consolidated balance-sheet and cash-flow fields for fiscal years ending March 2022–2026. It contains **644 observations**, including both current and comparative columns from ten reports, **320 validation-only candidates**, and **138 exact accounting checks** across twenty source columns. Seven supporting note pages preserve definition and conflict context.

The source documents are the same ten authenticated reports recorded in [batch1/source_manifest.json](../batch1/source_manifest.json). Local PDF bytes were rechecked against those hashes before extraction. For TCS FY2026, extraction uses the reacquired official PDF, whose hash is `a19bddbe9cfd136de02fbd266335034a31d507efe790dfec0241be9aa0b0a5a0`; the differing upload is not used. Batch1's `bytes` for that entry describes the upload; `official_bytes` describes the official copy. All 26 selected statement pages and seven supporting note pages were visually inspected. Complete PDFs and rendered images remain outside Git; page text, URLs, document hashes and PDF/printed page mappings are retained here.

All observations remain `quality_status=unverified` and `is_preferred=false`. Validation is evidence preparation, not production approval. No database writes or automatic source preferences occur. M2 and issue #14 remain open.

## Exact field readiness

[Field readiness](field_readiness.json) lists every company/metric/fiscal-year combination, including withheld conflicts and comparative-only coverage. [Metric registry](metric_registry.json) gives the definitions. These are candidates for a controlled review/loading process, subject to the companion metadata and gates below.

| Fields | RIL validation candidates | TCS validation candidates |
|---|---|---|
| `noncurrent_assets`, `current_assets`, `total_assets`, `share_capital`, `other_equity`, `noncontrolling_interest`, `noncurrent_liabilities`, `current_liabilities`, `inventory`, `cash_and_cash_equivalents`, `trade_payables`, `noncurrent_lease_liabilities`, `current_lease_liabilities` | FY2022–2026 | FY2022–2026 |
| `total_equity` | FY2023–2026; FY2022 reported comparative is retained but not selected | FY2022–2026 |
| `trade_receivables`, `noncurrent_borrowings`, `current_borrowings`, `noncurrent_deferred_payment_liabilities` | FY2022–2026 | Unavailable in this selected field set; absence is not zero |
| `equity_attributable_owners`, `noncurrent_billed_receivables`, `noncurrent_unbilled_receivables`, `current_billed_receivables`, `current_unbilled_receivables` | Unavailable in this selected field set | FY2022–2026 |
| `cash_generated_before_tax`, `taxes_paid_net`, `cash_from_operations`, `cash_from_financing`, `opening_cash`, `closing_cash`, `interest_paid_cash`, `lease_payments_cash` | FY2022–2026 | FY2022–2026 |
| `cash_from_investing`, `cash_change` | FY2022–2023 and FY2025–2026; FY2024 withheld | FY2022–2026 |
| `capex_ppe_intangibles_cash`, `deferred_payment_cash` | FY2022–2026 | Unavailable in this selected field set |
| `cash_subsidiary_additions` | FY2022–2024; FY2024 must stay with its original source-column cash bridge | Unavailable in this selected field set |
| `cash_demerger_deduction` | FY2023–2024; FY2024 source reports nil | Unavailable in this selected field set |
| `capex_ppe_cash`, `capex_intangibles_cash`, `rou_acquisition_cash`, `cash_fx_adjustment` | Unavailable in this selected field set | FY2022–2026 |
| `asset_acquisition_cash` | Unavailable in this selected field set | FY2025–2026 |
| `subsidiary_acquisition_cash` | Unavailable in this selected field set | FY2026 |

The candidate policy selects only current-year columns and excludes every conflicting key. It does not silently backfill absent current-year fields from comparative columns. RIL FY2022 total equity can be derived from reported components, and a reported FY2022 subtotal exists in the following report; both are reviewable, but neither is promoted to a current-year reported fact here. FY2021 comparatives support opening-balance review and are not candidates in the five-year loading window.

## RIL FY2024 cash presentation conflict

| Field, INR crore | Original FY2024 report PDF113, printed222–223 | FY2025 report PDF102, printed200–201 comparative |
|---|---:|---:|
| `cash_from_investing` | -114,301 | -113,581 |
| `cash_change` | 27,841 | 28,561 |
| Cash added on subsidiary inclusion | 720 separately reported | No separate line |
| Closing cash | 97,225 | 97,225 |

Both source-column cash bridges reconcile. The ₹720 movement and omission of the separate adjustment suggest a presentation reclassification. FY2025 Note44 (PDF138, printed272) permits regrouping/reclassification generally, but does not explicitly explain this adjustment. The [conflict ledger](conflict_ledger.json) keeps both versions unresolved. Review the acquisition cash-flow bridge and approve a coherent source-column policy before preference selection. Combining the newer cash movement with the original subsidiary addition would double-count ₹720.

Batch1's four RIL FY2022 P&L conflicts also remain unresolved. The two batches together contain **376 conflict-free validation candidates** and six unresolved conflicting keys; this is not 376 approved production facts.

## Definitions that must survive loading

- Balance-sheet fields are **instant** measurements at 31 March. The ingestion model uses the FY annual container (`period_start=1 April`, `period_end=31 March`); `measurement_type` and `as_of` in companion metadata preserve their actual meaning. They must not become annual flows.
- Source amounts are INR crore, normalized exactly by `10000000`. Parentheses become negative cash amounts. A plain, visually reviewed dash is recorded as reported nil. Starred/inexact dashes and tiny-value footnotes are not converted to zero or selected as exact facts. TCS digit glyph substitutions and internal-space removal are recorded in each affected observation.
- RIL current borrowings already contain current maturities (FY2026 Notes16/20). Adding Note16's current maturities again would double-count them. Leases, deferred-payment liabilities, accrued interest and supplier-financing definitions require explicit treatment before publishing a generic `total_debt`.
- TCS billed/unbilled and current/non-current receivables stay separate. The debt field is unavailable until the full applicable liability notes are reviewed; no missing borrowing line becomes zero. FY2026 Class B convertible preference shares are presented as a financial liability, with terms preserved in the supporting note, and are not automatically classified as borrowings.
- `interest_paid_cash` is a cash payment, not P&L `interest_expense`. RIL FY2022/FY2023 cash-flow footnotes exclude Financial Services Segment from the marked interest line. RIL Note29 separates interest expense, lease interest, other borrowing costs and exchange losses, with capitalization context. TCS Note16 separates lease interest, tax interest and other interest costs. No generic coverage denominator is approved.
- RIL's capex cash line includes spectrum when explicitly labelled; deferred-payment cash stays separate. TCS PPE, intangible, ROU, asset-acquisition and subsidiary-acquisition cash stay separate. A generic capex/FCF policy still needs review. No COGS, EBIT, owner PAT, EPS or ratio is fabricated from these selected fields.
- The CSV loader discards extra metadata. The JSON evidence, registry, source-column policy, quality status and preferred flags must be carried by any future publisher. Do not pass these rows to SQL defaults that imply verification.

## Reproduction and checks

From the repository root:

```bash
PYTHONPATH=python python python/scripts/validate_m2_batch2.py data/m2/ril-tcs/batch2
PYTHONPATH=python python python/scripts/validate_financial_csv.py candidate_facts_validation_only.csv --root data/m2/ril-tcs/batch2
pytest
ruff check python
```

The [validation receipt](validation_receipt.json) records model/loader counts, exact unit scaling, source and page-text references, conflict exclusion and zero database writes. The [reconciliation ledger](reconciliation_ledger.json) records observation IDs and arithmetic for assets, equity, liabilities, operating cash, cash movements, closing-cash bridges, and balance-sheet/CF cash agreement. It also identifies two RIL FY2022-report equity derivations which are not raw production facts.

The checker verifies the committed text hashes and observation references. It does not independently redownload official PDFs or reproduce the original visual inspection. Regression tests reject restored conflicting candidates, source-hash changes and altered comparative values. See [M2 next steps](../../../../docs/M2_NEXT_STEPS.md) and [missing artifacts](missing_artifacts.json) for the remaining gates.
