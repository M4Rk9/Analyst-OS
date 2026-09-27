# Contributing

Analyst OS uses milestone-focused development.

## Workflow

1. Branch from `main` using `feat/`, `fix/`, `docs/`, or `chore/` prefixes.
2. Keep changes scoped to one coherent milestone or fix.
3. Add or update tests for behavior changes.
4. Run `ruff check python` and `pytest` locally.
5. Never commit secrets, local `.env` files, downloaded filings, or generated private artifacts.
6. Open a pull request with scope, validation evidence, security impact, and remaining work.
7. Merge only after required CI checks pass.

## Engineering principles

- Accuracy over feature count.
- Python performs authoritative financial calculations; AI explains verified results.
- No evidence means no confident claim.
- Prefer primary company filings and preserve provenance.
- Use least privilege and safe DOM APIs.
- Keep dependencies minimal.
- Avoid expanding V1 beyond the documented roadmap.
