"""Financial evidence must bind its section, date, sign and explicit display."""

import copy
from pathlib import Path

import pytest
from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.statement_review import check_statement_row
from scripts.audit_ril_tcs_statements import statement_packet
from scripts.plan_ril_tcs_load import load_catalog, read_json

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    def line(text, x, y, right):
        return {"text": text, "bbox": [x, y, right, y + 10]}

    lines = [
        line("March 31, 2026", 400, 20, 450),
        line("March 31, 2025", 500, 20, 550),
        line("Non-current liabilities", 40, 40, 160),
        line("Borrowings", 40, 60, 130),
        line("1,234", 400, 60, 450),
        line("999", 500, 60, 550),
        line("Current liabilities", 40, 90, 160),
        line("Borrowings", 40, 110, 130),
        line("456", 400, 110, 450),
        line("789", 500, 110, 550),
    ]
    observation = {
        "observation_id": "TEST ONLY", "company_slug": "tcs",
        "metric_code": "noncurrent_borrowings", "source_sha256": "a" * 64,
        "source_page": 1, "source_label": "Non-current liabilities Borrowings",
        "source_fiscal_year": 2026, "fiscal_year": 2026, "column_role": "current_year",
        "raw_value": "1234", "raw_value_text": "1,234", "unit_scale": "10000000",
        "normalized_value": "12340000000", "reporting_basis": "consolidated",
        "measurement_type": "instant", "as_of": "2026-03-31",
    }
    return lines, observation


def test_repeated_borrowings_resolve_to_statement_section():
    lines, observation = inputs()
    result = check_statement_row(lines, observation)
    assert result["section"]["text"] == "Non-current liabilities"
    assert result["amount"]["text"] == "1,234"
    observation.update(metric_code="current_borrowings", raw_value="456", raw_value_text="456",
                       normalized_value="4560000000")
    assert check_statement_row(lines, observation)["amount"]["text"] == "456"


@pytest.mark.parametrize("change", ["date", "basis", "sign", "duplicate", "dash", "section"])
def test_unverifiable_statement_rows_remain_unavailable(change):
    lines, observation = inputs()
    if change == "date":
        observation["as_of"] = "2025-03-31"
    elif change == "basis":
        observation["reporting_basis"] = "standalone"
    elif change == "sign":
        lines[4]["text"] = "(1,234)"
    elif change == "duplicate":
        lines.append(copy.deepcopy(lines[4]))
    elif change == "dash":
        lines[4]["text"] = "-"
    else:
        lines[2]["text"] = "Current liabilities"
    with pytest.raises(ValueError):
        check_statement_row(lines, observation)


def test_real_statement_packet_binds_all_checks_and_keeps_two_dashes_unavailable():
    catalog = load_catalog(ROOT)
    path = ROOT / "data/m2/ril-tcs/review"
    audit = read_json(path / "bs_cf_source_audit.json")
    assert audit["catalog_sha256"] == catalog["sha256"]
    assert audit["summary"]["corroborated_candidates"] == 318
    assert audit["summary"]["unavailable_candidates"] == 2
    assert audit["summary"]["approved_reviews"] == 0
    assert statement_packet(catalog, audit) == (path / "BS_CF_DECISION_PACKET.md").read_text()
    observations = {o["observation_id"]: o for o in catalog["payload"]["observations"]}
    for check in audit["statement_observations"]:
        assert check["evidence_sha256"] == digest(observations[check["observation_id"]])


def test_modified_statement_audit_cannot_generate_packet():
    catalog = load_catalog(ROOT)
    audit = read_json(ROOT / "data/m2/ril-tcs/review/bs_cf_source_audit.json")
    audit["catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        statement_packet(catalog, audit)
