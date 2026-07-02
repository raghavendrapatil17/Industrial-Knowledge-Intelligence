"""Pydantic models shared across the API."""
from __future__ import annotations

from pydantic import BaseModel


class Citation(BaseModel):
    doc_id: str
    doc_type: str
    chunk_id: str
    snippet: str
    score: float


class Entity(BaseModel):
    id: str          # normalized, e.g. "PUMP-204"
    type: str        # equipment | location | personnel | regulatory | material | document
    label: str


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    entities: list[Entity]
    confidence: float
    confidence_label: str
    graph: dict          # subgraph relevant to this answer (node-link JSON)
    mode: str            # "llm" or "offline"
    elapsed_ms: int


class GraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    stats: dict
