"""Bounded page-aware chunking for untrusted document text."""

from dataclasses import dataclass

from .extractor import ExtractedPage

DEFAULT_CHUNK_CHARS = 4_000


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    page: int
    text: str


def chunk_pages(
    pages: list[ExtractedPage],
    *,
    max_chars: int = DEFAULT_CHUNK_CHARS,
) -> list[DocumentChunk]:
    if max_chars < 500 or max_chars > 12_000:
        raise ValueError("max_chars must be between 500 and 12000")

    chunks: list[DocumentChunk] = []
    for page in pages:
        text = page.text.strip()
        while text:
            if len(text) <= max_chars:
                chunks.append(DocumentChunk(page=page.page, text=text))
                break

            split_at = text.rfind("\n", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = text.rfind(" ", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = max_chars

            chunk = text[:split_at].strip()
            if chunk:
                chunks.append(DocumentChunk(page=page.page, text=chunk))
            text = text[split_at:].strip()

    return chunks
