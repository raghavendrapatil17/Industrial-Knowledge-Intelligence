"""
Lightweight hybrid retrieval index.

- BM25 lexical retrieval (rank-bm25): excellent for tag-heavy industrial queries
  ("PUMP-204", "OISD-STD-105"), zero model download, fully offline.
- Optional dense embeddings (sentence-transformers) blended in when enabled.

Kept intentionally dependency-light and reproducible for a reliable live demo.
"""
from __future__ import annotations

import re
import math
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from . import config

_TOKEN = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    # keep hyphenated tags (PUMP-204) as single tokens AND their parts for recall
    toks: list[str] = []
    for m in _TOKEN.findall(text.lower()):
        toks.append(m)
        if "-" in m:
            toks.extend(m.split("-"))
    return toks


@dataclass
class Hit:
    chunk_id: str
    score: float


class HybridIndex:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.ids = [c["chunk_id"] for c in chunks]
        self._corpus_tokens = [tokenize(c["text"]) for c in chunks]
        # BM25Okapi divides by corpus size — guard the empty-corpus case
        self.bm25 = BM25Okapi(self._corpus_tokens) if self._corpus_tokens else None
        self._dense = None
        self._embeddings = None
        if config.USE_DENSE_EMBEDDINGS:
            self._try_load_dense()

    def _try_load_dense(self) -> None:  # pragma: no cover (optional path)
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            self._dense = SentenceTransformer("all-MiniLM-L6-v2")
            embs = self._dense.encode([c["text"] for c in self.chunks],
                                      normalize_embeddings=True)
            self._embeddings = np.asarray(embs, dtype="float32")
        except Exception as e:
            print(f"[vectorstore] dense embeddings unavailable ({e}); using BM25 only")
            self._dense = None

    def search(self, query: str, top_k: int = 6) -> list[Hit]:
        if self.bm25 is None:
            return []
        q_tokens = tokenize(query)
        bm = self.bm25.get_scores(q_tokens)
        bm_max = max(bm) if len(bm) and max(bm) > 0 else 1.0
        scores = [s / bm_max for s in bm]  # normalize 0..1

        if self._dense is not None and self._embeddings is not None:  # pragma: no cover
            import numpy as np
            qv = self._dense.encode([query], normalize_embeddings=True)[0]
            dense = self._embeddings @ np.asarray(qv, dtype="float32")
            scores = [0.5 * s + 0.5 * float(d) for s, d in zip(scores, dense)]

        ranked = sorted(zip(self.ids, scores), key=lambda x: x[1], reverse=True)
        return [Hit(cid, float(sc)) for cid, sc in ranked[:top_k] if sc > 0]
