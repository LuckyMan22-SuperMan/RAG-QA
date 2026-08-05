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
    ? s.docs.map((d) => `<li>
        <span class="dname" title="${escapeHtml(d.name)}">${escapeHtml(d.name)}</span>
        <span class="badge">${d.chunks} chunks</span>
        <button class="doc-remove" data-name="${escapeHtml(d.name)}" title="Remove this file">&times;</button>
      </li>`).join("")
    : `<li class="muted">Nothing indexed yet.</li>`;
  list.querySelectorAll(".doc-remove").forEach((btn) =>
    btn.addEventListener("click", () => removeDoc(btn.dataset.name)));

  const badge = $("llm-badge");
  if (s.llm.available) { badge.className = "pill on"; badge.textContent = `LLM: ${s.llm.model}`; }
  else { badge.className = "pill off"; badge.textContent = "LLM: off (extractive)"; }
}

// ------------------------------------------------------------ ingest
const dz = $("dropzone");
const fileInput = $("file-input");
dz.addEventListener("click", () => fileInput.click());
dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("drag"); });
dz.addEventListener("dragleave", () => dz.classList.remove("drag"));
dz.addEventListener("drop", (e) => { e.preventDefault(); dz.classList.remove("drag"); if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); });
fileInput.addEventListener("change", () => { if (fileInput.files.length) uploadFiles(fileInput.files); });

async function uploadFiles(files) {
  $("ingest-error").textContent = "";
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const prev = dz.innerHTML;
  dz.innerHTML = `<div class="dz-icon"><span class="spinner"></span></div><p>Indexing ${files.length} file(s)…</p>`;
  try {
    const r = await api("/api/ingest", { method: "POST", body: fd });
    await refreshStatus();
    if (r.errors && r.errors.length) {
      $("ingest-error").textContent = r.errors.map((e) => `${e.name}: ${e.error}`).join("; ");
    }
  } catch (e) {
    $("ingest-error").textContent = e.message;
  } finally {
    dz.innerHTML = prev;
    fileInput.value = "";
  }
}

// ------------------------------------------------------------ remove single doc
async function removeDoc(name) {
  $("ingest-error").textContent = "";
  try {
    const fd = new FormData();
    fd.append("name", name);
    await api("/api/remove", { method: "POST", body: fd });
    await refreshStatus();
  } catch (e) {
    $("ingest-error").textContent = e.message;
  }
}
async function ask() {
  const q = $("question").value.trim();
  $("ask-error").textContent = "";
  if (!q) { $("ask-error").textContent = "Enter a question."; return; }
  const btn = $("ask-btn");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>`;
  try {
    const fd = new FormData();
    fd.append("question", q);
    fd.append("top_k", $("topk").value);
    fd.append("mode", $("mode").value);
    const r = await api("/api/ask", { method: "POST", body: fd });
    renderAnswer(r);
  } catch (e) {
    $("ask-error").textContent = e.message;
  } finally {
    btn.disabled = false; btn.textContent = "Ask";
  }
}
