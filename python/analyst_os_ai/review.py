"""Exact, reviewer-selected AI drafts; structural checks are not semantic approval."""

import re
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from analyst_os_ingestion.planning import digest
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from .schemas import AIInsightBundle

PROMPT_VERSION = "reviewed-quotes-2.0"
RESTRICTED = re.compile(
    r"\b(?:buy|sell|target price|guaranteed returns?)\b|```|<\s*/?\s*[A-Za-z]", re.I
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Source(Strict):
    id: str
    company_id: str
    company_slug: str
    source_url: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_count: int = Field(gt=0)
    fiscal_year: int

    @field_validator("id", "company_id")
    @classmethod
    def uuid_string(cls, value):
        UUID(value)
        return value

    @field_validator("source_url")
    @classmethod
    def https_only(cls, value):
        if HttpUrl(value).scheme != "https":
            raise ValueError("source must use HTTPS")
        return value


class Page(Strict):
    page: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=50_000)


class Draft(Strict):
    version: int = Field(default=1, ge=1, le=1)
    prompt_version: str = Field(default=PROMPT_VERSION, pattern=r"^reviewed-quotes-2\.0$")
    source: Source
    model_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    pages: list[Page] = Field(min_length=1, max_length=10)
    bundle: AIInsightBundle


class Decision(Strict):
    status: str = Field(pattern=r"^(pending|approved|rejected)$")
    reviewer: str = Field(max_length=120)
    rationale: str = Field(max_length=1800)
    reviewed_at: str = Field(default="", max_length=40)


class Review(Strict):
    version: int = Field(default=1, ge=1, le=1)
    draft_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decisions: dict[str, Decision]


def checked_draft(payload):
    draft = Draft.model_validate(payload)
    pages = {p.page: p.text for p in draft.pages}
    if len(pages) != len(draft.pages) or max(pages) > draft.source.page_count:
        raise ValueError("duplicate or out-of-range evidence pages")
    if sum(len(p.text) for p in draft.pages) > 40_000:
        raise ValueError("evidence context exceeds 40000 characters")
    if draft.bundle.company_slug != draft.source.company_slug:
        raise ValueError("draft company mismatch")
    for insight in draft.bundle.insights:
        if RESTRICTED.search(insight.title + " " + insight.text):
            raise ValueError("draft contains restricted recommendation or markup")
        for evidence in insight.evidence:
            if str(evidence.source_url) != str(HttpUrl(draft.source.source_url)):
                raise ValueError("unapproved evidence URL")
            if evidence.page not in pages or not evidence.quote:
                raise ValueError("reviewed insight requires a supplied page and quotation")
            if evidence.quote not in pages[evidence.page]:
                raise ValueError("quotation does not occur on the cited extracted PDF page")
    return draft.model_dump(mode="json")


def review_template(payload):
    draft = checked_draft(payload)
    return {
        "version": 1,
        "draft_sha256": digest(draft),
        "decisions": {
            str(i): {"status": "pending", "reviewer": "", "rationale": "", "reviewed_at": ""}
            for i in range(len(draft["bundle"]["insights"]))
        },
    }


def approved_rows(payload, review_payload):
    draft = checked_draft(payload)
    review = Review.model_validate(review_payload).model_dump(mode="json")
    if review["draft_sha256"] != digest(draft):
        raise ValueError("review does not bind this exact draft")
    if set(review["decisions"]) != {str(i) for i in range(len(draft["bundle"]["insights"]))}:
        raise ValueError("review must cover each exact candidate index")
    rows = []
    for index, insight in enumerate(draft["bundle"]["insights"]):
        decision = review["decisions"][str(index)]
        if decision["status"] != "approved":
            continue
        if not decision["reviewer"].strip() or not decision["rationale"].strip():
            raise ValueError("approval requires reviewer and rationale")
        timestamp = datetime.fromisoformat(decision["reviewed_at"])
        if timestamp.tzinfo is None or timestamp > datetime.now(UTC):
            raise ValueError("approval requires an actual timezone-aware review timestamp")
        rows.append(
            {
                "id": str(uuid5(NAMESPACE_URL, f"analyst-os:ai:{digest(draft)}:{index}")),
                "company_id": draft["source"]["company_id"],
                "source_document_id": draft["source"]["id"],
                "section": insight["section"],
                "title": insight["title"],
                "insight_text": insight["text"],
                "confidence": insight["confidence"],
                "evidence": insight["evidence"],
                "model_name": draft["bundle"]["model_name"],
                "prompt_version": PROMPT_VERSION,
                "validation_status": "validated",
                "source_sha256": draft["source"]["sha256"],
                "review_sha256": digest(review),
                "model_digest": draft["model_digest"],
                "candidate_index": index,
            }
        )
    if not rows:
        raise ValueError("no explicitly approved AI insights")
    return draft, review, rows
