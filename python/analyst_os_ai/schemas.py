"""Validated output schemas for source-backed AI insights."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

InsightSection = Literal[
    "business_brief",
    "financial_changes",
    "positives",
    "risks",
    "management_outlook",
]
Confidence = Literal["low", "medium", "high"]
HTML_TAG_PATTERN = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: HttpUrl
    page: int = Field(gt=0)
    section: str | None = Field(default=None, max_length=160)

    @field_validator("source_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("evidence source URL must use HTTPS")
        return value


class AIInsight(BaseModel):
    """One concise, evidence-backed interpretation produced by the local model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    section: InsightSection
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=1800)
    confidence: Confidence
    evidence: list[EvidenceReference] = Field(min_length=1, max_length=8)

    @field_validator("title", "text")
    @classmethod
    def reject_html_like_output(cls, value: str) -> str:
        if HTML_TAG_PATTERN.search(value):
            raise ValueError("AI insight text may not contain HTML-like markup")
        return value


class AIInsightBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    model_name: str = Field(min_length=1, max_length=120)
    insights: list[AIInsight] = Field(min_length=1, max_length=12)
