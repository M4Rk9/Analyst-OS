# RIL/TCS review-bound import planning

> **Live status update, 2026-10-04:** The approved 56-fact P&L subset and ten sources are now loaded and independently verified. The remaining 320 candidates are pending and six conflict keys are withheld. See [approved load evidence and remaining gates](../../../../docs/M2_APPROVED_LOAD_STATUS.md). Statements below about zero production loads or all 376 candidates being pending describe the committed offline baseline, not the current target. Pending templates remain unchanged.

The offline planner combines 764 observations from batches 1 and 2, selects 376 current-year candidates, and withholds six unresolved conflicting keys. It preserves the full companion metadata, including source hashes/pages/labels, reporting basis, source column, instant-versus-duration measurement, as-of dates and exact metric definitions.

The committed plan proposes **zero inserts**: all source/fact reviews are pending and no target snapshot has been supplied. A merged evidence PR, valid arithmetic or a CSV schema pass is not an approval. The separate provenance schema, snapshot exporter and controlled publisher are now implemented; this offline component still does not complete an M2 load.

| Artifact | Purpose |
|---|---|
| [PNL_DECISION_PACKET.md](PNL_DECISION_PACKET.md) | First 56 P&L decisions with exact IDs, values, sources and definitions; still pending |
| `pnl_source_audit.json` | PDF label-row/dated-column checks for all 120 P&L observations, not approvals |
| `official_retrieval_receipt.json` | Fresh issuer re-fetch results for all ten pinned PDFs |
| [SOURCE_REVIEW_NOTES.md](SOURCE_REVIEW_NOTES.md) | Actual visual inspection scope and TCS FY2026 file-size correction |
| `pnl_metric_definitions.json` | Six explicit group P&L definitions; combines with batch2's 43 metric definitions |
| `catalog_index.json` | Source-review keys and all 376 candidate IDs, evidence/definition fingerprints and page/measurement references |
| `review_template.json` | Empty, pending review ledger bound to the entire catalog digest |
| `load_plan.json` | Reproducible current dry run: 376 blocked candidates, six withheld keys, no inserts or writes |
| `target_snapshot_schema.json` | Format contract for the implemented privileged target exporter; not an actual snapshot |

## Run the current plan

From the repository root:

```bash
PYTHONPATH=python python python/scripts/plan_ril_tcs_load.py \
  --reviews data/m2/ril-tcs/review/review_template.json \
  --output data/m2/ril-tcs/review/load_plan.json
pytest
ruff check python
```

The script rechecks batch2's exact accounting bridges and receipt, batch1's income identities, both CSV byte hashes, model validity and candidate-to-observation equality before planning. Git attributes require LF for M2 evidence. Batch1's receipt now hashes the committed LF CSV; its original CRLF archive hash is retained separately. No financial amounts changed.

## Review records

A trusted reviewer copies the pending template and records source and fact decisions after inspecting the cited evidence and definition. Review keys come from `catalog_index.json`: source keys bind company and official PDF hash, while fact keys are exact observation IDs. An approved or rejected decision requires `status`, `reviewer`, a timezone-aware `reviewed_at` and a substantive `rationale`. Unlisted entries remain pending.

The ledger's `catalog_sha256` binds all observations, their source manifest, the 49 definitions and the current-year/conflict-exclusion policy. Changing a value, source, scope, measurement or definition invalidates the previous ledger. Decisions for unknown or withheld facts are rejected. There is no conflict-resolution override in this planner; the six keys require a separate reviewed resolution package before they become eligible.

These records are explicit attestations from a trusted local workflow. They do not authenticate the named reviewer or create a digital signature. Do not generate approved decisions merely to make an import plan nonempty. No synthetic approvals or target exports are committed here.

## Target snapshot contract

A target export must conform to `target_snapshot_schema.json` and include:

- The exact Supabase `project_ref`, a timezone-aware capture time, `complete=true`, and both company slugs in the scope.
- Every source document and financial observation for the scoped companies, including unverified, conflicting and non-preferred rows. Use a privileged, trusted exporter; an anon export cannot establish completeness because RLS hides relevant rows. Completeness is attested by the exporter, not independently proven by the planner.
- For each existing fact, its database ID, source-backed `record`, the **actual stored** `normalized_value`, basis, measurement/as-of metadata, definition fingerprint, quality status and preferred flag. Stored normalization must equal raw value times scale. The provenance migration persists this metadata privately. Do not invent it for legacy records; they need reviewed source/provenance mapping before this contract can be satisfied.

A target-aware invocation adds `--target-snapshot /trusted/path/snapshot.json --expected-project-ref <actual-project-ref>`. No target file or project reference is fabricated as a default. Snapshots must be no more than 24 hours old and not future-dated. The API requires an explicit expected project reference even if the snapshot itself names a project.

The planner blocks a different value/currency, source-URL/hash replacement, different period start/basis/measurement/definition, an existing pending/rejected/conflicting source, or a silent preferred-source replacement. Identical, verified, preferred observations produce `already_present`, not another insert. Existing unverified facts are not silently upgraded. Plan output hashes bind the review ledger and snapshot for later audit.

## Controlled loading remains separate

The offline planner's `apply_ready` remains false and it has no network client, credentials, SQL generation or apply mode. The separate [controlled publisher](../../../../docs/CONTROLLED_PUBLISHING.md) resolves UUIDs and commits approved facts, provenance and an immutable receipt atomically after a fresh locked target check. The [snapshot exporter](../../../../docs/TARGET_SNAPSHOT.md) and [provenance schema](../../../../docs/PROVENANCE_SCHEMA.md) are implemented and locally tested, but actual target preflight/migration/runtime verification and loading remain pending.

The focused packet corroborates the 56 P&L candidates; it does not audit the other 320 balance-sheet/cash-flow candidates or resolve the six conflict keys. Real reviews, remaining definitions, derived-output provenance, other-company history and release gates remain in [M2_NEXT_STEPS.md](../../../../docs/M2_NEXT_STEPS.md).

## Reproduce the P&L corroboration

Provide a trusted directory containing all ten exact pinned **official** PDFs, using manifest filenames. For TCS FY2026, use the official reacquired copy; the differing upload is rejected. The script performs no downloads, database calls, approvals or financial-value substitutions:

```bash
PYTHONPATH=python python python/scripts/audit_ril_tcs_pnl.py \
  --source-root /trusted/local/official-reports \
  --output-dir data/m2/ril-tcs/review
```

It validates PDF hashes, byte/page counts and all 120 signed amounts against exact labels and dated columns. A matching number elsewhere on the page or in the wrong column does not pass. Unavailable, dashed and footnoted numeric text is not guessed. The geometry method is scoped to these P&L layouts; unsupported/ambiguous layouts stop instead of falling back to page-wide matching. Digit-glyph cleanup is explicitly recorded and requires the visual check noted above. PDF rendering/geometry may vary between PyMuPDF versions; retain the original audit if replay output differs and investigate rather than rehashing approval records.

The TCS size correction changes the catalog digest; the committed pending artifacts have been regenerated. A previous private approved ledger must undergo a new review, never an automatic hash rewrite.
