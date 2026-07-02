"""
Evaluation harness — quantifies the system against domain-expert benchmark questions,
and against a naive keyword-search baseline (what an engineer does today).

Metrics reported:
  - retrieval hit-rate : did the expected source document appear in the answer's citations?
  - answer coverage    : did the answer text mention the expected key fact/tag?
  - time-to-answer     : median ms  (the brief's "time-to-answer vs traditional search")
  - vs keyword baseline: same hit-rate metric for a plain substring/keyword search
"""
from __future__ import annotations

import re
import time
from statistics import median

# (question, expected source doc, expected key token in answer)
BENCHMARK = [
    ("What is PUMP-204's mechanical seal failure history?", "WO-2019-0453.txt", "seal"),
    ("Why is PUMP-204 bearing vibration rising?", "WO-2024-1187.txt", "bearing"),
    ("What near-miss involved hot work near PUMP-204?", "nearmiss-NM-2023-089.txt", "hot work"),
    ("What OISD standard governs the work permit system?", "OISD-STD-105-excerpt.txt", "permit"),
    ("Which Factory Act section covers machinery guarding?", "Factory-Act-excerpts.txt", "21"),
    ("What safety procedure covers confined space entry in Area-7?", "SP-CSE-014.txt", "confined"),
    ("What permit authorised hot work near PUMP-204 discharge?", "PTW-2024-3320.txt", "hot work"),
    ("What did the 2019 incident on MOTOR-204A reveal?", "incident-2019-report.txt", "guard"),
    ("Which pump supplies feed water to Boiler B-301?", "boiler-B301-procedure.txt", "PUMP-204"),
    ("What are the seal flush temperature limits for the feed water pump?", "OM-CP-04-centrifugal-pump.txt", "80"),
    ("What is the vibration alarm setpoint for PUMP-204?", "insp-INS-2024-0210.txt", "7.1"),
    ("What lubricant is used on the pump bearings?", "MSDS-turbine-lube-oil.txt", "ISO VG 46"),
]


def _keyword_baseline(engine, question: str) -> tuple[str | None, int]:
    """Naive baseline: substring keyword scan across raw documents (what search does today)."""
    t0 = time.perf_counter()
    terms = [w for w in re.findall(r"[a-z0-9-]+", question.lower()) if len(w) > 3]
    best, best_score = None, 0
    for did in engine.all_docs():
        text = engine.full_text(did).lower()
        score = sum(text.count(t) for t in terms)
        if score > best_score:
            best, best_score = did, score
    return best, int((time.perf_counter() - t0) * 1000)


def run(engine) -> dict:
    rows = []
    sys_times, base_times = [], []
    sys_hits = base_hits = coverage_hits = 0

    for q, expected, key in BENCHMARK:
        t0 = time.perf_counter()
        res = engine.ask(q)
        dt = int((time.perf_counter() - t0) * 1000)
        sys_times.append(dt)
        cited = [c["doc_id"] for c in res["citations"]]
        hit = expected in cited
        cover = key.lower() in res["answer"].lower()
        sys_hits += hit
        coverage_hits += cover

        base_doc, base_dt = _keyword_baseline(engine, q)
        base_times.append(base_dt)
        base_hit = base_doc == expected
        base_hits += base_hit

        rows.append({
            "question": q, "expected": expected,
            "retrieved": cited[:3], "hit": hit, "coverage": cover,
            "time_ms": dt, "baseline_doc": base_doc, "baseline_hit": base_hit,
        })

    n = len(BENCHMARK)
    return {
        "summary": {
            "questions": n,
            "retrieval_hit_rate": round(100 * sys_hits / n),
            "answer_coverage": round(100 * coverage_hits / n),
            "baseline_hit_rate": round(100 * base_hits / n),
            "median_time_ms": int(median(sys_times)),
            "baseline_median_time_ms": int(median(base_times)),
        },
        "results": rows,
    }
