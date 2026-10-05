# Roadmap

**M2 verified complete (2026-10-04):** [five-company load evidence](M2_FIVE_COMPANY_LOAD_STATUS.md) records 629 approved facts and post-load formula checks. Historical preparation queues are superseded; runtime derived outputs and deployment remain release gates.

Exactly eight milestones are used unless a compelling technical reason requires otherwise.

## M0 — Foundation — Completed

- Repository structure and technical documentation
- README and security policy
- Frontend shell and Python package skeletons
- Pytest and CI foundation

**Verified:** repository installs and the milestone quality gate passed.

## M1 — Data Foundation — Completed in repository

- Supabase schema and migrations
- RLS on every exposed table
- Explicit read-only public access policies
- Company, reporting-period, financial-data, calculated-metric, red-flag, and source-document models
- Provenance/integrity constraints and five-company seed set
- Static migration-policy tests

**Runtime note:** the target Supabase project must still receive the migrations and pass anon-key runtime verification before M7 can be released.

## M2 — Financial Data Pipeline — Completed for selected primary-source history

Implemented and verified in repository:

- Controlled-root CSV ingestion
- Pydantic normalization/validation
- HTTPS source validation
- size/path protections
- deterministic unit normalization
- duplicate/conflict detection with fail-closed behavior
- ingestion tests and validation-only CLI

Verified on the live target: selected five-company primary filings, exact approved observations and definitions, controlled native loads, every fact/source/approval fingerprint, explicit withheld conflicts and unavailable dashes. See [the verification record](M2_FIVE_COMPANY_LOAD_STATUS.md) and its post-load deterministic checks. Selected core coverage does not imply full note transcription, resolved disagreements or comparable-growth inputs.

## M3 — Financial Analytics — Selected reported policy published and verified

- Growth and CAGR
- Margins and ROE/ROA/ROCE
- Leverage/liquidity/interest coverage
- Cash-flow metrics and working capital
- Receivables, inventory and payables days; cash conversion cycle
- Deterministic investigation-signal rules
- Versioned formula/rule constants
- Unit tests for missing, zero, negative and non-finite inputs

**Verified:** merged CI passed the repository quality/security gate.

M3 production publication is independently verified: [43 metrics / one signal / 32 unavailable](M3_PUBLICATION_VERIFICATION.md). Wider formulas remain unavailable where definitions or inputs do not support them.

## M4 — AI Insight Pipeline — First RIL publication verified; runtime partially complete

- Trusted-root PDF validation and bounded PyMuPDF extraction
- Page-aware document chunking
- Loopback-only local Ollama client
- Prompt templates that treat document text as untrusted evidence
- Strict Pydantic insight/evidence schemas
- Company, model, source-URL and cited-page validation
- Full evidence provenance retained in `ai_insights`
- RLS limiting public visibility to validated insights backed by permitted source documents
- Tests for path traversal, invalid files, loopback enforcement, prompt/evidence boundaries and provenance

The [controlled M4 workflow](M4_CONTROLLED_PUBLICATION.md) adds exact quotation checks, model digest capture, explicit per-insight review, private provenance, native dry-run/apply, atomic receipts and recovery. Structural validation is not semantic truth verification. [The first RIL publication is independently verified](M4_PUBLICATION_VERIFICATION.md): genuine local generation, reviewer-corrected citations, explicit approval, atomic publication, durable receipt and anon-role visibility. Other-company coverage, HTTP Data API and browser evidence rendering remain runtime gates.

## M5 — Interactive Frontend — Completed in repository

- Searchable five-company selector
- Verified company overview
- Read-only Supabase workspace loading
- Financial trend table with dependency-free SVG trend charts
- Deterministic metric presentation
- Investigation-signal presentation
- Validated AI insight sections using the final evidence JSONB provenance schema
- Same-sector peer snapshot when a verified peer exists in V1 coverage
- Verified primary-source list
- Safe DOM rendering with `textContent`/`createElement`
- Browser JavaScript syntax checking in CI

**Verified:** merged CI passed Ruff, pytest, browser JavaScript syntax checks and dependency audit.

## M6 — Security & Performance Hardening — Completed in repository

- Strict Cloudflare Pages CSP/security headers
- RLS/read-only regression tests covering every exposed table including `ai_insights`
- Static checks for unsafe browser DOM/dynamic execution patterns
- Tracked local-secret/config regression checks
- Browser privileged-key marker scanning
- Frontend alignment with hardened AI evidence provenance
- HTTPS-only source-link validation
- Node-24-compatible first-party GitHub Actions
- Dependency-free public frontend preserved

**Important finding fixed:** M5 originally expected single-page AI provenance fields while hardened M4 stores the complete evidence array as JSONB. M6 aligned the browser with the final schema so valid insights do not fail closed after deployment.

**Verified:** merged PR #12 passed Ruff, pytest, browser JavaScript syntax checks and pip-audit before merge.

## M7 — Portfolio Release — In progress / externally gated

Repository-side release preparation now includes:

- architecture documentation and Mermaid diagram
- portfolio demo walkthrough
- zero-cost Supabase + Cloudflare Pages deployment runbook
- evidence-based release checklist
- corrected README/roadmap status

Still blocking a real release:

- M3/M4 validated derived-output publication and frontend binding
- target Supabase project configuration and runtime RLS verification
- Cloudflare Pages production deployment
- real-browser functional/security/accessibility checks
- screenshots from the verified deployed application
- final release-commit CI

See `docs/RELEASE_CHECKLIST.md` and `docs/DEPLOYMENT.md`.

## Status discipline

Each milestone must: inspect current state, state goal, implement, test, security-review, fix findings, update documentation, summarize changes, and record remaining work. A milestone is never called production-ready without verification evidence.
