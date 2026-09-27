begin;

alter table public.companies enable row level security;
alter table public.reporting_periods enable row level security;
alter table public.source_documents enable row level security;
alter table public.financial_facts enable row level security;
alter table public.calculated_metrics enable row level security;
alter table public.red_flags enable row level security;

-- Start from deny-all for browser roles, then grant only SELECT.
revoke all on table public.companies from anon, authenticated;
revoke all on table public.reporting_periods from anon, authenticated;
revoke all on table public.source_documents from anon, authenticated;
revoke all on table public.financial_facts from anon, authenticated;
revoke all on table public.calculated_metrics from anon, authenticated;
revoke all on table public.red_flags from anon, authenticated;

grant usage on schema public to anon, authenticated;
grant select on table public.companies to anon, authenticated;
grant select on table public.reporting_periods to anon, authenticated;
grant select on table public.source_documents to anon, authenticated;
grant select on table public.financial_facts to anon, authenticated;
grant select on table public.calculated_metrics to anon, authenticated;
grant select on table public.red_flags to anon, authenticated;

create policy companies_public_read
    on public.companies
    for select
    to anon, authenticated
    using (is_active = true);

create policy reporting_periods_public_read
    on public.reporting_periods
    for select
    to anon, authenticated
    using (
        exists (
            select 1
            from public.companies c
            where c.id = reporting_periods.company_id
              and c.is_active = true
        )
    );

create policy source_documents_public_read
    on public.source_documents
    for select
    to anon, authenticated
    using (
        verification_status = 'verified'
        and exists (
            select 1
            from public.companies c
            where c.id = source_documents.company_id
              and c.is_active = true
        )
    );

create policy financial_facts_public_read
    on public.financial_facts
    for select
    to anon, authenticated
    using (
        quality_status = 'verified'
        and exists (
            select 1
            from public.companies c
            where c.id = financial_facts.company_id
              and c.is_active = true
        )
    );

create policy calculated_metrics_public_read
    on public.calculated_metrics
    for select
    to anon, authenticated
    using (
        exists (
            select 1
            from public.companies c
            where c.id = calculated_metrics.company_id
              and c.is_active = true
        )
    );

create policy red_flags_public_read
    on public.red_flags
    for select
    to anon, authenticated
    using (
        is_active = true
        and exists (
            select 1
            from public.companies c
            where c.id = red_flags.company_id
              and c.is_active = true
        )
    );

commit;
