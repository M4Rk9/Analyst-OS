# Analyst OS — RIL and TCS first ingestion batch

Prepared 3 October 2026. Audited repository commit: 3133c4560b94ef4a49759f78c03ce2a74c2f924b.

## Completed

- Identified five annual reports per company, FY2021–22 through FY2025–26.
- Matched nine uploaded PDFs byte-for-byte with official HTTPS report URLs.
- The uploaded TCS FY2025–26 PDF differs from the official file at its URL. Both have 360 pages and the six selected P&L values agree. No cause for the binary difference is asserted. The batch uses the independently downloaded official copy, retained in the evidence archive, with its own SHA-256; the uploaded hash is preserved separately.
- Visually inspected all ten P&L statement pages and the RIL consolidated demerger note. Text extraction correction for the TCS FY2024–25 digit glyph is retained in observations; the official TCS FY2025–26 text also needs word-spacing cleanup. Raw text excerpts are retained.
- Extracted 120 source observations: six P&L fields × current/comparative column × ten reports. Sixty are current-year observations within the requested five-year window. The earliest comparative columns also contain FY2020–21; they are kept as evidence, excluded from the candidate CSV.
- Recorded four conflicting keys for RIL FY2021–22. Both original and re-presented values remain in observations and the conflict ledger.
- Prepared 56 unique candidate rows and passed them through the repository CSV loader. Four unresolved RIL keys are excluded. Model validation is not production approval.

## What each file is for

| File | Purpose |
|---|---|
| source_manifest.json | Official URLs, local/official SHA-256, page counts, origin checks and retrieval timestamps |
| observations.json | All 120 observations, source IDs, raw/normalized values, fiscal dates, basis, column role, page mapping and review status |
| conflict_ledger.json | Both observations for each conflicting key and explanatory note reference |
| candidate_facts_validation_only.csv | 56 deduplicated, schema-valid candidate facts; not a privileged-load instruction |
| validation_receipt.json | Counts, exact arithmetic checks, repository loader/conflict results and CSV hash |
| *_pnl.txt | Raw statement text for reproducible extraction and correction audit |
| Source PDFs and rendered pages | Retained in the separately delivered evidence archive; not duplicated in this Git repository |
| TCS FY2025–26 official source | Independently downloaded and retained in the evidence archive; reacquire via the manifest URL and verify its SHA-256 |
| Reproduction script | Included in the separately delivered evidence archive; no database writes |

## Approved extraction definitions (not yet approved for production)

All observations are consolidated annual statements, currency INR, displayed monetary unit crore, normalization raw_value × 10,000,000. Fiscal-year convention uses the ending year. source_page is the 1-based PDF page; printed_pages separately preserves the report footer. Dates are annual April 1–March 31. Publication dates are not inferred from the auditor signature date.

| metric_code | Meaning |
|---|---|
| revenue | Revenue from operations, not gross sales/services before recovered GST and not total income |
| other_income | Statement other income |
| total_income | Statement total income = revenue from operations + other income |
| finance_costs | Full finance-cost line, not automatically interest expense |
| total_expenses | Audited P&L total expenses, not the differently defined directors-report operating-expense subtotal |
| profit_for_year | Total consolidated profit for the year, including non-controlling interests; not owners-only PAT; continuing/discontinued scope follows the cited statement |

profit_for_year is deliberately not silently mapped to PAT/net_income aliases. RIL reports have changes in presentation and discontinued operations; the RIL FY2024–25 line labelled Profit After Tax is before share of associates/JVs, and differs from Profit for the year. Growth/margin calculations must use explicitly compatible definitions. No EBITDA, EBIT, EPS, owners-only PAT or industrial ratios have been guessed.

## Five-year current-column observations

Values below are INR crore, as reported in each year’s own consolidated statement. This table is evidence, not a comparable adjusted time series.

| Company | FY ended | Revenue from operations | Total income | Profit for year (group) | PDF page / printed pages |
|---|---|---:|---:|---:|---|
| reliance-industries | 2022 | 721,634 | 736,581 | 67,845 | 198 / 393 |
| reliance-industries | 2023 | 891,311 | 903,045 | 74,088 | 209 / 414-415 |
| reliance-industries | 2024 | 914,472 | 930,529 | 79,020 | 111 / 218-219 |
| reliance-industries | 2025 | 980,136 | 998,114 | 81,309 | 100 / 196-197 |
| reliance-industries | 2026 | 1,075,675 | 1,104,637 | 95,754 | 101 / 198-199 |
| tcs | 2022 | 191,754 | 195,772 | 38,449 | 245 / 245 |
| tcs | 2023 | 225,458 | 228,907 | 42,303 | 191 / 191 |
| tcs | 2024 | 240,893 | 245,315 | 46,099 | 181 / 181 |
| tcs | 2025 | 255,324 | 259,286 | 48,797 | 181 / 179 |
| tcs | 2026 | 267,021 | 271,423 | 49,454 | 167 / 197 |

## RIL FY2021–22 conflict review

| Field | Original FY2021–22 | FY2022–23 comparative | Status |
|---|---:|---:|---|
| revenue | 721,634 | 717,635 | Excluded from candidate CSV |
| other_income | 14,947 | 14,943 | Excluded from candidate CSV |
| total_income | 736,581 | 732,578 | Excluded from candidate CSV |
| total_expenses | 655,555 | 653,555 | Excluded from candidate CSV |

Consolidated Note 32 in RIL FY2022–23, PDF page 234 / printed 464–465, states that prior-year figures were presented as if financial-services discontinued operations had been discontinued in the prior year. The arithmetic bridge for total income is 736,581 − 732,578 = 4,003 crore; the note lists discontinued total income of 3,988 crore. The remaining 15-crore presentation difference needs a documented note-level bridge; it is not silently reconciled here. The note’s discontinued expenses are 2,000 crore, matching 655,555 − 653,555. Revenue and other-income component bridges still require detailed segment/note mapping. No preferred value or adjusted history was silently selected.

## Validation evidence and limits

All 120 observations construct successfully using the repository Pydantic model. All raw×scale values are exact Decimal results. Revenue plus other income equals total income for every one of the 20 source columns. The repository detects four conflicts, agreeing with the ledger. The 56-row candidate CSV passes load_financial_csv, including its required-column, model and batch-conflict checks. No full pytest run was performed; pytest is absent in this runtime. No existing target-database facts were compared.

## Remaining before controlled production loading

1. Review and explicitly approve the four RIL re-presentation decisions and metric/basis mappings. Retain original and comparative observations; record preference rather than deleting history.
2. Extract and review consolidated balance sheets, operating cash flows and relevant notes: assets, equity, debt/leases, current balances, receivables/inventory/payables, CFO, capex and interest definition. These reports are already acquired; extraction/review remains. Keep each unavailable until reviewed.
3. Define owners-versus-group profit, continuing/discontinued operations and EPS/corporate-action history; register canonical metric names and analytics applicability.
4. Complete the missing controlled publisher and target-ID resolution; preserve the companion provenance/basis metadata because CSV mapping drops unrecognized fields. Explicitly mark pending/unverified until approved—do not rely on SQL verified defaults.
5. Compare batch facts against existing DB observations, perform controlled loading and reconciliation, then rerun deterministic analytics using approved input IDs.
6. Collect/review HDFC Bank, Tata Motors and L&T history. M2 and issue #14 remain incomplete.

No database writes, repository commits, issue edits or GitHub uploads occurred. The candidate CSV is staging evidence only.

## Reproduction from the evidence archive

Place the original ten source files in upload/ beside the script. Provide the Analyst OS main checkout in analyst-os/. Run python build_ril_tcs_batch.py with fitz, pandas and pydantic available. It reacquires official sources, detects binary differences, constructs/validates observations, writes manifests/conflicts/candidates and performs no database writes. Preserve this package before rerunning because output files are regenerated.

## Repository scope

This commit contains the lightweight manifests, observations, conflict ledger, raw statement text, candidate CSV and validation receipt. Full PDFs, rendered page images and the extraction builder remain in the delivered evidence archive. The manifest records immutable hashes and official reacquisition URLs. The source_file/extraction_file values are historical audit-workspace references, not paths available in this repository.
