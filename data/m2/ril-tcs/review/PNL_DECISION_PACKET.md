# First P&L load decision packet

**Decision state: pending.** This is a source-backed proposal for 56 P&L observations, not an approved ledger, executable plan or production load.

Catalog SHA-256: `e8d4dc3d24cbef2ef81c37f2eadefcd40b0862d66cf73e65da1ec6549eab6c41`. P&L audit SHA-256: `dd55cae60d0234a76ff4bc161c4ca76288258f7164ce5857d19190fbcfa6d1db`.

The official retrieval receipt and visual inspection notes accompany this packet. All 120 current/comparative observations passed label-row, dated-column and amount checks. Four FY2022 RIL P&L keys remain withheld; the other two catalog conflicts are cash-flow keys outside this packet.

## Decisions to record

1. Select each authenticated official PDF, including the reacquired TCS FY2026 copy rather than the different upload. Source keys are in `pnl_source_audit.json`.
2. Accept or reject each exact observation ID below with its definition. Current-year statement selection is not an assertion of adjusted comparability.
3. Copy the current pending `review_template.json` to a protected local path. Record actual reviewer identity, timezone-aware decision time and substantive rationale for approved/rejected source and fact entries. Leave other entries pending. Do not copy an audit result into an approval status.
4. After target preflight/migrations, export a fresh privileged snapshot, build and inspect the plan, preview the publisher/schema inventory, then explicitly apply only the approved target-ready selection. Retain the atomic receipt.

Merging this packet approves neither the sources nor the facts. An approved P&L subset can be loaded independently of pending balance-sheet/cash-flow decisions, but it does not complete M2 or establish all derived analytics inputs.

## Exact review scope

| Field | RIL fiscal years | TCS fiscal years | Candidates |
|---|---|---|---:|
| revenue | FY2023–2026 | FY2022–2026 | 9 |
| other_income | FY2023–2026 | FY2022–2026 | 9 |
| total_income | FY2023–2026 | FY2022–2026 | 9 |
| finance_costs | FY2022–2026 | FY2022–2026 | 10 |
| total_expenses | FY2023–2026 | FY2022–2026 | 9 |
| profit_for_year | FY2022–2026 | FY2022–2026 | 10 |

RIL: 26 candidates. TCS: 30 candidates. All decisions remain pending.

## Definitions and limits

- **revenue:** Consolidated revenue from operations; excludes recovered GST and other income. Scope follows the cited statement, without an adjusted comparability assertion.
- **other_income:** Consolidated statement other income. Scope follows the cited statement.
- **total_income:** Consolidated statement total income, equal to revenue from operations plus other income.
- **finance_costs:** Full consolidated P&L finance-cost line; not interest_expense or a generic interest-coverage denominator.
- **total_expenses:** Consolidated P&L total expenses, not directors-report operating expenses or inferred COGS.
- **profit_for_year:** Consolidated group profit for the year including NCI; continuing/discontinued scope follows the cited statement. Not owner PAT/net_income, and not RIL's distinct pre-associate/JV Profit After Tax subtotal.

All values below are **INR crore** exactly as recorded in the statement; normalized INR is raw value × 10,000,000. Annual durations are April 1 to March 31. Finance costs are not interest expense; group profit includes NCI and is not owner PAT. Do not map these fields to EBIT, EBITDA, COGS, debt or generic PAT aliases.

The current frontend only charts `revenue` from this six-field packet. Displaying the other fields needs explicit presentation labels; this packet does not silently rename them to existing chart aliases.

## reliance-industries

| Exact observation ID | INR crore | PDF page / printed page | Source row |
|---|---:|---|---|
| `reliance-industries:2022:finance_costs:report2022` | 14,584 | [198](https://www.ril.com/ar2021-22/pdf/RIL-Integrated-Annual-Report-2021-22.pdf#page=198) / 393 | Finance Costs |
| `reliance-industries:2022:profit_for_year:report2022` | 67,845 | [198](https://www.ril.com/ar2021-22/pdf/RIL-Integrated-Annual-Report-2021-22.pdf#page=198) / 393 | Profit for the Year |
| `reliance-industries:2023:revenue:report2023` | 8,91,311 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Revenue from Operations |
| `reliance-industries:2023:other_income:report2023` | 11,734 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Other Income |
| `reliance-industries:2023:total_income:report2023` | 9,03,045 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Total Income |
| `reliance-industries:2023:finance_costs:report2023` | 19,571 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Finance Costs |
| `reliance-industries:2023:total_expenses:report2023` | 8,09,023 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Total Expenses |
| `reliance-industries:2023:profit_for_year:report2023` | 74,088 | [209](https://www.ril.com/ar2022-23/pdf/RIL-Integrated-Annual-Report-2022-23.pdf#page=209) / 414-415 | Profit for the Year |
| `reliance-industries:2024:revenue:report2024` | 9,14,472 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Revenue from Operations |
| `reliance-industries:2024:other_income:report2024` | 16,057 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Other Income |
| `reliance-industries:2024:total_income:report2024` | 9,30,529 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Total Income |
| `reliance-industries:2024:finance_costs:report2024` | 23,118 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Finance Costs |
| `reliance-industries:2024:total_expenses:report2024` | 8,26,189 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Total Expenses |
| `reliance-industries:2024:profit_for_year:report2024` | 79,020 | [111](https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2023-24.pdf#page=111) / 218-219 | Profit for the Year |
| `reliance-industries:2025:revenue:report2025` | 9,80,136 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Revenue from Operations |
| `reliance-industries:2025:other_income:report2025` | 17,978 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Other Income |
| `reliance-industries:2025:total_income:report2025` | 9,98,114 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Total Income |
| `reliance-industries:2025:finance_costs:report2025` | 24,269 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Finance Costs |
| `reliance-industries:2025:total_expenses:report2025` | 8,92,097 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Total Expenses |
| `reliance-industries:2025:profit_for_year:report2025` | 81,309 | [100](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf#page=100) / 196-197 | Profit for the year |
| `reliance-industries:2026:revenue:report2026` | 10,75,675 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Revenue from Operations |
| `reliance-industries:2026:other_income:report2026` | 28,962 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Other Income |
| `reliance-industries:2026:total_income:report2026` | 11,04,637 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Total Income |
| `reliance-industries:2026:finance_costs:report2026` | 27,061 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Finance Costs |
| `reliance-industries:2026:total_expenses:report2026` | 9,81,475 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Total Expenses |
| `reliance-industries:2026:profit_for_year:report2026` | 95,754 | [101](https://www.ril.com/reports/RIL-Integrated-Annual-Report-2025-26.pdf#page=101) / 198-199 | Profit for the year |

## tcs

| Exact observation ID | INR crore | PDF page / printed page | Source row |
|---|---:|---|---|
| `tcs:2022:revenue:report2022` | 1,91,754 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | Revenue from operations |
| `tcs:2022:other_income:report2022` | 4,018 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | Other income |
| `tcs:2022:total_income:report2022` | 1,95,772 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | TOTAL INCOME |
| `tcs:2022:finance_costs:report2022` | 784 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | Finance costs |
| `tcs:2022:total_expenses:report2022` | 1,44,085 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | TOTAL EXPENSES |
| `tcs:2022:profit_for_year:report2022` | 38,449 | [245](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2021-22/ar/annual-report-2021-2022.pdf#page=245) / 245 | PROFIT FOR THE YEAR |
| `tcs:2023:revenue:report2023` | 2,25,458 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | Revenue from operations |
| `tcs:2023:other_income:report2023` | 3,449 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | Other income |
| `tcs:2023:total_income:report2023` | 2,28,907 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | TOTAL INCOME |
| `tcs:2023:finance_costs:report2023` | 779 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | Finance costs |
| `tcs:2023:total_expenses:report2023` | 1,72,000 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | TOTAL EXPENSES |
| `tcs:2023:profit_for_year:report2023` | 42,303 | [191](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2022-23/ar/annual-report-2022-2023.pdf#page=191) / 191 | PROFIT FOR THE YEAR |
| `tcs:2024:revenue:report2024` | 2,40,893 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | Revenue from operations |
| `tcs:2024:other_income:report2024` | 4,422 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | Other income |
| `tcs:2024:total_income:report2024` | 2,45,315 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | TOTAL INCOME |
| `tcs:2024:finance_costs:report2024` | 778 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | Finance costs |
| `tcs:2024:total_expenses:report2024` | 1,82,360 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | TOTAL EXPENSES |
| `tcs:2024:profit_for_year:report2024` | 46,099 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf#page=181) / 181 | PROFIT FOR THE YEAR |
| `tcs:2025:revenue:report2025` | 2,55,324 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | Revenue from operations |
| `tcs:2025:other_income:report2025` | 3,962 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | Other income |
| `tcs:2025:total_income:report2025` | 2, 59, 286 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | TOTAL INCOME |
| `tcs:2025:finance_costs:report2025` | 796 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | Finance costs |
| `tcs:2025:total_expenses:report2025` | 1, 93, 955 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | TOTAL EXPENSES |
| `tcs:2025:profit_for_year:report2025` | 48, 797 | [181](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf#page=181) / 179 | PROFIT FOR THE Y EAR |
| `tcs:2026:revenue:report2026` | 2,67,021 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | Revenue from operations |
| `tcs:2026:other_income:report2026` | 4,402 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | Other income |
| `tcs:2026:total_income:report2026` | 2, 7 1, 423 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | TOTAL INCOME |
| `tcs:2026:finance_costs:report2026` | 1,227 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | Finance costs |
| `tcs:2026:total_expenses:report2026` | 2, 01, 410 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | TOTAL EXPENSES |
| `tcs:2026:profit_for_year:report2026` | 49, 454 | [167](https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2025-26/ar/annual-report-2025-2026.pdf#page=167) / 197 | PROFIT FOR THE Y EAR |

## Withheld and remaining

RIL FY2022 revenue, other income, total income and total expenses have competing demerger-era presentations. Retain both statements and resolve scope coherently in a separate resolution package. No value-selection override is introduced here.

The other 320 candidates remain pending and are outside this row audit. Owner profit, interest/debt scope, EBIT/capex policy, RIL FY2022 equity and the two FY2024 cash-flow conflicts still require source/definition work. HDFC Bank, Tata Motors and L&T history remains unconfirmed. Target/RLS/concurrency, derived-output provenance and deployment verification remain release gates.
