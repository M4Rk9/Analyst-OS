"""Offline, review-bound planning. This module has no database or network writer."""

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from .conflicts import fact_key, find_conflicts
from .loader import _record_from_row
from .models import FinancialFactRecord

SHA = r"^[0-9a-f]{64}$"


def digest(value: object) -> str:
    """Hash canonical JSON, including provenance and definitions, not just amounts."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class Review(BaseModel):
    """An explicit attestation; not an authentication or digital-signature mechanism."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer: str | None = Field(default=None, min_length=1, max_length=160)
    reviewed_at: datetime | None = None
    rationale: str | None = Field(default=None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def require_attestation(self):
        if self.status != "pending":
            if not self.reviewer or not self.reviewed_at or not self.rationale:
                raise ValueError("approved/rejected reviews require reviewer, time and rationale")
        if self.reviewed_at is not None and self.reviewed_at.utcoffset() is None:
            raise ValueError("review time must include a timezone")
        return self


class ReviewLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalog_sha256: str = Field(pattern=SHA)
    sources: dict[str, Review] = Field(default_factory=dict)
    facts: dict[str, Review] = Field(default_factory=dict)


class ExistingFact(BaseModel):
    """Privileged snapshot entry; an anon export would hide relevant conflicts."""

    model_config = ConfigDict(extra="forbid")
    id: UUID
    record: FinancialFactRecord
    normalized_value: Decimal
    reporting_basis: Literal["consolidated", "standalone"]
    measurement_type: Literal["instant", "duration"]
    as_of: str | None
    definition_sha256: str = Field(pattern=SHA)
    quality_status: Literal["verified", "unverified", "conflict"]
    is_preferred: bool

    @model_validator(mode="after")
    def require_stored_normalization(self):
        if (
            not self.normalized_value.is_finite()
            or self.normalized_value != self.record.normalized_value
        ):
            raise ValueError("target stored normalization mismatch")
        return self


class ExistingSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_slug: str
    source_url: HttpUrl
    sha256: str = Field(pattern=SHA)
    verification_status: Literal["pending", "verified", "rejected", "conflict"]

    @field_validator("source_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("target source URL must use HTTPS")
        return value


class TargetSnapshot(BaseModel):
    """Completeness is attested by the trusted exporter, not established by this planner."""

    model_config = ConfigDict(extra="forbid")
    project_ref: str = Field(pattern=r"^[a-z0-9]{20}$")
    captured_at: datetime
    complete: Literal[True]
    company_slugs: list[str] = Field(min_length=1)
    sources: list[ExistingSource]
    facts: list[ExistingFact]

    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.captured_at.utcoffset() is None:
            raise ValueError("snapshot time must include a timezone")
        if len(self.company_slugs) != len(set(self.company_slugs)):
            raise ValueError("duplicate snapshot scope")
        keys = [(s.company_slug, str(s.source_url)) for s in self.sources]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate target source URL")
        ids = [f.id for f in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate target fact ID")
        natural_keys = [(fact_key(f.record), str(f.record.source.source_url)) for f in self.facts]
        if len(natural_keys) != len(set(natural_keys)):
            raise ValueError("duplicate target observation natural key")
        source_map = {(s.company_slug, str(s.source_url)): s for s in self.sources}
        preferred = set()
        for fact in self.facts:
            r = fact.record
            if r.company_slug not in self.company_slugs:
                raise ValueError("target fact lies outside attested scope")
            source = source_map.get((r.company_slug, str(r.source.source_url)))
            if source is None or source.sha256 != r.source.sha256:
                raise ValueError("target fact/source mismatch")
            expected_as_of = (
                r.period_end.isoformat() if fact.measurement_type == "instant" else None
            )
            if fact.as_of != expected_as_of:
                raise ValueError("target measurement date mismatch")
            if fact.is_preferred:
                key = fact_key(r)
                if key in preferred:
                    raise ValueError("multiple target preferred facts for one key")
                preferred.add(key)
        if any(s.company_slug not in self.company_slugs for s in self.sources):
            raise ValueError("target source lies outside attested scope")
        return self


def source_key(observation: dict) -> str:
    return f"{observation['company_slug']}:{observation['source_sha256']}"


def build_catalog(
    observations: list[dict],
    definitions: dict[str, dict],
    manifest: list[dict],
    fiscal_years: set[int],
) -> dict:
    """Validate all evidence before selecting current-year conflict-free candidates."""
    source_map = {(m["company_slug"], m["report_fiscal_year"]): m for m in manifest}
    if len(source_map) != len(manifest):
        raise ValueError("duplicate report in source manifest")
    if not fiscal_years:
        raise ValueError("a nonempty fiscal-year selection is required")
    entries = []
    records = []
    seen = set()
    urls = {}
    for original in observations:
        o = dict(original)
        oid = o["observation_id"]
        if oid in seen:
            raise ValueError("duplicate observation ID")
        seen.add(oid)
        definition = definitions[o["metric_code"]]
        kind = definition["measurement_type"]
        if kind not in {"instant", "duration"} or not definition.get("definition"):
            raise ValueError("missing metric definition/measurement type")
        # Batch1 predates measurement metadata; its explicitly defined P&L fields are durations.
        o.setdefault("measurement_type", kind)
        o.setdefault("as_of", o["period_end"] if kind == "instant" else None)
        if o["measurement_type"] != kind or o["as_of"] != (
            o["period_end"] if kind == "instant" else None
        ):
            raise ValueError("evidence measurement metadata mismatch")
        if o["reporting_basis"] != "consolidated":
            raise ValueError("this catalog only supports consolidated evidence")
        if o["quality_status"] != "unverified" or o["is_preferred"] is not False:
            raise ValueError("input evidence must not preapprove itself")
        source = source_map[(o["company_slug"], o["source_fiscal_year"])]
        if any(
            o[field] != source[name]
            for field, name in [
                ("source_sha256", "sha256"),
                ("source_url", "source_url"),
                ("source_title", "title"),
                ("source_publisher", "publisher"),
            ]
        ):
            raise ValueError("source manifest mismatch")
        url_key = (o["company_slug"], o["source_url"])
        if url_key in urls and urls[url_key] != o["source_sha256"]:
            raise ValueError("source URL has competing document hashes")
        urls[url_key] = o["source_sha256"]
        record = _record_from_row({k: str(v) if v is not None else "" for k, v in o.items()})
        if record.source.document_type != "annual_report":
            raise ValueError("this catalog only supports annual-report evidence")
        if record.source_page is not None and record.source_page > source["page_count"]:
            raise ValueError("evidence page exceeds authenticated PDF page count")
        if record.source.sha256 is None or record.source_page is None or not record.source_label:
            raise ValueError("source hash, page and label are required")
        if str(record.normalized_value) != o["normalized_value"]:
            raise ValueError("normalization mismatch")
        role = o["column_role"]
        if role not in {"current_year", "comparative"}:
            raise ValueError("invalid column role")
        expected_year = o["source_fiscal_year"] - (role == "comparative")
        if record.fiscal_year != expected_year:
            raise ValueError("source column fiscal year mismatch")
        if (
            record.period_type != "FY"
            or record.period_start.isoformat() != f"{expected_year - 1}-04-01"
            or record.period_end.isoformat() != f"{expected_year}-03-31"
        ):
            raise ValueError("catalog expects April-March annual reporting periods")
        entry = {
            "observation": o,
            "definition": definition,
            "definition_sha256": digest(definition),
            "evidence_sha256": digest(o),
            "source_key": source_key(o),
        }
        entries.append(entry)
        records.append(record)
    bad = {c.key for c in find_conflicts(records)}
    candidates, withheld = [], []
    selected = set()
    for entry, record in zip(entries, records, strict=True):
        o = entry["observation"]
        if o["column_role"] != "current_year" or o["fiscal_year"] not in fiscal_years:
            continue
        key = fact_key(record)
        if key in selected:
            raise ValueError("multiple current-year observations for a candidate key")
        selected.add(key)
        (withheld if key in bad else candidates).append(entry)
    catalog = {
        "version": 1,
        "policy": "current_year_columns_exclude_all_conflicting_keys",
        "fiscal_years": sorted(fiscal_years),
        "definitions": definitions,
        "source_manifest": manifest,
        "observations": [e["observation"] for e in entries],
    }
    return {
        "sha256": digest(catalog),
        "observations": len(entries),
        "candidates": candidates,
        "withheld": withheld,
        "conflicting_keys": len(bad),
    }


def empty_reviews(catalog: dict) -> ReviewLedger:
    """A merge/schema pass cannot implicitly become a source or fact approval."""
    return ReviewLedger(catalog_sha256=catalog["sha256"])


def build_load_plan(
    catalog: dict,
    reviews: ReviewLedger,
    *,
    target: TargetSnapshot | None = None,
    expected_project_ref: str | None = None,
    now: datetime | None = None,
    max_snapshot_age: timedelta = timedelta(hours=24),
) -> dict:
    """Return reviewable proposals/blocks, never SQL, writes, or implicit status upgrades."""
    if reviews.catalog_sha256 != catalog["sha256"]:
        raise ValueError("review ledger is stale for this evidence/definition catalog")
    candidate_ids = {e["observation"]["observation_id"] for e in catalog["candidates"]}
    source_keys = {e["source_key"] for e in catalog["candidates"]}
    if set(reviews.facts) - candidate_ids or set(reviews.sources) - source_keys:
        raise ValueError("review ledger references unknown or withheld evidence")
    now = now or datetime.now(UTC)
    if now.utcoffset() is None or max_snapshot_age <= timedelta(0):
        raise ValueError("invalid planning time/snapshot age limit")
    for review in [*reviews.facts.values(), *reviews.sources.values()]:
        if review.reviewed_at is not None and review.reviewed_at > now:
            raise ValueError("review time lies in the future")
    if target is not None:
        if not expected_project_ref or target.project_ref != expected_project_ref:
            raise ValueError("target project mismatch")
        if not timedelta(0) <= now - target.captured_at <= max_snapshot_age:
            raise ValueError("target snapshot is stale or future-dated")
        companies = {e["observation"]["company_slug"] for e in catalog["candidates"]}
        if not companies.issubset(set(target.company_slugs)):
            raise ValueError("target snapshot does not cover incoming companies")
    existing = defaultdict(list)
    source_map = {}
    if target:
        for f in target.facts:
            existing[fact_key(f.record)].append(f)
        source_map = {(s.company_slug, str(s.source_url)): s for s in target.sources}
    blocked, proposed, unchanged = [], [], []
    for entry in catalog["candidates"]:
        o = entry["observation"]
        oid = o["observation_id"]
        fact_review = reviews.facts.get(oid, Review())
        src_review = reviews.sources.get(entry["source_key"], Review())
        reasons = []
        if src_review.status != "approved":
            reasons.append(f"source_review_{src_review.status}")
        if fact_review.status != "approved":
            reasons.append(f"fact_review_{fact_review.status}")
        if target is None:
            reasons.append("target_snapshot_missing")
        record = _record_from_row({k: str(v) if v is not None else "" for k, v in o.items()})
        old_source = source_map.get((o["company_slug"], o["source_url"]))
        if old_source and old_source.sha256 != o["source_sha256"]:
            reasons.append("target_source_hash_conflict")
        if old_source and old_source.verification_status != "verified":
            reasons.append("target_source_not_verified")
        same_source = None
        for old in existing[fact_key(record)]:
            previous = old.record
            if (previous.currency, previous.normalized_value) != (
                record.currency,
                record.normalized_value,
            ):
                reasons.append("target_value_conflict")
            if (
                previous.period_start,
                old.reporting_basis,
                old.measurement_type,
                old.as_of,
                old.definition_sha256,
            ) != (
                record.period_start,
                o["reporting_basis"],
                o["measurement_type"],
                o["as_of"],
                entry["definition_sha256"],
            ):
                reasons.append("target_definition_or_period_conflict")
            if str(previous.source.source_url) == o["source_url"]:
                same_source = old
                if previous != record:
                    reasons.append("target_existing_observation_differs")
                if old.quality_status != "verified" or not old.is_preferred:
                    reasons.append("target_existing_review_state_differs")
            elif old.is_preferred:
                reasons.append("target_preferred_replacement_requires_review")
        if reasons:
            blocked.append(
                {
                    "observation_id": oid,
                    "reasons": sorted(set(reasons)),
                    "evidence_sha256": entry["evidence_sha256"],
                    "definition_sha256": entry["definition_sha256"],
                }
            )
        elif same_source:
            unchanged.append({"observation_id": oid, "existing_fact_id": str(same_source.id)})
        else:
            proposed.append(
                {
                    "observation_id": oid,
                    "record": record.model_dump(mode="json"),
                    "normalized_value": str(record.normalized_value),
                    "quality_status": "verified",
                    "is_preferred": True,
                    "provenance": entry,
                    "fact_review": fact_review.model_dump(mode="json"),
                    "source_review": src_review.model_dump(mode="json"),
                }
            )
    return {
        "plan_version": 1,
        "catalog_sha256": catalog["sha256"],
        "review_ledger_sha256": digest(reviews.model_dump(mode="json")),
        "target_project_ref": target.project_ref if target else None,
        "target_snapshot_sha256": digest(target.model_dump(mode="json")) if target else None,
        "target_snapshot_captured_at": target.captured_at.isoformat() if target else None,
        "summary": {
            "evidence_observations": catalog["observations"],
            "candidate_facts": len(candidate_ids),
            "unresolved_conflicting_keys": catalog["conflicting_keys"],
            "withheld_current_year_facts": len(catalog["withheld"]),
            "blocked_candidates": len(blocked),
            "proposed_inserts": len(proposed),
            "already_present": len(unchanged),
            "production_writes": 0,
        },
        "withheld": [
            {
                "observation_id": e["observation"]["observation_id"],
                "reason": "unresolved_source_conflict",
            }
            for e in catalog["withheld"]
        ],
        "blocked": blocked,
        "proposed_facts": proposed,
        "already_present": unchanged,
        "apply_ready": False,
        "apply_blockers": [
            "No executable database writer in this planner",
            "Target ID resolution and transaction-time conflict recheck required",
            "Persist definition, basis, measurement and review provenance in schema",
            "Verify target migration/RLS state before any privileged write",
        ],
    }
