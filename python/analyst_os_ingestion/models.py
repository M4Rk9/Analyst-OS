"""Validated input models for source-backed financial ingestion."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

DocumentType = Literal[
    "annual_report",
    "quarterly_result",
    "investor_presentation",
    "earnings_release",
    "exchange_disclosure",
    "ir_material",
]
PeriodType = Literal["FY", "Q1", "Q2", "Q3", "Q4", "TTM"]


class SourceMetadata(BaseModel):
    """Primary-source provenance attached to an ingested fact."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)

    title: str = Field(min_length=1, max_length=300)
    document_type: DocumentType
    source_url: HttpUrl
    publisher: str = Field(min_length=1, max_length=200)
    published_at: date | None = None
    fiscal_year: int | None = Field(default=None, ge=1900, le=2200)
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("source_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("source_url must use HTTPS")
        return value


class FinancialFactRecord(BaseModel):
    """One source observation before database ID resolution."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)

    company_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    period_type: PeriodType
    fiscal_year: int = Field(ge=1900, le=2200)
    period_start: date
    period_end: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    metric_code: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    raw_value: Decimal
    raw_value_text: str | None = Field(default=None, max_length=160)
    unit_scale: Decimal = Field(default=Decimal("1"), gt=0)
    source: SourceMetadata
    source_page: int | None = Field(default=None, gt=0)
    source_label: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def validate_period(self) -> "FinancialFactRecord":
        if self.period_start > self.period_end:
            raise ValueError("period_start must be on or before period_end")
        return self

    @property
    def normalized_value(self) -> Decimal:
        """Return the deterministic base-unit value represented by the record."""

        return self.raw_value * self.unit_scale
