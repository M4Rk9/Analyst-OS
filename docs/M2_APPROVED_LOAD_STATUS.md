# M2 approved RIL/TCS load status

As of 2026-10-04, the first controlled P&L load is committed: 56 verified preferred observations (26 Reliance Industries, 30 TCS), ten pinned official source documents and ten reporting periods. Marky approved this exact subset under the P&L packet's definitions. The private ledger and full receipt remain operator audit records.

## Verified evidence

- Receipt import ID: `9c70584d-84d5-4663-a939-7fe1c842bda0`.
- Commit recorded at: `2026-10-04T12:18:54.438445Z`.
- Receipt SHA-256: `05c4e1f6d5d6bcb83f69a87f5d090cba0f42d36e3afcb2d51245362345cd09a3`.
- Reviewed plan SHA-256: `5e71d16b0afda62bf37e0492db89c9db143857c40d35950e64291ef4ae5e7dd1`.
- Schema inventory SHA-256: `9a6951b9c0e8485687215bf1fc493a53c92c1e3a72566fa46682375ac7347874`.
- Catalog SHA-256: `e8d4dc3d24cbef2ef81c37f2eadefcd40b0862d66cf73e65da1ec6549eab6c41`.

Independent privileged read-only verification matched all observation IDs, raw and normalized values, period/company/metric references, source pages/labels, review and evidence fingerprints, source/fact UUIDs and stored receipt payload. The database contains 56 fact provenance records, ten source provenance records, one review ledger and one committed receipt. The 320 pending candidates and six withheld conflict keys are absent.

A subsequent read-only transaction with `SET LOCAL ROLE anon` confirmed visibility of the 56 preferred facts, ten source documents and ten reporting periods. The public company join returned RIL 26, TCS 30, HDFC Bank 0, Tata Motors 0 and Larsen & Toubro 0. This verifies public database permissions, not an HTTP REST response, deployed browser rendering or derived analytics.

PR #24 is confirmed merged at commit `c60db629cc708319ecea47c6ba23f57426d17875`. The native operator preview and apply succeeded using the verified client TLS path. This does not attest encryption of the pooler's internal database leg.

## Next gate

The [consolidated completion package](M2_COMPLETION_PACKAGE.md) now provides the audited 318-fact RIL/TCS BS/CF decision packet and the 255-fact other-company core packet. Two historical dash-to-zero candidates remain unavailable; the six original conflict keys stay withheld under Marky's decision. Fifteen new primary source PDFs are pinned for HDFC Bank, L&T and the proposed Tata/TMPV history, with forty further comparative conflicts withheld.

Actual new reviews, fresh native snapshots/previews and controlled apply/receipt verification remain required before M2 or issue #14 can close. Derived outputs, HTTP/browser checks and deployment are subsequent release gates. The first receipt and original catalog approval remain immutable; regenerate all future plans with the new numeric-display guard.
