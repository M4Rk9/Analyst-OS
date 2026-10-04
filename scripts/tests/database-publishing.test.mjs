// Execute the real Python publisher and its parameterized SQL in ephemeral PostgreSQL.
// Only the transport/TLS observation is mocked; all SQL, constraints and commits are real.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFile, readdir } from 'node:fs/promises';
import { spawn, execFileSync } from 'node:child_process';
import { createInterface } from 'node:readline';
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';
const evidence = JSON.parse(execFileSync(process.env.PYTHON ?? 'python',
  ['-m', 'scripts.database_test_fixture'],
  { env: { ...process.env, PYTHONPATH: 'python' }, maxBuffer: 5 * 1024 * 1024 }).toString());

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
  const child = spawn(process.env.PYTHON ?? 'python', ['-u', '-m', 'scripts.publisher_test_driver', scenario],
    { env: { ...process.env, PYTHONPATH: 'python' }, stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '', result, insertStatements = 0;
  child.stderr.on('data', chunk => { stderr += chunk; });
  const lines = createInterface({ input: child.stdout });
  const closed = new Promise((resolve, reject) => {
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve() : reject(new Error(stderr)));
  });
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
  await closed;
  return { result, insertStatements };
}
async function counts(db) {
  return (await db.query(`select (select count(*)::integer from public.financial_facts) as facts,
    (select count(*)::integer from public.source_documents) as sources,
    (select count(*)::integer from ingestion.fact_provenance) as proofs,
    (select count(*)::integer from ingestion.load_receipts) as receipts`)).rows[0];
}

test('publisher loads all 376 candidates with atomic proof and one durable replay-safe receipt', async () => {
  const db = await database();
  try {
    const { result } = await drive(db, 'all');
    assert.ok(!result.error, result.error);
    assert.equal(result.inserted, 376);
    assert.equal(result.replayed, true);
    assert.deepEqual(await counts(db), { facts: 376, sources: 10, proofs: 376, receipts: 1 });
    await assert.rejects(() => db.exec('delete from ingestion.load_receipts'), /append-only/);
    await db.exec('set role anon');
    assert.equal((await db.query('select count(*)::integer as n from public.financial_facts')).rows[0].n, 376);
    await assert.rejects(() => db.query('select * from ingestion.load_receipts'), /permission denied/);
  } finally { await db.close(); }
});
for (const scenario of ['preview', 'pending']) {
  test(`${scenario} cannot insert anything`, async () => {
    const db = await database();
    try {
      const { result, insertStatements } = await drive(db, scenario);
      assert.ok(!result.error, result.error);
      assert.equal(result.writes, 0);
      assert.equal(insertStatements, 0);
      assert.deepEqual(await counts(db), { facts: 0, sources: 0, proofs: 0, receipts: 0 });
    } finally { await db.close(); }
  });
}
test('schema hash mismatch prevents inserts', async () => {
  const db = await database();
  try {
    const { result, insertStatements } = await drive(db, 'schema_mismatch');
    assert.match(result.error, /reviewed schema hash/);
    assert.equal(insertStatements, 0);
    assert.equal((await counts(db)).facts, 0);
  } finally { await db.close(); }
});
test('a late receipt failure rolls back facts, documents and proof together', async () => {
  const db = await database();
  try {
    const { result } = await drive(db, 'one', async (_db, m) =>
      m.sql.includes('insert into ingestion.load_receipts'));
    assert.match(result.error, /injected failure/);
    assert.deepEqual(await counts(db), { facts: 0, sources: 0, proofs: 0, receipts: 0 });
  } finally { await db.close(); }
});
test('lost COMMIT response reports uncertainty; durable receipt supports same-request recovery', async () => {
  const db = await database();
  let lost = false;
  try {
    const { result } = await drive(db, 'commit_unknown', async (database, m) => {
      if (m.sql === 'commit' && !lost) {
        lost = true;
        await database.exec('commit');
        return true;
      }
      return false;
    });
    assert.ok(!result.error, result.error);
    assert.equal(result.recovered, true);
    assert.deepEqual(await counts(db), { facts: 1, sources: 1, proofs: 1, receipts: 1 });
  } finally { await db.close(); }
});
test('disabled publication triggers fail schema audit', async () => {
  const db = await database();
  try {
    await db.exec('alter table public.financial_facts disable trigger facts_reviewed_publication');
    const { result } = await drive(db, 'one');
    assert.match(result.error, /disabled target integrity trigger/);
    assert.equal((await counts(db)).facts, 0);
  } finally { await db.close(); }
});
test('browser write grants fail schema audit', async () => {
  const db = await database();
  try {
    await db.exec('grant insert on public.financial_facts to anon');
    const { result } = await drive(db, 'one');
    assert.match(result.error, /unsafe table grants/);
    assert.equal((await counts(db)).facts, 0);
  } finally { await db.close(); }
});
test('a source committed after preview blocks the reviewed selection during the fresh check', async () => {
  const db = await database();
  let seeded = false;
  try {
    const { result } = await drive(db, 'one', async (database, m) => {
      if (m.sql === 'begin isolation level read committed read write' && !seeded) {
        seeded = true;
        const o = evidence.entries[0].observation;
        await database.query(`insert into public.source_documents
          (company_id,title,document_type,fiscal_year,source_url,publisher,sha256)
          select id,$1,$2,$3,$4,$5,$6 from public.companies where slug=$7`,
          [o.source_title,o.source_document_type,o.source_fiscal_year,o.source_url,
            o.source_publisher,o.source_sha256,o.company_slug]);
      }
      return false;
    });
    assert.match(result.error, /fresh target conflicts/);
    assert.deepEqual(await counts(db), { facts: 0, sources: 1, proofs: 0, receipts: 0 });
  } finally { await db.close(); }
});
test('post-insert verification failure rolls back the whole load', async () => {
  const db = await database();
  let altered = false;
  try {
    const { result } = await drive(db, 'one', async (database, m) => {
      if (m.sql === 'set constraints all immediate' && !altered) {
        altered = true;
        await database.exec("update public.financial_facts set quality_status='conflict',is_preferred=false");
      }
      return false;
    });
    assert.match(result.error, /post-insert verification failed/);
    assert.deepEqual(await counts(db), { facts: 0, sources: 0, proofs: 0, receipts: 0 });
  } finally { await db.close(); }
});
