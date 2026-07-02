"""
Cross-agent analytics: the executive Operations Overview and the Asset-360 drill-down.
Both aggregate over the SAME knowledge graph the agents use.
"""
from __future__ import annotations

from collections import defaultdict

from .agents import maintenance_rca, compliance_report, lessons_learned


def operations_overview(engine) -> dict:
    """Plant-wide KPI snapshot + proactive alerts, assembled from every agent."""
    docs = engine.all_docs()
    doc_types: dict[str, int] = defaultdict(int)
    for d in docs:
        doc_types[engine.doc_type(d)] += 1

    entity_types: dict[str, int] = defaultdict(int)
    for n in engine.graph.nodes:
        if engine.graph.nodes[n].get("kind") != "document":
            entity_types[engine.graph.nodes[n].get("type", "entity")] += 1

    # asset health across all equipment
    assets = []
    for eq in engine.equipment_nodes():
        r = maintenance_rca(engine, eq)
        assets.append({
            "equipment": eq, "health_label": r["health_label"],
            "health_score": r["health_score"], "events": r["n_failure_events"],
            "recurring": len(r["recurring_themes"]),
        })
    assets.sort(key=lambda a: a["health_score"])
    at_risk = [a for a in assets if a["health_score"] < 40]

    comp = compliance_report(engine)
    lessons = lessons_learned(engine)

    # proactive alerts — the "push warnings before conditions recur" idea from the brief
    alerts = []
    for a in at_risk:
        alerts.append({
            "severity": "High", "type": "Asset health",
            "message": f"{a['equipment']} is {a['health_label']} "
                       f"({a['events']} failure events, {a['recurring']} recurring patterns).",
            "action": "rca", "ref": a["equipment"],
        })
    for g in comp["gap_list"]:
        alerts.append({
            "severity": "Medium", "type": "Compliance gap",
            "message": f"{g['regulation']}: {g['requirement']}",
            "action": "compliance", "ref": g["id"],
        })
    for p in lessons["patterns"]:
        if p["severity"] == "High":
            alerts.append({
                "severity": "High", "type": "Recurring failure",
                "message": f"{p['pattern']} — {p['occurrences']}× across {', '.join(p['equipment']) or 'assets'}.",
                "action": "lessons", "ref": p["pattern"],
            })

    graph_density = round(
        engine.graph.number_of_edges() / max(engine.graph.number_of_nodes(), 1), 2)

    return {
        "kpis": {
            "documents": len(docs),
            "document_types": len(doc_types),
            "entities": sum(entity_types.values()),
            "graph_nodes": engine.graph.number_of_nodes(),
            "graph_edges": engine.graph.number_of_edges(),
            "graph_density": graph_density,
            "assets_tracked": len(assets),
            "assets_at_risk": len(at_risk),
            "compliance_coverage": comp["summary"]["coverage_pct"],
            "compliance_gaps": comp["summary"]["gaps"],
            "recurring_patterns": lessons["stats"]["recurring_patterns"],
            "open_alerts": len(alerts),
        },
        "assets": assets,
        "alerts": sorted(alerts, key=lambda a: 0 if a["severity"] == "High" else 1),
        "document_types": dict(doc_types),
        "entity_types": dict(entity_types),
    }


def entity_profile(engine, entity_id: str) -> dict:
    """Asset-360: everything the graph knows about one entity."""
    G = engine.graph
    eid = entity_id.strip()
    if not G.has_node(eid):
        # try uppercase tag form
        eid = eid.upper()
    if not G.has_node(eid):
        return {"error": f"'{entity_id}' not found in the knowledge graph."}

    node = G.nodes[eid]
    kind = node.get("kind", "entity")
    etype = node.get("type", "entity")

    linked_docs, connected = [], defaultdict(list)
    for nb in G.neighbors(eid):
        nd = G.nodes[nb]
        rel = G.edges[eid, nb].get("rel", "")
        if nd.get("kind") == "document":
            linked_docs.append({"doc_id": nb, "doc_type": nd.get("doc_type", ""), "rel": rel})
        else:
            connected[nd.get("type", "entity")].append(nb)

    profile = {
        "id": eid, "type": etype, "kind": kind,
        "linked_documents": sorted(linked_docs, key=lambda d: d["doc_id"]),
        "connected_entities": {k: sorted(v) for k, v in connected.items()},
        "degree": G.degree(eid),
    }
    # equipment gets a health snapshot
    if etype == "equipment":
        r = maintenance_rca(engine, eid)
        profile["health"] = {
            "label": r["health_label"], "score": r["health_score"],
            "events": r["n_failure_events"], "recurring_themes": r["recurring_themes"],
        }
    return profile
