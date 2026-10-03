begin;

-- Legacy derived outputs have no review-bound input contract yet. Do not leave
-- them public after demoting their inputs. Require a separate reviewed upgrade.
do $$
begin
    if exists (select 1 from public.calculated_metrics)
       or exists (select 1 from public.red_flags) then
        raise exception 'review existing calculated_metrics/red_flags before this provenance migration';
    end if;
end;
$$;

-- Preserve amounts; remove legacy publication assertions without review evidence.
update public.financial_facts set quality_status = 'unverified', is_preferred = false
where quality_status = 'verified' or is_preferred;
update public.source_documents set verification_status = 'pending'
where verification_status = 'verified';
alter table public.financial_facts alter column quality_status set default 'unverified';
alter table public.financial_facts
    add constraint facts_finite_values check (
        raw_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and normalized_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and unit_scale not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)),
    add constraint facts_exact_normalization check (normalized_value = raw_value * unit_scale),
    add constraint facts_preferred_verified check (not is_preferred or quality_status = 'verified');
alter table public.reporting_periods add constraint periods_company_id_unique unique (company_id, id);
alter table public.source_documents add constraint sources_company_id_unique unique (company_id, id);
alter table public.financial_facts
    add constraint facts_same_company_period foreign key (company_id, reporting_period_id)
        references public.reporting_periods (company_id, id),
    add constraint facts_same_company_source foreign key (company_id, source_document_id)
        references public.source_documents (company_id, id);
create unique index financial_facts_one_preferred
    on public.financial_facts (company_id, reporting_period_id, metric_code)
    where is_preferred;

create schema ingestion;
revoke all on schema ingestion from public, anon, authenticated;
grant usage on schema ingestion to service_role;

-- Store the Python canonical UTF-8 JSON verbatim. jsonb::text is NOT its hash input.
create table ingestion.evidence_catalogs (
    catalog_sha256 text primary key check (catalog_sha256 ~ '^[0-9a-f]{64}$'),
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    created_at timestamptz not null default now(),
    check (catalog_sha256 = encode(sha256(convert_to(canonical_json, 'UTF8')), 'hex')),
    check ((jsonb_typeof(payload) = 'object'
        and payload->>'version' = '1'
        and payload->>'policy' = 'current_year_columns_exclude_all_conflicting_keys'
        and jsonb_typeof(payload->'observations') = 'array'
        and jsonb_typeof(payload->'source_manifest') = 'array'
        and jsonb_typeof(payload->'definitions') = 'object'
        and jsonb_typeof(payload->'fiscal_years') = 'array') is true)
);
create table ingestion.review_ledgers (
    review_ledger_sha256 text primary key check (review_ledger_sha256 ~ '^[0-9a-f]{64}$'),
    catalog_sha256 text not null references ingestion.evidence_catalogs,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    created_at timestamptz not null default now(),
    unique (catalog_sha256, review_ledger_sha256),
    check (review_ledger_sha256 = encode(sha256(convert_to(canonical_json, 'UTF8')), 'hex')),
    check ((payload->>'catalog_sha256' = catalog_sha256
        and jsonb_typeof(payload->'sources') = 'object'
        and jsonb_typeof(payload->'facts') = 'object') is true)
);
create table ingestion.source_provenance (
    source_document_id uuid not null references public.source_documents on delete restrict,
    catalog_sha256 text not null,
    review_ledger_sha256 text not null,
    primary key (source_document_id, catalog_sha256, review_ledger_sha256),
    foreign key (catalog_sha256, review_ledger_sha256)
        references ingestion.review_ledgers (catalog_sha256, review_ledger_sha256)
);
create table ingestion.fact_provenance (
    fact_id uuid not null references public.financial_facts on delete restrict,
    source_document_id uuid not null,
    catalog_sha256 text not null,
    review_ledger_sha256 text not null,
    observation_id text not null,
    evidence_sha256 text not null check (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    definition_sha256 text not null check (definition_sha256 ~ '^[0-9a-f]{64}$'),
    evidence_canonical_json text not null,
    definition_canonical_json text not null,
    observation jsonb generated always as (evidence_canonical_json::jsonb) stored,
    definition jsonb generated always as (definition_canonical_json::jsonb) stored,
    created_at timestamptz not null default now(),
    primary key (fact_id, catalog_sha256, review_ledger_sha256),
    unique (catalog_sha256, review_ledger_sha256, observation_id),
    foreign key (source_document_id, catalog_sha256, review_ledger_sha256)
        references ingestion.source_provenance,
    check (evidence_sha256 = encode(sha256(convert_to(evidence_canonical_json, 'UTF8')), 'hex')),
    check (definition_sha256 = encode(sha256(convert_to(definition_canonical_json, 'UTF8')), 'hex')),
    check ((jsonb_typeof(observation) = 'object'
        and observation->>'observation_id' = observation_id
        and jsonb_typeof(definition) = 'object') is true)
);

alter table ingestion.evidence_catalogs enable row level security;
alter table ingestion.review_ledgers enable row level security;
alter table ingestion.source_provenance enable row level security;
alter table ingestion.fact_provenance enable row level security;
revoke all on all tables in schema ingestion from public, anon, authenticated, service_role;
grant select, insert on all tables in schema ingestion to service_role;
alter default privileges in schema ingestion revoke execute on functions from public;
alter default privileges in schema ingestion revoke all on tables from anon, authenticated;

-- Review text is an attestation, not authenticated identity or a digital signature.
create function ingestion.approved_review(review jsonb) returns boolean
language plpgsql security invoker set search_path = pg_catalog as $$
begin
    return coalesce(
        review->>'status' = 'approved'
        and jsonb_typeof(review->'reviewer') = 'string'
        and length(regexp_replace(review->>'reviewer', '^[[:space:]]+|[[:space:]]+$', '', 'g')) between 1 and 160
        and jsonb_typeof(review->'rationale') = 'string'
        and length(regexp_replace(review->>'rationale', '^[[:space:]]+|[[:space:]]+$', '', 'g')) between 1 and 2000
        and (review->>'reviewed_at') ~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
        and (review->>'reviewed_at')::timestamptz <= current_timestamp, false);
exception when invalid_datetime_format or datetime_field_overflow then
    return false;
end;
$$;

create function ingestion.immutable_evidence() returns trigger
language plpgsql security invoker set search_path = pg_catalog as $$
begin
    raise exception 'ingestion evidence is append-only; retain old records and add a new ledger';
end;
$$;
create trigger catalogs_immutable before update or delete on ingestion.evidence_catalogs
    for each row execute function ingestion.immutable_evidence();
create trigger ledgers_immutable before update or delete on ingestion.review_ledgers
    for each row execute function ingestion.immutable_evidence();
create trigger source_provenance_immutable before update or delete on ingestion.source_provenance
    for each row execute function ingestion.immutable_evidence();
create trigger fact_provenance_immutable before update or delete on ingestion.fact_provenance
    for each row execute function ingestion.immutable_evidence();

create function ingestion.assert_source(source_id uuid) returns void
language plpgsql security invoker set search_path = pg_catalog as $$
declare
    s public.source_documents;
    company_slug text;
begin
    select * into s from public.source_documents where id = source_id for share;
    if not found or s.verification_status <> 'verified' then return; end if;
    select slug into company_slug from public.companies where id = s.company_id for share;
    if not exists (
        select 1 from ingestion.source_provenance p
        join ingestion.review_ledgers r using (catalog_sha256, review_ledger_sha256)
        join ingestion.evidence_catalogs c using (catalog_sha256)
        cross join lateral jsonb_array_elements(c.payload->'source_manifest') m
        where p.source_document_id = s.id
          and m->>'company_slug' = company_slug
          and m->>'sha256' = s.sha256
          and m->>'source_url' = s.source_url
          and m->>'title' = s.title and m->>'publisher' = s.publisher
          and (m->>'report_fiscal_year')::integer = s.fiscal_year
          and (m->>'page_count')::integer = s.page_count
          and s.document_type = 'annual_report' and s.fiscal_quarter is null
          and s.published_at is null
          and ingestion.approved_review(r.payload->'sources'->(company_slug || ':' || s.sha256))
    ) then raise exception 'verified source lacks matching approved provenance: %', s.id; end if;
end;
$$;

create function ingestion.assert_fact(fact_id uuid) returns void
language plpgsql security invoker set search_path = pg_catalog as $$
declare
    f public.financial_facts;
    s public.source_documents;
    period public.reporting_periods;
    company_slug text;
begin
    select * into f from public.financial_facts where id = fact_id for share;
    if not found or f.quality_status <> 'verified' then return; end if;
    select * into s from public.source_documents where id = f.source_document_id for share;
    select * into period from public.reporting_periods where id = f.reporting_period_id for share;
    select slug into company_slug from public.companies where id = f.company_id for share;
    perform ingestion.assert_source(s.id);
    if s.verification_status <> 'verified' then
        raise exception 'verified fact requires a verified source: %', f.id;
    end if;
    if not exists (
        select 1 from ingestion.fact_provenance p
        join ingestion.review_ledgers r using (catalog_sha256, review_ledger_sha256)
        join ingestion.evidence_catalogs c using (catalog_sha256)
        where p.fact_id = f.id and p.source_document_id = s.id
          and (select count(*) from jsonb_array_elements(c.payload->'observations') o
               where o = p.observation) = 1
          and c.payload->'definitions'->f.metric_code = p.definition
          and p.definition->>'metric_code' = f.metric_code
          and p.observation->>'metric_code' = f.metric_code
          and p.observation->>'company_slug' = company_slug
          and p.observation->>'source_sha256' = s.sha256
          and p.observation->>'source_url' = s.source_url
          and p.observation->>'source_title' = s.title
          and p.observation->>'source_publisher' = s.publisher
          and p.observation->>'source_document_type' = s.document_type
          and (p.observation->>'source_fiscal_year')::integer = s.fiscal_year
          and p.observation->>'period_type' = period.period_type
          and (p.observation->>'fiscal_year')::integer = period.fiscal_year
          and (p.observation->>'period_start')::date = period.period_start
          and (p.observation->>'period_end')::date = period.period_end
          and p.observation->>'currency' = f.currency and f.currency = period.currency
          and (p.observation->>'raw_value')::numeric = f.raw_value
          and (p.observation->>'normalized_value')::numeric = f.normalized_value
          and (p.observation->>'unit_scale')::numeric = f.unit_scale
          and (p.observation->>'source_page')::integer = f.source_page
          and f.source_page <= s.page_count
          and p.observation->>'source_label' = f.source_label
          and p.observation->>'raw_value_text' is not distinct from f.raw_value_text
          and p.observation->>'reporting_basis' = 'consolidated'
          and p.observation->>'quality_status' = 'unverified'
          and p.observation->'is_preferred' = 'false'::jsonb
          and p.observation->>'column_role' = 'current_year'
          and period.period_type = 'FY' and period.fiscal_year = s.fiscal_year
          and period.published_at is null
          and period.period_start = make_date(period.fiscal_year - 1, 4, 1)
          and period.period_end = make_date(period.fiscal_year, 3, 31)
          and c.payload->'fiscal_years' @> jsonb_build_array(period.fiscal_year)
          and p.observation->>'measurement_type' = p.definition->>'measurement_type'
          and (p.observation->>'measurement_type' = 'duration' and p.observation->'as_of' = 'null'::jsonb
            or p.observation->>'measurement_type' = 'instant'
               and (p.observation->>'as_of')::date = period.period_end)
          and length(btrim(p.definition->>'definition')) > 0
          and ingestion.approved_review(r.payload->'facts'->p.observation_id)
          and ingestion.approved_review(r.payload->'sources'->(company_slug || ':' || s.sha256))
          and not exists (
              select 1 from jsonb_array_elements(c.payload->'observations') o
              where o->>'company_slug' = company_slug and o->>'metric_code' = f.metric_code
                and o->>'period_type' = period.period_type
                and (o->>'period_end')::date = period.period_end
                and (o->>'fiscal_year')::integer = period.fiscal_year
                and ((o->>'normalized_value')::numeric <> f.normalized_value
                     or o->>'currency' <> f.currency)
          )
    ) then raise exception 'verified fact lacks matching conflict-free approved provenance: %', f.id; end if;
end;
$$;

create function ingestion.check_publication() returns trigger
language plpgsql security invoker set search_path = pg_catalog as $$
declare linked record;
begin
    if tg_table_name = 'financial_facts' then
        perform ingestion.assert_fact(new.id);
    elsif tg_table_name = 'source_documents' then
        perform ingestion.assert_source(new.id);
        for linked in select id from public.financial_facts where source_document_id = new.id loop
            perform ingestion.assert_fact(linked.id);
        end loop;
    elsif tg_table_name = 'reporting_periods' then
        for linked in select id from public.financial_facts where reporting_period_id = new.id loop
            perform ingestion.assert_fact(linked.id);
        end loop;
    elsif tg_table_name = 'companies' then
        for linked in select id from public.source_documents where company_id = new.id loop
            perform ingestion.assert_source(linked.id);
        end loop;
        for linked in select id from public.financial_facts where company_id = new.id loop
            perform ingestion.assert_fact(linked.id);
        end loop;
    end if;
    return null;
end;
$$;

-- Validate the final transaction, so facts and FK-linked proof can be staged together.
create constraint trigger facts_reviewed_publication after insert or update on public.financial_facts
    deferrable initially deferred for each row execute function ingestion.check_publication();
create constraint trigger sources_reviewed_publication after insert or update on public.source_documents
    deferrable initially deferred for each row execute function ingestion.check_publication();
create constraint trigger periods_reviewed_publication after update on public.reporting_periods
    deferrable initially deferred for each row execute function ingestion.check_publication();
create constraint trigger companies_reviewed_publication after update on public.companies
    deferrable initially deferred for each row execute function ingestion.check_publication();

revoke all on all functions in schema ingestion from public, anon, authenticated;
grant execute on all functions in schema ingestion to service_role;

drop policy financial_facts_public_read on public.financial_facts;
create policy financial_facts_public_read on public.financial_facts for select to anon, authenticated
using (
    quality_status = 'verified'
    and exists (select 1 from public.companies c where c.id = financial_facts.company_id and c.is_active)
    and exists (select 1 from public.source_documents s
        where s.id = financial_facts.source_document_id
          and s.company_id = financial_facts.company_id and s.verification_status = 'verified')
);

comment on schema ingestion is 'Private append-only evidence and review attestations; never expose via the Data API.';
comment on table ingestion.fact_provenance is 'Retains full observation, measurement basis/date, definition and review hashes. Not a production load receipt.';
commit;
