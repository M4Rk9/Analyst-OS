"""Deterministic financial formulas for Analyst OS.

All functions are intentionally small, explicit, and side-effect free. Missing inputs
produce ``None`` rather than invented values. Division by zero also produces ``None``.
Percentages are returned as percentage points (for example, 12.5 means 12.5%).
"""

from decimal import Decimal, InvalidOperation

Number = int | float | str | Decimal


def to_decimal(value: Number | None) -> Decimal | None:
    """Convert supported numeric input to ``Decimal`` without accepting NaN/Infinity."""

    if value is None:
        return None
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid numeric value") from exc
    if not result.is_finite():
        raise ValueError("numeric value must be finite")
    return result


def safe_divide(numerator: Number | None, denominator: Number | None) -> Decimal | None:
    """Return numerator / denominator, or ``None`` for missing/zero denominator."""

    num = to_decimal(numerator)
    den = to_decimal(denominator)
    if num is None or den is None or den == 0:
        return None
    return num / den


def percentage_ratio(numerator: Number | None, denominator: Number | None) -> Decimal | None:
    ratio = safe_divide(numerator, denominator)
    return None if ratio is None else ratio * Decimal("100")


def growth_rate(current: Number | None, previous: Number | None) -> Decimal | None:
    """Period-on-period growth in percent, preserving negative numerators."""

    current_value = to_decimal(current)
    previous_value = to_decimal(previous)
    if current_value is None or previous_value is None or previous_value == 0:
        return None
    return ((current_value - previous_value) / abs(previous_value)) * Decimal("100")


def cagr(ending: Number | None, beginning: Number | None, years: int) -> Decimal | None:
    """Compound annual growth rate in percent for positive endpoints."""

    end_value = to_decimal(ending)
    begin_value = to_decimal(beginning)
    if end_value is None or begin_value is None or begin_value <= 0 or end_value < 0 or years <= 0:
        return None
    ratio = end_value / begin_value
    annual_factor = Decimal(str(float(ratio) ** (1 / years)))
    return (annual_factor - Decimal("1")) * Decimal("100")


def margin(profit: Number | None, revenue: Number | None) -> Decimal | None:
    return percentage_ratio(profit, revenue)


def roe(net_income: Number | None, average_equity: Number | None) -> Decimal | None:
    return percentage_ratio(net_income, average_equity)


def roa(net_income: Number | None, average_assets: Number | None) -> Decimal | None:
    return percentage_ratio(net_income, average_assets)


def roce(
    ebit: Number | None,
    total_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    assets = to_decimal(total_assets)
    current_liab = to_decimal(current_liabilities)
    if assets is None or current_liab is None:
        return None
    return percentage_ratio(ebit, assets - current_liab)


def debt_to_equity(total_debt: Number | None, total_equity: Number | None) -> Decimal | None:
    return safe_divide(total_debt, total_equity)


def current_ratio(
    current_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    return safe_divide(current_assets, current_liabilities)


def interest_coverage(ebit: Number | None, interest_expense: Number | None) -> Decimal | None:
    return safe_divide(ebit, interest_expense)


def free_cash_flow(
    cash_from_operations: Number | None,
    capital_expenditure: Number | None,
) -> Decimal | None:
    cfo = to_decimal(cash_from_operations)
    capex = to_decimal(capital_expenditure)
    if cfo is None or capex is None:
        return None
    return cfo - abs(capex)


def cfo_to_pat(
    cash_from_operations: Number | None,
    profit_after_tax: Number | None,
) -> Decimal | None:
    return safe_divide(cash_from_operations, profit_after_tax)


def working_capital(
    current_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    assets = to_decimal(current_assets)
    liabilities = to_decimal(current_liabilities)
    if assets is None or liabilities is None:
        return None
    return assets - liabilities
