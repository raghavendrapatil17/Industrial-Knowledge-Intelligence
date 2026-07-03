"""
External industry failure-intelligence references.

The Lessons Learned engine cross-references the plant's *internal* recurring patterns
against *known industry* failure modes, so an internal pattern can be matched to a
recognised, documented failure mode with an industry-standard control.

NOTE: this is a small curated reference set (paraphrased from public industry knowledge —
API / OISD / CSB-style learnings). It is the integration point for live external incident
databases; the matching logic is identical whether the source is bundled or a live feed.
"""
from __future__ import annotations

# theme (matches agents._THEMES keys) -> known industry failure mode reference
_REFERENCES = {
    "Mechanical seal failure": {
        "failure_mode": "Centrifugal pump mechanical-seal failure from flush-plan fouling",
        "industry_ref": "API 682 seal systems; public refinery pump-seal fire case learnings",
        "prevalence": "One of the most common rotating-equipment failure modes in hydrocarbon service",
        "standard_control": "Upgrade seal flush plan (e.g. API Plan 23 with dedicated cooler) and control feedwater chemistry",
    },
    "Bearing degradation": {
        "failure_mode": "Rolling-element bearing spalling from contamination / thermal cycling",
        "industry_ref": "ISO 10816 / ISO 20816 vibration severity guidance",
        "prevalence": "Leading cause of unplanned pump/motor outages industry-wide",
        "standard_control": "Condition-based replacement on vibration trend; verify lubrication and alignment",
    },
    "Hot work / ignition proximity": {
        "failure_mode": "Flash fire from hot work near a hydrocarbon/seal leak",
        "industry_ref": "OISD-STD-105 work-permit system; public incident inquiries into permit failures",
        "prevalence": "A repeat contributor to serious industrial incidents",
        "standard_control": "Mandatory adjacent-equipment leak check + SIMOPS review before any hot-work permit",
    },
    "Gas / hydrocarbon exposure": {
        "failure_mode": "Confined-space / gas accumulation leading to fire or asphyxiation",
        "industry_ref": "Factory Act Sec. 36; public gas-release inquiry learnings",
        "prevalence": "High-severity, recurring across heavy industry",
        "standard_control": "Continuous gas monitoring, atmosphere testing and standby attendant",
    },
    "Machinery guard failure": {
        "failure_mode": "Contact injury from an unguarded/unre-instated rotating part",
        "industry_ref": "Factory Act Sec. 21 (fencing of machinery)",
        "prevalence": "Common statutory non-compliance finding",
        "standard_control": "Guard-reinstatement sign-off + LOTO for any work inside the guard line",
    },
    "Feedwater / water chemistry": {
        "failure_mode": "Scale-driven component distress from poor boiler feedwater chemistry",
        "industry_ref": "Boiler water-treatment good practice (e.g. IS / ASME guidance)",
        "prevalence": "Frequent root cause behind repeat seal/tube failures",
        "standard_control": "Logged conductivity/hardness monitoring with excursion alerts",
    },
    "Vibration exceedance": {
        "failure_mode": "Progressive rotating-equipment damage from sustained high vibration",
        "industry_ref": "ISO 20816 vibration severity zones",
        "prevalence": "Universal early-warning indicator",
        "standard_control": "Act at ALARM (not TRIP) thresholds; trend continuously",
    },
}


def match(theme: str) -> dict | None:
    return _REFERENCES.get(theme)
