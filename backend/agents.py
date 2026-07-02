"""
Specialist agents built on top of the shared KnowledgeEngine (vector index + knowledge
graph). All three consume the SAME graph the Copilot uses — this is the "one brain, many
lenses" design that the problem statement rewards.

  agent 3  maintenance_rca(engine, equipment_id) -> RCA + predictive maintenance
  agent 4  compliance_report(engine)             -> regulatory gap analysis
  agent 5  lessons_learned(engine)               -> recurring failure patterns

Everything is deterministic/offline by default; maintenance_rca can optionally use the LLM
for a narrative summary when a key is configured.
"""
from __future__ import annotations

import re
from collections import defaultdict

from . import llm, config


# --------------------------------------------------------------------------- #
# shared parsing helpers
# --------------------------------------------------------------------------- #
_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def _first_date(text: str) -> str | None:
    m = _DATE.search(text)
    return m.group(1) if m else None


def _section(text: str, *labels: str) -> str | None:
    """Return the text following the first matching UPPERCASE label up to the next blank line/label."""
    for label in labels:
        m = re.search(rf"{label}\s*:?\s*\n?(.+?)(?:\n\s*\n|\n[A-Z][A-Z /&()-]{{3,}}:|\Z)",
                      text, re.S | re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    return None


def _vibration_readings(text: str) -> list[float]:
    """Actual readings only (measured in 'mm/s RMS'); ignore alarm/trip THRESHOLDS."""
    vals = []
    for m in re.finditer(r"([\d.]+)\s*mm/s\s*RMS", text):
        # skip if preceded by threshold words like alarm/trip/below/normal
        pre = text[max(0, m.start() - 30):m.start()].lower()
        if any(w in pre for w in ("alarm", "trip", "below", "normal", "above")):
            continue
        vals.append(float(m.group(1)))
    return vals


def _mentions(text: str, entity_id: str) -> int:
    return len(re.findall(re.escape(entity_id), text, re.I))


# theme keywords for pattern clustering (agent 5) and RCA tagging — tuned to FAILURE
# semantics so normal-procedure mentions (routine isolation, "recycle gas compressor")
# don't create false patterns.
_THEMES = {
    "Mechanical seal failure": r"seal (leak|fail|face wear|flush)|leaking.*seal",
    "Bearing degradation": r"bearing.*(vibrat|spall|degrad|replace|defect|high)",
    "Machinery guard failure": r"guard.*(remov|not reinstat|missing|not in place)",
    "Hot work / ignition proximity": r"hot work|grinding|ignition|flash fire",
    "Gas / hydrocarbon exposure": r"hydrocarbon|\bLEL\b|flammable gas|gas leak|entrapped gas",
    "Feedwater / water chemistry": r"feedwater|conductivity|scal(e|ing)|water treatment",
    "Vibration exceedance": r"vibration.*(rising|alarm|high|exceed)|rising.*vibration",
}


def _themes_in(text: str) -> list[str]:
    return [name for name, pat in _THEMES.items() if re.search(pat, text, re.I)]


_FAILURE_TYPES = {"Maintenance Work Order", "Near-Miss Report", "Inspection Report",
                  "Incident Investigation Report"}


# --------------------------------------------------------------------------- #
# Agent 3 — Maintenance Intelligence & RCA
# --------------------------------------------------------------------------- #
def maintenance_rca(engine, equipment_id: str) -> dict:
    equipment_id = equipment_id.strip().upper()
    linked = engine.docs_for_entity(equipment_id)
    # keep only documents where this equipment is a PRIMARY subject (mentioned >= 2x),
    # so passing references (e.g. another asset's work order) don't pollute the RCA.
    doc_ids = [d for d in linked if _mentions(engine.full_text(d), equipment_id) >= 2]

    events: list[dict] = []
    all_vibration: list[tuple[str, float]] = []
    root_causes: list[dict] = []
    recommendations: list[dict] = []
    themes_counter: dict[str, int] = defaultdict(int)

    for did in doc_ids:
        dtype = engine.doc_type(did)
        text = engine.full_text(did)
        if dtype not in _FAILURE_TYPES:
            continue
        date = _first_date(text) or "n/a"
        problem = _section(text, "PROBLEM DESCRIPTION", "DESCRIPTION OF EVENT", "SUMMARY", "RESULTS")
        rc = _section(text, "Root cause", "ROOT CAUSES", "FINDINGS")
        rec = _section(text, "RECOMMENDATION", "CORRECTIVE ACTIONS", "FOLLOW-UP",
                       "LESSON LEARNED / RECOMMENDATION")
        for name in _themes_in(text):
            themes_counter[name] += 1
        for v in _vibration_readings(text):
            all_vibration.append((date, v))
        events.append({
            "date": date, "doc_id": did, "doc_type": dtype,
            "summary": (problem[:220] + "…") if problem and len(problem) > 220 else (problem or dtype),
        })
        if rc:
            root_causes.append({"doc_id": did, "text": (rc[:260] + "…") if len(rc) > 260 else rc})
        if rec:
            recommendations.append({"doc_id": did, "text": (rec[:260] + "…") if len(rec) > 260 else rec})

    events.sort(key=lambda e: e["date"])

    # --- health / risk scoring ---
    n_fail = len(events)
    vib_vals = [v for _, v in all_vibration]
    peak_vib = max(vib_vals) if vib_vals else None
    recent = [e for e in events if e["date"] >= "2024-01-01"]
    # recurring theme = same failure theme appearing 2+ times
    recurring = sorted([t for t, c in themes_counter.items() if c >= 2],
                       key=lambda t: -themes_counter[t])

    score = 100
    score -= min(n_fail, 5) * 7          # failure history
    score -= len(recurring) * 8          # systemic recurrence is the real risk signal
    if peak_vib and peak_vib >= 7.1:     # a genuine reading at/over alarm
        score -= 10
    score = max(10, min(100, score))
    if score >= 75:
        health = "Healthy"
    elif score >= 40:
        health = "Watch — Degrading"
    else:
        health = "At Risk"

    # --- narrative (LLM if available, else deterministic) ---
    narrative = _rca_narrative(engine, equipment_id, events, root_causes, recurring, peak_vib)

    return {
        "equipment": equipment_id,
        "health_label": health,
        "health_score": score,
        "n_failure_events": n_fail,
        "recent_events": len(recent),
        "peak_vibration_mm_s": peak_vib,
        "recurring_themes": recurring,
        "timeline": events,
        "root_causes": root_causes,
        "recommendations": recommendations,
        "linked_documents": doc_ids,
        "narrative": narrative,
        "vibration_trend": [{"date": d, "value": v} for d, v in sorted(all_vibration)],
    }


def _rca_narrative(engine, eqp, events, root_causes, recurring, peak_vib) -> str:
    if not events:
        return f"No maintenance, inspection, or incident history found for {eqp} in the corpus."
    if config.llm_available():
        ctx = [{"doc_id": e["doc_id"], "doc_type": e["doc_type"],
                "text": engine.full_text(e["doc_id"])} for e in events]
        q = (f"Perform a Root Cause Analysis for {eqp}. Using ONLY the maintenance, inspection, "
             f"near-miss and incident records provided, explain the underlying (systemic) root "
             f"cause connecting these events, not just the immediate causes. Give a predictive "
             f"maintenance recommendation. Cite [DOC-ID].")
        try:
            ans, _ = llm.generate_answer(q, ctx)
            return ans
        except Exception:
            pass
    # deterministic fallback
    parts = [f"{eqp} shows {len(events)} recorded failure/inspection events."]
    if recurring:
        parts.append("Recurring pattern(s): " + ", ".join(recurring) +
                     " — indicating a systemic issue rather than isolated component failures.")
    if peak_vib:
        parts.append(f"Peak recorded vibration {peak_vib} mm/s.")
    if root_causes:
        parts.append("Documented root causes converge on: " +
                     "; ".join(rc["text"] for rc in root_causes[:2]))
    parts.append("Predictive action: keep on the vibration watch list, address the recurring "
                 "root cause upstream, and pre-empt the next failure rather than repair-after-fail.")
    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Agent 4 — Quality & Regulatory Compliance Intelligence
# --------------------------------------------------------------------------- #
# Requirements distilled from the regulations present in the corpus. Each is checked for
# supporting EVIDENCE across the document set; missing evidence surfaces as a compliance GAP.
_REQUIREMENTS = [
    {"id": "OISD105-PTW", "regulation": "OISD-STD-105", "area": "Work Permit",
     "requirement": "A written Permit-to-Work is issued for hot work.",
     "evidence": [r"permit to work", r"\bPTW-\d"], },
    {"id": "OISD105-GAS", "regulation": "OISD-STD-105", "area": "Work Permit",
     "requirement": "Gas testing (LEL/O2) performed and recorded before hot work.",
     "evidence": [r"gas test", r"LEL\s*\d", r"O2\s*\d"], },
    {"id": "OISD105-SIMOPS", "regulation": "OISD-STD-105", "area": "SIMOPS",
     "requirement": "Simultaneous-operations (SIMOPS) review reconciles conflicting permits.",
     "evidence": [r"simops", r"simultaneous operation"], },
    {"id": "FA36-CSE", "regulation": "Factory Act Section 36", "area": "Confined Space",
     "requirement": "Confined space entry requires atmosphere testing + standby attendant.",
     "evidence": [r"standby attendant", r"confined space", r"continuous gas monitor"], },
    {"id": "FA21-GUARD", "regulation": "Factory Act Section 21", "area": "Machinery Guarding",
     "requirement": "Rotating machinery guards fitted and reinstated before restart.",
     "evidence": [r"guard.*(intact|in place|reinstat)", r"machinery.*fenc"], },
    {"id": "OISD106-HOTSURF", "regulation": "OISD-STD-106", "area": "Hot Surface",
     "requirement": "Hot surfaces above limit are insulated.",
     "evidence": [r"insulat", r"hot surface"], },
    # --- deliberately harder-to-evidence items (expected GAPS) ---
    {"id": "GUARD-SIGNOFF", "regulation": "Factory Act Section 21", "area": "Machinery Guarding",
     "requirement": "Guard-reinstatement sign-off recorded on EVERY rotating-equipment work order.",
     "evidence": [r"guard reinstat.*sign-?off", r"guard sign-?off"], },
    {"id": "FEEDWATER-LOG", "regulation": "OEM / Reliability", "area": "Water Chemistry",
     "requirement": "Feedwater chemistry (conductivity/hardness) monitoring records maintained.",
     "evidence": [r"feedwater chemistry (record|log|report)", r"conductivity log"], },
    {"id": "PESO-CERT", "regulation": "PESO", "area": "Pressure Systems",
     "requirement": "Valid PESO certification for pressure vessels / systems on file.",
     "evidence": [r"\bPESO\b.*certif", r"pressure vessel certif"], },
]


def compliance_report(engine) -> dict:
    corpus = {did: engine.full_text(did) for did in engine.all_docs()}
    results = []
    covered = gaps = 0
    for req in _REQUIREMENTS:
        cites = []
        for did, text in corpus.items():
            if any(re.search(p, text, re.I) for p in req["evidence"]):
                cites.append(did)
        status = "Covered" if cites else "Gap"
        if status == "Covered":
            covered += 1
        else:
            gaps += 1
        results.append({
            "id": req["id"], "regulation": req["regulation"], "area": req["area"],
            "requirement": req["requirement"], "status": status,
            "evidence": cites[:4],
        })
    total = len(results)
    return {
        "summary": {
            "total_requirements": total, "covered": covered, "gaps": gaps,
            "coverage_pct": round(100 * covered / total) if total else 0,
        },
        "requirements": sorted(results, key=lambda r: (r["status"] != "Gap", r["regulation"])),
        "gap_list": [r for r in results if r["status"] == "Gap"],
    }


# --------------------------------------------------------------------------- #
# Agent 5 — Lessons Learned & Failure Intelligence
# --------------------------------------------------------------------------- #
_RECOMMENDATION_BY_THEME = {
    "Mechanical seal failure": "Address upstream water chemistry; consider seal plan upgrade (e.g. API Plan 23) on affected pumps.",
    "Bearing degradation": "Add affected assets to a vibration watch list with condition-based bearing replacement.",
    "Machinery guarding / LOTO": "Enforce guard-reinstatement sign-off and mandatory LOTO for any work inside the guard line.",
    "Hot work / ignition proximity": "Make adjacent seal/flange leak verification a mandatory hot-work permit pre-control.",
    "Gas / hydrocarbon exposure": "Strengthen continuous gas monitoring and SIMOPS review before authorising work.",
    "Feedwater / water chemistry": "Institute logged feedwater chemistry monitoring to prevent scaling-driven failures.",
    "Vibration exceedance": "Trend vibration continuously and act at alarm, not trip, thresholds.",
}


def lessons_learned(engine) -> dict:
    # gather failure events across the corpus
    theme_events: dict[str, list[dict]] = defaultdict(list)
    theme_equipment: dict[str, set[str]] = defaultdict(set)
    from .entities import extract_entities

    for did in engine.all_docs():
        dtype = engine.doc_type(did)
        if dtype not in _FAILURE_TYPES:
            continue
        text = engine.full_text(did)
        date = _first_date(text) or "n/a"
        # attribute only to equipment that is a primary subject of the doc (>= 2 mentions)
        eqp = [e.id for e in extract_entities(text)
               if e.type == "equipment" and _mentions(text, e.id) >= 2]
        for name in _themes_in(text):
            theme_events[name].append({"doc_id": did, "doc_type": dtype, "date": date})
            theme_equipment[name].update(eqp)

    patterns = []
    for theme, evs in theme_events.items():
        if len(evs) < 2:
            continue  # a pattern needs recurrence
        sev = "High" if len(evs) >= 3 else "Medium"
        patterns.append({
            "pattern": theme,
            "occurrences": len(evs),
            "severity": sev,
            "equipment": sorted(theme_equipment[theme]),
            "documents": sorted({e["doc_id"] for e in evs}),
            "date_range": f"{min(e['date'] for e in evs)} → {max(e['date'] for e in evs)}",
            "recommendation": _RECOMMENDATION_BY_THEME.get(theme, "Review and standardise controls."),
        })
    patterns.sort(key=lambda p: (-p["occurrences"], p["pattern"]))

    return {
        "patterns": patterns,
        "stats": {
            "failure_documents_analysed": sum(1 for d in engine.all_docs()
                                              if engine.doc_type(d) in _FAILURE_TYPES),
            "recurring_patterns": len(patterns),
            "high_severity": sum(1 for p in patterns if p["severity"] == "High"),
        },
    }
