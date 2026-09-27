"""Local, source-backed AI interpretation for Analyst OS.

Ollama is a local/offline dependency and is never part of the public request path.
"""

from .chunking import DocumentChunk, chunk_pages
from .extractor import DocumentValidationError, ExtractedPage, extract_pdf_pages, resolve_safe_pdf
from .ollama import OllamaSecurityError, generate_json, validate_local_ollama_url
from .pipeline import AIOutputValidationError, generate_insights, validate_insight_bundle
from .schemas import AIInsight, AIInsightBundle, EvidenceReference

__all__ = [
    "AIInsight",
    "AIInsightBundle",
    "AIOutputValidationError",
    "DocumentChunk",
    "DocumentValidationError",
    "EvidenceReference",
    "ExtractedPage",
    "OllamaSecurityError",
    "chunk_pages",
    "extract_pdf_pages",
    "generate_insights",
    "generate_json",
    "resolve_safe_pdf",
    "validate_insight_bundle",
    "validate_local_ollama_url",
]
