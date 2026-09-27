# Security Policy

Security is a first-class release requirement for Analyst OS.

## Reporting a vulnerability

Please do not disclose exploitable vulnerabilities in a public issue. Contact the repository owner privately through an appropriate GitHub channel and include reproduction steps, affected paths, impact, and a proposed mitigation when possible.

## Non-negotiable controls

- Never commit passwords, tokens, API credentials, private keys, `.env` files, or Supabase service-role keys.
- Never place privileged credentials in frontend JavaScript.
- Enable RLS on every exposed Supabase table.
- Browser access is read-only and limited to explicitly public-display data.
- Privileged database writes are performed only by controlled local/server-side Python workflows.
- Ollama remains local and is never exposed directly to the public internet.
- AI output and extracted document text are untrusted input.
- Do not render AI output as HTML or execute AI-generated code.
- Reject unsafe/oversized document inputs and unsafe URL protocols.

## Release blockers

A release is blocked by any exposed/committed secret, missing RLS on exposed data, browser write permission, public Ollama endpoint, unsafe AI-generated HTML, critical known dependency vulnerability, unvalidated document ingestion, major XSS risk, secret leakage in CI logs, privileged frontend credentials, or undocumented access policy.

Detailed engineering controls are maintained in [`docs/SECURITY.md`](docs/SECURITY.md).
