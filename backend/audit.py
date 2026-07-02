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

_MAX_BYTES = 2 * 1024 * 1024   # cap log size; trim to last _KEEP lines beyond this
_KEEP = 2000
_TAIL_BYTES = 256 * 1024       # recent() only needs the tail of the file


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
            # bound unbounded growth: keep only the last _KEEP lines
            if _LOG.stat().st_size > _MAX_BYTES:
                lines = _LOG.read_text(encoding="utf-8").splitlines()[-_KEEP:]
                _LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:  # auditing must never break answering
        pass


def _read_records(tail_only: bool = False) -> list[dict]:
    """Parse the log, skipping any malformed/partial line (crash-safe)."""
    if not _LOG.exists():
        return []
    with _lock:
        if tail_only and _LOG.stat().st_size > _TAIL_BYTES:
            with _LOG.open("rb") as f:
                f.seek(-_TAIL_BYTES, 2)
                data = f.read().decode("utf-8", "ignore")
            lines = data.splitlines()[1:]   # drop first (likely partial) line
        else:
            lines = _LOG.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue   # skip a truncated/partial final line
    return out


def _csv_safe(val) -> str:
    """Neutralise CSV formula-injection (leading = + - @ tab/CR execute in Excel)."""
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def export_csv() -> str:
    """Full audit log as CSV (for compliance record-keeping)."""
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp_utc", "question", "mode", "confidence", "confidence_label",
                "grounded", "sources", "elapsed_ms"])
    for e in _read_records():
        w.writerow([_csv_safe(e.get("ts")), _csv_safe(e.get("question")), _csv_safe(e.get("mode")),
                    e.get("confidence"), _csv_safe(e.get("confidence_label")), e.get("grounded"),
                    _csv_safe("; ".join(e.get("sources", []))), e.get("elapsed_ms")])
    return buf.getvalue()


def recent(n: int = 25) -> dict:
    events = _read_records(tail_only=True)
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
