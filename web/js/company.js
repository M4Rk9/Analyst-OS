"use strict";

const COMPANY_META = Object.freeze({
  "reliance-industries": { name: "Reliance Industries", symbol: "RELIANCE" },
  "tcs": { name: "Tata Consultancy Services", symbol: "TCS" },
  "hdfc-bank": { name: "HDFC Bank", symbol: "HDFCBANK" },
  "tata-motors": { name: "Tata Motors", symbol: "TATAMOTORS" },
  "larsen-toubro": { name: "Larsen & Toubro", symbol: "LT" },
});

const TREND_METRICS = new Set(Object.keys(window.AnalystFinancialDisplay.labels));

const SECTION_LABELS = Object.freeze({
  business_brief: "Business in brief",
  financial_changes: "What changed financially?",
  positives: "Key positives",
  risks: "Key risks",
  management_outlook: "Management outlook",
});

function element(tag, { className = "", text = "" } = {}) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function selectedCompanySlug() {
  const slug = new URLSearchParams(window.location.search).get("company") || "";
  return Object.hasOwn(COMPANY_META, slug) ? slug : "";
}

function queryString(values) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== null && value !== undefined && value !== "") params.set(key, String(value));
  }
  return params.toString();
}

async function selectRows(table, values) {
  if (!window.AnalystDataClient) throw new Error("The read-only data client is unavailable.");
  const rows = await window.AnalystDataClient.select(table, queryString(values));
  return Array.isArray(rows) ? rows : [];
}

async function optionalRows(table, values) {
  try {
    return await selectRows(table, values);
  } catch (error) {
    console.warn(`Optional dataset ${table} is unavailable.`, error);
    return [];
  }
}

function humanize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/gu, (character) => character.toUpperCase());
}

function numberValue(value) {
  return window.AnalystFinancialDisplay.numberValue(value);
}

function formatNumber(value, unit = "") {
  const number = numberValue(value);
  if (number === null) return "—";
  const normalizedUnit = String(unit || "").toLowerCase();
  const formatted = number.toLocaleString("en-IN", { maximumFractionDigits: 2 });
  if (normalizedUnit.includes("percent") || normalizedUnit === "%") return `${formatted}%`;
  if (normalizedUnit.includes("ratio") || normalizedUnit === "x") return `${formatted}×`;
  return new Intl.NumberFormat("en-IN", {
    notation: Math.abs(number) >= 100000 ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(number);
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
  const link = element("a", { className: "source-link", text: label });
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function empty(container, message) {
  container.replaceChildren(element("div", { className: "empty-state", text: message }));
}

function periodLabel(period) {
  if (!period) return "Unknown period";
  return period.period_type === "FY"
    ? `FY${period.fiscal_year}`
    : `${period.period_type} FY${period.fiscal_year}`;
}

function renderHeader(company) {
  document.getElementById("company-name").textContent = company.name;
  document.getElementById("company-symbol").textContent = `${company.ticker} · ${company.exchange}`;
  const descriptors = [company.sector, company.industry].filter(Boolean);
  document.getElementById("company-summary").textContent = descriptors.join(" · ") || "Verified profile";
  document.title = `${company.name} | Analyst OS`;
}

function renderOverview(company) {
  const panel = document.getElementById("overview");
  const grid = element("div", { className: "overview-grid" });
  for (const [label, value] of [
    ["Ticker", company.ticker],
    ["Exchange", company.exchange],
    ["Sector", company.sector],
    ["Industry", company.industry || "—"],
  ]) {
    const item = element("div", { className: "overview-item" });
    item.append(
      element("span", { className: "data-label", text: label }),
      element("strong", { text: value }),
    );
    grid.append(item);
  }
  const links = element("div", { className: "overview-links" });
  for (const [label, url] of [
    ["Company website ↗", company.website_url],
    ["Investor relations ↗", company.investor_relations_url],
  ]) {
    const link = externalLink(label, url);
    if (link) links.append(link);
  }
  if (links.childElementCount) grid.append(links);
  panel.replaceChildren(element("h2", { text: "Overview" }), grid);
}

function renderTrendSvg(entries, label, slug) {
  const segments = window.AnalystFinancialDisplay.trendSegments(entries, slug);
  const points = segments.flat();
  if (points.length < 2) return null;

  const width = 260;
  const height = 64;
  const padding = 6;
  const minimum = Math.min(...points.map((point) => point.value));
  const maximum = Math.max(...points.map((point) => point.value));
  const firstYear = Math.min(...points.map((point) => point.period.fiscal_year));
  const lastYear = Math.max(...points.map((point) => point.period.fiscal_year));
  const spread = maximum - minimum || 1;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${label} trend`);
  svg.classList.add("trend-chart");

  const coordinates = (point) => [
    padding + ((point.period.fiscal_year - firstYear) / (lastYear - firstYear || 1)) * (width - padding * 2),
    height - padding - ((point.value - minimum) / spread) * (height - padding * 2),
  ];
  for (const segment of segments) {
    if (segment.length > 1) {
      const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      polyline.setAttribute("points", segment.map((point) => coordinates(point)
        .map((coordinate) => coordinate.toFixed(1)).join(",")).join(" "));
      polyline.setAttribute("fill", "none");
      polyline.setAttribute("stroke", "currentColor");
      polyline.setAttribute("stroke-width", "2");
      polyline.setAttribute("vector-effect", "non-scaling-stroke");
      svg.append(polyline);
    }
    for (const point of segment) {
      const [x, y] = coordinates(point);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x.toFixed(1));
      circle.setAttribute("cy", y.toFixed(1));
      circle.setAttribute("r", "2.5");
      circle.setAttribute("fill", "currentColor");
      svg.append(circle);
    }
  }
  return svg;
}

function renderFinancials(facts, periodMap, sourceMap, company) {
  const container = document.getElementById("financial-content");
  const groups = new Map();
  for (const fact of facts) {
    if (!TREND_METRICS.has(fact.metric_code)) continue;
    const period = periodMap.get(fact.reporting_period_id);
    if (!period) continue;
    if (!groups.has(fact.metric_code)) groups.set(fact.metric_code, []);
    groups.get(fact.metric_code).push({ period, value: fact.normalized_value, fact });
  }
  if (!groups.size) {
    empty(container, "No verified preferred financial history has been loaded yet.");
    return;
  }

  const table = element("table", { className: "data-table" });
  const head = element("thead");
  const headRow = element("tr");
  for (const label of ["Reported metric", "History", "Latest (INR)", "Period", "Evidence"]) headRow.append(element("th", { text: label }));
  head.append(headRow);
  table.append(head);
  const body = element("tbody");
  for (const [metric, entries] of groups) {
    entries.sort((a, b) => a.period.period_end.localeCompare(b.period.period_end));
    const latest = entries.at(-1);
    const row = element("tr");
    const label = window.AnalystFinancialDisplay.metricLabel(metric);
    row.append(element("th", { text: label }));
    const trendCell = element("td");
    trendCell.append(renderTrendSvg(entries, label, company.slug) || element("span", {
      className: "muted",
      text: "Insufficient history",
    }));
    row.append(trendCell);
    row.append(element("td", { className: "numeric", text: formatNumber(latest.value) }));
    row.append(element("td", { text: periodLabel(latest.period) }));
    const evidence = element("td");
    const source = sourceMap.get(latest.fact.source_document_id);
    const link = source ? externalLink(`FY${source.fiscal_year} · PDF p.${latest.fact.source_page} ↗`, source.source_url) : null;
    evidence.append(link || element("span", { text: "Unavailable" }));
    row.append(evidence);
    body.append(row);
  }
  table.append(body);
  const note = element("p", { className: "muted", text: "Reported consolidated figures in INR. Missing years are unavailable. Report scopes may differ; these lines do not assert comparable growth." });
  if (company.slug === "tata-motors") note.append(element("span", { text: " Original Tata Motors continues into TMPV; FY2026 is a series break. The new CV company is separate. FY2024 core facts remain withheld." }));
  container.replaceChildren(note, table);
}

function latestMetrics(metrics, periodMap) {
  return window.AnalystFinancialDisplay.latestPeriodMetrics(metrics, periodMap);
}

function renderRatios(metrics, periodMap) {
  const container = document.getElementById("ratio-content");
  const rows = latestMetrics(metrics, periodMap);
  if (!rows.length) {
    empty(container, "No deterministic calculated metrics are available yet.");
    return;
  }
  const grid = element("div", { className: "metric-grid" });
  for (const metric of rows) {
    const card = element("article", { className: "metric-card" });
    card.append(
      element("span", { className: "data-label", text: humanize(metric.metric_code) }),
      element("strong", { className: "metric-value", text: formatNumber(metric.value, metric.unit) }),
      element("span", {
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
  if (!flags.length) {
    empty(container, "No active deterministic investigation signals are available.");
    return;
  }
  const list = element("div", { className: "signal-list" });
  for (const flag of flags) {
    const card = element("article", { className: `signal signal-${flag.severity}` });
    const period = periodMap.get(flag.reporting_period_id);
    card.append(
      element("span", { className: "signal-severity", text: `${flag.severity} signal` }),
      element("h3", { text: flag.title }),
      element("p", { text: flag.description }),
      element("small", {
        className: "muted",
        text: `${period ? periodLabel(period) : "Company level"} · rule ${flag.rule_version}`,
      }),
    );
    list.append(card);
  }
  container.replaceChildren(list);
}

function evidenceItems(insight) {
  return Array.isArray(insight.evidence)
    ? insight.evidence.filter((item) => item && typeof item === "object")
    : [];
}

function renderInsights(insights, sourceMap) {
  const container = document.getElementById("insight-content");
  if (!insights.length) {
    empty(container, "No validated source-backed AI insights are available yet.");
    return;
  }
  const list = element("div", { className: "insight-list" });
  for (const insight of insights) {
    const card = element("article", { className: "insight" });
    card.append(
      element("span", {
        className: "data-label",
        text: SECTION_LABELS[insight.section] || humanize(insight.section),
      }),
      element("h3", { text: insight.title }),
      element("p", { text: insight.insight_text }),
    );

    const meta = element("div", { className: "insight-meta" });
    meta.append(element("span", { text: `${insight.confidence} confidence` }));
    const source = sourceMap.get(insight.source_document_id);
    for (const evidence of evidenceItems(insight)) {
      const page = Number.isInteger(Number(evidence.page)) ? Number(evidence.page) : null;
      const section = typeof evidence.section === "string" ? evidence.section : "";
      const label = [source?.title || "Primary source", page ? `p.${page}` : "", section]
        .filter(Boolean)
        .join(" · ");
      const link = externalLink(`${label} ↗`, evidence.source_url);
      if (link) meta.append(link);
    }
    card.append(meta);
    list.append(card);
  }
  container.replaceChildren(list);
}

function renderPeers(company, companies) {
  const container = document.getElementById("peer-content");
  const peers = companies.filter((candidate) => (
    candidate.id !== company.id && candidate.sector === company.sector
  ));
  if (!peers.length) {
    empty(container, "No verified same-sector peer is configured in the small V1 universe.");
    return;
  }
  const table = element("table", { className: "data-table" });
  const head = element("thead");
  const headRow = element("tr");
  for (const label of ["Company", "Ticker", "Exchange", "Sector"]) headRow.append(element("th", { text: label }));
  head.append(headRow);
  table.append(head);
  const body = element("tbody");
  for (const peer of peers) {
    const row = element("tr");
    const companyCell = element("td");
    const link = element("a", { text: peer.name });
    link.href = `./company.html?company=${encodeURIComponent(peer.slug)}`;
    companyCell.append(link);
    row.append(
      companyCell,
      element("td", { text: peer.ticker }),
      element("td", { text: peer.exchange }),
      element("td", { text: peer.sector }),
    );
    body.append(row);
  }
  table.append(body);
  container.replaceChildren(table);
}

function renderSources(sources) {
  const container = document.getElementById("source-content");
  if (!sources.length) {
    empty(container, "No verified primary-source documents are available yet.");
    return;
  }
  const list = element("div", { className: "source-list" });
  for (const source of sources) {
    const card = element("article", { className: "source-item" });
    const details = [humanize(source.document_type), source.publisher];
    if (source.fiscal_year) details.push(`FY${source.fiscal_year}`);
    if (source.fiscal_quarter) details.push(`Q${source.fiscal_quarter}`);
    if (source.published_at) details.push(formatDate(source.published_at));
    card.append(
      element("h3", { text: source.title }),
      element("p", { className: "muted", text: details.join(" · ") }),
    );
    const link = externalLink("Open primary source ↗", source.source_url);
    if (link) card.append(link);
    list.append(card);
  }
  container.replaceChildren(list);
}

function renderFailure(message) {
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
    if (container) empty(container, message);
  }
}

async function loadWorkspace() {
  const slug = selectedCompanySlug();
  if (!slug) {
    renderFailure("Select a supported company from the home page.");
    return;
  }

  let companyRows;
  try {
    companyRows = await selectRows("companies", {
      select: "id,slug,name,ticker,exchange,sector,industry,website_url,investor_relations_url",
      slug: `eq.${slug}`,
      limit: 1,
    });
  } catch (error) {
    console.error("Unable to load company profile.", error);
    renderFailure("Verified data is unavailable. Check the public Supabase configuration.");
    return;
  }
  const company = companyRows[0];
  if (!company) {
    renderFailure("This company is not available in the verified public dataset.");
    return;
  }
  renderHeader(company);
  renderOverview(company);

  const filter = `eq.${company.id}`;
  const [periods, facts, metrics, flags, insights, sources, universe] = await Promise.all([
    optionalRows("reporting_periods", {
      select: "id,period_type,fiscal_year,period_end,currency",
      company_id: filter,
      order: "period_end.asc",
    }),
    optionalRows("financial_facts", {
      select: "id,reporting_period_id,metric_code,normalized_value,currency,source_document_id,source_page,source_label",
      company_id: filter,
      is_preferred: "eq.true",
      quality_status: "eq.verified",
    }),
    optionalRows("calculated_metrics", {
      select: "reporting_period_id,metric_code,value,unit,formula_version,computed_at",
      company_id: filter,
      order: "computed_at.desc",
    }),
    optionalRows("red_flags", {
      select: "reporting_period_id,flag_code,title,description,severity,rule_version,computed_at",
      company_id: filter,
      order: "computed_at.desc",
    }),
    optionalRows("ai_insights", {
      select: "source_document_id,section,title,insight_text,confidence,evidence,model_name,prompt_version,generated_at",
      company_id: filter,
      order: "generated_at.desc",
    }),
    optionalRows("source_documents", {
      select: "id,title,document_type,fiscal_year,fiscal_quarter,source_url,publisher,published_at",
      company_id: filter,
      order: "published_at.desc",
    }),
    optionalRows("companies", {
      select: "id,slug,name,ticker,exchange,sector",
      order: "name.asc",
    }),
  ]);

  const periodMap = new Map(periods.map((period) => [period.id, period]));
  const sourceMap = new Map(sources.map((source) => [source.id, source]));
  renderFinancials(facts, periodMap, sourceMap, company);
  renderRatios(metrics, periodMap);
  renderSignals(flags, periodMap);
  renderInsights(insights, sourceMap);
  renderPeers(company, universe);
  renderSources(sources);
}

document.addEventListener("DOMContentLoaded", loadWorkspace);
