// Real deterministic publication SQL and transactions; synthetic transport only.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFile, readdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';
async function database() {
  const db = new PGlite({ extensions: { pgcrypto } });
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    grant usage on schema public to service_role;
    alter default privileges in schema public grant all on tables to service_role;`);
  for (const file of (await readdir('supabase/migrations')).filter(p => p.endsWith('.sql')).sort()) {
    await db.exec(await readFile(`supabase/migrations/${file}`, 'utf8'));
  }
  return db;
}
async function drive(db, scenario, inject) {
  const child = spawn(process.env.PYTHON ?? 'python', ['-u', '-m', 'scripts.analytics_test_driver', scenario],
    { env: { ...process.env, PYTHONPATH: 'python' }, stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '', result, insertStatements = 0;
  child.stderr.on('data', chunk => { stderr += chunk; });
  const lines = createInterface({ input: child.stdout });
  const closed = new Promise(resolve => {
    child.on('error', error => resolve({ error }));
    child.on('close', code => resolve({ code }));
  });
  const timeout = setTimeout(() => child.kill(), 180_000);
  try {
    for await (const line of lines) {
      const message = JSON.parse(line);
      if (message.result) { result = message.result; continue; }
      let sql = message.sql, index = 0;
      if (/^\s*insert\b/i.test(sql)) insertStatements++;
      sql = sql.replace(/%s/g, () => `$${++index}`);
      try {
        if (inject && await inject(db, message)) throw Error('TEST ONLY injected failure');
        let rows;
        if (message.params == null) rows = (await db.exec(sql))[0]?.rows ?? [];
        else rows = (await db.query(sql, message.params)).rows;
        // PGlite has no TLS transport. Unit tests separately require actual SSL=true.
        if (sql.includes("current_setting('transaction_read_only')")) rows[0].ssl = true;
        child.stdin.write(JSON.stringify({ rows }) + '\n');
      } catch (error) {
        child.stdin.write(JSON.stringify({ error: error.message }) + '\n');
      }
    }
    const exit = await closed;
    if (exit.error) throw exit.error;
    if (exit.code !== 0) throw new Error(stderr || `Publisher exited with code ${exit.code}`);
    return { result, insertStatements };
  } finally {
    clearTimeout(timeout);
    lines.close();
    child.stdin.destroy();
    if (child.exitCode === null && child.signalCode === null) child.kill();
    await closed;
  }
}

async function counts(db) {
  return (await db.query(`select (select count(*)::integer from public.financial_facts) as facts,
    (select count(*)::integer from public.calculated_metrics) as metrics,
    (select count(*)::integer from public.red_flags) as flags,
    (select count(*)::integer from analytics.load_receipts) as receipts,
    (select count(*)::integer from analytics.metric_provenance) as proofs`)).rows[0];
}

test('629 reviewed facts produce 43 provenanced metrics, supported signals and one replay-safe receipt', async () => {
  const db = await database();
  try {
    const { result } = await drive(db, 'all');
    assert.ok(!result.error, result.error);
    assert.equal(result.metrics, 43);
    assert.equal(result.unavailable, 32);
    assert.equal(result.replayed, true);
    assert.equal(result.flags, 1);
    assert.deepEqual(await counts(db), { facts: 629, metrics: 43, flags: result.flags, receipts: 1, proofs: 43 });
    assert.equal((await db.query(`select count(*)::integer as n from public.calculated_metrics m
      join public.reporting_periods p on p.id=m.reporting_period_id join public.companies c on c.id=m.company_id
      where (c.slug='tata-motors' and p.fiscal_year=2024) or (c.slug='hdfc-bank' and m.metric_code<>'cfo_to_reported_group_profit')`)).rows[0].n, 0);
    await assert.rejects(() => db.exec('update public.calculated_metrics set value=value+1'), /append-only/);
    await assert.rejects(() => db.exec('delete from public.red_flags'), /append-only/);
    await assert.rejects(() => db.exec('delete from analytics.metric_provenance'), /append-only/);
    // Missing provenance and arbitrary formulas cannot become public even for a privileged writer.
    await assert.rejects(() => db.exec(`insert into public.calculated_metrics
      (company_id,reporting_period_id,metric_code,value,unit,formula_version,input_facts)
      select p.company_id,p.id,'current_ratio',999,'ratio','1.0',m.input_facts
      from public.reporting_periods p cross join public.calculated_metrics m
      where p.company_id=(select id from public.companies where slug='hdfc-bank') limit 1`), /reviewed input contract/);
    assert.equal((await db.query(`select bool_and(not public.reported_metric_is_valid(
      jsonb_populate_record(null::public.calculated_metrics,to_jsonb(m)||'{"value":999}'::jsonb))) as rejected
      from public.calculated_metrics m`)).rows[0].rejected, true);
    assert.equal((await db.query(`select bool_and(not public.reported_flag_is_valid(
      jsonb_populate_record(null::public.red_flags,to_jsonb(f)||'{"title":"Buy this company"}'::jsonb))) as rejected
      from public.red_flags f`)).rows[0].rejected, true);
    await db.exec('set role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.calculated_metrics')).rows[0].n, 43);
    assert.equal((await db.query('select count(*)::integer as n from public.red_flags')).rows[0].n, result.flags);
    await assert.rejects(() => db.exec('select * from analytics.load_receipts'), /permission denied/);
    await assert.rejects(() => db.exec('delete from public.calculated_metrics'), /permission denied/);
    await db.exec('reset role');
    // Visibility follows current verified preferred evidence, not stale computed status.
    await db.exec(`update public.financial_facts set quality_status='conflict',is_preferred=false
      where id=(select (input_facts->0->>'fact_id')::uuid from public.calculated_metrics
        where metric_code='cfo_to_reported_group_profit' and value<0.7 limit 1)`);
    await db.exec('set role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.calculated_metrics')).rows[0].n, 42);
    assert.equal((await db.query('select count(*)::integer as n from public.red_flags')).rows[0].n, result.flags-1);
  } finally { await db.close(); }
});

for (const scenario of ['preview', 'preview_tamper', 'schema_mismatch']) {
  test(`${scenario} cannot insert derived rows`, async () => {
    const db = await database();
    try {
      const { result } = await drive(db, scenario);
      if (scenario === 'preview') {
        assert.ok(!result.error, result.error);
        assert.equal(result.plan.metrics_to_insert.length, 43);
        assert.equal(result.plan.production_writes, 0);
      } else assert.match(result.error, scenario === 'preview_tamper' ? /does not match/ : /reviewed schema hash/);
      assert.deepEqual(await counts(db), { facts: 629, metrics: 0, flags: 0, receipts: 0, proofs: 0 });
    } finally { await db.close(); }
  });
}

test('a late receipt failure rolls back all metrics, flags, contracts and proofs', async () => {
  const db = await database();
  try {
    const { result } = await drive(db, 'all', async (_db, m) => m.sql.includes('insert into analytics.load_receipts'));
    assert.match(result.error, /injected failure/);
    assert.deepEqual(await counts(db), { facts: 629, metrics: 0, flags: 0, receipts: 0, proofs: 0 });
    assert.equal((await db.query('select count(*)::integer as n from analytics.publication_requests')).rows[0].n, 0);
  } finally { await db.close(); }
});

test('uncertain analytics COMMIT is recovered using the durable receipt and same request', async () => {
  const db = await database();
  let lost = false;
  try {
    const { result } = await drive(db, 'commit_unknown', async (database, m) => {
      if (m.sql==='commit' && !lost && (await database.query('select count(*)::integer as n from analytics.load_receipts')).rows[0].n === 1) {
        lost=true; await database.exec('commit'); return true;
      }
      return false;
    });
    assert.ok(!result.error, result.error);
    assert.equal(lost, true);
    assert.equal(result.metrics, 43);
    assert.equal(result.replayed, true);
    assert.equal((await counts(db)).receipts, 1);
  } finally { await db.close(); }
});

test('database quotient matches 28 significant digits and half-even ties', async () => {
  const db = await database();
  try {
    for (const [n,d,expected] of [
      ['1','3','0.3333333333333333333333333333'], ['-1','3','-0.3333333333333333333333333333'],
      ['12345678901234567890123456785','10','1234567890123456789012345678'],
      ['12345678901234567890123456795','10','1234567890123456789012345680'],
      ['0','1','0'], ['1','0',null], ['1','-1',null],
    ]) {
      assert.equal((await db.query('select public.reported_decimal_quotient($1::numeric,$2::numeric) is not distinct from $3::numeric as valid',
        [n,d,expected])).rows[0].valid, true);
    }
  } finally { await db.close(); }
});

test('a source fact changed after dry run prevents any derived publication', async () => {
  const db = await database();
  let ready = false, changed = false;
  try {
    const { result } = await drive(db, 'all', async (database,m) => {
      if (m.sql.includes('n.nspname=\'public\' and p.proname=any')) ready=true;
      if (ready && !changed && m.sql==='begin isolation level read committed read write') {
        changed=true;
        await database.exec(`update public.financial_facts set quality_status='conflict',is_preferred=false
          where id=(select id from public.financial_facts limit 1)`);
      }
      return false;
    });
    assert.ok(changed);
    assert.match(result.error, /approved inputs|reviewed analytics inputs/);
    assert.equal((await counts(db)).metrics, 0);
    assert.equal((await counts(db)).receipts, 0);
  } finally { await db.close(); }
});
