"""Capture fresh native evidence and preview analytics; no database writer/apply mode."""

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from analyst_os_analytics.preview import build_analytics_preview
from analyst_os_ingestion.planning import ReviewLedger, digest
from analyst_os_ingestion.publishing import schema_inventory
from analyst_os_ingestion.snapshot import (
    SnapshotError,
    collect_snapshot,
    connection_parameters,
    write_snapshot,
)
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as universe_catalog
from scripts.preview_approved_history import PROJECT, write_private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    try:
        output = args.output_dir.resolve()
        if output.is_relative_to(repo / "web") or output.is_relative_to(repo / "data/m2"):
            raise SnapshotError(
                "private analytics artifacts cannot be written to public/pinned data"
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
        args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(
            **params, autocommit=True, prepare_threshold=None, row_factory=dict_row
        ) as connection:
            target = collect_snapshot(connection, project_ref=PROJECT, scope=scope)
            inventory, schema_sha = schema_inventory(connection)
        preview = build_analytics_preview(packets, target, project_ref=PROJECT)
        preview["schema_sha256"] = schema_sha
        write_snapshot(target, args.output_dir / "analytics.target-snapshot.json")
        write_private(args.output_dir / "analytics.preview.json", preview)
        write_private(args.output_dir / "analytics.schema-inventory.json", inventory)
        summary = {
            k: preview[k]
            for k in (
                "mode",
                "production_writes",
                "project_ref",
                "approved_loaded_facts",
                "available",
                "unavailable",
                "schema_sha256",
            )
        }
        summary["preview_sha256"] = digest(preview)
        write_private(args.output_dir / "analytics.summary.json", summary)
        print(json.dumps(summary, indent=2))
    except SnapshotError as error:
        print(f"Analytics preview stopped: {error}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "Analytics preview failed. Check credentials, TLS and use a new output directory. "
            "Partial files are not a completed preview; no database writes occurred.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
