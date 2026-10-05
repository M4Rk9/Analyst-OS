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

async function counts(db) {
  return (await db.query(`select (select count(*)::integer from public.ai_insights) as insights,
    (select count(*)::integer from insights.insight_provenance) as proofs,
    (select count(*)::integer from insights.load_receipts) as receipts,
    (select count(*)::integer from insights.publication_requests) as requests`)).rows[0];
}

test('reviewed AI publication is exact, provenanced, replay-safe and read-only to browsers', async () => {
  const db = await database();
  try {
    const {result} = await drive(db, 'all');
    assert.ok(!result.error, result.error);
    assert.equal(result.replayed, true);
    assert.deepEqual(await counts(db), {insights:1,proofs:1,receipts:1,requests:1});
    await db.exec('set role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.ai_insights')).rows[0].n,1);
    for (const sql of ['update public.ai_insights set title=title', 'delete from public.ai_insights',
      'insert into public.ai_insights default values', 'select * from insights.publication_requests']) {
      await assert.rejects(()=>db.exec(sql),/permission denied/);
    }
    await db.exec('reset role');
    await assert.rejects(()=>db.exec('delete from public.ai_insights'),/append-only/);
    await assert.rejects(()=>db.exec('delete from insights.insight_provenance'),/append-only/);
    await db.exec(`update public.financial_facts set quality_status='unverified',is_preferred=false;
      update public.source_documents set verification_status='pending'`);
    await db.exec('set role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.ai_insights')).rows[0].n,0);
  } finally {await db.close();}
});

for (const [scenario,pattern] of [['preview',null],['plan_changed',/plan hash/],
  ['schema_changed',/schema hash/],['source_changed',/unverified/],
  ['pending_guard',/explicit reviewer approval/],['quote_guard',/matching extracted quotation/]]) {
  test(`AI ${scenario} performs no AI inserts`, async()=>{
    const db=await database();
    try {
      const {result}=await drive(db,scenario);
      if(pattern) assert.match(result.error,pattern);
      else {assert.ok(!result.error,result.error);assert.equal(result.plan.production_writes,0);}
      assert.deepEqual(await counts(db),{insights:0,proofs:0,receipts:0,requests:0});
    } finally {await db.close();}
  });
}

test('AI receipt insert failure atomically rolls back rows, request and proofs',async()=>{
  const db=await database();
  try {
    const {result}=await drive(db,'all',async(_db,m)=>m.sql.includes('insert into insights.load_receipts'));
    assert.match(result.error,/injected failure/);
    assert.deepEqual(await counts(db),{insights:0,proofs:0,receipts:0,requests:0});
  } finally {await db.close();}
});

test('AI uncertain COMMIT recovers the durable receipt before same-request replay',async()=>{
  const db=await database();let lost=false;
  try {
    const {result}=await drive(db,'commit_unknown',async(database,m)=>{
      if(m.sql==='commit'&&!lost&&(await counts(db)).receipts===1){
        lost=true;await database.exec('commit');return true;
      }
      return false;
    });
    assert.ok(!result.error,result.error);assert.ok(lost);assert.equal(result.replayed,true);
    assert.deepEqual(await counts(db),{insights:1,proofs:1,receipts:1,requests:1});
  } finally {await db.close();}
});
async function drive(db, scenario, inject) {
  const child = spawn(process.env.PYTHON ?? 'python', ['-u', '-m', 'scripts.ai_test_driver', scenario],
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
