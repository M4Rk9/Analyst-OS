"""Exact source passages and strict model-selected evidence references."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from .chunking import DocumentChunk
from .schemas import AIInsight


@dataclass(frozen=True)
class SourcePassage:
    quote_id: str
    page: int
    quote: str


def build_passages(chunks: list[DocumentChunk]) -> list[SourcePassage]:
    """Slice contiguous text without rewriting whitespace or punctuation."""
    passages = []
    for chunk in chunks:
        if chunk.page < 1:
            raise ValueError("evidence pages must be positive")
        start = 0
        while start < len(chunk.text):
            end = min(start + 800, len(chunk.text))
            if end < len(chunk.text):
                boundary = chunk.text.rfind("\n", start + 400, end)
                if boundary != -1:
                    end = boundary + 1
            quote = chunk.text[start:end].strip()
            if len(quote) >= 20:
                passages.append(SourcePassage(f"Q{len(passages) + 1:04d}", chunk.page, quote))
            start = end
    if not passages:
        raise ValueError("source has no passages of at least 20 characters")
    if len(passages) > 512:
        raise ValueError("too many source passages for one AI request")
    return passages


class SelectedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    quote_id: str = Field(pattern=r"^Q[0-9]{4}$")


class SelectedInsight(AIInsight):
    evidence: list[SelectedEvidence] = Field(min_length=1, max_length=8)


class SelectedBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    insights: list[SelectedInsight] = Field(min_length=1, max_length=12)


def resolve_selection(
    payload: dict[str, object],
    *,
    passages: list[SourcePassage],
    source_url: str,
    model: str,
) -> dict[str, object]:
    """Attach trusted citations; never repair freehand model quotations."""
    selected = SelectedBundle.model_validate(payload)
    catalog = {passage.quote_id: passage for passage in passages}
    if len(catalog) != len(passages):
        raise ValueError("duplicate source passage IDs")
    result = selected.model_dump()
    for insight in result["insights"]:
        citations = []
        for evidence in insight["evidence"]:
            passage = catalog.get(evidence["quote_id"])
            if passage is None:
                raise ValueError("AI output selected an unknown source passage")
            citations.append({"source_url": source_url, "page": passage.page,
                              "section": None, "quote": passage.quote})
        insight["evidence"] = citations
    result["model_name"] = model
    return result
