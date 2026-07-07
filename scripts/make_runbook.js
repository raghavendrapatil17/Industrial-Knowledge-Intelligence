/* Click-by-click demo runbook -> Desktop (.docx). */
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, BorderStyle } = require("docx");

const ORANGE = "C0451B", DARK = "1A1F26", CYAN = "0E6E8C", GREY = "555555";

const items = [];
const H = (t) => items.push({ h: t });
const SUB = (t) => items.push({ sub: t });
const S = (n, t) => items.push({ n, t });
const SAY = (t) => items.push({ say: t });
const NOTE = (t) => items.push({ note: t });

H("PART 1 — Start the app (before recording)");
S(1, "Open a terminal: press the Windows key, type  cmd , press Enter.");
S(2, "Type:  cd \"D:/Ai Project\"   then press Enter.");
S(3, "Type:  python scripts/build_index.py   then Enter. Wait until it finishes (~10 sec).");
S(4, "Type:  python -m backend.main   then Enter. The server starts.");
S(5, "Leave this terminal window OPEN — the app runs inside it. Do not close it during the demo.");

H("PART 2 — Open the app in the browser");
S(6, "Open Chrome.");
S(7, "Click the address bar, type  127.0.0.1:8000 , press Enter. The Operations Overview page loads.");
S(8, "Press F11 → full screen (clean look).");
S(9, "Press Ctrl and 0 together → sets zoom to 100%.");

H("PART 3 — Start recording");
S(10, "Press Windows key + G → the Xbox Game Bar appears.");
S(11, "In the small Capture box, click the microphone icon so it is ON (not crossed out).");
S(12, "Click the round ● record button (or press Windows + Alt + R). Recording has started.");
S(13, "Take a breath. Speak slowly.");

H("PART 4 — The demo (click-by-click)");
SUB("Screen 1 — Operations Overview (~20 sec)");
S(14, "Slowly move the mouse across the number cards at the top, then to the red PUMP-204 alert.");
SAY("Engineers lose a third of their time searching across a dozen disconnected systems, and retiring experts take decades of knowledge with them. This is the whole plant's health in one view.");

SUB("Screen 2 — Expert Copilot (~60 sec)");
S(16, "In the LEFT SIDEBAR, click  Expert Copilot .");
S(17, "At the top, click the FIRST grey suggested-question chip (\"What do we know about PUMP-204's failure history...\"). Wait ~1 sec for the answer.");
SAY("In milliseconds — a cited answer, a confidence score, and a green 'Grounded' badge, pulled across a work order, near-miss and inspection.");
S(20, "Click one ORANGE citation chip (e.g. [WO-2024-1187.txt]). A document pops up with a highlighted sentence.");
SAY("Every claim is traceable to the exact source sentence.");
S(21, "Click the ✕ at the top-right of the popup to close it.");
S(22, "On the RIGHT side (the graph), hover the mouse over the orange 'PUMP-204' dot — connected items light up.");
SAY("The knowledge graph found these links across documents automatically — this is more than a chatbot.");

SUB("Screen 3 — A second question (~20 sec)");
S(24, "Click the question box at the bottom, type:  What OISD requirement applies to hot work near Unit-3?  then press Ask (or Enter).");
SAY("A different type of question — compliance — same instant, cited answer.");

SUB("Screen 4 — Maintenance & RCA, the live feed (~45 sec)");
S(26, "In the LEFT SIDEBAR, click  Maintenance & RCA . It loads PUMP-204 automatically.");
SAY("It scored PUMP-204 'At Risk', built a failure timeline, and found the recurring root cause.");
S(28, "Point at the 'Live operating conditions' card — the numbers change every few seconds.");
SAY("And it fuses that history with a live sensor feed — watch the vibration update, and it flags an alarm the moment a reading crosses its limit.");
S(30, "Near the top, click the Equipment dropdown (says PUMP-204) → choose K-101.");
SAY("Pick a healthy asset and it says so — it's asset-specific, not blanket alarms.");

SUB("Screen 5 — Compliance + Lessons (~25 sec)");
S(32, "In the LEFT SIDEBAR, click  Compliance .");
SAY("OISD, Factory Act and PESO checked against our records — 67% covered, three gaps, with a one-click evidence pack.");
S(34, "In the LEFT SIDEBAR, click  Lessons Learned . Point at a card line: 'Matches known industry failure mode.'");
SAY("And it benchmarks our recurring patterns against known industry failure modes — ISO and API standards.");

SUB("Screen 6 — The wow: live P&ID ingestion (~40 sec)");
S(37, "In the LEFT SIDEBAR, click  Ingestion & Graph .");
S(38, "Top-right: click the orange  Upload document  button.");
S(39, "In the file window: go to Desktop → double-click  DEMO-P&ID-drawing.png .");
S(40, "Wait ~3-5 sec → a green message (toast) appears bottom-right confirming it was ingested.");
SAY("This is a P&ID drawing — it reads the equipment tags AND works out how they connect from the layout, and links it into the graph in seconds. PDFs, spreadsheets, email, even engineering drawings — one brain.");

SUB("Screen 7 — Close (~20 sec)");
S(42, "Let the big graph sit on screen for a moment.");
SAY("One knowledge graph, five agents. A hundred percent retrieval accuracy versus sixty-seven for keyword search, in milliseconds instead of hours. And when the engineer who knows this plant retires — the knowledge stays.");

H("PART 5 — Stop & save");
S(44, "Press Windows + Alt + R to STOP recording.");
S(45, "The video is saved in  This PC → Videos → Captures .");
S(46, "Open it, watch once — check your voice is clear. If good, keep it; if not, re-record from Part 3.");
S(47, "After you're done: click the terminal, press Ctrl + C to stop the server. Run  python scripts/build_index.py  again to reset the data.");

NOTE("Tips: speak slowly, pause between screens, don't rush clicks. If you fumble a line, pause and repeat it (trim later). Record a second backup take right after a good one. Offline mode means nothing can fail live.");

// ---- render ----
const children = [];
children.push(new Paragraph({ spacing: { after: 60 }, children: [
  new TextRun({ text: "DEMO RUNBOOK — click by click", bold: true, color: ORANGE, size: 30 }),
]}));
children.push(new Paragraph({ spacing: { after: 160 }, children: [
  new TextRun({ text: "Industrial Knowledge Intelligence  ·  aim ~3.5 minutes  ·  keep this open on your phone while recording", color: GREY, size: 17, italics: true }),
]}));

for (const it of items) {
  if (it.h) {
    children.push(new Paragraph({ spacing: { before: 180, after: 80 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ORANGE, space: 3 } },
      children: [new TextRun({ text: it.h, bold: true, color: ORANGE, size: 22 })] }));
  } else if (it.sub) {
    children.push(new Paragraph({ spacing: { before: 120, after: 50 },
      children: [new TextRun({ text: it.sub, bold: true, color: DARK, size: 19 })] }));
  } else if (it.say) {
    children.push(new Paragraph({ spacing: { after: 70 }, indent: { left: 360 }, children: [
      new TextRun({ text: "SAY:  ", bold: true, color: CYAN, size: 17 }),
      new TextRun({ text: "“" + it.say + "”", italics: true, color: CYAN, size: 18 }),
    ]}));
  } else if (it.note) {
    children.push(new Paragraph({ spacing: { before: 120 }, children: [
      new TextRun({ text: it.note, italics: true, color: GREY, size: 16 }) ]}));
  } else {
    children.push(new Paragraph({ spacing: { after: 40 }, children: [
      new TextRun({ text: it.n + ".  ", bold: true, color: ORANGE, size: 18 }),
      new TextRun({ text: it.t, color: DARK, size: 18 }),
    ]}));
  }
}

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 18, color: DARK } } } },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1008, right: 1008, bottom: 1008, left: 1008 } } }, children }],
});
Packer.toBuffer(doc).then((buf) => {
  const out = "C:\\Users\\patil\\Desktop\\DEMO-Runbook-click-by-click.docx";
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
