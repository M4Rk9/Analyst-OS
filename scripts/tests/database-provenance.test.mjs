// Real PostgreSQL in memory; no Supabase credentials or target writes.
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { execFileSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';

const db = new PGlite({ extensions: { pgcrypto } });
const hash = (text) => createHash('sha256').update(text, 'utf8').digest('hex');
const fixture = JSON.parse(execFileSync(process.env.PYTHON ?? 'python',
  ['-m', 'scripts.database_test_fixture'], {
    env: { ...process.env, PYTHONPATH: 'python' }, maxBuffer: 5 * 1024 * 1024,
  }).toString());
const snapshotStatements = JSON.parse(execFileSync(process.env.PYTHON ?? 'python', ['-c',
  'import json; from analyst_os_ingestion.snapshot import QUERIES,MEASURE_QUERIES,CONTEXT_SQL; print(json.dumps({"rows":QUERIES,"measures":MEASURE_QUERIES,"context":CONTEXT_SQL}))'],
  { env: { ...process.env, PYTHONPATH: 'python' } }).toString());
const snapshotSQL = snapshotStatements.rows;
const entry = fixture.entries.find(e => e.observation.company_slug === 'tcs'
  && e.observation.metric_code === 'revenue' && e.observation.fiscal_year === 2022);
const migrationPaths = (await readdir('supabase/migrations')).filter(p => p.endsWith('.sql')).sort();
const provenanceMigration = await readFile(`supabase/migrations/${migrationPaths.find(p => p.endsWith('_reviewed_provenance.sql'))}`, 'utf8');
async function baseSchema(database) {
  await database.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    grant usage on schema public to service_role;
    alter default privileges in schema public grant all on tables to service_role;`);
  for (const path of migrationPaths.filter(p => p.startsWith('000'))) {
    await database.exec(await readFile(`supabase/migrations/${path}`, 'utf8'));
  }
}

async function rollback(callback) {
  await db.exec('begin');
  try { await callback(); } finally { await db.exec('rollback'); }
}
async function rejects(callback, pattern) {
  await assert.rejects(callback, pattern);
}
async function ledger(value) {
  const text = JSON.stringify(value);
  const sha = hash(text);
  await db.query(`insert into ingestion.review_ledgers
    (review_ledger_sha256,catalog_sha256,canonical_json) values ($1,$2,$3)`,
    [sha, fixture.catalog_sha256, text]);
  return sha;
}
async function stage(e = entry, options = {}) {
  const o = e.observation;
  const company = (await db.query('select id from public.companies where slug=$1',
    [o.company_slug])).rows[0].id;
  const existingPeriod = options.reuse ? (await db.query(`select id from public.reporting_periods
    where company_id=$1 and period_type=$2 and fiscal_year=$3 and period_end=$4`,
    [company, o.period_type, o.fiscal_year, o.period_end])).rows[0] : null;
  const existingSource = options.reuse ? (await db.query(`select id from public.source_documents
    where company_id=$1 and source_url=$2`, [company, o.source_url])).rows[0] : null;
  const periodId = existingPeriod?.id ?? randomUUID();
  const sourceId = existingSource?.id ?? randomUUID();
  const factId = randomUUID();
  if (!existingPeriod) await db.query(`insert into public.reporting_periods
    (id,company_id,period_type,fiscal_year,period_start,period_end,currency)
    values ($1,$2,$3,$4,$5,$6,$7)`,
    [periodId, company, o.period_type, o.fiscal_year, o.period_start, o.period_end, o.currency]);
  if (!existingSource) await db.query(`insert into public.source_documents
    (id,company_id,title,document_type,fiscal_year,source_url,publisher,sha256,page_count,verification_status)
    values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
    [sourceId, company, o.source_title, o.source_document_type, o.source_fiscal_year,
      o.source_url, o.source_publisher, o.source_sha256,
      JSON.parse(fixture.catalog_canonical_json).source_manifest.find(m => m.sha256 === o.source_sha256).page_count,
      options.sourceStatus ?? 'verified']);
  await db.query(`insert into public.financial_facts
    (id,company_id,reporting_period_id,metric_code,raw_value_text,raw_value,normalized_value,
     currency,unit_scale,source_document_id,source_page,source_label,quality_status,is_preferred)
    values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)`,
    [factId, company, periodId, o.metric_code, o.raw_value_text, o.raw_value, o.normalized_value,
      o.currency, o.unit_scale, sourceId, o.source_page, o.source_label,
      options.factStatus ?? 'verified', options.preferred ?? true]);
  if (options.proof !== false) {
    const review = options.review ?? fixture.review_ledger_sha256;
    await db.query(`insert into ingestion.source_provenance values ($1,$2,$3) on conflict do nothing`,
      [sourceId, fixture.catalog_sha256, review]);
    await db.query(`insert into ingestion.fact_provenance
      (fact_id,source_document_id,catalog_sha256,review_ledger_sha256,observation_id,
       evidence_sha256,definition_sha256,evidence_canonical_json,definition_canonical_json)
      values ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
      [factId, sourceId, fixture.catalog_sha256, review, o.observation_id,
        e.evidence_sha256, e.definition_sha256, e.evidence_canonical_json, e.definition_canonical_json]);
  }
  return { company, periodId, sourceId, factId };
}

before(async () => {
  await baseSchema(db);
  // Deliberately exercise upgrade of a legacy implicit verification assertion.
  await db.exec(`insert into public.reporting_periods (id,company_id,period_type,fiscal_year,period_start,period_end,currency)
    select '00000000-0000-0000-0000-000000000001',id,'FY',2000,'1999-04-01','2000-03-31','INR'
    from public.companies where slug='tcs';
    insert into public.source_documents (id,company_id,title,document_type,source_url,publisher,verification_status)
    select '00000000-0000-0000-0000-000000000002',id,'Legacy test fixture','annual_report','https://example.invalid/legacy','TEST ONLY','verified'
    from public.companies where slug='tcs';
    insert into public.financial_facts (id,company_id,reporting_period_id,metric_code,raw_value,normalized_value,source_document_id,is_preferred)
    select '00000000-0000-0000-0000-000000000003',id,'00000000-0000-0000-0000-000000000001',
      'legacy_test',1,1,'00000000-0000-0000-0000-000000000002',true
    from public.companies where slug='tcs';`);
  for (const path of migrationPaths.filter(p => !p.startsWith('000'))) {
    await db.exec(await readFile(`supabase/migrations/${path}`, 'utf8'));
  }
  await db.query('insert into ingestion.evidence_catalogs (catalog_sha256,canonical_json) values ($1,$2)',
    [fixture.catalog_sha256, fixture.catalog_canonical_json]);
  await db.query(`insert into ingestion.review_ledgers
    (review_ledger_sha256,catalog_sha256,canonical_json) values ($1,$2,$3)`,
    [fixture.review_ledger_sha256, fixture.catalog_sha256, fixture.review_canonical_json]);
});
after(async () => { await db.close(); });

test('legacy assertions become unavailable, without changing amounts', async () => {
  const row = (await db.query("select quality_status,is_preferred,raw_value::text,normalized_value::text from public.financial_facts where metric_code='legacy_test'")).rows[0];
  assert.deepEqual(row, { quality_status: 'unverified', is_preferred: false, raw_value: '1', normalized_value: '1' });
  assert.equal((await db.query('select verification_status from public.source_documents')).rows[0].verification_status, 'pending');
});
test('private proof tables have RLS and no browser grants or definer functions', async () => {
  const rows = (await db.query(`select c.relname,c.relrowsecurity,
    has_table_privilege('anon',c.oid,'SELECT') as anon_read,
    has_table_privilege('authenticated',c.oid,'INSERT') as browser_write
    from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='ingestion' and c.relkind='r'`)).rows;
  assert.equal(rows.length, 4);
  for (const row of rows) assert.ok(row.relrowsecurity && !row.anon_read && !row.browser_write);
  const funcs = (await db.query(`select p.prosecdef,has_function_privilege('anon',p.oid,'EXECUTE') as callable
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='ingestion'`)).rows;
  assert.ok(funcs.length >= 5);
  for (const row of funcs) assert.ok(!row.prosecdef && !row.callable);
});
test('a real reviewed candidate can be staged with proof and read by browser roles', async () => {
  await rollback(async () => {
    await db.exec('set local role service_role');
    const ids = await stage();
    await db.exec('set constraints all immediate; reset role; set local role anon');
    assert.equal((await db.query('select id from public.financial_facts')).rows[0].id, ids.factId);
    await db.exec('set local role authenticated');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 1);
  });
});
test('a commit without any approved proof rolls back', async () => {
  await db.exec('begin');
  try {
    await stage(entry, { proof: false });
    await rejects(() => db.exec('commit'), /lacks matching approved provenance/);
  } finally { await db.exec('rollback'); }
  assert.equal((await db.query("select count(*)::integer as n from public.financial_facts where metric_code='revenue'")).rows[0].n, 0);
});
test('all 376 candidate observations preserve P&L, instant BS and duration CF semantics', async () => {
  await rollback(async () => {
    await db.exec('set local role service_role');
    for (const e of fixture.entries.slice(0, fixture.candidate_count)) {
      await stage(e, { reuse: true });
    }
    await db.exec('set constraints all immediate');
    const counts = (await db.query(`select observation->>'measurement_type' as kind,count(*)::integer as n
      from ingestion.fact_provenance group by kind`)).rows;
    assert.ok(counts.find(c => c.kind === 'instant' && c.n > 0));
    assert.ok(counts.find(c => c.kind === 'duration' && c.n > 0));
    await db.exec('reset role; set local role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 376);
    assert.equal((await db.query('select count(*)::integer as n from public.source_documents')).rows[0].n, 10);
  });
});
test('snapshot SQL includes all scoped quality states and round-trips through the Python planner', async () => {
  await rollback(async () => {
    // The legacy fixture has no proof: omit its company by selecting RIL only.
    await db.exec('set local role service_role');
    const ril = fixture.entries.slice(0, fixture.candidate_count)
      .filter(e => e.observation.company_slug === 'reliance-industries');
    for (const e of ril) await stage(e, { reuse: true, sourceStatus: 'pending',
      factStatus: 'unverified', preferred: false });
    await db.exec('set constraints all immediate');
    const scope = ['reliance-industries'];
    const rows = {};
    for (const [name, query] of Object.entries(snapshotSQL)) {
      rows[name] = (await db.query(query.replace('%s', '$1') + ' limit $2', [scope, 10001])).rows;
      const measured = (await db.query(snapshotStatements.measures[name]
        .replace('%s', '$1').replace('%s', '$2'), [scope, 10001])).rows[0];
      assert.equal(measured.row_count, rows[name].length);
      assert.ok(Number(measured.byte_count) < 5 * 1024 * 1024);
    }
    assert.equal(rows.facts.length, ril.length);
    assert.ok(rows.facts.every(f => f.quality_status === 'unverified' && !f.is_preferred));
    const result = JSON.parse(execFileSync(process.env.PYTHON ?? 'python', ['-c',
      `import json,sys; from analyst_os_ingestion.snapshot import build_snapshot
from analyst_os_ingestion.planning import TargetSnapshot,digest
rows=json.load(sys.stdin)
target=build_snapshot(rows,project_ref='abcdefghijklmnopqrst',scope=['reliance-industries'],captured_at='2026-10-04T07:00:00Z')
payload=target.model_dump(mode='json'); TargetSnapshot.model_validate(payload)
print(json.dumps({'facts':len(target.facts),'sources':len(target.sources),'digest':digest(payload)}))`],
      { input: JSON.stringify(rows), env: { ...process.env, PYTHONPATH: 'python' },
        maxBuffer: 5 * 1024 * 1024 }).toString());
    assert.equal(result.facts, ril.length);
    assert.equal(result.sources, 5);
    assert.match(result.digest, /^[0-9a-f]{64}$/);
    await db.exec('reset role; set local role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 0);
  });
});
test('snapshot SQL reads are permitted and writes rejected in a read-only transaction', async () => {
  await db.exec('begin isolation level repeatable read read only; set local role service_role; set local row_security=off');
  try {
    const context = (await db.query(snapshotStatements.context)).rows[0];
    assert.equal(context.read_only, 'on');
    assert.equal(context.isolation, 'repeatable read');
    assert.equal(context.row_security, 'off');
    assert.equal(context.privileged, true);
    for (const query of Object.values(snapshotSQL)) {
      await db.query(query.replace('%s', '$1') + ' limit $2', [['reliance-industries', 'tcs'], 10001]);
    }
    await rejects(() => db.exec('update public.financial_facts set id=id'), /read-only transaction/);
  } finally { await db.exec('rollback'); }
});
for (const status of ['pending', 'rejected']) {
  for (const scope of ['sources', 'facts']) {
    test(`${status} ${scope} review cannot publish`, async () => {
      await rollback(async () => {
        const value = JSON.parse(fixture.review_canonical_json);
        const key = scope === 'sources' ? entry.source_key : entry.observation.observation_id;
        value[scope][key].status = status;
        await stage(entry, { review: await ledger(value) });
        await rejects(() => db.exec('set constraints all immediate'), /lacks matching/);
      });
    });
  }
}
test('all six withheld conflicts reject even synthetic approvals', async () => {
  assert.equal(fixture.entries.length - fixture.candidate_count, 6);
  for (const e of fixture.entries.slice(fixture.candidate_count)) {
    await rollback(async () => {
      await stage(e);
      await rejects(() => db.exec('set constraints all immediate'), /conflict-free approved provenance/);
    });
  }
});
test('default facts stay unverified and invisible', async () => {
  await rollback(async () => {
    const ids = await stage(entry, { proof: false, sourceStatus: 'pending', factStatus: 'unverified', preferred: false });
    await db.query('update public.financial_facts set quality_status=default where id=$1', [ids.factId]);
    await db.exec('set constraints all immediate');
    assert.equal((await db.query('select quality_status from public.financial_facts where id=$1', [ids.factId])).rows[0].quality_status, 'unverified');
    await db.exec('set local role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 0);
  });
});
for (const role of ['anon', 'authenticated']) {
  test(`${role} cannot read private reviews or write public facts`, async () => {
    await rollback(async () => {
      await db.exec(`set local role ${role}`);
      await rejects(() => db.query('select * from ingestion.review_ledgers'), /permission denied/);
    });
    await rollback(async () => {
      await db.exec(`set local role ${role}`);
      await rejects(() => db.exec("update public.financial_facts set raw_value=2"), /permission denied/);
    });
  });
  test(`${role} INSERT/UPDATE/DELETE is denied on every exposed table`, async () => {
    for (const table of ['companies', 'reporting_periods', 'source_documents', 'financial_facts',
      'calculated_metrics', 'red_flags', 'ai_insights']) {
      for (const sql of [`insert into public.${table} default values`,
        `update public.${table} set id=id`, `delete from public.${table}`]) {
        await rollback(async () => {
          await db.exec(`set local role ${role}`);
          await rejects(() => db.exec(sql), /permission denied/);
        });
      }
    }
  });
}
test('hash mismatch cannot masquerade as the Python catalog', async () => {
  await rollback(async () => {
    await rejects(() => db.query('insert into ingestion.evidence_catalogs (catalog_sha256,canonical_json) values ($1,$2)',
      ['0'.repeat(64), fixture.catalog_canonical_json]), /check constraint/);
  });
});
test('evidence and definition hashes survive storage byte-for-byte', async () => {
  await rollback(async () => {
    await stage();
    const p = (await db.query('select * from ingestion.fact_provenance')).rows[0];
    assert.equal(hash(p.evidence_canonical_json), entry.evidence_sha256);
    assert.equal(hash(p.definition_canonical_json), entry.definition_sha256);
    assert.deepEqual(p.observation, entry.observation);
    assert.deepEqual(p.definition, entry.definition);
    await db.exec('set constraints all immediate');
  });
});
for (const update of [
  'normalized_value=normalized_value+1', 'unit_scale=1',
  "raw_value='NaN',normalized_value='NaN'", "unit_scale='Infinity',normalized_value='Infinity'",
  "currency='USD'", 'source_page=source_page+1', "source_label='changed'",
  "raw_value_text='changed'", "metric_code='other_metric'",
]) {
  test(`changed fact ${update} is rejected`, async () => {
    await rollback(async () => {
      const ids = await stage();
      await rejects(async () => {
        await db.query(`update public.financial_facts set ${update} where id=$1`, [ids.factId]);
        await db.exec('set constraints all immediate');
      }, /constraint|lacks matching/);
    });
  });
}
for (const patch of [{ reporting_basis: 'standalone' }, { measurement_type: 'instant' },
  { as_of: '2022-03-31' }, { extraction_correction: 'altered after review' }]) {
  test(`altered companion evidence ${JSON.stringify(patch)} fails`, async () => {
    await rollback(async () => {
      const modified = structuredClone(entry);
      Object.assign(modified.observation, patch);
      modified.evidence_canonical_json = JSON.stringify(modified.observation);
      modified.evidence_sha256 = hash(modified.evidence_canonical_json);
      await stage(modified);
      await rejects(() => db.exec('set constraints all immediate'), /approved provenance/);
    });
  });
}
test('a changed definition cannot reuse an approved catalog', async () => {
  await rollback(async () => {
    const modified = structuredClone(entry);
    modified.definition.definition = 'Different measurement scope';
    modified.definition_canonical_json = JSON.stringify(modified.definition);
    modified.definition_sha256 = hash(modified.definition_canonical_json);
    await stage(modified);
    await rejects(() => db.exec('set constraints all immediate'), /approved provenance/);
  });
});
test('dropping a companion field cannot pass subset matching', async () => {
  await rollback(async () => {
    const modified = structuredClone(entry);
    delete modified.observation.printed_pages;
    modified.evidence_canonical_json = JSON.stringify(modified.observation);
    modified.evidence_sha256 = hash(modified.evidence_canonical_json);
    await stage(modified);
    await rejects(() => db.exec('set constraints all immediate'), /approved provenance/);
  });
});
for (const update of ["verification_status='pending'", "sha256=repeat('0',64)", "title='changed'", 'page_count=1', "published_at='2022-05-01'"]) {
  test(`source mutation ${update} cannot invalidate a published fact`, async () => {
    await rollback(async () => {
      const ids = await stage();
      await db.query(`update public.source_documents set ${update} where id=$1`, [ids.sourceId]);
      await rejects(() => db.exec('set constraints all immediate'), /verified source|approved provenance/);
    });
  });
}
test('a source and its facts can be demoted atomically', async () => {
  await rollback(async () => {
    const ids = await stage();
    await db.query("update public.source_documents set verification_status='pending' where id=$1", [ids.sourceId]);
    await db.query("update public.financial_facts set quality_status='unverified',is_preferred=false where id=$1", [ids.factId]);
    await db.exec('set constraints all immediate; set local role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 0);
  });
});
test('cross-company period/source references fail', async () => {
  for (const field of ['source_document_id', 'reporting_period_id']) {
    await rollback(async () => {
      const ids = await stage();
      const table = field === 'source_document_id' ? 'source_documents' : 'reporting_periods';
      await rejects(async () => {
        await db.query(`update public.${table} set company_id=(select id from public.companies where slug='hdfc-bank') where id=$1`,
          [field === 'source_document_id' ? ids.sourceId : ids.periodId]);
      }, /foreign key constraint/);
    });
  }
});
test('period and company identity changes recheck provenance', async () => {
  for (const sql of ["update public.reporting_periods set period_start='2021-04-02' where fiscal_year=2022",
    "update public.companies set slug='changed-tcs' where slug='tcs'"]) {
    await rollback(async () => {
      await stage();
      await db.exec(sql);
      await rejects(() => db.exec('set constraints all immediate'), /approved provenance/);
    });
  }
});
test('only one preferred fact for a company/period/metric', async () => {
  await rollback(async () => {
    const ids = await stage();
    await rejects(() => db.query(`insert into public.financial_facts
      (company_id,reporting_period_id,metric_code,raw_value,normalized_value,unit_scale,source_document_id,quality_status,is_preferred)
      select company_id,reporting_period_id,metric_code,raw_value,normalized_value,unit_scale,
        '00000000-0000-0000-0000-000000000002','verified',true
      from public.financial_facts where id=$1`, [ids.factId]), /financial_facts_one_preferred/);
  });
});
test('proof is retained; reviews cannot be edited or deleted', async () => {
  for (const sql of ['delete from ingestion.review_ledgers',
    "update ingestion.evidence_catalogs set canonical_json=canonical_json",
    'delete from ingestion.fact_provenance', 'delete from ingestion.source_provenance']) {
    await rollback(async () => {
      await stage();
      await rejects(() => db.exec(sql), /append-only/);
    });
  }
});
for (const patch of [{ reviewer: ' ' }, { reviewer: '\t\n' }, { rationale: '' }, { reviewed_at: '2999-01-01T00:00:00Z' },
  { reviewed_at: '2020-01-01T00:00:00' }, { reviewed_at: 'invalidZ' }]) {
  test(`invalid review attestation ${JSON.stringify(patch)} fails closed`, async () => {
    await rollback(async () => {
      const value = JSON.parse(fixture.review_canonical_json);
      Object.assign(value.facts[entry.observation.observation_id], patch);
      await stage(entry, { review: await ledger(value) });
      await rejects(() => db.exec('set constraints all immediate'), /approved provenance/);
    });
  });
}
test('the privileged preflight is read-only and reports legacy counts', async () => {
  const beforeCount = (await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n;
  const results = await db.exec(await readFile('supabase/preflight_reviewed_provenance.sql', 'utf8'));
  const normalization = results.find(r => r.rows[0]?.invalid_normalization_or_nonfinite_values !== undefined);
  assert.equal(Number(normalization.rows[0].invalid_normalization_or_nonfinite_values), 0);
  assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, beforeCount);
});
test('legacy derived outputs block migration before any demotion', async () => {
  const legacyDb = new PGlite({ extensions: { pgcrypto } });
  try {
    await baseSchema(legacyDb);
    await legacyDb.exec(`insert into public.reporting_periods
      (company_id,period_type,fiscal_year,period_start,period_end,currency)
      select id,'FY',2000,'1999-04-01','2000-03-31','INR' from public.companies where slug='tcs';
      insert into public.source_documents
      (company_id,title,document_type,source_url,publisher,verification_status)
      select id,'TEST ONLY legacy source','annual_report','https://example.invalid/test','TEST ONLY','verified'
      from public.companies where slug='tcs';
      insert into public.calculated_metrics
      (company_id,reporting_period_id,metric_code,value,unit,formula_version)
      select company_id,id,'test_metric',1,'TEST ONLY','test' from public.reporting_periods;`);
    await rejects(() => legacyDb.exec(provenanceMigration), /review existing calculated_metrics\/red_flags/);
    await legacyDb.exec('rollback');
    assert.equal((await legacyDb.query('select verification_status from public.source_documents')).rows[0].verification_status, 'verified');
    assert.equal((await legacyDb.query("select to_regnamespace('ingestion') as schema")).rows[0].schema, null);
  } finally { await legacyDb.close(); }
});
test('invalid legacy normalization rolls back the migration instead of repairing values', async () => {
  const legacyDb = new PGlite({ extensions: { pgcrypto } });
  try {
    await baseSchema(legacyDb);
    await legacyDb.exec(`insert into public.reporting_periods
      (company_id,period_type,fiscal_year,period_start,period_end,currency)
      select id,'FY',2000,'1999-04-01','2000-03-31','INR' from public.companies where slug='tcs';
      insert into public.source_documents
      (company_id,title,document_type,source_url,publisher,verification_status)
      select id,'TEST ONLY legacy source','annual_report','https://example.invalid/test','TEST ONLY','verified'
      from public.companies where slug='tcs';
      insert into public.financial_facts
      (company_id,reporting_period_id,metric_code,raw_value,normalized_value,source_document_id)
      select p.company_id,p.id,'test_metric',1,2,s.id
      from public.reporting_periods p join public.source_documents s using (company_id);`);
    await rejects(() => legacyDb.exec(provenanceMigration), /facts_exact_normalization/);
    await legacyDb.exec('rollback');
    const row = (await legacyDb.query('select quality_status,raw_value::text,normalized_value::text from public.financial_facts')).rows[0];
    assert.deepEqual(row, { quality_status: 'verified', raw_value: '1', normalized_value: '2' });
    assert.equal((await legacyDb.query("select to_regnamespace('ingestion') as schema")).rows[0].schema, null);
  } finally { await legacyDb.close(); }
});
