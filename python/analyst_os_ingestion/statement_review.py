"""Pinned BS/CF row corroboration; never interpret dashes as zero or create approvals."""

import hashlib
import re
from decimal import Decimal
from pathlib import Path

import fitz

from .planning import digest
from .source_review import MAX_PDF_BYTES, compact_label, page_lines, printed_amount


def statement_label(observation: dict) -> str:
    """Remove known extraction-context prefixes, retaining the actual printed row label."""
    code = observation["metric_code"]
    company = observation["company_slug"]
    label = observation["source_label"]
    if code == "share_capital":
        return "Equity Share Capital" if company == "reliance-industries" else "Share capital"
    if code == "inventory":
        return "Inventories"
    if code in {"noncurrent_borrowings", "current_borrowings"}:
        return "Borrowings"
    if code in {"noncurrent_lease_liabilities", "current_lease_liabilities"}:
        return "Lease liabilities"
    if code.endswith("billed_receivables"):
        return "Unbilled" if "unbilled" in code else "Billed"
    if code == "capex_ppe_intangibles_cash":
        return re.split(r"Activities\s+", label, flags=re.IGNORECASE)[-1]
    if code == "lease_payments_cash":
        return re.split(r"(?:ACTIVITIES|ACTIV ITIES)\s+", label)[-1]
    return label


def _label_rows(lines: list[dict], target: str) -> list[dict]:
    rows = [{"lines": [line], **line} for line in lines if compact_label(line["text"]) == target]
    if rows:
        return rows
    # Wrapped labels must occupy two adjacent lines in the same label column.
    for line in lines:
        prefix = compact_label(line["text"])
        if not prefix or not target.startswith(prefix):
            continue
        for following in lines:
            if (
                abs(following["bbox"][0] - line["bbox"][0]) < 3
                and 0 < following["bbox"][1] - line["bbox"][1] < 14
                and compact_label(line["text"] + following["text"]) == target
            ):
                rows.append({
                    "lines": [line, following],
                    "text": line["text"] + following["text"],
                    "bbox": line["bbox"],
                })
    return rows


def _section_for(lines: list[dict], label: dict, observation: dict) -> dict | None:
    code = observation["metric_code"]
    if not code.startswith(("noncurrent_", "current_")):
        return None
    family = "liabilities" if any(x in code for x in ["borrowings", "liabilities"]) else "assets"
    expected = ("noncurrent" if code.startswith("noncurrent_") else "current") + family
    headings = [
        line for line in lines
        if compact_label(line["text"]).replace("-", "")
        in {"current" + family, "noncurrent" + family}
        and -3 <= label["bbox"][0] - line["bbox"][0] < 90
        and line["bbox"][3] < label["bbox"][1] + 2
    ]
    if not headings:
        # TCS FY2022 current receivables continue in the right-hand pane; its
        # current-assets heading is in the left-hand pane, above the continuation.
        if not (
            observation["company_slug"] == "tcs"
            and observation["source_fiscal_year"] == 2022
            and observation["source_page"] == 243
            and expected == "currentassets"
            and label["bbox"][0] > 350
        ):
            raise ValueError("statement section header missing")
        headings = [
            line for line in lines
            if compact_label(line["text"]).replace("-", "") == expected
        ]
    if not headings:
        raise ValueError("statement section header missing")
    section = max(headings, key=lambda line: line["bbox"][1])
    if compact_label(section["text"]).replace("-", "") != expected:
        raise ValueError("label belongs to a different statement section")
    return section


def check_statement_row(lines: list[dict], observation: dict) -> dict:
    """Select label and dated column without using the expected amount to locate the row."""
    target = compact_label(statement_label(observation))
    labels = _label_rows(lines, target)
    if len(labels) > 1 and observation["metric_code"].startswith(("noncurrent_", "current_")):
        supported = []
        for label in labels:
            try:
                section = _section_for(lines, label, observation)
            except ValueError:
                continue
            supported.append((label, section))
        if len(supported) != 1:
            raise ValueError("statement section does not resolve duplicate label")
        label, section = supported[0]
    else:
        if len(labels) != 1:
            raise ValueError("statement label missing or ambiguous")
        label = labels[0]
        section = _section_for(lines, label, observation)
    headers = []
    report_year = observation["source_fiscal_year"]
    for year in [report_year, report_year - 1]:
        targets = {
            f"31stmarch,{year}", f"march31,{year}", f"31march{year}",
            f"{year - 1}-{str(year)[-2:]}",
        }
        candidates = [
            line for line in lines
            if compact_label(line["text"]) in targets
            and line["bbox"][0] > label["bbox"][2]
            and line["bbox"][3] < label["bbox"][1] + 2
        ]
        if not candidates:
            raise ValueError("dated statement column header missing")
        headers.append(min(candidates, key=lambda line: line["bbox"][0]))
    if headers[0]["bbox"][0] >= headers[1]["bbox"][0]:
        raise ValueError("unsupported statement column order")
    if observation["column_role"] not in {"current_year", "comparative"}:
        raise ValueError("unsupported statement column role")
    slot = 0 if observation["column_role"] == "current_year" else 1
    if observation["fiscal_year"] != report_year - slot:
        raise ValueError("observation differs from dated statement year")
    if observation["reporting_basis"] != "consolidated":
        raise ValueError("unsupported statement basis")
    if observation["measurement_type"] == "instant":
        if observation["as_of"] != f"{observation['fiscal_year']}-03-31":
            raise ValueError("instant measurement date differs")
    elif observation["measurement_type"] != "duration" or observation["as_of"] is not None:
        raise ValueError("unsupported measurement metadata")
    numeric = [
        line for line in lines
        if abs(line["bbox"][3] - label["bbox"][3]) < 2
        and line["bbox"][0] > label["bbox"][2]
        and printed_amount(line["text"]) is not None
        and abs(line["bbox"][2] - headers[slot]["bbox"][2]) < 30
        and abs(line["bbox"][2] - headers[slot]["bbox"][2])
        < abs(line["bbox"][2] - headers[1 - slot]["bbox"][2])
    ]
    if len(numeric) != 1:
        raise ValueError("explicit amount missing or ambiguous in dated label row")
    amount = numeric[0]
    actual = printed_amount(amount["text"])
    if actual != Decimal(observation["raw_value"]):
        raise ValueError("statement row amount differs from observation")
    if printed_amount(observation["raw_value_text"]) != actual:
        raise ValueError("raw display amount is not an explicit matching number")
    if Decimal(observation["unit_scale"]) != 10_000_000 or (
        actual * 10_000_000 != Decimal(observation["normalized_value"])
    ):
        raise ValueError("statement INR-crore normalization differs")
    return {
        "observation_id": observation["observation_id"],
        "evidence_sha256": digest(observation),
        "source_sha256": observation["source_sha256"],
        "source_page": observation["source_page"],
        "column_role": observation["column_role"],
        "label": label, "section": section, "year_header": headers[slot],
        "amount": amount, "raw_value": str(actual),
        "normalized_value": observation["normalized_value"],
        "result": "label_row_and_dated_column_match", "review_status": "pending",
    }


def audit_statement_sources(catalog: dict, source_root: Path, observations: list[dict]) -> dict:
    root = source_root.resolve(strict=True)
    bound = {o["observation_id"]: o for o in catalog["payload"]["observations"]}
    selected = []
    for original in observations:
        canonical = bound.get(original["observation_id"])
        if canonical is None or {k: canonical.get(k) for k in original} != original:
            raise ValueError("statement observation differs from bound catalog")
        selected.append(canonical)
    candidate_ids = {e["observation"]["observation_id"] for e in catalog["candidates"]}
    sources, checks = [], []
    for source in catalog["payload"]["source_manifest"]:
        path = (root / source["file"]).resolve(strict=True)
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf":
            raise ValueError("source PDF lies outside supplied root")
        if not 0 < path.stat().st_size <= MAX_PDF_BYTES:
            raise ValueError("source PDF size outside limit")
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if sha != source["sha256"] or len(content) != source["bytes"]:
            raise ValueError("source PDF hash or byte count differs")
        with fitz.open(stream=content, filetype="pdf") as document:
            if len(document) != source["page_count"]:
                raise ValueError("source PDF page count differs")
            by_page = {}
            scoped = [o for o in selected if o["source_sha256"] == sha]
            for observation in scoped:
                page = observation["source_page"]
                if not 1 <= page <= len(document):
                    raise ValueError("statement page outside source PDF")
                if page not in by_page:
                    by_page[page] = page_lines(document[page - 1])
                try:
                    result = check_statement_row(by_page[page], observation)
                except ValueError as error:
                    result = {
                        "observation_id": observation["observation_id"],
                        "evidence_sha256": digest(observation), "source_sha256": sha,
                        "source_page": page, "result": "unavailable", "reason": str(error),
                        "review_status": "pending",
                    }
                result["candidate"] = observation["observation_id"] in candidate_ids
                checks.append(result)
            sources.append({
                "source_key": source["company_slug"] + ":" + sha, "sha256": sha,
                "bytes": len(content), "page_count": len(document),
                "source_url": source["source_url"], "statement_rows_checked": len(scoped),
                "result": "pinned_pdf_bytes_and_pages_match", "review_status": "pending",
            })
    if len(checks) != len(selected) or len({c["observation_id"] for c in checks}) != len(checks):
        raise ValueError("statement audit scope incomplete or duplicated")
    passing = [c for c in checks if c["result"] == "label_row_and_dated_column_match"]
    return {
        "version": 1, "catalog_sha256": catalog["sha256"],
        "method": "PyMuPDF exact label/section, dated column, signed explicit amount",
        "sources": sources, "statement_observations": checks,
        "summary": {
            "documents": len(sources), "observations_checked": len(checks),
            "corroborated_observations": len(passing),
            "corroborated_candidates": sum(c["candidate"] for c in passing),
            "unavailable_candidates": sum(
                c["candidate"] for c in checks if c["result"] == "unavailable"
            ),
            "approved_reviews": 0, "production_writes": 0,
        },
        "limitations": [
            "Geometry corroboration is not reviewer approval or cross-year comparability.",
            "Known context prefixes and one TCS FY2022 continuation layout are explicit.",
            "Digits use the existing documented Greek-digit map; footnotes/dashes do not pass.",
            "No conflicting key is unwithheld; the original catalog and ledger remain bound.",
        ],
    }
