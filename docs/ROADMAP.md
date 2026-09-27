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

**Verification gate:** CI must pass Ruff, pytest and dependency audit before this milestone is merged.

## M4 — AI Insight Pipeline — Upcoming

- Safe document extraction and chunking
- Local Ollama client
- Prompt templates
- Source references
- Output schema validation
- Prompt-injection resistance

## M5 — Interactive Frontend — Upcoming

- Company search/selector
- Company overview
- Financial trends
- Ratio presentation
- Red flags
- AI insight sections
- Peer snapshot
- Sources

## M6 — Security & Performance Hardening — Upcoming

Audit and fix RLS, secrets, dependencies, XSS, input/output validation, source URLs, database permissions, performance, responsiveness, and accessibility. Security findings are fixed rather than merely documented.

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
