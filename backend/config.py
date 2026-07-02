"""Central configuration. Reads .env if present; safe defaults otherwise."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "documents"
STORAGE_DIR = ROOT / "storage"
FRONTEND_DIR = ROOT / "frontend"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = STORAGE_DIR / "index.json"        # chunks + entities
GRAPH_PATH = STORAGE_DIR / "graph.json"        # knowledge graph (node-link)

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

USE_DENSE_EMBEDDINGS = os.getenv("USE_DENSE_EMBEDDINGS", "0") == "1"

# Chunking
CHUNK_MAX_CHARS = 1100
CHUNK_OVERLAP_CHARS = 150

# Retrieval
TOP_K = 6
GRAPH_EXPANSION_HOPS = 1


def llm_available() -> bool:
    """True if an LLM API key is configured for the selected provider."""
    if LLM_PROVIDER == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return False
