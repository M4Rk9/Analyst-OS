"use strict";

const INITIAL_COMPANIES = Object.freeze([
  { slug: "reliance-industries", name: "Reliance Industries", symbol: "RELIANCE" },
  { slug: "tcs", name: "Tata Consultancy Services", symbol: "TCS" },
  { slug: "hdfc-bank", name: "HDFC Bank", symbol: "HDFCBANK" },
  { slug: "tata-motors", name: "Tata Motors", symbol: "TATAMOTORS" },
  { slug: "larsen-toubro", name: "Larsen & Toubro", symbol: "LT" },
]);

function renderCompanyList() {
  const container = document.getElementById("company-list");
  if (!container) return;

  for (const company of INITIAL_COMPANIES) {
    const link = document.createElement("a");
    link.className = "company-link";
    link.href = `./company.html?company=${encodeURIComponent(company.slug)}`;

    const name = document.createElement("strong");
    name.textContent = company.name;

    const symbol = document.createElement("span");
    symbol.textContent = company.symbol;

    link.append(name, symbol);
    container.append(link);
  }
}

document.addEventListener("DOMContentLoaded", renderCompanyList);
