# Roadmap

Exactly eight milestones are used unless a compelling technical reason requires otherwise.

## M0 — Foundation — Completed

- Repository structure and technical documentation
- README and security policy
- Frontend shell and Python package skeletons
- Pytest and CI foundation

**Verified:** repository installs, Ruff and pytest pass, and dependency audit passes.

## M1 — Data Foundation — Completed

- Supabase schema and migrations
- RLS on every exposed table
- Explicit read-only public access policies
- Company, reporting-period, financial-data, calculated-metric, red-flag, and source-document models
- Provenance/integrity constraints and five-company seed set
- Static migration-policy tests

**Production configuration note:** migrations still need to be applied and anon-key-tested in the target Supabase project during M7.

## M2 — Financial Data Pipeline — In progress

Implemented:

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
- Six deterministic investigation-signal rules
- Versioned formula/rule constants
- Unit tests for missing, zero, negative and non-finite inputs

**Verified:** merged CI passed Ruff, pytest and dependency audit.

## M4 — AI Insight Pipeline — Completed in repository

- Trusted-root PDF validation and bounded PyMuPDF extraction
- Page-aware document chunking
- Localhost-only Ollama client
- Prompt templates that treat document text as untrusted evidence
- Strict Pydantic insight/evidence schemas
- Company, model, source-URL and cited-page validation
- Source-backed `ai_insights` storage with RLS and public SELECT-only access
- Tests for path traversal, invalid files, localhost enforcement and citation provenance

**Verified:** merged CI passed Ruff, pytest and dependency audit.

## M5 — Interactive Frontend — Completed in repository

- Searchable five-company selector
- Verified company overview
- Read-only Supabase workspace loading
- Financial trend table with dependency-free SVG trend charts
- Deterministic metric presentation
- Investigation-signal presentation
- Validated AI insight sections with primary-source provenance links
- Same-sector peer snapshot when a verified peer exists in V1 coverage
- Verified primary-source list
- Safe DOM rendering with `textContent`/`createElement`
- Browser JavaScript syntax checking in CI

**Verified:** merged CI passed Ruff, pytest, browser JavaScript syntax checks and dependency audit.

## M6 — Security & Performance Hardening — In progress

Implemented in the feature branch:

- Cloudflare CSP and browser security headers
- Static release-gate tests for unsafe DOM/dynamic execution APIs
- Static checks preventing privileged Supabase credential markers in web assets
- Tests preventing accidental tracking of `.env` and browser runtime config
- RLS/read-only checks expanded to every exposed table, including `ai_insights`
- Central 500-row default bound and 10-second timeout for public Supabase reads
- Current first-party GitHub Actions upgraded and pinned to exact commit SHAs
- CI rule enforcing SHA pinning for first-party actions
- Hardening findings and production verification checklist documented

Remaining gate:

- Pass the complete M6 pull-request CI and fix any findings before merge

## M7 — Portfolio Release — Upcoming

- Cloudflare Pages deployment
- Production Supabase configuration
- RLS verification
- Final tests
- Screenshots and architecture diagram
- Polished README/demo instructions
- Release checklist

## Status discipline

Each milestone must: inspect current state, state goal, implement, test, security-review, fix findings, update documentation, summarize changes, and record remaining work. A milestone is never called production-ready without verification evidence.
