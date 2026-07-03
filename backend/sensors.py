"""
Real-time operating conditions — a live sensor feed the Maintenance/RCA agent fuses
with document history.

NOTE: this is a *simulated* SCADA feed (deterministic model that oscillates over time so
the demo shows live values). In production this module is the integration point for a real
plant historian / SCADA / OPC-UA source — the rest of the platform is unchanged.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

# per-asset envelope: metric -> (baseline, amplitude, alarm_limit or None, unit)
# tuned so at-risk assets (e.g. PUMP-204) actually breach alarm, matching their history.
_SPECS = {
    "PUMP-204": [("Vibration", 7.4, 0.6, 7.1, "mm/s RMS"),
                 ("Bearing temp", 84, 3, 90, "degC"),
                 ("Discharge pressure", 41, 0.4, None, "barg")],
    "PUMP-205": [("Vibration", 2.2, 0.3, 7.1, "mm/s RMS"),
                 ("Bearing temp", 52, 2, 90, "degC")],
    "MOTOR-204A": [("Vibration", 2.4, 0.3, 7.1, "mm/s RMS"),
                   ("Winding temp", 74, 4, 120, "degC")],
    "B-301": [("Drum level", 50, 4, None, "%"),
              ("Feedwater conductivity", 6.4, 1.2, 5.0, "uS/cm")],
    "K-101": [("Vibration", 3.1, 0.3, 7.1, "mm/s RMS"),
              ("Lube oil temp", 48, 2, 70, "degC")],
}
_GENERIC = [("Vibration", 2.3, 0.3, 7.1, "mm/s RMS"), ("Bearing temp", 55, 2, 85, "degC")]


def current_readings(equipment_id: str) -> dict:
    eqp = equipment_id.strip().upper()
    specs = _SPECS.get(eqp, _GENERIC)
    now = datetime.now(timezone.utc)
    phase = ((now.second + now.microsecond / 1e6) / 60.0) * 2 * math.pi
    readings = []
    for i, (name, base, amp, alarm, unit) in enumerate(specs):
        val = round(base + amp * math.sin(phase + i * 1.7), 2)
        status = "ALARM" if (alarm is not None and val >= alarm) else "Normal"
        readings.append({"metric": name, "value": val, "unit": unit,
                         "alarm": alarm, "status": status})
    return {
        "equipment": eqp,
        "ts": now.isoformat(timespec="seconds"),
        "readings": readings,
        "alarms": [r["metric"] for r in readings if r["status"] == "ALARM"],
        "simulated": True,
    }
