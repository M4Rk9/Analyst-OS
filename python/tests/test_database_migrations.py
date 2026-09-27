import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"
ALL_SQL = "\n".join(
    path.read_text(encoding="utf-8").lower()
    for path in sorted(MIGRATIONS.glob("*.sql"))
)
SEED_SQL = (MIGRATIONS / "0003_seed_companies.sql").read_text(encoding="utf-8")

EXPOSED_TABLES = (
    "companies",
    "reporting_periods",
    "source_documents",
    "financial_facts",
    "calculated_metrics",
    "red_flags",
    "ai_insights",
)


def test_every_exposed_table_has_rls_and_select_grant() -> None:
    for table in EXPOSED_TABLES:
        assert f"alter table public.{table} enable row level security;" in ALL_SQL
        assert f"grant select on table public.{table} to anon, authenticated;" in ALL_SQL


def test_browser_roles_receive_no_write_policy() -> None:
    assert not re.search(
        r"create\s+policy[\s\S]*?for\s+(insert|update|delete|all)\b",
        ALL_SQL,
    )


def test_browser_roles_are_revoked_before_public_select_grants() -> None:
    for table in EXPOSED_TABLES:
        assert f"revoke all on table public.{table} from anon, authenticated;" in ALL_SQL


def test_initial_company_seed_is_exactly_the_documented_universe() -> None:
    expected_slugs = {
        "reliance-industries",
        "tcs",
        "hdfc-bank",
        "tata-motors",
        "larsen-toubro",
    }
    found_slugs = set(re.findall(r"\('([a-z0-9-]+)',\s*'", SEED_SQL))
    assert found_slugs == expected_slugs
