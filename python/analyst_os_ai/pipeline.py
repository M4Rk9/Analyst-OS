"""Validation boundary around local AI interpretation."""

from pydantic import ValidationError

from .chunking import DocumentChunk
from .ollama import generate_json
from .prompts import SYSTEM_INSTRUCTIONS, build_analysis_prompt
from .schemas import AIInsightBundle


class AIOutputValidationError(ValueError):
    """Raised when local model output cannot be trusted for storage/display."""


def validate_insight_bundle(
    payload: dict[str, object],
    *,
    expected_company_slug: str,
    expected_model_name: str,
    allowed_source_url: str,
    allowed_pages: set[int],
) -> AIInsightBundle:
    try:
        bundle = AIInsightBundle.model_validate(payload)
    except ValidationError as exc:
        raise AIOutputValidationError("AI output failed schema validation") from exc

    if bundle.company_slug != expected_company_slug:
        raise AIOutputValidationError("AI output company does not match request")
    if bundle.model_name != expected_model_name:
        raise AIOutputValidationError("AI output model name does not match request")

    for insight in bundle.insights:
        for evidence in insight.evidence:
            if str(evidence.source_url) != allowed_source_url:
                raise AIOutputValidationError("AI output cited an unapproved source URL")
            if evidence.page not in allowed_pages:
                raise AIOutputValidationError("AI output cited a page not supplied as evidence")
    return bundle


def generate_insights(
    *,
    company_slug: str,
    source_url: str,
    chunks: list[DocumentChunk],
    model: str,
    calculated_metrics: dict[str, str] | None = None,
    ollama_base_url: str = "http://127.0.0.1:11434",
) -> AIInsightBundle:
    """Generate, then strictly validate, a local source-backed insight bundle."""

    if not chunks:
        raise ValueError("at least one evidence chunk is required")

    prompt = build_analysis_prompt(
        company_slug=company_slug,
        source_url=source_url,
        chunks=chunks,
        calculated_metrics=calculated_metrics,
    )
    payload = generate_json(
        model=model,
        system_prompt=SYSTEM_INSTRUCTIONS,
        user_prompt=prompt,
        base_url=ollama_base_url,
    )
    payload["model_name"] = model
    return validate_insight_bundle(
        payload,
        expected_company_slug=company_slug,
        expected_model_name=model,
        allowed_source_url=source_url,
        allowed_pages={chunk.page for chunk in chunks},
    )
