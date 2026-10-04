"""Reproduce the pending three-company evidence from pinned local PDF files."""

import argparse
import json
from pathlib import Path

from analyst_os_ingestion.universe_review import extract_history
from scripts.plan_ril_tcs_load import read_json
from scripts.plan_universe_history import reconciliations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    directory = repo / "data/m2/universe"
    output = args.output_dir.resolve(strict=True)
    if output.is_relative_to(args.source_root.resolve()) or output.is_relative_to(directory):
        raise ValueError("audit output cannot replace pinned source or committed evidence")
    result = extract_history(args.source_root, read_json(directory / "source_manifest.json"),
                             read_json(directory / "extraction_configuration.json"))
    checks = reconciliations(result["observations"])
    for name, value in [("history_evidence.json", result), ("reconciliation_ledger.json", checks)]:
        (output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog_sha256": result["catalog_sha256"], **result["summary"]}))


if __name__ == "__main__":
    main()
