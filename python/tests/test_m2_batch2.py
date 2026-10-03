"""Keep real evidence selection and cash reconciliations from silently regressing."""

import csv
import json
import shutil
from pathlib import Path

import pytest
from analyst_os_ingestion.conflicts import assert_no_conflicts
from analyst_os_ingestion.loader import load_financial_csv
from scripts.validate_m2_batch2 import validate_batch

BATCH = Path(__file__).resolve().parents[2] / "data/m2/ril-tcs/batch2"


def test_real_batch_reconciles_and_candidates_exclude_all_conflicts() -> None:
    receipt, checks = validate_batch(BATCH)
    assert receipt == json.loads((BATCH / "validation_receipt.json").read_text())
    assert checks == json.loads((BATCH / "reconciliation_ledger.json").read_text())
    assert receipt["accounting_identity_checks"] == 138
    assert receipt["conflicting_keys"] == 2
    first = load_financial_csv(
        "candidate_facts_validation_only.csv", allowed_root=BATCH.parent / "batch1"
    )
    second = load_financial_csv("candidate_facts_validation_only.csv", allowed_root=BATCH)
    assert len(first + second) == 376
    assert_no_conflicts(first + second)


@pytest.mark.parametrize("mutation", ["conflicting_candidate", "changed_source", "broken_cash"])
def test_evidence_checker_rejects_unsafe_changes(tmp_path: Path, mutation: str) -> None:
    batch = tmp_path / "batch2"
    shutil.copytree(BATCH, batch)
    first = tmp_path / "batch1"
    first.mkdir()
    shutil.copyfile(BATCH.parent / "batch1/source_manifest.json", first / "source_manifest.json")
    observations_path = batch / "observations.json"
    observations = json.loads(observations_path.read_text())
    if mutation == "conflicting_candidate":
        path = batch / "candidate_facts_validation_only.csv"
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        excluded = next(
            o
            for o in observations
            if o["company_slug"] == "reliance-industries"
            and o["fiscal_year"] == 2024
            and o["metric_code"] == "cash_change"
            and o["column_role"] == "current_year"
        )
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows([*rows, excluded])
        expected = "Candidate row count mismatch"
    elif mutation == "changed_source":
        observations[0]["source_sha256"] = "0" * 64
        observations_path.write_text(json.dumps(observations))
        expected = "Source hash mismatch"
    else:
        # Corrupt a comparative which never enters the candidate CSV. Its cash
        # source value must still be validated, rather than checking candidates alone.
        o = next(
            o
            for o in observations
            if o["company_slug"] == "tcs"
            and o["source_fiscal_year"] == 2022
            and o["fiscal_year"] == 2021
            and o["metric_code"] == "closing_cash"
        )
        o["raw_value"] = "6859"
        o["normalized_value"] = "68590000000"
        observations_path.write_text(json.dumps(observations))
        expected = "Raw source value mismatch"
    with pytest.raises(ValueError, match=expected):
        validate_batch(batch)
