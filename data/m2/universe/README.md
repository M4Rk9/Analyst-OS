# Pending primary-source history for HDFC Bank, L&T and Tata

Fifteen source PDFs cover FY2022–FY2026: five per company, with the Tata FY2026 entity-continuity proposal explicitly pending. The packet selects reported consolidated core rows only. It does not transpose every note, assign industrial definitions to the bank, or fabricate unavailable metrics.

- [Decision packet](DECISION_PACKET.md): 255 exact candidate IDs, definitions and 15 pinned source keys.
- [Entity scope decision](ENTITY_SCOPE_DECISION.md): original Tata entity into TMPV, with a demerger series break; new CV company stays separate.
- `source_manifest.json`: selected source URLs, PDF hashes/bytes/pages, archive transport/member metadata and scope notes.
- `history_evidence.json`: 590 current/comparative observations, dated-column/row bounding boxes and exact evidence hashes. All remain unverified and non-preferred.
- `extraction_configuration.json`: explicit labels and one-based PDF statement pages. Exact labels or columns that cannot be established become gaps.
- `reconciliation_ledger.json`: 90 passing checks for reported income, balance-sheet totals, equity/liability totals and BS/CF cash definitions. This is not a complete line-by-line cash bridge or an adjusted comparability audit.
- `conflict_ledger.json`: 40 changed comparative keys, with all source values retained and current-year keys withheld.
- `candidate_facts_validation_only.csv`: 255 unverified, non-preferred candidates; never an approval or executable import.
- `review_index.json`: candidate/withheld IDs and catalog/evidence/CSV fingerprints.
- `review_template.json`, `pending_load_plan.json`: reproducible empty-review baselines; zero proposed inserts, no target attestation.
- `retrieval_inventory.json`, `tata_exchange_retrievals.json`, `tata_exchange_comparison.json`: retrieval attempts, successful alternate primary filings and selected statement-version checks. Earlier issuer HTTP 403s do not mean the corresponding report is missing: NSE copies were retrieved.

HDFC FY2025 uses the revised July 25, 2025 filing. Its cover says leadership profiles needed updating. The numeric sequences of the four selected primary statement pages match the original July 14 filing (original PDF 459–462; revised PDF 442–445). Both complete PDF hashes are retained. HDFC's amalgamation scope is explained in the FY2024 report, schedule 18(1), PDF page 472; FY2024 P&L includes the acquired operations from July 1, 2023. Original/current and comparative observations remain separate.

All dates are actual report columns, all units are explicitly printed INR crore, normalization uses Decimal, and signs are retained. Source publication dates not established from the filing are left unavailable. For ZIP filings, use the named bounded PDF member and its own hash/page count; the transport ZIP hash is separate.

## Reproduce and validate

From the repository root with dependencies installed and all selected PDFs under a local source root:

```bash
mkdir /tmp/analyst-os-universe-audit
PYTHONPATH=python python3 python/scripts/audit_universe_history.py --source-root /path/to/pinned-pdfs --output-dir /tmp/analyst-os-universe-audit
PYTHONPATH=python python3 python/scripts/plan_universe_history.py --output /tmp/universe-pending-plan.json
```

Compare the reproduced evidence and reconciliation JSON with the committed artifacts. The dedicated 60 MB limit applies to this offline evidence preparation; the existing 40 MB AI/source-review limit remains unchanged. PDF bytes are not embedded in Git. Retrieved sources have been retained privately.

## Controlled loading after actual review

Keep credentials, ledgers, snapshots, reviewed plans and receipts outside Git. Use the existing verified native TLS connection and CA certificate; never put a password in a command or screenshot.

Before the next native preview, apply the new explicit-reported-amount migration and inspect the changed live schema hash. The publisher requires its validated constraint; an old schema hash cannot be reused.

1. Record actual review decisions for the packet's exact 255 IDs and 15 source keys, including the Tata scope proposal. Keep all 40 conflicts withheld. The pending template cannot approve itself.
2. Export a fresh complete privileged target snapshot using `export_target_snapshot.py --companies hdfc-bank larsen-toubro tata-motors` and the usual project/CA/output arguments.
3. Run `plan_universe_history.py --reviews <private-ledger> --target-snapshot <fresh-snapshot> --expected-project-ref <project-ref> --output <private-plan>`.
4. Run `publish_universe_history.py` with the same ledger/snapshot/plan, returned plan SHA-256, expected project ref and CA path. Default operation is a read-only native preview. This reuses the existing atomic publisher, not a CSV write path.
5. Inspect the live schema inventory/hash and preview before explicit `--apply --expected-schema-sha256 <reviewed-live-schema-sha256>`. Retain the atomic receipt and verify resulting IDs, values, definitions, periods, source/fact provenance and public read permissions.

The RIL/TCS BS/CF packet uses its unchanged separate catalog/ledger and the existing `plan_ril_tcs_load.py` / `publish_ril_tcs.py` commands. Fresh RIL/TCS snapshots must include the 56 already-loaded facts. The planner blocks the two historically zero-encoded dashes even if someone approves them. Old committed receipts and review fingerprints are immutable audit history; all subsequent plans must be regenerated with this guard.
