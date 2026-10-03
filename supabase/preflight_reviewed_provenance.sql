-- Privileged read-only preflight. Run BEFORE the provenance migration.
begin transaction read only;
select version() as postgres_version;
select count(*) as legacy_verified_sources
from public.source_documents where verification_status = 'verified';
select count(*) as legacy_assertions_to_demote
from public.financial_facts where quality_status = 'verified' or is_preferred;
select count(*) as invalid_normalization_or_nonfinite_values
from public.financial_facts
where normalized_value <> raw_value * unit_scale
   or raw_value in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
   or normalized_value in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
   or unit_scale in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric);
select count(*) as cross_company_references
from public.financial_facts f
join public.reporting_periods p on p.id = f.reporting_period_id
join public.source_documents s on s.id = f.source_document_id
where f.company_id <> p.company_id or f.company_id <> s.company_id;
select (select count(*) from public.calculated_metrics) as existing_calculated_metrics,
       (select count(*) from public.red_flags) as existing_red_flags;
rollback;
