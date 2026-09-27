"use strict";

const INITIAL_COMPANIES = Object.freeze([
  { slug: "reliance-industries", name: "Reliance Industries", symbol: "RELIANCE" },
  { slug: "tcs", name: "Tata Consultancy Services", symbol: "TCS" },
  { slug: "hdfc-bank", name: "HDFC Bank", symbol: "HDFCBANK" },
  { slug: "tata-motors", name: "Tata Motors", symbol: "TATAMOTORS" },
  { slug: "larsen-toubro", name: "Larsen & Toubro", symbol: "LT" },
]);

function buildCompanyLink(company) {
  const link = document.createElement("a");
  link.className = "company-link";
  link.href = `./company.html?company=${encodeURIComponent(company.slug)}`;

  const name = document.createElement("strong");
  name.textContent = company.name;

  const symbol = document.createElement("span");
  symbol.textContent = company.symbol;

  link.append(name, symbol);
  return link;
}

function renderCompanyList(companies = INITIAL_COMPANIES) {
  const container = document.getElementById("company-list");
  const empty = document.getElementById("company-search-empty");
  if (!container) return;

  container.replaceChildren(...companies.map(buildCompanyLink));
  if (empty) empty.hidden = companies.length !== 0;
}

function configureSearch() {
  const input = document.getElementById("company-search");
  if (!input) return;

  input.addEventListener("input", () => {
    const query = input.value.trim().toLocaleLowerCase("en-IN");
    if (!query) {
      renderCompanyList();
      return;
    }

    const matches = INITIAL_COMPANIES.filter((company) => {
      const name = company.name.toLocaleLowerCase("en-IN");
      const symbol = company.symbol.toLocaleLowerCase("en-IN");
      return name.includes(query) || symbol.includes(query);
    });
    renderCompanyList(matches);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderCompanyList();
  configureSearch();
});
