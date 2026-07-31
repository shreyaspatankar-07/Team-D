"""
pages/machine_explorer.py — Machine Explorer (Module 3).

Renders machine cards using native Streamlit components wherever possible
to guarantee correct rendering. HTML is only used for the timeline/events
where colored dots and layout require it, built via string concatenation
(not f-strings) for safety.
"""

import streamlit as st
from utils.health import (
    compute_health_score,
    compute_failure_probability,
    get_sensor_status,
)
from utils.charts import (
    chart_gauge_temperature,
    chart_gauge_rpm,
    chart_gauge_torque,
    chart_tool_wear_gauge,
    chart_health_gauge,
    chart_temperature_comparison,
)
from utils.timeline import generate_maintenance_timeline, generate_recent_events
from utils.styles import page_header, section_header
from utils import db


# ── Colour helpers ────────────────────────────────────────────────────────────

def _priority_color(priority: str) -> str:
    return {"critical": "#ef4444", "warning": "#f59e0b", "normal": "#22c55e"}.get(priority, "#94a3b8")

def _type_color(event_type: str) -> str:
    return {"critical": "#ef4444", "warning": "#f59e0b", "success": "#22c55e", "info": "#3b82f6"}.get(event_type, "#94a3b8")


# ── Sensor Card (HTML via concatenation, not f-string) ────────────────────────

def _sensor_card_html(label: str, value_str: str, unit: str, status: str, color: str) -> str:
    """Build a sensor value card. Uses string concatenation to avoid f-string issues."""
    bg_map = {
        "#22c55e": "#dcfce7", "#f59e0b": "#fef3c7",
        "#ef4444": "#fee2e2", "#3b82f6": "#dbeafe", "#94a3b8": "#f1f5f9",
    }
    badge_bg = bg_map.get(color, "#f1f5f9")
    badge_tc = color if color != "#94a3b8" else "#475569"

    return (
        '<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;'
        ' padding:16px 12px 14px 12px; text-align:center;'
        ' box-shadow:0 1px 3px rgba(0,0,0,0.04); position:relative; overflow:hidden; height:100%;">'
        '<div style="position:absolute; top:0; left:0; right:0; height:4px; background:' + color + ';'
        ' border-radius:12px 12px 0 0;"></div>'
        '<div style="font-size:0.67rem; font-weight:700; color:#64748b; text-transform:uppercase;'
        ' letter-spacing:0.06em; margin:8px 0 6px 0;">' + label + '</div>'
        '<div style="font-size:1.45rem; font-weight:800; color:#1e293b; line-height:1.1; margin-bottom:2px;">'
        + value_str +
        '</div>'
        '<div style="font-size:0.7rem; color:#94a3b8; margin-bottom:8px;">' + unit + '</div>'
        '<span style="background:' + badge_bg + '; color:' + badge_tc + '; padding:2px 9px;'
        ' border-radius:9999px; font-size:0.67rem; font-weight:700; text-transform:uppercase;'
        ' letter-spacing:0.04em;">' + status + '</span>'
        '</div>'
    )


# ── Machine Info Card (native Streamlit) ──────────────────────────────────────

def _render_machine_info_card(machine, score: int, category: str, color: str, fp: int) -> None:
    """Render machine ID and health score using native Streamlit components."""
    has_failed = int(machine.get("Machine failure", 0)) == 1
    type_full  = {"L": "Low Quality", "M": "Medium Quality", "H": "High Quality"}.get(
        str(machine["Type"]), str(machine["Type"])
    )
    product_id = str(machine["Product ID"])

    # Status label
    if has_failed:
        status_label = "FAILED"
        status_color = "#b91c1c"
    elif category in ("Good", "Excellent"):
        status_label = "HEALTHY"
        status_color = "#15803d"
    elif category == "Warning":
        status_label = "WARNING"
        status_color = "#92400e"
    else:
        status_label = "CRITICAL"
        status_color = "#b91c1c"

    # Failure modes
    failure_modes = []
    for col, label in [
        ("TWF", "Tool Wear Failure"), ("HDF", "Heat Dissipation Failure"),
        ("PWF", "Power Failure"),     ("OSF", "Overstrain Failure"), ("RNF", "Random Failure"),
    ]:
        if machine.get(col, 0) == 1:
            failure_modes.append(label)

    with st.container():
        # Card header
        id_col, status_col = st.columns([3, 2])
        with id_col:
            st.markdown(
                '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
                ' letter-spacing:0.06em; margin:0 0 2px 0;">Machine ID</p>'
                '<p style="font-size:1.55rem; font-weight:800; color:#1e293b; margin:0 0 2px 0;'
                ' line-height:1.1;">' + product_id + '</p>'
                '<p style="font-size:0.84rem; color:#64748b; margin:0;">' + type_full + '</p>',
                unsafe_allow_html=True,
            )
            if failure_modes:
                st.markdown(
                    '<p style="font-size:0.8rem; color:#b91c1c; font-weight:600; margin:6px 0 0 0;">'
                    'Active failures: ' + ", ".join(failure_modes) + '</p>',
                    unsafe_allow_html=True,
                )
        with status_col:
            st.markdown(
                '<div style="text-align:right;">'
                '<span style="background:' + ("#fee2e2" if has_failed or category not in ("Good","Excellent","Warning") else ("#fef3c7" if category == "Warning" else "#dcfce7")) + ';'
                ' color:' + status_color + '; padding:4px 14px; border-radius:9999px;'
                ' font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">'
                + status_label + '</span>'
                '<p style="font-size:0.75rem; color:#64748b; margin:10px 0 2px 0; text-align:right;">Health Score</p>'
                '<p style="font-size:1.35rem; font-weight:800; color:' + color + '; margin:0; text-align:right;">'
                + str(score) + '<span style="font-size:0.85rem; font-weight:400; color:#94a3b8;"> / 100</span></p>'
                '<p style="font-size:0.74rem; color:#94a3b8; margin:2px 0 0 0; text-align:right;">'
                'Failure probability: ' + str(fp) + '%</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        # Health bar using native Streamlit progress
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin:12px 0 4px 0;">Health Score — ' + category + '</p>',
            unsafe_allow_html=True,
        )
        st.progress(score / 100)


# ── Failure Analysis Card (native Streamlit) ──────────────────────────────────

def _render_failure_card(machine, category: str, score: int, failure_modes: list) -> None:
    """Render failure analysis using native Streamlit metric columns."""
    has_failed = int(machine.get("Machine failure", 0)) == 1

    if has_failed:
        status_text = "FAILURE DETECTED"
        confidence  = 96
        risk_level  = "Critical"
        reason      = ", ".join([m[0] for m in failure_modes]) if failure_modes else "Multiple failure modes"
        bg_color    = "#fff7f7"
        border_color = "#fca5a5"
    elif category == "Warning":
        status_text = "WARNING — Monitor Closely"
        confidence  = 78
        risk_level  = "Medium"
        reason      = "One or more sensors approaching warning thresholds."
        bg_color    = "#fffbeb"
        border_color = "#fcd34d"
    else:
        status_text = "HEALTHY"
        confidence  = max(85, score)
        risk_level  = "Low"
        reason      = "All sensors within normal operating range."
        bg_color    = "#f0fdf4"
        border_color = "#86efac"

    failure_type_str = ", ".join([m[0] for m in failure_modes]) if failure_modes else "None Detected"

    st.markdown(
        '<div style="background:' + bg_color + '; border:1px solid ' + border_color + ';'
        ' border-radius:14px; padding:20px 22px; margin-bottom:16px;">',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin-bottom:4px;">Status</p>'
            '<p style="font-size:1.0rem; font-weight:800; color:#1e293b; margin:0;">' + status_text + '</p>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin-bottom:4px;">Confidence</p>'
            '<p style="font-size:1.05rem; font-weight:800; color:#1e293b; margin:0;">' + str(confidence) + '%</p>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin-bottom:4px;">Risk Level</p>'
            '<p style="font-size:1.0rem; font-weight:700; color:#1e293b; margin:0;">' + risk_level + '</p>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin-bottom:4px;">Failure Type</p>'
            '<p style="font-size:0.88rem; font-weight:600; color:#1e293b; margin:0;">' + failure_type_str + '</p>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(0,0,0,0.06);">'
        '<span style="font-size:0.72rem; font-weight:700; color:#64748b; text-transform:uppercase;'
        ' letter-spacing:0.05em;">Root Cause: </span>'
        '<span style="font-size:0.84rem; color:#1e293b;">' + reason + '</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ── Health Status Card (native Streamlit) ─────────────────────────────────────

def _render_health_status_card(score: int, category: str, color: str, has_failed: bool) -> None:
    """Render health status and recommendation using native Streamlit components."""
    if has_failed:
        rec          = "Immediate shutdown and full inspection required. Do not continue operating."
        rec_bg       = "#fff7f7"
        rec_border   = "#fca5a5"
    elif category == "Critical":
        rec          = "Schedule urgent maintenance today. Reduce operating load immediately."
        rec_bg       = "#fff7f7"
        rec_border   = "#fca5a5"
    elif category == "Warning":
        rec          = "Schedule preventive maintenance within 24\u201348 hours. Monitor sensors closely."
        rec_bg       = "#fffbeb"
        rec_border   = "#fcd34d"
    elif category == "Good":
        rec          = "Continue routine monitoring. Maintenance on current schedule."
        rec_bg       = "#f0fdf4"
        rec_border   = "#86efac"
    else:
        rec          = "Machine operating optimally. Continue standard maintenance schedule."
        rec_bg       = "#f0fdf4"
        rec_border   = "#86efac"

    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
        ' letter-spacing:0.06em; margin:0 0 4px 0;">Health Score — ' + category + '</p>',
        unsafe_allow_html=True,
    )
    st.progress(score / 100)
    st.markdown(
        '<p style="font-size:0.72rem; color:#94a3b8; margin:2px 0 12px 0;">'
        + str(score) + ' / 100</p>',
        unsafe_allow_html=True,
    )

    # Recommendation box
    st.markdown(
        '<div style="padding:12px 14px; background:' + rec_bg + '; border-radius:8px;'
        ' border:1px solid ' + rec_border + ';">'
        '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
        ' letter-spacing:0.06em; margin:0 0 4px 0;">Recommendation</p>'
        '<p style="font-size:0.86rem; color:#1e293b; line-height:1.5; margin:0;">' + rec + '</p>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Timeline HTML builder (string concatenation) ──────────────────────────────

def _build_timeline_html(timeline: list) -> str:
    """Build the maintenance timeline HTML via string concatenation (no f-string)."""
    parts = [
        '<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:16px;">'
    ]
    for item in timeline:
        dot_color = _priority_color(item.get("priority", "normal"))
        event_text = str(item.get("event", ""))
        detail_text = str(item.get("detail", ""))
        due_text = str(item.get("due", ""))
        parts.append(
            '<div style="display:flex; gap:12px; align-items:flex-start; padding:10px 0;'
            ' border-bottom:1px solid #f1f5f9;">'
            '<div style="width:10px; height:10px; border-radius:50%; background:' + dot_color + ';'
            ' margin-top:5px; flex-shrink:0;"></div>'
            '<div style="flex:1; min-width:0;">'
            '<div style="font-size:0.86rem; font-weight:600; color:#1e293b; margin-bottom:3px;">'
            + event_text + '</div>'
            '<div style="font-size:0.76rem; color:#64748b; line-height:1.4;">'
            + detail_text + '</div>'
            '</div>'
            '<div style="font-size:0.72rem; font-weight:600; color:#94a3b8; white-space:nowrap;'
            ' padding-top:2px; flex-shrink:0;">' + due_text + '</div>'
            '</div>'
        )
    parts.append('</div>')
    return "".join(parts)


# ── Events HTML builder (string concatenation) ────────────────────────────────

def _build_events_html(events: list) -> str:
    """Build the recent events HTML via string concatenation (no f-string)."""
    parts = [
        '<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:16px;">'
    ]
    for evt in events:
        dot_color  = _type_color(evt.get("type", "info"))
        event_text = str(evt.get("event", ""))
        time_text  = str(evt.get("time", ""))
        parts.append(
            '<div style="display:flex; gap:10px; align-items:flex-start; padding:8px 0;'
            ' border-bottom:1px solid #f1f5f9;">'
            '<div style="width:8px; height:8px; border-radius:50%; background:' + dot_color + ';'
            ' margin-top:5px; flex-shrink:0;"></div>'
            '<div style="flex:1; min-width:0;">'
            '<div style="font-size:0.81rem; color:#1e293b; font-weight:500; line-height:1.4;">'
            + event_text + '</div>'
            '</div>'
            '<div style="font-size:0.71rem; color:#94a3b8; white-space:nowrap; flex-shrink:0;'
            ' padding-top:2px;">' + time_text + '</div>'
            '</div>'
        )
    parts.append('</div>')
    return "".join(parts)


# ── Main Page Renderer ────────────────────────────────────────────────────────

def render(df, raw_df) -> None:
    """Render the Machine Explorer page."""

    page_header(
        "🔍",
        "Machine Explorer",
        "Select any machine to explore its live sensor readings, health status, and maintenance forecast.",
    )

    # ── Machine Selector with Prev / Next ─────────────────────────────────────
    product_ids    = sorted(raw_df["Product ID"].unique().tolist())
    total_machines = len(product_ids)

    if "selected_machine_id" not in st.session_state:
        st.session_state["selected_machine_id"] = product_ids[0]

    current_id = st.session_state["selected_machine_id"]
    if current_id not in product_ids:
        current_id = product_ids[0]
        st.session_state["selected_machine_id"] = current_id

    current_idx = product_ids.index(current_id)

    col_prev, col_select, col_next = st.columns([1, 6, 1])

    with col_prev:
        st.write("")  # vertical spacer
        if st.button("◀", disabled=(current_idx == 0), width='stretch', help="Previous machine"):
            st.session_state["selected_machine_id"] = product_ids[current_idx - 1]
            st.rerun()

    with col_select:
        selected = st.selectbox(
            f"Select Machine (showing {current_idx + 1} of {total_machines:,})",
            options=product_ids,
            index=current_idx,
            key="explorer_machine_select",
        )
        if selected != current_id:
            st.session_state["selected_machine_id"] = selected
            st.rerun()

    with col_next:
        st.write("")  # vertical spacer
        if st.button("▶", disabled=(current_idx == total_machines - 1), width='stretch', help="Next machine"):
            st.session_state["selected_machine_id"] = product_ids[current_idx + 1]
            st.rerun()

    # ── Load Machine Data ─────────────────────────────────────────────────────
    machine_rows = raw_df[raw_df["Product ID"] == st.session_state["selected_machine_id"]]
    if machine_rows.empty:
        st.error("Selected machine not found in dataset.")
        return

    machine    = machine_rows.iloc[0]
    score, category, color = compute_health_score(machine)
    fp         = compute_failure_probability(machine, score)
    has_failed = int(machine.get("Machine failure", 0)) == 1

    # ── Machine Info Card ─────────────────────────────────────────────────────
    st.write("")
    section_header("Selected Machine", "Identity, status and health score.")
    _render_machine_info_card(machine, score, category, color, fp)

    # ── Create Work Order Button ───────────────────────────────────────────────
    # Available for both failed and healthy machines.
    # Clicking auto-fills the Work Order Creation form via session state.
    wo_btn_col, _ = st.columns([2, 5])
    with wo_btn_col:
        if st.button(
            "🔧  Create Work Order",
            key="explorer_create_wo_btn",
            type="primary",
            width="stretch",
            help="Navigate to Work Order Creation with this machine's details pre-filled.",
        ):
            # ── Determine failure type ─────────────────────────────────────────
            failure_codes = [c for c in ["TWF", "HDF", "PWF", "OSF", "RNF"]
                             if machine.get(c, 0) == 1]
            # Use the first detected failure type; fall back to TWF for healthy machines
            primary_failure = failure_codes[0] if failure_codes else db.FAILURE_TYPES[0]

            # ── Recommended Technician Type ────────────────────────────────────
            if failure_codes:
                tech_type = db.FAILURE_TO_TECH_TYPE.get(primary_failure, db.TECHNICIAN_TYPES[0])
                priority  = db.FAILURE_TO_PRIORITY.get(primary_failure, "Medium")
                description = db.FAILURE_DESCRIPTIONS.get(primary_failure, "")
            else:
                tech_type   = db.HEALTHY_TECH_TYPE
                priority    = db.HEALTHY_PRIORITY
                description = db.HEALTHY_DESCRIPTION

            # ── Write pre-fill payload to session state ────────────────────────
            st.session_state["woc_prefill"] = {
                "product_id":   str(machine["Product ID"]),
                "failure_type": primary_failure,
                "tech_type":    tech_type,
                "priority":     priority,
                "description":  description,
            }
            # Navigate to Work Order Creation page
            st.session_state["page"] = "work_order_creation"
            st.rerun()

    section_header("Live Sensor Values", "Current readings with operating-range status badges.")

    sensors = [
        ("Air Temperature",  float(machine["Air temperature [K]"]),    "K",   "Air temperature [K]"),
        ("Process Temp",     float(machine["Process temperature [K]"]), "K",   "Process temperature [K]"),
        ("Rotational Speed", float(machine["Rotational speed [rpm]"]),  "rpm", "Rotational speed [rpm]"),
        ("Torque",           float(machine["Torque [Nm]"]),             "Nm",  "Torque [Nm]"),
        ("Tool Wear",        float(machine["Tool wear [min]"]),         "min", "Tool wear [min]"),
    ]

    cols = st.columns(5)
    for col, (label, value, unit, sensor_key) in zip(cols, sensors):
        status, s_color = get_sensor_status(sensor_key, value)
        with col:
            st.markdown(
                _sensor_card_html(label, f"{value:.1f}", unit, status, s_color),
                unsafe_allow_html=True,
            )

    # ── Gauge Charts ──────────────────────────────────────────────────────────
    st.write("")
    section_header("Sensor Gauges", "Visual operating-range indicators for each sensor.")

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            chart_gauge_temperature(float(machine["Air temperature [K]"]), "Air Temperature"),
            width="stretch",
        )
    with g2:
        st.plotly_chart(
            chart_gauge_temperature(float(machine["Process temperature [K]"]), "Process Temperature"),
            width="stretch",
        )
    with g3:
        st.plotly_chart(
            chart_temperature_comparison(
                float(machine["Air temperature [K]"]),
                float(machine["Process temperature [K]"]),
            ),
            width="stretch",
        )

    g4, g5, g6 = st.columns(3)
    with g4:
        st.plotly_chart(chart_gauge_rpm(float(machine["Rotational speed [rpm]"])), width="stretch")
    with g5:
        st.plotly_chart(chart_gauge_torque(float(machine["Torque [Nm]"])), width="stretch")
    with g6:
        st.plotly_chart(chart_tool_wear_gauge(float(machine["Tool wear [min]"])), width="stretch")

    # ── Failure Analysis ──────────────────────────────────────────────────────
    section_header("Failure Analysis", "Prediction result with confidence, risk level, and root cause.")

    mode_map = {
        "TWF": ("Tool Wear Failure",       "Excessive tool degradation beyond safe limits."),
        "HDF": ("Heat Dissipation Failure", "Insufficient cooling — process temperature too high."),
        "PWF": ("Power Failure",            "Operating outside the rated power envelope."),
        "OSF": ("Overstrain Failure",       "Excessive torque relative to machine grade."),
        "RNF": ("Random Failure",           "Stochastic failure — no single identifiable root cause."),
    }
    failure_modes = [(label, desc) for col_key, (label, desc) in mode_map.items() if machine.get(col_key, 0) == 1]

    _render_failure_card(machine, category, score, failure_modes)

    if failure_modes:
        with st.expander("Failure Mode Details"):
            for label, desc in failure_modes:
                st.markdown(f"**{label}:** {desc}")

    # ── Health Status ─────────────────────────────────────────────────────────
    health_col, gauge_col = st.columns([3, 2])

    with health_col:
        section_header("Health Status", "Composite score with maintenance recommendation.")
        _render_health_status_card(score, category, color, has_failed)

    with gauge_col:
        st.write("")
        st.plotly_chart(chart_health_gauge(score, category, color), width="stretch")

    # ── Maintenance Timeline + Recent Events ──────────────────────────────────
    tl_col, ev_col = st.columns(2)

    with tl_col:
        section_header("Maintenance Timeline", "Dynamically generated from current machine condition.")
        timeline = generate_maintenance_timeline(machine, score, category)
        st.markdown(_build_timeline_html(timeline), unsafe_allow_html=True)

    with ev_col:
        section_header("Recent Events", "Auto-generated activity log based on machine state.")
        events = generate_recent_events(machine, score, category)
        st.markdown(_build_events_html(events), unsafe_allow_html=True)
