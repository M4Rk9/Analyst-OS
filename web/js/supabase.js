"use strict";

(function exposeAnalystDataClient(global) {
  const config = global.ANALYST_OS_CONFIG || {};

  function assertConfigured() {
    if (!config.supabaseUrl || !config.supabaseAnonKey) {
      throw new Error("Supabase browser configuration is not present.");
    }

    const url = new URL(config.supabaseUrl);
    if (url.protocol !== "https:") {
      throw new Error("Supabase URL must use HTTPS.");
    }
    return url;
  }

  async function select(table, query = "") {
    const baseUrl = assertConfigured();
    if (!/^[a-z][a-z0-9_]*$/u.test(table)) {
      throw new Error("Invalid table name.");
    }

    const endpoint = new URL(`/rest/v1/${table}`, baseUrl);
    endpoint.search = query;

    const response = await fetch(endpoint, {
      method: "GET",
      headers: {
        apikey: config.supabaseAnonKey,
        Authorization: `Bearer ${config.supabaseAnonKey}`,
        Accept: "application/json",
      },
      credentials: "omit",
      referrerPolicy: "strict-origin-when-cross-origin",
    });

    if (!response.ok) {
      throw new Error(`Data request failed with status ${response.status}.`);
    }
    return response.json();
  }

  global.AnalystDataClient = Object.freeze({ select });
})(window);
