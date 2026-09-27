"""Secure local extraction of text from trusted-root PDF files."""

from dataclasses import dataclass
from pathlib import Path

import fitz

DEFAULT_MAX_PDF_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_PAGES = 500
DEFAULT_MAX_PAGE_CHARS = 50_000


class DocumentValidationError(ValueError):
    """Raised when a source document fails local security validation."""


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    page: int
    text: str


def resolve_safe_pdf(
    candidate: str | Path,
    *,
    allowed_root: str | Path,
    max_bytes: int = DEFAULT_MAX_PDF_BYTES,
) -> Path:
    root = Path(allowed_root).expanduser().resolve(strict=True)
    path = (root / candidate).expanduser().resolve(strict=True)

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise DocumentValidationError("document path escapes the allowed root") from exc

    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise DocumentValidationError("document must be a PDF inside the allowed root")
    if path.stat().st_size > max_bytes:
        raise DocumentValidationError("document exceeds the configured size limit")

    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise DocumentValidationError("document does not have a valid PDF signature")
    return path


def _clean_text(text: str, *, max_chars: int) -> str:
    cleaned = "".join(char for char in text if char in "\n\t" or ord(char) >= 32)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    return cleaned.strip()[:max_chars]


def extract_pdf_pages(
    candidate: str | Path,
    *,
    allowed_root: str | Path,
    max_bytes: int = DEFAULT_MAX_PDF_BYTES,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_page_chars: int = DEFAULT_MAX_PAGE_CHARS,
) -> list[ExtractedPage]:
    path = resolve_safe_pdf(candidate, allowed_root=allowed_root, max_bytes=max_bytes)
    try:
        document = fitz.open(path)
    except (fitz.FileDataError, RuntimeError) as exc:
        raise DocumentValidationError("unable to parse PDF safely") from exc

    try:
        if document.page_count <= 0 or document.page_count > max_pages:
            raise DocumentValidationError("document page count is outside allowed limits")

        pages: list[ExtractedPage] = []
        for index in range(document.page_count):
            text = _clean_text(document.load_page(index).get_text("text"), max_chars=max_page_chars)
            if text:
                pages.append(ExtractedPage(page=index + 1, text=text))
        return pages
    finally:
        document.close()
