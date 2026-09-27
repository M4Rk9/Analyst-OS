begin;

create table public.ai_insights (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id) on delete cascade,
    source_document_id uuid not null references public.source_documents(id) on delete restrict,
    section text not null check (
        section in ('business_brief', 'financial_changes', 'positives', 'risks', 'management_outlook')
    ),
    title text not null check (length(title) between 1 and 160),
    insight_text text not null check (length(insight_text) between 1 and 1800),
    confidence text not null check (confidence in ('low', 'medium', 'high')),
    source_page integer not null check (source_page > 0),
    source_section text check (source_section is null or length(source_section) <= 160),
    model_name text not null check (length(model_name) between 1 and 120),
    prompt_version text not null default '1.0' check (length(prompt_version) between 1 and 40),
    validation_status text not null default 'validated' check (
        validation_status in ('validated', 'rejected')
    ),
    generated_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    unique (
        company_id,
        source_document_id,
        section,
        source_page,
        title,
        model_name,
        prompt_version
    )
);

create index ai_insights_company_section_idx
    on public.ai_insights (company_id, section, generated_at desc);

alter table public.ai_insights enable row level security;
revoke all on table public.ai_insights from anon, authenticated;
grant select on table public.ai_insights to anon, authenticated;

create policy "public_read_validated_ai_insights"
on public.ai_insights
for select
to anon, authenticated
using (validation_status = 'validated');

comment on table public.ai_insights is
    'Validated local-Ollama interpretations with primary-source page provenance.';

commit;
