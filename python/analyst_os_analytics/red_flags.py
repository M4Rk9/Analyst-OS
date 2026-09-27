"""Deterministic investigation signals for Analyst OS.

These rules produce research prompts, not investment recommendations. Missing or
non-meaningful evidence suppresses a signal instead of guessing.
"""

from dataclasses import dataclass
from decimal import Decimal

from .formulas import growth_rate, safe_divide, to_decimal

RED_FLAG_RULE_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class RedFlag:
    code: str
    title: str
    description: str
    severity: str
    evidence: dict[str, str]
    rule_version: str = RED_FLAG_RULE_VERSION


def _text(value: Decimal | None) -> str:
    return "unavailable" if value is None else format(value, "f")


def receivables_outpace_revenue(
    *,
    receivables_current: object,
    receivables_previous: object,
    revenue_current: object,
    revenue_previous: object,
    spread_threshold_pct: Decimal = Decimal("15"),
) -> RedFlag | None:
    receivable_growth = growth_rate(receivables_current, receivables_previous)
    revenue_growth = growth_rate(revenue_current, revenue_previous)
    if receivable_growth is None or revenue_growth is None:
        return None
    spread = receivable_growth - revenue_growth
    if spread < spread_threshold_pct:
        return None
    return RedFlag(
        code="receivables_outpace_revenue",
        title="Receivables are growing faster than revenue",
        description=(
            "Receivables growth materially exceeds revenue growth; "
            "investigate collection quality."
        ),
        severity="medium",
        evidence={
            "receivables_growth_pct": _text(receivable_growth),
            "revenue_growth_pct": _text(revenue_growth),
            "spread_pct": _text(spread),
        },
    )


def inventory_outpaces_revenue(
    *,
    inventory_current: object,
    inventory_previous: object,
    revenue_current: object,
    revenue_previous: object,
    spread_threshold_pct: Decimal = Decimal("15"),
) -> RedFlag | None:
    inventory_growth = growth_rate(inventory_current, inventory_previous)
    revenue_growth = growth_rate(revenue_current, revenue_previous)
    if inventory_growth is None or revenue_growth is None:
        return None
    spread = inventory_growth - revenue_growth
    if spread < spread_threshold_pct:
        return None
    return RedFlag(
        code="inventory_outpaces_revenue",
        title="Inventory is growing faster than revenue",
        description=(
            "Inventory growth materially exceeds revenue growth; "
            "investigate demand and obsolescence."
        ),
        severity="medium",
        evidence={
            "inventory_growth_pct": _text(inventory_growth),
            "revenue_growth_pct": _text(revenue_growth),
            "spread_pct": _text(spread),
        },
    )


def weak_cash_conversion(
    *,
    cash_from_operations: object,
    profit_after_tax: object,
    threshold: Decimal = Decimal("0.7"),
) -> RedFlag | None:
    ratio = safe_divide(cash_from_operations, profit_after_tax)
    pat = to_decimal(profit_after_tax)
    if ratio is None or pat is None or pat <= 0 or ratio >= threshold:
        return None
    return RedFlag(
        code="weak_cash_conversion",
        title="Operating cash flow is materially below PAT",
        description=(
            "CFO/PAT is below the configured threshold; investigate earnings-to-cash conversion."
        ),
        severity="high",
        evidence={"cfo_pat": _text(ratio), "threshold": _text(threshold)},
    )


def debt_rising_rapidly(
    *,
    debt_current: object,
    debt_previous: object,
    threshold_pct: Decimal = Decimal("30"),
) -> RedFlag | None:
    debt_growth = growth_rate(debt_current, debt_previous)
    if debt_growth is None or debt_growth < threshold_pct:
        return None
    return RedFlag(
        code="debt_rising_rapidly",
        title="Debt increased rapidly",
        description=(
            "Total debt increased beyond the configured threshold; "
            "investigate funding needs and leverage."
        ),
        severity="medium",
        evidence={"debt_growth_pct": _text(debt_growth), "threshold_pct": _text(threshold_pct)},
    )


def falling_interest_coverage(
    *,
    coverage_current: object,
    coverage_previous: object,
    decline_threshold_pct: Decimal = Decimal("25"),
) -> RedFlag | None:
    decline = growth_rate(coverage_current, coverage_previous)
    if decline is None or decline > -decline_threshold_pct:
        return None
    return RedFlag(
        code="falling_interest_coverage",
        title="Interest coverage deteriorated materially",
        description="Interest coverage declined materially; investigate debt-service resilience.",
        severity="high",
        evidence={"coverage_change_pct": _text(decline)},
    )


def sustained_margin_deterioration(
    *,
    margins: list[object],
    minimum_decline_points: Decimal = Decimal("2"),
) -> RedFlag | None:
    parsed = [to_decimal(value) for value in margins]
    if len(parsed) < 3 or any(value is None for value in parsed):
        return None
    values = [value for value in parsed if value is not None]
    if not all(left > right for left, right in zip(values, values[1:], strict=False)):
        return None
    total_decline = values[0] - values[-1]
    if total_decline < minimum_decline_points:
        return None
    return RedFlag(
        code="sustained_margin_deterioration",
        title="Margins have deteriorated across consecutive periods",
        description=(
            "Margins declined in each observed period; investigate pricing, mix, and cost pressure."
        ),
        severity="medium",
        evidence={"total_decline_points": _text(total_decline), "periods": str(len(values))},
    )
