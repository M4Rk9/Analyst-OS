"""Source review checks must find the labelled dated row, never any matching number."""

import copy
from pathlib import Path

import pytest
from analyst_os_ingestion.planning import digest
from analyst_os_ingestion.source_review import audit_pnl_sources, check_pnl_row, printed_amount
from scripts.audit_ril_tcs_pnl import decision_packet
from scripts.plan_ril_tcs_load import load_catalog, read_json, review_index

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    def line(text, x, y, right):
        return {"text": text, "bbox": [x, y, right, y + 10]}

    lines = [
        line("2025-26", 400, 40, 450),
        line("2024-25", 500, 40, 550),
        line("Finance Costs", 40, 80, 140),
        line("29", 350, 80, 365),
        line("1,234", 400, 80, 450),
        line("999", 500, 80, 550),
        line("1,234", 400, 150, 450),
    ]
    observation = {
        "observation_id": "TEST ONLY",
        "source_sha256": "a" * 64,
        "source_page": 1,
        "source_label": "Finance Costs",
        "source_fiscal_year": 2026,
        "fiscal_year": 2026,
        "column_role": "current_year",
        "raw_value": "1234",
        "raw_value_text": "1,234",
        "unit_scale": "10000000",
        "normalized_value": "12340000000",
    }
    return lines, observation


def test_source_row_checks_bind_label_column_and_normalization():
    lines, observation = inputs()
    result = check_pnl_row(lines, observation)
    assert result["amount"]["bbox"] == [400, 80, 450, 90]
    assert result["year_header"]["text"] == "2025-26"
    assert result["review_status"] == "pending"
    observation.update(
        fiscal_year=2025,
        column_role="comparative",
        raw_value="999",
        raw_value_text="999",
        normalized_value="9990000000",
    )
    assert check_pnl_row(lines, observation)["raw_value"] == "999"


@pytest.mark.parametrize(
    "change",
    [
        "wrong_row",
        "wrong_column",
        "wrong_year",
        "duplicate",
        "missing_label",
        "scale",
        "normalization",
        "sign",
    ],
)
def test_page_wide_matches_and_changed_metadata_cannot_pass(change):
    lines, observation = inputs()
    if change == "wrong_row":
        lines[4]["text"] = "888"
    elif change == "wrong_column":
        lines[4]["text"], lines[5]["text"] = lines[5]["text"], lines[4]["text"]
    elif change == "wrong_year":
        observation["fiscal_year"] = 2025
    elif change == "duplicate":
        lines.append(copy.deepcopy(lines[4]))
    elif change == "missing_label":
        lines[2]["text"] = "Unrelated label"
    elif change == "scale":
        observation["unit_scale"] = "1"
    elif change == "normalization":
        observation["normalized_value"] = "1"
    else:
        lines[4]["text"] = "(1,234)"
    with pytest.raises(ValueError):
        check_pnl_row(lines, observation)


@pytest.mark.parametrize("text", ["-", "-*", "1,234*", "1,234#", "NaN", "Infinity"])
def test_nonexplicit_or_footnoted_numbers_are_unavailable(text):
    assert printed_amount(text) is None


def test_digit_glyph_and_spacing_cleanup_is_exact():
    assert printed_amount("(2, 55, 32ϰ)") == -255324


def test_committed_packet_and_audit_bind_current_evidence_without_approval():
    catalog = load_catalog(ROOT)
    directory = ROOT / "data/m2/ril-tcs/review"
    audit = read_json(directory / "pnl_source_audit.json")
    retrieval = read_json(directory / "official_retrieval_receipt.json")
    assert audit["catalog_sha256"] == catalog["sha256"]
    assert read_json(directory / "catalog_index.json") == review_index(catalog)
    assert len(audit["pnl_observations"]) == 120
    observations = [
        o
        for o in catalog["payload"]["observations"]
        if o["metric_code"]
        in {
            "revenue",
            "other_income",
            "total_income",
            "finance_costs",
            "total_expenses",
            "profit_for_year",
        }
    ]
    assert {r["observation_id"]: r["evidence_sha256"] for r in audit["pnl_observations"]} == {
        o["observation_id"]: digest(o) for o in observations
    }
    manifest = catalog["payload"]["source_manifest"]
    assert len(retrieval["retrievals"]) == len(manifest) == 10
    for source, fetched in zip(manifest, retrieval["retrievals"], strict=True):
        assert (source["sha256"], source["bytes"], source["page_count"], source["source_url"]) == (
            fetched["sha256"],
            fetched["bytes"],
            fetched["page_count"],
            fetched["source_url"],
        )
    assert decision_packet(catalog, audit) == (directory / "PNL_DECISION_PACKET.md").read_text()
    assert audit["summary"]["approved_reviews"] == 0
    assert all(r["review_status"] == "pending" for r in audit["pnl_observations"])
    ledger = read_json(directory / "review_template.json")
    assert all(
        r["status"] == "pending" for r in [*ledger["sources"].values(), *ledger["facts"].values()]
    )


def test_different_catalog_cannot_reuse_decision_packet():
    catalog = load_catalog(ROOT)
    audit = read_json(ROOT / "data/m2/ril-tcs/review/pnl_source_audit.json")
    audit["catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="different catalog"):
        decision_packet(catalog, audit)


@pytest.mark.parametrize("change", ["amount", "drop", "duplicate"])
def test_altered_audit_cannot_generate_a_decision_packet(change):
    catalog = load_catalog(ROOT)
    audit = read_json(ROOT / "data/m2/ril-tcs/review/pnl_source_audit.json")
    if change == "amount":
        audit["pnl_observations"][0]["raw_value"] = "1"
    elif change == "drop":
        audit["pnl_observations"].pop()
    else:
        audit["pnl_observations"].append(copy.deepcopy(audit["pnl_observations"][0]))
    with pytest.raises(ValueError, match="audit"):
        decision_packet(catalog, audit)


def test_changed_pdf_bytes_cannot_be_audited(tmp_path):
    catalog = load_catalog(ROOT)
    source = catalog["payload"]["source_manifest"][0]
    (tmp_path / source["file"]).write_bytes(b"TEST ONLY wrong PDF bytes")
    observations = read_json(ROOT / "data/m2/ril-tcs/batch1/observations.json")
    with pytest.raises(ValueError, match="hash or byte count"):
        audit_pnl_sources(catalog, tmp_path, observations)


def test_altered_observation_is_rejected_before_pdf_inspection(tmp_path):
    catalog = load_catalog(ROOT)
    observations = read_json(ROOT / "data/m2/ril-tcs/batch1/observations.json")
    observations[0]["source_label"] = "Unrelated label"
    with pytest.raises(ValueError, match="differs from bound catalog"):
        audit_pnl_sources(catalog, tmp_path, observations)
