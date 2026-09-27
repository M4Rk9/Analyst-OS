# Analyst OS — Project Specification

## Objective

Build a finished, security-first portfolio project that makes fundamental analysis of a small supported company universe easier while demonstrating frontend engineering, Python/Pandas/NumPy, SQL/PostgreSQL/Supabase, deterministic financial analytics, local Ollama integration, document processing, provenance, testing, Git/GitHub, and deployment.

## Priorities

1. Accuracy
2. Security
3. Simplicity
4. Smooth performance
5. Minimalist professional UI
6. Explainable calculations
7. Source-backed AI insights

## Fixed stack

- Frontend: HTML, CSS, vanilla JavaScript
- Hosting: Cloudflare Pages
- Database: Supabase PostgreSQL
- Analytics: Python, Pandas, NumPy
- AI: local Ollama
- Documents: Python + PyMuPDF when needed
- Version control/CI: GitHub + GitHub Actions

Avoid React/Next.js/TypeScript, Redis, Kubernetes, paid LLM or financial APIs, vector databases, microservices, complex queues, and unnecessary cloud services.

## V1 features

- Company overview
- Historical financial trends
- Core deterministic ratios
- Deterministic red-flag signals requiring further investigation
- Concise source-backed AI insights
- Small peer snapshot
- Primary-source references

## Explicit non-goals

No live trading, real-time prices, recommendations, buy/sell signals, target prices, portfolio management, payments, subscriptions, social features, mobile app, complex authentication, DCF, Monte Carlo, options analytics, automatic pitch books, large screeners, proprietary datasets, social sentiment, or complex ML models.

## Initial company coverage

Approximately five companies only until the end-to-end system is verified: Reliance Industries, TCS, HDFC Bank, Tata Motors, and Larsen & Toubro.

## Core calculation rule

**Python calculates. AI interprets.**

The LLM must not invent missing data or act as the authority for numerical financial calculations. Unverified information is represented as unavailable/insufficient evidence.

## Data quality

Preserve reporting period, fiscal year/quarter, currency, units, source provenance, raw value, normalized value, calculated metrics, and AI interpretations as distinct concepts. Never silently overwrite history or hide source conflicts.

## Regulatory positioning

Analyst OS is an analysis/research tool, not an investment adviser. Outputs remain neutral and never rank companies as investments.
