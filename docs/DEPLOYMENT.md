# Deployment runbook

Analyst OS V1 is designed for a zero-cost portfolio deployment using Supabase free tier and Cloudflare Pages. Production deployment is a controlled release step; do not expose privileged credentials or bypass the runtime RLS checks below.

## 1. Supabase project

Create a Supabase project and apply the SQL migrations in numerical order from `supabase/migrations/`.

After migration, verify that the initial five-company seed is present and that every exposed table has Row Level Security enabled.

### Credentials

Two credential classes have different trust levels:

- **Browser:** project URL + browser-safe anon key only
- **Privileged local pipeline:** service-role credential kept in local environment variables only

Never put a privileged credential in `web/`, Cloudflare Pages source files, Git history, screenshots, issue comments, or CI logs.

## 2. Runtime RLS verification

Before deployment, test with the browser anon key—not with an admin client.

For every exposed table:

- SELECT intended public data: must succeed
- INSERT: must fail
- UPDATE: must fail
- DELETE: must fail

Also verify that AI insights exposed publicly are validated and backed by permitted source documents according to the final migration policies.

## 3. Browser configuration

Copy:

```text
web/js/config.example.js -> web/js/config.js
```

Set only:

```js
window.ANALYST_OS_CONFIG = Object.freeze({
  supabaseUrl: "https://YOUR_PROJECT.supabase.co",
  supabaseAnonKey: "YOUR_BROWSER_SAFE_ANON_KEY",
});
```

`web/js/config.js` is intentionally ignored by Git. If the deployment platform needs a generated config file, generate it during deployment from values that are explicitly safe for browser exposure. Never reuse the privileged local ingestion credential.

## 4. Cloudflare Pages

Create a Pages project connected to this GitHub repository.

Recommended configuration:

- Production branch: `main`
- Framework preset: none/static
- Build command: none required
- Build output directory: `web`

The `web/_headers` file carries the repository-defined browser security policy and cache behavior. After deployment, inspect real HTTP responses and confirm those headers are present.

## 5. Deployment smoke test

Check in a real browser:

1. home page loads without console errors
2. five-company search works
3. selecting a populated company opens the analytical workspace
4. verified financial trends/metrics render when data exists
5. missing datasets show explicit empty states rather than invented values
6. AI insights render as text and preserve evidence links
7. all external source links use HTTPS
8. keyboard navigation and visible focus states work
9. mobile layout remains usable
10. browser network requests are GET-only against the public Supabase API

## 6. Security header verification

Confirm the deployed site returns the intended controls from `web/_headers`, including:

- Content-Security-Policy
- Referrer-Policy
- X-Content-Type-Options
- frame/object/base restrictions in CSP
- Permissions-Policy

Do not call the release production-ready if Cloudflare is not serving the expected policy.

## 7. Final code gate

At the exact release commit, GitHub Actions must pass:

```text
Ruff
pytest
browser JavaScript syntax checks
pip-audit
```

Do not release from a commit whose quality/security gate is red.

## 8. Data release gate

M2 remains a blocker until the initial company universe has reviewed primary-source financial history loaded with provenance. Do not populate production tables with fabricated demo numbers merely to make the UI look complete.

## 9. Ollama deployment rule

There is no public Ollama deployment for V1. Ollama remains local/offline and produces validated data before that data is written to Supabase. The public site must remain functional when Ollama is not running.
