# Roadmap

Exactly eight milestones are used unless a compelling technical reason requires otherwise.

## M0 — Foundation — Completed on foundation branch

- Repository structure
- Technical documentation
- README and security policy
- Frontend shell
- Python package skeletons
- Pytest foundation
- CI foundation

**Exit gate:** repository installs cleanly, smoke tests pass, CI is defined, no secrets or privileged browser credentials are committed.

## M1 — Data Foundation — Upcoming

- Supabase schema and migrations
- RLS on every exposed table
- Read-only public access policies
- Company, reporting-period, financial-data, source-document models
- Provenance and integrity constraints
- Seed approximately five companies

## M2 — Financial Data Pipeline — Upcoming

- Controlled source ingestion
- Normalization and validation
- Approximately five years of history where available
- Duplicate/conflict handling
- Tests and source provenance

## M3 — Financial Analytics — Upcoming

Deterministic Python calculations for growth, CAGR, margins, ROE/ROA/ROCE, leverage, cash-flow metrics, selected working-capital indicators, and red-flag rules. Every financial formula receives unit tests including zero, missing, and negative-value edge cases.

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
