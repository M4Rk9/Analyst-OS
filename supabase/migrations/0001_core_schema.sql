begin;

create extension if not exists pgcrypto;

create table public.companies (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique check (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
    name text not null check (length(name) between 1 and 160),
    ticker text not null check (ticker ~ '^[A-Z0-9&.-]{1,24}$'),
    exchange text not null default 'NSE' check (exchange in ('NSE', 'BSE')),
    sector text not null check (length(sector) between 1 and 120),
    industry text,
    website_url text check (website_url is null or website_url ~ '^https://'),
    investor_relations_url text check (
        investor_relations_url is null or investor_relations_url ~ '^https://'
    ),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (ticker, exchange)
);

create table public.reporting_periods (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    period_type text not null check (period_type in ('FY', 'Q1', 'Q2', 'Q3', 'Q4', 'TTM')),
    fiscal_year smallint not null check (fiscal_year between 1900 and 2200),
    period_start date not null,
    period_end date not null,
    currency char(3) not null check (currency ~ '^[A-Z]{3}$'),
    published_at date,
    created_at timestamptz not null default now(),
    check (period_start <= period_end),
    unique (company_id, period_type, fiscal_year, period_end)
);

create table public.source_documents (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    title text not null check (length(title) between 1 and 300),
    document_type text not null check (
        document_type in (
            'annual_report',
            'quarterly_result',
            'investor_presentation',
            'earnings_release',
            'exchange_disclosure',
            'ir_material'
        )
    ),
    fiscal_year smallint check (fiscal_year is null or fiscal_year between 1900 and 2200),
    fiscal_quarter smallint check (fiscal_quarter is null or fiscal_quarter between 1 and 4),
    source_url text not null check (source_url ~ '^https://'),
    publisher text not null check (length(publisher) between 1 and 200),
    published_at date,
    retrieved_at timestamptz not null default now(),
    sha256 text check (sha256 is null or sha256 ~ '^[0-9a-f]{64}$'),
    page_count integer check (page_count is null or page_count > 0),
    verification_status text not null default 'pending' check (
        verification_status in ('pending', 'verified', 'rejected', 'conflict')
    ),
    created_at timestamptz not null default now(),
    unique (company_id, source_url)
);

create table public.financial_facts (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    reporting_period_id uuid not null references public.reporting_periods(id) on delete cascade,
    metric_code text not null check (metric_code ~ '^[a-z][a-z0-9_]{1,63}$'),
    raw_value_text text,
    raw_value numeric not null,
    normalized_value numeric not null,
    currency char(3) check (currency is null or currency ~ '^[A-Z]{3}$'),
    unit_scale numeric not null default 1 check (unit_scale > 0),
    source_document_id uuid not null references public.source_documents(id) on delete restrict,
    source_page integer check (source_page is null or source_page > 0),
    source_label text,
    quality_status text not null default 'verified' check (
        quality_status in ('verified', 'conflict', 'unverified')
    ),
    is_preferred boolean not null default false,
    created_at timestamptz not null default now(),
    unique (company_id, reporting_period_id, metric_code, source_document_id)
);

create table public.calculated_metrics (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    reporting_period_id uuid not null references public.reporting_periods(id) on delete cascade,
    metric_code text not null check (metric_code ~ '^[a-z][a-z0-9_]{1,63}$'),
    value numeric not null,
    unit text not null check (length(unit) between 1 and 40),
    formula_version text not null check (length(formula_version) between 1 and 40),
    input_facts jsonb not null default '[]'::jsonb check (jsonb_typeof(input_facts) = 'array'),
    computed_at timestamptz not null default now(),
    unique (company_id, reporting_period_id, metric_code, formula_version)
);

create table public.red_flags (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    reporting_period_id uuid references public.reporting_periods(id) on delete cascade,
    flag_code text not null check (flag_code ~ '^[a-z][a-z0-9_]{1,63}$'),
    title text not null check (length(title) between 1 and 180),
    description text not null check (length(description) between 1 and 1200),
    severity text not null check (severity in ('low', 'medium', 'high')),
    evidence jsonb not null default '{}'::jsonb check (jsonb_typeof(evidence) = 'object'),
    rule_version text not null check (length(rule_version) between 1 and 40),
    is_active boolean not null default true,
    computed_at timestamptz not null default now(),
    unique nulls not distinct (company_id, reporting_period_id, flag_code, rule_version)
);

create index reporting_periods_company_end_idx
    on public.reporting_periods (company_id, period_end desc);
create index source_documents_company_fy_idx
    on public.source_documents (company_id, fiscal_year desc);
create index financial_facts_company_metric_idx
    on public.financial_facts (company_id, metric_code, reporting_period_id);
create index calculated_metrics_company_metric_idx
    on public.calculated_metrics (company_id, metric_code, reporting_period_id);
create index red_flags_company_active_idx
    on public.red_flags (company_id, is_active, reporting_period_id);

comment on table public.financial_facts is
    'Source-backed observations. Never silently overwrite conflicting historical values.';
comment on table public.calculated_metrics is
    'Deterministic Python-computed metrics. AI must not author these values.';
comment on table public.red_flags is
    'Deterministic investigation signals, not investment recommendations.';

commit;
