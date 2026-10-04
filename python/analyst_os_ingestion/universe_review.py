"""Conservative extraction of explicitly configured consolidated statement rows.

This is evidence preparation only. Unknown labels, dates, dashes and ambiguous
columns become gaps. No source or observation can approve itself.
"""

import hashlib
from pathlib import Path

import fitz

from .planning import build_catalog, digest
from .source_review import compact_label, page_lines, printed_amount

MAX_SOURCE_BYTES = 60_000_000


def extract_row(lines, labels, year, *, occurrence=None, section=None):
    """Bind exact labels to date headers and amounts; never search by expected value."""
    targets = {compact_label(label) for label in labels}
    matches = [line for line in lines if compact_label(line["text"]) in targets]
    if section:
        supported = []
        headings = {compact_label(s).replace("-", "") for s in section["headings"]}
        expected = compact_label(section["expected"]).replace("-", "")
        for line in matches:
            above = [
                h for h in lines
                if compact_label(h["text"]).replace("-", "") in headings
                and h["bbox"][3] < line["bbox"][1] + 2
            ]
            if above and compact_label(max(above, key=lambda h: h["bbox"][1])["text"]).replace(
                "-", ""
            ) == expected:
                supported.append(line)
        matches = supported
    matches.sort(key=lambda line: (line["bbox"][1], line["bbox"][0]))
    if occurrence is not None:
        matches = matches[occurrence:occurrence + 1]
    if len(matches) != 1:
        raise ValueError("exact statement label missing or ambiguous")
    label = matches[0]
    headers = []
    for column_year in [year, year - 1]:
        dates = {
            f"march31,{column_year}", f"march31,{column_year}*",
            f"asat31-3-{column_year}", f"{column_year - 1}-{str(column_year)[-2:]}",
        }
        # Some Tata cash-flow pages print a shared full date above bare years.
        if any(
            compact_label(line["text"]) == "yearendedmarch31,"
            and line["bbox"][3] < label["bbox"][1]
            for line in lines
        ):
            dates.add(str(column_year))
        options = [
            line for line in lines
            if compact_label(line["text"]) in dates
            and line["bbox"][0] > label["bbox"][2]
            and line["bbox"][3] < label["bbox"][1] + 2
        ]
        if not options:
            raise ValueError("dated column header unavailable")
        headers.append(min(options, key=lambda line: line["bbox"][0]))
    if headers[0]["bbox"][0] >= headers[1]["bbox"][0]:
        raise ValueError("unsupported column order")
    values = []
    for slot in range(2):
        candidates = [
            line for line in lines
            if line["bbox"][0] > label["bbox"][2]
            and abs(line["bbox"][3] - label["bbox"][3]) < 2
            and abs(line["bbox"][2] - headers[slot]["bbox"][2]) < 35
            and abs(line["bbox"][2] - headers[slot]["bbox"][2])
            < abs(line["bbox"][2] - headers[1 - slot]["bbox"][2])
        ]
        if len(candidates) != 1 or printed_amount(candidates[0]["text"]) is None:
            raise ValueError("explicit numeric amount missing or ambiguous")
        values.append({"label": label, "header": headers[slot], "amount": candidates[0]})
    return values


def extract_history(source_root: Path, manifest: list, configuration: dict) -> dict:
    root = source_root.resolve(strict=True)
    observations, evidence, gaps, definitions = [], [], [], {}
    source_checks = []
    for source in manifest:
        path = (root / source["file"]).resolve(strict=True)
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf":
            raise ValueError("source must be a PDF inside source root")
        if not 0 < path.stat().st_size <= MAX_SOURCE_BYTES:
            raise ValueError("source PDF exceeds bounded evidence-preparation limit")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError("source PDF hash mismatch")
        if len(content) != source["bytes"]:
            raise ValueError("source PDF byte count mismatch")
        company, year = source["company_slug"], source["report_fiscal_year"]
        settings = configuration[company]
        with fitz.open(stream=content, filetype="pdf") as document:
            if len(document) != source["page_count"]:
                raise ValueError("source PDF page count mismatch")
            pages = {}
            for metric in settings["metrics"]:
                code = metric["metric_code"]
                definition = {
                    "metric_code": code, "measurement_type": metric["measurement_type"],
                    "definition": metric["definition"], "currency": "INR",
                    "unit": "crore", "unit_scale": "10000000",
                }
                if code in definitions and definitions[code] != definition:
                    raise ValueError("competing metric definition")
                definitions[code] = definition
                results = []
                errors = []
                for page in settings["pages"][str(year)][metric["statement"]]:
                    if not 1 <= page <= len(document):
                        raise ValueError("statement page outside PDF")
                    if page not in pages:
                        text = document[page - 1].get_text()
                        # Unit verification is explicit and precedes normalization.
                        if "crore" not in text.lower():
                            raise ValueError("configured statement page has no crore unit")
                        pages[page] = page_lines(document[page - 1])
                    try:
                        rows = extract_row(
                            pages[page], metric["labels"], year,
                            occurrence=metric.get("occurrence"), section=metric.get("section"),
                        )
                        results.append((page, rows))
                    except ValueError as error:
                        errors.append({"page": page, "reason": str(error)})
                if len(results) != 1:
                    gaps.append({
                        "company_slug": company, "fiscal_year": year, "metric_code": code,
                        "source_sha256": source["sha256"], "reasons": errors,
                        "status": "unavailable", "ambiguous_matches": len(results),
                    })
                    continue
                page, rows = results[0]
                for slot, row in enumerate(rows):
                    fiscal_year = year - slot
                    raw = printed_amount(row["amount"]["text"])
                    observation = {
                        "observation_id": f"{company}:{fiscal_year}:{code}:report{year}",
                        "company_slug": company, "period_type": "FY", "fiscal_year": fiscal_year,
                        "period_start": f"{fiscal_year - 1}-04-01",
                        "period_end": f"{fiscal_year}-03-31", "currency": "INR",
                        "metric_code": code, "raw_value": str(raw),
                        "raw_value_text": row["amount"]["text"].strip(),
                        "unit_scale": "10000000", "normalized_value": str(raw * 10_000_000),
                        "source_title": source["title"], "source_document_type": "annual_report",
                        "source_url": source["source_url"], "source_publisher": source["publisher"],
                        "source_fiscal_year": year, "source_sha256": source["sha256"],
                        "source_page": page, "source_label": row["label"]["text"].strip(),
                        "reporting_basis": "consolidated",
                        "measurement_type": metric["measurement_type"],
                        "as_of": f"{fiscal_year}-03-31" if metric["measurement_type"] == "instant"
                        else None, "column_role": "current_year" if slot == 0 else "comparative",
                        "quality_status": "unverified", "is_preferred": False,
                        "scope_note": source["scope_note"],
                    }
                    observations.append(observation)
                    evidence.append({
                        "observation_id": observation["observation_id"],
                        "evidence_sha256": digest(observation), "source_page": page, **row,
                        "review_status": "pending",
                    })
        source_checks.append({
            "company_slug": company, "report_fiscal_year": year, "sha256": source["sha256"],
            "bytes": source["bytes"], "page_count": source["page_count"],
            "result": "pinned_bytes_hash_and_page_count_match", "review_status": "pending",
        })
    catalog = build_catalog(observations, definitions, manifest, set(range(2022, 2027)))
    return {
        "version": 1, "manifest": manifest, "definitions": definitions,
        "observations": observations, "row_evidence": evidence, "gaps": gaps,
        "source_checks": source_checks, "catalog_sha256": catalog["sha256"],
        "summary": {
            "sources": len(manifest), "observations": len(observations),
            "candidates": len(catalog["candidates"]), "withheld": len(catalog["withheld"]),
            "conflicting_keys": catalog["conflicting_keys"], "unavailable_fields": len(gaps),
            "approved_reviews": 0, "production_writes": 0,
        },
    }
