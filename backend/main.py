"""
FastAPI application — serves the API and the frontend SPA.

Run:  python -m backend.main      (or: uvicorn backend.main:app --reload)
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .schemas import AskRequest
from .graph import full_graph_json

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("iki.api")

app = FastAPI(title="Industrial Knowledge Intelligence",
              description="Unified Asset & Operations Brain — one knowledge graph, five agents.",
              version="2.0")

_engine = None  # lazy-loaded KnowledgeEngine


def get_engine():
    global _engine
    if _engine is None:
        from .rag import KnowledgeEngine
        if not config.INDEX_PATH.exists() or not config.GRAPH_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Index not built. Run: python scripts/build_index.py",
            )
        _engine = KnowledgeEngine()
    return _engine


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_provider": config.LLM_PROVIDER,
        "llm_available": config.llm_available(),
        "index_built": config.INDEX_PATH.exists() and config.GRAPH_PATH.exists(),
    }


@app.post("/api/ask")
def ask(req: AskRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Empty question")
    from . import audit
    engine = get_engine()
    q = req.question.strip()
    resp = engine.ask(q, top_k=req.top_k)
    audit.log_query(q, resp)     # provenance / auditability
    return resp


@app.get("/api/audit")
def audit_trail():
    from . import audit
    return audit.recent(25)


@app.get("/api/audit/export")
def audit_export():
    from fastapi.responses import PlainTextResponse
    from . import audit
    return PlainTextResponse(audit.export_csv(), media_type="text/csv", headers={
        "Content-Disposition": 'attachment; filename="audit_log.csv"'})


@app.get("/api/graph")
def graph():
    engine = get_engine()
    return full_graph_json(engine.graph)


@app.get("/api/equipment")
def equipment():
    engine = get_engine()
    return {"equipment": engine.equipment_nodes()}


@app.get("/api/rca/{equipment_id}")
def rca(equipment_id: str):
    from .agents import maintenance_rca
    engine = get_engine()
    return maintenance_rca(engine, equipment_id)


@app.get("/api/compliance")
def compliance():
    from .agents import compliance_report
    engine = get_engine()
    return compliance_report(engine)


@app.get("/api/lessons")
def lessons():
    from .agents import lessons_learned
    engine = get_engine()
    return lessons_learned(engine)


# --- live ingestion ---
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    engine = get_engine()
    MAX = 8 * 1024 * 1024
    # reject oversized uploads BEFORE buffering the whole body into memory
    if getattr(file, "size", None) and file.size > MAX:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB).")
    raw = await file.read(MAX + 1)
    if len(raw) > MAX:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB).")
    name = file.filename or "uploaded.txt"
    if name.lower().endswith(".pdf"):
        from io import BytesIO
        try:
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(BytesIO(raw)).pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {e}")
    else:
        text = raw.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text in file.")
    log.info("ingesting uploaded document: %s (%d bytes)", name, len(raw))
    result = engine.add_document(name, text)
    return result


# --- analytics ---
@app.get("/api/overview")
def overview():
    from .analytics import operations_overview
    return operations_overview(get_engine())


@app.get("/api/entity/{entity_id}")
def entity(entity_id: str):
    from .analytics import entity_profile
    return entity_profile(get_engine(), entity_id)


@app.get("/api/benchmark")
def benchmark():
    from .benchmark import run
    return run(get_engine())


# --- audit-ready exports (open -> print to PDF) ---
@app.get("/api/export/rca/{equipment_id}", response_class=HTMLResponse)
def export_rca(equipment_id: str):
    from .reports import rca_report_html
    html = rca_report_html(get_engine(), equipment_id)
    return HTMLResponse(content=html, headers={
        "Content-Disposition": f'inline; filename="RCA_{equipment_id}.html"'})


@app.get("/api/export/compliance", response_class=HTMLResponse)
def export_compliance():
    from .reports import compliance_pack_html
    return HTMLResponse(content=compliance_pack_html(get_engine()), headers={
        "Content-Disposition": 'inline; filename="Compliance_Evidence_Pack.html"'})


@app.get("/api/documents")
def documents():
    engine = get_engine()
    docs = {}
    for c in engine.chunks:
        docs.setdefault(c["doc_id"], {"doc_id": c["doc_id"], "doc_type": c["doc_type"],
                                      "chunks": 0})
        docs[c["doc_id"]]["chunks"] += 1
    return {"documents": sorted(docs.values(), key=lambda d: d["doc_id"])}


@app.get("/api/document/{doc_id}")
def document(doc_id: str):
    engine = get_engine()
    parts = [c for c in engine.chunks if c["doc_id"] == doc_id]
    if not parts:
        raise HTTPException(status_code=404, detail="Document not found")
    parts.sort(key=lambda c: c["order"])
    return {
        "doc_id": doc_id,
        "doc_type": parts[0]["doc_type"],
        "text": "\n\n".join(p["text"] for p in parts),
    }


# --- serve frontend ---
@app.get("/")
def index():
    return FileResponse(str(config.FRONTEND_DIR / "index.html"))


if config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(" Industrial Knowledge Intelligence")
    print(f" LLM provider : {config.LLM_PROVIDER}  (key configured: {config.llm_available()})")
    print(f" Index built  : {config.INDEX_PATH.exists() and config.GRAPH_PATH.exists()}")
    print(" Open         : http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
