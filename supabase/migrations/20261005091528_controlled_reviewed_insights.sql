begin;
do $$ begin
    if exists (select 1 from public.ai_insights) then
        raise exception 'review legacy AI insights before installing controlled publication';
    end if;
end $$;

create schema insights;
revoke all on schema insights from public, anon, authenticated;
grant usage on schema insights to service_role;
create table insights.publication_requests (
    request_sha256 text primary key,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (request_sha256=encode(sha256(convert_to(canonical_json,'UTF8')),'hex')),
    check ((payload->'draft'->>'prompt_version'='reviewed-quotes-2.0') is true),
    check ((jsonb_typeof(payload->'rows')='array' and jsonb_array_length(payload->'rows') between 1 and 12) is true),
    check (((payload->>'draft_canonical_json')::jsonb=payload->'draft'
        and (payload->>'review_canonical_json')::jsonb=payload->'review'
        and payload->'review'->>'draft_sha256'=encode(sha256(convert_to(payload->>'draft_canonical_json','UTF8')),'hex')) is true)
);
create table insights.insight_provenance (
    insight_id uuid primary key references public.ai_insights(id) on delete restrict,
    request_sha256 text not null references insights.publication_requests
);
create index ai_provenance_request_idx on insights.insight_provenance(request_sha256);
create table insights.load_receipts (
    request_sha256 text primary key references insights.publication_requests,
    import_id uuid not null unique,
    receipt_sha256 text not null,
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    check (receipt_sha256=encode(sha256(convert_to(canonical_json,'UTF8')),'hex')),
    check ((payload->>'request_sha256'=request_sha256 and payload->>'import_id'=import_id::text
        and payload->>'outcome'='committed') is true)
);
alter table insights.publication_requests enable row level security;
alter table insights.insight_provenance enable row level security;
alter table insights.load_receipts enable row level security;
revoke all on all tables in schema insights from public, anon, authenticated;
grant select,insert on all tables in schema insights to service_role;
revoke update,delete,truncate on public.ai_insights from service_role;
alter table public.ai_insights
    add column source_sha256 text not null check (source_sha256 ~ '^[a-f0-9]{64}$'),
    add column review_sha256 text not null check (review_sha256 ~ '^[a-f0-9]{64}$'),
    add column model_digest text not null check (model_digest ~ '^[a-f0-9]{64}$'),
    add column candidate_index integer not null check (candidate_index between 0 and 11),
    add constraint ai_same_company_source foreign key (company_id,source_document_id)
        references public.source_documents(company_id,id) on delete restrict;

create function insights.immutable_output() returns trigger
language plpgsql security invoker set search_path=pg_catalog as $$
begin raise exception 'reviewed AI publication is append-only'; end $$;
create trigger ai_insights_immutable before update or delete on public.ai_insights
for each row execute function insights.immutable_output();
create trigger ai_requests_immutable before update or delete on insights.publication_requests
for each row execute function insights.immutable_output();
create trigger ai_proofs_immutable before update or delete on insights.insight_provenance
for each row execute function insights.immutable_output();
create trigger ai_receipts_immutable before update or delete on insights.load_receipts
for each row execute function insights.immutable_output();

create function insights.check_publication() returns trigger
language plpgsql security invoker set search_path=pg_catalog as $$
declare request jsonb; wanted jsonb; candidate jsonb; decision jsonb; source jsonb;
    evidence jsonb; page jsonb; quoted text; matching integer;
begin
    select r.payload into request from insights.insight_provenance p
        join insights.publication_requests r using(request_sha256) where p.insight_id=new.id;
    if request is null then raise exception 'AI insight lacks reviewed publication provenance'; end if;
    select e into wanted from jsonb_array_elements(request->'rows') e where e->>'id'=new.id::text;
    if wanted is null or wanted <> (to_jsonb(new)-'generated_at'-'created_at') then
        raise exception 'AI row differs from exact reviewed publication';
    end if;
    source := request->'draft'->'source';
    candidate := request->'draft'->'bundle'->'insights'->new.candidate_index;
    decision := request->'review'->'decisions'->new.candidate_index::text;
    if not ((ingestion.approved_review(decision)
        and request->'draft'->>'prompt_version'='reviewed-quotes-2.0'
        and new.prompt_version='reviewed-quotes-2.0' and new.validation_status='validated'
        and new.model_name=request->'draft'->'bundle'->>'model_name'
        and new.model_digest=request->'draft'->>'model_digest'
        and new.review_sha256=encode(sha256(convert_to(request->>'review_canonical_json','UTF8')),'hex')
        and new.section=candidate->>'section' and new.title=candidate->>'title'
        and new.insight_text=candidate->>'text' and new.confidence=candidate->>'confidence'
        and new.evidence=candidate->'evidence') is true) then
        raise exception 'AI selection lacks exact explicit reviewer approval';
    end if;
    if new.title || ' ' || new.insight_text ~* '\m(buy|sell|target price|guaranteed returns?)\M|```|<\s*/?\s*[A-Za-z]' then
        raise exception 'AI output contains restricted recommendation or markup';
    end if;
    select count(*) into matching from public.source_documents s join public.companies c on c.id=s.company_id
        where s.id=new.source_document_id and s.company_id=new.company_id and c.is_active
        and s.verification_status='verified' and s.sha256=new.source_sha256
        and source->>'id'=s.id::text and source->>'company_id'=s.company_id::text
        and source->>'company_slug'=c.slug and source->>'source_url'=s.source_url
        and source->>'sha256'=s.sha256 and (source->>'page_count')::integer=s.page_count
        and (source->>'fiscal_year')::integer=s.fiscal_year;
    if matching<>1 then raise exception 'AI source differs from approved live source'; end if;
    perform ingestion.assert_source(new.source_document_id);
    for evidence in select e from jsonb_array_elements(new.evidence) e loop
        quoted := evidence->>'quote';
        select e into page from jsonb_array_elements(request->'draft'->'pages') e
            where e->>'page'=evidence->>'page';
        if not ((length(quoted) between 20 and 1000 and page is not null
            and position(quoted in page->>'text')>0 and evidence->>'source_url'=source->>'source_url'
            and (evidence->>'page')::integer between 1 and (source->>'page_count')::integer) is true) then
            raise exception 'AI citation lacks matching extracted quotation';
        end if;
    end loop;
    return new;
end $$;
create constraint trigger ai_reviewed_publication after insert on public.ai_insights
deferrable initially deferred for each row execute function insights.check_publication();
revoke all on all functions in schema insights from public,anon,authenticated;
grant execute on all functions in schema insights to service_role;

drop policy "public_read_validated_ai_insights" on public.ai_insights;
create policy "public_read_validated_ai_insights" on public.ai_insights for select to anon,authenticated
using (validation_status='validated' and prompt_version='reviewed-quotes-2.0'
    and exists(select 1 from public.companies c where c.id=ai_insights.company_id and c.is_active)
    and exists(select 1 from public.source_documents s where s.id=ai_insights.source_document_id
        and s.company_id=ai_insights.company_id and s.verification_status='verified'
        and s.sha256=ai_insights.source_sha256));
commit;
