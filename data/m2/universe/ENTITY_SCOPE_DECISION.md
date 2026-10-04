# Tata Motors FY2026 entity scope decision — pending

The proposed five-year history follows **the original Tata Motors Limited legal entity**, renamed **Tata Motors Passenger Vehicles Limited (TMPV)** for FY2026. It records a series break and retains original reported scopes. Acceptance must be explicit in the financial/source review. No ticker/seed mutation or pro-forma comparability is authorized by this packet.

| Evidence | Pinned artifact / location | Implication |
|---|---|---|
| Exchange cover identifies TMPV as formerly Tata Motors Limited | `tata-motors_2026_tmpv.pdf`, PDF page 1; URL and hash in `source_manifest.json` | Supports original-entity continuity proposal |
| Composite scheme includes CV demerger and PV amalgamation | Same PDF, note 50(I), PDF pages 436–437 (printed 431–432) | Appointed July 1, 2025; effective October 1, 2025 |
| FY2025 P&L comparative is re-presented | Same PDF, PDF page 332 (printed 327), note 50 | Preserve the original FY2025 report and withhold changed comparative keys |
| Reported FY2026 profit includes exceptional disposal gain and discontinued operations | Same PDF, PDF page 332 and note 50(I), page 437 | Group profit is not recurring profit; do not infer a growth/earnings normalization |
| New commercial-vehicle company has a different comparative duration | `tata-motors_2026.pdf`, PDF page 269 (printed 267) | Comparative June 23, 2024–March 31, 2025 cannot be relabelled April–March FY2025 |

The CV alternative was retrieved from `https://cv.tatamotors.com/assets/cv/files/AnnualReportFY26.pdf`; its bytes, SHA-256, page count and retrieval record are retained in `retrieval_inventory.json`. It is outside the proposed load catalog. The selected TMPV report is an NSE-filed primary report; source approval remains pending.

Two source-version checks also support this proposal: the FY2023 and FY2025 NSE filings have the same numeric token sequences on the selected BS, P&L and CF pages as the issuer-hosted copies. They have different document hashes and one extra exchange cover sheet; see `tata_exchange_comparison.json`. This is a statement-page comparison, not a claim that the complete PDFs are byte-identical or that all report notes were reviewed.

**Concrete decision:** accept the original-entity TMPV continuity mapping, retain a FY2026 series break and reported-operation definitions, keep the new CV entity separate, and retain all changed comparative keys withheld. If rejected, leave Tata FY2026 source/fact reviews pending and prepare a new entity-specific catalog before any load.
