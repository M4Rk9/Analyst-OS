# Financial Analytics

Analyst OS follows one strict rule: **Python calculates; AI interprets.**

The analytics package is deterministic, side-effect free, versioned, and conservative about missing or financially non-meaningful inputs. It never fills missing numbers with guesses.

## Formula set

- Period-on-period growth
- CAGR
- Profit/revenue margins
- ROE, ROA, ROCE
- Debt/equity
- Current ratio
- Interest coverage
- Free cash flow
- CFO/PAT
- Working capital
- Receivables days
- Inventory days
- Payables days
- Cash conversion cycle

Percentages are represented as percentage points. Ratio outputs such as debt/equity remain plain ratios. Working-capital days use 365 days for the V1 annual convention.

## Edge-case policy

- Missing value -> `None`
- Zero denominator -> `None`
- NaN/Infinity -> rejected
- Negative current profit/margin -> preserved where meaningful
- Growth from a zero or negative comparison base -> `None` because the percentage is not economically interpretable
- ROE/ROA/ROCE, debt/equity, current ratio, interest coverage and CFO/PAT -> suppressed when their required denominator is non-positive
- CAGR -> suppressed for non-positive beginning values, negative ending values, or non-positive periods
- Working-capital days -> require a non-negative balance and positive annual flow

## Calculation provenance

`FORMULA_VERSION` identifies the implemented formula rules. Production `calculated_metrics` records should persist that version along with the IDs of the verified financial facts used as inputs. A changed definition or threshold should increment the applicable version instead of silently altering historical output.

## Red flags

Current deterministic signals are:

1. Receivables growing materially faster than revenue
2. Inventory growing materially faster than revenue
3. CFO materially below PAT
4. Debt rising rapidly
5. Interest coverage deteriorating materially
6. Sustained margin deterioration

They are **signals requiring further investigation**, not BUY/SELL outputs or investment recommendations. Missing or non-meaningful evidence suppresses a signal. Thresholds are explicit and the rule set carries `RED_FLAG_RULE_VERSION`.

## Data-definition discipline

Arithmetic is valid only when upstream facts use compatible definitions, periods, currency and scale. The ingestion layer remains responsible for normalization and verified provenance; analytics does not attempt to repair ambiguous source data.

## Tests

`python/tests/test_analytics.py` covers normal cases, missing values, divide-by-zero, negative values, non-positive bases, non-finite inputs, working-capital ratios and red-flag trigger/non-trigger paths.
