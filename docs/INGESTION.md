# Financial Data Ingestion

## Principle

Production financial facts are accepted only when they carry primary-source provenance and pass deterministic validation. Analyst OS does not scrape arbitrary third-party finance sites or invent missing values.

## Current M2 pipeline

The local ingestion package provides:

- Pydantic validation for company, fiscal-period, currency, metric, source, page, and value fields
- HTTPS-only source URLs
- controlled-root CSV loading with path-traversal protection
- CSV size limits
- strict required-column checks
- deterministic scale normalization (`normalized_value = raw_value × unit_scale`)
- negative-value preservation where financially valid
- duplicate/conflict detection across competing source observations
- fail-closed behavior when sources disagree
- a validation-only CLI that performs no database writes

## CSV contract

Required columns:

`company_slug`, `period_type`, `fiscal_year`, `period_start`, `period_end`, `currency`, `metric_code`, `raw_value`, `unit_scale`, `source_title`, `source_document_type`, `source_url`, `source_publisher`.

Optional columns include raw display text, source publication/fiscal metadata, SHA-256, source page, and source label.

All remote source URLs must use HTTPS. The ingestion process should point to official company/IR/exchange material documented in `docs/DATA_SOURCES.md`.

## Validation-only usage

```bash
python python/scripts/validate_financial_csv.py facts.csv --root /trusted/local/ingestion
```

The script reports counts only and does not publish data.

## Production population status

The pipeline code is implemented and testable, but the repository intentionally does not contain fabricated five-year financial history. M2 remains **in progress** until real primary filings are selected, normalized, reviewed, and loaded for the initial company universe. Conflicting observations must be recorded/resolved explicitly rather than silently selected.

## First reviewed RIL/TCS evidence batch

See [data/m2/ril-tcs/batch1](../data/m2/ril-tcs/batch1/README.md) for five-year report provenance, 120 consolidated P&L observations, four preserved RIL re-presentation conflicts, and 56 unique validation-only candidate facts. Nine uploads matched official bytes; the TCS FY2025–26 official copy was independently reacquired when the uploaded hash differed. All records remain staging evidence. The CSV does not carry quality-state or reporting-basis approval; a privileged publisher must preserve the companion metadata and approve each observation explicitly. This batch does not complete M2 or issue #14.

## RIL/TCS balance-sheet and cash-flow evidence

[Batch2](../data/m2/ril-tcs/batch2/README.md) retains 644 source observations and 320 validation-only candidates, with 138 exact accounting checks and two unresolved RIL FY2024 cash-flow conflicts. Together with batch1 there are 376 candidates and six unresolved conflict keys. Run `PYTHONPATH=python python python/scripts/validate_m2_batch2.py data/m2/ril-tcs/batch2` to recheck the evidence and receipt. Preserve the JSON companion metadata: instant balance-sheet semantics, source-column selection, quality/preference flags and metric definitions are not enforced or preserved by the CSV loader. Follow [M2_NEXT_STEPS.md](M2_NEXT_STEPS.md) before implementing any database writes.
