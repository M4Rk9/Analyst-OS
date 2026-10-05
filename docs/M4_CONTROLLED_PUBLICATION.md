# M4 controlled local AI publication

Repository implementation is ready for local execution. **Live M4 is pending**:
no actual Ollama drafts, human AI reviews or AI publication receipts have been
verified. M2 source approvals and M3 approvals do not approve AI interpretations.

## Boundaries

The model runs on loopback only, without tools or database credentials in its
prompt. The generator closes its read-only database connection before inference.
Redirects and proxy inheritance are blocked; responses and selected page context
are bounded. Exact installed model tag and digest are checked before and after
generation. A model tag is not replaced with a guessed alias.

The local PDF must match the reviewed source SHA256 already loaded in Supabase.
Each quotation must be an exact 20-1000 character substring of the cited extracted
physical PDF page. Every output is initially pending. Schema/citation checking
does **not** establish that an interpretation is true: the reviewer must examine
each claim in the PDF, source scope, periods, units and definitions. Unsupported
claims, numerical calculations, recommendations and ungrounded certainty must
be rejected. A source's language about future plans is management outlook, not
an established future fact. Do not fill missing financial facts using AI.

The exact draft (including full supplied page text, PDF hash, model digest and
prompt version) is SHA256-bound to an indexed review. Changing text, quotations,
pages or model invalidates that review. Native preview/apply reconstructs this
binding. SQL independently rejects missing/pending approval, source/company
mismatch, changed rows and unmatched quotations. It validates the submitted
extraction contract, not PDF bytes or semantic entailment; the local extractor
and explicit human review provide those boundaries.

Three RLS-enabled append-only private tables retain requests, insight provenance
and durable receipts. Never expose `insights` in the Data API. Private functions
use SECURITY INVOKER; browsers have no private-schema usage or writes. Public
insights are hidden when their source becomes unverified or company inactive.
Concurrent source demotion must first demote its verified facts under M2 rules.

## Prepare on Windows

Merge this PR, apply its migration through the controlled schema workflow, and
pull main. No draft may be approved in advance. Use a trusted PDF directory and
new private output directories **outside the repository**.

```powershell
cd C:\Analyst-OS
git pull --ff-only origin main
py -m pip install -e ".[database]"
ollama list
```

If Ollama is absent, install it from https://ollama.com/download/windows. Disable cloud features in the Ollama server environment using `OLLAMA_NO_CLOUD=1`
and restart Ollama; setting it only in the Python process cannot configure an
already-running server. The generator rejects cloud tags and remote/model metadata
and requires installed GGUF weights. Select
an installed exact tag appropriate to the laptop; download with `ollama pull`
if necessary. The workflow never auto-downloads a model or exposes its server.

The following FY2026 IDs were confirmed in the live project on 2026-10-05. Each
source must still pass the original M2 approval checks at execution time.

| Company | Source document ID |
| --- | --- |
| RIL | `e8b13e22-456e-49f2-a993-fd30dbd12db4` |
| TCS | `a7a1c68d-4437-43f3-b9fe-aa3230c8fcdd` |
| HDFC Bank | `888da60b-80bc-4d72-bb4f-ceb1be0fa55c` |
| L&T | `4f5fdf77-9008-4824-a450-75a318ec02cb` |
| Tata/TMPV | `feb4252a-186d-4e08-8537-40a37aef0c66` |

All five have pinned sources; actual local PDF presence and an installed Ollama
model must be confirmed on the operator's machine. Do not substitute new CV
company reports for the original Tata/TMPV series. See the M2 entity scope.

## Generate a first RIL draft

Place the exact approved RIL PDF in `C:\AnalystOS-private\pdfs`. Set `$modelTag`
to the exact installed name from `ollama list`. Physical pages 2,3,4 of this pinned
PDF contain the company introduction and management statement; generated claims
remain pending until reviewed. Add other pages only after inspecting their scope.

```powershell
cd C:\Analyst-OS\python
$modelTag = "YOUR_EXACT_INSTALLED_MODEL_TAG"
py -m scripts.ai_insights generate `
  --ssl-root-cert C:\AnalystOS-private\ca.pem `
  --source-document-id e8b13e22-456e-49f2-a993-fd30dbd12db4 `
  --pdf-root C:\AnalystOS-private\pdfs `
  --pdf RIL-Integrated-Annual-Report-2025-26.pdf `
  --pages 2,3,4 --model $modelTag `
  --output-dir C:\AnalystOS-private\m4-ril-draft-01
```

The native PostgreSQL URL is read from `ANALYST_OS_DATABASE_URL` or requested
through hidden input. TLS verify-full and the same CA used in M2/M3 are required.
Do not share a password, privileged URL or service-role key in drafts or Git.

## Explicit review

Inspect `ai.draft.json`, the cited PDF pages and `ai.review.json`. The template has
every candidate indexed and pending. For accepted candidates only, set:

```json
{"status":"approved","reviewer":"Marky","reviewed_at":"ACTUAL_ISO8601_TIME_WITH_TIMEZONE","rationale":"Explain why these exact claims and quotations are supported."}
```

This is a syntax example, **not recorded approval**. Use an actual rationale and a timezone-aware ISO8601 timestamp of the review,
leave unresolved entries pending and mark unsupported entries rejected. Never
edit draft text and reuse an old approval. Regenerate its review template if the
draft changes. Human review should cover every assertion, not just a title.
The model's low/medium/high confidence is its self-assessment, not a statistical
score. Confidence does not remove the need to verify claims.

## Read-only preview and native apply

```powershell
py -m scripts.ai_insights preview `
  --ssl-root-cert C:\AnalystOS-private\ca.pem `
  --draft C:\AnalystOS-private\m4-ril-draft-01\ai.draft.json `
  --review C:\AnalystOS-private\m4-ril-draft-01\ai.review.json `
  --output-dir C:\AnalystOS-private\m4-ril-preview-01
```

Review `ai.plan.json` and `ai.summary.json`; it must report zero writes. Apply
requires that exact plan and both hashes from its summary:

```powershell
py -m scripts.ai_insights apply `
  --ssl-root-cert C:\AnalystOS-private\ca.pem `
  --draft C:\AnalystOS-private\m4-ril-draft-01\ai.draft.json `
  --review C:\AnalystOS-private\m4-ril-draft-01\ai.review.json `
  --plan C:\AnalystOS-private\m4-ril-preview-01\ai.plan.json `
  --expected-plan-sha256 EXACT_REVIEWED_PLAN_HASH `
  --expected-schema-sha256 EXACT_REVIEWED_SCHEMA_HASH `
  --output-dir C:\AnalystOS-private\m4-ril-apply-01
```

Apply locks source/approval/output tables with a five-second lock timeout,
rebuilds the plan, and commits approved rows, proofs and receipt atomically.
Existing rows cannot be overwritten. Identical request replay verifies the
original receipt and exact committed rows. A changed review of a previously
published draft is a conflict requiring explicit adjudication, not an update.
Plans bind exact source, review and schema state; they contain no time-varying
financial calculations and are rechecked at apply. They have no elapsed-time
expiry; source/review/schema changes reject them regardless of age.

For lost COMMIT response or local receipt save failure, use the reported import
ID before retrying. Recovery is read-only and independent of local preview files:

```powershell
py -m scripts.ai_insights receipt `
  --ssl-root-cert C:\AnalystOS-private\ca.pem `
  --receipt-import-id EXACT_IMPORT_UUID `
  --output-dir C:\AnalystOS-private\m4-recovery-01
```

Retain `ai.receipt.json` and independently check it against Supabase. Repeat the
workflow for each company with an actually reviewed source/page selection; do
not promise a fixed number of insights or all five sections when evidence is
insufficient. Verify browser read-only visibility, citation links, reviewer
label, mobile/keyboard rendering and public operation without Ollama before
closing M4's runtime gates. No fake model outputs or synthetic approvals belong
in production. All test approvals are explicitly marked TEST ONLY.
