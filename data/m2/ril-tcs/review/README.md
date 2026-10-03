# RIL/TCS review-bound import planning

The offline planner combines 764 observations from batches 1 and 2, selects 376 current-year candidates, and withholds six unresolved conflicting keys. It preserves the full companion metadata, including source hashes/pages/labels, reporting basis, source column, instant-versus-duration measurement, as-of dates and exact metric definitions.

The committed plan proposes **zero inserts**: all source/fact reviews are pending and no target snapshot has been supplied. A merged evidence PR, valid arithmetic or a CSV schema pass is not an approval. This is a tested planning component, not a database publisher or a completed M2 load.

| Artifact | Purpose |
|---|---|
| `pnl_metric_definitions.json` | Six explicit group P&L definitions; combines with batch2's 43 metric definitions |
| `catalog_index.json` | Source-review keys and all 376 candidate IDs, evidence/definition fingerprints and page/measurement references |
| `review_template.json` | Empty, pending review ledger bound to the entire catalog digest |
| `load_plan.json` | Reproducible current dry run: 376 blocked candidates, six withheld keys, no inserts or writes |
| `target_snapshot_schema.json` | Format contract for a future privileged, complete target export; not an actual snapshot |

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

A later target export must conform to `target_snapshot_schema.json` and include:

- The exact Supabase `project_ref`, a timezone-aware capture time, `complete=true`, and both company slugs in the scope.
- Every source document and financial observation for the scoped companies, including unverified, conflicting and non-preferred rows. Use a privileged, trusted exporter; an anon export cannot establish completeness because RLS hides relevant rows. Completeness is attested by the exporter, not independently proven by the planner.
- For each existing fact, its database ID, source-backed `record`, the **actual stored** `normalized_value`, basis, measurement/as-of metadata, definition fingerprint, quality status and preferred flag. Stored normalization must equal raw value times scale. The current schema does not persist all this metadata; do not invent it for legacy records. Such records need a reviewed provenance mapping/schema extension before this contract can be satisfied.

A target-aware invocation adds `--target-snapshot /trusted/path/snapshot.json --expected-project-ref <actual-project-ref>`. No target file or project reference is fabricated as a default. Snapshots must be no more than 24 hours old and not future-dated. The API requires an explicit expected project reference even if the snapshot itself names a project.

The planner blocks a different value/currency, source-URL/hash replacement, different period start/basis/measurement/definition, an existing pending/rejected/conflicting source, or a silent preferred-source replacement. Identical, verified, preferred observations produce `already_present`, not another insert. Existing unverified facts are not silently upgraded. Plan output hashes bind the review ledger and snapshot for later audit.

## Before any writer

`apply_ready` is always false. There is no network client, credential handling, SQL generation or `--apply` mode. Proposal rows retain a nested source-backed record and companion provenance rather than dropping metadata through the CSV loader.

Still required: persist review/definition/measurement provenance in a reviewed schema extension; replace implicit verification defaults with explicit status handling; resolve company/period/source/fact IDs; create and verify a privileged snapshot exporter; implement atomic, idempotent writes with a fresh in-transaction conflict check; verify target migrations and runtime RLS; and produce a real load receipt. A stale offline snapshot must never be used as authorization for a later write. Analytics/AI and other-company coverage remain separate gates in [M2_NEXT_STEPS.md](../../../../docs/M2_NEXT_STEPS.md).
