# Analyst OS

Analyst OS is a minimalist, source-backed, AI-assisted company-analysis workspace built as a flagship portfolio project. It demonstrates financial analytics, Python data engineering, PostgreSQL/Supabase, local AI with Ollama, secure frontend engineering, testing, and deployment discipline.

> **Positioning:** research and analysis tool only. Analyst OS does not provide investment advice, BUY/SELL signals, target prices, or guaranteed returns.

## V1 scope

- Company overview
- Historical financial trends
- Deterministic financial ratios
- Deterministic red-flag signals
- Source-backed AI insights
- Small peer snapshot
- Primary-source references

The initial target universe is approximately five listed Indian companies: Reliance Industries, TCS, HDFC Bank, Tata Motors, and Larsen & Toubro. Coverage expands only after the end-to-end system is validated.

## Architecture principle

**Python calculates. AI interprets.**

The public app is static HTML/CSS/JavaScript on Cloudflare Pages. It reads prepared, public-display data from Supabase using browser-safe credentials and read-only RLS policies. Privileged ingestion, analytics, document parsing, and Ollama execution happen offline/local and write validated outputs to Supabase with server-side credentials.

```text
Public user -> Cloudflare Pages -> HTML/CSS/JS -> Supabase read-only API -> PostgreSQL

Official filings -> Python ingestion -> validation -> normalized data
                -> deterministic analytics/red flags
                -> document extraction -> local Ollama -> validated insights
                -> Supabase
```

Ollama is never required by the public application and must never be exposed to the public internet.

## Zero-cost V1

Development and initial portfolio deployment are designed for ₹0 using Cloudflare Pages free tier, Supabase free tier, GitHub/GitHub Actions, local Ollama, open-source Python libraries, and public company disclosures. No paid VPS, domain, financial API, LLM API, or data subscription is required.

## Repository layout

```text
web/                       Static frontend
python/                    Ingestion, analytics, AI, scripts, tests
supabase/migrations/       Database schema and RLS migrations
docs/                      Architecture, roadmap, security, sources
.github/workflows/         CI
```

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

## Milestone status

| Milestone | Status |
|---|---|
| M0 — Foundation | Completed on foundation branch |
| M1 — Data Foundation | Upcoming |
| M2 — Financial Data Pipeline | Upcoming |
| M3 — Financial Analytics | Upcoming |
| M4 — AI Insight Pipeline | Upcoming |
| M5 — Interactive Frontend | Upcoming |
| M6 — Security & Performance Hardening | Upcoming |
| M7 — Portfolio Release | Upcoming |

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for acceptance criteria.

## Security

Security is a release gate. Exposed secrets, missing RLS, browser write access, public Ollama endpoints, unsafe AI HTML, unvalidated documents, major XSS risks, critical vulnerable dependencies, or undocumented access policies block release. See [`SECURITY.md`](SECURITY.md) and [`docs/SECURITY.md`](docs/SECURITY.md).

## License

No license has been selected yet. Until one is added, all rights are reserved by the repository owner.
