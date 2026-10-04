# M2 five-company controlled load verification

Verified on 2026-10-04 in project `swahxcccptpfxwvhgfxz`: **629 approved, verified, preferred financial facts**. The two new native operator loads committed 318 RIL/TCS observations and 255 HDFC Bank/L&T/Tata observations. The original 56-fact load and its immutable receipt are preserved.

| Company | Loaded facts | Selected source reports represented in the database |
| --- | ---: | --- |
| Reliance Industries | 176 | FY2022–FY2026 |
| Tata Consultancy Services | 198 | FY2022–FY2026 |
| HDFC Bank | 93 | FY2022–FY2026 |
| Larsen & Toubro | 99 | FY2022–FY2026 |
| Tata Motors / original entity into TMPV | 63 | FY2022, FY2023, FY2025, FY2026 |

The reviewed primary-source inventory covers 25 reports. There are 24 source-document rows and 24 reporting-period rows in the database: Tata's FY2024 report remains pinned and approved in [the approval record](M2_HISTORY_APPROVAL.json), but every selected current-year core candidate for that year is withheld by conflict detection. No financial fact or empty source/period row was invented to fill that gap. This is reviewed selected core statement history, not full annual-report note transcription or complete financial coverage.

## Committed receipts

| Load | Import ID | Recorded transaction time (UTC) | Inserted | Already present |
| --- | --- | --- | ---: | ---: |
| RIL/TCS BS/CF | `843757eb-2755-4d17-8343-cf6145be9634` | 2026-10-04T15:16:04.987739Z | 318 | 56 |
| HDFC Bank/L&T/Tata | `29ec689a-17c3-4e01-a4ff-bb91ff9594e4` | 2026-10-04T15:21:04.300772Z | 255 | 0 |

- RIL/TCS receipt SHA-256: `b4a674e2f532013d70e4471d819918777d2e3f46541dec4860ee8203e9eaeb9c`.
- Other-company receipt SHA-256: `3f9065a3ef5808417ba402b82b9f1aa26ec5c42b20f76f872ae550d48ecbf1fb`.
- Reviewed and independently revalidated schema SHA-256: `8be735c5872b0ed9fa14f00a1d9fedc51afb70c9d122dd13905e32d55d0413b6`.

The complete operator receipts were supplied for independent verification and remain retained private audit artifacts, alongside the private database receipts. Their canonical SHA-256 values and canonical payloads match the stored records. The first receipt remains unchanged; see [the historical first-load record](M2_APPROVED_LOAD_STATUS.md). `recorded_at` is the transaction timestamp, not an independently measured commit time.

## Independent verification

The read-only audit checked all 629 observation IDs against the exact approved ledgers and validated catalogs. Every evidence and definition SHA-256 and canonical payload matched the pinned repository inputs. It matched inserted fact/source UUIDs, catalog and review fingerprints, company, period type/start/end/year, metric, printed value, raw numeric value, normalized INR, currency, scale, source URL/document hash, PDF page and label, verified status and preferred selection. There were zero mismatches, zero facts without provenance and zero missing matching source-provenance links. The database has two catalogs, three review ledgers and three committed receipts. The old 56 observations retain their original approval provenance.

The exact loaded set equals the approved set. All **46 conflicting keys remain withheld**, and the **two printed-dash candidates remain unavailable**. No unsupported EBIT, EBITDA, recurring profit, comprehensive debt, conventional capex or comparable-growth proxy was loaded. Marky's approved FY2026 Tata series break remains recorded; the new commercial-vehicle entity is separate.

The current publisher schema inventory passes its integrity checks and equals the reviewed fingerprint. RLS, validated numeric-display/normalization constraints, immutable provenance triggers and read-only browser grants remain intact. A separate `SET LOCAL ROLE anon` query read 629 public facts, 24 source documents and 24 periods; no public table grants browser writes, and browser roles have no private ingestion schema usage. This verifies database role behavior, not HTTP Data API or deployed browser behavior.

## Post-load deterministic analytics check

[M2_POST_LOAD_VERIFICATION.json](M2_POST_LOAD_VERIFICATION.json) retains receipt bindings, verified totals and 75 post-load formula checks across five companies and FY2022–FY2026. The existing version 1.0 current-ratio, working-capital and CFO/positive reported consolidated group-profit formulas were run only on inputs independently matched to the loaded facts. Independent Decimal division/subtraction reproduced every result: 43 were available and 32 correctly unavailable. Each row retains input observation IDs and exact normalized values. These checks satisfy the post-load rerun and calculated-result spot-check acceptance criteria; they are offline evidence, not publication of derived rows.

Missing facts, nonpositive profit bases and absent bank-specific industrial-ratio inputs stay unavailable. No industrial ratio is inferred for HDFC Bank; no capex/debt proxy, adjusted profit, inter-year growth or Tata series continuity is inferred. The CFO/group-profit check uses reported group profit and cannot be described as recurring-earnings cash conversion. Derived publication needs explicit definitions, provenance and an appropriate controlled output path.

## Milestone and release boundary

**M2 selected primary-source history population is verified complete.** Issue #14's source selection, review, normalization, provenance, conflict recording, controlled loading, post-load deterministic checks and unavailable-value requirements have evidence. This does not make the application production-ready.

Remaining M3/M4/M7 runtime work includes publishing validated derived outputs, binding reported metric definitions to frontend consumers, HTTP Data API checks, AI runtime validation, live multi-session contention/recovery exercises, Cloudflare Pages deployment, real security headers, browser/accessibility checks and final release CI/screenshots. The UI must continue to show unavailable values for unsupported analytics and withheld observations.
