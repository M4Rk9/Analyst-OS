# Official source and P&L inspection notes

Inspection by **Codex (AI-assisted evidence review)** on 2026-10-04. This records actual source corroboration and visual inspection, not human approval, authenticated reviewer identity or permission to load. No approved ledger is created.

All ten issuer URLs were re-fetched successfully. Returned bytes, SHA-256 and page counts match the corrected manifest; the retrieval receipt records timestamps and the RIL FY2024 redirect to its issuer's dated reports directory. This confirms the pinned copies at those retrieval times, not permanent URL immutability.

The nine current supplied RIL/TCS files available for this check matched their pinned versions except TCS FY2026, whose upload still matches the separately recorded uploaded hash. RIL FY2022 was inspected from the official re-fetch and the earlier supplied `AR_2021-22.pdf`, both matching the pinned hash.

## Visual table checks

Rendered the following ten P&L table pages from freshly fetched official bytes and inspected the consolidated heading, INR-crore unit, current/comparative headers and six extracted metric rows. This does not assert inspection of every note or full financial-statement transcription.

| Company | Report FY | PDF page | Printed page | Inspection finding |
|---|---:|---:|---|---|
| RIL | 2022 | 198 | 393 | Consolidated P&L; original FY2022 scope; four keys still conflict with the next report's comparative |
| RIL | 2023 | 209 | 414–415 | Re-presented FY2022 comparative; continuing/discontinued components shown separately before full group profit |
| RIL | 2024 | 111 | 218–219 | Group profit row distinct from continuing/discontinued components |
| RIL | 2025 | 100 | 196–197 | Profit After Tax subtotal is distinct from profit for the year after associates/JVs |
| RIL | 2026 | 101 | 198–199 | Same subtotal/group-profit distinction; group profit includes NCI |
| TCS | 2022 | 245 | 245 | Current/comparative amounts on the left pane; OCI on continuation pane is outside the selected rows |
| TCS | 2023 | 191 | 191 | Group profit includes NCI; shareholder profit is a distinct row |
| TCS | 2024 | 181 | 181 | Group profit is distinct from shareholder profit; no EBITDA/EBIT inference |
| TCS | 2025 | 181 | 179 | Visual digits corroborate the recorded font-glyph correction and spacing cleanup |
| TCS | 2026 | 167 | 197 | Official reacquired copy, not the differing upload; group profit distinct from shareholder profit |

For the six selected fields, all 120 current/comparative raw amounts match the labelled dated columns, including the competing observations. Geometry checks retain original extracted text and bounding boxes. Correct arithmetic or visual agreement does not approve comparability, a preferred series or a different metric definition.

## Metadata correction

The TCS FY2026 manifest paired the official SHA-256 with the upload's 30,438,344-byte size. The pinned official copy is **22,126,348 bytes**. Set `bytes` to the official count and retain the old size as `uploaded_bytes`, alongside the already retained differing upload hash. No source hash, financial amount, CSV byte hash or selected observation changes.

This correction changes the full-catalog digest from `4ca38d331e7240ff333ec4d402b0e4b2c2baabef46aeb43227e8cb0421c94d8d` to `e8d4dc3d24cbef2ef81c37f2eadefcd40b0862d66cf73e65da1ec6549eab6c41`. The committed index, pending template and zero-write plan were regenerated. Any private decisions bound to the old digest must be reviewed again; never rewrite their hashes to make them pass.

## Decision recommendation

The 56 conflict-free P&L rows are ready for an explicit source/fact decision **under the six definitions in the packet**, with the remaining 320 candidates pending. Approving the subset requires actual decisions for the ten official source keys and the selected exact observation IDs. Four P&L conflicts and two cash-flow conflicts remain excluded. No actual target has been inspected, so this is review readiness, not target load readiness.

Full finance costs are not interest expense; group profit is not owner PAT. Do not infer debt, EBIT/EBITDA, COGS or capex from these rows. RIL scope changes require care before growth/ratio comparisons. The current frontend's P&L chart allowlist only includes revenue among these six fields, so loading this subset alone will not populate every intended financial panel.
