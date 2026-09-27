"""Validated output schemas for source-backed AI insights."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

InsightSection = Literal[
    "business_brief",
    "financial_changes",
    "positives",
    "risks",
    "management_outlook",
]
Confidence = Literal["low", "medium", "high"]


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: HttpUrl
    page: int = Field(gt=0)
    section: str | None = Field(default=None, max_length=160)


class AIInsight(BaseModel):
    """One concise, evidence-backed interpretation produced by the local model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    section: InsightSection
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=1800)
    confidence: Confidence
    evidence: list[EvidenceReference] = Field(min_length=1, max_length=8)


class AIInsightBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    model_name: str = Field(min_length=1, max_length=120)
    insights: list[AIInsight] = Field(min_length=1, max_length=12)
