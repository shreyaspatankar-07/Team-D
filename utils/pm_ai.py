"""
utils/pm_ai.py — AI-based Preventive Maintenance Recommendations (Module 7).

Uses existing ML outputs (health score, failure probability, sensor thresholds)
from utils/health.py and pm_schedule data from utils/db.py.
No new model is trained; the recommendations are rule-based on the existing
predictive outputs already computed for the Machine Explorer.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from utils.health import (
    compute_health_score,
    compute_failure_probability,
    get_sensor_status,
)


# ── Risk tier thresholds ───────────────────────────────────────────────────────

_RISK_CRITICAL  = 70   # failure_probability >= this → Critical risk
_RISK_HIGH      = 45   # failure_probability >= this → High risk
_RISK_MEDIUM    = 25   # failure_probability >= this → Medium risk


def _risk_tier(failure_prob: int) -> tuple[str, str]:
    """Return (tier_label, color) for a given failure probability."""
    if failure_prob >= _RISK_CRITICAL:
        return "Critical", "#ef4444"
    elif failure_prob >= _RISK_HIGH:
        return "High", "#f59e0b"
    elif failure_prob >= _RISK_MEDIUM:
        return "Medium", "#3b82f6"
    else:
        return "Low", "#22c55e"


def _days_until(date_str: str) -> int | None:
    """Return days until a date string (YYYY-MM-DD), or None if unparseable."""
    try:
        target = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return (target - datetime.now().date()).days
    except (ValueError, TypeError):
        return None


# ── Per-machine recommendation ─────────────────────────────────────────────────

def generate_machine_recommendation(
    machine: dict | pd.Series,
    schedules: list[dict],
) -> dict:
    """
    Generate a structured AI recommendation for one machine.

    Args:
        machine:   A row from the AI4I dataset (dict or Series).
        schedules: All pm_schedule dicts from db.fetch_all_pm_schedules().

    Returns a dict with keys:
        product_id, machine_type, health_score, health_category,
        failure_probability, risk_tier, risk_color,
        primary_action, reasons, suggested_tasks, urgency
    """
    product_id   = str(machine.get("Product ID", ""))
    machine_type = str(machine.get("Type", ""))

    score, category, color = compute_health_score(machine)
    fp = compute_failure_probability(machine, score)
    tier, risk_color = _risk_tier(fp)

    # Sensor anomalies
    sensors = [
        ("Air temperature [K]",     machine.get("Air temperature [K]",     0)),
        ("Process temperature [K]", machine.get("Process temperature [K]", 0)),
        ("Rotational speed [rpm]",  machine.get("Rotational speed [rpm]",  0)),
        ("Torque [Nm]",             machine.get("Torque [Nm]",             0)),
        ("Tool wear [min]",         machine.get("Tool wear [min]",         0)),
    ]

    anomalous = []
    for sensor_name, val in sensors:
        status, _ = get_sensor_status(sensor_name, float(val))
        if status in ("Warning", "Critical", "Elevated", "Low"):
            anomalous.append((sensor_name, status, val))

    has_failed   = int(machine.get("Machine failure", 0)) == 1
    tool_wear    = float(machine.get("Tool wear [min]", 0))
    active_modes = [
        k for k in ("TWF", "HDF", "PWF", "OSF", "RNF")
        if int(machine.get(k, 0)) == 1
    ]

    # Existing schedules for this machine
    machine_schedules = [s for s in schedules if s.get("product_id") == product_id]
    overdue_count  = sum(1 for s in machine_schedules if s.get("status") == "Overdue")
    upcoming_count = sum(1 for s in machine_schedules if s.get("status") == "Upcoming")

    # ── Build reasons ──
    reasons: list[str] = []
    suggested_tasks: list[str] = []

    if has_failed:
        reasons.append(f"⚠ Machine has FAILED — failure modes: {', '.join(active_modes) or 'Unknown'}")
        suggested_tasks.append("Full Preventive Maintenance")
        suggested_tasks.append("General Inspection")

    if tool_wear > 160:
        reasons.append(f"🔧 Tool wear at {tool_wear:.0f} min (threshold: 220 min) — replacement imminent")
        suggested_tasks.append("Tool Wear Inspection")

    for sensor_name, status, val in anomalous:
        short = sensor_name.split("[")[0].strip()
        reasons.append(f"📊 {short} reading is {status} ({val:.1f})")
        if "temperature" in sensor_name.lower() or "Temperature" in sensor_name:
            if "Cooling System Check" not in suggested_tasks:
                suggested_tasks.append("Cooling System Check")
        if "Torque" in sensor_name or "speed" in sensor_name.lower():
            if "Lubrication Service" not in suggested_tasks:
                suggested_tasks.append("Lubrication Service")

    if overdue_count > 0:
        reasons.append(f"📅 {overdue_count} scheduled maintenance task(s) are overdue")

    if upcoming_count > 0:
        reasons.append(f"📆 {upcoming_count} maintenance task(s) due within the next 7 days")

    if not reasons:
        reasons.append("✅ Machine health is good — continue routine monitoring")
        suggested_tasks.append("General Inspection")

    # Deduplicate suggested tasks while preserving order
    seen: set[str] = set()
    unique_tasks: list[str] = []
    for t in suggested_tasks:
        if t not in seen:
            seen.add(t)
            unique_tasks.append(t)

    # ── Primary action ──
    if has_failed or tier == "Critical":
        primary_action = "Immediate Inspection & Repair Required"
        urgency = "critical"
    elif tier == "High" or overdue_count > 0:
        primary_action = "Schedule Urgent Preventive Maintenance"
        urgency = "high"
    elif tier == "Medium" or upcoming_count > 0:
        primary_action = "Schedule Preventive Maintenance Soon"
        urgency = "medium"
    else:
        primary_action = "Continue Routine Monitoring"
        urgency = "low"

    return {
        "product_id":          product_id,
        "machine_type":        machine_type,
        "health_score":        score,
        "health_category":     category,
        "failure_probability": fp,
        "risk_tier":           tier,
        "risk_color":          risk_color,
        "primary_action":      primary_action,
        "reasons":             reasons,
        "suggested_tasks":     unique_tasks,
        "urgency":             urgency,
    }


# ── Fleet-level recommendations ────────────────────────────────────────────────

def generate_fleet_recommendations(
    df: pd.DataFrame,
    schedules: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Rank all machines and return the top_n requiring the most attention.

    Sorting key: failure_probability DESC, then overdue schedules DESC.
    """
    results: list[dict] = []

    # Build a quick lookup: product_id → overdue count
    overdue_map: dict[str, int] = {}
    for s in schedules:
        if s.get("status") == "Overdue":
            pid = s.get("product_id", "")
            overdue_map[pid] = overdue_map.get(pid, 0) + 1

    # Deduplicate machines: take only the first row per product_id
    seen_pids: set[str] = set()
    for _, row in df.iterrows():
        pid = str(row.get("Product ID", ""))
        if pid in seen_pids:
            continue
        seen_pids.add(pid)

        rec = generate_machine_recommendation(row, schedules)
        rec["overdue_count"] = overdue_map.get(pid, 0)
        results.append(rec)

    # Sort by failure probability descending, overdue count descending
    results.sort(key=lambda r: (r["failure_probability"], r["overdue_count"]), reverse=True)
    return results[:top_n]


# ── Summary stats ──────────────────────────────────────────────────────────────

def fleet_risk_summary(recommendations: list[dict]) -> dict:
    """
    Return count of machines per risk tier from a list of recommendations.
    """
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in recommendations:
        tier = r.get("risk_tier", "Low")
        counts[tier] = counts.get(tier, 0) + 1
    return counts
