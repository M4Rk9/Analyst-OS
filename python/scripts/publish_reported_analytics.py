"""Native TLS-only reported analytics publisher. Default: read-only dry run."""

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from analyst_os_analytics.preview import build_analytics_preview
from analyst_os_analytics.publishing import inspect_receipt, prepare_request, preview, publish
from analyst_os_ingestion.planning import ReviewLedger, TargetSnapshot, digest
from analyst_os_ingestion.snapshot import SnapshotError, collect_snapshot, connection_parameters
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as universe_catalog
from scripts.preview_approved_history import PROJECT, write_private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--receipt-import-id", help="Read-only durable receipt recovery")
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--expected-preview-sha256")
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--expected-schema-sha256")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    try:
        if args.apply and args.receipt_import_id:
            raise SnapshotError("receipt inspection cannot apply changes")
        if args.apply and not all(
            (
                args.preview_dir,
                args.expected_preview_sha256,
                args.expected_plan_sha256,
                args.expected_schema_sha256,
            )
        ):
            raise SnapshotError(
                "apply requires the reviewed preview directory and all three hashes"
            )
        output = args.output_dir.resolve()
        if output.is_relative_to(repo / "web") or output.is_relative_to(repo / "data/m2"):
            raise SnapshotError(
                "private publication artifacts cannot be written to public/pinned data"
            )
        packets = [
            (loader(repo), ReviewLedger.model_validate(read_json(repo / path)))
            for loader, path in (
                (load_catalog, "data/m2/ril-tcs/review/marky_approved_reviews.json"),
                (universe_catalog, "data/m2/universe/marky_approved_reviews.json"),
            )
        ]
        scope = sorted(
            {o["company_slug"] for c, _ in packets for o in c["payload"]["observations"]}
        )
        url = os.environ.get("ANALYST_OS_DATABASE_URL") or getpass(
            "Complete PostgreSQL connection URL (hidden): "
        )
        params = connection_parameters(url, PROJECT, args.ssl_root_cert)
        del url
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(
            **params, autocommit=True, prepare_threshold=None, row_factory=dict_row
        ) as connection:
            if args.receipt_import_id:
                result = inspect_receipt(connection, args.receipt_import_id, project_ref=PROJECT)
                write_private(output / "analytics.receipt.json", result)
                summary = {
                    "mode": "receipt_inspection",
                    "production_writes": 0,
                    "verified": result["verified"],
                    "receipt_sha256": result["receipt_sha256"],
                }
            elif args.apply:
                target = TargetSnapshot.model_validate(
                    read_json(args.preview_dir / "analytics.target-snapshot.json")
                )
                reviewed = read_json(args.preview_dir / "analytics.preview.json")
                request = prepare_request(
                    packets,
                    target,
                    reviewed,
                    project_ref=PROJECT,
                    expected_preview_sha256=args.expected_preview_sha256,
                )
                result = publish(
                    connection,
                    request,
                    read_json(args.preview_dir / "analytics.plan.json"),
                    expected_plan_sha256=args.expected_plan_sha256,
                    expected_schema_sha256=args.expected_schema_sha256,
                )
                write_private(output / "analytics.receipt.json", result)
                summary = {
                    "mode": "apply",
                    "replayed": result["replayed"],
                    "receipt_sha256": result["receipt_sha256"],
                    "import_id": result["receipt"]["import_id"],
                    "inserted_metrics": len(result["receipt"]["inserted_metrics"]),
                    "inserted_flags": len(result["receipt"]["inserted_flags"]),
                    "unavailable": result["receipt"]["unavailable"],
                }
            else:
                target = collect_snapshot(connection, project_ref=PROJECT, scope=scope)
                reviewed = build_analytics_preview(packets, target, project_ref=PROJECT)
                request = prepare_request(
                    packets,
                    target,
                    reviewed,
                    project_ref=PROJECT,
                    expected_preview_sha256=digest(reviewed),
                )
                plan, inventory = preview(connection, request)
                for filename, payload in (
                    ("analytics.target-snapshot.json", target.model_dump(mode="json")),
                    ("analytics.preview.json", reviewed),
                    ("analytics.plan.json", plan),
                    ("analytics.schema-inventory.json", inventory),
                ):
                    write_private(output / filename, payload)
                summary = {
                    "mode": "dry_run",
                    "production_writes": 0,
                    "available": plan["available"],
                    "unavailable": plan["unavailable"],
                    "metrics_to_insert": len(plan["metrics_to_insert"]),
                    "flags_to_insert": len(plan["flags_to_insert"]),
                    "preview_sha256": digest(reviewed),
                    "plan_sha256": digest(plan),
                    "schema_sha256": plan["schema_sha256"],
                    "request_sha256": request["request_sha256"],
                }
        write_private(output / "analytics.summary.json", summary)
        print(json.dumps(summary, indent=2))
    except SnapshotError as error:
        print(f"Analytics publication stopped: {error}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "Analytics publication failed; retain artifacts and inspect the durable receipt "
            "before retry. "
            "Check the connection, TLS, migrations and use a new output directory.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
