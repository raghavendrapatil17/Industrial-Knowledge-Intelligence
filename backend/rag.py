"""
Retrieval + reasoning orchestrator.

Pipeline for a question:
  1. Hybrid retrieve top chunks (BM25 [+ optional dense]).
  2. Extract entities from the question + top chunks; expand via the knowledge graph
     (graph traversal) to pull in connected documents the lexical search alone might miss.
  3. Assemble grounded context; generate a cited answer (LLM or offline extractive).
  4. Compute a confidence score (corroborating sources + retrieval strength).
  5. Return the answer, citations, entities, and the relevant answer-subgraph.
"""
from __future__ import annotations

import json
import re
import time
import logging
import threading

from . import config
from .vectorstore import HybridIndex
from .graph import load_graph, build_graph, save_graph, subgraph_json, neighbors_of
from .entities import extract_entities
from .ingestion import detect_doc_type, _split_sections
from . import llm

log = logging.getLogger("iki.engine")


def _safe_filename(name: str) -> str:
    """Reduce an uploaded filename to a safe basename (no path traversal / illegal chars)."""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name).strip().lstrip(".")
    if not name:
        name = "upload.txt"
    if "." not in name:
        name += ".txt"
    return name


class KnowledgeEngine:
    def __init__(self):
        data = json.loads(config.INDEX_PATH.read_text(encoding="utf-8"))
        self.chunks: list[dict] = data["chunks"]
        self.graph = load_graph()
        self._lock = threading.RLock()   # guards live-ingestion mutations
        self._reindex(persist=False, rebuild_graph=False)

    # -- (re)build all derived state from self.chunks ---------------------------
    def _reindex(self, persist: bool = True, rebuild_graph: bool = True) -> None:
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self.index = HybridIndex(self.chunks)
        self._doc_text = {}
        self._doc_type = {}
        for c in sorted(self.chunks, key=lambda x: (x["doc_id"], x["order"])):
            self._doc_text.setdefault(c["doc_id"], "")
            self._doc_text[c["doc_id"]] += ("\n\n" if self._doc_text[c["doc_id"]] else "") + c["text"]
            self._doc_type[c["doc_id"]] = c["doc_type"]
        if rebuild_graph:
            self.graph = build_graph(self.chunks)
        if persist:
            config.INDEX_PATH.write_text(
                json.dumps({"chunks": self.chunks}, ensure_ascii=False), encoding="utf-8")
            save_graph(self.graph)

    # -- live ingestion: add a document at runtime ------------------------------
    def add_document(self, filename: str, text: str, raw: bytes | None = None) -> dict:
        """Ingest a new document into the live index + knowledge graph.
        `raw` is the original file bytes — persisted verbatim so a binary format
        (xlsx/pdf/eml) re-parses correctly on the next index rebuild."""
        doc_id = _safe_filename(filename)   # strip path components + illegal chars
        with self._lock:
            # de-dup name (doc_id is guaranteed to contain a "." by _safe_filename)
            if doc_id in self._doc_type:
                stem, _, ext = doc_id.rpartition(".")
                n = 2
                while f"{stem}-{n}.{ext}" in self._doc_type:
                    n += 1
                doc_id = f"{stem}-{n}.{ext}"

            doc_type = detect_doc_type(text, doc_id)
            sections = _split_sections(text)
            before_nodes, before_edges = self.graph.number_of_nodes(), self.graph.number_of_edges()

            added = [{
                "chunk_id": f"{doc_id}::{i}", "doc_id": doc_id,
                "doc_type": doc_type, "text": sect, "order": i,
            } for i, sect in enumerate(sections)]
            # rebind (not in-place append) so concurrent readers keep a stable list
            self.chunks = self.chunks + added

            # persist the ORIGINAL file so it survives restart AND re-parses correctly
            try:
                if raw is not None:
                    (config.DATA_DIR / doc_id).write_bytes(raw)
                else:
                    (config.DATA_DIR / doc_id).write_text(text, encoding="utf-8")
            except Exception as e:  # pragma: no cover
                log.warning("could not persist uploaded file: %s", e)

            self._reindex(persist=True, rebuild_graph=True)

        ents = extract_entities(text)
        linked_docs = set()
        for e in ents:
            if self.graph.has_node(e.id):
                linked_docs |= {n for n in self.graph.neighbors(e.id)
                                if self.graph.nodes[n].get("kind") == "document" and n != doc_id}
        return {
            "doc_id": doc_id, "doc_type": doc_type, "chunks": len(sections),
            "entities_extracted": len(ents),
            "entities": sorted({e.id for e in ents}),
            "linked_to_documents": sorted(linked_docs),
            "graph_nodes_added": self.graph.number_of_nodes() - before_nodes,
            "graph_edges_added": self.graph.number_of_edges() - before_edges,
        }

    # -- shared accessors used by the specialist agents -------------------------
    def full_text(self, doc_id: str) -> str:
        return self._doc_text.get(doc_id, "")

    def doc_type(self, doc_id: str) -> str:
        return self._doc_type.get(doc_id, "Document")

    def all_docs(self) -> list[str]:
        return sorted(self._doc_text.keys())

    def docs_for_entity(self, entity_id: str) -> list[str]:
        """Document files linked to an entity in the knowledge graph."""
        if not self.graph.has_node(entity_id):
            return []
        return sorted(n for n in self.graph.neighbors(entity_id)
                      if self.graph.nodes[n].get("kind") == "document")

    def equipment_nodes(self) -> list[str]:
        return sorted(n for n in self.graph.nodes
                      if self.graph.nodes[n].get("type") == "equipment")

    # -- grounding: sentences in a chunk that best support the question ---------
    _STOP = {"the", "and", "for", "are", "with", "that", "this", "from", "any", "was",
             "what", "which", "when", "where", "how", "does", "did", "has", "have",
             "system", "report", "records", "about", "into", "near", "our", "all"}

    @staticmethod
    def _supporting_sentences(text: str, question: str, answer: str, k: int = 2) -> list[str]:
        import re as _re
        # ignore stopwords so grounding keys off meaningful terms/tags, not "the"/"system"
        terms = set(t for t in _re.findall(r"[a-z0-9-]+", (question + " " + answer).lower())
                    if len(t) > 2 and t not in KnowledgeEngine._STOP)
        scored = []
        for sent in _re.split(r"(?<=[.!?])\s+|\n+", text):
            s = sent.strip()
            if len(s) < 20 or s.upper().startswith(("DOCUMENT TYPE", "REPORT NO", "WORK ORDER NO")):
                continue
            st = set(_re.findall(r"[a-z0-9-]+", s.lower()))
            score = len(terms & st) + sum(2 for t in terms if "-" in t and t in s.lower())
            if score > 0:
                scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]

    @staticmethod
    def _follow_ups(entities: list[dict], question: str) -> list[str]:
        """Context-aware next questions derived from the answer's entities."""
        ups: list[str] = []
        ql = question.lower()
        def _pick(t):
            same = [e["id"] for e in entities if e["type"] == t]
            # prefer an entity that appears in the question itself
            return next((x for x in same if x.lower() in ql), same[0] if same else None)
        eq = _pick("equipment")
        reg = _pick("regulatory")
        loc = _pick("location")
        if eq:
            ups.append(f"What is {eq}'s maintenance and failure history?")
            ups.append(f"What safety procedures apply to work on {eq}?")
        if reg:
            ups.append(f"What does {reg} require?")
        if loc and len(ups) < 3:
            ups.append(f"What permits or hazards are active in {loc}?")
        # de-dupe, drop anything identical to the asked question, cap at 3
        out = []
        for u in ups:
            if u.lower() != question.lower() and u not in out:
                out.append(u)
        return out[:3]

    # -- confidence heuristic ---------------------------------------------------
    @staticmethod
    def _confidence(hits, distinct_docs: int, top_score: float) -> tuple[float, str]:
        # corroboration: more distinct source documents => higher trust
        corr = min(distinct_docs / 4.0, 1.0)
        strength = min(top_score, 1.0)
        score = round(0.6 * corr + 0.4 * strength, 2)
        label = "High" if score >= 0.7 else "Medium" if score >= 0.4 else "Low"
        return score, label

    def ask(self, question: str, top_k: int | None = None) -> dict:
        t0 = time.time()
        top_k = max(1, min(int(top_k or config.TOP_K), 50))   # clamp; reject bad values

        # snapshot a consistent view of the index/graph under the lock so a concurrent
        # live-ingestion reindex can't pair a new index with a stale by_id map (KeyError).
        with self._lock:
            index, by_id, chunks, graph = self.index, self.by_id, self.chunks, self.graph

        # 1. lexical/dense retrieval
        hits = index.search(question, top_k=top_k)
        retrieved = [by_id[h.chunk_id] for h in hits if h.chunk_id in by_id]
        top_score = hits[0].score if hits else 0.0

        # 2. graph expansion: entities in question + retrieved -> neighbouring docs
        seed_entities = {e.id for e in extract_entities(question)}
        for c in retrieved:
            for e in extract_entities(c["text"]):
                seed_entities.add(e.id)

        expanded_nodes = neighbors_of(graph, list(seed_entities),
                                      hops=config.GRAPH_EXPANSION_HOPS)
        connected_docs = [n for n in expanded_nodes
                          if graph.nodes.get(n, {}).get("kind") == "document"]

        # pull in a couple of graph-connected docs not already retrieved (cross-doc power)
        have = {c["doc_id"] for c in retrieved}
        for doc_id in connected_docs:
            if doc_id not in have and len(retrieved) < top_k + 3:
                # add that document's header chunk (lowest order), robust to list order
                doc_chunks = [c for c in chunks if c["doc_id"] == doc_id]
                extra = min(doc_chunks, key=lambda c: c["order"]) if doc_chunks else None
                if extra:
                    retrieved.append(extra)
                    have.add(doc_id)

        # 3. answer generation
        answer, mode = llm.generate_answer(question, retrieved)

        # 4. citations + entities
        citations = []
        seen_docs = set()
        for h in hits:
            c = by_id.get(h.chunk_id)
            if not c:
                continue
            citations.append({
                "doc_id": c["doc_id"], "doc_type": c["doc_type"],
                "chunk_id": c["chunk_id"],
                "snippet": (c["text"][:220] + "…") if len(c["text"]) > 220 else c["text"],
                "score": round(h.score, 3),
                "highlights": self._supporting_sentences(c["text"], question, answer),
            })
            seen_docs.add(c["doc_id"])
        # include graph-added docs as citations too
        for c in retrieved:
            if c["doc_id"] not in seen_docs:
                citations.append({
                    "doc_id": c["doc_id"], "doc_type": c["doc_type"],
                    "chunk_id": c["chunk_id"],
                    "snippet": (c["text"][:220] + "…") if len(c["text"]) > 220 else c["text"],
                    "score": 0.0, "via": "graph",
                    "highlights": self._supporting_sentences(c["text"], question, answer),
                })
                seen_docs.add(c["doc_id"])

        # entities to display
        answer_entities = []
        seen_e = set()
        for eid in seed_entities:
            if eid in seen_e or not graph.has_node(eid):
                continue
            seen_e.add(eid)
            answer_entities.append({
                "id": eid,
                "type": graph.nodes[eid].get("type", "entity"),
                "label": graph.nodes[eid].get("label", eid),
            })

        # 5. confidence + answer subgraph
        conf, conf_label = self._confidence(hits, len(seen_docs), top_score)
        sub_nodes = set(expanded_nodes) | seen_docs | seed_entities
        sub_nodes = {n for n in sub_nodes if graph.has_node(n)}
        graph_json = subgraph_json(graph, sub_nodes)

        entities_sorted = sorted(answer_entities, key=lambda e: e["type"])
        # grounding gate: an answer is "grounded" only if supporting sentences were found
        # AND retrieval was corroborated — otherwise flag it for human verification.
        grounded = bool(citations) and any(c.get("highlights") for c in citations) and conf >= 0.4
        advisory = None if grounded else (
            "Low supporting evidence — verify against source documents before acting."
            if citations else "No matching records found for this query.")
        return {
            "answer": answer,
            "citations": citations,
            "entities": entities_sorted,
            "follow_ups": self._follow_ups(entities_sorted, question),
            "confidence": conf,
            "confidence_label": conf_label,
            "grounded": grounded,
            "advisory": advisory,
            "graph": graph_json,
            "mode": mode,
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
