"""Create both approved M2 native previews; no apply mode or financial writer."""

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from analyst_os_ingestion.planning import ReviewLedger, build_load_plan, digest
from analyst_os_ingestion.publishing import prepare_request, preview
from analyst_os_ingestion.snapshot import (
    SnapshotError,
    collect_snapshot,
    connection_parameters,
    write_snapshot,
)
from scripts.plan_ril_tcs_load import load_catalog, read_json
from scripts.plan_universe_history import load_catalog as load_universe

PROJECT = "swahxcccptpfxwvhgfxz"


def write_private(path, payload):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def prepare_packet(connection, catalog, reviews, project_ref):
    scope = sorted({e["observation"]["company_slug"] for e in catalog["candidates"]})
    target = collect_snapshot(connection, project_ref=project_ref, scope=scope)
    plan = build_load_plan(catalog, reviews, target=target, expected_project_ref=project_ref)
    request = prepare_request(catalog, reviews, target, plan,
                              expected_plan_sha256=digest(plan), project_ref=project_ref)
    native = preview(connection, request)
    return target, plan, native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    try:
        url = os.environ.get("ANALYST_OS_DATABASE_URL") or getpass(
            "PostgreSQL connection URL (hidden): "
        )
        params = connection_parameters(url, PROJECT, args.ssl_root_cert)
        del url
        # A new directory prevents old snapshots/previews from being mistaken for this run.
        args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        import psycopg
        from psycopg.rows import dict_row

        summary = {"project_ref": PROJECT, "production_writes": 0, "packets": {}}
        with psycopg.connect(**params, autocommit=True, prepare_threshold=None,
                             row_factory=dict_row) as connection:
            for name, loader, relative in [
                ("ril-tcs", load_catalog, "data/m2/ril-tcs/review"),
                ("universe", load_universe, "data/m2/universe"),
            ]:
                reviews = ReviewLedger.model_validate(
                    read_json(repo / relative / "marky_approved_reviews.json")
                )
                target, plan, native = prepare_packet(connection, loader(repo), reviews, PROJECT)
                write_snapshot(target, args.output_dir / f"{name}.target-snapshot.json")
                write_private(args.output_dir / f"{name}.load-plan.json", plan)
                write_private(args.output_dir / f"{name}.native-preview.json", native)
                summary["packets"][name] = {
                    **plan["summary"], "plan_sha256": digest(plan),
                    "schema_sha256": native["schema_sha256"],
                    "review_ledger_sha256": digest(reviews.model_dump(mode="json")),
                }
        write_private(args.output_dir / "preview-summary.json", summary)
        print(json.dumps(summary, indent=2))
    except SnapshotError as error:
        print(f"Preview stopped: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("Preview failed. Check TLS, credentials, schema and use a new output directory. "
              "Partial files are not a completed preview; no load was performed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
