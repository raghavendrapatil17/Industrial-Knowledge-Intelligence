"""
Entity extraction for industrial documents.

Strategy: deterministic, high-precision regex patterns tuned to industrial document
conventions (equipment tags, permit/work-order IDs, regulatory references, personnel,
locations, materials). This is fast, offline, and demo-reproducible. An optional LLM
pass can augment recall (see llm.extract_entities) but is NOT required.

Entity types: equipment | personnel | regulatory | location | material | document
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Ordered so that more specific patterns (document IDs, regulatory) win before the
# generic equipment matcher.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Regulatory references
    ("regulatory", re.compile(r"\bOISD-STD-\d{3}\b")),
    ("regulatory", re.compile(r"\bFactory Act Section\s*\d+[A-Z]?\b", re.I)),
    ("regulatory", re.compile(r"\bSection\s*(?:21|36|7A)\b")),
    # Document identifiers (work orders, permits, reports, procedures, drawings)
    ("document", re.compile(r"\bWO-\d{4}-\d{3,4}\b")),
    ("document", re.compile(r"\bNM-\d{4}-\d{2,3}\b")),
    ("document", re.compile(r"\bINS-\d{4}-\d{3,4}\b")),
    ("document", re.compile(r"\bINC-\d{4}-\d{2,3}\b")),
    ("document", re.compile(r"\bPTW-\d{4}-\d{3,4}\b")),
    ("document", re.compile(r"\bPID-[A-Z0-9-]+\b")),
    ("document", re.compile(r"\bSP-[A-Z]+-\d+\b")),
    ("document", re.compile(r"\bOP-[A-Z0-9]+-\d+\b")),
    ("document", re.compile(r"\bOM-[A-Z]+-\d+\b")),
    # Materials
    ("material", re.compile(r"\bTurbine Lube Oil ISO VG\s*\d+\b", re.I)),
    ("material", re.compile(r"\bISO VG\s*\d+\b", re.I)),
    # Locations
    ("location", re.compile(r"\bUnit-\d+\b")),
    ("location", re.compile(r"\bArea-\d+\b")),
    ("location", re.compile(r"\bBL-\d+\b")),
    # Personnel  (e.g. "R. Sharma")
    ("personnel", re.compile(r"\b[A-Z]\.\s?[A-Z][a-z]{2,}\b")),
    # Equipment tags (specific families) — checked LAST so IDs above are not swallowed
    ("equipment", re.compile(r"\bPUMP-\d{2,3}\b")),
    ("equipment", re.compile(r"\bMOTOR-\d{2,3}[A-Z]?\b")),
    ("equipment", re.compile(r"\bVALVE-\d{2,3}\b")),
    ("equipment", re.compile(r"\bFO-\d{2,3}\b")),
    ("equipment", re.compile(r"\bB-\d{3}\b")),   # boiler
    ("equipment", re.compile(r"\bK-\d{3}\b")),   # compressor
]

_TYPE_PRIORITY = ["regulatory", "document", "material", "location", "personnel", "equipment"]


@dataclass(frozen=True)
class ExtractedEntity:
    id: str
    type: str
    label: str


def normalize(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw.strip())
    # Uppercase tag-like ids; keep personnel/material human-readable
    if re.match(r"^[A-Za-z]{1,6}-", s) or s.upper().startswith(("OISD", "SECTION", "FACTORY")):
        return s.upper()
    return s


def extract_entities(text: str) -> list[ExtractedEntity]:
    """Return de-duplicated entities found in `text`, highest-priority type per id."""
    found: dict[str, ExtractedEntity] = {}
    claimed_spans: list[tuple[int, int]] = []

    for etype, pat in _PATTERNS:
        for m in pat.finditer(text):
            span = (m.start(), m.end())
            # skip if overlaps something already claimed by a higher-priority pattern
            if any(s < span[1] and span[0] < e for s, e in claimed_spans):
                continue
            eid = normalize(m.group(0))
            if not eid:
                continue
            # keep the higher-priority type if this id was already seen
            if eid in found:
                if _TYPE_PRIORITY.index(etype) < _TYPE_PRIORITY.index(found[eid].type):
                    found[eid] = ExtractedEntity(eid, etype, eid)
            else:
                found[eid] = ExtractedEntity(eid, etype, eid)
            claimed_spans.append(span)

    # Filter personnel false-positives: an initial + a common non-name word
    # (e.g. "U. Kingdom", "e.g. Started") is not a person.
    _NOT_SURNAMES = {"KINGDOM", "STATES", "SECTION", "STANDARD", "REPORT", "ORDER",
                     "AREA", "UNIT", "NOTES", "STARTED", "CHANGE", "DEGC", "ISO", "RMS",
                     "APPROX", "MINIMUM", "MAXIMUM", "NORMAL", "STATUS", "TYPE"}
    cleaned = {}
    for eid, e in found.items():
        if e.type == "personnel":
            surname = eid.split()[-1].upper() if " " in eid else ""
            if surname in _NOT_SURNAMES or any(w in eid.upper() for w in ("DEGC", "ISO", "RMS")):
                continue
        cleaned[eid] = e
    return list(cleaned.values())


if __name__ == "__main__":
    sample = open(__file__.replace("backend/entities.py", "data/documents/WO-2024-1187.txt"),
                  encoding="utf-8").read() if False else "PUMP-204 driven by MOTOR-204A in Unit-3 Area-7, ref WO-2019-0453, OISD-STD-106, A. Nair."
    for e in extract_entities(sample):
        print(f"{e.type:12} {e.id}")
