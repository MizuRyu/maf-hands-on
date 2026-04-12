/**
 * MAF Platform – API Client
 * fetch() ラッパー + レスポンス envelope 処理
 */

const API_BASE = "/api";

const api = {
  async get(path) {
    return this._request("GET", path);
  },

  async post(path, body) {
    return this._request("POST", path, body);
  },

  async patch(path, body) {
    return this._request("PATCH", path, body);
  },

  async del(path) {
    return this._request("DELETE", path);
  },

  async _request(method, path, body) {
    const url = `${API_BASE}${path}`;
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body !== undefined) {
      opts.body = JSON.stringify(body);
    }

    const res = await fetch(url, opts);

    if (res.status === 204) {
      return { code: 204 };
    }

    const json = await res.json();

    if (!res.ok) {
      const err = new Error(json.detail || `API error ${res.status}`);
      err.code = json.code || res.status;
      err.errorType = json.error_type || "unknown";
      err.detail = json.detail;
      throw err;
    }

    return json;
  },
};

/* --- Toast notifications --- */
function showToast(message, type = "success") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

/* --- Badge helper --- */
function statusBadge(status) {
  if (!status) return "";
  return `<span class="badge badge-${status}">${status}</span>`;
}

/* --- Date formatting --- */
function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("ja-JP", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
}

function formatDuration(ms) {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/* --- Loading state --- */
function showLoading(container) {
  container.innerHTML = '<div class="loading">Loading</div>';
}

function showEmpty(container, message = "データがありません") {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

/* --- Pagination helpers --- */
function buildQueryString(params) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== "" && v !== "all") {
      qs.set(k, v);
    }
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

/* --- URL param helpers --- */
function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}
