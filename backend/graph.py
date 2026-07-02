"""
Knowledge graph construction and querying.

Nodes:
  - document nodes  (one per source file)
  - entity nodes    (equipment, personnel, regulatory, location, material)
Edges:
  - (document) --MENTIONS--> (entity)
  - (entity)   --CO_OCCURS-- (entity)   weighted by # shared documents

The graph is what turns "a pile of PDFs" into a linked "operations brain": querying
PUMP-204 traverses to the work orders, near-miss, inspection, and safety procedure
that reference it — cross-document intelligence, not single-document lookup.
"""
from __future__ import annotations

import json
import itertools
from collections import defaultdict

import networkx as nx

from . import config
from .entities import extract_entities, ExtractedEntity

_TYPE_COLORS = {
    "equipment": "#ff6b35",
    "personnel": "#4cc9f0",
    "regulatory": "#f7508f",
    "location": "#7bd88f",
    "material": "#f4c04a",
    "document": "#93a1b3",
}


def build_graph(chunks: list[dict]) -> nx.Graph:
    G = nx.Graph()
    # doc_id -> set of entities mentioned in it
    doc_entities: dict[str, dict[str, ExtractedEntity]] = defaultdict(dict)
    doc_type: dict[str, str] = {}

    for c in chunks:
        doc_type[c["doc_id"]] = c["doc_type"]
        for e in extract_entities(c["text"]):
            doc_entities[c["doc_id"]][e.id] = e

    # Map document-reference ids (e.g. "WO-2019-0453") to the actual file node
    # ("WO-2019-0453.txt") so a report citing a work order links to that work order.
    stem_to_file = {doc_id.rsplit(".", 1)[0].upper(): doc_id for doc_id in doc_type}

    def resolve(e: ExtractedEntity) -> tuple[str, bool]:
        """Return (node_id, is_document_file). Merge doc-refs onto real files."""
        if e.type == "document" and e.id.upper() in stem_to_file:
            return stem_to_file[e.id.upper()], True
        return e.id, False

    # add document nodes
    for doc_id, dtype in doc_type.items():
        G.add_node(doc_id, kind="document", type="document", label=doc_id,
                   doc_type=dtype, color=_TYPE_COLORS["document"])

    # add entity nodes + MENTIONS edges
    entity_docs: dict[str, set[str]] = defaultdict(set)
    for doc_id, ents in doc_entities.items():
        resolved_ids: dict[str, ExtractedEntity] = {}
        for e in ents.values():
            node_id, is_file = resolve(e)
            if is_file:
                # cross-reference between two documents (skip self-reference)
                if node_id != doc_id:
                    G.add_edge(doc_id, node_id, rel="REFERENCES", weight=1.0)
                continue
            resolved_ids[node_id] = e
            if not G.has_node(node_id):
                G.add_node(node_id, kind="entity", type=e.type, label=e.label,
                           color=_TYPE_COLORS.get(e.type, "#cccccc"))
            G.add_edge(doc_id, node_id, rel="MENTIONS", weight=1.0)
            entity_docs[node_id].add(doc_id)
        # replace with resolved set for co-occurrence step
        doc_entities[doc_id] = resolved_ids

    # entity-entity CO_OCCURS edges (weighted by shared docs)
    pair_shared: dict[tuple[str, str], int] = defaultdict(int)
    for ents in doc_entities.values():
        ids = sorted(ents.keys())
        for a, b in itertools.combinations(ids, 2):
            pair_shared[(a, b)] += 1
    for (a, b), n in pair_shared.items():
        if n >= 1:
            G.add_edge(a, b, rel="CO_OCCURS", weight=float(n))

    # stash degree/centrality for sizing
    for node in G.nodes:
        G.nodes[node]["degree"] = G.degree(node)
    return G


def save_graph(G: nx.Graph, path=None) -> None:
    path = path or config.GRAPH_PATH
    data = nx.node_link_data(G, edges="links")
    path.write_text(json.dumps(data), encoding="utf-8")


def load_graph(path=None) -> nx.Graph:
    path = path or config.GRAPH_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return nx.node_link_graph(data, edges="links")


def neighbors_of(G: nx.Graph, entity_ids: list[str], hops: int = 1) -> set[str]:
    """Return entity_ids plus their n-hop neighbours (documents + entities)."""
    frontier = set(e for e in entity_ids if G.has_node(e))
    seen = set(frontier)
    for _ in range(hops):
        nxt = set()
        for n in frontier:
            nxt |= set(G.neighbors(n))
        nxt -= seen
        seen |= nxt
        frontier = nxt
    return seen


def subgraph_json(G: nx.Graph, node_ids: set[str]) -> dict:
    """node-link JSON for a subgraph, ready for the frontend graph view."""
    H = G.subgraph(node_ids)
    nodes = [{
        "id": n,
        "label": G.nodes[n].get("label", n),
        "type": G.nodes[n].get("type", "entity"),
        "kind": G.nodes[n].get("kind", "entity"),
        "doc_type": G.nodes[n].get("doc_type", ""),
        "color": G.nodes[n].get("color", "#cccccc"),
        "degree": G.nodes[n].get("degree", 1),
    } for n in H.nodes]
    edges = [{
        "source": u, "target": v,
        "rel": d.get("rel", ""), "weight": d.get("weight", 1.0),
    } for u, v, d in H.edges(data=True)]
    return {"nodes": nodes, "edges": edges}


def full_graph_json(G: nx.Graph) -> dict:
    data = subgraph_json(G, set(G.nodes))
    kinds = defaultdict(int)
    for n in G.nodes:
        kinds[G.nodes[n].get("type", "entity")] += 1
    data["stats"] = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "by_type": dict(kinds),
    }
    return data
