# Architecture

## Public path

```text
Browser
  -> Cloudflare Pages
  -> static HTML/CSS/JavaScript
  -> Supabase REST API using browser-safe anon credentials
  -> PostgreSQL tables/views protected by RLS
```

The browser has no production INSERT/UPDATE/DELETE capability.

## Offline analytical path

```text
Official company / exchange disclosure
  -> bounded document download or controlled local input
  -> MIME/size/filename validation
  -> text/table extraction
  -> normalized financial records + provenance
  -> deterministic Python analytics
  -> deterministic red-flag rules
  -> local Ollama interpretation of verified context
  -> schema validation + provenance validation
  -> privileged local write to Supabase
```

## Trust boundaries

### Untrusted
- Browser input
- External URLs
- Public company documents
- Extracted document text
- AI model output

### Trusted only after validation
- Normalized financial records
- Deterministic calculated metrics
- AI insights matching the application schema and evidence policy

### Privileged
- Supabase service-role credentials
- Database write operations
- Local ingestion configuration

Privileged data never crosses into static frontend files.

## Availability model

The public application serves precomputed analytical data. Ollama is offline/local and is not part of request-time serving. This keeps the deployed app cheap, fast, and independent of a continuously running AI server.

## Design constraints

- Static-first frontend
- Minimal dependencies
- No microservices
- No paid infrastructure required for V1
- Precompute heavy work
- Cache prepared analytical results where appropriate
- Add indexes only for measured/obvious query patterns
