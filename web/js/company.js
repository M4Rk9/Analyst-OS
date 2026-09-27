"use strict";

const COMPANY_META = Object.freeze({
  "reliance-industries": { name: "Reliance Industries", symbol: "RELIANCE" },
  "tcs": { name: "Tata Consultancy Services", symbol: "TCS" },
  "hdfc-bank": { name: "HDFC Bank", symbol: "HDFCBANK" },
  "tata-motors": { name: "Tata Motors", symbol: "TATAMOTORS" },
  "larsen-toubro": { name: "Larsen & Toubro", symbol: "LT" },
});

function selectedCompanySlug() {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get("company") || "";
  return Object.hasOwn(COMPANY_META, slug) ? slug : "";
}

function renderHeader() {
  const slug = selectedCompanySlug();
  const meta = slug ? COMPANY_META[slug] : null;
  if (!meta) return;

  const name = document.getElementById("company-name");
  const symbol = document.getElementById("company-symbol");
  const summary = document.getElementById("company-summary");

  if (name) name.textContent = meta.name;
  if (symbol) symbol.textContent = meta.symbol;
  if (summary) summary.textContent = "Verified company metadata and analytical outputs will load from the secured data layer.";
  document.title = `${meta.name} | Analyst OS`;
}

document.addEventListener("DOMContentLoaded", renderHeader);
