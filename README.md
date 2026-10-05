# Analyst OS

**M2 update (2026-10-04):** [five-company controlled loading is independently verified](docs/M2_FIVE_COMPANY_LOAD_STATUS.md): 629 approved primary-source facts, preserved approval/provenance, 46 withheld conflict keys and two unavailable printed-dash candidates. M2 selected history population is complete. M3 production publication is verified; AI publication and deployment gates remain open.

**M3 live verified:** [43 metrics and one signal were loaded through the native controlled publisher](docs/M3_PUBLICATION_VERIFICATION.md); 32 calculations remain unavailable. **Next runtime step:** [M4 controlled local AI drafting, explicit review and publication](docs/M4_CONTROLLED_PUBLICATION.md). No AI output has been approved or published yet.

Analyst OS is a minimalist, source-backed, AI-assisted company-analysis workspace built as a flagship portfolio project. It demonstrates financial analytics, Python data engineering, PostgreSQL/Supabase, local AI with Ollama, secure frontend engineering, testing, and deployment discipline.

> **Positioning:** research and analysis tool only. Analyst OS does not provide investment advice, BUY/SELL signals, target prices, company investment rankings, or guaranteed returns.

## Current status

Repository engineering is implemented through **M6 — Security & Performance Hardening**. The project is **not yet production-ready** because runtime release gates remain:

1. **M4 runtime outputs:** generate real local-model drafts, explicitly review their source-backed claims, publish through the native controlled path, and verify frontend binding. The [M2 load verification](docs/M2_FIVE_COMPANY_LOAD_STATUS.md) includes the post-load formula rerun; it does not publish derived database rows.
2. **M7 deployment verification:** complete HTTP Data API, concurrency/recovery, Cloudflare Pages, security-header, browser and accessibility checks.

No synthetic production financial values are used merely to make the UI appear complete.

## V1 scope

- Company overview
- Historical financial trends
- Deterministic financial ratios
- Deterministic red-flag investigation signals
- Source-backed AI insights
- Small peer snapshot
- Primary-source references

The initial target universe is intentionally limited to five listed Indian companies: Reliance Industries, TCS, HDFC Bank, Tata Motors, and Larsen & Toubro. Coverage expands only after the end-to-end system is verified.

## Architecture principle

**Python calculates. AI interprets.**

The public application is static HTML/CSS/Vanilla JavaScript on Cloudflare Pages. It reads prepared public-display data from Supabase using browser-safe credentials and read-only RLS policies.

Privileged ingestion, normalization, deterministic analytics, document parsing, and Ollama execution happen locally/offline. Only validated outputs are eligible for controlled writes to Supabase.

```mermaid
flowchart LR
    U[Public user] --> CF[Cloudflare Pages\nHTML · CSS · Vanilla JS]
    CF -->|HTTPS · anon key · SELECT only| API[Supabase REST API]
    API --> DB[(PostgreSQL + RLS)]

    SRC[Official filings] --> ING[Python ingestion + validation]
    ING --> CALC[Deterministic analytics + red flags]
    SRC --> DOC[Bounded document extraction]
    DOC --> AI[Local Ollama interpretation]
    CALC --> V[Schema + provenance validation]
    AI --> V
    ING --> V
    V -->|privileged local write| DB
```

Ollama is never required by the public application and must never be exposed to the public internet.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the trust boundaries and full system design.

## Security model

Security is a release gate, not an afterthought. The repository includes controls for:

- RLS on every exposed Supabase table
- SELECT-only browser access
- no privileged Supabase credentials in frontend assets
- safe DOM rendering rather than untrusted HTML injection
- HTTPS-only external source links
- strict Cloudflare Pages CSP/security headers
- bounded document parsing
- prompt-injection-aware evidence handling
- loopback-only Ollama access
- strict AI output/evidence validation
- tracked-secret/config regression tests
- dependency vulnerability auditing

Exposed secrets, missing RLS, browser write access, a public Ollama endpoint, unsafe AI HTML, unvalidated documents, major XSS risks, critical vulnerable dependencies, or undocumented access policies block release.

## Zero-cost V1

Development and the intended initial portfolio deployment are designed for **₹0** using:

- Cloudflare Pages free tier
- Supabase free tier
- GitHub and GitHub Actions
- local Ollama
- public company disclosures
- open-source Python libraries

No paid VPS, custom domain, financial API, LLM API, or data subscription is required for V1.

## Repository layout

```text
web/                       Static frontend
python/                    Ingestion, analytics, AI, scripts, tests
supabase/migrations/       Database schema and RLS migrations
docs/                      Architecture, roadmap, security, sources, release docs
.github/workflows/         CI
```

Useful documentation:

- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestone status and acceptance criteria
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design and trust boundaries
- [`docs/DATABASE.md`](docs/DATABASE.md) — database model
- [`docs/AI_PIPELINE.md`](docs/AI_PIPELINE.md) — local AI security/provenance model
- [`docs/DEMO.md`](docs/DEMO.md) — portfolio/interview walkthrough
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Supabase + Cloudflare Pages deployment runbook
- [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) — evidence-based M7 release gate
- [`SECURITY.md`](SECURITY.md) and [`docs/SECURITY.md`](docs/SECURITY.md) — security policy/design

## Local setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
```

Copy `.env.example` to `.env` only for local development. Never commit `.env` or privileged credentials.

For the frontend, copy `web/js/config.example.js` to `web/js/config.js` and supply only browser-safe Supabase values. `config.js` is intentionally ignored by Git.

## CI quality gate

Pull requests are expected to pass:

```text
Ruff
pytest
browser JavaScript syntax validation
PostgreSQL migration/provenance tests (development-only PGlite)
npm audit
pip-audit
```

A milestone is not considered verified while its required gate is failing.

## Milestone status

| Milestone | Status |
|---|---|
| M0 — Foundation | Completed |
| M1 — Data Foundation | Completed in repository |
| M2 — Financial Data Pipeline | Completed — 629 approved facts independently verified |
| M3 — Financial Analytics | Selected reported policy published and verified |
| M4 — AI Insight Pipeline | Controlled workflow implemented; local execution/review/publication pending |
| M5 — Interactive Frontend | Completed in repository |
| M6 — Security & Performance Hardening | Completed in repository |
| M7 — Portfolio Release | In progress — external deployment/runtime checks pending |

## License

No license has been selected yet. Until one is added, all rights are reserved by the repository owner.
