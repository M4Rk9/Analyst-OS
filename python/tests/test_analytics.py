from decimal import Decimal

import pytest
from analyst_os_analytics.formulas import (
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
    receivables_days,
    roa,
    roce,
    roe,
    safe_divide,
    working_capital,
)
from analyst_os_analytics.red_flags import (
    debt_rising_rapidly,
    falling_interest_coverage,
    inventory_outpaces_revenue,
    receivables_outpace_revenue,
    sustained_margin_deterioration,
    weak_cash_conversion,
)


def test_safe_divide_handles_missing_and_zero() -> None:
    assert safe_divide(None, 10) is None
    assert safe_divide(10, None) is None
    assert safe_divide(10, 0) is None


def test_growth_rate_supports_negative_current_value() -> None:
    assert growth_rate(-50, 100) == Decimal("-150.0")


def test_growth_rate_suppresses_non_positive_base() -> None:
    assert growth_rate(-50, -100) is None
    assert growth_rate(10, 0) is None


def test_margin_and_return_ratios() -> None:
    assert margin(20, 100) == Decimal("20.0")
    assert margin(-10, 100) == Decimal("-10.0")
    assert roe(15, 100) == Decimal("15.00")
    assert roa(10, 200) == Decimal("5.00")
    assert roce(20, 250, 50) == Decimal("10.0")


def test_non_positive_financial_denominators_are_suppressed() -> None:
    assert margin(10, 0) is None
    assert roe(10, -100) is None
    assert roa(10, 0) is None
    assert debt_to_equity(10, -5) is None
    assert current_ratio(10, 0) is None
    assert interest_coverage(10, -2) is None


def test_leverage_and_liquidity_ratios() -> None:
    assert debt_to_equity(50, 100) == Decimal("0.5")
    assert current_ratio(150, 100) == Decimal("1.5")
    assert interest_coverage(40, 10) == Decimal("4")


def test_cash_flow_metrics() -> None:
    assert free_cash_flow(100, 25) == Decimal("75")
    assert free_cash_flow(100, -25) == Decimal("75")
    assert cfo_to_pat(80, 100) == Decimal("0.8")
    assert cfo_to_pat(80, -100) is None
    assert working_capital(150, 100) == Decimal("50")


def test_working_capital_days_and_cash_conversion_cycle() -> None:
    assert receivables_days(100, 1000) == Decimal("36.5")
    assert inventory_days(200, 1000) == Decimal("73.0")
    assert payables_days(150, 1000) == Decimal("54.75")
    assert cash_conversion_cycle("36.5", "73", "54.75") == Decimal("54.75")


def test_working_capital_days_require_meaningful_flows() -> None:
    assert receivables_days(100, 0) is None
    assert inventory_days(-1, 1000) is None
    assert payables_days(100, -1000) is None
    assert cash_conversion_cycle(10, None, 5) is None


def test_cagr_handles_edge_cases() -> None:
    assert cagr(121, 100, 2) == pytest.approx(Decimal("10"), rel=Decimal("0.000001"))
    assert cagr(100, 0, 2) is None
    assert cagr(-100, 50, 2) is None
    assert cagr(100, 50, 0) is None


def test_non_finite_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        safe_divide("NaN", 1)


def test_receivables_signal_only_when_growth_spread_is_material() -> None:
    flag = receivables_outpace_revenue(
        receivables_current=140,
        receivables_previous=100,
        revenue_current=110,
        revenue_previous=100,
    )
    assert flag is not None
    assert flag.code == "receivables_outpace_revenue"

    assert (
        receivables_outpace_revenue(
            receivables_current=110,
            receivables_previous=100,
            revenue_current=105,
            revenue_previous=100,
        )
        is None
    )


def test_inventory_signal_requires_evidence() -> None:
    assert (
        inventory_outpaces_revenue(
            inventory_current=None,
            inventory_previous=100,
            revenue_current=110,
            revenue_previous=100,
        )
        is None
    )


def test_weak_cash_conversion_rule() -> None:
    assert weak_cash_conversion(cash_from_operations=50, profit_after_tax=100) is not None
    assert weak_cash_conversion(cash_from_operations=90, profit_after_tax=100) is None
    assert weak_cash_conversion(cash_from_operations=-10, profit_after_tax=-20) is None


def test_debt_growth_rule() -> None:
    assert debt_rising_rapidly(debt_current=140, debt_previous=100) is not None
    assert debt_rising_rapidly(debt_current=120, debt_previous=100) is None


def test_interest_coverage_rule() -> None:
    assert falling_interest_coverage(coverage_current=2, coverage_previous=4) is not None
    assert falling_interest_coverage(coverage_current=3.5, coverage_previous=4) is None


def test_sustained_margin_deterioration_rule() -> None:
    assert sustained_margin_deterioration(margins=[20, 18.5, 17]) is not None
    assert sustained_margin_deterioration(margins=[20, 19.5, 20]) is None
    assert sustained_margin_deterioration(margins=[20, None, 17]) is None
