"""Duplicate and conflict detection for financial observations."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from .models import FinancialFactRecord


@dataclass(frozen=True)
class FactKey:
    company_slug: str
    period_type: str
    fiscal_year: int
    period_end: str
    metric_code: str


@dataclass(frozen=True)
class FactConflict:
    key: FactKey
    values: tuple[tuple[str, Decimal], ...]


class DataConflictError(ValueError):
    """Raised when competing source observations cannot be silently reconciled."""


def fact_key(record: FinancialFactRecord) -> FactKey:
    return FactKey(
        company_slug=record.company_slug,
        period_type=record.period_type,
        fiscal_year=record.fiscal_year,
        period_end=record.period_end.isoformat(),
        metric_code=record.metric_code,
    )


def find_conflicts(records: list[FinancialFactRecord]) -> list[FactConflict]:
    grouped: dict[FactKey, list[FinancialFactRecord]] = defaultdict(list)
    for record in records:
        grouped[fact_key(record)].append(record)

    conflicts: list[FactConflict] = []
    for key, observations in grouped.items():
        distinct = {(record.currency, record.normalized_value) for record in observations}
        if len(distinct) > 1:
            conflicts.append(FactConflict(key=key, values=tuple(sorted(distinct))))
    return conflicts


def assert_no_conflicts(records: list[FinancialFactRecord]) -> None:
    conflicts = find_conflicts(records)
    if conflicts:
        keys = ", ".join(conflict.key.metric_code for conflict in conflicts[:5])
        raise DataConflictError(f"unresolved source conflicts detected for: {keys}")
