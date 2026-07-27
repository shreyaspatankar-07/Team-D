"""
utils/timeline.py — Dynamic maintenance timeline and recent events generation.

Generates realistic, context-aware maintenance schedules and event logs
based on current machine sensor values and health status.
"""

from datetime import datetime, timedelta
import random


# ── Maintenance Timeline ──────────────────────────────────────────────────────

def generate_maintenance_timeline(machine, health_score: int, health_category: str) -> list:
    """
    Generate a prioritized maintenance timeline based on machine state.

    Returns a list of dicts:
      { event, priority ('critical'|'warning'|'normal'), due, detail, icon }
    """
    timeline = []
    now = datetime.now()

    tool_wear = machine["Tool wear [min]"]
    air_temp  = machine["Air temperature [K]"]
    proc_temp = machine["Process temperature [K]"]
    rpm       = machine["Rotational speed [rpm]"]
    torque    = machine["Torque [Nm]"]
    has_failed = int(machine.get("Machine failure", 0)) == 1

    # ── Tool Replacement / Check ──
    if has_failed or tool_wear > 220:
        timeline.append({
            "event":    "Emergency Tool Replacement",
            "priority": "critical",
            "due":      "Immediate",
            "detail":   f"Tool wear at {tool_wear:.0f} min — exceeded safe operating limit (220 min).",
            "color":    "#ef4444",
        })
    elif tool_wear > 160:
        hours_remaining = max(1, round((220 - tool_wear) * 0.12))
        timeline.append({
            "event":    "Scheduled Tool Replacement",
            "priority": "warning",
            "due":      f"Within {hours_remaining}h",
            "detail":   f"Tool wear at {tool_wear:.0f} min — approaching replacement threshold.",
            "color":    "#f59e0b",
        })
    else:
        remaining_pct = round((220 - tool_wear) / 220 * 100)
        hours_remaining = max(4, round((200 - tool_wear) * 0.15))
        timeline.append({
            "event":    "Tool Inspection",
            "priority": "normal",
            "due":      f"In {hours_remaining}h",
            "detail":   f"Tool wear at {tool_wear:.0f} min — {remaining_pct}% life remaining.",
            "color":    "#22c55e",
        })

    # ── Cooling System ──
    temp_diff = proc_temp - air_temp
    if temp_diff > 12 or proc_temp > 314:
        timeline.append({
            "event":    "Cooling System Inspection",
            "priority": "warning" if not has_failed else "critical",
            "due":      "Next shift" if not has_failed else "Immediate",
            "detail":   (
                f"Temperature differential {temp_diff:.1f} K exceeds normal range (\u226410 K). "
                f"Check coolant flow and heat exchanger efficiency."
            ),
            "color":    "#f59e0b" if not has_failed else "#ef4444",
        })
    else:
        timeline.append({
            "event":    "Cooling System Check",
            "priority": "normal",
            "due":      "Weekly",
            "detail":   f"Temp differential {temp_diff:.1f} K — within normal range. Routine verification.",
            "color":    "#22c55e",
        })

    # ── Lubrication ──
    if rpm > 1800 or torque > 55:
        timeline.append({
            "event":    "Lubrication Service",
            "priority": "warning",
            "due":      "Within 24h",
            "detail":   (
                f"High-load operation detected (RPM: {rpm:.0f}, Torque: {torque:.1f} Nm). "
                "Increased lubrication demand."
            ),
            "color":    "#f59e0b",
        })
    else:
        timeline.append({
            "event":    "Lubrication Service",
            "priority": "normal",
            "due":      "In 72h",
            "detail":   f"Operating within normal load range. Routine lubrication schedule.",
            "color":    "#22c55e",
        })

    # ── Full Inspection ──
    if has_failed or health_category == "Critical":
        timeline.append({
            "event":    "Emergency Full Inspection",
            "priority": "critical",
            "due":      "Immediate",
            "detail":   f"Health score {health_score}/100 — full mechanical inspection required.",
            "color":    "#ef4444",
        })
    elif health_category == "Warning":
        timeline.append({
            "event":    "Preventive Inspection",
            "priority": "warning",
            "due":      "Today",
            "detail":   f"Health score {health_score}/100 — preventive inspection recommended.",
            "color":    "#f59e0b",
        })
    else:
        next_insp_h = max(8, round((health_score - 60) * 0.4))
        timeline.append({
            "event":    "Routine Inspection",
            "priority": "normal",
            "due":      f"In {next_insp_h}h",
            "detail":   f"Health score {health_score}/100 — standard preventive maintenance.",
            "color":    "#22c55e",
        })

    # ── Vibration Analysis (if high RPM) ──
    if rpm > 2000:
        timeline.append({
            "event":    "Vibration Analysis",
            "priority": "warning",
            "due":      "Within 48h",
            "detail":   f"Rotational speed {rpm:.0f} RPM — above nominal range. Recommend vibration signature check.",
            "color":    "#f59e0b",
        })

    return timeline


# ── Recent Events ─────────────────────────────────────────────────────────────

def generate_recent_events(machine, health_score: int, health_category: str) -> list:
    """
    Generate a realistic sequence of recent machine events.

    Returns a list of dicts:
      { time_label, event, type ('info'|'warning'|'critical'|'success'), icon }
    """
    now = datetime.now()
    events = []

    tool_wear = machine["Tool wear [min]"]
    air_temp  = machine["Air temperature [K]"]
    proc_temp = machine["Process temperature [K]"]
    rpm       = machine["Rotational speed [rpm]"]
    torque    = machine["Torque [Nm]"]
    has_failed = int(machine.get("Machine failure", 0)) == 1
    machine_id = machine.get("Product ID", "Unknown")

    def _ago(minutes: int) -> str:
        t = now - timedelta(minutes=minutes)
        return t.strftime("%H:%M")

    # Most recent: current prediction update
    events.append({
        "time":  _ago(0),
        "event": f"Prediction updated — Health: {health_score}/100 ({health_category})",
        "type":  "critical" if has_failed else ("warning" if health_category == "Warning" else "success"),
        "icon":  "[CRITICAL]" if has_failed else ("[WARN]" if health_category == "Warning" else "[OK]"),
    })

    # Temperature event
    temp_diff = proc_temp - air_temp
    if temp_diff > 12:
        events.append({
            "time":  _ago(random.randint(5, 15)),
            "event": f"Thermal alert — Process temp {proc_temp:.1f} K (\u0394T {temp_diff:.1f} K)",
            "type":  "warning",
            "icon":  "[TEMP]",
        })
    else:
        events.append({
            "time":  _ago(random.randint(8, 20)),
            "event": f"Temperature nominal — Air {air_temp:.1f} K / Process {proc_temp:.1f} K",
            "type":  "info",
            "icon":  "[TEMP]",
        })

    # Tool wear event
    if tool_wear > 200:
        events.append({
            "time":  _ago(random.randint(20, 40)),
            "event": f"Tool wear threshold alert — {tool_wear:.0f} min (critical range)",
            "type":  "critical",
            "icon":  "[ALERT]",
        })
    elif tool_wear > 130:
        events.append({
            "time":  _ago(random.randint(30, 60)),
            "event": f"Tool wear advisory — {tool_wear:.0f} min (approaching limit)",
            "type":  "warning",
            "icon":  "[WEAR]",
        })
    else:
        events.append({
            "time":  _ago(random.randint(40, 90)),
            "event": f"Tool wear check — {tool_wear:.0f} min (normal operating range)",
            "type":  "info",
            "icon":  "[WEAR]",
        })

    # Failure or health event
    if has_failed:
        failure_modes = []
        mode_map = {
            "TWF": "Tool Wear Failure",
            "HDF": "Heat Dissipation Failure",
            "PWF": "Power Failure",
            "OSF": "Overstrain Failure",
            "RNF": "Random Failure",
        }
        for col, label in mode_map.items():
            if machine.get(col, 0) == 1:
                failure_modes.append(label)
        mode_str = ", ".join(failure_modes) if failure_modes else "Unknown"
        events.append({
            "time":  _ago(random.randint(45, 90)),
            "event": f"Failure detected — {mode_str}",
            "type":  "critical",
            "icon":  "[FAIL]",
        })
    else:
        events.append({
            "time":  _ago(random.randint(60, 120)),
            "event": f"Health score computed — {health_score}/100",
            "type":  "success",
            "icon":  "[OK]",
        })

    # Lubrication event
    events.append({
        "time":  _ago(random.randint(90, 180)),
        "event": "Lubrication check completed — within spec",
        "type":  "info",
        "icon":  "[LUBE]",
    })

    # Inspection event
    events.append({
        "time":  _ago(random.randint(200, 360)),
        "event": f"Routine inspection logged for {machine_id}",
        "type":  "success",
        "icon":  "[LOG]",
    })

    # RPM event
    if rpm > 2000:
        events.append({
            "time":  _ago(random.randint(300, 500)),
            "event": f"High RPM operation — {rpm:.0f} rpm (monitor vibration)",
            "type":  "warning",
            "icon":  "[RPM]",
        })

    # Sort by time (most recent first — they already are, but just in case)
    return events
