# Demo Script — 3 to 4 minutes (rehearse until automatic)

**Golden rule:** only ask questions you've tested 5+ times. Prepared questions only.

---

### 0. Setup (before you present)
- `python -m backend.main` running, browser at `http://127.0.0.1:8000`.
- If you have an `ANTHROPIC_API_KEY` set, the badge says "LLM: anthropic" (fluent answers).
  If not, it says "Offline mode (extractive)" — **still fully works, still cited.** Either is fine.
- Have the **Documents** tab loaded once so it's warm.

---

### 1. Open with the pain — not the tech (20 sec)
> "A large Indian plant runs 7 to 12 disconnected document systems. When a pump keeps failing,
> the answer is split across a 2019 maintenance log, a P&ID note, a near-miss report, and a
> safety procedure — and nobody ever cross-referenced them. Engineers lose 35% of their time to
> this, and it drives up to 22% of unplanned downtime."

### 2. Show the corpus briefly (20 sec)
- Click the **Documents** tab. "15 real plant document types — work orders, near-miss reports,
  inspections, P&IDs, permits, OISD and Factory Act references."
- Don't dwell. This is the least exciting part visually.

### 3. The golden-thread question — LIVE (70 sec)
- Click the sample chip / type:
  **"What do we know about PUMP-204's failure history and any related safety concerns?"**
- Point at the answer as it renders:
  - "It pulled from **multiple document types** — the 2019 seal work order, the 2024 bearing job,
    the near-miss, the inspection — and connected them into one failure story."
  - Click a **citation chip** → the source document opens **with the exact supporting sentences
    highlighted**. "Every claim is traceable to the sentence that grounds it — not just the document."
  - (Optional wow) Tap the **mic** and ask the next question by voice — "built for a technician on
    the plant floor, hands full." Or hit **Ctrl/Cmd-K** to jump anywhere instantly.
  - Click a **suggested follow-up** to keep the thread going.
  - Point at the **confidence badge** and the **entity chips** (PUMP-204, MOTOR-204A, OISD-STD-105…).
- Now the payoff — the **Answer Graph** on the right:
  - "This is what makes it more than a PDF chatbot. `PUMP-204` links across every document that
    mentions it — the graph *found* those relationships. Drag a node; hover to inspect."

### 4. Breadth question — it's not a one-trick pony (30 sec)
- **"What OISD requirement applies to hot work near Unit-3?"**
- "Different question type — regulatory compliance — same instant, cited answer. It knows the
  permit system, the confined-space procedure, and the Factory Act sections that apply here."

### 4b. Show the specialist agents — same graph, many lenses (40 sec, optional if time)
- Click **Maintenance & RCA** → asset dropdown on `PUMP-204`: "It scored this asset **At Risk**,
  built a **failure timeline** from 2019 to 2024, found the **recurring root cause** — seal/bearing
  distress driven by feedwater chemistry — and gave predictive recommendations. Switch to K-101:
  **Healthy**. It's asset-specific, not blanket alarms."
- Click **Compliance** → "OISD, Factory Act and PESO requirements checked against our records —
  **67% covered, 3 gaps** it wants us to close before an audit does."
- Click **Lessons Learned** → "Recurring failure patterns across the whole plant history — the
  systemic signals no single report shows."
- Punchline: "**One knowledge graph, five agents.** Same brain, different lenses."

### 5. Close on impact + scale (30 sec)
> "Answers in milliseconds instead of hours. Every answer cited and traceable. Five agents —
> copilot, RCA, compliance, lessons-learned — all running on one knowledge graph. And this same
> architecture works for a refinery, a data centre, or a power plant: point it at their documents
> and the graph rebuilds itself. When the engineer who knows this plant retires, the knowledge stays."

---

### Backup plan
- Record this exact run as a video **early** and keep it ready. If the live demo hiccups, play it.
- The offline extractive mode means the demo works with **no internet and no API key** — bring that
  as your safety net.
