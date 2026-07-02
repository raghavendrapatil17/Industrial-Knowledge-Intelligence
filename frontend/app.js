/* App controller: 5-agent platform — copilot, knowledge graph, RCA, compliance, lessons. */
const $ = (s) => document.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };

const SAMPLE_QS = [
  "What do we know about PUMP-204's failure history and any related safety concerns?",
  "What OISD requirement applies to hot work near Unit-3?",
  "Why does PUMP-204's mechanical seal keep failing?",
  "What safety procedure covers confined space entry in Area-7?",
];

let answerGraph = null, fullGraph = null;
let fullGraphCache = null;
const loaded = { overview: false, graph: false, rca: false, compliance: false, lessons: false };

document.addEventListener("DOMContentLoaded", init);

async function init() {
  answerGraph = new ForceGraph($("#graph"), $("#tooltip"));
  answerGraph.onDocClick = openDoc; answerGraph.onEntityClick = openAsset360;
  fullGraph = new ForceGraph($("#fullgraph"), $("#tooltip2"));
  fullGraph.onDocClick = openDoc; fullGraph.onEntityClick = openAsset360;
  buildLegend("#legend", false); buildLegend("#legend2", true);

  const s = $("#samples");
  SAMPLE_QS.forEach((q) => {
    const c = el("span", "chip", q.length > 46 ? q.slice(0, 45) + "…" : q);
    c.title = q; c.onclick = () => { $("#q").value = q; ask(q); };
    s.appendChild(c);
  });

  $("#askForm").addEventListener("submit", (e) => { e.preventDefault(); const q = $("#q").value.trim(); if (q) ask(q); });
  $("#modalClose").onclick = () => ($("#modal").hidden = true);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("#modal").hidden = true; });
  $("#a360Close").onclick = () => ($("#asset360").hidden = true);
  $("#asset360").addEventListener("click", (e) => { if (e.target.id === "asset360") $("#asset360").hidden = true; });

  document.querySelectorAll(".nav").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.view)));
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchCopilotTab(t.dataset.tab)));
  $("#rcaSelect").addEventListener("change", (e) => runRCA(e.target.value));

  // uploads
  $("#uploadBtn").onclick = () => $("#fileInput").click();
  $("#fileInput").addEventListener("change", (e) => { if (e.target.files[0]) uploadFile(e.target.files[0]); });
  // exports
  $("#rcaExport").onclick = () => { const id = $("#rcaSelect").value; if (id) window.open("/api/export/rca/" + encodeURIComponent(id), "_blank"); };
  $("#compExport").onclick = () => window.open("/api/export/compliance", "_blank");
  // benchmark
  $("#benchBtn").onclick = runBenchmark;
  // graph search + clear chat
  $("#graphSearch").addEventListener("input", (e) => { const n = fullGraph.searchNodes(e.target.value); });
  $("#clearChat").onclick = clearConversation;
  // voice + command palette
  setupVoice();
  setupCommandPalette();

  await loadHealth();
  await loadOverview();
}

/* ================= VOICE INPUT (field mode) ================= */
function setupVoice() {
  const btn = $("#micBtn");
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { btn.style.display = "none"; return; }   // graceful: hide if unsupported
  const rec = new SR();
  rec.lang = "en-IN"; rec.interimResults = false; rec.maxAlternatives = 1;
  let listening = false;
  btn.onclick = () => { listening ? rec.stop() : rec.start(); };
  rec.onstart = () => { listening = true; btn.classList.add("rec"); $("#q").placeholder = "Listening…"; };
  rec.onend = () => { listening = false; btn.classList.remove("rec"); $("#q").placeholder = "Ask about equipment, permits, procedures, regulations…"; };
  rec.onerror = () => { toast("Voice input", "Mic unavailable or permission denied", "err"); };
  rec.onresult = (e) => { const t = e.results[0][0].transcript; $("#q").value = t; ask(t); };
}

/* ================= COMMAND PALETTE (Ctrl/Cmd+K) ================= */
let cmdItems = [], cmdSel = 0, cmdEquip = [];
function setupCommandPalette() {
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); }
    else if (e.key === "Escape" && !$("#cmdk").hidden) closeCmdk();
  });
  $("#cmdkInput").addEventListener("input", (e) => renderCmdk(e.target.value));
  $("#cmdkInput").addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); cmdSel = Math.min(cmdSel+1, cmdItems.length-1); paintCmdkSel(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); cmdSel = Math.max(cmdSel-1, 0); paintCmdkSel(); }
    else if (e.key === "Enter") { e.preventDefault(); if (cmdItems[cmdSel]) cmdItems[cmdSel].run(); }
  });
  $("#cmdk").addEventListener("click", (e) => { if (e.target.id === "cmdk") closeCmdk(); });
}
async function openCmdk() {
  if (!cmdEquip.length) { try { cmdEquip = (await (await fetch("/api/equipment")).json()).equipment; } catch(e){} }
  $("#cmdk").hidden = false; $("#cmdkInput").value = ""; renderCmdk(""); $("#cmdkInput").focus();
}
function closeCmdk() { $("#cmdk").hidden = true; }
function renderCmdk(qraw) {
  const q = qraw.toLowerCase().trim();
  const views = [
    ["overview","Operations Overview"],["copilot","Expert Copilot"],["graph","Ingestion & Knowledge Graph"],
    ["rca","Maintenance & RCA"],["compliance","Compliance"],["lessons","Lessons Learned"]];
  const items = [];
  views.forEach(([v,label]) => items.push({ icon:"view", label:"Go to "+label, kind:"View", run:()=>{closeCmdk(); switchView(v);} }));
  cmdEquip.forEach((e) => items.push({ icon:TYPE_COLORS.equipment, label:"Asset 360 · "+e, kind:"Asset", run:()=>{closeCmdk(); openAsset360(e);} }));
  if (q) items.push({ icon:"ask", label:`Ask: “${qraw}”`, kind:"Query", run:()=>{closeCmdk(); switchView("copilot").then(()=>ask(qraw));} });
  cmdItems = items.filter(it => !q || it.label.toLowerCase().includes(q) || it.kind==="Query").slice(0, 8);
  cmdSel = 0;
  const list = $("#cmdkList");
  list.innerHTML = cmdItems.map((it,i)=>{
    const dot = it.icon && it.icon.startsWith("#") ? `<span class="dot" style="background:${it.icon}"></span>`
      : `<span class="dot" style="background:var(--accent)"></span>`;
    return `<div class="cmdk-item ${i===0?'sel':''}" data-i="${i}">${dot}<span>${escapeHtml(it.label)}</span><span class="kind">${it.kind}</span></div>`;
  }).join("") || `<div class="cmdk-item"><span>No matches</span></div>`;
  list.querySelectorAll(".cmdk-item[data-i]").forEach(n=> n.onclick = () => cmdItems[+n.dataset.i].run());
}
function paintCmdkSel() {
  document.querySelectorAll(".cmdk-item").forEach((n,i)=> n.classList.toggle("sel", i===cmdSel));
  const sel = document.querySelectorAll(".cmdk-item")[cmdSel]; if (sel) sel.scrollIntoView({block:"nearest"});
}

async function loadHealth() {
  try {
    const h = await (await fetch("/api/health")).json();
    const m = $("#modeBadge");
    if (!h.index_built) { m.textContent = "Index not built"; m.className = "badge badge-offline"; }
    else if (h.llm_available) { m.textContent = "LLM: " + h.llm_provider; m.className = "badge badge-llm"; }
    else { m.textContent = "Offline mode (extractive)"; m.className = "badge badge-offline"; }
    const docs = await (await fetch("/api/documents")).json();
    $("#docBadge").textContent = docs.documents.length + " documents";
    $("#docBadge").className = "badge badge-doc";
  } catch (e) { $("#modeBadge").textContent = "server offline"; }
}

const _hiddenTypes = new Set();
function buildLegend(sel, interactive) {
  const items = [["equipment","Equipment"],["personnel","Personnel"],["regulatory","Regulatory"],
    ["location","Location"],["material","Material"],["document","Document"]];
  const host = $(sel);
  host.innerHTML = items.map(([k,l]) =>
    `<span class="li" data-type="${k}"><span class="dot" style="background:${TYPE_COLORS[k]}"></span>${l}</span>`).join("");
  if (interactive) {
    host.querySelectorAll(".li").forEach((li) => li.onclick = () => {
      const t = li.dataset.type;
      if (_hiddenTypes.has(t)) { _hiddenTypes.delete(t); li.classList.remove("off"); }
      else { _hiddenTypes.add(t); li.classList.add("off"); }
      fullGraph.setHidden(_hiddenTypes);
    });
  }
}

/* animate a number from 0 -> target, preserving prefix/suffix (e.g. "~10 ms", "67%") */
function countUp(el) {
  const m = (el.textContent || "").match(/^(\D*)(\d+)(.*)$/);
  if (!m) return;
  const pre = m[1], target = +m[2], suf = m[3];
  const dur = 650, t0 = performance.now();
  const tick = (now) => {
    const p = Math.min((now - t0) / dur, 1);
    const val = Math.round((1 - Math.pow(1 - p, 3)) * target);
    el.textContent = pre + val + suf;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
function animateNumbers(sel) { document.querySelectorAll(sel).forEach(countUp); }

/* ---------------- view navigation ---------------- */
async function switchView(name) {
  document.querySelectorAll(".nav").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
  if (name === "overview" && !loaded.overview) await loadOverview();
  if (name === "graph") { fullGraph.resize(); await loadFullGraph(); }
  if (name === "copilot") { answerGraph.resize(); answerGraph._draw(); }
  if (name === "rca" && !loaded.rca) await initRCA();
  if (name === "compliance" && !loaded.compliance) await loadCompliance();
  if (name === "lessons" && !loaded.lessons) await loadLessons();
}

/* ================= COPILOT ================= */
async function ask(q) {
  addUser(q); $("#q").value = "";
  const btn = $("#askBtn"); btn.disabled = true;
  const thinking = addThinking();
  try {
    const res = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
    const data = await res.json();
    thinking.remove();
    if (!res.ok) { addBotText(data.detail || "Something went wrong."); return; }
    renderAnswer(data);
    switchCopilotTab("answer");
    const hi = new Set([...data.entities.map(e => e.id), ...data.citations.map(c => c.doc_id)]);
    $("#graphEmpty").style.display = "none";
    answerGraph.setData(data.graph, [...hi]);
  } catch (e) { thinking.remove(); addBotText("Could not reach the server. Is it running?"); }
  finally { btn.disabled = false; $("#q").focus(); }
}

function renderAnswer(d) {
  const wrap = el("div", "msg bot");
  wrap.appendChild(el("div", "answer-meta",
    `<span class="conf ${d.confidence_label}">${d.confidence_label} confidence · ${(d.confidence*100).toFixed(0)}%</span>` +
    `<span class="meta-pill">${d.mode === "llm" ? "🤖 LLM answer" : "📄 Extractive answer"}</span>` +
    `<span class="meta-pill">⚡ ${d.elapsed_ms} ms</span>` +
    `<span class="meta-pill">${d.citations.length} sources</span>`));
  wrap.appendChild(el("div", "answer-body", linkifyCitations(d.answer)));
  if (d.entities.length) {
    const ents = el("div", "entities");
    const order = ["equipment","location","regulatory","personnel","material","document"];
    d.entities.sort((a,b)=>order.indexOf(a.type)-order.indexOf(b.type)).forEach((e) => {
      const x = el("span", "ent", `<span class="dot" style="background:${TYPE_COLORS[e.type]||'#ccc'}"></span><b>${e.id}</b>`);
      x.title = "Asset 360: " + e.type; x.style.cursor = "pointer";
      x.onclick = () => openAsset360(e.id);
      ents.appendChild(x);
    });
    wrap.appendChild(ents);
  }
  // answer actions (copy)
  const actions = el("div", "ans-actions");
  const copyBtn = el("button", "mini-btn", "⧉ Copy answer");
  copyBtn.onclick = () => {
    const srcs = d.citations.map(c => c.doc_id).join(", ");
    navigator.clipboard.writeText(d.answer + "\n\nSources: " + srcs).then(
      () => { copyBtn.textContent = "✓ Copied"; setTimeout(() => copyBtn.textContent = "⧉ Copy answer", 1500); },
      () => toast("Copy failed", "", "err"));
  };
  actions.appendChild(copyBtn);
  wrap.appendChild(actions);

  // follow-up suggestions
  if (d.follow_ups && d.follow_ups.length) {
    const fu = el("div", "followups", `<div class="fu-label">Suggested follow-ups</div>`);
    d.follow_ups.forEach((q) => {
      const b = el("button", "fu"); b.textContent = q; b.onclick = () => ask(q);
      fu.appendChild(b);
    });
    wrap.appendChild(fu);
  }

  // grounded highlighting: map doc -> supporting sentences
  const hlMap = {};
  d.citations.forEach((c) => { hlMap[c.doc_id] = c.highlights || []; });

  $("#chat").appendChild(wrap);
  wrap.querySelectorAll(".cite").forEach((c) => c.onclick = () => openDoc(c.dataset.doc, hlMap[c.dataset.doc]));
  scrollChat();
}

function linkifyCitations(text) {
  const esc = text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  return esc.replace(/\[([A-Za-z0-9._-]+)\]/g, (m, id) => {
    const doc = /\.(txt|pdf|md)$/.test(id) ? id : id + ".txt";
    return `<span class="cite" data-doc="${doc}" title="Open ${doc}">${id}</span>`;
  });
}

function clearConversation() {
  $("#chat").innerHTML = `<div class="msg system"><p>Conversation cleared. Ask a new question to search the knowledge base.</p></div>`;
  answerGraph.setData({ nodes: [], edges: [] }, []);
  $("#graphEmpty").style.display = "grid";
}
function addUser(q){ $("#chat").appendChild(el("div","msg user")).textContent=q; scrollChat(); }
function addBotText(t){ $("#chat").appendChild(el("div","msg bot")).textContent=t; scrollChat(); }
function addThinking(){ const d=el("div","msg bot",'<span class="typing"><span></span><span></span><span></span></span>'); $("#chat").appendChild(d); scrollChat(); return d; }
function scrollChat(){ const c=$("#chat"); c.scrollTop=c.scrollHeight; }

async function switchCopilotTab(name) {
  document.querySelectorAll("#view-copilot .tab").forEach((t)=>t.classList.toggle("active", t.dataset.tab===name));
  const docsView = $("#docsView"), graphWrap = $("#graphWrap");
  if (name === "docs") { graphWrap.style.display="none"; docsView.classList.add("show"); docsView.hidden=false; await renderDocs(); }
  else { docsView.classList.remove("show"); docsView.hidden=true; graphWrap.style.display="block"; answerGraph.resize(); answerGraph._draw(); }
}

async function renderDocs() {
  const v = $("#docsView");
  const data = await (await fetch("/api/documents")).json();
  v.innerHTML = `<p class="dim" style="margin:2px 0 12px">${data.documents.length} documents in the knowledge base — click to view.</p>`;
  data.documents.forEach((d) => {
    const row = el("div","doc-row",`<div><div class="name">${d.doc_id}</div><div class="type">${d.doc_type}</div></div><div class="type">${d.chunks} chunk${d.chunks>1?"s":""}</div>`);
    row.onclick = () => openDoc(d.doc_id); v.appendChild(row);
  });
}

/* ================= KNOWLEDGE GRAPH ================= */
async function loadFullGraph() {
  if (!fullGraphCache) fullGraphCache = await (await fetch("/api/graph")).json();
  const s = fullGraphCache.stats;
  $("#graphStats").textContent = `${s.nodes} nodes · ${s.edges} edges · ` +
    Object.entries(s.by_type).map(([k,v])=>`${v} ${k}`).join(" · ");
  if (!loaded.graph) { fullGraph.setData(fullGraphCache, []); loaded.graph = true; }
  else { fullGraph._draw(); }
}

/* ================= MAINTENANCE / RCA ================= */
async function initRCA() {
  loaded.rca = true;
  const eq = await (await fetch("/api/equipment")).json();
  const sel = $("#rcaSelect");
  sel.innerHTML = eq.equipment.map((e)=>`<option value="${e}">${e}</option>`).join("");
  const preferred = eq.equipment.includes("PUMP-204") ? "PUMP-204" : eq.equipment[0];
  sel.value = preferred;
  await runRCA(preferred);
}

async function runRCA(id) {
  const body = $("#rcaBody");
  body.innerHTML = `<p class="dim">Running RCA for ${id}…</p>`;
  const d = await (await fetch("/api/rca/" + encodeURIComponent(id))).json();
  const hClass = d.health_label.startsWith("Healthy") ? "Healthy" : d.health_label.startsWith("Watch") ? "Watch" : "At";
  const barColor = hClass === "Healthy" ? "#3fb950" : hClass === "Watch" ? "#d29922" : "#f85149";

  let html = `<div class="cards">
    <div class="card"><div class="k">Asset health</div><div class="v small health-${hClass}">${d.health_label}</div>
      <div class="gauge"><span style="width:${d.health_score}%;background:${barColor}"></span></div></div>
    <div class="card"><div class="k">Health score</div><div class="v">${d.health_score}<span style="font-size:14px;color:var(--dim)">/100</span></div></div>
    <div class="card"><div class="k">Failure events</div><div class="v">${d.n_failure_events}</div></div>
    <div class="card"><div class="k">Peak vibration</div><div class="v small">${d.peak_vibration_mm_s ? d.peak_vibration_mm_s+" mm/s" : "—"}</div></div>
  </div>`;

  if (d.recurring_themes.length)
    html += `<div class="block"><h3>Recurring failure themes</h3>${d.recurring_themes.map(t=>`<span class="themepill">${t}</span>`).join("")}</div>`;

  html += `<div class="block"><h3>Root Cause Analysis</h3><div class="narrative">${linkifyCitations(d.narrative)}</div></div>`;

  if (d.timeline.length) {
    html += `<div class="block"><h3>Failure & inspection timeline</h3><div class="timeline">` +
      d.timeline.map(t=>`<div class="tl-item"><div class="tl-date">${t.date}</div>
        <div class="tl-doc"><span class="doclink" data-doc="${t.doc_id}">${t.doc_id}</span> · ${t.doc_type}</div>
        <div class="tl-sum">${escapeHtml(t.summary||"")}</div></div>`).join("") + `</div></div>`;
  }

  if (d.recommendations.length) {
    html += `<div class="block"><h3>Predictive maintenance recommendations</h3><ul style="margin:0;padding-left:18px;line-height:1.6">` +
      d.recommendations.map(r=>`<li>${escapeHtml(r.text)} <span class="evlink" data-doc="${r.doc_id}">[${r.doc_id}]</span></li>`).join("") + `</ul></div>`;
  }

  html += `<p class="dim">Linked documents: ${d.linked_documents.map(x=>`<span class="doclink" data-doc="${x}">${x}</span>`).join(", ") || "none"}</p>`;
  body.innerHTML = html;
  body.querySelectorAll("[data-doc]").forEach((n)=> n.onclick = () => openDoc(n.dataset.doc));
}

/* ================= COMPLIANCE ================= */
async function loadCompliance() {
  loaded.compliance = true;
  const d = await (await fetch("/api/compliance")).json();
  const s = d.summary;
  const barColor = s.coverage_pct >= 80 ? "#3fb950" : s.coverage_pct >= 50 ? "#d29922" : "#f85149";
  let html = `<div class="cards">
    <div class="card"><div class="k">Coverage</div><div class="v">${s.coverage_pct}%</div>
      <div class="gauge"><span style="width:${s.coverage_pct}%;background:${barColor}"></span></div></div>
    <div class="card"><div class="k">Requirements</div><div class="v">${s.total_requirements}</div></div>
    <div class="card"><div class="k">Covered</div><div class="v health-Healthy">${s.covered}</div></div>
    <div class="card"><div class="k">Gaps</div><div class="v health-At">${s.gaps}</div></div>
  </div>`;

  if (d.gap_list.length) {
    html += `<div class="block"><h3>Compliance gaps — act before an audit finds these</h3><ul style="margin:0;padding-left:18px;line-height:1.7">` +
      d.gap_list.map(g=>`<li><b>${g.regulation}</b> — ${escapeHtml(g.requirement)}</li>`).join("") + `</ul></div>`;
  }

  html += `<div class="block"><h3>Requirement coverage matrix</h3><table class="tbl">
    <thead><tr><th>Status</th><th>Regulation</th><th>Area</th><th>Requirement</th><th>Evidence</th></tr></thead><tbody>` +
    d.requirements.map(r=>`<tr>
      <td><span class="st ${r.status}">${r.status}</span></td>
      <td>${r.regulation}</td><td>${r.area}</td><td>${escapeHtml(r.requirement)}</td>
      <td>${r.evidence.length ? r.evidence.map(e=>`<span class="evlink" data-doc="${e}">${e}</span>`).join("<br>") : "<span class='dim'>—</span>"}</td>
    </tr>`).join("") + `</tbody></table></div>`;

  const body = $("#complianceBody");
  body.innerHTML = html;
  body.querySelectorAll("[data-doc]").forEach((n)=> n.onclick = () => openDoc(n.dataset.doc));
}

/* ================= LESSONS LEARNED ================= */
async function loadLessons() {
  loaded.lessons = true;
  const d = await (await fetch("/api/lessons")).json();
  const s = d.stats;
  let html = `<div class="cards">
    <div class="card"><div class="k">Failure docs analysed</div><div class="v">${s.failure_documents_analysed}</div></div>
    <div class="card"><div class="k">Recurring patterns</div><div class="v">${s.recurring_patterns}</div></div>
    <div class="card"><div class="k">High severity</div><div class="v health-At">${s.high_severity}</div></div>
  </div>`;

  html += `<div class="patterns">` + d.patterns.map(p=>`
    <div class="pattern ${p.severity}">
      <div class="meta"><span class="pat-sev ${p.severity}">${p.severity}</span>
        <span class="themepill">${p.occurrences}× occurrences</span></div>
      <h4>${p.pattern}</h4>
      <div class="pat-line"><b>Assets:</b> ${p.equipment.join(", ") || "—"}</div>
      <div class="pat-line"><b>Window:</b> ${p.date_range}</div>
      <div class="pat-line"><b>Evidence:</b> ${p.documents.map(x=>`<span class="doclink" data-doc="${x}">${x}</span>`).join(", ")}</div>
      <div class="pat-rec">${escapeHtml(p.recommendation)}</div>
    </div>`).join("") + `</div>`;
  if (!d.patterns.length) html += `<p class="dim">No recurring patterns detected.</p>`;

  const body = $("#lessonsBody");
  body.innerHTML = html;
  body.querySelectorAll("[data-doc]").forEach((n)=> n.onclick = () => openDoc(n.dataset.doc));
}

/* ================= OPERATIONS OVERVIEW ================= */
async function loadOverview() {
  loaded.overview = true;
  const d = await (await fetch("/api/overview")).json();
  const k = d.kpis;
  const kpi = (cls,label,val,sub) => `<div class="kpi ${cls}"><div class="k">${label}</div><div class="v">${val}${sub?` <small>${sub}</small>`:""}</div></div>`;
  let html = `<div class="kpi-grid">
    ${kpi("", "Documents", k.documents)}
    ${kpi("", "Entities linked", k.entities)}
    ${kpi("", "Graph edges", k.graph_edges)}
    ${kpi(k.assets_at_risk?"bad":"good", "Assets at risk", k.assets_at_risk, "of "+k.assets_tracked)}
    ${kpi(k.compliance_coverage>=80?"good":k.compliance_coverage>=50?"warn":"bad", "Compliance", k.compliance_coverage+"%")}
    ${kpi(k.compliance_gaps?"warn":"good", "Compliance gaps", k.compliance_gaps)}
    ${kpi("warn", "Recurring patterns", k.recurring_patterns)}
    ${kpi(k.open_alerts?"bad":"good", "Open alerts", k.open_alerts)}
  </div>`;

  html += `<div id="benchResult"></div>`;

  html += `<div class="two-col">
    <div class="block"><h3>Proactive alerts</h3><div id="alertList">` +
    d.alerts.map((a,i)=>`<div class="alert ${a.severity}" data-action="${a.action}" data-ref="${escapeAttr(a.ref)}">
      <span class="ico"></span>
      <div><div class="t">${a.type}</div><div class="txt">${escapeHtml(a.message)}</div></div></div>`).join("") +
    (d.alerts.length?"":`<p class="dim">No open alerts.</p>`) + `</div></div>
    <div><div class="block"><h3>Asset health ranking</h3>` +
    d.assets.map(a=>{ const c=a.health_score>=75?"#3fb950":a.health_score>=40?"#d29922":"#f85149";
      return `<div class="asset-row" data-asset="${a.equipment}"><span class="nm">${a.equipment}</span>
      <span style="display:flex;align-items:center;gap:8px"><span class="mini-gauge"><span style="width:${a.health_score}%;background:${c}"></span></span>
      <span style="font-size:12px;color:${c};font-weight:700">${a.health_score}</span></span></div>`; }).join("") +
    `</div></div></div>`;

  const body = $("#overviewBody");
  body.innerHTML = html;
  body.querySelectorAll(".alert").forEach(a=> a.onclick = () => {
    const act=a.dataset.action, ref=a.dataset.ref;
    if (act==="rca") { switchView("rca").then(()=>{ $("#rcaSelect").value=ref; runRCA(ref); }); }
    else switchView(act);
  });
  body.querySelectorAll(".asset-row").forEach(r=> r.onclick = () => openAsset360(r.dataset.asset));
  animateNumbers("#overviewBody .kpi .v");
}

async function runBenchmark() {
  const btn = $("#benchBtn"); btn.disabled = true; btn.textContent = "Running…";
  try {
    const d = await (await fetch("/api/benchmark")).json();
    const s = d.summary;
    $("#benchResult").innerHTML = `<div class="bench-box"><h3 style="margin:0 0 12px;font-size:14px">Evaluation benchmark — ${s.questions} domain-expert questions</h3>
      <div class="bench-grid">
        <div class="bench-stat"><div class="bv health-Healthy">${s.retrieval_hit_rate}%</div><div class="bk">Retrieval hit-rate</div></div>
        <div class="bench-stat"><div class="bv">${s.answer_coverage}%</div><div class="bk">Answer coverage</div></div>
        <div class="bench-stat"><div class="bv health-At">${s.baseline_hit_rate}%</div><div class="bk">Keyword-search baseline</div></div>
        <div class="bench-stat"><div class="bv">${s.median_time_ms}<small style="font-size:13px">ms</small></div><div class="bk">Median time-to-answer</div></div>
      </div></div>`;
    animateNumbers("#benchResult .bench-stat .bv");
    toast("Benchmark complete", `${s.retrieval_hit_rate}% hit-rate vs ${s.baseline_hit_rate}% keyword search · ${s.median_time_ms}ms median`, "ok");
  } catch (e) { toast("Benchmark failed", "", "err"); }
  finally { btn.disabled = false; btn.textContent = "Run evaluation benchmark"; }
}

/* ================= LIVE UPLOAD ================= */
async function uploadFile(file) {
  toast("Ingesting…", file.name, "");
  const fd = new FormData(); fd.append("file", file);
  try {
    const res = await fetch("/api/upload", { method: "POST", body: fd });
    const d = await res.json();
    if (!res.ok) { toast("Upload failed", d.detail || "", "err"); return; }
    toast("Document ingested ✓", `${d.doc_id}: ${d.entities_extracted} entities, linked to ${d.linked_to_documents.length} docs, +${d.graph_edges_added} graph edges`, "ok");
    // refresh graph + badges
    fullGraphCache = null; loaded.graph = false; loaded.overview = false;
    await loadHealth();
    fullGraph.resize(); await loadFullGraph();
  } catch (e) { toast("Upload failed", "Could not reach server", "err"); }
  finally { $("#fileInput").value = ""; }
}

/* ================= ASSET 360 ================= */
async function openAsset360(id) {
  const d = await (await fetch("/api/entity/" + encodeURIComponent(id))).json();
  if (d.error) { toast("Not found", d.error, "err"); return; }
  $("#a360Title").textContent = d.id;
  $("#a360Type").textContent = d.type + " · " + d.degree + " links";
  let html = "";
  if (d.health) {
    const c = d.health.score>=75?"#3fb950":d.health.score>=40?"#d29922":"#f85149";
    html += `<div class="cards"><div class="card"><div class="k">Health</div><div class="v small" style="color:${c}">${d.health.label}</div>
      <div class="gauge"><span style="width:${d.health.score}%;background:${c}"></span></div></div>
      <div class="card"><div class="k">Failure events</div><div class="v">${d.health.events}</div></div></div>`;
    if (d.health.recurring_themes.length) html += `<h4>Recurring themes</h4><div class="a360-chips">${d.health.recurring_themes.map(t=>`<span class="themepill">${escapeHtml(t)}</span>`).join("")}</div>`;
    html += `<p style="margin:12px 0"><button class="btn-ghost" onclick="window.open('/api/export/rca/${encodeURIComponent(d.id)}','_blank')">⬇ Export RCA report</button></p>`;
  }
  html += `<h4>Linked documents (${d.linked_documents.length})</h4>`;
  html += d.linked_documents.map(x=>`<div class="doc-row" data-doc="${x.doc_id}"><div><div class="name">${x.doc_id}</div><div class="type">${x.doc_type}</div></div><div class="type">${x.rel}</div></div>`).join("") || `<p class="dim">none</p>`;
  const conn = Object.entries(d.connected_entities);
  if (conn.length) {
    html += `<h4>Connected entities</h4><div class="a360-chips">`;
    conn.forEach(([type,ids])=> ids.forEach(x=> html += `<span class="ent" data-ent="${escapeAttr(x)}" style="cursor:pointer"><span class="dot" style="background:${TYPE_COLORS[type]||'#ccc'}"></span><b>${escapeHtml(x)}</b></span>`));
    html += `</div>`;
  }
  const body = $("#a360Body");
  body.innerHTML = html;
  body.querySelectorAll("[data-doc]").forEach(n=> n.onclick = () => { $("#asset360").hidden=true; openDoc(n.dataset.doc); });
  body.querySelectorAll("[data-ent]").forEach(n=> n.onclick = () => openAsset360(n.dataset.ent));
  $("#asset360").hidden = false;
}

/* ================= toasts ================= */
function toast(title, msg, kind) {
  const t = el("div", "toast " + (kind||""), `<b>${escapeHtml(title)}</b>${msg?escapeHtml(msg):""}`);
  $("#toasts").appendChild(t);
  setTimeout(()=>{ t.style.opacity="0"; t.style.transition="opacity .3s"; setTimeout(()=>t.remove(),300); }, 4200);
}

/* ================= shared ================= */
function escapeHtml(s){ return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function escapeAttr(s){ return escapeHtml(s).replace(/"/g,"&quot;"); }

async function openDoc(docId, highlights) {
  try {
    const d = await (await fetch("/api/document/" + encodeURIComponent(docId))).json();
    if (d.detail) return;
    $("#modalTitle").textContent = d.doc_id;
    $("#modalType").textContent = d.doc_type;
    const body = $("#modalBody");
    if (highlights && highlights.length) {
      let html = escapeHtml(d.text);
      let n = 0;
      highlights.forEach((h) => {
        const eh = escapeHtml(h.trim());
        if (eh && html.includes(eh)) { html = html.split(eh).join(`<mark>${eh}</mark>`); n++; }
      });
      body.innerHTML = html;
      // note banner + scroll to first mark
      if (n) {
        setTimeout(() => { const m = body.querySelector("mark"); if (m) m.scrollIntoView({block:"center"}); }, 30);
      }
    } else {
      body.textContent = d.text;
    }
    $("#modal").hidden = false;
  } catch (e) {}
}
