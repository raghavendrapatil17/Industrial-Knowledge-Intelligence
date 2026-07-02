# Industrial Knowledge Intelligence — Unified Asset & Operations Brain

> **ET AI Hackathon 2026 · Problem Statement #8** — *AI for Industrial Knowledge Intelligence*

An AI platform that ingests a plant's **heterogeneous documents** — P&IDs, maintenance work
orders, near-miss reports, inspection records, safety procedures, permits, regulatory
references — links them into a **knowledge graph**, and lets any engineer ask a question in
plain language and get a **cited, confidence-scored answer in milliseconds** instead of hours.

When the senior engineer who knows this plant retires, the knowledge doesn't retire with them.

---

## The problem (from the brief)

- Engineers in asset-intensive industries spend **35% of their time** searching for information (McKinsey 2024).
- The average large Indian plant runs **7–12 disconnected document systems** (NASSCOM-EY).
- Fragmentation drives **18–22% of unplanned downtime** (BIS Research).
- **~25% of experienced industrial engineers retire within a decade**, taking undocumented knowledge with them.

The technology exists. The **intelligence layer that connects it** does not. That's what this builds.

---

## What we built — all 5 sub-agents on one shared knowledge graph

| # | Agent | Status | What it does |
|---|-------|--------|--------------|
| 1 | **Universal Document Ingestion & Knowledge Graph Agent** | ✅ Built | Ingests heterogeneous formats — **PDF, text, spreadsheets (.xlsx/.csv), email (.eml), and scanned images/photos via OCR** — extracts entities, builds a linked knowledge graph across document types |
| 2 | **Expert Knowledge Copilot** | ✅ Built | RAG chat: cited, confidence-scored answers in ~10ms, mobile-ready |
| 3 | **Maintenance Intelligence & RCA Agent** | ✅ Built | Per-asset root-cause + health score + failure timeline + predictive recs |
| 4 | **Quality & Regulatory Compliance Intelligence** | ✅ Built | OISD/Factory Act/PESO requirement-coverage matrix + gap detection |
| 5 | **Lessons Learned & Failure Intelligence Engine** | ✅ Built | Recurring failure-pattern detection across incident/near-miss history |

**All five are lenses over the same knowledge graph** — the design the problem statement rewards:
one "operations brain," many views. The Copilot answers ad-hoc questions; RCA, Compliance and
Lessons are pre-computed analytic dashboards over the same linked corpus.

### Platform capabilities (beyond the 5 agents)

| Capability | What it does | Why it matters |
|---|---|---|
| **Live document upload** | Drop in a **PDF, spreadsheet, email or text file** → parsed, entity-extracted, linked into the graph, **instantly queryable** | Proves "updates automatically as new records arrive" across structured + unstructured formats |
| **Operations Overview** | Executive KPI landing: at-risk assets, compliance gaps, recurring patterns + **proactive alerts** | Plant-wide situational awareness |
| **Asset 360** | Click any entity anywhere → full profile: linked docs, connected entities, health | Cross-functional knowledge discovery |
| **Audit evidence export** | One-click downloadable **RCA report** + **compliance evidence pack** (HTML→PDF) | Straight from the brief: "evidence packages for audits" |
| **Evaluation benchmark** | 12 expert questions scored live: **100% retrieval hit-rate vs 67% keyword search, ~10ms** | Quantified, not hand-waved |
| **Grounded citation highlighting** | Click a citation → the source doc opens with the **exact supporting sentences highlighted** | Makes RAG trustworthiness undeniable |
| **Voice query (field mode)** | Speak your question via the mic button (Web Speech API) | Hits the brief's "mobile for field technicians" |
| **Smart follow-up suggestions** | Context-aware next questions after every answer | Guides discovery, smooths the demo |
| **Command palette (Ctrl/Cmd-K)** | Jump to any view, asset, or question instantly | Signals a real, polished product |
| **OCR / scanned-document intelligence** | Upload a photo or scanned form → **RapidOCR reads it**, entities extracted, linked into the graph (pure-pip, offline) | Handles real-world paper/scans, not just digital files |
| **Expert feedback loop** | 👍/👎 on any answer → logged as **captured expert validation** | Preserves retiring-workforce knowledge |
| **Grounding / trust gate** | Every answer is marked **Grounded** or flagged **⚠ Verify** with a low-evidence advisory | Trust in safety-critical use |
| **Audit trail** | Append-only provenance log of every query (time, confidence, grounding, sources) | Full auditability for regulated industries |
| **Resilience** | LLM circuit-breaker → instant graceful fallback; runs fully offline | Demo never hard-fails |

### Measured results (via `python scripts/benchmark.py`)

| Metric | This system | Keyword-search baseline |
|---|---|---|
| Retrieval hit-rate | **100%** | 67% |
| Answer coverage | **92%** | — |
| Median time-to-answer | **~10 ms** | (vs the brief's "35% of time" = hours of manual search) |

### The differentiator: cross-document intelligence, not "just another PDF chatbot"

The demo corpus contains a **golden thread** — equipment tag `PUMP-204` deliberately appears
across a P&ID note, two work orders (2019 & 2024), a near-miss report, an inspection report,
a safety procedure, a permit, an incident report, and a shift log. Ask about it and the system
**assembles the failure story across all of them** and shows the linkage in an interactive graph
— provably cross-document, not single-document retrieval.

---

## Architecture

```
 Documents (txt / PDF / scanned / spreadsheets)
        │
        ▼
 ┌─────────────────────┐     ┌──────────────────────────┐
 │  Ingestion Layer     │     │  Entity Extraction         │
 │  parse + section-    │────▶│  equipment tags, permits,  │
 │  aware chunking      │     │  regulations, personnel,   │
 └─────────┬───────────┘     │  locations, materials      │
           │                  └────────────┬─────────────┘
           ▼                               ▼
 ┌─────────────────────┐        ┌──────────────────────────┐
 │  Hybrid Index        │        │  Knowledge Graph (networkx)│
 │  BM25 (+ optional    │        │  nodes: docs + entities    │
 │  dense embeddings)   │        │  edges: MENTIONS /         │
 └─────────┬───────────┘        │  REFERENCES / CO_OCCURS    │
           │                     └────────────┬─────────────┘
           └───────────┬──────────────────────┘
                       ▼
        ┌──────────────────────────────────────┐
        │   Retrieval + Reasoning (RAG)          │
        │   vector hits + graph traversal expand │
        │   → grounded context → cited answer    │
        │   → confidence score                   │
        └──────────────────┬───────────────────┘
                           ▼
        ┌──────────────────────────────────────┐
        │   Web app (FastAPI + vanilla SPA)      │
        │   chat · clickable citations ·         │
        │   confidence · interactive graph ·     │
        │   document viewer · mobile-responsive  │
        └──────────────────────────────────────┘
```

### Why these choices
- **Hybrid retrieval (BM25 + graph traversal)** — BM25 nails tag-heavy queries (`PUMP-204`,
  `OISD-STD-105`); graph traversal pulls in connected documents lexical search alone would miss.
- **Deterministic regex entity extraction** — high precision on industrial conventions, fast,
  fully offline, demo-reproducible. LLM extraction can augment recall (optional).
- **`networkx` in-memory graph** — right-sized; no Neo4j overhead for a hackathon.
- **Graceful offline fallback** — with an LLM key it generates fluent cited answers; **without any
  key or internet it still produces grounded, cited extractive answers**, so the live demo can never hard-fail.
- **No CDN / no build step frontend** — self-contained canvas graph engine → works offline.

---

## Tech stack

| Layer | Tool |
|-------|------|
| Backend / API | Python 3.13, FastAPI, Uvicorn |
| Doc parsing | `pypdf`, section-aware chunker |
| Retrieval | `rank-bm25` (+ optional `sentence-transformers`) |
| Entity extraction | regex NER (+ optional Claude tool-use) |
| Knowledge graph | `networkx` |
| Answer generation | Anthropic Claude / OpenAI (+ offline extractive fallback) |
| Frontend | Vanilla HTML/CSS/JS, custom canvas force-directed graph |

---

## Quick start

```bash
# 1. install
pip install -r requirements.txt

# 2. generate the demo corpus (with the planted golden thread)
python scripts/generate_corpus.py

# 3. build the index + knowledge graph
python scripts/build_index.py

# 4. run
python -m backend.main
# open http://127.0.0.1:8000
```

### Optional — enable LLM-quality answers
Copy `.env.example` to `.env` and set a key:
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
No key? It runs in **offline extractive mode** — still cited, still works.

---

## API

| Endpoint | Purpose |
|----------|---------|
| `GET  /api/health` | status, LLM mode, index state |
| `POST /api/ask` | `{ "question": "..." }` → answer, citations, entities, confidence, answer-subgraph |
| `GET  /api/graph` | full knowledge graph (node-link JSON) |
| `GET  /api/documents` | corpus listing |
| `GET  /api/document/{id}` | full document text |
| `GET  /api/equipment` | equipment tags in the graph (RCA picker) |
| `GET  /api/rca/{equipment_id}` | RCA: health score, timeline, root causes, predictive recs |
| `GET  /api/compliance` | requirement-coverage matrix + gap list |
| `GET  /api/lessons` | recurring failure patterns |
| `POST /api/upload` | live-ingest a new document (multipart) → entities + graph links |
| `GET  /api/overview` | plant-wide KPIs + proactive alerts |
| `GET  /api/entity/{id}` | Asset 360 profile (linked docs, connections, health) |
| `GET  /api/benchmark` | evaluation metrics vs keyword baseline |
| `GET  /api/export/rca/{id}` | downloadable RCA report (HTML) |
| `GET  /api/export/compliance` | downloadable compliance evidence pack (HTML) |
| `GET  /api/audit` | provenance log of recent queries + stats |
| `POST /api/feedback` | log 👍/👎 expert validation on an answer |

Interactive API docs auto-generated at **`/docs`** (Swagger UI).

### Run with Docker
```bash
docker build -t iki .
docker run -p 8000:8000 iki      # builds corpus + index at image-build time
```

### Tests
```bash
pip install pytest
pytest -q                        # 12 tests: entities, graph, RCA, compliance, upload, benchmark
```

---

## Demo questions (rehearsed — see `docs/DEMO_SCRIPT.md`)

1. *“What do we know about PUMP-204's failure history and any related safety concerns?”* — the golden thread.
2. *“What OISD requirement applies to hot work near Unit-3?”* — compliance breadth.
3. *“Why does PUMP-204's mechanical seal keep failing?”* — root-cause reasoning across documents.

---

## Evaluation-criteria mapping

| Criterion (weight) | How this addresses it |
|---|---|
| Innovation (25%) | Cross-document knowledge graph + hybrid graph-augmented retrieval, not plain RAG |
| Business Impact (25%) | Directly attacks the 35% search-time and 18–22% downtime stats; retiring-workforce knowledge capture |
| Technical Excellence (20%) | Hybrid retrieval, graph traversal expansion, confidence scoring, graceful degradation |
| Scalability (15%) | Domain-agnostic pipeline — same architecture works for a refinery, data centre, or power plant |
| User Experience (15%) | Clean web UI, clickable citations, confidence badges, live graph, mobile-responsive for field techs |

---

## Repository layout

```
backend/        FastAPI app
  ingestion.py    parse + section-aware chunking
  entities.py     regex entity extraction (equipment/permits/regs/personnel/…)
  vectorstore.py  BM25 (+ optional dense) hybrid index
  graph.py        knowledge-graph build/query (networkx)
  rag.py          retrieval + reasoning orchestrator (KnowledgeEngine)
  agents.py       agents 3–5: maintenance/RCA, compliance, lessons-learned
  llm.py          Anthropic/OpenAI + offline extractive fallback
  main.py         API routes + serves the SPA
frontend/       self-contained SPA (index.html, style.css, app.js, graph.js)
scripts/        generate_corpus.py, build_index.py
data/documents/ the demo corpus (with golden thread)
docs/           demo script, architecture notes
```

All code is original and created during the hackathon. Public-style regulatory/manual content
is paraphrased (nothing copied verbatim); plant records are synthetic.
