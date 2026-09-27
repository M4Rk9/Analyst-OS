# Security Engineering

## Secrets

Real secrets stay only in local or platform-managed environment variables. `.env` and `web/js/config.js` are ignored. The browser may use only a public Supabase project URL and browser-safe anon key. Service-role keys are local/server-side only.

## Supabase

Every exposed table must enable Row Level Security. Public policies are explicit SELECT-only policies for rows intended for public display. Do not create browser INSERT/UPDATE/DELETE policies. Privileged writes originate from controlled ingestion/analytics workflows.

## Browser

- Prefer `textContent`, `createElement`, and explicit attribute assignment.
- Do not render AI output with `innerHTML`.
- Do not use `eval`, `Function`, dynamic script execution, or unvalidated event-handler strings.
- External links must resolve to `https:` before being attached to the DOM.
- Add `rel="noopener noreferrer"` to external new-tab links.
- Keep third-party browser scripts to a minimum.

## AI

Ollama binds to local-only networking for this project. AI receives curated factual context and deterministic metrics, not secrets. Model output is untrusted, schema-validated, length-bounded, and cannot execute code, shell commands, SQL, HTML, configuration changes, or direct database writes.

### Prompt injection rule

Instructions discovered inside company documents are data, not instructions. The application prompt must explicitly state that retrieved text cannot override system/application rules. AI insights are rejected when evidence/provenance requirements are not met.

## Document ingestion

Before parsing, validate:

- allowed source scheme (`https:` for remote sources)
- file size against configured maximum
- expected MIME type
- safe generated/local filename (do not trust remote filename)
- parser errors/timeouts where feasible
- page/text limits where feasible

Do not allow arbitrary user-supplied filesystem paths. Do not execute embedded document content.

## Database integrity

Use foreign keys, uniqueness constraints, CHECK constraints, NOT NULL where semantically valid, timestamps, and provenance. Financial records preserve raw/normalized/calculated separation, period, currency, scale/units, source, and fiscal context. Historical records are versioned or conflict-recorded rather than silently overwritten.

## Dependencies and CI

Keep dependencies small and version-bounded. CI runs linting, tests, and dependency vulnerability auditing. Critical dependency vulnerabilities block release until fixed or explicitly removed from the dependency graph.

## Security review checklist

- [ ] No committed secrets
- [ ] No service-role key in frontend
- [ ] RLS enabled on all exposed tables
- [ ] Public access is SELECT-only
- [ ] No public Ollama endpoint
- [ ] No unsafe AI HTML
- [ ] No `eval`/dynamic code execution
- [ ] Source URLs validated
- [ ] Document size/MIME/path validation active
- [ ] AI output schema validation active
- [ ] No critical known dependency vulnerability
- [ ] CI does not print secrets
- [ ] Access policy documented
