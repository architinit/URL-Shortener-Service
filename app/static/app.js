const form = document.getElementById("shorten-form");
const resultBox = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");
const aliasInput = document.getElementById("custom-alias");
const tableBody = document.querySelector("#links-table tbody");
const emptyState = document.getElementById("empty-state");
const linksCountEl = document.getElementById("links-count");
const paginationEl = document.getElementById("pagination");
const toastContainer = document.getElementById("toast-container");
const themeToggleBtn = document.getElementById("theme-toggle");
const root = document.documentElement;

const ALIAS_RE = /^[a-zA-Z0-9_-]{3,16}$/;

const state = { page: 1, perPage: 10, total: 0, hasNext: false };
let openStatsCode = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function showToast(message, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast("Copied to clipboard", "success");
  } catch {
    showToast("Could not copy — please copy manually", "error");
  }
}

function applyTheme(theme) {
  root.setAttribute("data-theme", theme);
  themeToggleBtn.textContent = theme === "dark" ? "☀️" : "🌙";
}

function initTheme() {
  const saved = localStorage.getItem("theme");
  const theme = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  applyTheme(theme);
}

themeToggleBtn.addEventListener("click", () => {
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  applyTheme(next);
});

function expiryBadge(expiresAt) {
  if (!expiresAt) return `<span class="badge never">Never</span>`;
  const expired = new Date(expiresAt) < new Date();
  if (expired) return `<span class="badge expired">Expired</span>`;
  return `<span class="badge active">${new Date(expiresAt).toLocaleDateString()}</span>`;
}

function renderRow(l) {
  return `
    <tr data-code="${l.short_code}">
      <td><a class="short-pill" href="/${l.short_code}" target="_blank" rel="noopener">/${l.short_code}</a></td>
      <td><span class="long-url" title="${escapeHtml(l.long_url)}">${escapeHtml(l.long_url)}</span></td>
      <td>${l.click_count}</td>
      <td>${expiryBadge(l.expires_at)}</td>
      <td class="actions-cell">
        <button type="button" class="icon-btn stats-toggle" data-code="${l.short_code}">Stats</button>
        <button type="button" class="danger-btn delete-btn" data-code="${l.short_code}">Delete</button>
      </td>
    </tr>
  `;
}

function renderPagination() {
  const totalPages = Math.max(1, Math.ceil(state.total / state.perPage));
  paginationEl.innerHTML = `
    <button type="button" class="ghost" id="prev-page" ${state.page <= 1 ? "disabled" : ""}>← Prev</button>
    <span>Page ${state.page} of ${totalPages}</span>
    <button type="button" class="ghost" id="next-page" ${!state.hasNext ? "disabled" : ""}>Next →</button>
  `;
  document.getElementById("prev-page").addEventListener("click", () => loadLinks(state.page - 1));
  document.getElementById("next-page").addEventListener("click", () => loadLinks(state.page + 1));
}

async function loadLinks(page = state.page) {
  state.page = Math.max(page, 1);
  const res = await fetch(`/api/links?page=${state.page}&per_page=${state.perPage}`);
  const data = await res.json();
  state.total = data.total;
  state.hasNext = data.has_next;

  linksCountEl.textContent = data.total ? `${data.total} link${data.total === 1 ? "" : "s"}` : "";

  if (data.links.length === 0) {
    tableBody.innerHTML = "";
    emptyState.style.display = "block";
  } else {
    emptyState.style.display = "none";
    tableBody.innerHTML = data.links.map(renderRow).join("");
  }

  renderPagination();
  return data;
}

async function toggleStats(btn) {
  const code = btn.dataset.code;
  const row = btn.closest("tr");

  document.querySelectorAll(".stats-row").forEach((r) => r.remove());
  document.querySelectorAll(".stats-toggle").forEach((b) => (b.textContent = "Stats"));

  if (openStatsCode === code) {
    openStatsCode = null;
    return;
  }

  openStatsCode = code;
  btn.textContent = "Loading…";

  const res = await fetch(`/api/stats/${code}`);
  if (!res.ok) {
    btn.textContent = "Stats";
    openStatsCode = null;
    showToast("Could not load stats", "error");
    return;
  }
  const data = await res.json();
  btn.textContent = "Hide";

  const clicksHtml = data.recent_clicks.length
    ? data.recent_clicks
        .slice(0, 5)
        .map(
          (c) => `
        <div class="click-item">
          <span>${new Date(c.clicked_at).toLocaleString()}</span>
          <span>${escapeHtml(c.referrer || "direct")}</span>
        </div>`
        )
        .join("")
    : `<div class="empty-clicks">No clicks yet.</div>`;

  const statsRow = document.createElement("tr");
  statsRow.className = "stats-row";
  statsRow.innerHTML = `<td colspan="5"><strong>${data.click_count}</strong> total click${data.click_count === 1 ? "" : "s"}${data.recent_clicks.length ? " — recent:" : ""}${clicksHtml}</td>`;
  row.after(statsRow);
}

async function handleDelete(code) {
  if (!confirm(`Delete short link /${code}? This can't be undone.`)) return;

  const res = await fetch(`/api/links/${code}`, { method: "DELETE" });
  if (!res.ok) {
    showToast("Failed to delete link", "error");
    return;
  }
  showToast(`Deleted /${code}`, "success");
  openStatsCode = null;
  const data = await loadLinks(state.page);
  if (data.links.length === 0 && state.page > 1) {
    loadLinks(state.page - 1);
  }
}

tableBody.addEventListener("click", (e) => {
  const statsBtn = e.target.closest(".stats-toggle");
  const deleteBtn = e.target.closest(".delete-btn");
  if (statsBtn) toggleStats(statsBtn);
  else if (deleteBtn) handleDelete(deleteBtn.dataset.code);
});

aliasInput.addEventListener("input", () => {
  const val = aliasInput.value.trim();
  aliasInput.classList.toggle("invalid", val.length > 0 && !ALIAS_RE.test(val));
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const long_url = document.getElementById("long-url").value.trim();
  const custom_alias = aliasInput.value.trim();
  const expires_in_days = document.getElementById("expires-in-days").value;

  submitBtn.disabled = true;
  submitBtn.textContent = "Shortening…";

  try {
    const res = await fetch("/api/shorten", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ long_url, custom_alias, expires_in_days: expires_in_days || null }),
    });
    const data = await res.json();

    if (!res.ok) {
      resultBox.className = "visible error";
      resultBox.textContent = data.error || "Something went wrong.";
      showToast(data.error || "Something went wrong.", "error");
    } else {
      resultBox.className = "visible success";
      resultBox.innerHTML = `
        <div class="result-row">
          <a href="${data.short_url}" target="_blank" rel="noopener">${data.short_url}</a>
          <button type="button" class="icon-btn" id="copy-btn">Copy</button>
        </div>
      `;
      document.getElementById("copy-btn").addEventListener("click", () => copyToClipboard(data.short_url));
      form.reset();
      aliasInput.classList.remove("invalid");
      showToast("Short link created", "success");
      loadLinks(1);
    }
  } catch (err) {
    resultBox.className = "visible error";
    resultBox.textContent = "Network error — is the server running?";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Shorten link";
  }
});

initTheme();
loadLinks();
