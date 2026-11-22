// Legal bot client: WebSocket token pipeline + sources/debug panels.
const $ = (s) => document.querySelector(s);
// anonymous per-browser id: your chats are saved under it, so you can go back to them (no account needed)
const UID = (() => { try { let u = localStorage.getItem("legalbot_uid"); if (!u) { u = (crypto.randomUUID?.() || String(Math.random()).slice(2)).replace(/-/g, ""); localStorage.setItem("legalbot_uid", u); } return u; } catch { return "anon"; } })();
const store = { get: (k) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } }, set: (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch {} } };
const state = { ws: null, sessionId: null, busy: false, current: null, answers: {}, status: null, fm: {} };

// ---------------------------------------------------------------- markdown
// The bot tags general-knowledge sentences "[background]" for the accuracy checks; readers don't need to see it
// (the notice line at the top of the answer already says when it goes beyond the knowledge base).
const clean = (t) => (t || "").replace(/^([ \t]*(?:[-*>]|\d+\.)?[ \t]*)\[background\][ \t]*/gim, "$1").replace(/[ \t]*\[background\]/gi, "");
function md(text) {
  let html;
  text = clean(text);
  try { html = DOMPurify.sanitize(marked.parse(text || "")); }
  catch { html = (text || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])).replace(/\n/g, "<br>"); }
  return html.replace(/\[(S\d+)\]/g, '<span class="cite" data-label="$1">[$1]</span>');
}
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---------------------------------------------------------------- websocket
function connect() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws?uid=${UID}`);
  state.ws = ws;
  ws.onopen = () => $("#conn").classList.add("on");
  ws.onclose = () => { $("#conn").classList.remove("on"); setBusy(false); setTimeout(connect, 1500); };
  ws.onmessage = (e) => onEvent(JSON.parse(e.data));
}
setInterval(() => state.ws?.readyState === 1 && state.ws.send(JSON.stringify({ type: "ping" })), 25000);

function onEvent(ev) {
  const a = state.current;
  switch (ev.type) {
    case "session":
      if (state.sessionId !== ev.session_id) { state.sessionId = ev.session_id; loadSessions(); }
      if (a) a.trace_id = ev.trace_id;
      break;
    case "status":
      $("#stage").textContent = { understanding: "Understanding question…", retrieving: "Searching knowledge base…", generating: `Writing answer (${ev.provider})…` }[ev.stage] || ev.stage;
      break;
    case "meta": if (a) { a.meta = ev; renderMeta(a); } break;
    case "mode": if (a) { a.mode = ev.mode; renderMeta(a); } break;
    case "sources": if (a) { a.sources = ev.sources; a.confidence = ev.confidence; renderMeta(a); select(a); } break;
    case "reset": if (a) { a.text = ""; a.body.innerHTML = ""; } break;
    case "token":
      if (a) { a.text += ev.text; a.body.innerHTML = md(a.text); a.body.classList.add("typing"); scroll(); }
      break;
    case "error": if (a) a.error = ev.message; $("#stage").textContent = "⚠️ " + ev.message; break;
    case "stopped": if (a) { a.text += "\n\n_[stopped]_"; a.body.innerHTML = md(a.text); } setBusy(false); break;
    case "done":
      if (a) {
        if (ev.answer) a.text = ev.answer;
        Object.assign(a, { support: ev.support || {}, mode: ev.mode || a.mode, message_id: ev.message_id, trace_id: ev.trace_id || a.trace_id, validation: ev.validation, fallback: ev.fallback, timings: ev.timings_ms, total_ms: ev.total_ms });
        a.body.innerHTML = md(a.text); a.body.classList.remove("typing");
        renderMeta(a); select(a);
      }
      setBusy(false); $("#stage").textContent = ev.total_ms ? `Done in ${(ev.total_ms / 1000).toFixed(1)}s` : "";
      refreshStatus();
      break;
  }
}

// ---------------------------------------------------------------- chat
function addMsg(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.innerHTML = `<div class="bubble"></div><div class="meta-row"></div>`;
  $("#chat").appendChild(el);
  document.body.classList.add("has-chat");
  const body = el.querySelector(".bubble");
  if (role === "user") body.textContent = text; else body.innerHTML = md(text);
  scroll();
  return { el, body, metaEl: el.querySelector(".meta-row"), text: role === "user" ? text : (text || "") };
}
function scroll() { const c = $("#chat"); c.scrollTop = c.scrollHeight; }

function send() {
  const text = $("#input").value.trim();
  if (!text || state.busy || state.ws?.readyState !== 1) return;
  addMsg("user", text);
  const a = addMsg("assistant", "");
  a.body.classList.add("typing");
  const id = "a" + Date.now(); state.answers[id] = a; state.current = a;
  a.el.onclick = (e) => { if (!e.target.closest("button")) select(a); };
  state.ws.send(JSON.stringify({
    type: "ask", session_id: state.sessionId, message: text,
    ...(state.status?.public ? { api_key: store.get("legalbot_key_anthropic") } : {}),
    options: { intent: $("#opt-intent").value, topic: $("#opt-topic").value, provider: $("#opt-provider").value, strict: $("#opt-strict").checked },
  }));
  $("#input").value = ""; grow(); setBusy(true);
}
function setBusy(b) { state.busy = b; $("#send").hidden = b; $("#stop").hidden = !b; }
function clearChat() { document.querySelectorAll("#chat .msg").forEach((m) => m.remove()); document.body.classList.remove("has-chat"); }
function openDrawer(side) { document.body.classList.remove("left-open", "right-open"); if (side) document.body.classList.add(side + "-open"); }
function grow() { const t = $("#input"); t.style.height = "auto"; t.style.height = t.scrollHeight + "px"; }

function renderMeta(a) {
  const v = a.validation?.verdict;
  const chips = [];
  if (a.meta) {
    chips.push(`<span class="chip">${esc(a.meta.intent?.replace("_", " "))}</span>`);
    (a.meta.topics || []).forEach((t) => chips.push(`<span class="chip">${esc(t)}</span>`));
    if (a.meta.is_follow_up) chips.push(`<span class="chip" title="${esc(a.meta.rewritten_query)}">follow-up rewritten</span>`);
    if (a.meta.safety_flags?.length) chips.push(`<span class="badge warn">input flagged</span>`);
  }
  const MODES = { kb: ["pass", "From your knowledge base"], kb_low: ["warn", "Limited material in your knowledge base"],
    hybrid: ["warn", "Knowledge base + background knowledge"], web: ["warn", "Web sources (not in your knowledge base)"],
    chat: ["na", "General answer"] };
  if (a.mode && MODES[a.mode]) chips.unshift(`<span class="badge ${MODES[a.mode][0]}">${MODES[a.mode][1]}</span>`);
  if (a.validation?.word_limit) { const w = a.validation.words, L = a.validation.word_limit;
    chips.push(`<span class="badge ${w > L * 1.05 ? "warn" : "pass"}">${w} / ${L} words</span>`); }
  if (a.validation?.unsupported_authorities?.length) chips.push(`<span class="badge warn" title="${esc(a.validation.unsupported_authorities.join("; "))}">⚠︎ ${a.validation.unsupported_authorities.length} to verify</span>`);
  if (a.confidence != null) chips.push(`<span class="chip">confidence ${a.confidence.toFixed(2)}</span>`);
  if (a.fallback) chips.push(`<span class="badge warn">fallback: ${esc(a.fallback)}</span>`);
  if (v) chips.push(`<span class="badge ${v === "n/a" ? "na" : v}" title="${esc(JSON.stringify(a.validation))}">grounding ${esc(v)}</span>`);
  if (a.sources?.length) chips.push(`<button data-act="sources" title="Show sources and debug">Sources (${a.sources.length})</button>`);
  if (a.message_id) chips.push(`<button data-act="up" title="Good answer">👍</button><button data-act="down" title="Bad answer">👎</button><button data-act="issue" title="File a debug issue">⚑ report</button>`);
  a.metaEl.innerHTML = chips.join("");
  a.metaEl.querySelectorAll("button").forEach((b) => (b.onclick = () => act(a, b.dataset.act, b)));
}

async function act(a, kind, btn) {
  if (kind === "issue") return openIssue(a);
  if (kind === "sources") { select(a); switchTab("sources"); return openDrawer("right"); }
  fbFor = { a, rating: kind === "up" ? 1 : -1, btn };
  $("#fb-title").textContent = kind === "up" ? "👍 What was good?" : "👎 What was wrong?";
  $("#fb-comment").value = "";
  $("#fb-dlg").showModal();
}

function select(a) {
  document.querySelectorAll(".msg.selected").forEach((e) => e.classList.remove("selected"));
  a.el.classList.add("selected");
  renderSources(a);
  if (a.trace_id && a.validation) loadTrace(a.trace_id); else $("#tab-debug").innerHTML = `<p class="muted">Trace available when the answer finishes.</p>`;
}

function citeTitles(a) {   // hover an [S#] in the answer -> the exact passage it relies on
  a.body.querySelectorAll(".cite").forEach((c) => {
    const p = a.support?.[c.dataset.label]?.[0];
    if (p) c.title = p.passage;
  });
}

function renderSources(a) {
  citeTitles(a);
  const s = a.sources || [];
  $("#tab-sources").innerHTML = s.length ? s.map((x) => `
    <div class="src" id="src-${x.label}">
      <h4>[${x.label}] ${esc(x.title)}</h4>
      <div class="id">${esc(x.id)}</div>
      <div class="meta-row"><span class="chip">${esc(x.authority)}</span><span class="chip">${esc(x.kind)}</span>
        <span class="chip">${esc(x.retrieved_by)}</span><span class="chip">score ${x.score}</span></div>
      ${x.original_path ? `<div class="small muted">Original: ${esc(x.original_path)}</div>` : ""}
      ${(a.support?.[x.label] || []).map((p) => `<div class="support"><div class="support-label">Supports: “${esc(p.claim.slice(0, 160))}${p.claim.length > 160 ? "…" : ""}”</div><blockquote>${esc(p.passage)}</blockquote></div>`).join("")
        || (x.snippet ? `<div class="snip">${esc(x.snippet)}</div>` : "")}
    </div>`).join("") : `<p class="muted">No sources.</p>`;
}

document.addEventListener("click", (e) => {
  const c = e.target.closest(".cite"); if (!c) return;
  const m = c.closest(".msg"); const a = Object.values(state.answers).find((x) => x.el === m) || state.current;
  if (a) select(a);
  switchTab("sources"); openDrawer("right");
  const el = document.getElementById("src-" + c.dataset.label);
  if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.classList.add("hl"); setTimeout(() => el.classList.remove("hl"), 1500); }
});

// ---------------------------------------------------------------- debug panel
async function loadTrace(id) {
  const t = await api(`/api/traces/${id}`).catch(() => null);
  if (!t) return;
  const d = t.retrieval_debug || {};
  const row = (k, v) => `<div class="kv"><b>${k}</b> ${esc(typeof v === "string" ? v : JSON.stringify(v))}</div>`;
  const bm = d.bm25 || {}, vec = d.vector || {};
  $("#tab-debug").innerHTML = `
    ${row("trace", t.trace_id)}${row("intent", `${t.intent} (${t.intent_confidence}) — ${t.intent_reason}`)}
    ${row("topics", t.topics)}${row("rewritten", t.rewritten_query)}${row("confidence", t.confidence)}
    ${row("validation", t.validation)}${row("timings ms", t.timings_ms)}${row("provider", t.provider_info || t.provider)}
    ${t.safety_flags?.length ? row("safety flags", t.safety_flags) : ""}
    ${d.topic_filter_relaxed ? row("note", "topic filter relaxed (no hits in routed topic)") : ""}
    <h5>FM1 · BM25 tokens</h5>
    ${row("query tokens", bm.query_tokens)}${row("synonyms added", bm.synonym_expansions)}${row("missing in KB", bm.missing_tokens)}
    <table class="dbg"><tr><th>#</th><th>section</th><th>score</th><th>matched</th></tr>
      ${(bm.hits || []).slice(0, 8).map((h, i) => `<tr><td>${i + 1}</td><td class="id">${esc(h.id)}</td><td>${h.score}</td><td>${esc(JSON.stringify(h.matched_tokens))}</td></tr>`).join("")}</table>
    <h5>FM2 · Vector chunks ${vec.enabled ? "" : "(disabled)"}</h5>
    <table class="dbg"><tr><th>#</th><th>source / chunk</th><th>dist</th></tr>
      ${(vec.hits || []).slice(0, 8).map((h, i) => `<tr><td>${i + 1}</td><td class="id">${esc(h.source)} · c${h.chunk_index}</td><td>${h.distance}</td></tr>`).join("")}</table>
    <h5>Fusion → rerank</h5>
    <table class="dbg"><tr><th>section</th><th>by</th><th>bm25#</th><th>vec#</th><th>rerank</th></tr>
      ${(d.fused || []).map((f) => `<tr><td class="id">${esc(f.id)}</td><td>${f.by.join("+")}</td><td>${f.bm25_rank ?? ""}</td><td>${f.vec_rank ?? ""}</td><td>${f.rerank ?? ""}</td></tr>`).join("")}</table>`;
}

async function loadTraces() {
  const ts = await api("/api/traces?limit=60");
  $("#tab-traces").innerHTML = ts.map((t) => `<div class="trace-row" data-id="${t.trace_id}">
      <div>${esc((t.question || "").slice(0, 90))}</div>
      <div class="muted">${esc(t.intent)} · conf ${t.confidence ?? "–"} · ${esc(t.validation_verdict)}${t.fallback ? " · " + esc(t.fallback) : ""}</div></div>`).join("") || `<p class="muted">No logs yet.</p>`;
  $("#tab-traces").querySelectorAll(".trace-row").forEach((r) => (r.onclick = () => { loadTrace(r.dataset.id); switchTab("debug"); }));
}

function switchTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.id === "tab-" + name));
  if (name === "traces") loadTraces();
}
document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => switchTab(b.dataset.tab)));

// ---------------------------------------------------------------- feedback (thumbs + comment)
let fbFor = null;
$("#fb-save").onclick = async () => {
  if (!fbFor) return;
  const { a, rating, btn } = fbFor;
  const r = await api("/api/feedback", "POST", { message_id: a.message_id, session_id: state.sessionId, rating, comment: $("#fb-comment").value });
  btn.textContent = rating > 0 ? "✅" : "📝";
  $("#stage").textContent = r.saved ? `Feedback saved → ${r.saved}` : "Feedback saved";
};

// ---------------------------------------------------------------- issues
let issueFor = null;
function openIssue(a) {
  issueFor = a;
  $("#issue-fm").innerHTML = Object.entries(state.fm).map(([k, v]) => `<option value="${k}">${k} — ${esc(v)}</option>`).join("");
  $("#issue-note").value = ""; $("#issue-expected").value = "";
  $("#issue-dlg").showModal();
}
$("#issue-save").onclick = async () => {
  if (!issueFor?.trace_id) return;
  const r = await api("/api/issues", "POST", { trace_id: issueFor.trace_id, failure_mode: $("#issue-fm").value, note: $("#issue-note").value, expected_source: $("#issue-expected").value });
  $("#stage").textContent = `Issue saved → ${r.folder}`;
};

// ---------------------------------------------------------------- sessions + status
async function loadSessions() {
  const ss = await api("/api/sessions");
  $("#sessions").innerHTML = ss.map((s) => `<li data-id="${s.id}" class="${s.id === state.sessionId ? "active" : ""}"><span>${esc(s.title)}</span><button class="del" title="Delete">×</button></li>`).join("");
  $("#sessions").querySelectorAll("li").forEach((li) => {
    li.onclick = (e) => e.target.classList.contains("del") ? delSession(li.dataset.id) : openSession(li.dataset.id);
  });
}
async function openSession(id) {
  state.sessionId = id; clearChat(); openDrawer(null);
  const msgs = await api(`/api/sessions/${id}`);
  for (const m of msgs) {
    const a = addMsg(m.role, m.content);
    if (m.role === "assistant") {
      Object.assign(a, { support: m.meta.support || {}, mode: m.meta.mode, message_id: m.id, trace_id: m.meta.trace_id, validation: m.meta.validation, fallback: m.meta.fallback, confidence: m.meta.confidence, meta: { intent: m.meta.intent, topics: [] }, sources: m.meta.sources });
      state.answers["m" + m.id] = a;
      renderMeta(a); a.el.onclick = (e) => { if (!e.target.closest("button")) select(a); };
    }
  }
  loadSessions();
}
async function delSession(id) {
  if (!confirm("Delete this chat?")) return;
  await api(`/api/sessions/${id}`, "DELETE");
  if (id === state.sessionId) newChat();
  loadSessions();
}
function newChat() { state.sessionId = null; clearChat(); openDrawer(null); $("#tab-sources").innerHTML = ""; $("#tab-debug").innerHTML = ""; loadSessions(); }

async function refreshStatus() {
  const s = await api("/api/status"); state.status = s;
  if (s.public) {
    document.body.classList.add("public");
    s.settings.keys_set = store.get("legalbot_key_anthropic") ? ["anthropic"] : [];
  }
  $("#topics").innerHTML = s.topics.map((t) => `<li><span>${esc(t.name)}</span><span class="date" title="last indexed ${esc(t.last_indexed)}">upd ${esc(t.last_updated || "–")}</span></li>`).join("") || `<li class="muted">No topics yet</li>`;
  const ix = s.index;
  $("#kb-meta").innerHTML = ix ? `${ix.sections} sections · ${ix.chunks} chunks${ix.vector ? "" : " · vector off"}<br>Review queue: ${s.review_queue}` : "Index not built yet";
  const topicSel = $("#opt-topic"), cur = topicSel.value;
  topicSel.innerHTML = `<option value="">Auto-route</option>` + s.topics.map((t) => `<option value="${t.slug}">${esc(t.name)}</option>`).join("");
  topicSel.value = cur;
  for (const sel of [$("#opt-provider"), $("#set-provider")]) {
    const c = sel.value;
    sel.innerHTML = s.providers.map((p) => `<option value="${p}">${p}${s.settings.keys_set.includes(p) ? " 🔑" : ""}</option>`).join("");
    sel.value = c || s.settings.provider;
  }
}

$("#open-settings").onclick = () => { $("#set-provider").value = $("#opt-provider").value; $("#settings-dlg").showModal(); };
$("#save-settings").onclick = async () => {
  const key = $("#set-key").value;
  if (state.status?.public) {   // public site: the key never leaves your browser except with your own questions
    if (key) store.set("legalbot_key_" + $("#set-provider").value, key);
    $("#set-key").value = ""; $("#opt-provider").value = $("#set-provider").value; refreshStatus(); return;
  }
  await api("/api/settings", "POST", { provider: $("#set-provider").value, model: $("#set-model").value, ...(key ? { api_key: key, remember_key: $("#set-remember").checked } : {}) });
  $("#set-key").value = ""; $("#opt-provider").value = $("#set-provider").value; refreshStatus();
};
$("#opt-provider").onchange = () => api("/api/settings", "POST", { provider: $("#opt-provider").value });
$("#opt-strict").onchange = () => api("/api/settings", "POST", { strict: $("#opt-strict").checked });

async function api(url, method = "GET", body) {
  const headers = { "X-Legalbot-User": UID, ...(body ? { "Content-Type": "application/json" } : {}) };
  const r = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

// ---------------------------------------------------------------- fix knowledge gaps (Claude job)
async function fixStatus() {
  const s = await api("/api/fix-gaps").catch(() => null);
  if (!s) return;
  const txt = s.running ? `Running: ${s.step || "…"}`
    : s.state === "done" ? `Last run done · report: ${s.report}`
    : s.state === "error" ? `Last run failed: ${s.step}` : "Not run yet";
  $("#fix-status").textContent = `${s.open_gaps} open gaps · ${txt}`;
  $("#fix-gaps").disabled = s.running || !s.open_gaps;
  if (s.running) setTimeout(fixStatus, 5000);
}
$("#fix-gaps").onclick = async () => {
  if (!confirm("Claude (Sonnet, your Claude login) will look up the missing cases/Acts on official sites, download them into the knowledge base and write a report in improvement/gap_fixes/. This uses your Claude plan's usage. Continue?")) return;
  await api("/api/fix-gaps", "POST");
  fixStatus();
};
$("#menu-btn").addEventListener("click", fixStatus);

// ---------------------------------------------------------------- boot
$("#composer").onsubmit = (e) => { e.preventDefault(); send(); };
$("#input").addEventListener("input", grow);
$("#menu-btn").onclick = () => openDrawer(document.body.classList.contains("left-open") ? null : "left");
$("#scrim").onclick = () => openDrawer(null);
$("#close-panel").onclick = () => openDrawer(null);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") openDrawer(null); });
$("#input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
$("#stop").onclick = () => state.ws?.send(JSON.stringify({ type: "stop" }));
$("#new-chat").onclick = newChat;
(async () => {
  state.fm = await api("/api/failure-modes");
  await refreshStatus(); await loadSessions(); connect();
})();
