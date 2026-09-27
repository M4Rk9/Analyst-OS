"use strict";

const COMPANY_META = Object.freeze({
  "reliance-industries": { name: "Reliance Industries", symbol: "RELIANCE" },
  "tcs": { name: "Tata Consultancy Services", symbol: "TCS" },
  "hdfc-bank": { name: "HDFC Bank", symbol: "HDFCBANK" },
  "tata-motors": { name: "Tata Motors", symbol: "TATAMOTORS" },
  "larsen-toubro": { name: "Larsen & Toubro", symbol: "LT" },
});

const TREND_METRICS = Object.freeze([
  "revenue",
  "operating_profit",
  "ebitda",
  "profit_after_tax",
  "pat",
  "net_income",
  "eps",
  "total_debt",
  "debt",
  "cash_from_operations",
  "cfo",
  "free_cash_flow",
  "fcf",
]);

const SECTION_LABELS = Object.freeze({
  business_brief: "Business in brief",
  financial_changes: "What changed financially?",
  positives: "Key positives",
  risks: "Key risks",
  management_outlook: "Management outlook",
});

function selectedCompanySlug() {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get("company") || "";
  return Object.hasOwn(COMPANY_META, slug) ? slug : "";
}

function createElement(tag, { className = "", text = "" } = {}) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text) element.textContent = text;
  return element;
}

function queryString(values) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== null && value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  return params.toString();
}

async function selectRows(table, values) {
  if (!window.AnalystDataClient) {
    throw new Error("The read-only data client is unavailable.");
  }
  return window.AnalystDataClient.select(table, queryString(values));
}

async function optionalRows(table, values) {
  try {
    const rows = await selectRows(table, values);
    return Array.isArray(rows) ? rows : [];
  } catch (error) {
    console.warn(`Optional dataset ${table} is unavailable.`, error);
    return [];
  }
}

function humanize(code) {
  return String(code || "")
    .replaceAll("_", " ")
    .replace(/\b\w/gu, (character) => character.toUpperCase());
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function numericValue(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatValue(value, unit = "") {
  const number = numericValue(value);
  if (number === null) return "—";

  const normalizedUnit = String(unit || "").toLowerCase();
  if (normalizedUnit.includes("percent") || normalizedUnit === "%") {
    return `${number.toLocaleString("en-IN", { maximumFractionDigits: 2 })}%`;
  }
  if (normalizedUnit.includes("ratio") || normalizedUnit === "x") {
    return `${number.toLocaleString("en-IN", { maximumFractionDigits: 2 })}×`;
  }

  return new Intl.NumberFormat("en-IN", {
    notation: Math.abs(number) >= 100000 ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(number);
}

function safeHttpsUrl(value) {
  try {
    const url = new URL(String(value));
    return url.protocol === "https:" ? url : null;
  } catch {
    return null;
  }
}

function externalLink(label, value) {
  const url = safeHttpsUrl(value);
  if (!url) return null;
  const link = createElement("a", { className: "source-link", text: label });
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function showEmpty(container, message) {
  container.replaceChildren(createElement("div", { className: "empty-state", text: message }));
}

function renderHeader(company) {
  const name = document.getElementById("company-name");
  const symbol = document.getElementById("company-symbol");
  const summary = document.getElementById("company-summary");

  if (name) name.textContent = company.name;
  if (symbol) symbol.textContent = `${company.ticker} · ${company.exchange}`;
  if (summary) {
    const descriptors = [company.sector, company.industry].filter(Boolean);
    summary.textContent = descriptors.length ? descriptors.join(" · ") : "Verified company profile";
  }
  document.title = `${company.name} | Analyst OS`;
}

function renderOverview(company) {
  const panel = document.getElementById("overview");
  if (!panel) return;

  const content = createElement("div", { className: "overview-grid" });
  const fields = [
    ["Ticker", company.ticker],
    ["Exchange", company.exchange],
    ["Sector", company.sector],
    ["Industry", company.industry || "—"],
  ];

  for (const [label, value] of fields) {
    const item = createElement("div", { className: "overview-item" });
    item.append(
      createElement("span", { className: "data-label", text: label }),
      createElement("strong", { text: value }),
    );
    content.append(item);
  }

  const links = createElement("div", { className: "overview-links" });
  const website = externalLink("Company website ↗", company.website_url);
  const investorRelations = externalLink("Investor relations ↗", company.investor_relations_url);
  if (website) links.append(website);
  if (investorRelations) links.append(investorRelations);
  if (links.childElementCount) content.append(links);

  panel.replaceChildren(createElement("h2", { text: "Overview" }), content);
}

function periodLabel(period) {
  if (!period) return "Unknown period";
  return period.period_type === "FY"
    ? `FY${period.fiscal_year}`
    : `${period.period_type} FY${period.fiscal_year}`;
}

function renderTrendSvg(points, label) {
  const values = points.map((point) => numericValue(point.value)).filter((value) => value !== null);
  if (values.length < 2) return null;

  const width = 260;
  const height = 64;
  const padding = 6;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${label} trend`);
  svg.classList.add("trend-chart");

  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  const coordinates = values.map((value, index) => {
    const x = padding + (index / (values.length - 1)) * (width - padding * 2);
    const y = height - padding - ((value - min) / spread) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  polyline.setAttribute("points", coordinates.join(" "));
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "currentColor");
  polyline.setAttribute("stroke-width", "2");
  polyline.setAttribute("vector-effect", "non-scaling-stroke");
  svg.append(polyline);
  return svg;
}

function renderFinancials(facts, periodMap) {
  const container = document.getElementById("financial-content");
  if (!container) return;

  const grouped = new Map();
  for (const fact of facts) {
    if (!TREND_METRICS.includes(fact.metric_code)) continue;
    const period = periodMap.get(fact.reporting_period_id);
    if (!period) continue;
    if (!grouped.has(fact.metric_code)) grouped.set(fact.metric_code, []);
    grouped.get(fact.metric_code).push({
      period,
      value: fact.normalized_value,
      currency: fact.currency || period.currency,
    });
  }

  if (!grouped.size) {
    showEmpty(container, "No verified preferred financial history has been loaded yet.");
    return;
  }

  const table = createElement("table", { className: "data-table" });
  const head = createElement("thead");
  const headRow = createElement("tr");
  for (const label of ["Metric", "Trend", "Latest", "Period"]) {
    headRow.append(createElement("th", { text: label }));
  }
  head.append(headRow);
  table.append(head);

  const body = createElement("tbody");
  for (const [metric, entries] of grouped) {
    entries.sort((left, right) => left.period.period_end.localeCompare(right.period.period_end));
    const latest = entries.at(-1);
    const row = createElement("tr");
    row.append(createElement("th", { text: humanize(metric) }));

    const chartCell = createElement("td");
    const chart = renderTrendSvg(entries, humanize(metric));
    chartCell.append(chart || createElement("span", { className: "muted", text: "Insufficient history" }));
    row.append(chartCell);

    row.append(createElement("td", { className: "numeric", text: formatValue(latest.value) }));
    row.append(createElement("td", { text: periodLabel(latest.period) }));
    body.append(row);
  }
  table.append(body);
  container.replaceChildren(table);
}

function latestByMetric(metrics, periodMap) {
  const byMetric = new Map();
  for (const metric of metrics) {
    const period = periodMap.get(metric.reporting_period_id);
    if (!period) continue;
    const current = byMetric.get(metric.metric_code);
    if (!current || current.period.period_end < period.period_end) {
      byMetric.set(metric.metric_code, { ...metric, period });
    }
  }
  return [...byMetric.values()].sort((left, right) => left.metric_code.localeCompare(right.metric_code));
}

function renderRatios(metrics, periodMap) {
  const container = document.getElementById("ratio-content");
  if (!container) return;
  const latest = latestByMetric(metrics, periodMap);
  if (!latest.length) {
    showEmpty(container, "No deterministic calculated metrics are available yet.");
    return;
  }

  const grid = createElement("div", { className: "metric-grid" });
  for (const metric of latest) {
    const card = createElement("article", { className: "metric-card" });
    card.append(
      createElement("span", { className: "data-label", text: humanize(metric.metric_code) }),
      createElement("strong", { className: "metric-value", text: formatValue(metric.value, metric.unit) }),
      createElement("span", {
        className: "metric-meta",
        text: `${periodLabel(metric.period)} · formula ${metric.formula_version}`,
      }),
    );
    grid.append(card);
  }
  container.replaceChildren(grid);
}

function renderSignals(flags, periodMap) {
  const container = document.getElementById("signal-content");
  if (!container) return;
  if (!flags.length) {
    showEmpty(container, "No active deterministic investigation signals are available.");
    return;
  }

  const list = createElement("div", { className: "signal-list" });
  for (const flag of flags) {
    const item = createElement("article", { className: `signal signal-${flag.severity}` });
    const period = periodMap.get(flag.reporting_period_id);
    item.append(
      createElement("span", { className: "signal-severity", text: `${flag.severity} signal` }),
      createElement("h3", { text: flag.title }),
      createElement("p", { text: flag.description }),
      createElement("small", {
        className: "muted",
        text: `${period ? periodLabel(period) : "Company level"} · rule ${flag.rule_version}`,
      }),
    );
    list.append(item);
  }
  container.replaceChildren(list);
}

function renderInsights(insights, sourceMap) {
  const container = document.getElementById("insight-content");
  if (!container) return;
  if (!insights.length) {
    showEmpty(container, "No validated source-backed AI insights are available yet.");
    return;
  }

  const list = createElement("div", { className: "insight-list" });
  for (const insight of insights) {
    const item = createElement("article", { className: "insight" });
    item.append(
      createElement("span", {
        className: "data-label",
        text: SECTION_LABELS[insight.section] || humanize(insight.section),
      }),
      createElement("h3", { text: insight.title }),
      createElement("p", { text: insight.insight_text }),
    );

    const source = sourceMap.get(insight.source_document_id);
    const sourceLink = source ? externalLink(
      `${source.title} · p.${insight.source_page} ↗`,
      source.source_url,
    ) : null;
    const meta = createElement("div", { className: "insight-meta" });
    meta.append(createElement("span", { text: `${insight.confidence} confidence` }));
    if (sourceLink) meta.append(sourceLink);
    item.append(meta);
    list.append(item);
  }
  container.replaceChildren(list);
}

function renderPeers(company, companies) {
  const container = document.getElementById("peer-content");
  if (!container) return;

  const peers = companies.filter((candidate) => (
    candidate.id !== company.id && candidate.sector === company.sector
  ));
  if (!peers.length) {
    showEmpty(
      container,
      "No verified same-sector peer is configured in the intentionally small V1 universe.",
    );
    return;
  }

  const table = createElement("table", { className: "data-table" });
  const head = createElement("thead");
  const row = createElement("tr");
  for (const label of ["Company", "Ticker", "Exchange", "Sector"]) {
    row.append(createElement("th", { text: label }));
  }
  head.append(row);
  table.append(head);

  const body = createElement("tbody");
  for (const peer of peers) {
    const peerRow = createElement("tr");
    const companyCell = createElement("td");
    const link = createElement("a", { text: peer.name });
    link.href = `./company.html?company=${encodeURIComponent(peer.slug)}`;
    companyCell.append(link);
    peerRow.append(
      companyCell,
      createElement("td", { text: peer.ticker }),
      createElement("td", { text: peer.exchange }),
      createElement("td", { text: peer.sector }),
    );
    body.append(peerRow);
  }
  table.append(body);
  container.replaceChildren(table);
}

function renderSources(sources) {
  const container = document.getElementById("source-content");
  if (!container) return;
  if (!sources.length) {
    showEmpty(container, "No verified primary-source documents are available yet.");
    return;
  }

  const list = createElement("div", { className: "source-list" });
  for (const source of sources) {
    const item = createElement("article", { className: "source-item" });
    const heading = createElement("h3", { text: source.title });
    const metaParts = [humanize(source.document_type), source.publisher];
    if (source.fiscal_year) metaParts.push(`FY${source.fiscal_year}`);
    if (source.fiscal_quarter) metaParts.push(`Q${source.fiscal_quarter}`);
    if (source.published_at) metaParts.push(formatDate(source.published_at));

    item.append(heading, createElement("p", { className: "muted", text: metaParts.join(" · ") }));
    const link = externalLink("Open primary source ↗", source.source_url);
    if (link) item.append(link);
    list.append(item);
  }
  container.replaceChildren(list);
}

function renderLoadFailure(message) {
  const summary = document.getElementById("company-summary");
  if (summary) summary.textContent = message;
  for (const id of [
    "financial-content",
    "ratio-content",
    "signal-content",
    "insight-content",
    "peer-content",
    "source-content",
  ]) {
    const container = document.getElementById(id);
    if (container) showEmpty(container, message);
  }
}

async function loadWorkspace() {
  const slug = selectedCompanySlug();
  if (!slug) {
    renderLoadFailure("Select a supported company from the home page.");
    return;
  }

  let companies;
  try {
    companies = await selectRows("companies", {
      select: "id,slug,name,ticker,exchange,sector,industry,website_url,investor_relations_url",
      slug: `eq.${slug}`,
      limit: 1,
    });
  } catch (error) {
    console.error("Unable to load company profile.", error);
    renderLoadFailure("Verified data is unavailable. Check the public Supabase configuration.");
    return;
  }

  const company = Array.isArray(companies) ? companies[0] : null;
  if (!company) {
    renderLoadFailure("This company is not available in the verified public dataset.");
    return;
  }

  renderHeader(company);
  renderOverview(company);

  const companyFilter = `eq.${company.id}`;
  const [periods, facts, metrics, flags, insights, sources, universe] = await Promise.all([
    optionalRows("reporting_periods", {
      select: "id,period_type,fiscal_year,period_end,currency",
      company_id: companyFilter,
      order: "period_end.asc",
    }),
    optionalRows("financial_facts", {
      select: "reporting_period_id,metric_code,normalized_value,currency,source_document_id",
      company_id: companyFilter,
      is_preferred: "eq.true",
    }),
    optionalRows("calculated_metrics", {
      select: "reporting_period_id,metric_code,value,unit,formula_version,computed_at",
      company_id: companyFilter,
      order: "computed_at.desc",
    }),
    optionalRows("red_flags", {
      select: "reporting_period_id,flag_code,title,description,severity,rule_version,computed_at",
      company_id: companyFilter,
      order: "computed_at.desc",
    }),
    optionalRows("ai_insights", {
      select: "source_document_id,section,title,insight_text,confidence,source_page,source_section,model_name,prompt_version,generated_at",
      company_id: companyFilter,
      order: "generated_at.desc",
    }),
    optionalRows("source_documents", {
      select: "id,title,document_type,fiscal_year,fiscal_quarter,source_url,publisher,published_at",
      company_id: companyFilter,
      order: "published_at.desc",
    }),
    optionalRows("companies", {
      select: "id,slug,name,ticker,exchange,sector",
      order: "name.asc",
    }),
  ]);

  const periodMap = new Map(periods.map((period) => [period.id, period]));
  const sourceMap = new Map(sources.map((source) => [source.id, source]));

  renderFinancials(facts, periodMap);
  renderRatios(metrics, periodMap);
  renderSignals(flags, periodMap);
  renderInsights(insights, sourceMap);
  renderPeers(company, universe);
  renderSources(sources);
}

document.addEventListener("DOMContentLoaded", loadWorkspace);
