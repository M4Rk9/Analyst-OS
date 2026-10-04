"""Preview reviewed RIL/TCS loads; explicit --apply is the only write path."""

import argparse
import json
import os
import sys
from contextlib import suppress
from pathlib import Path

from analyst_os_ingestion.planning import ReviewLedger, TargetSnapshot
from analyst_os_ingestion.publishing import PublishError, prepare_request, preview, publish
from analyst_os_ingestion.snapshot import connection_parameters
from scripts.plan_ril_tcs_load import load_catalog, read_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--target-snapshot", type=Path, required=True)
    parser.add_argument("--reviewed-plan", type=Path, required=True)
    parser.add_argument("--expected-plan-sha256", required=True)
    parser.add_argument("--expected-project-ref", required=True)
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--expected-schema-sha256")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        request = prepare_request(
            load_catalog(Path(__file__).resolve().parents[2]),
            ReviewLedger.model_validate(read_json(args.reviews)),
            TargetSnapshot.model_validate(read_json(args.target_snapshot)),
            read_json(args.reviewed_plan),
            expected_plan_sha256=args.expected_plan_sha256,
            project_ref=args.expected_project_ref,
        )
        if args.apply and (not args.expected_schema_sha256 or not request["selected"]):
            raise PublishError(
                "apply requires a reviewed schema hash and approved target-ready facts"
            )
        params = connection_parameters(
            os.environ.get("ANALYST_OS_DATABASE_URL", ""),
            args.expected_project_ref,
            args.ssl_root_cert,
        )
        if args.apply:
            params["options"] = "-c default_transaction_read_only=off -c search_path=pg_catalog"
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            **params, autocommit=True, prepare_threshold=None, row_factory=dict_row
        )
        try:
            if args.apply:
                result = publish(
                    connection, request, expected_schema_sha256=args.expected_schema_sha256
                )
            else:
                result = preview(connection, request)
        finally:
            # Preserve uncertain-COMMIT diagnostics instead of an automatic rollback.
            with suppress(Exception):
                connection.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except PublishError as error:
        print(f"Publishing stopped: {error}", file=sys.stderr)
    except Exception:
        print(
            "Publishing failed; inspect credentials, TLS, target schema and evidence locally. "
            "Raw server errors are suppressed.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
