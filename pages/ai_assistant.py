"""
pages/ai_assistant.py — AI Maintenance Assistant (Module 4).

Key changes vs v1:
  - st.chat_message() + st.write_stream() for native streaming chat
  - st.markdown(report_text) renders Markdown properly (headers, bullets, bold)
  - Machine summary uses native Streamlit components + inline-style HTML
  - No CSS class dependencies anywhere
  - PDF export with robust Unicode sanitisation
"""

import streamlit as st
from datetime import datetime

from utils.health import (
    compute_health_score,
    compute_failure_probability,
    get_sensor_status,
    get_suggested_questions,
)
from utils import ollama_service
from utils.report_formatter import (
    get_report_metadata,
    render_report_metadata_html,
    build_markdown_report,
    build_pdf_report,
)
from utils.styles import page_header, section_header


# ── Session State ─────────────────────────────────────────────────────────────

def _ensure_state() -> None:
    for key, default in [
        ("ai_reports", {}),
        ("ai_report_metas", {}),
        ("chat_histories", {}),
        ("selected_machine_id", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


def _get_machine(raw_df, machine_id: str):
    rows = raw_df[raw_df["Product ID"] == machine_id]
    return rows.iloc[0] if not rows.empty else None


# ── Machine Summary (left column) ─────────────────────────────────────────────

def _render_machine_summary(machine, score: int, category: str, color: str, fp: int) -> None:
    """Compact machine card for the AI Assistant left column — native Streamlit components."""
    has_failed = int(machine.get("Machine failure", 0)) == 1
    type_full  = {"L": "Low Quality", "M": "Medium Quality", "H": "High Quality"}.get(
        str(machine["Type"]), str(machine["Type"])
    )
    product_id = str(machine["Product ID"])

    # Status styling
    if has_failed:
        status_label, status_bg, status_tc = "FAILED",   "#fee2e2", "#b91c1c"
    elif category == "Warning":
        status_label, status_bg, status_tc = "WARNING",  "#fef3c7", "#92400e"
    elif category in ("Good", "Excellent"):
        status_label, status_bg, status_tc = "HEALTHY",  "#dcfce7", "#15803d"
    else:
        status_label, status_bg, status_tc = "CRITICAL", "#fee2e2", "#b91c1c"

    # Failure modes
    failure_modes = []
    for col, label in [
        ("TWF", "Tool Wear"), ("HDF", "Heat Dissipation"),
        ("PWF", "Power"),     ("OSF", "Overstrain"), ("RNF", "Random"),
    ]:
        if machine.get(col, 0) == 1:
            failure_modes.append(label)

    # Header row: machine ID + status badge
    id_col, st_col = st.columns([3, 2])
    with id_col:
        st.markdown(
            '<p style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
            ' letter-spacing:0.06em; margin:0 0 2px 0;">Machine</p>'
            '<p style="font-size:1.4rem; font-weight:800; color:#1e293b; margin:0; line-height:1.1;">'
            + product_id + '</p>'
            '<p style="font-size:0.8rem; color:#64748b; margin:3px 0 0 0;">' + type_full + '</p>',
            unsafe_allow_html=True,
        )
    with st_col:
        st.markdown(
            '<div style="text-align:right;">'
            '<span style="background:' + status_bg + '; color:' + status_tc + '; padding:4px 12px;'
            ' border-radius:9999px; font-size:0.75rem; font-weight:700; text-transform:uppercase;'
            ' letter-spacing:0.04em;">' + status_label + '</span>'
            '<p style="font-size:0.73rem; color:#64748b; margin:8px 0 2px 0; text-align:right;">Health</p>'
            '<p style="font-size:1.2rem; font-weight:800; color:' + color + '; margin:0; text-align:right;">'
            + str(score) + '<span style="font-size:0.8rem; font-weight:400; color:#94a3b8;"> /100</span></p>'
            '<p style="font-size:0.72rem; color:#94a3b8; margin:2px 0 0 0; text-align:right;">'
            'Fail prob: ' + str(fp) + '%</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Health progress bar (native Streamlit)
    st.progress(score / 100)

    # Failure row
    if failure_modes:
        st.markdown(
            '<div style="margin-top:6px; padding:6px 10px; background:#fee2e2;'
            ' border-radius:6px; font-size:0.78rem; color:#b91c1c; font-weight:600;">'
            'Active failures: ' + ", ".join(failure_modes) + '</div>',
            unsafe_allow_html=True,
        )

    # Sensor readings — built via string concatenation for safe rendering
    sensors = [
        ("Air Temp",  float(machine["Air temperature [K]"]),    "K",   "Air temperature [K]"),
        ("Proc Temp", float(machine["Process temperature [K]"]), "K",   "Process temperature [K]"),
        ("RPM",       float(machine["Rotational speed [rpm]"]),  "rpm", "Rotational speed [rpm]"),
        ("Torque",    float(machine["Torque [Nm]"]),             "Nm",  "Torque [Nm]"),
        ("Tool Wear", float(machine["Tool wear [min]"]),         "min", "Tool wear [min]"),
    ]
    bg_map = {
        "#22c55e": "#dcfce7", "#f59e0b": "#fef3c7",
        "#ef4444": "#fee2e2", "#3b82f6": "#dbeafe", "#94a3b8": "#f1f5f9",
    }
    parts = [
        '<div style="margin-top:10px;">'
        '<div style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;'
        ' letter-spacing:0.06em; margin-bottom:6px;">Sensor Readings</div>'
    ]
    for s_label, s_val, s_unit, s_key in sensors:
        s_status, s_color = get_sensor_status(s_key, s_val)
        badge_bg = bg_map.get(s_color, "#f1f5f9")
        badge_tc = s_color if s_color != "#94a3b8" else "#475569"
        parts.append(
            '<div style="display:flex; justify-content:space-between; align-items:center;'
            ' padding:6px 0; border-bottom:1px solid #f1f5f9;">'
            '<span style="font-size:0.79rem; color:#64748b;">' + s_label + '</span>'
            '<div style="display:flex; align-items:center; gap:6px;">'
            '<span style="font-size:0.82rem; font-weight:600; color:#1e293b;">'
            + f"{s_val:.1f}" + ' ' + s_unit + '</span>'
            '<span style="background:' + badge_bg + '; color:' + badge_tc + '; padding:2px 9px;'
            ' border-radius:9999px; font-size:0.68rem; font-weight:700; text-transform:uppercase;'
            ' letter-spacing:0.04em;">' + s_status + '</span>'
            '</div>'
            '</div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ── Export Buttons ────────────────────────────────────────────────────────────

def _show_export_buttons(report_text: str, meta: dict, context: dict, machine_id: str) -> None:
    """Render the Markdown and PDF export download buttons."""
    st.write("")
    exp_col1, exp_col2 = st.columns(2)

    ts = meta.get("ts_display", datetime.now().strftime("%Y%m%d_%H%M%S"))
    ts_fn = ts.replace(" ", "_").replace(":", "")

    with exp_col1:
        md_content = build_markdown_report(report_text, meta, context)
        st.download_button(
            label="Export Report",
            data=md_content.encode("utf-8"),
            file_name=f"report_{machine_id}_{ts_fn}.md",
            mime="text/markdown",
            width="stretch",
            key=f"dl_md_{machine_id}_{ts_fn}",
        )

    with exp_col2:
        pdf_bytes = build_pdf_report(report_text, meta, context)
        if pdf_bytes:
            st.download_button(
                label="Export PDF",
                data=pdf_bytes,
                file_name=f"report_{machine_id}_{ts_fn}.pdf",
                mime="application/pdf",
                width="stretch",
                key=f"dl_pdf_{machine_id}_{ts_fn}",
            )


# ── Main Page Renderer ────────────────────────────────────────────────────────

def render(df, raw_df) -> None:
    """Render the AI Maintenance Assistant page."""

    _ensure_state()

    page_header(
        "🤖",
        "AI Maintenance Assistant",
        "Powered by Llama 3.2 via Ollama — full machine context injected automatically.",
    )

    # ── Ollama Availability Check ─────────────────────────────────────────────
    if not ollama_service.is_ollama_available():
        st.markdown(
            """
            <div style="background:#fff7f7; border:1px solid #fca5a5; border-radius:12px;
                        padding:20px 24px; margin-bottom:20px;">
                <div style="font-size:1.05rem; font-weight:700; color:#b91c1c; margin-bottom:8px;">
                    ⚠️ Ollama Server Unavailable
                </div>
                <div style="font-size:0.86rem; color:#7f1d1d; line-height:1.6;">
                    The local Ollama server is not running or not reachable at
                    <code style="background:#fee2e2; padding:1px 5px; border-radius:4px;">http://localhost:11434</code>
                    <br><br>
                    <strong>To start Ollama:</strong><br>
                    1. Open a terminal and run: <code style="background:#fee2e2; padding:1px 5px; border-radius:4px;">ollama serve</code><br>
                    2. Ensure the model exists: <code style="background:#fee2e2; padding:1px 5px; border-radius:4px;">ollama pull llama3.2</code><br>
                    3. Refresh this page.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Machine Selector ──────────────────────────────────────────────────────
    product_ids = sorted(raw_df["Product ID"].unique().tolist())
    current_id  = st.session_state.get("selected_machine_id", product_ids[0])
    if current_id not in product_ids:
        current_id = product_ids[0]

    selected_id = st.selectbox(
        "Select Machine (synced with Machine Explorer)",
        options=product_ids,
        index=product_ids.index(current_id),
        key="ai_machine_selectbox",
    )

    if selected_id != st.session_state.get("selected_machine_id"):
        st.session_state["selected_machine_id"] = selected_id

    machine_id = selected_id
    machine    = _get_machine(raw_df, machine_id)
    if machine is None:
        st.error("Machine data not found.")
        return

    score, category, color = compute_health_score(machine)
    fp         = compute_failure_probability(machine, score)
    has_failed = int(machine.get("Machine failure", 0)) == 1
    context    = ollama_service.build_machine_context(machine)

    # Initialise per-machine chat history
    if machine_id not in st.session_state["chat_histories"]:
        st.session_state["chat_histories"][machine_id] = []

    st.write("")

    # ══════════════════════════════════════════════════════════════════════════
    # TWO-COLUMN LAYOUT: Machine Summary | AI Report
    # ══════════════════════════════════════════════════════════════════════════
    left_col, right_col = st.columns([2, 3], gap="large")

    with left_col:
        section_header("Machine Summary", "Current status and sensor readings.")
        _render_machine_summary(machine, score, category, color, fp)

    with right_col:
        section_header("AI Maintenance Report", "")

        cached_report = st.session_state["ai_reports"].get(machine_id)
        cached_meta   = st.session_state["ai_report_metas"].get(machine_id)

        if not ollama_service.is_ollama_available():
            # Show cached report if available, but no generate button
            if cached_report:
                st.caption("Showing cached report (Ollama offline).")
                if cached_meta:
                    st.markdown(render_report_metadata_html(cached_meta), unsafe_allow_html=True)
                st.markdown(cached_report)
                _show_export_buttons(cached_report, cached_meta or {}, context, machine_id)
            else:
                st.info("Start Ollama to generate a report.")
        else:
            # Generate / Refresh button row
            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                generate_btn = st.button(
                    "🔄 Refresh Report" if cached_report else "⚡ Generate Report",
                    type="primary",
                    width="stretch",
                    key=f"gen_{machine_id}",
                )
            with btn_col2:
                if cached_report and st.button("🗑️ Clear", width="stretch", key=f"clear_{machine_id}"):
                    st.session_state["ai_reports"].pop(machine_id, None)
                    st.session_state["ai_report_metas"].pop(machine_id, None)
                    st.rerun()

            if generate_btn:
                meta = get_report_metadata(machine_id)
                st.markdown(render_report_metadata_html(meta), unsafe_allow_html=True)
                try:
                    # Stream the report; st.write_stream renders Markdown in real time
                    report_text = st.write_stream(ollama_service.generate_report(context))
                    st.session_state["ai_reports"][machine_id]      = report_text
                    st.session_state["ai_report_metas"][machine_id] = meta
                    _show_export_buttons(report_text, meta, context, machine_id)
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

            elif cached_report:
                if cached_meta:
                    st.markdown(render_report_metadata_html(cached_meta), unsafe_allow_html=True)
                # Render as Markdown (proper headers, bullets, bold)
                st.markdown(cached_report)
                _show_export_buttons(cached_report, cached_meta or {}, context, machine_id)

            else:
                st.markdown(
                    f"""
                    <div style="background:#f8fafc; border:1px dashed #cbd5e1; border-radius:10px;
                                padding:30px 20px; text-align:center; color:#94a3b8;">
                        <div style="font-size:2rem; margin-bottom:8px;">📄</div>
                        <div style="font-size:0.88rem; font-weight:500; color:#64748b;">
                            Click <strong>Generate Report</strong> to create an AI-powered
                            maintenance report for <strong>{machine_id}</strong>.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # SUGGESTED QUESTIONS
    # ══════════════════════════════════════════════════════════════════════════
    st.write("")
    section_header("Suggested Questions", "Click any question to ask the AI assistant.")

    questions  = get_suggested_questions(has_failed, category)
    history    = st.session_state["chat_histories"].get(machine_id, [])

    q_cols = st.columns(3)
    for i, q in enumerate(questions):
        with q_cols[i % 3]:
            if st.button(q, key=f"sq_{machine_id}_{i}", width="stretch"):
                history.append({"role": "user", "content": q})
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # CHAT INTERFACE — native st.chat_message()
    # ══════════════════════════════════════════════════════════════════════════
    st.write("")

    chat_hdr, clear_btn_col = st.columns([5, 1])
    with chat_hdr:
        section_header("Conversation", f"Full context of {machine_id} injected into every message.")
    with clear_btn_col:
        st.write("")
        if st.button("🗑️ Clear", key=f"clear_chat_{machine_id}", width="stretch"):
            st.session_state["chat_histories"][machine_id] = []
            st.rerun()

    # Display conversation history
    history = st.session_state["chat_histories"].get(machine_id, [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # If last message is from user and Ollama is available, generate AI response
    if history and history[-1]["role"] == "user" and ollama_service.is_ollama_available():
        question = history[-1]["content"]
        report   = st.session_state["ai_reports"].get(machine_id, "")
        try:
            with st.chat_message("assistant"):
                gen      = ollama_service.chat(context, report, history[:-1], question)
                ai_text  = st.write_stream(gen)
            history.append({"role": "assistant", "content": ai_text})
            st.rerun()
        except Exception as e:
            err = f"Failed to get response: {e}"
            st.error(err)
            history.append({"role": "assistant", "content": f"[Error: {err}]"})
            st.rerun()
    elif history and history[-1]["role"] == "user" and not ollama_service.is_ollama_available():
        history.append({"role": "assistant", "content": "Ollama server is offline. Please start it and try again."})
        st.rerun()

    # Chat input
    if prompt := st.chat_input(
        f"Ask about machine {machine_id}...",
        key=f"chat_input_{machine_id}",
    ):
        history = st.session_state["chat_histories"].setdefault(machine_id, [])
        history.append({"role": "user", "content": prompt})
        st.rerun()
