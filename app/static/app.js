const form = document.getElementById("shorten-form");
const resultBox = document.getElementById("result");
const tableBody = document.querySelector("#links-table tbody");

async function loadLinks() {
  const res = await fetch("/api/links?page=1&per_page=20");
  const data = await res.json();
  tableBody.innerHTML = data.links.map(l => `
    <tr>
      <td><a href="/${l.short_code}" target="_blank">/${l.short_code}</a></td>
      <td>${l.long_url}</td>
      <td>${l.click_count}</td>
      <td>${l.expires_at ? new Date(l.expires_at).toLocaleDateString() : "-"}</td>
    </tr>
  `).join("");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const long_url = document.getElementById("long-url").value.trim();
  const custom_alias = document.getElementById("custom-alias").value.trim();
  const expires_in_days = document.getElementById("expires-in-days").value;

  const res = await fetch("/api/shorten", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ long_url, custom_alias, expires_in_days: expires_in_days || null }),
  });
  const data = await res.json();

  if (!res.ok) {
    resultBox.textContent = `Error: ${data.error}`;
  } else {
    resultBox.innerHTML = `Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
    form.reset();
    loadLinks();
  }
});

loadLinks();
