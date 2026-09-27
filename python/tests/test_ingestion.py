from decimal import Decimal
from pathlib import Path

import pytest

from analyst_os_ingestion import (
    DataConflictError,
    FinancialFactRecord,
    IngestionValidationError,
    SourceMetadata,
    assert_no_conflicts,
    load_financial_csv,
    resolve_safe_csv,
)


def source(url: str = "https://example.com/report.pdf") -> SourceMetadata:
    return SourceMetadata(
        title="Annual Report",
        document_type="annual_report",
        source_url=url,
        publisher="Example Company",
        fiscal_year=2026,
    )


def fact(value: str, *, source_url: str = "https://example.com/report.pdf") -> FinancialFactRecord:
    return FinancialFactRecord(
        company_slug="example-company",
        period_type="FY",
        fiscal_year=2026,
        period_start="2025-04-01",
        period_end="2026-03-31",
        currency="INR",
        metric_code="revenue",
        raw_value=value,
        unit_scale="10000000",
        source=source(source_url),
    )


def write_csv(path: Path, rows: list[str]) -> None:
    header = (
        "company_slug,period_type,fiscal_year,period_start,period_end,currency,metric_code,"
        "raw_value,unit_scale,source_title,source_document_type,source_url,source_publisher\n"
    )
    path.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")


def test_normalized_value_is_deterministic_and_negative_values_are_preserved() -> None:
    record = fact("-12.5")
    assert record.normalized_value == Decimal("-125000000.0")


def test_source_url_must_be_https() -> None:
    with pytest.raises(ValueError):
        source("http://example.com/report.pdf")


def test_conflicting_sources_are_not_silently_chosen() -> None:
    records = [
        fact("100", source_url="https://example.com/a.pdf"),
        fact("101", source_url="https://example.com/b.pdf"),
    ]
    with pytest.raises(DataConflictError):
        assert_no_conflicts(records)


def test_matching_sources_do_not_create_false_conflict() -> None:
    records = [
        fact("100", source_url="https://example.com/a.pdf"),
        fact("100", source_url="https://example.com/b.pdf"),
    ]
    assert_no_conflicts(records)


def test_loader_rejects_missing_required_value(tmp_path: Path) -> None:
    csv_path = tmp_path / "facts.csv"
    write_csv(
        csv_path,
        [
            "example-company,FY,2026,2025-04-01,2026-03-31,INR,revenue,,10000000,"
            "Annual Report,annual_report,https://example.com/report.pdf,Example Company"
        ],
    )
    with pytest.raises(IngestionValidationError):
        load_financial_csv("facts.csv", allowed_root=tmp_path)


def test_loader_accepts_valid_controlled_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "facts.csv"
    write_csv(
        csv_path,
        [
            "example-company,FY,2026,2025-04-01,2026-03-31,INR,revenue,123.5,10000000,"
            "Annual Report,annual_report,https://example.com/report.pdf,Example Company"
        ],
    )
    records = load_financial_csv("facts.csv", allowed_root=tmp_path)
    assert len(records) == 1
    assert records[0].normalized_value == Decimal("1235000000.0")


def test_safe_path_blocks_traversal(tmp_path: Path) -> None:
    root = tmp_path / "trusted"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("x", encoding="utf-8")

    with pytest.raises(IngestionValidationError):
        resolve_safe_csv("../outside.csv", allowed_root=root)


def test_safe_path_enforces_size_limit(tmp_path: Path) -> None:
    csv_path = tmp_path / "large.csv"
    csv_path.write_bytes(b"x" * 32)

    with pytest.raises(IngestionValidationError):
        resolve_safe_csv("large.csv", allowed_root=tmp_path, max_bytes=16)
