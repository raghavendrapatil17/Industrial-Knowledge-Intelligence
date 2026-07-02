/* Generates the ET AI Hackathon deck — dark, premium, product-matched.
   node scripts/make_deck.js  ->  ET_AI_Hackathon_IKI.pptx  */
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";                 // 13.33 x 7.5
p.author = "ET AI Hackathon Team";
p.title = "Industrial Knowledge Intelligence";

const W = 13.33, H = 7.5, M = 0.7;
const C = {
  bg: "0E1218", bg2: "0B0E13", card: "18202B", cardHi: "1E2735",
  orange: "FF6B35", orange2: "FF8C5F", cyan: "4CC9F0",
  white: "FFFFFF", text: "E9EEF5", mut: "97A4B3", dim: "63707E",
  green: "46D07F", red: "FF5C57", gold: "F4C04A", line: "2A3644",
};
const F = "Calibri";
const shadow = () => ({ type: "outer", color: "000000", blur: 9, offset: 3, angle: 90, opacity: 0.35 });

function slide(dark = true) {
  const s = p.addSlide();
  s.background = { color: dark ? C.bg : C.bg };
  return s;
}
function kicker(s, txt, x = M, y = M) {
  s.addShape(p.shapes.OVAL, { x, y: y + 0.06, w: 0.14, h: 0.14, fill: { color: C.orange } });
  s.addText(txt.toUpperCase(), { x: x + 0.26, y, w: 8, h: 0.3, margin: 0, fontFace: F,
    fontSize: 12.5, bold: true, color: C.orange, charSpacing: 2.5 });
}
function title(s, txt, y = 1.12, w = 11.9, size = 33) {
  s.addText(txt, { x: M, y, w, h: 0.95, margin: 0, fontFace: F, fontSize: size, bold: true, color: C.white });
}
function card(s, x, y, w, h, fill = C.card) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.09,
    fill: { color: fill }, line: { color: C.line, width: 1 }, shadow: shadow() });
}
function pageNo(s, n) {
  s.addText(String(n).padStart(2, "0") + " / 10", { x: W - 1.7, y: H - 0.5, w: 1.2, h: 0.3,
    margin: 0, align: "right", fontFace: F, fontSize: 10, color: C.dim });
}

/* ---------- 1. TITLE ---------- */
(() => {
  const s = slide();
  // monogram mark
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.7, w: 1.15, h: 1.15, rectRadius: 0.16,
    fill: { color: C.orange }, shadow: shadow() });
  s.addText("IKI", { x: M, y: 1.7, w: 1.15, h: 1.15, margin: 0, align: "center", valign: "middle",
    fontFace: F, fontSize: 26, bold: true, color: C.white });
  s.addText("ET AI HACKATHON 2026  ·  PROBLEM STATEMENT #8", { x: M, y: 1.0, w: 11, h: 0.3, margin: 0,
    fontFace: F, fontSize: 13, bold: true, color: C.orange, charSpacing: 2 });
  s.addText("Industrial Knowledge Intelligence", { x: M, y: 3.05, w: 12, h: 1.0, margin: 0,
    fontFace: F, fontSize: 48, bold: true, color: C.white });
  s.addText("Unified Asset & Operations Brain", { x: M, y: 4.05, w: 12, h: 0.6, margin: 0,
    fontFace: F, fontSize: 25, color: C.cyan });
  s.addText([
    { text: "One knowledge graph reads every plant document — drawings, work orders, near-misses, ", options: {} },
    { text: "procedures — links it, and answers any engineer in seconds with cited, trustworthy answers.", options: {} },
  ], { x: M, y: 4.95, w: 11.4, h: 0.8, margin: 0, fontFace: F, fontSize: 15, italic: true, color: C.mut, lineSpacingMultiple: 1.15 });
  s.addText("AI for Industrial Knowledge Intelligence  ·  NLP / RAG / Knowledge Graph / LLM Agents",
    { x: M, y: H - 0.7, w: 12, h: 0.3, margin: 0, fontFace: F, fontSize: 12, color: C.dim });
  s.addNotes("Open with the pain, not the tech. A plant runs 7-12 disconnected document systems; when something fails the answer is scattered and nobody cross-references it. We built a system that reads all of it, links it, and answers any engineer in seconds — and keeps that knowledge when the senior engineer retires.");
})();

/* ---------- 2. PROBLEM ---------- */
(() => {
  const s = slide();
  kicker(s, "The Problem  ·  Business Impact");
  title(s, "Knowledge fragments faster than plants can capture it");
  const stats = [
    ["35%", "of an engineer's time is lost searching for information", "McKinsey 2024"],
    ["7–12", "disconnected document systems in the average large plant", "NASSCOM–EY"],
    ["18–22%", "of unplanned downtime traced to that fragmentation", "BIS Research"],
    ["~25%", "of experienced engineers retire within a decade", "Industry est."],
  ];
  const w = 2.86, gap = 0.19, y = 2.35, h = 3.0;
  stats.forEach((st, i) => {
    const x = M + i * (w + gap);
    card(s, x, y, w, h);
    s.addText(st[0], { x: x + 0.05, y: y + 0.35, w: w - 0.1, h: 1.1, margin: 0, align: "center",
      fontFace: F, fontSize: 44, bold: true, color: C.orange });
    s.addText(st[1], { x: x + 0.28, y: y + 1.55, w: w - 0.56, h: 1.0, margin: 0, align: "center",
      fontFace: F, fontSize: 14.5, color: C.text, lineSpacingMultiple: 1.05 });
    s.addText(st[2], { x: x + 0.15, y: y + h - 0.5, w: w - 0.3, h: 0.3, margin: 0, align: "center",
      fontFace: F, fontSize: 10.5, italic: true, color: C.dim });
  });
  s.addText("The technology exists. The intelligence layer that connects it does not — that is what we built.",
    { x: M, y: y + h + 0.35, w: 12, h: 0.4, margin: 0, fontFace: F, fontSize: 15, italic: true, color: C.cyan });
  pageNo(s, 2);
  s.addNotes("Lead with these four numbers. 35% and 25% are the money stats — time lost now, knowledge lost forever.");
})();

/* ---------- 3. WHY EXISTING TOOLS FAIL ---------- */
(() => {
  const s = slide();
  kicker(s, "Why existing tools fail");
  title(s, "Search finds documents. Engineers need answers.");
  const items = [
    ["Siloed systems", "P&IDs, work orders, procedures and inspections each live in their own system. No tool spans them."],
    ["No cross-linking", "The same pump appears in five documents that were never connected — so the full failure story is invisible."],
    ["The knowledge cliff", "What senior engineers know is undocumented. When they retire, it is gone and cannot be recovered."],
  ];
  const w = 3.86, gap = 0.26, y = 2.35, h = 2.7;
  items.forEach((it, i) => {
    const x = M + i * (w + gap);
    card(s, x, y, w, h);
    s.addShape(p.shapes.OVAL, { x: x + 0.35, y: y + 0.38, w: 0.5, h: 0.5, fill: { color: C.cardHi }, line: { color: C.orange, width: 1.5 } });
    s.addText(String(i + 1), { x: x + 0.35, y: y + 0.38, w: 0.5, h: 0.5, margin: 0, align: "center", valign: "middle", fontFace: F, fontSize: 18, bold: true, color: C.orange });
    s.addText(it[0], { x: x + 0.35, y: y + 1.02, w: w - 0.6, h: 0.5, margin: 0, fontFace: F, fontSize: 18, bold: true, color: C.white });
    s.addText(it[1], { x: x + 0.35, y: y + 1.55, w: w - 0.66, h: 1.0, margin: 0, fontFace: F, fontSize: 13.5, color: C.mut, lineSpacingMultiple: 1.1 });
  });
  s.addText([
    { text: "“Data present, but unacted upon.”", options: { bold: true, color: C.text } },
    { text: "   — the pattern behind repeated industrial incidents.", options: { color: C.mut } },
  ], { x: M, y: y + h + 0.4, w: 12, h: 0.4, margin: 0, fontFace: F, fontSize: 15, italic: true });
  pageNo(s, 3);
})();

/* ---------- 4. SOLUTION ---------- */
(() => {
  const s = slide();
  kicker(s, "Our Solution");
  title(s, "One knowledge graph. Five specialist agents.");
  const agents = [
    ["Ingestion & Knowledge Graph", "Reads any document, extracts entities, links them into a live graph"],
    ["Expert Copilot", "Plain-language Q&A with cited, confidence-scored answers in ~10 ms"],
    ["Maintenance & RCA", "Per-asset health, failure timeline, root cause & predictive actions"],
    ["Compliance Intelligence", "OISD / Factory Act / PESO coverage matrix with gap detection"],
    ["Lessons Learned", "Recurring failure patterns across the plant's whole history"],
  ];
  // central concept chip
  const cy = 2.3;
  s.addText("The same graph powers all five — one brain, many lenses.", { x: M, y: cy, w: 12, h: 0.4, margin: 0, fontFace: F, fontSize: 14.5, italic: true, color: C.cyan });
  const w = 3.87, hgap = 0.26, vgap = 0.24, y0 = 2.95, h = 1.85;
  agents.forEach((a, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * (w + hgap);
    const y = y0 + row * (h + vgap);
    card(s, x, y, w, h);
    s.addShape(p.shapes.OVAL, { x: x + 0.32, y: y + 0.32, w: 0.34, h: 0.34, fill: { color: C.orange } });
    s.addText(String(i + 1), { x: x + 0.32, y: y + 0.32, w: 0.34, h: 0.34, margin: 0, align: "center", valign: "middle", fontFace: F, fontSize: 14, bold: true, color: C.white });
    s.addText(a[0], { x: x + 0.8, y: y + 0.3, w: w - 1.0, h: 0.7, margin: 0, valign: "middle", fontFace: F, fontSize: 15.5, bold: true, color: C.white });
    s.addText(a[1], { x: x + 0.34, y: y + 1.02, w: w - 0.6, h: 0.7, margin: 0, fontFace: F, fontSize: 12.5, color: C.mut, lineSpacingMultiple: 1.05 });
  });
  // 6th cell -> "plus" capability card
  const x = M + 2 * (w + hgap), y = y0 + h + vgap;
  card(s, x, y, w, h, C.cardHi);
  s.addText("+ Platform", { x: x + 0.34, y: y + 0.3, w: w - 0.6, h: 0.4, margin: 0, fontFace: F, fontSize: 15.5, bold: true, color: C.orange });
  s.addText("Live upload · Asset 360 · audit exports · voice query · command palette",
    { x: x + 0.34, y: y + 0.85, w: w - 0.6, h: 0.9, margin: 0, fontFace: F, fontSize: 12.5, color: C.mut, lineSpacingMultiple: 1.1 });
  pageNo(s, 4);
})();

/* ---------- 5. ARCHITECTURE ---------- */
(() => {
  const s = slide();
  kicker(s, "How it works  ·  Technical Excellence");
  title(s, "Ingest, link, retrieve, cite");
  const y = 2.65, bh = 1.25, TW = 12.0, aw = 0.5, bw = (TW - 3 * aw) / 4; // even 4-stage row
  const stages = [
    ["Documents", "PDF · scans · sheets", C.card],
    ["Ingestion", "parse · chunk · NER", C.card],
    ["Knowledge Graph", "entities + relationships", C.cardHi],
    ["Hybrid Retrieval", "BM25 + graph traversal", C.card],
  ];
  stages.forEach((st, i) => {
    const x = M + i * (bw + aw);
    card(s, x, y, bw, bh, st[2]);
    s.addText(st[0], { x: x + 0.1, y: y + 0.28, w: bw - 0.2, h: 0.5, margin: 0, align: "center", fontFace: F, fontSize: 15, bold: true, color: C.white });
    s.addText(st[1], { x: x + 0.1, y: y + 0.74, w: bw - 0.2, h: 0.4, margin: 0, align: "center", fontFace: F, fontSize: 11, color: C.mut });
    if (i < 3) s.addShape(p.shapes.LINE, { x: x + bw + 0.05, y: y + bh / 2, w: aw - 0.1, h: 0, line: { color: C.orange, width: 2.5, endArrowType: "triangle" } });
  });
  // down arrow to outputs
  s.addShape(p.shapes.LINE, { x: M + TW / 2, y: y + bh + 0.03, w: 0, h: 0.42, line: { color: C.orange, width: 2.5, endArrowType: "triangle" } });
  // outputs card spanning width, 3 columns inside
  const y2 = y + bh + 0.55, oh = 1.55;
  card(s, M, y2, TW, oh, C.card);
  const outs = [
    ["Cited answer", "grounded to the source sentence, with a confidence score"],
    ["Knowledge graph view", "cross-document links, visualised and explorable"],
    ["5 agents · web + mobile", "copilot · RCA · compliance · lessons · overview"],
  ];
  const cw = TW / 3;
  outs.forEach((o, i) => {
    const x = M + i * cw;
    if (i > 0) s.addShape(p.shapes.LINE, { x, y: y2 + 0.3, w: 0, h: oh - 0.6, line: { color: C.line, width: 1 } });
    s.addText(o[0], { x: x + 0.35, y: y2 + 0.34, w: cw - 0.55, h: 0.5, margin: 0, fontFace: F, fontSize: 15, bold: true, color: C.orange });
    s.addText(o[1], { x: x + 0.35, y: y2 + 0.82, w: cw - 0.6, h: 0.6, margin: 0, fontFace: F, fontSize: 12.5, color: C.mut, lineSpacingMultiple: 1.05 });
  });
  s.addText("Python · FastAPI · rank-bm25 · networkx · offline extractive fallback + LLM circuit-breaker",
    { x: M, y: H - 0.55, w: 12, h: 0.3, margin: 0, fontFace: F, fontSize: 11.5, italic: true, color: C.dim });
  pageNo(s, 5);
})();

/* ---------- 6. DIFFERENTIATOR ---------- */
(() => {
  const s = slide();
  kicker(s, "What makes it different  ·  Innovation");
  title(s, "Not another PDF chatbot — a linked operations brain");
  // left: golden thread concept
  card(s, M, 2.3, 6.0, 4.35);
  s.addText("The golden thread", { x: M + 0.4, y: 2.55, w: 5, h: 0.4, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.orange });
  s.addText("One equipment tag — PUMP-204 — physically linked across every document type that mentions it:",
    { x: M + 0.4, y: 3.0, w: 5.2, h: 0.7, margin: 0, fontFace: F, fontSize: 13, color: C.mut, lineSpacingMultiple: 1.1 });
  // central node + satellites
  const cx = M + 3.0, cy = 5.2;
  const sat = [["P&ID", -2.1, -0.7], ["Work order '19", -2.3, 0.55], ["Near-miss", -0.1, 1.05], ["Inspection", 2.1, 0.55], ["Safety proc.", 2.25, -0.7]];
  sat.forEach(([lab, dx, dy]) => {
    // pptxgenjs requires non-negative w/h — use abs + flip for direction
    s.addShape(p.shapes.LINE, {
      x: Math.min(cx, cx + dx), y: Math.min(cy, cy + dy),
      w: Math.abs(dx) || 0.001, h: Math.abs(dy) || 0.001,
      flipH: dx < 0, flipV: dy < 0,
      line: { color: C.line, width: 1.5 },
    });
  });
  sat.forEach(([lab, dx, dy]) => {
    const ox = cx + dx - 0.55, oy = cy + dy - 0.18;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: ox, y: oy, w: 1.1, h: 0.42, rectRadius: 0.08, fill: { color: C.cardHi }, line: { color: C.line, width: 1 } });
    s.addText(lab, { x: ox, y: oy, w: 1.1, h: 0.42, margin: 0, align: "center", valign: "middle", fontFace: F, fontSize: 9.5, color: C.text });
  });
  s.addShape(p.shapes.OVAL, { x: cx - 0.55, y: cy - 0.35, w: 1.1, h: 0.7, fill: { color: C.orange }, shadow: shadow() });
  s.addText("PUMP-204", { x: cx - 0.55, y: cy - 0.35, w: 1.1, h: 0.7, margin: 0, align: "center", valign: "middle", fontFace: F, fontSize: 11, bold: true, color: C.white });
  // right: three differentiators
  const diffs = [
    ["Cross-document reasoning", "Graph traversal assembles the full story lexical search alone would miss."],
    ["Grounded to the sentence", "Every claim links to the exact supporting sentence in the source — not just the file."],
    ["Live, self-updating", "Drop in a new document and it is entity-extracted, linked, and queryable instantly."],
  ];
  const rx = M + 6.4, rw = 6.2; let ry = 2.3;
  diffs.forEach((d) => {
    card(s, rx, ry, rw, 1.3);
    s.addShape(p.shapes.OVAL, { x: rx + 0.3, y: ry + 0.45, w: 0.4, h: 0.4, fill: { color: C.orange } });
    s.addText(d[0], { x: rx + 0.9, y: ry + 0.22, w: rw - 1.1, h: 0.45, margin: 0, fontFace: F, fontSize: 15.5, bold: true, color: C.white });
    s.addText(d[1], { x: rx + 0.9, y: ry + 0.66, w: rw - 1.2, h: 0.55, margin: 0, fontFace: F, fontSize: 12.5, color: C.mut, lineSpacingMultiple: 1.05 });
    ry += 1.45;
  });
  pageNo(s, 6);
  s.addNotes("This is the slide that separates us from 'another RAG chatbot'. The golden thread proves cross-document linking is real, not hoped-for.");
})();

/* ---------- 7. RESULTS ---------- */
(() => {
  const s = slide();
  kicker(s, "Proof  ·  Technical Excellence + Business Impact");
  title(s, "Measured on a domain-expert benchmark");
  // big stat callouts
  const stats = [["100%", "retrieval hit-rate", C.orange], ["~10 ms", "median time-to-answer", C.cyan], ["92%", "answer coverage", C.green], ["5 / 5", "agents on one graph", C.gold]];
  const w = 2.86, gap = 0.19, y = 2.35, h = 1.7;
  stats.forEach((st, i) => {
    const x = M + i * (w + gap); card(s, x, y, w, h);
    s.addText(st[0], { x: x + 0.05, y: y + 0.25, w: w - 0.1, h: 0.9, margin: 0, align: "center", fontFace: F, fontSize: 40, bold: true, color: st[2] });
    s.addText(st[1], { x: x + 0.1, y: y + 1.12, w: w - 0.2, h: 0.4, margin: 0, align: "center", fontFace: F, fontSize: 13, color: C.mut });
  });
  // comparison bars: our system vs keyword search
  const by = 4.5, bx = M, bw = 7.9, tH = 0.5;
  card(s, M, 4.25, 12.0, 2.55);
  s.addText("Retrieval hit-rate vs. today's keyword search", { x: bx + 0.4, y: by, w: 8, h: 0.4, margin: 0, fontFace: F, fontSize: 15, bold: true, color: C.white });
  const bar = (yy, label, pct, col) => {
    s.addText(label, { x: bx + 0.4, y: yy - 0.02, w: 3.0, h: 0.4, margin: 0, valign: "middle", fontFace: F, fontSize: 13, color: C.text });
    const tx = bx + 3.4;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: tx, y: yy, w: bw, h: tH, rectRadius: 0.06, fill: { color: C.cardHi } });
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: tx, y: yy, w: bw * pct / 100, h: tH, rectRadius: 0.06, fill: { color: col } });
    s.addText(pct + "%", { x: tx + bw + 0.15, y: yy, w: 0.8, h: tH, margin: 0, valign: "middle", fontFace: F, fontSize: 14, bold: true, color: col });
  };
  bar(by + 0.62, "Our system", 100, C.orange);
  bar(by + 1.42, "Keyword search", 67, C.dim);
  s.addText("Same corpus, 12 expert questions. We also answer in ~10 ms vs. hours of manual search across 7–12 systems.",
    { x: M, y: H - 0.5, w: 12.4, h: 0.35, margin: 0, fontFace: F, fontSize: 11.5, italic: true, color: C.dim });
  pageNo(s, 7);
})();

/* ---------- 8. SCALE & ROADMAP ---------- */
(() => {
  const s = slide();
  kicker(s, "Scale & Roadmap  ·  Scalability");
  title(s, "One architecture, any asset-heavy sector");
  const secs = [
    ["Domain-agnostic", ["Point it at a refinery, a data centre, or a power plant", "The graph rebuilds itself from their documents", "No retraining — the pipeline is content-driven"]],
    ["Deeper on the same graph", ["Live sensor / SCADA fusion into the graph", "P&ID computer-vision digitisation", "Multi-plant, multi-language field access"]],
    ["Enterprise-ready", ["Docker deployment · REST API · Swagger docs", "12 automated tests · structured logging", "Offline fallback + LLM circuit-breaker"]],
  ];
  const w = 3.86, gap = 0.26, y = 2.35, h = 3.6;
  secs.forEach((sec, i) => {
    const x = M + i * (w + gap); card(s, x, y, w, h, i === 0 ? C.cardHi : C.card);
    s.addText(sec[0], { x: x + 0.34, y: y + 0.34, w: w - 0.6, h: 0.5, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.orange });
    s.addText(sec[1].map((t, j) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: true, paraSpaceAfter: 8, color: C.text } })),
      { x: x + 0.34, y: y + 1.0, w: w - 0.62, h: 2.4, margin: 0, fontFace: F, fontSize: 13, color: C.text });
  });
  pageNo(s, 8);
})();

/* ---------- 9. IMPACT / MAPPING ---------- */
(() => {
  const s = slide();
  kicker(s, "Why it wins");
  title(s, "Every judging criterion, covered");
  const rows = [
    ["Innovation", "Cross-document knowledge graph + graph-augmented retrieval — not plain RAG", C.orange],
    ["Business Impact", "Attacks the 35% search-time and 18–22% downtime losses; captures retiring knowledge", C.cyan],
    ["Technical Excellence", "Hybrid retrieval, grounded citations, benchmark, tests, Docker, resilience", C.green],
    ["Scalability", "Domain-agnostic pipeline — same brain for any asset-heavy sector", C.gold],
    ["User Experience", "Enterprise UI, clickable citations, voice, command palette, mobile-ready", C.orange2],
  ];
  let y = 2.35; const h = 0.82, gap = 0.12;
  rows.forEach((r) => {
    card(s, M, y, 12.0, h);
    s.addShape(p.shapes.OVAL, { x: M + 0.32, y: y + h / 2 - 0.09, w: 0.18, h: 0.18, fill: { color: r[2] } });
    s.addText(r[0], { x: M + 0.7, y, w: 3.1, h, margin: 0, valign: "middle", fontFace: F, fontSize: 15, bold: true, color: C.white });
    s.addText(r[1], { x: M + 3.9, y, w: 7.9, h, margin: 0, valign: "middle", fontFace: F, fontSize: 13, color: C.mut });
    y += h + gap;
  });
  pageNo(s, 9);
})();

/* ---------- 10. CLOSE ---------- */
(() => {
  const s = slide();
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 2.05, w: 1.05, h: 1.05, rectRadius: 0.16, fill: { color: C.orange }, shadow: shadow() });
  s.addText("IKI", { x: M, y: 2.05, w: 1.05, h: 1.05, margin: 0, align: "center", valign: "middle", fontFace: F, fontSize: 24, bold: true, color: C.white });
  s.addText("The knowledge stays — even when the engineer retires.", { x: M, y: 3.35, w: 12, h: 0.9, margin: 0, fontFace: F, fontSize: 30, bold: true, color: C.white });
  s.addText("Industrial Knowledge Intelligence  ·  Unified Asset & Operations Brain",
    { x: M, y: 4.35, w: 12, h: 0.4, margin: 0, fontFace: F, fontSize: 16, color: C.cyan });
  s.addText([
    { text: "Working prototype (public GitHub + README)  ·  live demo  ·  ", options: { color: C.mut } },
    { text: "built entirely during the hackathon", options: { color: C.orange, bold: true } },
  ], { x: M, y: 5.15, w: 12, h: 0.4, margin: 0, fontFace: F, fontSize: 13, italic: true });
  s.addText("Thank you.", { x: M, y: H - 1.0, w: 6, h: 0.5, margin: 0, fontFace: F, fontSize: 18, bold: true, color: C.white });
  s.addNotes("Close on the human line: when the senior engineer retires, the knowledge doesn't retire with them. Then invite questions.");
})();

p.writeFile({ fileName: "ET_AI_Hackathon_IKI.pptx" }).then(f => console.log("wrote", f));
