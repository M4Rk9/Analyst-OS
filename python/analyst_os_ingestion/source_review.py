"""Local PDF evidence checks; never create review approvals or replace financial values."""

import hashlib
import re
from decimal import Decimal
from pathlib import Path

import fitz

from .amounts import printed_amount
from .planning import digest

MAX_PDF_BYTES = 40_000_000


def compact_label(text: str) -> str:
    return re.sub(r"\s", "", text).casefold()



def page_lines(page) -> list[dict]:
    return [
        {"text": "".join(s["text"] for s in line["spans"]), "bbox": list(line["bbox"])}
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
    ]


def check_pnl_row(lines: list[dict], observation: dict) -> dict:
    """Bind a unique label row to its dated column, rather than any number on a page."""
    labels = [
        line
        for line in lines
        if compact_label(line["text"]) == compact_label(observation["source_label"])
    ]
    if len(labels) != 1:
        raise ValueError("P&L label missing or ambiguous")
    label = labels[0]
    report_year = observation["source_fiscal_year"]
    headers = []
    for year in [report_year, report_year - 1]:
        candidates = [
            line
            for line in lines
            if compact_label(line["text"]) in {f"{year - 1}-{str(year)[-2:]}", f"march31,{year}"}
            and line["bbox"][0] > label["bbox"][2]
            and line["bbox"][3] < label["bbox"][1] + 2
        ]
        if not candidates:
            raise ValueError("dated P&L column header missing")
        # A two-page spread can repeat a header over the continuation pane.
        headers.append(min(candidates, key=lambda line: line["bbox"][0]))
    if headers[0]["bbox"][0] >= headers[1]["bbox"][0]:
        raise ValueError("unsupported P&L column order")
    slot = 0 if observation["column_role"] == "current_year" else 1
    if observation["column_role"] not in {"current_year", "comparative"}:
        raise ValueError("unsupported P&L column role")
    if observation["fiscal_year"] != report_year - slot:
        raise ValueError("observation fiscal year differs from dated source column")
    header = headers[slot]
    other = headers[1 - slot]
    numeric = []
    for line in lines:
        # Bottom baselines accommodate small bold/regular font-height differences.
        if abs(line["bbox"][3] - label["bbox"][3]) > 2:
            continue
        if line["bbox"][0] <= label["bbox"][2]:
            continue
        if printed_amount(line["text"]) is None:
            continue
        right = line["bbox"][2]
        if abs(right - header["bbox"][2]) < 30 and (
            abs(right - header["bbox"][2]) < abs(right - other["bbox"][2])
        ):
            numeric.append(line)
    if len(numeric) != 1:
        raise ValueError("P&L amount missing or ambiguous in dated label row")
    amount = numeric[0]
    actual = printed_amount(amount["text"])
    if actual != Decimal(observation["raw_value"]):
        raise ValueError("P&L source row amount differs from observation")
    if printed_amount(observation["raw_value_text"]) != actual:
        raise ValueError("P&L raw display amount differs from source row")
    if Decimal(observation["unit_scale"]) != 10_000_000 or (
        actual * 10_000_000 != Decimal(observation["normalized_value"])
    ):
        raise ValueError("P&L INR-crore normalization differs")
    return {
        "observation_id": observation["observation_id"],
        "evidence_sha256": digest(observation),
        "source_sha256": observation["source_sha256"],
        "source_page": observation["source_page"],
        "column_role": observation["column_role"],
        "label": label,
        "year_header": header,
        "amount": amount,
        "raw_value": str(actual),
        "normalized_value": observation["normalized_value"],
        "result": "label_row_and_dated_column_match",
        "review_status": "pending",
    }


def audit_pnl_sources(catalog: dict, source_root: Path, observations: list[dict]) -> dict:
    root = source_root.resolve(strict=True)
    by_id = {o["observation_id"]: o for o in catalog["payload"]["observations"]}
    canonical_observations = []
    for original in observations:
        bound = by_id.get(original["observation_id"])
        if bound is None or {k: bound.get(k) for k in original} != original:
            raise ValueError("source observation differs from bound catalog")
        canonical_observations.append(bound)
    sources, checks = [], []
    for source in catalog["payload"]["source_manifest"]:
        path = (root / source["file"]).resolve(strict=True)
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf":
            raise ValueError("source PDF must be inside the supplied root")
        if not 0 < path.stat().st_size <= MAX_PDF_BYTES:
            raise ValueError("source PDF size outside limit")
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if sha != source["sha256"] or len(content) != source["bytes"]:
            raise ValueError("source PDF hash or byte count differs from manifest")
        with fitz.open(stream=content, filetype="pdf") as doc:
            if len(doc) != source["page_count"]:
                raise ValueError("source PDF page count differs from manifest")
            selected = [o for o in canonical_observations if o["source_sha256"] == sha]
            lines_by_page = {}
            for observation in selected:
                page = observation["source_page"]
                if not 1 <= page <= len(doc):
                    raise ValueError("source page outside PDF")
                if page not in lines_by_page:
                    lines_by_page[page] = page_lines(doc[page - 1])
                checks.append(check_pnl_row(lines_by_page[page], observation))
            sources.append(
                {
                    "source_key": source["company_slug"] + ":" + sha,
                    "company_slug": source["company_slug"],
                    "report_fiscal_year": source["report_fiscal_year"],
                    "source_url": source["source_url"],
                    "sha256": sha,
                    "bytes": len(content),
                    "page_count": len(doc),
                    "pnl_rows_checked": len(selected),
                    "result": "pinned_pdf_bytes_and_pages_match",
                    "review_status": "pending",
                }
            )
    if len(checks) != len(observations) or len({c["observation_id"] for c in checks}) != len(
        checks
    ):
        raise ValueError("P&L audit did not cover every observation exactly once")
    return {
        "version": 1,
        "catalog_sha256": catalog["sha256"],
        "method": "PyMuPDF text-line geometry; exact label, dated column and signed amount",
        "digit_glyph_map": "ϬϭϮϯϰϱϲϳϴϵ -> 0123456789; whitespace/grouping removed",
        "sources": sources,
        "pnl_observations": checks,
        "summary": {
            "documents": len(sources),
            "pnl_observations": len(checks),
            "approved_reviews": 0,
            "production_writes": 0,
        },
        "limitations": [
            "Local bytes must be independently authenticated against official retrieval evidence.",
            "Geometry checks corroborate extraction; they do not approve sources, "
            "definitions or series.",
            "No balance-sheet or cash-flow row audit is asserted by this P&L packet.",
            "Conflicts, target inspection and actual review decisions remain separate gates.",
        ],
    }
