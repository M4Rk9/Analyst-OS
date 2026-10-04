# Approved M2 history: native preview handoff

Marky approved the exact 318 RIL/TCS BS/CF observations and 255 HDFC Bank/L&T/Tata observations on 2026-10-04 at 14:06:27 UTC. The rationale is: “I accept the cited evidence, source selection and stated definitions.” The original 56 P&L approvals retain their original reviewer time and rationale.

The approval includes all fifteen newly pinned source PDFs and original Tata Motors legal-entity continuity into TMPV with a FY2026 series break. The new CV company remains separate. All 46 conflict keys remain withheld and the two printed-dash candidates remain unavailable.

See [the approval receipt](M2_HISTORY_APPROVAL.json) and the two executable review ledgers:

- [RIL/TCS ledger](../data/m2/ril-tcs/review/marky_approved_reviews.json): 374 approved facts, including the original 56 and new 318; original ten source reviews preserved.
- [Other-company ledger](../data/m2/universe/marky_approved_reviews.json): 255 approved facts and their fourteen source keys. The fifteenth approved report has no conflict-free candidate facts, so its approval is retained in the receipt but it is not scheduled for loading.

These files record a financial decision, not a completed load. The historical decision packets and empty templates retain their preparation-time pending state; the approval receipt supersedes that state for precisely the listed IDs.

## Live prerequisite completed

The merged `explicit_reported_amounts` migration was applied to project `swahxcccptpfxwvhgfxz` on 2026-10-04. A read-only check confirmed `facts_explicit_reported_amount` is validated. There are still 56 live financial facts: RIL 26 and TCS 30. No financial fact, source, review ledger or receipt was written by this approval preparation.

## Generate fresh native previews

After merging this PR, update your local checkout and run the following in the repository root, using the same trusted CA certificate that worked for the first load:

```powershell
git pull --ff-only
python -m pip install -e ".[database]"
$env:PYTHONPATH = "python"
python -m scripts.preview_approved_history --ssl-root-cert "C:\path\to\your-ca.crt" --output-dir "data/processed/m2-approved-preview-20261004"
```

Replace the certificate path with its actual local path. Use a new output directory for each run. The command uses `ANALYST_OS_DATABASE_URL` if it is already set; otherwise it requests the complete PostgreSQL connection URL with hidden input. Use the existing direct/session URL on port 5432 and the actual password, without placeholder brackets. Reserved password characters must be URL-encoded. Keep the URL out of chat and committed files.

The command opens a native TLS-verified, privileged read-only connection, obtains fresh scoped snapshots, regenerates both plans, checks the live schema and returns controlled previews. It has no apply option. The final `preview-summary.json` is created only after both previews succeed. A failed run can leave partial files; those are not a complete preview.

Expected results if the target remains unchanged:

| Packet | Proposed inserts | Already present | Withheld conflict keys |
|---|---:|---:|---:|
| RIL/TCS | 318 | 56 | 6 |
| HDFC/L&T/Tata | 255 | 0 | 40 |

Both previews must report zero production writes. The RIL/TCS plan also retains two blocked dash candidates. Inspect all unexpected blocks or existing rows before considering application.

Send `preview-summary.json` and both `*.native-preview.json` files for review. The snapshots and reviewed plans are retained locally for the publisher. Fresh snapshots expire after 24 hours; regenerate them if necessary.

## Completion boundary

This environment has connector access for the prerequisite migration and read-only verification, but no native database credential. It therefore has not produced live native previews. Offline approval validation cannot substitute for those previews.

After inspecting the native previews, the remaining actions are explicit controlled application with reviewed plan/schema hashes, receipt preservation, independent provenance verification and updating issue #14 and the release checklist. If all approved facts load successfully, the expected total is 629 facts: RIL 176, TCS 198, HDFC Bank 93, L&T 99 and Tata 63. M2 remains open until those checks pass.
