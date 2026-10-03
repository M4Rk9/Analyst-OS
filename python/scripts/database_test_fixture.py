"""Emit real candidate evidence with TEST-ONLY attestations for an ephemeral DB.

Never writes a review ledger, connects to a target, or loads production data.
"""

import json
from pathlib import Path

from analyst_os_ingestion.planning import digest
from scripts.plan_ril_tcs_load import load_catalog


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fixture() -> dict:
    catalog = load_catalog(Path(__file__).resolve().parents[2])
    approval = {
        "status": "approved",
        "reviewer": "TEST ONLY — not a human review",
        "reviewed_at": "2020-01-01T00:00:00Z",
        "rationale": "Synthetic attestation for an ephemeral database test only.",
    }
    ledger = {
        "catalog_sha256": catalog["sha256"],
        "sources": {},
        "facts": {},
    }
    entries = catalog["candidates"] + catalog["withheld"]
    for entry in entries:
        ledger["sources"][entry["source_key"]] = approval
        ledger["facts"][entry["observation"]["observation_id"]] = approval
    return {
        "catalog_sha256": catalog["sha256"],
        "catalog_canonical_json": canonical(catalog["payload"]),
        "review_ledger_sha256": digest(ledger),
        "review_canonical_json": canonical(ledger),
        "entries": [
            {
                **entry,
                "evidence_canonical_json": canonical(entry["observation"]),
                "definition_canonical_json": canonical(entry["definition"]),
            }
            for entry in entries
        ],
        "candidate_count": len(catalog["candidates"]),
    }


if __name__ == "__main__":
    print(json.dumps(fixture(), ensure_ascii=False))
