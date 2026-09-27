"""Deterministic financial analytics for Analyst OS.

Authoritative financial calculations live here. Language models may explain validated
outputs but must not replace these calculations.
"""

from .formulas import (
    FORMULA_VERSION,
    cagr,
    cash_conversion_cycle,
    cfo_to_pat,
    current_ratio,
    debt_to_equity,
    free_cash_flow,
    growth_rate,
    interest_coverage,
    inventory_days,
    margin,
    payables_days,
    percentage_ratio,
    receivables_days,
    roa,
    roce,
    roe,
    safe_divide,
    to_decimal,
    working_capital,
)
from .red_flags import (
    RED_FLAG_RULE_VERSION,
    RedFlag,
    debt_rising_rapidly,
    falling_interest_coverage,
    inventory_outpaces_revenue,
    receivables_outpace_revenue,
    sustained_margin_deterioration,
    weak_cash_conversion,
)

__all__ = [
    "FORMULA_VERSION",
    "RED_FLAG_RULE_VERSION",
    "RedFlag",
    "cagr",
    "cash_conversion_cycle",
    "cfo_to_pat",
    "current_ratio",
    "debt_rising_rapidly",
    "debt_to_equity",
    "falling_interest_coverage",
    "free_cash_flow",
    "growth_rate",
    "interest_coverage",
    "inventory_days",
    "inventory_outpaces_revenue",
    "margin",
    "payables_days",
    "percentage_ratio",
    "receivables_days",
    "receivables_outpace_revenue",
    "roa",
    "roce",
    "roe",
    "safe_divide",
    "sustained_margin_deterioration",
    "to_decimal",
    "weak_cash_conversion",
    "working_capital",
]
