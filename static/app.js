const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function highlight(text, keywords) {
  let out = escapeHtml(text);
  for (const kw of keywords) {
    if (kw.length < 2) continue;
    const re = new RegExp(`\\b(${kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    out = out.replace(re, "<mark>$1</mark>");
  }
  return out;
}

// citation markers [1] -> styled span
function styleCitations(html) {
  return html.replace(/\[(\d+)\]/g, '<span class="cite">[$1]</span>');
}

// ------------------------------------------------------------ status / LLM
async function refreshStatus() {
  const s = await api("/api/status");
  $("stat-docs").textContent = s.num_docs;
  $("stat-chunks").textContent = s.num_chunks;
  $("stat-vocab").textContent = s.vocab_size;
  const list = $("doc-list");
  list.innerHTML = s.docs.length
