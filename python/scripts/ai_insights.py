"""Generate local drafts, preview exact reviewer selections, or publish with pinned hashes."""

import argparse
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from getpass import getpass
from pathlib import Path

from analyst_os_ai.chunking import DocumentChunk
from analyst_os_ai.extractor import extract_pdf_pages, resolve_safe_pdf
from analyst_os_ai.ollama import model_digest
from analyst_os_ai.pipeline import generate_insights
from analyst_os_ai.publishing import (
    begin,
    contract,
    inspect_receipt,
    preview,
    publish,
    source_record,
)
from analyst_os_ai.review import checked_draft, review_template
from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.snapshot import SnapshotError, connection_parameters
from scripts.preview_approved_history import PROJECT, write_private


def read_json(path):
    if path.stat().st_size > 2 * 1024 * 1024:
        raise SnapshotError("AI artifact exceeds size bound")
    return json.loads(path.read_text(encoding="utf-8"))


def output_root(path):
    root = path.resolve()
    repo = Path(__file__).resolve().parents[2]
    if root.is_relative_to(repo):
        raise SnapshotError("AI drafts, reviews and receipts must be outside the repository")
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    return root


def connect(args):
    import psycopg
    from psycopg.rows import dict_row

    url = os.environ.get("ANALYST_OS_DATABASE_URL") or getpass("PostgreSQL URL (hidden): ")
    params = connection_parameters(url, PROJECT, args.ssl_root_cert)
    return psycopg.connect(**params, autocommit=True, prepare_threshold=None, row_factory=dict_row)


@contextmanager
def session(args):
    connection = connect(args)
    try:
        yield connection
    finally:
        # Cleanup failure cannot erase a confirmed commit or its recovery ID.
        try:
            connection.close()
        except Exception:
            print(
                "Database connection cleanup failed; preserve the receipt or recovery ID.",
                file=sys.stderr,
            )


def generate(args):
    # Close the privileged connection before the model receives source text.
    with session(args) as db:
        begin(db)
        source = source_record(db, args.source_document_id)
        db.rollback()
    path = resolve_safe_pdf(args.pdf, allowed_root=args.pdf_root, max_bytes=100 * 1024 * 1024)
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise SnapshotError("local PDF does not match the approved source hash")
    selected = {int(p) for p in args.pages.split(",")}
    if not 1 <= len(selected) <= 10 or min(selected) < 1 or max(selected) > source["page_count"]:
        raise SnapshotError("select 1-10 physical PDF page numbers within the pinned source")
    pages = [
        p
        for p in extract_pdf_pages(
            path, allowed_root=args.pdf_root, max_bytes=100 * 1024 * 1024, max_pages=1500
        )
        if p.page in selected
    ]
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise SnapshotError("PDF changed during extraction")
    if {p.page for p in pages} != selected or sum(len(p.text) for p in pages) > 40_000:
        raise SnapshotError("selected pages are empty or exceed context bound")
    before = model_digest(args.model)
    bundle = generate_insights(
        company_slug=source["company_slug"],
        source_url=source["source_url"],
        chunks=[DocumentChunk(p.page, p.text) for p in pages],
        model=args.model,
    )
    if model_digest(args.model) != before:
        raise SnapshotError("local model changed during generation")
    payload = checked_draft(
        {
            "version": 1,
            "source": source,
            "model_digest": before,
            "pages": [{"page": p.page, "text": p.text} for p in pages],
            "bundle": bundle.model_dump(mode="json"),
        }
    )
    output = output_root(args.output_dir)
    write_private(output / "ai.draft.json", payload)
    write_private(output / "ai.review.json", review_template(payload))
    return {
        "mode": "draft",
        "production_writes": 0,
        "draft_sha256": digest(payload),
        "candidates": len(payload["bundle"]["insights"]),
        "review_status": "pending",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["generate", "preview", "apply", "receipt"])
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-document-id")
    parser.add_argument("--pdf-root", type=Path)
    parser.add_argument("--pdf")
    parser.add_argument("--pages", help="Comma-separated physical PDF pages, not printed labels")
    parser.add_argument("--model", help="Exact installed Ollama tag, including :tag")
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--expected-schema-sha256")
    parser.add_argument("--receipt-import-id")
    args = parser.parse_args()
    try:
        if args.mode == "generate":
            if not all((args.source_document_id, args.pdf_root, args.pdf, args.pages, args.model)):
                raise SnapshotError("generate requires source id, PDF root/file, pages and model")
            summary = generate(args)
        else:
            output = output_root(args.output_dir)
            with session(args) as db:
                if args.mode == "receipt":
                    if not args.receipt_import_id:
                        raise SnapshotError("receipt requires import id")
                    result = inspect_receipt(db, args.receipt_import_id)
                else:
                    if not args.draft or not args.review:
                        raise SnapshotError("preview/apply require exact draft and review files")
                    payload, sha = contract(read_json(args.draft), read_json(args.review), PROJECT)
                    if args.mode == "preview":
                        plan, schema = preview(db, payload, sha)
                        write_private(output / "ai.plan.json", plan)
                        write_private(output / "ai.schema.json", schema)
                        summary = {
                            "mode": "dry_run",
                            "production_writes": 0,
                            "approved": len(payload["rows"]),
                            "to_insert": len(plan["rows_to_insert"]),
                            "plan_sha256": digest(plan),
                            "schema_sha256": plan["schema_sha256"],
                        }
                        write_private(output / "ai.summary.json", summary)
                        print(json.dumps(summary, indent=2))
                        return 0
                    if not all((args.plan, args.expected_plan_sha256, args.expected_schema_sha256)):
                        raise SnapshotError("apply requires reviewed plan and both pinned hashes")
                    result = publish(
                        db,
                        payload,
                        sha,
                        read_json(args.plan),
                        expected_plan_sha256=args.expected_plan_sha256,
                        expected_schema_sha256=args.expected_schema_sha256,
                    )
                try:
                    write_private(output / "ai.receipt.json", result)
                except Exception:
                    raise SnapshotError(
                        "durable receipt verified; local save failed. Recover "
                        f"import_id={result['receipt']['import_id']}"
                    ) from None
                summary = {
                    "mode": args.mode,
                    "import_id": result["receipt"]["import_id"],
                    "receipt_sha256": result["receipt_sha256"],
                    "insights": len(result["receipt"]["insight_ids"]),
                }
        print(json.dumps(summary, indent=2))
        return 0
    except SnapshotError as error:
        print(f"AI workflow stopped: {error}", file=sys.stderr)
    except Exception:
        print(
            "AI workflow stopped safely. Check local model, source, review, TLS and migrations; "
            "if apply was attempted, recover the durable receipt before retry.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
