"""Safe CSV loader for controlled local financial ingestion."""

from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from .conflicts import assert_no_conflicts
from .models import FinancialFactRecord, SourceMetadata

DEFAULT_MAX_CSV_BYTES = 5 * 1024 * 1024

REQUIRED_COLUMNS = {
    "company_slug",
    "period_type",
    "fiscal_year",
    "period_start",
    "period_end",
    "currency",
    "metric_code",
    "raw_value",
    "unit_scale",
    "source_title",
    "source_document_type",
    "source_url",
    "source_publisher",
}


class IngestionValidationError(ValueError):
    """Raised for invalid local inputs without echoing potentially hostile content."""


def resolve_safe_csv(
    candidate: str | Path,
    *,
    allowed_root: str | Path,
    max_bytes: int = DEFAULT_MAX_CSV_BYTES,
) -> Path:
    root = Path(allowed_root).expanduser().resolve(strict=True)
    path = (root / candidate).expanduser().resolve(strict=True)

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise IngestionValidationError("input path escapes the allowed ingestion root") from exc

    if not path.is_file() or path.suffix.lower() != ".csv":
        raise IngestionValidationError("input must be a CSV file inside the allowed root")
    if path.stat().st_size > max_bytes:
        raise IngestionValidationError("input CSV exceeds the configured size limit")
    return path


def _optional(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def _record_from_row(row: dict[str, str]) -> FinancialFactRecord:
    source = SourceMetadata(
        title=row["source_title"],
        document_type=row["source_document_type"],
        source_url=row["source_url"],
        publisher=row["source_publisher"],
        published_at=_optional(row.get("source_published_at", "")),
        fiscal_year=_optional(row.get("source_fiscal_year", "")),
        fiscal_quarter=_optional(row.get("source_fiscal_quarter", "")),
        sha256=_optional(row.get("source_sha256", "")),
    )
    return FinancialFactRecord(
        company_slug=row["company_slug"],
        period_type=row["period_type"],
        fiscal_year=row["fiscal_year"],
        period_start=row["period_start"],
        period_end=row["period_end"],
        currency=row["currency"],
        metric_code=row["metric_code"],
        raw_value=row["raw_value"],
        raw_value_text=_optional(row.get("raw_value_text", "")),
        unit_scale=row["unit_scale"],
        source=source,
        source_page=_optional(row.get("source_page", "")),
        source_label=_optional(row.get("source_label", "")),
    )


def load_financial_csv(
    candidate: str | Path,
    *,
    allowed_root: str | Path,
    max_bytes: int = DEFAULT_MAX_CSV_BYTES,
) -> list[FinancialFactRecord]:
    path = resolve_safe_csv(candidate, allowed_root=allowed_root, max_bytes=max_bytes)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise IngestionValidationError(
            f"CSV is missing required columns: {', '.join(sorted(missing))}"
        )

    records: list[FinancialFactRecord] = []
    for index, row in frame.iterrows():
        try:
            records.append(_record_from_row(row.to_dict()))
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            raise IngestionValidationError(f"invalid financial fact at CSV row {index + 2}") from exc

    assert_no_conflicts(records)
    return records
