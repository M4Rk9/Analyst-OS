# M3 controlled publication verification

Independently verified against the live project `swahxcccptpfxwvhgfxz` on
2026-10-04; counts, validity helpers, proof counts and receipt identity rechecked
2026-10-05 while preparing M4.

| Item | Verified result |
| --- | --- |
| Original approved facts | 629 retained |
| Published reported-core-1 metrics | 43 |
| Metrics accepted by SQL validity helper | 43 |
| Investigation signals | 1 (Tata/TMPV FY2026 cash conversion) |
| Signals accepted by SQL validity helper | 1 |
| Metric / signal provenance records | 43 / 1 |
| Unavailable calculations | 32; no rows manufactured |
| Import ID | `86b61940-09f9-4b94-aff1-dca0aeda6cad` |
| Recorded at | `2026-10-04T17:41:51.697328Z` |
| Request SHA256 | `23d7805cb1cca189871cd4536884b9977e1158cfaa07cd278fd389ed01341898` |
| Receipt SHA256 | `800c3e07e598a2f032a5cf98036765c17553d3ae716aa151121b415bcfd18a67` |
| Reviewed plan SHA256 | `7dfc1c5570ad6d74708dda204562c0db20d2e3d579eb5ec3728806af5ece4319` |
| Applied schema SHA256 | `986a6822875a55e453ede234c46e27a963ce2564d68508d1d8c7e82c887b14db` |

The uploaded receipt hash matched its canonical payload and the durable database
receipt. All 43 committed metric values and their 86 input references matched
the reviewed plan exactly; signal fields also matched. Native controlled loading
was used. No alternative connector inserted financial or derived values.

This completes the M3 production publication gate. It does not attest frontend
rendering, HTTP Data API access, live lock contention or deployment. The M7
checklist retains those separate runtime gates. No comparable-growth, debt,
margin, capex or owner-PAT definitions were invented.
