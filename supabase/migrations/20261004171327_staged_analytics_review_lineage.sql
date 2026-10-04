begin;
-- A staged load keeps each fact's original immutable ledger. The selected latest
-- packet must independently approve that exact observation and source in the
-- same pinned catalog; assert_fact still verifies its original load provenance.
create or replace function analytics.check_publication() returns trigger
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
                or not exists (
                    select 1 from jsonb_array_elements(request->'packet_bindings') binding
                    join ingestion.review_ledgers selected
                        on selected.catalog_sha256=binding->>'catalog_sha256'
                        and selected.review_ledger_sha256=binding->>'review_ledger_sha256'
                    where selected.catalog_sha256=proof.catalog_sha256
                        and ingestion.approved_review(selected.payload->'facts'->proof.observation_id)
                        and ingestion.approved_review(selected.payload->'sources'->
                            ((proof.observation->>'company_slug') || ':' || (proof.observation->>'source_sha256')))
                )
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

commit;
