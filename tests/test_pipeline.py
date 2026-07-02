"""
Pipeline tests for the Industrial Knowledge Intelligence platform.
Run:  pytest -q     (from the project root, after python scripts/build_index.py)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.entities import extract_entities, normalize
from backend.ingestion import ingest_dir, detect_doc_type
from backend.graph import build_graph


# ---------- entity extraction ----------
def test_extract_equipment_and_regulatory():
    ents = {e.id: e.type for e in extract_entities(
        "PUMP-204 driven by MOTOR-204A in Unit-3, ref WO-2019-0453, OISD-STD-106, A. Nair.")}
    assert ents.get("PUMP-204") == "equipment"
    assert ents.get("MOTOR-204A") == "equipment"
    assert ents.get("UNIT-3") == "location"
    assert ents.get("OISD-STD-106") == "regulatory"
    assert ents.get("WO-2019-0453") == "document"
    assert ents.get("A. Nair") == "personnel"


def test_normalize_tags_uppercased():
    assert normalize("pump-204") == "PUMP-204"


def test_doc_type_detection():
    assert detect_doc_type("DOCUMENT TYPE: Near-Miss Report\n...", "x.txt") == "Near-Miss Report"


# ---------- ingestion + graph ----------
@pytest.fixture(scope="module")
def chunks():
    cs = ingest_dir()
    assert cs, "no chunks — run scripts/generate_corpus.py first"
    return [c.dict() for c in cs]


def test_corpus_ingests(chunks):
    docs = {c["doc_id"] for c in chunks}
    assert len(docs) >= 15


def test_golden_thread_links_across_docs(chunks):
    G = build_graph(chunks)
    assert G.has_node("PUMP-204")
    linked = [n for n in G.neighbors("PUMP-204") if G.nodes[n].get("kind") == "document"]
    # the golden thread must span many document types
    assert len(linked) >= 8


# ---------- engine + agents (needs a built index) ----------
@pytest.fixture(scope="module")
def engine():
    from backend import config
    if not config.INDEX_PATH.exists():
        pytest.skip("index not built — run python scripts/build_index.py")
    from backend.rag import KnowledgeEngine
    return KnowledgeEngine()


def test_ask_returns_cited_answer(engine):
    r = engine.ask("PUMP-204 seal failure history")
    assert r["citations"], "no citations returned"
    assert r["answer"]
    assert 0.0 <= r["confidence"] <= 1.0


def test_ask_cross_document(engine):
    r = engine.ask("What do we know about PUMP-204 failure history and safety concerns?")
    cited = {c["doc_id"] for c in r["citations"]}
    assert len(cited) >= 3  # pulls from multiple documents


def test_rca_is_asset_specific(engine):
    from backend.agents import maintenance_rca
    pump = maintenance_rca(engine, "PUMP-204")
    comp = maintenance_rca(engine, "K-101")
    assert pump["n_failure_events"] > comp["n_failure_events"]
    assert pump["health_score"] < comp["health_score"]


def test_compliance_finds_gaps(engine):
    from backend.agents import compliance_report
    d = compliance_report(engine)
    assert d["summary"]["gaps"] >= 1
    assert d["summary"]["covered"] >= 1


def test_lessons_finds_recurring_patterns(engine):
    from backend.agents import lessons_learned
    d = lessons_learned(engine)
    assert d["stats"]["recurring_patterns"] >= 1


def test_live_upload_and_link(engine):
    # snapshot persisted state so this mutating test leaves no trace
    from backend import config
    index_backup = config.INDEX_PATH.read_bytes()
    graph_backup = config.GRAPH_PATH.read_bytes()
    before = len(engine.all_docs())
    res = engine.add_document("TEST-UPLOAD-PUMP.txt",
        "DOCUMENT TYPE: Work Order\nEQUIPMENT: PUMP-204\nPUMP-204 seal replaced. Ref OISD-STD-105.")
    try:
        assert res["entities_extracted"] >= 2
        assert "PUMP-204" in res["entities"]
        assert res["linked_to_documents"]  # links to existing PUMP-204 docs
        assert len(engine.all_docs()) == before + 1
    finally:
        # restore clean state: source file + persisted index + graph
        (config.DATA_DIR / res["doc_id"]).unlink(missing_ok=True)
        config.INDEX_PATH.write_bytes(index_backup)
        config.GRAPH_PATH.write_bytes(graph_backup)


def test_benchmark_beats_baseline(engine):
    from backend.benchmark import run
    r = run(engine)
    assert r["summary"]["retrieval_hit_rate"] >= r["summary"]["baseline_hit_rate"]
