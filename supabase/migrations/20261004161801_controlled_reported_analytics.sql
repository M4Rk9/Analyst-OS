begin;
do $$ begin
    if exists (select 1 from public.calculated_metrics) or exists (select 1 from public.red_flags) then
        raise exception 'review legacy derived outputs before installing analytics guards';
    end if;
end $$;

create schema analytics;
revoke all on schema analytics from public, anon, authenticated;
grant usage on schema analytics to service_role;
create table analytics.publication_requests (
    request_sha256 text primary key,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (request_sha256 = encode(sha256(convert_to(canonical_json,'UTF8')),'hex')),
    check ((payload->>'policy_version' = 'reported-core-1' and payload->>'formula_version' = '1.0') is true),
    check ((jsonb_typeof(payload->'calculations') = 'array') is true)
);
create table analytics.metric_provenance (
    metric_id uuid primary key references public.calculated_metrics(id) on delete restrict,
    request_sha256 text not null references analytics.publication_requests(request_sha256),
    calculation_sha256 text not null,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (calculation_sha256 = encode(sha256(convert_to(canonical_json,'UTF8')),'hex'))
);
create table analytics.flag_provenance (
    flag_id uuid primary key references public.red_flags(id) on delete restrict,
    request_sha256 text not null references analytics.publication_requests(request_sha256),
    flag_sha256 text not null,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (flag_sha256 = encode(sha256(convert_to(canonical_json,'UTF8')),'hex'))
);
create table analytics.load_receipts (
    request_sha256 text primary key references analytics.publication_requests(request_sha256),
    import_id uuid not null unique,
    receipt_sha256 text not null,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (receipt_sha256 = encode(sha256(convert_to(canonical_json,'UTF8')),'hex')),
    check ((payload->>'request_sha256' = request_sha256 and payload->>'import_id' = import_id::text
        and payload->>'outcome' = 'committed') is true)
);
create index metric_provenance_request_idx on analytics.metric_provenance(request_sha256);
create index flag_provenance_request_idx on analytics.flag_provenance(request_sha256);
alter table analytics.publication_requests enable row level security;
alter table analytics.metric_provenance enable row level security;
alter table analytics.flag_provenance enable row level security;
alter table analytics.load_receipts enable row level security;
revoke all on all tables in schema analytics from public, anon, authenticated;
grant select, insert on all tables in schema analytics to service_role;
revoke update, delete, truncate on public.calculated_metrics, public.red_flags from service_role;
alter table public.calculated_metrics add column policy_version text not null default 'reported-core-1';
alter table public.calculated_metrics add constraint metrics_reported_policy check (
    policy_version = 'reported-core-1' and formula_version = '1.0'
    and metric_code in ('current_ratio','working_capital','cfo_to_reported_group_profit')
    and value not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric));

-- Exact Decimal precision=28, ROUND_HALF_EVEN, without float or PostgreSQL's
-- default division scale. Quotient equality is checked independently in SQL.
create function public.reported_decimal_quotient(n numeric, d numeric) returns numeric
language plpgsql immutable strict security invoker set search_path = '' as $$
declare a numeric := abs(n); b numeric := abs(d); k integer; s integer;
    numerator numeric; denominator numeric; q numeric; r numeric;
begin
    if d <= 0 or n in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        or d in ('NaN'::numeric,'Infinity'::numeric) then return null; end if;
    if n = 0 then return 0; end if;
    k := length(trunc(a)::text) - length(trunc(b)::text);
    while a < b * power(10::numeric,k) loop k := k - 1; end loop;
    while a >= b * power(10::numeric,k+1) loop k := k + 1; end loop;
    s := 27-k;
    numerator := a * power(10::numeric,greatest(s,0));
    denominator := b * power(10::numeric,greatest(-s,0));
    q := div(numerator,denominator); r := mod(numerator,denominator);
    if 2*r > denominator or (2*r = denominator and mod(q,2) <> 0) then q := q+1; end if;
    return sign(n) * q * power(10::numeric,-s);
end $$;

create function public.reported_metric_is_valid(m public.calculated_metrics) returns boolean
language plpgsql stable security invoker set search_path = '' as $$
declare a public.financial_facts; b public.financial_facts; slug text; fy integer;
    first_code text; second_code text; expected numeric;
begin
    if m.policy_version <> 'reported-core-1' or m.formula_version <> '1.0'
        or jsonb_array_length(m.input_facts) <> 2 then return false; end if;
    select c.slug,p.fiscal_year into slug,fy from public.companies c
      join public.reporting_periods p on p.company_id=c.id
      where c.id=m.company_id and c.is_active and p.id=m.reporting_period_id
        and p.period_type='FY' and p.currency='INR';
    if slug is null or fy not between 2022 and 2026 or slug not in
        ('reliance-industries','tcs','hdfc-bank','larsen-toubro','tata-motors') then return false; end if;
    if m.metric_code in ('current_ratio','working_capital') then
        first_code := 'current_assets'; second_code := 'current_liabilities';
    elsif m.metric_code='cfo_to_reported_group_profit' then
        first_code := case when slug in ('reliance-industries','tcs') then 'cash_from_operations' else 'cfo' end;
        second_code := 'profit_for_year';
    else return false; end if;
    select * into a from public.financial_facts where id=(m.input_facts->0->>'fact_id')::uuid;
    select * into b from public.financial_facts where id=(m.input_facts->1->>'fact_id')::uuid;
    if a.id is null or b.id is null or a.company_id<>m.company_id or b.company_id<>m.company_id
      or a.reporting_period_id<>m.reporting_period_id or b.reporting_period_id<>m.reporting_period_id
      or a.metric_code<>first_code or b.metric_code<>second_code
      or not a.is_preferred or not b.is_preferred or a.quality_status<>'verified' or b.quality_status<>'verified'
      or a.currency<>'INR' or b.currency<>'INR'
      or (m.input_facts->0->>'normalized_value')::numeric is distinct from a.normalized_value
      or (m.input_facts->1->>'normalized_value')::numeric is distinct from b.normalized_value
      or not exists (select 1 from public.source_documents s where s.id=a.source_document_id and s.verification_status='verified')
      or not exists (select 1 from public.source_documents s where s.id=b.source_document_id and s.verification_status='verified')
      then return false; end if;
    if m.metric_code='working_capital' then
        expected := a.normalized_value-b.normalized_value;
        if m.unit<>'INR' then return false; end if;
    else
        expected := public.reported_decimal_quotient(a.normalized_value,b.normalized_value);
        if m.unit<>'ratio' then return false; end if;
    end if;
    return expected is not null and expected=m.value;
exception when invalid_text_representation or numeric_value_out_of_range then return false;
end $$;

create function public.reported_flag_is_valid(f public.red_flags) returns boolean
language sql stable security invoker set search_path = '' as $$
 select coalesce(f.is_active and f.flag_code='weak_reported_group_cash_conversion' and f.rule_version='1.0'
    and f.severity='high' and f.title='Operating cash flow is below reported group profit'
    and f.description='CFO / reported consolidated group profit is below 0.7; investigate earnings-to-cash conversion. This is an investigation signal, not an investment recommendation.'
    and exists (select 1 from public.calculated_metrics m
        where m.id::text=f.evidence->>'metric_id' and m.company_id=f.company_id
        and m.reporting_period_id=f.reporting_period_id and m.metric_code='cfo_to_reported_group_profit'
        and m.value<0.7 and public.reported_metric_is_valid(m)
        and f.evidence=jsonb_build_object('metric_id',m.id::text,'threshold','0.7','policy_version',m.policy_version)),false)
$$;

create function analytics.immutable_output() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin raise exception 'analytics evidence and outputs are append-only'; end $$;

create function analytics.check_publication() returns trigger
language plpgsql security invoker set search_path = '' as $$
declare p jsonb; request jsonb; input jsonb; proof ingestion.fact_provenance;
begin
    if tg_table_name='calculated_metrics' then
        select mp.payload,r.payload into p,request from analytics.metric_provenance mp
            join analytics.publication_requests r using(request_sha256) where mp.metric_id=new.id;
        if p is null or not public.reported_metric_is_valid(new)
            or not coalesce(request->'calculations' @> jsonb_build_array(p),false)
            or p->>'status'<>'available' or (p->>'value')::numeric is distinct from new.value
            or p->'inputs' is distinct from new.input_facts or p->>'metric_code' is distinct from new.metric_code
            or p->>'unit' is distinct from new.unit
            or not exists (select 1 from public.companies c join public.reporting_periods rp on rp.company_id=c.id
                where c.id=new.company_id and rp.id=new.reporting_period_id and c.slug=p->>'company_slug'
                and rp.fiscal_year=(p->>'fiscal_year')::integer)
            then raise exception 'derived metric lacks a valid reviewed input contract'; end if;
        for input in select value from jsonb_array_elements(new.input_facts) loop
            select * into proof from ingestion.fact_provenance where fact_id=(input->>'fact_id')::uuid;
            if proof.fact_id is null or proof.observation_id is distinct from input->>'observation_id'
                or proof.evidence_sha256 is distinct from input->>'evidence_sha256'
                or proof.definition_sha256 is distinct from input->>'definition_sha256'
                or not coalesce(request->'packet_bindings' @> jsonb_build_array(jsonb_build_object(
                    'catalog_sha256',proof.catalog_sha256,'review_ledger_sha256',proof.review_ledger_sha256)),false)
                then raise exception 'derived input approval provenance mismatch'; end if;
            perform ingestion.assert_fact(proof.fact_id);
        end loop;
    else
        select fp.payload into p from analytics.flag_provenance fp
            join analytics.metric_provenance mp on mp.metric_id=(fp.payload->'evidence'->>'metric_id')::uuid
                and mp.request_sha256=fp.request_sha256 where fp.flag_id=new.id;
        if p is null or not public.reported_flag_is_valid(new) or p is distinct from jsonb_build_object(
            'company_id',new.company_id::text,'reporting_period_id',new.reporting_period_id::text,
            'flag_code',new.flag_code,'title',new.title,'description',new.description,'severity',new.severity,
            'evidence',new.evidence,'rule_version',new.rule_version)
            then raise exception 'derived signal lacks valid metric provenance'; end if;
    end if;
    return null;
end $$;

create trigger requests_immutable before update or delete on analytics.publication_requests for each row execute function analytics.immutable_output();
create trigger metric_provenance_immutable before update or delete on analytics.metric_provenance for each row execute function analytics.immutable_output();
create trigger flag_provenance_immutable before update or delete on analytics.flag_provenance for each row execute function analytics.immutable_output();
create trigger analytics_receipts_immutable before update or delete on analytics.load_receipts for each row execute function analytics.immutable_output();
create trigger metrics_immutable before update or delete on public.calculated_metrics for each row execute function analytics.immutable_output();
create trigger flags_immutable before update or delete on public.red_flags for each row execute function analytics.immutable_output();
create constraint trigger metrics_reviewed_publication after insert on public.calculated_metrics
    deferrable initially deferred for each row execute function analytics.check_publication();
create constraint trigger flags_reviewed_publication after insert on public.red_flags
    deferrable initially deferred for each row execute function analytics.check_publication();
revoke all on all functions in schema analytics from public, anon, authenticated;
grant execute on all functions in schema analytics to service_role;
revoke all on function public.reported_decimal_quotient(numeric,numeric),
    public.reported_metric_is_valid(public.calculated_metrics),public.reported_flag_is_valid(public.red_flags) from public;
grant execute on function public.reported_decimal_quotient(numeric,numeric),
    public.reported_metric_is_valid(public.calculated_metrics),public.reported_flag_is_valid(public.red_flags) to anon, authenticated, service_role;
drop policy calculated_metrics_public_read on public.calculated_metrics;
create policy calculated_metrics_public_read on public.calculated_metrics for select to anon, authenticated
    using (public.reported_metric_is_valid(calculated_metrics));
drop policy red_flags_public_read on public.red_flags;
create policy red_flags_public_read on public.red_flags for select to anon, authenticated
    using (public.reported_flag_is_valid(red_flags));
comment on schema analytics is 'Private immutable derived input contracts and atomic receipts. Never expose through Data API.';
commit;
