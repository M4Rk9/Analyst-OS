# M4 publication verification — first RIL insight

Verified on 2026-10-05 against Supabase project `swahxcccptpfxwvhgfxz`. This is partial M4 runtime completion: one RIL business brief is published; five-company AI coverage and browser rendering are not yet verified.

## Genuine generation and explicit review

The operator generated the draft locally using `qwen2.5:3b`. Installed model digest: `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`. The pinned RIL FY2026 source is `e8b13e22-456e-49f2-a993-fd30dbd12db4`, SHA256 `ed8affb5e7d2da16e19ed925be925b04a8ee581038ff75ada1a5d0cb7309c1e0`.

The model produced one low-confidence business-scope interpretation. Its original page-2 citation did not support every clause. Review added an exact page-4 quotation covering the energy-security and consumer-business aims, rebuilt the pending review, and obtained Marky's explicit approval of candidate 0. The original draft remains separate; no rejected output was published. This is a model interpretation with reviewer-corrected citations, not evidence that the model's initial citations were complete.

## Publication binding

| Item | Verified value |
| --- | --- |
| Import ID | `9382a7b9-1733-49c7-9833-bafd7f5585cb` |
| Insight ID | `16082599-4b38-5079-9eaf-1754cf07c910` |
| Committed at (UTC) | `2026-10-05T16:09:07.942827Z` |
| Draft SHA256 | `92f5529caa04162820f523da62b1342d54149fb4fe5dd4845a9b1cd5ec72092a` |
| Review SHA256 | `ff04d59e6d9ceb5ed7c3539347b7baf883fd9dc47ce73c593634645bea4b7bc9` |
| Request SHA256 | `93f9e50ebc22418eda26c567ae3cc08c2c58d3f96770a45d26cbdb6ed4769172` |
| Plan SHA256 | `3d462d035f358433a6b926e8f74365b767f2d22ddcdf7513eae203dbcaff576e` |
| Schema SHA256 | `8fd69be480b49d2eab5c6df052370540c1930792b87682cc0c93d26d412d2a3d` |
| Receipt SHA256 | `897f6598226c838b39edecba9440a784ef2f97a49e72006dcf71728820d5dd5b` |

The uploaded dry-run plan had zero writes, one approved candidate, one insertion and no already-present rows. Its canonical hash matched the summary. Independent live queries confirmed the uploaded receipt exactly equals the durable receipt; its canonical hash is valid; the public row and private request row match the reviewed plan; the PDF/model hashes, approved review, draft binding and private provenance match. There is exactly one live AI insight.

An actual SQL SELECT under the `anon` role returned the validated insight with two citations. Anonymous SELECT permission is present; INSERT/UPDATE/DELETE permissions and private `insights` schema usage are absent. This verifies database-role visibility, not HTTP Data API configuration or real-browser rendering.

Existing totals remain 629 financial facts, 43 calculated metrics and one investigation signal.

## Remaining M4 gates

- Generate, inspect, explicitly review and publish supported interpretations for TCS, HDFC Bank, L&T and the original Tata/TMPV entity scope.
- Verify browser evidence links, reviewer label, mobile/keyboard rendering and public operation with Ollama stopped.
- Complete HTTP Data API/read-only checks and remaining release checks in M7.
- Preserve private drafts/reviews/receipts locally; do not commit credentials or full source-page text.

No fixed number of sections or insights is promised where evidence is insufficient. Receipt/replay recovery code exists; this first successful commit does not establish that all concurrency or lost-response recovery cases have been exercised.
