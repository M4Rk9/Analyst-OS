# M2 consolidated completion package

**Superseded status (2026-10-04):** the approved loads have committed and all 629 facts were independently verified. See [M2_FIVE_COMPANY_LOAD_STATUS.md](M2_FIVE_COMPANY_LOAD_STATUS.md). The preparation/preview instructions below are historical; do not apply these plans again as a new load.


Current decision: Marky approved the exact 573-fact package and fifteen new sources on 2026-10-04. The explicit-number constraint is live and validated; financial publication remains pending. See [approval records and native preview instructions](M2_APPROVED_HISTORY_PREVIEW.md). The preparation-time inventory and findings below are retained for audit.

Baseline: PR #25 merged at `1d27e28c8412097b38d37f41e9e9ed177464626a`. Preparation performed on 2026-10-04. **M2 remains open pending explicit new review and controlled publication.** This package completes the source retrieval, core normalization, source-row audit, conflict recording and loading-tool preparation that can proceed under the existing approval boundary.

## Verified facts versus review gaps

| Company | Pinned history | Already loaded | New conflict-free packet | Unavailable / withheld |
|---|---|---:|---:|---|
| Reliance Industries | FY2022–FY2026; 5 previously approved PDFs | 26 P&L facts | 150 BS/CF facts | 2 printed-dash candidates unavailable; existing conflict keys withheld |
| TCS | FY2022–FY2026; 5 previously approved PDFs | 30 P&L facts | 168 BS/CF facts | Existing conflict keys withheld |
| HDFC Bank | FY2022–FY2026; 5 NSE-filed PDFs, FY2025 revised | 0 | 93 core facts | Changed comparative keys withheld; bank definitions apply |
| Larsen & Toubro | FY2022–FY2026; 5 issuer-hosted PDFs | 0 | 99 core facts | Changed comparative keys withheld; financial-services finance costs not aliased |
| Tata Motors | FY2022–FY2026; original entity into TMPV proposed | 0 | 63 core facts | FY2026 mapping needs acceptance; changed comparative keys withheld; new CV company separate |

The two pending decision packets total **573 facts** (318 RIL/TCS + 255 other-company core facts). None is newly approved or loaded. There are **46 recorded conflict keys** across the two catalogs (6 existing + 40 new), and **2 printed-dash candidates** which cannot become numeric zero. There is no missing annual-report PDF in the proposed five-year inventory; scope/definition review and publication are the remaining blockers. The inventory is established from retrieved issuer/NSE primary artifacts, not from an assumed GitHub Datasets contents list.

The first live controlled load remains exactly 56 verified preferred P&L facts. A fresh read-only database count during this preparation confirmed RIL 26, TCS 30 and the other companies zero. See [the immutable first-load status](M2_APPROVED_LOAD_STATUS.md) for its retained receipt and prior full provenance verification. No production writes were performed for this package.

## Ready for explicit review, then controlled loading

1. [RIL/TCS BS/CF decision packet](../data/m2/ril-tcs/review/BS_CF_DECISION_PACKET.md): exact 318 source-corroborated IDs and definitions. The audit binds all 644 BS/CF observations to their pinned source pages; 637 pass explicit numeric label/section/date/sign checks. The seven failures include the two unavailable current-year dashes and five comparative rows. Existing 138 reconciliation checks remain reproducible, but old extraction arithmetic does not justify treating a printed dash as zero.
2. [Other-company decision packet](../data/m2/universe/DECISION_PACKET.md): exact 255 IDs, 15 new source keys, reported-scope definitions and 40 withheld conflicts. All 590 current/comparative core observations bind exact printed labels, dated columns and INR-crore amounts; 90 additional core identity/definition checks pass. This is selected core statement coverage, not complete note transcription or a full CF bridge.
3. [Tata entity scope decision](../data/m2/universe/ENTITY_SCOPE_DECISION.md): accept original-entity continuity into TMPV with a FY2026 series break, keep the new CV company separate and keep changed comparative keys withheld. That proposal is part of the new packet's approval boundary.

Exact fields ready for review are listed by company/year in these packets, their JSON indexes and `candidate_facts_validation_only.csv`. Source approval, numerical corroboration and schema validation are distinct from fact approval. No EBITDA, EBIT, adjusted revenue, comprehensive debt, conventional capex, recurring-profit or comparable-growth proxy is inferred. Unsupported analytics inputs stay unavailable and are not a reason to invent a financial value.

The additional explicit-number constraint is prepared in `supabase/migrations/20261004133000_explicit_reported_amounts.sql`. It validates verified source display amounts against raw numeric values and rejects dashes, footnotes, missing text and wrong signs. Existing unverified evidence and immutable approvals/receipts are retained. The publisher requires this validated constraint before any subsequent preview/apply.

## Remaining actions to close M2

- Marky records actual financial decisions for the two exact packets, including the Tata mapping and new 15-source selection. The original 56-fact/10-source approval and its rationale stay unchanged. Unlisted IDs stay pending; all conflict keys and dash candidates stay withheld/unavailable.
- Apply the explicit-number migration after merge if not yet recorded as live. It must validate existing verified rows without changing their values or reviews; an unsupported verified display stops the migration. Inspect the updated schema hash.
- Export fresh privileged native snapshots for RIL/TCS and the other three companies, regenerate the two private reviewed plans, inspect schema/plan fingerprints and obtain native controlled previews. Pending offline plans propose zero inserts and cannot substitute for this step.
- Explicitly apply through the atomic publisher with reviewed hashes, preserve both receipts, and independently verify all resulting facts/provenance and intended public read behavior.
- Only after those checks update issue #14, roadmap and release checklist to mark M2 complete. M3/M4 runtime outputs, browser rendering and deployment checks remain subsequent release work and do not become completed merely because M2 source history is loaded.

No new private database credential was available to this execution environment. The previous operator's hidden-password native TLS session is required for authenticated preview/apply; financial SQL writes through an alternate connector were not used. The stored schema hash from the first load is historical and must be checked against the next live preview.

## Review wording for the concrete package

Use this only after inspecting and accepting the linked evidence and definitions:

> I approve the exact 318 RIL/TCS BS/CF observations and the exact 255 HDFC Bank/L&T/Tata observations listed in the two decision packets, and the fifteen newly pinned source PDFs. Record me as reviewer Marky. I accept their cited evidence and reported consolidated definitions, including original Tata Motors legal-entity continuity into TMPV with a FY2026 series break and the new CV company kept separate. Keep all 46 conflict keys withheld and the two printed-dash candidates unavailable. My rationale is that I accept the cited evidence, source selection and stated definitions. Prepare fresh controlled load previews.

This example is not an approval, reviewer timestamp or ledger entry. A subsequent actual statement is needed because Marky's existing explicit authorization approved only 56 P&L facts and expressly kept the other 320 candidates pending.
