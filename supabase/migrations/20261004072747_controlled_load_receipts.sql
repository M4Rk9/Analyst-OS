begin;
create table ingestion.load_receipts (
    import_id uuid primary key,
    request_sha256 text not null unique check (request_sha256 ~ '^[0-9a-f]{64}$'),
    project_ref text not null check (project_ref ~ '^[a-z0-9]{20}$'),
    receipt_sha256 text not null check (receipt_sha256 ~ '^[0-9a-f]{64}$'),
    canonical_json text not null,
    payload jsonb generated always as (canonical_json::jsonb) stored,
    recorded_at timestamptz not null default now(),
    check (receipt_sha256 = encode(sha256(convert_to(canonical_json, 'UTF8')), 'hex')),
    check ((payload->>'import_id' = import_id::text
        and payload->>'request_sha256' = request_sha256
        and payload->>'project_ref' = project_ref
        and payload->>'outcome' = 'committed'
        and jsonb_typeof(payload->'inserted') = 'array'
        and jsonb_typeof(payload->'already_present') = 'array') is true)
);
alter table ingestion.load_receipts enable row level security;
revoke all on table ingestion.load_receipts from public, anon, authenticated, service_role;
grant select, insert on table ingestion.load_receipts to service_role;
create trigger load_receipts_immutable before update or delete on ingestion.load_receipts
    for each row execute function ingestion.immutable_evidence();
comment on table ingestion.load_receipts is
    'Atomic load audit. Visible to a different transaction only after facts/provenance commit. No credentials.';
commit;
