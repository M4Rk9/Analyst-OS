# AI insight pipeline

Analyst OS uses local Ollama only. The public Cloudflare Pages application never calls Ollama and never exposes the Ollama HTTP endpoint.

## Flow

1. A primary-source PDF is placed inside a trusted local ingestion directory.
2. The extractor validates path containment, `.pdf` extension, size, PDF signature, and page count.
3. PyMuPDF extracts bounded page text.
4. Page-aware chunks preserve source-page provenance.
5. Python-calculated metrics may be supplied as verified context.
6. The prompt explicitly treats document content as untrusted evidence, never instructions.
7. Python builds a bounded catalog of exact contiguous source passages, each with an ID and physical PDF page. Whitespace and punctuation inside each passage are preserved.
8. Ollama is called only through a localhost URL and selects passage IDs for its interpretations. Strict Pydantic validation rejects unknown IDs and model-supplied quote, page, or URL overrides. Python attaches the catalog's exact citations before validating the persisted bundle.
9. Company, model, source URL, and cited pages must match the supplied evidence.
10. Only validated output is eligible for controlled storage in `public.ai_insights`.

## Prompt-injection posture

Document text is never granted authority. Instructions found in annual reports, filings, presentations, or any other source are treated as quoted data. The system prompt explicitly forbids following embedded commands, role changes, requests for secrets, tool calls, or other instruction-like content.

This is defense-in-depth rather than a claim that prompt injection is perfectly solvable. The key architectural protection is that the model has no tools, shell access, secrets, production-write credentials, or public network role.

## Output restrictions

AI output must not contain or drive:

- authoritative financial calculations
- invented missing numbers
- executable HTML/JavaScript
- shell commands
- direct database writes
- BUY/SELL labels
- target prices
- guaranteed returns

## Provenance

Each stored insight retains company, source document, source page, optional source section, model name, prompt version, validation status, and timestamps. The database exposes only validated rows through SELECT-only RLS policy.

## Controlled M4 execution

Use [M4_CONTROLLED_PUBLICATION.md](M4_CONTROLLED_PUBLICATION.md) for the executable workflow. Legacy schema/page-only validation is draft-level validation, not publication approval. Publication requires exact quotations, a pinned PDF/model digest, explicit review of the exact draft, native preview hashes and a durable receipt. Live AI publication is pending.

## Exact passage selection

Generation asks for 1–3 concise supported interpretations and may omit sections. Short fragments under 20 characters are excluded; passages are at most 800 characters. Passage IDs are local to each request, and only the resolved quote/page/URL is saved in the draft. The persisted `reviewed-quotes-2.0` contract and database migration are unchanged. Freehand rejected drafts cannot be repaired through this path: generate a new draft instead.

Exact quotation matching establishes provenance, not semantic support. A reviewer must still check the whole claim against its selected passages, attribute management aspirations, and reject misleading or unsupported interpretations. A catalog can contain untrusted instructions, but those instructions have no authority. Live M4 completion still requires genuine local generation, explicit review, controlled publication, receipt verification, and public UI checks.
