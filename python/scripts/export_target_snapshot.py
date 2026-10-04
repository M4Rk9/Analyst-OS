"""Read-only privileged snapshot CLI. Credentials are accepted only via environment."""

import argparse
import os
import sys
from pathlib import Path

from analyst_os_ingestion.snapshot import (
    DEFAULT_SCOPE,
    SnapshotError,
    collect_snapshot,
    connection_parameters,
    write_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-project-ref", required=True)
    parser.add_argument("--ssl-root-cert", type=Path, required=True)
    parser.add_argument("--companies", nargs="+", default=list(DEFAULT_SCOPE))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        params = connection_parameters(
            os.environ.get("ANALYST_OS_DATABASE_URL", ""),
            args.expected_project_ref, args.ssl_root_cert,
        )
        # Optional driver is imported only for explicit live export.
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(**params, autocommit=True, prepare_threshold=None,
                             row_factory=dict_row) as connection:
            snapshot = collect_snapshot(connection, project_ref=args.expected_project_ref,
                                        scope=args.companies)
        sha = write_snapshot(snapshot, args.output)
    except SnapshotError as error:
        print(f"Snapshot export stopped: {error}", file=sys.stderr)
        return 1
    except Exception:
        # Server/driver errors may embed connection details. Never print them or tracebacks.
        print("Snapshot export failed; check credentials, TLS, privileges and provenance locally.",
              file=sys.stderr)
        return 1
    print(f"Snapshot created: {len(snapshot.sources)} sources, "
          f"{len(snapshot.facts)} facts; sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
