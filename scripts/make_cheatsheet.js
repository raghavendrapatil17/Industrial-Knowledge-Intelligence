/* One-page printable demo cheat-sheet -> Desktop. */
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, AlignmentType, Table, TableRow, TableCell,
        WidthType, BorderStyle, ShadingType } = require("docx");

const ORANGE = "C0451B", DARK = "1A1F26", GREY = "555555", CYAN = "0E6E8C";
const CW = 10080; // content width, US Letter with 0.6" margins

const run = (t, o = {}) => new TextRun({ text: t, color: DARK, size: 17, ...o });
const line = (children, opts = {}) => new Paragraph({ spacing: { after: 40 }, children, ...opts });

function shotTable() {
  const b = { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" };
  const borders = { top: b, bottom: b, left: b, right: b };
  const widths = [900, 3200, 5980];
  const cell = (runs, w, opts = {}) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    shading: opts.head ? { fill: "F3ECE7", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ spacing: { after: 0 }, children: runs })],
  });
  const head = (t) => cell([new TextRun({ text: t, bold: true, color: ORANGE, size: 16 })], widths[["Time","Do (click / action)","Say — key line"].indexOf(t)], { head: true });
  const rows = [
    ["0:00", "Operations Overview — sweep KPIs + red PUMP-204 alert",
     "35% of time lost searching; retiring experts — answers scattered across a dozen systems."],
    ["0:20", "Expert Copilot — ask Q1; click a citation; hover PUMP-204 node",
     "Cited, Grounded, ~10 ms. The graph links across documents — this is more than a chatbot."],
    ["1:20", "Copilot — ask Q2",
     "Different question — compliance — same instant, cited answer."],
    ["1:40", "Maintenance & RCA — point at the LIVE sensor card ticking; switch to K-101",
     "At Risk + root cause, fused with a live sensor feed — vibration updates, alarms in real time. K-101 = Healthy: asset-specific."],
    ["2:25", "Compliance (67%, 3 gaps) → Lessons (point 'Matches industry failure mode')",
     "Gaps flagged with an evidence pack; patterns benchmarked to ISO / API / OISD failure modes."],
    ["2:50", "Ingestion & Graph — Upload → DEMO-P&ID-drawing.png → wait for green toast",
     "Reads a P&ID: tags AND connections, linked in seconds. PDFs, spreadsheets, email, drawings — one brain."],
    ["3:30", "Hold on the graph, then stop recording",
     "One graph, five agents. 100% vs 67% keyword search, milliseconds not hours. When the engineer retires — the knowledge stays."],
  ];
  return new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: ["Time","Do (click / action)","Say — key line"].map(head) }),
      ...rows.map((r) => new TableRow({ children: [
        cell([new TextRun({ text: r[0], bold: true, color: CYAN, size: 16 })], widths[0]),
        cell([new TextRun({ text: r[1], color: DARK, size: 16 })], widths[1]),
        cell([new TextRun({ text: r[2], italics: true, color: DARK, size: 16 })], widths[2]),
      ] })),
    ],
  });
}

const children = [
  new Paragraph({ spacing: { after: 20 }, children: [
    new TextRun({ text: "DEMO CHEAT-SHEET", bold: true, color: ORANGE, size: 30 }),
    new TextRun({ text: "   Industrial Knowledge Intelligence   ·   aim ~3.5 min", color: GREY, size: 18 }),
  ]}),
  line([new TextRun({ text: "SETUP: ", bold: true, color: ORANGE, size: 16 }),
        run("app at localhost:8000 · F11 fullscreen · Win+G to record (MIC ON) · rehearse the 3 Qs 5× · record a backup take · offline mode = nothing fails live.", { size: 16 })]),
  line([new TextRun({ text: "Q1: ", bold: true, color: CYAN, size: 16 }),
        run("What do we know about PUMP-204's failure history and any related safety concerns?", { size: 16 })]),
  line([new TextRun({ text: "Q2: ", bold: true, color: CYAN, size: 16 }),
        run("What OISD requirement applies to hot work near Unit-3?", { size: 16 }),
        new TextRun({ text: "     (Q3 = just click the RCA tab, no typing)", color: GREY, size: 15, italics: true })]),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun("")] }),
  shotTable(),
  new Paragraph({ spacing: { before: 120, after: 20 }, children: [
    new TextRun({ text: "AFTER: ", bold: true, color: ORANGE, size: 16 }),
    run("watch it once (audio clear?) · trim in Clipchamp · export 1080p, under 4 min · upload YouTube (Unlisted) or keep <20 MB · test link in incognito · then run  python scripts/build_index.py  to reset the corpus.", { size: 16 }),
  ]}),
];

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 17, color: DARK } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 864, right: 864, bottom: 864, left: 864 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = "C:\\Users\\patil\\Desktop\\DEMO-Cheat-Sheet.docx";
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
