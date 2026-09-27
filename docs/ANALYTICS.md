# Financial analytics

Analyst OS follows one strict rule: **Python calculates; AI interprets.**

The analytics package is deterministic, side-effect free, and deliberately conservative about missing data. Missing inputs and zero denominators return `None`; they are never replaced with guessed values.

## Implemented formulas

- Period-on-period growth
- CAGR
- Profit/revenue margins
- ROE
- ROA
- ROCE
- Debt/equity
- Current ratio
- Interest coverage
- Free cash flow
- CFO/PAT
- Working capital

Percentages are represented as percentage points. Ratio outputs such as debt/equity remain plain ratios.

## Data-definition discipline

A formula is only meaningful when upstream facts use compatible definitions, reporting periods, currency, and units. The analytics package therefore performs arithmetic only; responsibility for verified provenance and normalized source facts remains in the ingestion layer.

## Edge-case behavior

- Missing numerator or denominator -> `None`
- Zero denominator -> `None`
- NaN/Infinity -> rejected
- Negative values -> preserved where mathematically valid
- CAGR -> suppressed for non-positive beginning values, negative ending values, or non-positive periods

## Red flags

Current deterministic investigation signals are:

1. Receivables growing materially faster than revenue
2. Inventory growing materially faster than revenue
3. CFO materially below PAT
4. Debt rising rapidly
5. Interest coverage deteriorating materially
6. Sustained margin deterioration

These are **signals requiring further investigation**, not BUY/SELL outputs and not investment recommendations. Missing evidence suppresses the signal.

Thresholds are explicit function parameters and should be versioned whenever production rules change.

## Tests

`python/tests/test_analytics.py` covers formulas, missing data, divide-by-zero behavior, negative values, non-finite inputs, and red-flag trigger/non-trigger paths.
