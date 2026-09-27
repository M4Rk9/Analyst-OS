# Portfolio demo guide

This walkthrough is designed for a recruiter, interviewer, engineer, or finance professional reviewing Analyst OS. It demonstrates the architecture and engineering decisions without pretending the project has more production coverage than it actually does.

## What to demonstrate

### 1. Start with the problem

Analyst OS reduces the friction of reviewing a listed company by combining verified financial history, deterministic ratios, investigation signals, source-backed document insights, and source provenance in one compact workspace.

The project is intentionally not a stock recommender, trading platform, or institutional research terminal.

### 2. Show the public workspace

Open the five-company selector and demonstrate:

- company search
- company overview
- historical financial trend presentation
- deterministic calculated metrics
- investigation signals
- source-backed AI insights
- primary-source links
- peer snapshot where a verified comparable exists in the limited V1 universe

If a dataset has not yet been populated, point out the explicit empty state rather than using synthetic production values.

### 3. Explain the calculation boundary

Show `python/analyst_os_analytics/` and explain the core principle:

> Python calculates. AI interprets.

Financial formulas and red-flag rules are deterministic and tested. The LLM is not trusted to create authoritative financial values.

### 4. Explain the AI trust boundary

Show `python/analyst_os_ai/` and explain:

- PDFs are validated before extraction
- evidence keeps page-level provenance
- document text is untrusted data, not instructions
- Ollama is restricted to local loopback access
- the model has no shell, tools, public serving role, or database credentials
- model JSON is schema-validated
- cited URLs/pages must belong to supplied evidence
- validated insights are stored for later read-only display

### 5. Explain database security

Show the Supabase migrations and tests:

- RLS is enabled on every exposed table
- browser roles are explicitly revoked first
- public roles receive SELECT only
- browser write policies are rejected by tests
- privileged writes are local/offline only
- provenance and financial-period metadata are preserved

### 6. Explain frontend security

Show the static frontend and CI release gates:

- no React/Next.js or browser framework
- safe DOM APIs rather than HTML injection
- HTTPS validation for external links
- CSP and security headers on Cloudflare Pages
- no privileged database credentials in web assets
- browser JavaScript syntax is checked in CI

### 7. Show CI

The primary quality gate runs:

1. Ruff
2. pytest
3. browser JavaScript syntax validation
4. dependency vulnerability audit

A milestone is not considered verified when this gate is failing.

## Suggested interview narrative

Analyst OS is strongest as an example of combining finance with software engineering discipline. The interesting part is not merely generating an AI summary; it is designing a trustworthy data path around the model: provenance, deterministic calculations, strict schemas, RLS, safe browser rendering, testable security requirements, and a deliberately limited product scope.

## Current limitation to disclose

Repository-side engineering for M0, M1, M3, M4, M5, and M6 is implemented. M2 is not complete until approximately five years of verified primary-source history is reviewed and loaded for the initial company universe. M7 is not complete until the real Supabase and Cloudflare deployments pass the runtime release checks.
