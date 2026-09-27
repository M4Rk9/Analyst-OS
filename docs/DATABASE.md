# Database Design

## Purpose

The Supabase/PostgreSQL layer stores source-backed company data, normalized financial observations, deterministic calculated metrics, investigation signals, and document provenance. It is designed so the public browser can read prepared data but cannot write production analytical records.

## Core tables

### `companies`
Canonical company identity and primary listing metadata. V1 contains only the initial five-company universe.

### `reporting_periods`
Fiscal period identity separate from the financial values themselves. Periods retain start/end dates, fiscal year, period type, currency, and publication date when known.

### `source_documents`
Primary-source provenance for annual reports, quarterly results, investor presentations, earnings releases, exchange disclosures, and other official IR material. URLs must use HTTPS; verification state and optional SHA-256 integrity metadata are preserved.

### `financial_facts`
Source observations with raw text/value, normalized value, scale, currency, source document/page/label, and a quality state. Multiple documents can produce competing observations; history is not silently overwritten.

### `calculated_metrics`
Python-authored deterministic metrics only. Each record carries a formula version and references to its inputs in JSON form.

### `red_flags`
Deterministic investigation signals. A red flag is not an investment conclusion and cannot encode BUY/SELL recommendations.

## Public access model

Every exposed table has Row Level Security enabled. The `anon` and `authenticated` roles are first stripped of table privileges and then receive explicit `SELECT` only. No browser INSERT/UPDATE/DELETE policy is created.

The public policies expose only active-company data and restrict source documents/financial facts to verified rows. Privileged writes are expected to use the Supabase service role from controlled local Python workflows.

## Integrity choices

- UUID primary keys avoid browser-visible sequences.
- Unique constraints prevent duplicate fiscal periods and duplicate observations from the same source.
- CHECK constraints validate enum-like fields, date ordering, currency shape, safe HTTPS URLs, positive page numbers/scales, and JSON structure.
- Indexes support the expected company/period/metric access patterns.
- Source provenance and deterministic calculation outputs remain separate.

## Applying migrations

Apply `supabase/migrations/` in lexical order using the Supabase SQL editor or CLI in a trusted environment. Review the generated project roles before production use and verify RLS behavior with an anon key before calling M1 production-configured.
