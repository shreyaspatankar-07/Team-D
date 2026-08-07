"""
pages/work_order_creation.py — Work Order Creation form page (Module 5).

Key behaviours:
  • Product ID selectbox lives OUTSIDE the form so its on_change fires
    immediately, auto-populating Machine Type from raw_df.
  • Technician Type selectbox also lives OUTSIDE the form for the same
    reason — selecting it narrows the Assigned Technician dropdown.
  • Both the Product ID and Technician Type can be pre-populated by the
    Machine Explorer via session-state keys (woc_prefill_*).
  • Description is auto-generated based on the machine state and is
    editable by the user before saving.
  • All database operations are delegated to utils/db.py.
"""

import streamlit as st
import pandas as pd

from utils import db
from utils.styles import page_header, section_header, COLORS


# ── Constants ──────────────────────────────────────────────────────────────────

MACHINE_TYPE_LABELS = {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}
MACHINE_TYPE_COLORS = {
    "L": ("#dcfce7", "#15803d"),
    "M": ("#dbeafe", "#1d4ed8"),
    "H": ("#fef3c7", "#92400e"),
}
FAILURE_TYPE_LABELS = {
    "TWF": "Tool Wear Failure (TWF)",
    "HDF": "Heat Dissipation Failure (HDF)",
    "PWF": "Power Failure (PWF)",
    "OSF": "Overstrain Failure (OSF)",
    "RNF": "Random Failure (RNF)",
}


# ── Product-ID → Machine-Type lookup ──────────────────────────────────────────

def _build_pid_to_type_map(raw_df: pd.DataFrame) -> dict[str, str]:
    """Return a dict mapping each Product ID to its Machine Type (L/M/H)."""
    return dict(zip(raw_df["Product ID"], raw_df["Type"]))


# ── Session-state helpers ──────────────────────────────────────────────────────

def _init_form_state(raw_df: pd.DataFrame) -> None:
    """
    Initialise default values for form session-state keys.
    Respects pre-fill values injected by the Machine Explorer
    (stored under woc_prefill_* keys).
    """
    # Consume pre-fill payload from Machine Explorer (one-shot)
    prefill = st.session_state.pop("woc_prefill", None)

    defaults: dict = {
        "woc_product_id_sel":      "",
        "woc_auto_machine_type":   "",
        "woc_tech_type_sel":       db.TECHNICIAN_TYPES[0],
        "woc_failure_type":        db.FAILURE_TYPES[0],
        "woc_priority":            "Medium",
        "woc_status":              db.STATUSES[0],
        "woc_description_area":    "",
        "woc_form_version":        0,
        "woc_last_saved_id":       None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Apply pre-fill from Machine Explorer if present
    if prefill:
        pid_to_type = _build_pid_to_type_map(raw_df)
        st.session_state["woc_product_id_sel"]    = prefill.get("product_id", "")
        st.session_state["woc_auto_machine_type"]  = pid_to_type.get(prefill.get("product_id", ""), "")
        st.session_state["woc_tech_type_sel"]      = prefill.get("tech_type", db.TECHNICIAN_TYPES[0])
        st.session_state["woc_failure_type"]       = prefill.get("failure_type", db.FAILURE_TYPES[0])
        st.session_state["woc_priority"]           = prefill.get("priority", "Medium")
        st.session_state["woc_status"]             = "Open"
        st.session_state["woc_description_area"]   = prefill.get("description", "")
        # Bump form version so widgets re-render with new defaults
        st.session_state["woc_form_version"] = st.session_state.get("woc_form_version", 0) + 1
        st.session_state["woc_last_saved_id"] = None


def _reset_form() -> None:
    """Clear all form session-state keys so the form resets to defaults."""
    for key in [
        "woc_product_id_sel", "woc_auto_machine_type", "woc_tech_type_sel",
        "woc_failure_type", "woc_priority", "woc_description_area", "woc_status",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["woc_form_version"] = st.session_state.get("woc_form_version", 0) + 1


# ── on_change callbacks ───────────────────────────────────────────────────────

def _on_product_id_change(pid_to_type: dict[str, str]) -> None:
    """Auto-populate Machine Type when a Product ID is selected."""
    selected_pid = st.session_state.get("woc_product_id_sel", "")
    st.session_state["woc_auto_machine_type"] = pid_to_type.get(selected_pid, "")


# ── Validation ─────────────────────────────────────────────────────────────────

def _validate(product_id: str, machine_type: str, tech_type: str, technician: str) -> list[str]:
    """Return a list of human-readable validation error messages."""
    errors: list[str] = []
    if not product_id.strip():
        errors.append("**Product ID** is required — please select a product.")
    if not machine_type.strip():
        errors.append("**Machine Type** could not be determined — please re-select a Product ID.")
    if not tech_type.strip():
        errors.append("**Technician Type** is required.")
    if not technician.strip() or technician == "— Select a technician —":
        errors.append("**Assigned Technician** is required — please choose a technician.")
    return errors


# ── Machine Type display card (read-only) ────────────────────────────────────

def _machine_type_card(machine_type: str) -> str:
    """Return an HTML read-only card for the auto-populated Machine Type."""
    if not machine_type:
        label = "—  Select a Product ID first"
        bg, tc, bar_color = "#f8fafc", "#94a3b8", "#e2e8f0"
    else:
        label = MACHINE_TYPE_LABELS.get(machine_type, machine_type)
        bg, tc = MACHINE_TYPE_COLORS.get(machine_type, ("#f1f5f9", "#475569"))
        bar_color = tc

    return f"""
    <div style="margin-top:4px; margin-bottom:4px;">
        <label style="font-size:0.875rem; font-weight:600; color:#374151; display:block; margin-bottom:4px;">
            Machine Type
            <span style="font-size:0.72rem; color:#94a3b8; font-weight:400; margin-left:6px;">(auto-populated)</span>
        </label>
        <div style="background:{bg}; border:1px solid {bar_color}40;
                    border-left:4px solid {bar_color}; border-radius:8px;
                    padding:10px 14px; font-size:0.9rem; font-weight:700;
                    color:{tc}; min-height:42px; display:flex; align-items:center; gap:8px;">
            <span>⚙</span> {label}
        </div>
        <p style="font-size:0.72rem; color:#94a3b8; margin-top:4px; margin-bottom:0;">
            Derived automatically from the selected Product ID.
        </p>
    </div>
    """


# ── Page render ───────────────────────────────────────────────────────────────

def render(raw_df: pd.DataFrame) -> None:
    """Render the Work Order Creation page."""

    pid_to_type = _build_pid_to_type_map(raw_df)
    product_options = sorted(pid_to_type.keys())

    _init_form_state(raw_df)

    # ── Page Header ────────────────────────────────────────────────────────────
    page_header(
        "",
        "Work Order Creation",
        "Generate and record maintenance work orders for machine failures.",
    )

    # ── Success banner ─────────────────────────────────────────────────────────
    if st.session_state.get("woc_last_saved_id"):
        wo_id = st.session_state["woc_last_saved_id"]
        st.success(
            f"Work Order **#{wo_id}** created successfully and saved to the database.",
            icon=None,
        )

    col_form, col_info = st.columns([3, 1], gap="large")

    with col_form:
        section_header("New Work Order", "Fill in all required fields and click Save.")

        # ── STEP 1: Product ID (outside form — triggers on_change immediately) ─
        st.markdown(
            '<p style="font-size:0.88rem; font-weight:600; color:#374151; margin-bottom:4px;">'
            'Product ID <span style="color:#ef4444;">*</span></p>',
            unsafe_allow_html=True,
        )
        pid_opts = [""] + product_options
        st.selectbox(
            label="Product ID",
            options=pid_opts,
            help="Select a Product ID — Machine Type fills in automatically.",
            key="woc_product_id_sel",
            on_change=_on_product_id_change,
            args=(pid_to_type,),
            label_visibility="collapsed",
        )

        selected_pid   = st.session_state.get("woc_product_id_sel", "")
        auto_mtype     = st.session_state.get("woc_auto_machine_type", "")

        # ── STEP 2: Technician Type (outside form — filters technician list) ───
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.88rem; font-weight:600; color:#374151; margin-bottom:4px;">'
            'Technician Type <span style="color:#ef4444;">*</span></p>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            label="Technician Type",
            options=db.TECHNICIAN_TYPES,
            help="Select the maintenance team — Assigned Technician list updates automatically.",
            key="woc_tech_type_sel",
            label_visibility="collapsed",
        )

        selected_tech_type = st.session_state.get("woc_tech_type_sel", db.TECHNICIAN_TYPES[0])
        available_technicians = db.TECHNICIANS.get(selected_tech_type, [])

        # ── STEP 3: Main form (remaining fields) ──────────────────────────────
        form_key = f"work_order_form_v{st.session_state['woc_form_version']}"

        with st.form(key=form_key, clear_on_submit=False):

            # Machine Type (read-only auto-fill display)
            st.markdown(_machine_type_card(auto_mtype), unsafe_allow_html=True)

            # Assigned Technician (filtered by Technician Type chosen above)
            st.markdown("<br>", unsafe_allow_html=True)
            technician_opts = ["— Select a technician —"] + available_technicians
            assigned_technician = st.selectbox(
                "Assigned Technician *",
                options=technician_opts,
                index=0,
                help="Technicians shown are from the selected Technician Type.",
                key="woc_assigned_technician",
            )

            # Failure Type + Priority
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                failure_type = st.selectbox(
                    "Failure Type *",
                    options=db.FAILURE_TYPES,
                    format_func=lambda ft: FAILURE_TYPE_LABELS.get(ft, ft),
                    key="woc_failure_type",
                )
            with r2c2:
                priority = st.selectbox(
                    "Priority *",
                    options=db.PRIORITIES,
                    key="woc_priority",
                )

            # Status
            status = st.selectbox(
                "Status",
                options=db.STATUSES,
                key="woc_status",
            )

            # Description (pre-filled if from Machine Explorer, user-editable)
            description = st.text_area(
                "Description",
                placeholder="Describe the failure, observations, and recommended action…",
                height=130,
                key="woc_description_area",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Action buttons
            btn_col1, btn_col2, _ = st.columns([1.2, 1, 2.8])
            with btn_col1:
                submitted = st.form_submit_button(
                    "Save Work Order",
                    type="primary",
                    width="stretch",
                )
            with btn_col2:
                reset_clicked = st.form_submit_button(
                    "Reset",
                    type="secondary",
                    width="stretch",
                )

        # ── Handle submission ──────────────────────────────────────────────────
        if submitted:
            current_mtype = st.session_state.get("woc_auto_machine_type", "")
            errors = _validate(selected_pid, current_mtype, selected_tech_type, assigned_technician)
            if errors:
                for err in errors:
                    st.error(err)
                st.session_state["woc_last_saved_id"] = None
            else:
                wo_id = db.insert_work_order(
                    product_id=selected_pid.strip(),
                    machine_type=current_mtype,
                    failure_type=failure_type,
                    priority=priority,
                    technician_type=selected_tech_type,
                    assigned_technician=assigned_technician.strip(),
                    description=description.strip(),
                    status=status,
                )
                st.session_state["woc_last_saved_id"] = wo_id
                _reset_form()
                st.rerun()

        if reset_clicked:
            st.session_state["woc_last_saved_id"] = None
            _reset_form()
            st.rerun()

    # ── Info / Tips panel ─────────────────────────────────────────────────────
    with col_info:
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px;
                        padding:18px 16px; font-size:0.83rem; color:#1e3a5f; line-height:1.7;">
                <div style="font-weight:700; font-size:0.9rem; margin-bottom:10px; color:#1d4ed8;">
                    Quick Guide
                </div>
                <ul style="margin:0; padding-left:16px;">
                    <li>Fields marked with <strong>*</strong> are required.</li>
                    <li>Select a <strong>Product ID</strong> — Machine Type fills automatically.</li>
                    <li>Select a <strong>Technician Type</strong> — the technician list updates.</li>
                    <li>Status defaults to <strong>Open</strong> on creation.</li>
                    <li>Use <em>Work Order Management</em> to update or delete.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                        padding:18px 16px; font-size:0.82rem; color:#1e293b; line-height:1.7;">
                <div style="font-weight:700; font-size:0.88rem; margin-bottom:10px; color:#334155;">
                    Failure Type Codes
                </div>
                <table style="width:100%; border-collapse:collapse;">
                    <tr><td style="color:#64748b; padding:3px 0; width:40%;">TWF</td><td style="font-weight:600;">Tool Wear</td></tr>
                    <tr><td style="color:#64748b; padding:3px 0;">HDF</td><td style="font-weight:600;">Heat Dissipation</td></tr>
                    <tr><td style="color:#64748b; padding:3px 0;">PWF</td><td style="font-weight:600;">Power Failure</td></tr>
                    <tr><td style="color:#64748b; padding:3px 0;">OSF</td><td style="font-weight:600;">Overstrain</td></tr>
                    <tr><td style="color:#64748b; padding:3px 0;">RNF</td><td style="font-weight:600;">Random Failure</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                        padding:18px 16px; font-size:0.82rem; color:#1e293b; line-height:1.7;">
                <div style="font-weight:700; font-size:0.88rem; margin-bottom:10px; color:#334155;">
                    Priority Levels
                </div>
                <table style="width:100%; border-collapse:collapse;">
                    <tr>
                        <td style="padding:4px 0;">
                            <span style="background:#dcfce7;color:#15803d;padding:2px 8px;
                                         border-radius:9999px;font-size:0.72rem;font-weight:700;">Low</span>
                        </td>
                        <td style="color:#64748b; padding-left:8px;">Routine maintenance</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0;">
                            <span style="background:#dbeafe;color:#1d4ed8;padding:2px 8px;
                                         border-radius:9999px;font-size:0.72rem;font-weight:700;">Medium</span>
                        </td>
                        <td style="color:#64748b; padding-left:8px;">Address soon</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0;">
                            <span style="background:#fef3c7;color:#92400e;padding:2px 8px;
                                         border-radius:9999px;font-size:0.72rem;font-weight:700;">High</span>
                        </td>
                        <td style="color:#64748b; padding-left:8px;">Urgent — escalate</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0;">
                            <span style="background:#fee2e2;color:#b91c1c;padding:2px 8px;
                                         border-radius:9999px;font-size:0.72rem;font-weight:700;">Critical</span>
                        </td>
                        <td style="color:#64748b; padding-left:8px;">Immediate action</td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
