"""Validate a controlled local CSV without writing anything to production."""

import argparse
from pathlib import Path

from analyst_os_ingestion import IngestionValidationError, load_financial_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="CSV path relative to --root")
    parser.add_argument("--root", required=True, help="Trusted local ingestion root")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        records = load_financial_csv(args.csv, allowed_root=Path(args.root))
    except IngestionValidationError as exc:
        print(f"Validation failed: {exc}")
        return 1

    companies = {record.company_slug for record in records}
    periods = {(record.company_slug, record.period_end) for record in records}
    summary = (
        f"Validated {len(records)} facts across {len(companies)} companies / "
        f"{len(periods)} periods."
    )
    print(summary)
    print("No database writes were performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
