# Demo Video — Camera-Ready Recording Script (target 3:30)

A word-for-word, shot-by-shot script you can record in one take. Everything below is
tested against the live app. Read the narration in **bold** aloud; do the *(actions in italics)*.

---

## A. Before you hit record (5-minute setup)

1. **Reset the demo data** so the graph is the clean, curated 15 docs:
   ```bash
   cd "D:/Ai Project"
   python scripts/build_index.py
   python -m backend.main
   ```
2. Open **Chrome** at **http://127.0.0.1:8000**. Press **F11** for full-screen (hides tabs/bookmarks).
3. Set browser zoom to **100%** (Ctrl+0). Use a **1920×1080** display if possible.
4. Close chat/notification apps. Put your phone on silent.
5. **Rehearse the 3 questions below at least 5 times.** Never ask an untested question on camera.
6. Have this script on a second screen or phone.

**Recording tool (Windows, no install):** press **Win + G** (Xbox Game Bar) → Capture widget →
record the screen. Or use **OBS Studio** for higher quality. Record at 1080p, 30fps.
Do a 10-second test clip first and check the audio.

**Mode note:** the top-left badge shows the engine. Offline mode is 100% fine to demo — it's
cited and instant. If you added OpenAI billing, it'll say "LLM: openai" and answers are more fluent.

---

## B. The three tested questions (copy-paste ready)

1. `What do we know about PUMP-204's failure history and any related safety concerns?`
2. `What OISD requirement applies to hot work near Unit-3?`
3. *(no typing — click the "Maintenance & RCA" tab and the PUMP-204 asset)*

---

## C. Shot-by-shot script

### SHOT 1 — The hook (0:00–0:25)  ·  *Start on the Operations Overview*
> **"In a large industrial plant, the answer to 'why did this fail' is scattered across a
> dozen disconnected systems. Engineers lose a third of their time just searching — and when a
> senior engineer retires, decades of knowledge walk out the door with them."**

*(Slowly move the cursor across the KPI cards and the red PUMP-204 alert.)*

> **"This is our Operations Overview — plant-wide asset health, compliance, and recurring risks
> in one glance. One knowledge graph, five agents. Let me show you."**

### SHOT 2 — The golden thread, live (0:25–1:35)  ·  *Click "Expert Copilot"*
*(Click the first sample chip OR paste question 1, press Ask.)*

> **"I'll ask in plain English: what do we know about pump 204's failure history and safety concerns?"**

*(Answer appears near-instantly. Point at the confidence badge and timing pill.)*

> **"In about ten milliseconds it answers — with a confidence score, and it's pulled from
> multiple document types: a 2019 work order, the 2024 bearing job, a near-miss, an inspection."**

*(Click one citation chip — the source document opens with sentences highlighted.)*

> **"Every claim is traceable. Click a citation and it opens the exact source, with the supporting
> sentence highlighted. This isn't a guess — it's grounded."**

*(Close the document. Point to the graph on the right.)*

> **"And this is what makes it more than a chatbot. The knowledge graph found these links across
> documents — the pump, its motor, the valve, the regulations, the people."**

*(Hover the PUMP-204 node so its neighborhood lights up. Optionally drag a node.)*

> **"Hover any asset and you see everything connected to it. That's cross-document intelligence."**

### SHOT 3 — Breadth: compliance question (1:35–2:05)  ·  *Still in Copilot*
*(Paste question 2, press Ask.)*

> **"It's not a one-trick pony. Ask a compliance question — what OISD requirement applies to hot
> work near Unit-3 — and it knows the permit system, the confined-space procedure, and the
> Factory Act sections that apply. Same instant, cited answer."**

### SHOT 4 — The specialist agents (2:05–2:55)  ·  *Click "Maintenance & RCA"*
*(The RCA dashboard loads on PUMP-204.)*

> **"The same graph powers four more agents. Maintenance and RCA scored pump 204 'At Risk',
> built a failure timeline from 2019 to 2024, and found the recurring root cause — seal and
> bearing distress driven by feedwater chemistry. Not four separate incidents — one systemic problem."**

*(Switch the dropdown to K-101.)*

> **"Pick a healthy asset and it says so. It's asset-specific, not blanket alarms."**

*(Click "Compliance" tab.)*

> **"Compliance maps OISD, Factory Act and PESO against our records — sixty-seven percent covered,
> three gaps to close before an audit finds them — with a one-click evidence pack."**

*(Click "Lessons Learned" tab, gesture at the pattern cards.)*

> **"And Lessons Learned surfaces recurring failure patterns across the whole plant history."**

### SHOT 5 — Live OCR / multi-format ingestion + close (2:55–3:40)  ·  *Click "Ingestion & Graph"*
*(THE BONUS WOW — rehearse this. Use `DEMO-scanned-maintenance-note.png` on your Desktop —
a **photo/scan of a paper note**. This shows Computer-Vision/OCR, the strongest on-brief moment.)*
*(Click **Upload document**, pick the image, wait a few seconds for the green toast.)*

> **"And it's not just digital files. This is a photo of a paper maintenance note. Watch — it runs
> OCR, reads the text, pulls out the equipment tags — PUMP-204, the OISD standard, the work order —
> and links them into the graph in seconds. PDFs, spreadsheets, email, even scanned paper — one brain."**

*(Point at the toast: entities extracted + documents linked. Optionally give the answer a 👍 to
show the expert-feedback capture. Let the graph settle.)*

> **"One knowledge graph. Five agents. A hundred-percent retrieval accuracy versus sixty-seven for
> keyword search, in milliseconds instead of hours. This same architecture works for a refinery,
> a data centre, or a power plant. And when the engineer who knows this plant retires — the
> knowledge stays."**

*(Hold on the graph for 2 seconds, then stop recording.)*

---

## D. After recording

- Watch it once at full volume. Re-record if audio is muffled or a question misfired.
- Trim dead air at the start/end (Game Bar clips save to `Videos/Captures`; Clipchamp — preinstalled — can trim).
- Keep it **under 4 minutes**. Export **1080p MP4**.
- **Upload as Unlisted on YouTube** (or public), OR keep the file **under 20 MB** if uploading to Unstop directly. Verify the link is publicly viewable in an incognito window.
- After any live-upload demo, run `python scripts/build_index.py` again to reset the corpus.

## E. Safety net
- Record a clean backup take immediately after your good one.
- Offline mode means the demo works with **no internet and no API key** — nothing to fail live.
- Only ask the three rehearsed questions. If a judge asks for a live one later, that's a bonus, not the demo.
