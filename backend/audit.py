"""
Audit trail — append-only provenance log of every question answered.

In regulated, safety-critical industries an answer isn't trustworthy unless it's
*traceable*: who asked what, when, how confident the system was, and exactly which
source documents grounded the answer. This module records that for every query, giving
the platform full auditability — a requirement real industrial deployments must meet.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

from . import config

_LOG = config.STORAGE_DIR / "audit_log.jsonl"
_lock = threading.Lock()


def log_query(question: str, resp: dict) -> None:
    """Append one answered-query record. Never raises into the request path."""
    try:
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "question": question,
            "mode": resp.get("mode"),
            "confidence": resp.get("confidence"),
            "confidence_label": resp.get("confidence_label"),
            "grounded": resp.get("grounded"),
            "sources": sorted({c["doc_id"] for c in resp.get("citations", [])}),
            "elapsed_ms": resp.get("elapsed_ms"),
        }
        with _lock:
            with _LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # auditing must never break answering
        pass


def recent(n: int = 25) -> dict:
    if not _LOG.exists():
        return {"events": [], "stats": {"total_queries": 0, "avg_confidence": None,
                                        "grounded_pct": None}}
    lines = _LOG.read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    total = len(events)
    confs = [e["confidence"] for e in events if isinstance(e.get("confidence"), (int, float))]
    grounded = [e for e in events if e.get("grounded")]
    return {
        "events": list(reversed(events[-n:])),
        "stats": {
            "total_queries": total,
            "avg_confidence": round(sum(confs) / len(confs), 2) if confs else None,
            "grounded_pct": round(100 * len(grounded) / total) if total else None,
        },
    }
