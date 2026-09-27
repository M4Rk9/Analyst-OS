# M6 security and performance hardening

This document records concrete repository findings and the corresponding fixes. It is not a substitute for production verification against the deployed Cloudflare Pages and Supabase projects.

## Findings fixed

### 1. Cloudflare browser security headers were absent

**Risk:** the static application had no repository-defined CSP or browser hardening policy.

**Fix:** `web/_headers` now defines a restrictive Content Security Policy, frame/object/base restrictions, referrer policy, MIME sniffing protection, permissions policy, COOP, and cache behavior. Inline scripts/styles and `unsafe-eval` are not permitted.

### 2. RLS test coverage did not include the M4 AI table

**Risk:** `ai_insights` had RLS in its migration, but the automated release gate did not require it.

**Fix:** migration tests now aggregate every SQL migration and require RLS, explicit public SELECT grants, and prior privilege revocation for all exposed tables, including `ai_insights`.

### 3. Unsafe browser APIs were policy-only

**Risk:** documentation prohibited `innerHTML`, `eval`, dynamic HTML insertion, and privileged credentials in browser assets, but CI did not enforce those rules.

**Fix:** static tests now fail if browser JavaScript uses unsafe DOM/execution APIs or if privileged Supabase credential markers appear anywhere under `web/`. The browser configuration example uses generic privileged-credential wording so literal privileged-key markers remain meaningful scanner signals rather than documentation-only false positives.

### 4. Local secret/config files were not a tested release gate

**Risk:** `.gitignore` was correct, but accidental tracking of `.env` or `web/js/config.js` would not automatically fail CI.

**Fix:** CI tests use `git ls-files` to verify local secret/config files are not tracked.

### 5. Browser reads had no central row bound or timeout

**Risk:** a malformed or unexpectedly large public dataset could cause excessive transfer/render work or leave a request hanging.

**Fix:** the read-only Supabase client now applies a default 500-row cap when a query does not specify a lower limit and aborts requests after 10 seconds.

### 6. CI actions used older floating major tags

**Risk:** floating tags weaken build reproducibility and the previous action versions emitted runtime deprecation warnings.

**Fix:** first-party GitHub Actions were upgraded to the current verified releases at the time of M6 and pinned to their exact 40-character commit SHAs. A static test now enforces SHA pinning for `actions/*` uses.

## Existing controls re-verified in repository

- Public browser access is SELECT-only by migration policy.
- Service-role credentials are not permitted in frontend assets.
- Source links are accepted only when they resolve to `https:`.
- AI text is rendered as plain text, not executable HTML.
- Ollama is restricted to localhost by the Python client.
- PDF ingestion is bounded by trusted-root path, extension/signature, size, and page limits.
- AI output requires a strict schema and approved source/page provenance.
- Python dependencies are audited in CI.
- Browser JavaScript receives syntax validation in CI.
- Responsive layout, reduced-motion handling, visible focus states, semantic landmarks, skip navigation, and chart ARIA labels are present.

## Production checks still required in M7

Repository checks cannot prove the state of external services. Before release, verify against the actual deployed projects:

1. Apply migrations to the production Supabase project.
2. Using only the browser anon key, confirm allowed SELECTs succeed and INSERT/UPDATE/DELETE fail on every exposed table.
3. Confirm the service-role key exists only in a controlled local ingestion environment.
4. Confirm Cloudflare serves the expected CSP/security headers.
5. Confirm `web/js/config.js` contains only the public project URL and browser-safe anon key.
6. Exercise keyboard navigation, responsive layouts, and primary flows in a real browser.
7. Re-run CI and dependency audit at the release commit.

Until those checks and the verified M2 data population are complete, the project must not be described as production-ready.
