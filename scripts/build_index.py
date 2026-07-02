"""
Build the searchable index + knowledge graph from data/documents/.
Run this once after generating/adding documents:  python scripts/build_index.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config
from backend.ingestion import ingest_dir
from backend.graph import build_graph, save_graph, full_graph_json


def main() -> None:
    print(f"Reading documents from {config.DATA_DIR} …")
    chunks = ingest_dir()
    docs = sorted({c.doc_id for c in chunks})
    print(f"  {len(chunks)} chunks across {len(docs)} documents")

    config.INDEX_PATH.write_text(
        json.dumps({"chunks": [c.dict() for c in chunks]}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  wrote index -> {config.INDEX_PATH}")

    print("Building knowledge graph …")
    G = build_graph([c.dict() for c in chunks])
    save_graph(G)
    stats = full_graph_json(G)["stats"]
    print(f"  graph: {stats['nodes']} nodes, {stats['edges']} edges")
    print(f"  by type: {stats['by_type']}")
    print(f"  wrote graph -> {config.GRAPH_PATH}")

    # Golden-thread sanity check
    thread = "PUMP-204"
    if G.has_node(thread):
        docs_linked = [n for n in G.neighbors(thread)
                       if G.nodes[n].get("kind") == "document"]
        print(f"\nGolden thread {thread} links to {len(docs_linked)} documents:")
        for d in sorted(docs_linked):
            print("   -", d)
    print("\nDone. Start the server with:  python -m backend.main")


if __name__ == "__main__":
    main()
