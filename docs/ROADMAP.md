# Roadmap

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

## M2 — Financial Data Pipeline — In progress

Implemented and verified in repository:

- Controlled-root CSV ingestion
- Pydantic normalization/validation
- HTTPS source validation
- size/path protections
- deterministic unit normalization
- duplicate/conflict detection with fail-closed behavior
- ingestion tests and validation-only CLI

Still required before M2 is complete:

- Select verified primary filings for the five-company universe
- Normalize and review approximately five years of history where available
- Resolve or explicitly record source conflicts
- Load verified records into the target Supabase project

No production financial values will be fabricated to satisfy the milestone.

## M3 — Financial Analytics — Completed in repository

- Growth and CAGR
- Margins and ROE/ROA/ROCE
- Leverage/liquidity/interest coverage
- Cash-flow metrics and working capital
- Receivables, inventory and payables days; cash conversion cycle
- Deterministic investigation-signal rules
- Versioned formula/rule constants
- Unit tests for missing, zero, negative and non-finite inputs

**Verified:** merged CI passed the repository quality/security gate.

## M4 — AI Insight Pipeline — Completed in repository

- Trusted-root PDF validation and bounded PyMuPDF extraction
- Page-aware document chunking
- Loopback-only local Ollama client
- Prompt templates that treat document text as untrusted evidence
- Strict Pydantic insight/evidence schemas
- Company, model, source-URL and cited-page validation
- Full evidence provenance retained in `ai_insights`
- RLS limiting public visibility to validated insights backed by permitted source documents
- Tests for path traversal, invalid files, loopback enforcement, prompt/evidence boundaries and provenance

**Verified:** merged M4 implementation and hardening PRs passed CI.

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

- M2 verified five-company data population
- target Supabase project configuration and runtime RLS verification
- Cloudflare Pages production deployment
- real-browser functional/security/accessibility checks
- screenshots from the verified deployed application
- final release-commit CI

See `docs/RELEASE_CHECKLIST.md` and `docs/DEPLOYMENT.md`.

## Status discipline

Each milestone must: inspect current state, state goal, implement, test, security-review, fix findings, update documentation, summarize changes, and record remaining work. A milestone is never called production-ready without verification evidence.
