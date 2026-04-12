/**
 * MAF Platform – Shared Components
 * ナビゲーション等の共通 UI をレンダリング
 */

const NAV_ITEMS = {
  admin: [
    { label: "Dashboard", href: "/static/index.html", id: "dashboard" },
    { label: "Agents",    href: "/static/admin/agents.html", id: "agents" },
    { label: "Tools",     href: "/static/admin/tools.html", id: "tools" },
    { label: "Workflows", href: "/static/admin/workflows.html", id: "workflows" },
    { label: "Runs",      href: "/static/admin/runs.html", id: "runs" },
    { label: "Eval",      href: "/static/admin/eval.html", id: "eval" },
  ],
  user: [
    { label: "Agents",    href: "/static/user/agents.html", id: "agents" },
    { label: "Workflows", href: "/static/user/workflows.html", id: "workflows" },
    { label: "My Runs",   href: "/static/user/my-runs.html", id: "my-runs" },
  ],
};

/**
 * Render the app header with navigation.
 * @param {string} mode - "admin" or "user"
 * @param {string} activeId - id of the active nav item
 */
function renderNav(mode, activeId) {
  const header = document.getElementById("app-header");
  if (!header) return;

  const items = NAV_ITEMS[mode] || [];
  const navLinks = items
    .map((item) => {
      const cls = item.id === activeId ? "active" : "";
      return `<a href="${item.href}" class="${cls}">${item.label}</a>`;
    })
    .join("");

  const otherMode = mode === "admin" ? "user" : "admin";
  const otherHref = mode === "admin" ? "/static/user/agents.html" : "/static/index.html";

  header.innerHTML = `
    <span class="logo">MAF Platform</span>
    <nav>${navLinks}</nav>
    <div class="mode-switch">
      <a href="/static/index.html" class="${mode === "admin" ? "active" : ""}">Admin</a>
      <a href="${otherHref}" class="${mode === "user" ? "active" : ""}">User</a>
    </div>
  `;
}

/**
 * Helper to build an HTML table from data.
 */
function buildTable(columns, rows, opts = {}) {
  if (!rows || rows.length === 0) {
    return `<div class="empty-state">${opts.emptyMessage || "データがありません"}</div>`;
  }

  const thead = columns
    .map((col) => `<th>${col.label}</th>`)
    .join("");

  const tbody = rows
    .map((row) => {
      const clickAttr = opts.onRowClick
        ? `class="clickable" onclick="${opts.onRowClick(row)}"`
        : "";
      const cells = columns
        .map((col) => `<td>${col.render ? col.render(row) : (row[col.key] ?? "—")}</td>`)
        .join("");
      return `<tr ${clickAttr}>${cells}</tr>`;
    })
    .join("");

  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${thead}</tr></thead>
        <tbody>${tbody}</tbody>
      </table>
    </div>
  `;
}
