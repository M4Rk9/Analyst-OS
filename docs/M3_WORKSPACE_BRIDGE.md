# Loaded history workspace and analytics preview

M2 is closed after the verified 629-fact controlled load. This bridge prepares the next runtime stage without publishing derived database rows or changing approved financial facts.

## Frontend bindings

The financial-history table recognizes the actual approved codes, including `profit_for_year`, `bank_total_income`, `bank_owner_profit`, `lt_reported_revenue`, `tata_reported_revenue`, `cash_from_operations` and `cfo`. Bank total income remains bank total income; reported group profit is not relabelled owner PAT or recurring profit. Same-period bank or industrial facts are not used as interchangeable proxies.

Displayed financial values are normalized INR. Latest displayed rows identify their reporting period and link to the selected official document with a PDF page reference. The fact query explicitly requires verified preferred observations. Null, blank, dash, nonnumeric and nonfinite values remain unavailable; explicit numeric zero remains zero.

Charts preserve missing fiscal years as gaps and separate Tata FY2026 from the earlier original-entity series. The page explains the approved TMPV continuity mapping, separate CV company and withheld FY2024 core facts. Lines show reported history and make no comparable-growth claim. Calculated ratio cards show only the company's latest loaded reporting period; old results and ambiguous formula-version choices are suppressed.

These changes do not establish HTTP API access, live browser correctness or deployment. Those checks still require the real configured application.

## Read-only native preview

After merge, in `C:\Analyst-OS`, update to `main` and use the same installed Python environment and CA file that completed M2:

```powershell
git pull --ff-only
$env:PYTHONPATH = "python"
py -m scripts.preview_loaded_analytics `
    --ssl-root-cert "C:\AnalystOS-private\ca.pem" `
    --output-dir "data/processed/m3-preview-01"
```

At the hidden prompt, paste the complete PostgreSQL URL that worked for M2. Use a new output directory for every attempt. The script also supports `ANALYST_OS_DATABASE_URL` when it is already set correctly. No URL or password is written to the output artifacts.

The native client uses verified TLS and a privileged read-only connection. The exporter reads the complete five-company scope in a repeatable-read transaction, validates stored catalogs and evidence against actual facts, then rolls back. The current publisher schema inventory is checked read-only. All approved observations must already exist unchanged; missing facts, conflicts, stale/wrong-project snapshots and changed definitions block calculation. No `--apply` option or derived SQL writer exists in this command.

The private output directory contains:

- `analytics.target-snapshot.json`: fresh complete native evidence snapshot.
- `analytics.schema-inventory.json`: independently inspected schema inventory.
- `analytics.preview.json`: versioned formula/policy, catalog/review/snapshot bindings, input fact UUIDs, observation IDs, evidence/definition fingerprints and exact Decimal values.
- `analytics.summary.json`: mode, zero production writes, counts and preview/schema hashes.

Share only the preview and summary for the next review. Keep the full target snapshot and schema inventory in the operator's private audit directory.

## Calculation boundary

Policy `reported-core-1` runs existing formula version 1.0 for current ratio, reported working capital, and CFO divided by positive reported consolidated group profit. It uses exactly matched same-period approved inputs. The independently verified M2 baseline yields 75 company/year/metric rows: 43 available and 32 unavailable. The native preview must confirm the current live baseline; tests and the historical report do not substitute for it.

The group-profit denominator includes each report's consolidated operation scope and non-controlling interests. It is not owner PAT, adjusted earnings or recurring cash conversion. The preview assigns a separate descriptive output code, `cfo_to_reported_group_profit`; it does not add financial aliases to the approval catalogs. HDFC Bank's industrial-ratio inputs remain unavailable. Missing Tata FY2024 inputs stay unavailable. No growth, CAGR, EBIT/EBITDA, comprehensive debt, conventional capex or comparable peer ratio is inferred.

## Next publication gate

Native preview verification comes before implementing controlled derived publication. That path needs explicit output definitions, reviewable schema/plan bindings, input-fact provenance, fresh-target revalidation, deterministic recomputation, atomic commit/receipt and retry behavior. No preview row should be inserted through manual SQL, browser writes or an alternate connector. `calculated_metrics`, `red_flags` and AI insights remain unchanged by this bridge.
