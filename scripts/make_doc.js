/* Generates a simple-English project overview .docx on the Desktop. */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, LevelFormat,
} = require("docx");

const ORANGE = "C0451B", DARK = "1A1F26", GREY = "555555";
const CW = 9360; // content width (US Letter, 1" margins)

const P = (text, opts = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, children: [new TextRun({ text, color: DARK, ...opts })] });
const lead = (t) => new Paragraph({ spacing: { after: 160, line: 288 }, children: [new TextRun({ text: t, color: DARK, size: 22 })] });
const bullet = (t, bold) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 80 },
  children: bold ? [new TextRun({ text: bold + ": ", bold: true, color: DARK }), new TextRun({ text: t, color: DARK })] : [new TextRun({ text: t, color: DARK })] });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 140 },
  children: [new TextRun({ text: t, bold: true, color: ORANGE, size: 30 })],
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ORANGE, space: 4 } } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 180, after: 90 },
  children: [new TextRun({ text: t, bold: true, color: DARK, size: 24 })] });

function table(headers, rows, widths) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (text, w, opts = {}) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    shading: opts.head ? { fill: "F3ECE7", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ children: [new TextRun({ text, bold: !!opts.head, color: opts.head ? ORANGE : DARK, size: 20 })] })],
  });
  return new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { head: true })) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, widths[i])) })),
    ],
  });
}

const children = [];

// ---- Title ----
children.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Industrial Knowledge Intelligence", bold: true, color: DARK, size: 48 })] }));
children.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Unified Asset & Operations Brain", color: ORANGE, size: 30 })] }));
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "ET AI Hackathon 2026  ·  Problem Statement #8", color: GREY, size: 22, bold: true })] }));
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Team raghupatil9036  —  Raghavendra S Patil, Pallavi C", color: GREY, size: 22 })] }));
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "GitHub: github.com/raghavendrapatil17/Industrial-Knowledge-Intelligence", color: GREY, size: 20, italics: true })] }));
children.push(new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "Live demo: industrial-knowledge-intelligence-sz8a.onrender.com", color: ORANGE, size: 20, italics: true, bold: true })] }));

// ---- 1. The Problem ----
children.push(H1("1. The Problem (in plain English)"));
children.push(lead("Big industrial plants — refineries, steel plants, power plants — run on paperwork. Every pump, valve and boiler has a history spread across many different systems: engineering drawings in one place, maintenance work orders in another, safety procedures in a third, inspection records in a fourth, and important emails buried in inboxes."));
children.push(P("Because nothing is connected, people waste enormous time and make risky decisions:", { bold: true }));
children.push(bullet("Engineers spend about 35% of their working hours just searching for information.", "Time lost"));
children.push(bullet("A typical large plant juggles 7 to 12 disconnected document systems.", "Fragmentation"));
children.push(bullet("This fragmentation causes 18–22% of unplanned downtime, because maintenance teams act without the full history.", "Downtime"));
children.push(bullet("About 25% of experienced engineers will retire within ten years, taking decades of undocumented knowledge with them.", "Knowledge cliff"));
children.push(lead("In short: the information exists, but there is no intelligent layer that connects it and gives a clear, trustworthy answer at the moment someone needs it. That missing layer is exactly what we built."));

// ---- 2. What We Built ----
children.push(H1("2. What We Built"));
children.push(lead("We built an AI platform that reads every kind of plant document, links everything together into one connected “knowledge graph,” and lets any engineer ask a question in plain language and get a cited, trustworthy answer in a fraction of a second instead of hours."));
children.push(P("It is one shared brain with five specialist agents working on top of it:"));
children.push(table(
  ["Agent", "What it does (simple English)"],
  [
    ["1. Ingestion & Knowledge Graph", "Reads PDFs, spreadsheets, emails, scanned photos, and even P&ID drawings (extracting tags and their connections). Pulls out equipment, people, dates and regulations and links them together."],
    ["2. Expert Copilot", "A chat assistant. Ask a question, get an answer with clickable sources, a confidence score, and a “grounded” or “verify” trust badge."],
    ["3. Maintenance & RCA", "Looks at an asset’s full history AND a live sensor feed together, explains the real root cause of failures, and says what to do next to prevent them."],
    ["4. Compliance Intelligence", "Checks the plant’s records against safety rules (OISD, Factory Act, PESO) and flags gaps before an audit does."],
    ["5. Lessons Learned", "Finds repeating failure patterns no single person would notice, and matches them to known industry failure modes (ISO / API / OISD)."],
  ],
  [3000, 6360]));

// ---- 3. Key Features ----
children.push(H1("3. Key Features"));
children.push(bullet("Ask a question in normal English and get an answer in about 10 milliseconds, with clickable links to the exact source document.", "Instant cited answers"));
children.push(bullet("Every claim links to the exact sentence in the source that supports it — you can see the proof, not just trust it.", "Grounded to the sentence"));
children.push(bullet("The same pump appears in five documents, and the graph automatically connects them, so you see the whole story across documents.", "Cross-document linking"));
children.push(bullet("Drop in a PDF, spreadsheet, email, or a photo of a paper form — it is read (with OCR for images), understood, and added to the graph in seconds.", "Reads any format"));
children.push(bullet("Upload a P&ID engineering drawing and the system reads the equipment tags and works out how they connect from their positions on the drawing — turning a picture into structured, linked data.", "P&ID digitisation"));
children.push(bullet("The maintenance agent combines the document history with a live sensor feed (vibration, temperature, pressure) that updates on screen, and raises an alert when a reading crosses its limit.", "Live operating conditions"));
children.push(bullet("Repeating problems are matched to known industry failure modes with standard references (ISO 20816, API 682, OISD), so the plant learns from the wider industry, not just itself.", "Industry benchmarking"));
children.push(bullet("Every answer is marked “Grounded” or flagged “Verify,” so people know when to double-check before acting on something safety-critical.", "Trust gate"));
children.push(bullet("Every question and answer is logged with time, confidence and sources — full traceability for regulated industries. Exportable as CSV.", "Audit trail"));
children.push(bullet("Engineers can thumbs-up a good answer to capture their expert validation — preserving knowledge before they retire.", "Expert feedback"));
children.push(bullet("One-click, print-ready Root Cause and Compliance reports for audits.", "Report exports"));
children.push(bullet("A clean web dashboard that also works on mobile for field technicians, with voice input and a command palette.", "Modern experience"));

// ---- 4. How It Works ----
children.push(H1("4. How It Works (the simple picture)"));
children.push(P("Documents  →  Read & understand  →  Link into a knowledge graph  →  Search + reason  →  Cited answer", { bold: true, color: ORANGE }));
children.push(lead("When a document arrives, the system extracts the important entities (equipment, people, dates, regulations) and connects them in a graph. When someone asks a question, it finds the most relevant pieces using two methods together — keyword search and following links in the graph — then writes a clear answer with the sources attached. It runs fully offline if needed, so a live demo can never fail."));

// ---- 5. Challenges & How We Overcame Them ----
children.push(H1("5. Challenges & How We Overcame Them"));
children.push(table(
  ["Challenge", "How we solved it"],
  [
    ["We could not get real, private plant documents.", "We built a realistic sample set and planted a “golden thread” — one pump (PUMP-204) that appears across many document types — to prove the cross-document linking really works."],
    ["Answers from AI can sound convincing but be wrong.", "We added a grounding/trust gate: an answer is only marked “Grounded” if real supporting sentences are found; otherwise it says “verify.”"],
    ["No paid AI key / no internet during a demo.", "The whole system works offline with a graceful fallback, plus a “circuit breaker” so a dead key never slows it down."],
    ["Real plants use many file types, not just PDFs.", "We added parsers for spreadsheets and email, and OCR so it can even read scanned forms and photos of paper notes."],
    ["A judge might upload a strange or broken file.", "Three rounds of security review hardened the app against bad uploads, injection attacks, and crashes."],
    ["Reports were unreadable in dark-mode browsers.", "We forced a clean white background on all exported reports."],
  ],
  [3400, 5960]));

// ---- 6. Results ----
children.push(H1("6. Results (proof it works)"));
children.push(table(
  ["Measure", "This system", "Old way (keyword search)"],
  [
    ["Correct document found", "100%", "67%"],
    ["Answer covers the key fact", "92%", "—"],
    ["Time to answer", "~10 milliseconds", "Minutes to hours (manual)"],
    ["Automated tests passing", "22 / 22", "—"],
    ["Security review rounds", "3 (all issues fixed)", "—"],
  ],
  [3400, 3000, 2960]));

// ---- 7. Technology ----
children.push(H1("7. Technology Used"));
children.push(bullet("Python, FastAPI (backend), a lightweight vanilla-JavaScript web app (frontend)."));
children.push(bullet("Hybrid search: BM25 keyword search + a networkx knowledge graph."));
children.push(bullet("RapidOCR for reading scanned images and P&IDs (with layout analysis for connections); openpyxl for spreadsheets."));
children.push(bullet("Works with Anthropic Claude or OpenAI when a key is present, with a full offline fallback."));
children.push(bullet("Docker-ready, hosted live on Render, with an automated test suite (22 tests) and API documentation."));

// ---- 8. What's Next ----
children.push(H1("8. What’s Next (roadmap)"));
children.push(bullet("Deeper P&ID understanding — full symbol recognition, on top of the tag-and-connection extraction we already do."));
children.push(bullet("Connect the live sensor feed to a real plant historian / SCADA source (today it uses a realistic simulated feed)."));
children.push(bullet("Link the industry failure-mode library to live external incident databases."));
children.push(bullet("Multi-language support for field technicians across regions."));
children.push(lead("The foundation — one connected knowledge graph with specialist agents — is built to scale to any asset-heavy industry: a refinery, a data centre, or a power plant. When the engineer who knows the plant retires, the knowledge stays."));

const doc = new Document({
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 260 } } } }] }] },
  styles: { default: { document: { run: { font: "Arial", size: 22, color: DARK } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = "C:\\Users\\patil\\Desktop\\Industrial-Knowledge-Intelligence-Overview.docx";
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
