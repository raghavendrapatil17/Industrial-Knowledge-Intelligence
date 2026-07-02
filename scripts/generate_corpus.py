"""
Generate the demo document corpus for the Industrial Knowledge Intelligence platform.

Design principle — the "GOLDEN THREAD":
    One equipment tag, PUMP-204 (Boiler Feed Water Pump, Unit-3 / Area-7), is
    deliberately planted across a P&ID note, two maintenance work orders (2019 & 2024),
    a near-miss report, an inspection report, a safety procedure, a permit-to-work,
    and a shift log. This proves CROSS-DOCUMENT linking works in the live demo, not just
    single-document retrieval.

Overlapping entities (so the knowledge graph has real relationships, not isolated nodes):
    Equipment : PUMP-204, MOTOR-204A, VALVE-77, B-301 (boiler), K-101 (compressor)
    Location  : Unit-3, Area-7, Battery Limit BL-3
    Personnel : R. Sharma, A. Nair, S. Iyer, P. Menon
    Regulatory: OISD-STD-105, OISD-STD-106, Factory Act Section 21, Factory Act Section 36
    Materials : Turbine Lube Oil ISO VG 46

Documents mix realistic SYNTHETIC plant records with PUBLIC-STYLE regulatory / manual
excerpts (paraphrased so nothing is copied verbatim — all content is original).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "documents"

# Each doc: filename -> (metadata header + body). doc_type drives graph edge semantics.
DOCS: dict[str, str] = {}

DOCS["PID-U3-BFW-note.txt"] = """DOCUMENT TYPE: Engineering Drawing Note (P&ID)
DRAWING NO: PID-U3-BFW-001 Rev C
UNIT: Unit-3  |  AREA: Area-7  |  BATTERY LIMIT: BL-3
TITLE: Boiler Feed Water System — Notes accompanying P&ID
DATE: 2018-11-02

1. Boiler Feed Water Pump PUMP-204 is a horizontal multistage centrifugal pump
   supplying feed water to Boiler B-301. Rated discharge pressure 42 barg,
   rated flow 120 m3/h. Driven by MOTOR-204A (3.3 kV, 250 kW).

2. Discharge line isolation is via VALVE-77 (10", gate). Minimum-flow recirculation
   line returns to the deaerator through orifice FO-204.

3. Mechanical seal is a cartridge single seal, API Plan 11 flush from pump discharge.
   Seal flush temperature not to exceed 80 degC.

4. PUMP-204 shares the common suction header with standby pump PUMP-205. Only one
   pump runs at a time; the other is on auto-standby.

5. All rotating equipment guards to comply with Factory Act Section 21 (fencing of
   machinery). Hot surfaces above 60 degC to be insulated per OISD-STD-106.

Reference documents: O&M Manual OM-CP-04, Safety Procedure SP-CSE-014.
"""

DOCS["WO-2019-0453.txt"] = """DOCUMENT TYPE: Maintenance Work Order
WORK ORDER NO: WO-2019-0453
EQUIPMENT: PUMP-204 (Boiler Feed Water Pump)  |  UNIT: Unit-3  |  AREA: Area-7
PRIORITY: High  |  STATUS: Closed
RAISED: 2019-03-14  |  COMPLETED: 2019-03-17
ASSIGNED TO: R. Sharma (Mechanical Maintenance)
REGULATORY REF: Factory Act Section 21

PROBLEM DESCRIPTION:
PUMP-204 mechanical seal reported leaking during morning shift. Seal flush line
running hot (measured 91 degC, above the 80 degC limit). Discharge pressure fluctuating
between 38-42 barg. Suspected seal face wear and clogged API Plan 11 flush orifice.

WORK PERFORMED:
- Isolated PUMP-204 via VALVE-77, blinded suction and discharge, LOTO applied.
- Replaced cartridge mechanical seal (P/N SEAL-204-CS).
- Cleaned and re-sized Plan 11 flush orifice; verified flush temp 68 degC on restart.
- Aligned pump-to-MOTOR-204A coupling; final rim/face within 0.05 mm.

FINDINGS:
Root cause: flush orifice partially blocked with scale, causing insufficient seal
cooling and premature seal face wear. Recommend water treatment review of feedwater
to Boiler B-301.

FOLLOW-UP: Monitor seal flush temperature weekly. Trend bearing vibration.
"""

DOCS["WO-2024-1187.txt"] = """DOCUMENT TYPE: Maintenance Work Order
WORK ORDER NO: WO-2024-1187
EQUIPMENT: PUMP-204 (Boiler Feed Water Pump)  |  UNIT: Unit-3  |  AREA: Area-7
PRIORITY: High  |  STATUS: Closed
RAISED: 2024-05-30  |  COMPLETED: 2024-06-04
ASSIGNED TO: A. Nair (Reliability Engineering)
REGULATORY REF: OISD-STD-106

PROBLEM DESCRIPTION:
PUMP-204 non-drive-end bearing showing rising vibration. Latest reading 7.8 mm/s RMS
(alarm at 7.1 mm/s, trip at 11.2 mm/s) — up from 3.2 mm/s six months ago. Bearing
housing temperature 84 degC. Correlates with prior seal history under WO-2019-0453.

WORK PERFORMED:
- Replaced both pump bearings (DE and NDE); found NDE bearing with spalling on outer race.
- Re-greased with Turbine Lube Oil ISO VG 46 compatible grease per OEM spec.
- Re-checked coupling alignment to MOTOR-204A. Vibration after job: 2.4 mm/s RMS.

FINDINGS:
Root cause: bearing degradation accelerated by repeated seal-flush overheating events
(see near-miss NM-2023-089 and WO-2019-0453). Reliability flag raised: recurring seal/
bearing distress on PUMP-204 indicates a systemic feedwater-quality issue upstream of
Boiler B-301, not an isolated component failure.

RECOMMENDATION: Add PUMP-204 to the critical-equipment vibration watch list. Review
feedwater chemistry. Consider seal upgrade to API Plan 23 (dedicated cooler).
"""

DOCS["nearmiss-NM-2023-089.txt"] = """DOCUMENT TYPE: Near-Miss Report
REPORT NO: NM-2023-089
LOCATION: Unit-3, Area-7 (near PUMP-204)  |  DATE: 2023-09-21  |  SHIFT: B
REPORTED BY: P. Menon (Shift In-Charge)
REVIEWED BY: S. Iyer (Safety Officer)
REGULATORY REF: OISD-STD-105, Factory Act Section 36

DESCRIPTION OF EVENT:
During routine rounds, operator noticed a fine spray of hot condensate and hydrocarbon
odour near the PUMP-204 mechanical seal area. Seal flush line temperature was reading
95 degC. A maintenance fitter was about to begin unrelated hot work (grinding) on an
adjacent pipe support under permit PTW-2023-2201, approximately 3 metres away.

POTENTIAL CONSEQUENCE:
Leaking hydrocarbon/condensate mist in proximity to a hot-work ignition source. Had the
grinding proceeded, a flash fire was credible. Confined layout of Area-7 near BL-3
would have hampered escape.

IMMEDIATE ACTION:
- Hot work stopped; PTW-2023-2201 suspended.
- PUMP-204 switched to standby PUMP-205; PUMP-204 isolated via VALVE-77.
- Area gas-tested; LEL 4%, ventilation increased.

LESSON LEARNED / RECOMMENDATION:
Permit-to-work risk assessment must explicitly check adjacent equipment seal integrity
before authorising hot work in Area-7. Cross-reference active seal-leak history (PUMP-204
has repeat seal issues per WO-2019-0453). Reinforce simultaneous-operations (SIMOPS) review.
"""

DOCS["insp-INS-2024-0210.txt"] = """DOCUMENT TYPE: Inspection Report
REPORT NO: INS-2024-0210
EQUIPMENT: PUMP-204 & MOTOR-204A  |  UNIT: Unit-3  |  AREA: Area-7
INSPECTION DATE: 2024-02-10  |  INSPECTOR: A. Nair (Reliability Engineering)
METHOD: Vibration analysis, thermography, visual

RESULTS:
- PUMP-204 NDE bearing vibration 6.9 mm/s RMS (approaching 7.1 mm/s alarm). Trend rising.
- Bearing housing thermography: 82 degC (ambient 34 degC). Hot spot at NDE.
- MOTOR-204A winding temperatures normal. Coupling guard intact (Factory Act Section 21 OK).
- Seal flush line: 71 degC, within limit. No active leak at time of inspection.

ASSESSMENT:
Early-stage NDE bearing defect. Not yet at alarm but degrading. Consistent with the
recurring seal/bearing pattern documented in NM-2023-089 and WO-2019-0453.

RECOMMENDATION:
Schedule bearing replacement within 90 days. Raised as WO-2024-1187. Keep PUMP-204 on
watch list. Verify feedwater chemistry to Boiler B-301.
"""

DOCS["SP-CSE-014.txt"] = """DOCUMENT TYPE: Safety Procedure
PROCEDURE NO: SP-CSE-014 Rev 4
TITLE: Confined Space Entry and Hot Work — Unit-3 Boiler Feed Water Area (Area-7)
EFFECTIVE: 2022-06-01  |  OWNER: S. Iyer (Safety Officer)
REGULATORY BASIS: OISD-STD-105, Factory Act Section 36 (confined spaces)

SCOPE:
Applies to confined space entry and hot work in Unit-3, Area-7, including work on or
adjacent to PUMP-204, PUMP-205, VALVE-77 and associated Boiler B-301 feedwater lines.

KEY REQUIREMENTS:
1. A valid Permit-to-Work (PTW) is mandatory. Hot work and confined space entry require
   separate permits and a documented SIMOPS (simultaneous operations) review.
2. Before hot work in Area-7, verify no active seal or flange leaks on nearby rotating
   equipment. Rotating pumps with a history of seal leakage (e.g. PUMP-204, ref
   WO-2019-0453, NM-2023-089) require a positive isolation check.
3. Gas testing: LEL must be below 5% and O2 between 19.5-23.5% before and during entry.
4. Continuous gas monitoring and a standby attendant are required for confined space entry.
5. Machinery guards must be in place per Factory Act Section 21 before restart.

EMERGENCY:
On gas alarm or visible leak, stop all hot work, evacuate Area-7 via BL-3 muster point,
and notify the Shift In-Charge and Safety Officer immediately.
"""

DOCS["PTW-2024-3320.txt"] = """DOCUMENT TYPE: Permit to Work
PERMIT NO: PTW-2024-3320
TYPE: Hot Work  |  LOCATION: Unit-3, Area-7 (near PUMP-204 discharge)
VALID: 2024-06-04 08:00 to 2024-06-04 17:00
ISSUED BY: S. Iyer (Safety Officer)  |  ACCEPTED BY: R. Sharma (Mechanical)
GOVERNING PROCEDURE: SP-CSE-014  |  REGULATORY REF: OISD-STD-105

WORK: Weld repair of pipe support bracket near PUMP-204 discharge line, following
bearing replacement under WO-2024-1187.

PRECONTROLS (verified before issue):
- PUMP-204 confirmed on standby (PUMP-205 running); PUMP-204 isolated via VALVE-77. YES
- No active seal leak on PUMP-204 (checked against NM-2023-089 history). YES
- Gas test LEL 0%, O2 20.9%. YES
- Fire watch posted; extinguisher and hose available. YES
- SIMOPS review completed — no conflicting permits in Area-7. YES

NOTES: This permit references lessons from NM-2023-089 — adjacent seal integrity was
explicitly verified before authorising hot work.
"""

DOCS["shiftlog-2024-06-15.txt"] = """DOCUMENT TYPE: Shift Log
DATE: 2024-06-15  |  SHIFT: A (06:00-14:00)  |  UNIT: Unit-3
SHIFT IN-CHARGE: P. Menon

06:20 - Took over shift. Boiler B-301 load 78%. PUMP-204 running, discharge 41 barg,
        vibration 2.5 mm/s (healthy after WO-2024-1187 bearing job). PUMP-205 standby.
08:45 - Routine round Area-7. VALVE-77 no passing. Seal flush 66 degC. All normal.
11:10 - Feedwater conductivity alarm on B-301 loop. Advised water treatment. Logged as
        possible contributor to recurring PUMP-204 seal/bearing history (per A. Nair note).
13:30 - Handover prepared. No permits active in Area-7. PUMP-204 stable.
"""

DOCS["incident-2019-report.txt"] = """DOCUMENT TYPE: Incident Investigation Report
REPORT NO: INC-2019-014
DATE OF EVENT: 2019-01-08  |  UNIT: Unit-3, Area-7
INVESTIGATION LEAD: S. Iyer (Safety Officer)
REGULATORY REF: Factory Act Section 21, OISD-STD-106

SUMMARY:
A maintenance technician sustained a minor hand injury while attempting to check the
coupling of MOTOR-204A driving PUMP-204. The coupling guard had been removed during an
earlier job and not reinstated, and the pump auto-started on level control while the
technician's hand was near the coupling.

ROOT CAUSES:
1. Machinery guard (Factory Act Section 21) not reinstated after previous maintenance.
2. PUMP-204 was on auto-start (level control) but not electrically isolated; LOTO not
   applied for what was assumed to be a "quick check".
3. No permit raised for the task.

CORRECTIVE ACTIONS:
- Mandatory guard-reinstatement sign-off added to all rotating-equipment work orders.
- LOTO required for ANY work inside the guard line, including inspection.
- Reinforced in Safety Procedure SP-CSE-014.

This incident is a key lesson-learned reference for all work on PUMP-204 / MOTOR-204A.
"""

DOCS["boiler-B301-procedure.txt"] = """DOCUMENT TYPE: Operating Procedure
PROCEDURE NO: OP-B301-02 Rev 2
TITLE: Boiler B-301 Startup and Feedwater Control — Unit-3
OWNER: Operations, Unit-3

FEEDWATER SUPPLY:
Boiler B-301 feed water is supplied by boiler feed water pump PUMP-204 (duty) with
PUMP-205 on standby. Maintain drum level 50% +/- 10%. Minimum discharge pressure 40 barg.

STARTUP NOTES:
1. Confirm PUMP-204 healthy — check latest vibration and seal-flush temperature. Do not
   start B-301 firing if PUMP-204 is under a maintenance hold (see current work orders).
2. Feedwater chemistry (conductivity, hardness) must be within limits. Poor feedwater
   quality has historically driven seal scaling on PUMP-204 (ref WO-2019-0453, WO-2024-1187).
3. On loss of PUMP-204, feed auto-transfers to PUMP-205; investigate PUMP-204 trip cause
   before returning to service.

SAFETY:
All work near B-301 feedwater pumps in Area-7 follows SP-CSE-014 and requires a permit.
"""

DOCS["OM-CP-04-centrifugal-pump.txt"] = """DOCUMENT TYPE: O&M Manual (Equipment)
MANUAL NO: OM-CP-04
TITLE: Horizontal Multistage Centrifugal Pump — Operation & Maintenance (paraphrased excerpt)
APPLIES TO: PUMP-204, PUMP-205 class boiler feed water pumps

MECHANICAL SEAL:
The pump is fitted with a cartridge mechanical seal using an API Plan 11 flush taken from
pump discharge. Seal flush temperature should remain below 80 degC. A rising flush
temperature indicates orifice fouling or inadequate cooling and can cause rapid seal-face
wear. If flush temperature exceeds the limit, investigate before continued operation.

BEARINGS:
Anti-friction bearings at drive and non-drive ends. Normal vibration below 4.5 mm/s RMS;
alarm typically set around 7.1 mm/s and trip around 11.2 mm/s. Rising non-drive-end
vibration with elevated housing temperature indicates bearing degradation. Lubricate with
manufacturer-approved grease compatible with Turbine Lube Oil ISO VG 46 systems.

COMMON FAILURE MODES:
- Seal failure from flush overheating (most common; often water-chemistry driven).
- Bearing spalling from contamination or repeated thermal cycling.
- Coupling misalignment causing elevated vibration.

MAINTENANCE:
Positively isolate and apply LOTO before any intrusive work. Reinstate all guards before
restart in accordance with statutory machinery-fencing requirements.
"""

DOCS["MSDS-turbine-lube-oil.txt"] = """DOCUMENT TYPE: Material Safety Data Sheet (SDS)
PRODUCT: Turbine Lube Oil ISO VG 46
SECTION 1 — IDENTIFICATION: Mineral-oil-based turbine/circulating oil. Used in rotating
equipment lubrication systems including boiler feed water pump sets (e.g. PUMP-204 area).

SECTION 2 — HAZARDS: Combustible liquid. Flash point > 200 degC (open cup). Mist or spray
onto hot surfaces above the flash point can ignite. Prolonged skin contact may cause irritation.

SECTION 4 — FIRST AID: Skin — wash with soap and water. Eyes — rinse 15 minutes. Inhalation
of mist — move to fresh air.

SECTION 5 — FIRE FIGHTING: Use dry chemical, CO2, or foam. Do NOT use water jet (spreads fire).

SECTION 7 — HANDLING & STORAGE: Keep away from ignition sources and hot surfaces. Relevant to
hot-work permits in Area-7 where lube systems and hot piping coexist (see SP-CSE-014).

SECTION 8 — EXPOSURE CONTROLS: Oil mist exposure limit 5 mg/m3 (8-hr TWA). Use gloves and
goggles when handling.
"""

DOCS["OISD-STD-105-excerpt.txt"] = """DOCUMENT TYPE: Regulatory Guideline (paraphrased public-style excerpt)
STANDARD: OISD-STD-105 — Work Permit System (paraphrased summary for demo use)

PURPOSE: Establishes a work permit system to control non-routine and hazardous work in
hydrocarbon-processing facilities, ensuring hazards are identified and controlled before work begins.

KEY PROVISIONS (summarised):
1. A written work permit is required for hot work, confined space entry, working at height,
   excavation, and other hazardous activities.
2. Hot work permits require verification that the area is free of flammable gas/vapour and
   that no leaking equipment is nearby. Continuous or periodic gas testing is mandated based
   on risk.
3. Simultaneous operations (SIMOPS) must be assessed; conflicting permits in the same area
   must be reconciled before issue.
4. Confined space entry requires atmosphere testing (LEL, oxygen, toxic gases), a standby
   person, and rescue arrangements.
5. Permits must define validity period, precautions, isolation, and acceptance by the
   performing authority.

APPLICATION: Governs permits such as PTW-2024-3320 for hot work in Unit-3 Area-7, and is the
regulatory basis for Safety Procedure SP-CSE-014.
"""

DOCS["Factory-Act-excerpts.txt"] = """DOCUMENT TYPE: Regulatory Reference (paraphrased public-style excerpt)
ACT: The Factories Act, 1948 (India) — paraphrased summary of selected sections for demo use

SECTION 21 — FENCING OF MACHINERY (summary):
Every dangerous part of machinery, including moving parts of prime movers, transmission
machinery, and every part that is a moving part of any machine, must be securely fenced/guarded.
Guards must be maintained and kept in position while the machinery is in motion. Relevant to
all rotating equipment such as PUMP-204 / MOTOR-204A couplings.

SECTION 36 — PRECAUTIONS AGAINST DANGEROUS FUMES, GASES ETC. (summary):
No person shall enter any confined space in which dangerous fumes are likely to be present
unless it is certified safe, or unless wearing suitable breathing apparatus with a lifeline
and a person keeping watch outside. Governs confined space entry procedures such as SP-CSE-014.

SECTION 7A — GENERAL DUTIES OF OCCUPIER (summary):
Ensure, so far as reasonably practicable, the health, safety and welfare of all workers,
including safe systems of work, safe plant and machinery, and adequate information/training.
"""

DOCS["compressor-K101-WO-2024-0902.txt"] = """DOCUMENT TYPE: Maintenance Work Order
WORK ORDER NO: WO-2024-0902
EQUIPMENT: K-101 (Recycle Gas Compressor)  |  UNIT: Unit-5  |  AREA: Area-2
PRIORITY: Medium  |  STATUS: Closed
RAISED: 2024-04-18  |  ASSIGNED TO: R. Sharma (Mechanical Maintenance)
REGULATORY REF: OISD-STD-106

PROBLEM: K-101 lube oil cooler fouling; oil supply temperature high at 62 degC.
WORK PERFORMED: Cleaned cooler tube bundle; topped up Turbine Lube Oil ISO VG 46.
Post-job oil temp 48 degC. Vibration normal.
FINDINGS: Routine fouling. Unrelated to Unit-3 boiler feed water issues. Included here to
show the plant runs multiple asset families — K-101 shares personnel (R. Sharma) and a
lubricant (ISO VG 46) with the PUMP-204 records but is otherwise a separate cluster.
"""

# --- structured (spreadsheet) + unstructured (email) formats, same golden thread ---
DOCS["equipment-register.csv"] = (
    "Equipment Tag,Description,Unit,Area,Criticality,Last Vibration mm/s,Regulatory Ref\n"
    "PUMP-204,Boiler Feed Water Pump,Unit-3,Area-7,Critical,7.8,OISD-STD-106\n"
    "PUMP-205,Boiler Feed Water Pump (standby),Unit-3,Area-7,Critical,2.1,OISD-STD-106\n"
    "MOTOR-204A,3.3kV motor driving PUMP-204,Unit-3,Area-7,Critical,2.4,Factory Act Section 21\n"
    "VALVE-77,Discharge isolation valve for PUMP-204,Unit-3,Area-7,High,,\n"
    "B-301,Boiler fed by PUMP-204,Unit-3,Area-7,Critical,,OISD-STD-106\n"
    "K-101,Recycle Gas Compressor,Unit-5,Area-2,Critical,3.1,OISD-STD-106\n"
)

DOCS["email-2024-06-10-feedwater.eml"] = (
    "From: A. Nair <a.nair@plant.example>\n"
    "To: P. Menon <p.menon@plant.example>\n"
    "Subject: PUMP-204 recurring seal/bearing issue - feedwater chemistry\n"
    "Date: Mon, 10 Jun 2024 09:15:00 +0530\n"
    "Content-Type: text/plain; charset=utf-8\n\n"
    "P. Menon,\n\n"
    "Following the bearing replacement under WO-2024-1187, I reviewed PUMP-204's history. "
    "The recurring seal and bearing distress traces back to feedwater chemistry on Boiler "
    "B-301 - scale is fouling the API Plan 11 flush orifice. This matches the 2019 seal "
    "failure (WO-2019-0453) and near-miss NM-2023-089.\n\n"
    "Please log feedwater conductivity every shift and flag excursions. We should also "
    "verify OISD-STD-106 insulation on the hot lines in Area-7.\n\n"
    "Regards,\nA. Nair\nReliability Engineering\n"
)


def _write_xlsx(path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vibration Log"
    ws.append(["Date", "Equipment", "Vibration mm/s RMS", "Bearing Temp degC", "Inspector", "Notes"])
    for row in [
        ["2024-02-10", "PUMP-204", 6.9, 82, "A. Nair", "NDE bearing trending up; raised WO-2024-1187"],
        ["2024-05-30", "PUMP-204", 2.4, 55, "A. Nair", "After bearing replacement (WO-2024-1187)"],
        ["2024-06-15", "PUMP-204", 2.5, 54, "P. Menon", "Healthy post-repair; Boiler B-301 stable"],
        ["2024-04-18", "K-101", 3.1, 48, "R. Sharma", "Recycle gas compressor routine check"],
    ]:
        ws.append(row)
    wb.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in DOCS.items():
        (OUT / name).write_text(body, encoding="utf-8")
    _write_xlsx(OUT / "inspection-vibration-log.xlsx")
    print(f"Wrote {len(DOCS) + 1} documents to {OUT} (incl. .csv, .eml, .xlsx)")
    # Report golden-thread coverage
    thread = "PUMP-204"
    hits = [n for n, b in DOCS.items() if thread in b]
    print(f"Golden thread '{thread}' appears in {len(hits)} documents:")
    for h in hits:
        print("  -", h)


if __name__ == "__main__":
    main()
