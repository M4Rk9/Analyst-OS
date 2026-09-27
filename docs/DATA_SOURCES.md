# Data Sources and Provenance

## Source priority

1. Official company annual reports
2. Official quarterly/financial results
3. Official investor presentations and earnings releases
4. Official company investor-relations pages
5. Exchange disclosures when legally and technically appropriate

Third-party aggregators are not authoritative inputs for V1 financial records.

## Required provenance

Where applicable retain:

- company
- document title
- document type
- fiscal year/quarter
- reporting period
- source URL
- source publisher
- publication date
- page number
- section/label
- retrieval timestamp
- source hash or other stable integrity marker when practical

## Conflict policy

If sources disagree, do not silently choose one. Record the conflict, prefer the primary company filing as the authoritative baseline when justified, and document normalization choices. Unresolved uncertainty is displayed as unavailable/insufficient evidence rather than fabricated certainty.

## Initial universe

V1 targets approximately five companies with accessible primary filings: Reliance Industries, TCS, HDFC Bank, Tata Motors, and Larsen & Toubro. This list is intentionally small until ingestion, analytics, AI provenance, frontend, and security work end-to-end.
