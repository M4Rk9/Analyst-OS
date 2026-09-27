"""Deterministic financial formulas for Analyst OS.

Missing or financially non-meaningful inputs produce ``None`` rather than invented
values. Percentages are returned as percentage points (12.5 means 12.5%).
"""

from decimal import Decimal, InvalidOperation

Number = int | float | str | Decimal
FORMULA_VERSION = "1.0"
DAYS_PER_YEAR = Decimal("365")


def to_decimal(value: Number | None) -> Decimal | None:
    """Convert supported numeric input to finite ``Decimal``."""

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


def _positive_denominator_ratio(
    numerator: Number | None,
    denominator: Number | None,
) -> Decimal | None:
    num = to_decimal(numerator)
    den = to_decimal(denominator)
    if num is None or den is None or den <= 0:
        return None
    return num / den


def percentage_ratio(numerator: Number | None, denominator: Number | None) -> Decimal | None:
    ratio = safe_divide(numerator, denominator)
    return None if ratio is None else ratio * Decimal("100")


def growth_rate(current: Number | None, previous: Number | None) -> Decimal | None:
    """Period-on-period growth in percent when the comparison base is positive.

    Percentage growth from a zero or negative base is suppressed as not meaningful.
    A negative current value is still supported when the previous value is positive.
    """

    current_value = to_decimal(current)
    previous_value = to_decimal(previous)
    if current_value is None or previous_value is None or previous_value <= 0:
        return None
    return ((current_value - previous_value) / previous_value) * Decimal("100")


def cagr(ending: Number | None, beginning: Number | None, years: int) -> Decimal | None:
    """Compound annual growth rate in percent for meaningful positive endpoints."""

    end_value = to_decimal(ending)
    begin_value = to_decimal(beginning)
    if end_value is None or begin_value is None or begin_value <= 0 or end_value < 0 or years <= 0:
        return None
    ratio = end_value / begin_value
    powered = Decimal(str(float(ratio) ** (1 / years)))
    return (powered - Decimal("1")) * Decimal("100")


def margin(profit: Number | None, revenue: Number | None) -> Decimal | None:
    ratio = _positive_denominator_ratio(profit, revenue)
    return None if ratio is None else ratio * Decimal("100")


def roe(net_income: Number | None, average_equity: Number | None) -> Decimal | None:
    ratio = _positive_denominator_ratio(net_income, average_equity)
    return None if ratio is None else ratio * Decimal("100")


def roa(net_income: Number | None, average_assets: Number | None) -> Decimal | None:
    ratio = _positive_denominator_ratio(net_income, average_assets)
    return None if ratio is None else ratio * Decimal("100")


def roce(
    ebit: Number | None,
    total_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    assets = to_decimal(total_assets)
    current_liab = to_decimal(current_liabilities)
    if assets is None or current_liab is None:
        return None
    ratio = _positive_denominator_ratio(ebit, assets - current_liab)
    return None if ratio is None else ratio * Decimal("100")


def debt_to_equity(total_debt: Number | None, total_equity: Number | None) -> Decimal | None:
    return _positive_denominator_ratio(total_debt, total_equity)


def current_ratio(
    current_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    return _positive_denominator_ratio(current_assets, current_liabilities)


def interest_coverage(ebit: Number | None, interest_expense: Number | None) -> Decimal | None:
    return _positive_denominator_ratio(ebit, interest_expense)


def free_cash_flow(
    cash_from_operations: Number | None,
    capital_expenditure: Number | None,
) -> Decimal | None:
    """Return CFO minus capex magnitude, tolerating either capex sign convention."""

    cfo = to_decimal(cash_from_operations)
    capex = to_decimal(capital_expenditure)
    if cfo is None or capex is None:
        return None
    return cfo - abs(capex)


def cfo_to_pat(
    cash_from_operations: Number | None,
    profit_after_tax: Number | None,
) -> Decimal | None:
    return _positive_denominator_ratio(cash_from_operations, profit_after_tax)


def working_capital(
    current_assets: Number | None,
    current_liabilities: Number | None,
) -> Decimal | None:
    assets = to_decimal(current_assets)
    liabilities = to_decimal(current_liabilities)
    if assets is None or liabilities is None:
        return None
    return assets - liabilities


def _days_ratio(
    average_balance: Number | None,
    annual_flow: Number | None,
    *,
    days: Decimal = DAYS_PER_YEAR,
) -> Decimal | None:
    balance = to_decimal(average_balance)
    flow = to_decimal(annual_flow)
    if balance is None or flow is None or balance < 0 or flow <= 0 or days <= 0:
        return None
    return (balance / flow) * days


def receivables_days(
    average_receivables: Number | None,
    revenue: Number | None,
) -> Decimal | None:
    return _days_ratio(average_receivables, revenue)


def inventory_days(
    average_inventory: Number | None,
    cost_of_goods_sold: Number | None,
) -> Decimal | None:
    return _days_ratio(average_inventory, cost_of_goods_sold)


def payables_days(
    average_payables: Number | None,
    cost_of_goods_sold: Number | None,
) -> Decimal | None:
    return _days_ratio(average_payables, cost_of_goods_sold)


def cash_conversion_cycle(
    receivable_days_value: Number | None,
    inventory_days_value: Number | None,
    payable_days_value: Number | None,
) -> Decimal | None:
    receivables = to_decimal(receivable_days_value)
    inventory = to_decimal(inventory_days_value)
    payables = to_decimal(payable_days_value)
    if receivables is None or inventory is None or payables is None:
        return None
    return receivables + inventory - payables
