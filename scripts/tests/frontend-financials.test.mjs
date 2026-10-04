import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const context = vm.createContext({ window: {}, document: { addEventListener() {} } });
vm.runInContext(await readFile('web/js/financial-display.js', 'utf8'), context);
vm.runInContext(await readFile('web/js/company.js', 'utf8'), context);
const display = context.window.AnalystFinancialDisplay;
const entry = (year, value) => ({ period: { fiscal_year: year, period_type: 'FY' }, value });

test('missing, blank, nonnumeric and nonfinite values stay unavailable', () => {
  for (const value of [null, undefined, '', '  ', '-', true, {}, Infinity, 'NaN', '0x10']) {
    assert.equal(display.numberValue(value), null);
  }
  assert.equal(display.numberValue('0'), 0);
  assert.equal(display.numberValue('-42'), -42);
  assert.equal(vm.runInContext('formatNumber(null)', context), '—');
});

test('all five company core metric names are recognized without financial aliases', () => {
  for (const code of ['revenue', 'lt_reported_revenue', 'tata_reported_revenue',
    'bank_total_income', 'bank_owner_profit', 'profit_for_year', 'cfo', 'cash_from_operations']) {
    assert.ok(display.labels[code]);
  }
  assert.equal(display.labels.profit_after_tax, undefined);
  assert.equal(display.labels.total_debt, undefined);
  assert.match(display.metricLabel('bank_total_income'), /Bank total income/);
  assert.match(display.metricLabel('profit_for_year'), /group profit/);
});

test('fiscal gaps and null observations do not become connected lines', () => {
  assert.equal(display.trendSegments([entry(2022, 1), entry(2024, 2)], 'tcs').length, 2);
  assert.equal(display.trendSegments([entry(2022, 1), entry(2023, null), entry(2024, 2)], 'tcs').length, 2);
  assert.equal(display.trendSegments([entry(2022, 0), entry(2023, -1)], 'tcs').length, 1);
});

test('Tata FY2026 stays a separate series while TCS consecutive history connects', () => {
  const values = [entry(2025, 1), entry(2026, 2)];
  assert.equal(display.trendSegments(values, 'tata-motors').length, 2);
  assert.equal(display.trendSegments(values, 'tcs').length, 1);
});

test('stale ratios and ambiguous formula versions are suppressed', () => {
  const periods = new Map([['old', { period_end: '2025-03-31' }], ['new', { period_end: '2026-03-31' }]]);
  const ratio = (period, version, value = '1') => ({ reporting_period_id: period,
    metric_code: 'current_ratio', formula_version: version, value });
  assert.equal(display.latestPeriodMetrics([ratio('old', '1')], periods).length, 0);
  assert.equal(display.latestPeriodMetrics([ratio('new', '1', null)], periods).length, 0);
  assert.equal(display.latestPeriodMetrics([ratio('new', '1'), ratio('new', '2')], periods).length, 0);
  assert.equal(display.latestPeriodMetrics([ratio('new', '1')], periods).length, 1);
});
