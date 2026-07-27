"""
utils/health.py — Health scoring, sensor status badges, and suggested AI questions.

Provides:
  - compute_health_score()   → (int score, str category, str color_hex)
  - compute_failure_probability() → int
  - get_sensor_status()      → (str label, str color_hex)
  - get_suggested_questions() → list[str]
  - health_bar_html()        → str (inline HTML)
  - sensor_badge_html()      → str (inline HTML)
"""

import pandas as pd

# ── Sensor Operating Thresholds ───────────────────────────────────────────────

SENSOR_THRESHOLDS = {
    "Air temperature [K]": {
        "normal_max": 309.0,
        "warning_max": 312.0,
        "display_min": 290,
        "display_max": 320,
        "unit": "K",
    },
    "Process temperature [K]": {
        "normal_max": 314.0,
        "warning_max": 316.0,
        "display_min": 295,
        "display_max": 325,
        "unit": "K",
    },
    "Rotational speed [rpm]": {
        "critical_low": 1000,
        "normal_low": 1200,
        "normal_high": 2000,
        "critical_high": 2500,
        "display_min": 0,
        "display_max": 3000,
        "unit": "rpm",
    },
    "Torque [Nm]": {
        "normal_max": 50.0,
        "warning_max": 65.0,
        "display_min": 0,
        "display_max": 80,
        "unit": "Nm",
    },
    "Tool wear [min]": {
        "normal_max": 100.0,
        "warning_max": 160.0,
        "critical_max": 220.0,
        "display_min": 0,
        "display_max": 253,
        "unit": "min",
    },
}

# ── Sensor Status Badge ───────────────────────────────────────────────────────

def get_sensor_status(sensor: str, value: float) -> tuple:
    """
    Returns (status_label: str, color_hex: str) based on operating range thresholds.
    """
    if sensor == "Air temperature [K]":
        if value > 312:
            return "Critical", "#ef4444"
        if value > 309:
            return "Warning", "#f59e0b"
        return "Normal", "#22c55e"

    elif sensor == "Process temperature [K]":
        if value > 316:
            return "Critical", "#ef4444"
        if value > 314:
            return "Warning", "#f59e0b"
        return "Normal", "#22c55e"

    elif sensor == "Rotational speed [rpm]":
        if value < 1000 or value > 2500:
            return "Critical", "#ef4444"
        if value < 1200 or value > 2000:
            return "Warning", "#f59e0b"
        return "Normal", "#22c55e"

    elif sensor == "Torque [Nm]":
        if value > 65:
            return "Critical", "#ef4444"
        if value > 50:
            return "Warning", "#f59e0b"
        if value < 8:
            return "Low", "#3b82f6"
        return "Normal", "#22c55e"

    elif sensor == "Tool wear [min]":
        if value > 220:
            return "Critical", "#ef4444"
        if value > 160:
            return "Warning", "#f59e0b"
        if value > 100:
            return "Elevated", "#f59e0b"
        return "Normal", "#22c55e"

    return "Unknown", "#94a3b8"


# ── Health Score Computation ──────────────────────────────────────────────────

def compute_health_score(machine) -> tuple:
    """
    Compute a 0–100 health score based on sensor readings and failure flag.

    Returns:
        (score: int, category: str, color: str)
    """
    # Immediately critical if machine has already failed
    if int(machine.get("Machine failure", 0)) == 1:
        score = max(5, 20 - sum([
            5 if machine.get("TWF", 0) == 1 else 0,
            5 if machine.get("HDF", 0) == 1 else 0,
            3 if machine.get("PWF", 0) == 1 else 0,
            3 if machine.get("OSF", 0) == 1 else 0,
            2 if machine.get("RNF", 0) == 1 else 0,
        ]))
        return score, "Critical", "#ef4444"

    score = 100

    # Tool wear penalty (most impactful single sensor)
    tw = machine["Tool wear [min]"]
    if tw > 220:
        score -= 35
    elif tw > 160:
        score -= 22
    elif tw > 100:
        score -= 10
    elif tw > 60:
        score -= 4

    # Air temperature penalty
    at = machine["Air temperature [K]"]
    if at > 312:
        score -= 18
    elif at > 309:
        score -= 9

    # Process temperature penalty
    pt = machine["Process temperature [K]"]
    if pt > 316:
        score -= 18
    elif pt > 314:
        score -= 9

    # RPM penalty
    rpm = machine["Rotational speed [rpm]"]
    if rpm < 1000 or rpm > 2500:
        score -= 18
    elif rpm < 1200 or rpm > 2000:
        score -= 9

    # Torque penalty
    torque = machine["Torque [Nm]"]
    if torque > 65:
        score -= 14
    elif torque > 50:
        score -= 7

    score = max(0, min(100, score))

    if score >= 85:
        return score, "Excellent", "#22c55e"
    elif score >= 70:
        return score, "Good", "#3b82f6"
    elif score >= 50:
        return score, "Warning", "#f59e0b"
    else:
        return score, "Critical", "#ef4444"


def compute_failure_probability(machine, health_score: int) -> int:
    """Derive a failure probability percentage from the health score."""
    if int(machine.get("Machine failure", 0)) == 1:
        return 85 + min(14, sum([
            3 if machine.get("TWF", 0) == 1 else 0,
            3 if machine.get("HDF", 0) == 1 else 0,
            2 if machine.get("PWF", 0) == 1 else 0,
            2 if machine.get("OSF", 0) == 1 else 0,
            1 if machine.get("RNF", 0) == 1 else 0,
        ]))
    # Map health score inversely to probability
    return max(2, round((100 - health_score) * 0.9))


# ── Suggested AI Questions ───────────────────────────────────────────────────

def get_suggested_questions(has_failed: bool, health_category: str) -> list:
    """Return context-appropriate suggested AI questions."""
    if has_failed:
        return [
            "What is the root cause of this failure?",
            "What is the complete repair procedure?",
            "Which components need immediate replacement?",
            "What is the estimated downtime for repairs?",
            "How can I prevent this failure in the future?",
            "Is it safe to operate this machine right now?",
            "What spare parts should I order urgently?",
        ]
    elif health_category == "Warning":
        return [
            "Which sensor readings are abnormal and why?",
            "Should I schedule preventive maintenance now?",
            "What is the remaining operational life?",
            "What maintenance actions will extend machine life?",
            "Can I continue operating until next scheduled maintenance?",
            "What early warning signs should I monitor closely?",
            "What is the priority of maintenance for this machine?",
        ]
    else:  # Good or Excellent
        return [
            "How can I optimize this machine's performance?",
            "What is the recommended maintenance schedule?",
            "Are all sensor readings within normal operating range?",
            "What efficiency improvements are possible?",
            "When should I schedule the next inspection?",
            "What preventive measures should I take proactively?",
            "How does this machine compare to fleet benchmarks?",
        ]


# ── HTML Rendering Helpers ────────────────────────────────────────────────────

def health_bar_html(score: int, category: str, color: str) -> str:
    """Return HTML for a color-coded health progress bar."""
    return f"""
    <div style="margin: 4px 0 12px 0;">
        <div style="background:#f1f5f9; border-radius:8px; overflow:hidden; height:12px;">
            <div style="background:{color}; width:{score}%; height:100%; border-radius:8px;
                        background: linear-gradient(90deg, {color}bb, {color});"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.75rem;">
            <span style="color:#94a3b8;">0</span>
            <span style="font-weight:700; color:{color};">{score} / 100 &mdash; {category}</span>
            <span style="color:#94a3b8;">100</span>
        </div>
    </div>
    """


def sensor_badge_html(status: str, color: str) -> str:
    """Return HTML for a sensor status pill badge."""
    # Map color to background tint
    bg_map = {
        "#22c55e": "#dcfce7",
        "#f59e0b": "#fef3c7",
        "#ef4444": "#fee2e2",
        "#3b82f6": "#dbeafe",
        "#94a3b8": "#f1f5f9",
    }
    bg = bg_map.get(color, "#f1f5f9")
    text = color if color != "#94a3b8" else "#475569"
    dot = "●"
    return (
        f'<span style="background:{bg}; color:{text}; padding:3px 10px; '
        f'border-radius:9999px; font-size:0.7rem; font-weight:700; '
        f'letter-spacing:0.04em; white-space:nowrap;">'
        f'{dot} {status.upper()}</span>'
    )
