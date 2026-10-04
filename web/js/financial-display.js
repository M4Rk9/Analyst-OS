"use strict";

(function exposeFinancialDisplay(global) {
  const labels = Object.freeze({
    revenue: "Reported revenue from operations",
    lt_reported_revenue: "L&T reported revenue from operations",
    tata_reported_revenue: "Tata / TMPV reported revenue from operations",
    bank_total_income: "Bank total income",
    bank_owner_profit: "Bank profit attributable to owners",
    profit_for_year: "Reported consolidated group profit",
    cash_from_operations: "Net cash from operating activities",
    cfo: "Net cash from operating activities",
    cash_from_investing: "Net cash from investing activities",
    cfi: "Net cash from investing activities",
    cash_from_financing: "Net cash from financing activities",
    cff: "Net cash from financing activities",
    total_assets: "Total assets",
    bank_total_assets: "Bank total assets",
    total_equity: "Total equity including non-controlling interests",
    current_assets: "Current assets",
    current_liabilities: "Current liabilities",
    cash_and_cash_equivalents: "Cash and cash equivalents",
    bank_deposits: "Bank deposits",
    bank_advances: "Bank advances",
    bank_borrowings: "Bank reported borrowings",
    bank_investments: "Bank investments",
    bank_cash_rbi: "Bank cash and balances with RBI",
    bank_balances_call_money: "Bank balances with banks and money at call",
    inventory: "Inventories",
  });

  function numberValue(value) {
    if (typeof value !== "number" && typeof value !== "string") return null;
    if (typeof value === "string" && !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/iu.test(value.trim())) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function hasBreak(slug, previous, current) {
    return previous.period_type !== "FY" || current.period_type !== "FY"
      || current.fiscal_year !== previous.fiscal_year + 1
      || (slug === "tata-motors" && current.fiscal_year === 2026);
  }

  // Retain nulls and fiscal-year gaps as segment boundaries instead of bridging them.
  function trendSegments(entries, slug) {
    const segments = [];
    let segment = [];
    let previous = null;
    for (const entry of entries) {
      const value = numberValue(entry.value);
      if (value === null || (previous && hasBreak(slug, previous.period, entry.period))) {
        if (segment.length) segments.push(segment);
        segment = [];
      }
      if (value !== null) segment.push({ ...entry, value });
      previous = value === null ? null : entry;
    }
    if (segment.length) segments.push(segment);
    return segments;
  }

  function metricLabel(code) {
    return labels[code] || String(code || "").replaceAll("_", " ");
  }

  const calculatedLabels = Object.freeze({
    current_ratio: "Current ratio",
    working_capital: "Reported working capital (INR)",
    cfo_to_reported_group_profit: "CFO / reported consolidated group profit",
  });

  function supportedMetrics(metrics) {
    return metrics.filter((m) => Object.hasOwn(calculatedLabels, m.metric_code)
      && m.policy_version === "reported-core-1" && m.formula_version === "1.0"
      && m.unit === (m.metric_code === "working_capital" ? "INR" : "ratio")
      && Array.isArray(m.input_facts) && m.input_facts.length === 2
      && m.input_facts.every((input) => input && typeof input.fact_id === "string"));
  }

  function latestPeriodMetrics(metrics, periodMap) {
    const dated = metrics.map((metric) => ({ ...metric, period: periodMap.get(metric.reporting_period_id) }))
      .filter((metric) => metric.period);
    const latest = [...periodMap.values()].map((period) => period.period_end).sort().at(-1);
    const selected = new Map();
    for (const metric of dated) {
      if (metric.period.period_end !== latest || numberValue(metric.value) === null) continue;
      // Multiple formula versions need an explicit selection policy; do not pick arbitrarily.
      selected.set(metric.metric_code, selected.has(metric.metric_code) ? null : metric);
    }
    return [...selected.values()].filter(Boolean).sort((a, b) => a.metric_code.localeCompare(b.metric_code));
  }

  global.AnalystFinancialDisplay = Object.freeze({
    labels, numberValue, trendSegments, metricLabel, latestPeriodMetrics, calculatedLabels, supportedMetrics,
  });
})(window);
