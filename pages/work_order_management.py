"""
pages/work_order_management.py — Work Order Management page (Module 6).

Features:
  - KPI cards (Total, Open, Assigned, In Progress, Completed, Closed)
  - Search (WO ID, Product ID, Failure Type, Technician Type, Technician)
  - Filters: Status, Priority, Machine Type, Failure Type, Technician Type,
    Assigned Technician — all combined with AND logic
  - Full work order table with inline Edit and Delete action buttons per row
  - Edit opens an inline expander form (editable: Priority, Technician Type,
    Assigned Technician, Status, Description)
  - Delete shows a two-step confirmation prompt, then removes from SQLite
  - KPI cards and table refresh automatically after every mutation

All DB operations are delegated to utils/db.py.
"""

import streamlit as st
import pandas as pd

from utils import db
from utils.styles import page_header, section_header, divider, COLORS


# ── Constants ──────────────────────────────────────────────────────────────────

MACHINE_TYPE_LABELS = {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}
FAILURE_TYPE_LABELS = {
    "TWF": "Tool Wear (TWF)",
    "HDF": "Heat Dissipation (HDF)",
    "PWF": "Power (PWF)",
    "OSF": "Overstrain (OSF)",
    "RNF": "Random (RNF)",
}

PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "Low":      ("#dcfce7", "#15803d"),
    "Medium":   ("#dbeafe", "#1d4ed8"),
    "High":     ("#fef3c7", "#92400e"),
    "Critical": ("#fee2e2", "#b91c1c"),
}

STATUS_COLORS: dict[str, tuple[str, str]] = {
    "Open":        ("#f1f5f9", "#475569"),
    "Assigned":    ("#dbeafe", "#1d4ed8"),
    "In Progress": ("#fef3c7", "#92400e"),
    "Completed":   ("#dcfce7", "#15803d"),
    "Closed":      ("#e9d5ff", "#6d28d9"),
}


# ── Badge helpers ──────────────────────────────────────────────────────────────

def _badge(text: str, color_map: dict, default: tuple = ("#f1f5f9", "#475569")) -> str:
    bg, tc = color_map.get(text, default)
    return (
        f'<span style="background:{bg}; color:{tc}; padding:3px 10px; '
        f'border-radius:9999px; font-size:0.71rem; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:0.04em; white-space:nowrap;">'
        f'{text}</span>'
    )


# ── KPI Cards ─────────────────────────────────────────────────────────────────

def _render_kpi_cards() -> None:
    """Fetch live counts from SQLite and render the 6 KPI metric cards."""
    kpis = db.fetch_kpis()

    kpi_defs = [
        ("📦 Total Orders",  kpis.get("total", 0),             "#3b82f6"),
        ("🟡 Open",          kpis.get("open_count", 0),        "#f59e0b"),
        ("🔵 Assigned",      kpis.get("assigned_count", 0),    "#3b82f6"),
        ("🔄 In Progress",   kpis.get("in_progress_count", 0), "#8b5cf6"),
        ("✅ Completed",     kpis.get("completed_count", 0),   "#22c55e"),
        ("🔒 Closed",        kpis.get("closed_count", 0),      "#64748b"),
    ]

    cols = st.columns(6)
    for col, (label, value, color) in zip(cols, kpi_defs):
        with col:
            col.markdown(
                f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                            padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.05);
                            border-top:3px solid {color};">
                    <div style="font-size:0.7rem; font-weight:700; color:#64748b;
                                text-transform:uppercase; letter-spacing:0.07em; margin-bottom:6px;">
                        {label}
                    </div>
                    <div style="font-size:1.9rem; font-weight:800; color:#1e293b; line-height:1;">
                        {value:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── Search & Filter helpers ───────────────────────────────────────────────────

def _apply_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Case-insensitive search across: WO ID, Product ID, Failure Type,
    Technician Type, and Assigned Technician.
    """
    if not query.strip():
        return df
    q = query.strip().lower()
    mask = (
        df["work_order_id"].astype(str).str.lower().str.contains(q)
        | df["product_id"].str.lower().str.contains(q)
        | df["failure_type"].str.lower().str.contains(q)
        | df["technician_type"].str.lower().str.contains(q)
        | df["assigned_technician"].str.lower().str.contains(q)
    )
    return df[mask]


def _apply_filters(
    df: pd.DataFrame,
    statuses: list[str],
    priorities: list[str],
    machine_types: list[str],
    failure_types: list[str],
    tech_types: list[str],
    technicians: list[str],
) -> pd.DataFrame:
    """Apply all active filters with AND logic."""
    if statuses:
        df = df[df["status"].isin(statuses)]
    if priorities:
        df = df[df["priority"].isin(priorities)]
    if machine_types:
        df = df[df["machine_type"].isin(machine_types)]
    if failure_types:
        df = df[df["failure_type"].isin(failure_types)]
    if tech_types:
        df = df[df["technician_type"].isin(tech_types)]
    if technicians:
        df = df[df["assigned_technician"].isin(technicians)]
    return df


# ── Inline Edit Panel ─────────────────────────────────────────────────────────

def _render_edit_panel(wo: dict) -> None:
    """
    Render an inline edit form inside a styled container.
    Editable fields: Priority, Technician Type, Assigned Technician,
    Status, Description.
    Non-editable (displayed as read-only): WO #, Product ID, Machine Type, Failure Type.
    """
    wo_id = int(wo["work_order_id"])

    # Two-step Technician Type → Technician selection (both outside sub-form)
    # Key is scoped to this WO so multiple panels can co-exist.
    tt_key    = f"edit_tech_type_{wo_id}"
    tech_key  = f"edit_technician_{wo_id}"

    # Initialise technician type key if needed
    if tt_key not in st.session_state:
        st.session_state[tt_key] = wo.get("technician_type", db.TECHNICIAN_TYPES[0])

    current_tt = st.session_state[tt_key]
    if current_tt not in db.TECHNICIAN_TYPES:
        current_tt = db.TECHNICIAN_TYPES[0]

    st.markdown(
        f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                    padding:20px 22px; margin:8px 0 16px 0;">
            <div style="font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase;
                        letter-spacing:0.06em; margin-bottom:14px;">
                ✏ Editing Work Order #{wo_id}
            </div>
            <div style="display:flex; gap:16px; flex-wrap:wrap; font-size:0.83rem; margin-bottom:14px;">
                <span style="color:#64748b;">Product: <strong style="color:#1e293b;">{wo['product_id']}</strong></span>
                <span style="color:#64748b;">Machine: <strong style="color:#1e293b;">{MACHINE_TYPE_LABELS.get(wo['machine_type'], wo['machine_type'])}</strong></span>
                <span style="color:#64748b;">Failure: <strong style="color:#1e293b;">{wo['failure_type']}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technician Type (outside form so it refreshes the technician list reactively)
    e1c1, e1c2 = st.columns(2)
    with e1c1:
        st.selectbox(
            "Technician Type",
            options=db.TECHNICIAN_TYPES,
            key=tt_key,
        )
    current_tt = st.session_state[tt_key]
    available  = db.TECHNICIANS.get(current_tt, [])

    # Determine safe index for assigned technician and initialise session state
    current_tech = wo.get("assigned_technician", "")
    tech_opts    = ["— Select —"] + available
    # Pre-populate the technician key so session state drives the widget
    if tech_key not in st.session_state:
        st.session_state[tech_key] = current_tech if current_tech in tech_opts else "— Select —"

    with e1c2:
        st.selectbox(
            "Assigned Technician",
            options=tech_opts,
            key=tech_key,
        )

    # The rest goes in a form so Save is explicit
    with st.form(key=f"edit_form_{wo_id}"):
        ef1, ef2 = st.columns(2)
        with ef1:
            # Pre-populate edit_priority key so session state drives the widget
            if f"edit_priority_{wo_id}" not in st.session_state:
                st.session_state[f"edit_priority_{wo_id}"] = wo["priority"] if wo["priority"] in db.PRIORITIES else db.PRIORITIES[0]
            new_priority = st.selectbox(
                "Priority",
                options=db.PRIORITIES,
                key=f"edit_priority_{wo_id}",
            )
        with ef2:
            # Pre-populate edit_status key so session state drives the widget
            if f"edit_status_{wo_id}" not in st.session_state:
                st.session_state[f"edit_status_{wo_id}"] = wo["status"] if wo["status"] in db.STATUSES else db.STATUSES[0]
            new_status = st.selectbox(
                "Status",
                options=db.STATUSES,
                key=f"edit_status_{wo_id}",
            )

        new_description = st.text_area(
            "Description",
            value=wo.get("description", ""),
            height=100,
            key=f"edit_desc_{wo_id}",
        )

        save_col, cancel_col, _ = st.columns([1, 1, 4])
        with save_col:
            save_clicked = st.form_submit_button("💾 Save", type="primary", width="stretch")
        with cancel_col:
            cancel_clicked = st.form_submit_button("✖ Cancel", type="secondary", width="stretch")

    if save_clicked:
        new_tech = st.session_state.get(tech_key, "")
        if not new_tech or new_tech == "— Select —":
            st.error("Please select an Assigned Technician before saving.")
        else:
            db.update_work_order(
                work_order_id=wo_id,
                product_id=wo["product_id"],
                machine_type=wo["machine_type"],
                failure_type=wo["failure_type"],
                priority=new_priority,
                technician_type=current_tt,
                assigned_technician=new_tech,
                description=new_description.strip(),
                status=new_status,
            )
            st.success(f"Work Order #{wo_id} updated successfully.")
            # Close the edit panel and refresh
            st.session_state.pop(f"wom_edit_open_{wo_id}", None)
            st.rerun()

    if cancel_clicked:
        st.session_state.pop(f"wom_edit_open_{wo_id}", None)
        st.rerun()


# ── Action Rows (table + per-row Edit/Delete) ─────────────────────────────────

def _render_action_table(df_filtered: pd.DataFrame) -> None:
    """
    Render the work order table with an Edit and Delete button on each row.
    Edit opens an inline editor below the row.
    Delete shows a two-step confirmation.
    """
    if df_filtered.empty:
        st.info("No work orders match the current search / filter criteria.")
        return

    # ── Column headers ─────────────────────────────────────────────────────────
    hdr_cols = st.columns([0.6, 1.2, 1, 1, 1, 1.6, 1.4, 1.4, 1, 0.8, 0.8])
    headers  = ["WO #", "Product ID", "Type", "Failure", "Priority",
                "Tech Type", "Technician", "Status", "Created", "Edit", "Delete"]
    for hdr_col, header in zip(hdr_cols, headers):
        hdr_col.markdown(
            f'<span style="font-size:0.7rem; font-weight:700; color:#64748b; '
            f'text-transform:uppercase; letter-spacing:0.06em;">{header}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<hr style="border:none; border-top:1px solid #e2e8f0; margin:4px 0 6px 0;">',
        unsafe_allow_html=True,
    )

    # ── One row per work order ─────────────────────────────────────────────────
    for _, row in df_filtered.iterrows():
        wo_id = int(row["work_order_id"])
        edit_open_key    = f"wom_edit_open_{wo_id}"
        confirm_del_key  = f"wom_confirm_del_{wo_id}"

        c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns(
            [0.6, 1.2, 1, 1, 1, 1.6, 1.4, 1.4, 1, 0.8, 0.8]
        )

        c0.markdown(
            f'<span style="font-weight:700; color:#1e293b; font-size:0.85rem;">#{wo_id}</span>',
            unsafe_allow_html=True,
        )
        c1.markdown(
            f'<span style="font-size:0.85rem; color:#334155;">{row["product_id"]}</span>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<span style="font-size:0.85rem; color:#334155;">'
            f'{MACHINE_TYPE_LABELS.get(row["machine_type"], row["machine_type"])}</span>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<span style="font-size:0.85rem; color:#334155;">{row["failure_type"]}</span>',
            unsafe_allow_html=True,
        )
        c4.markdown(_badge(row["priority"], PRIORITY_COLORS), unsafe_allow_html=True)
        c5.markdown(
            f'<span style="font-size:0.78rem; color:#475569;">{row["technician_type"]}</span>',
            unsafe_allow_html=True,
        )
        c6.markdown(
            f'<span style="font-size:0.82rem; color:#334155; font-weight:500;">'
            f'{row["assigned_technician"]}</span>',
            unsafe_allow_html=True,
        )
        c7.markdown(_badge(row["status"], STATUS_COLORS), unsafe_allow_html=True)
        # Show only the date part (first 10 chars of ISO timestamp)
        c8.markdown(
            f'<span style="font-size:0.78rem; color:#64748b;">{str(row["created_date"])[:10]}</span>',
            unsafe_allow_html=True,
        )

        # Edit button — toggles the inline editor
        with c9:
            edit_label = "✏" if not st.session_state.get(edit_open_key) else "▲"
            if st.button(edit_label, key=f"wom_edit_btn_{wo_id}", help="Edit this work order"):
                # Toggle
                if st.session_state.get(edit_open_key):
                    st.session_state.pop(edit_open_key, None)
                else:
                    st.session_state[edit_open_key] = True
                    # Close any other open editors
                    for k in list(st.session_state.keys()):
                        if k.startswith("wom_edit_open_") and k != edit_open_key:
                            del st.session_state[k]
                st.rerun()

        # Delete button
        with c10:
            if st.button("🗑", key=f"wom_del_btn_{wo_id}", help="Delete this work order"):
                # Toggle confirmation
                if st.session_state.get(confirm_del_key):
                    st.session_state.pop(confirm_del_key, None)
                else:
                    st.session_state[confirm_del_key] = True
                    # Close any open edit panels
                    for k in list(st.session_state.keys()):
                        if k.startswith("wom_edit_open_"):
                            del st.session_state[k]
                st.rerun()

        # ── Inline edit panel (shown when this row's edit is open) ────────────
        if st.session_state.get(edit_open_key):
            _render_edit_panel(dict(row))

        # ── Delete confirmation (shown below the row) ──────────────────────────
        if st.session_state.get(confirm_del_key):
            st.warning(
                f"⚠ Permanently delete Work Order **#{wo_id}** "
                f"({row['product_id']} — {row['assigned_technician']})? "
                "This cannot be undone.",
            )
            y_col, n_col, _ = st.columns([1, 1, 6])
            with y_col:
                if st.button(
                    "✅ Confirm Delete",
                    key=f"wom_yes_del_{wo_id}",
                    type="primary",
                    width="stretch",
                ):
                    db.delete_work_order(wo_id)
                    st.session_state.pop(confirm_del_key, None)
                    st.success(f"Work Order #{wo_id} deleted.")
                    st.rerun()
            with n_col:
                if st.button("❌ Cancel", key=f"wom_no_del_{wo_id}", width="stretch"):
                    st.session_state.pop(confirm_del_key, None)
                    st.rerun()

        st.markdown(
            '<hr style="border:none; border-top:1px solid #f1f5f9; margin:2px 0;">',
            unsafe_allow_html=True,
        )


# ── Main render ───────────────────────────────────────────────────────────────

def render() -> None:
    """Render the complete Work Order Management page."""

    page_header(
        "📋",
        "Work Order Management",
        "View, search, filter, update, and delete maintenance work orders.",
    )

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    section_header("Overview", "Live counts across all work orders in the database.")
    _render_kpi_cards()

    divider()

    # ── Load data ─────────────────────────────────────────────────────────────
    all_orders = db.fetch_all_work_orders()

    if not all_orders:
        st.info(
            "📭 No work orders found. Use the **Work Order Creation** page to add your first record.",
            icon=None,
        )
        return

    df_all = pd.DataFrame(all_orders)
    # Ensure technician_type column exists (backward-compat for old rows)
    if "technician_type" not in df_all.columns:
        df_all["technician_type"] = ""

    # ── Search + Filter Controls ───────────────────────────────────────────────
    section_header("Search & Filter", "Narrow down work orders using the controls below.")

    search_col, _ = st.columns([3, 1])
    with search_col:
        search_query = st.text_input(
            "🔍 Search",
            placeholder="Search by WO ID, Product ID, Failure Type, Technician Type, or Technician…",
            key="wom_search",
            label_visibility="collapsed",
        )

    # Filter row 1 — Status, Priority, Machine Type, Failure Type
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filter_status = st.multiselect(
            "Status", options=db.STATUSES, key="wom_filter_status", placeholder="All Statuses"
        )
    with f2:
        filter_priority = st.multiselect(
            "Priority", options=db.PRIORITIES, key="wom_filter_priority", placeholder="All Priorities"
        )
    with f3:
        filter_machine = st.multiselect(
            "Machine Type",
            options=db.MACHINE_TYPES,
            format_func=lambda t: MACHINE_TYPE_LABELS.get(t, t),
            key="wom_filter_machine",
            placeholder="All Types",
        )
    with f4:
        filter_failure = st.multiselect(
            "Failure Type",
            options=db.FAILURE_TYPES,
            format_func=lambda ft: FAILURE_TYPE_LABELS.get(ft, ft),
            key="wom_filter_failure",
            placeholder="All Failures",
        )

    # Filter row 2 — Technician Type + Assigned Technician (dynamic)
    ft1, ft2 = st.columns(2)
    with ft1:
        filter_tech_type = st.multiselect(
            "Technician Type",
            options=db.TECHNICIAN_TYPES,
            key="wom_filter_tech_type",
            placeholder="All Technician Types",
        )
    with ft2:
        # If a Technician Type filter is active, narrow the technician options
        if filter_tech_type:
            tech_pool = [n for tt in filter_tech_type for n in db.TECHNICIANS.get(tt, [])]
        else:
            tech_pool = db.ALL_TECHNICIANS
        filter_technician = st.multiselect(
            "Assigned Technician",
            options=tech_pool,
            key="wom_filter_technician",
            placeholder="All Technicians",
        )

    # Apply search then all filters
    df_filtered = _apply_search(df_all, search_query)
    df_filtered = _apply_filters(
        df_filtered,
        statuses=filter_status,
        priorities=filter_priority,
        machine_types=filter_machine,
        failure_types=filter_failure,
        tech_types=filter_tech_type,
        technicians=filter_technician,
    )

    # Results summary
    st.markdown(
        f'<p style="font-size:0.8rem; color:#64748b; margin:6px 0 14px 0;">'
        f'Showing <strong>{len(df_filtered):,}</strong> of '
        f'<strong>{len(df_all):,}</strong> work orders.</p>',
        unsafe_allow_html=True,
    )

    divider()

    # ── Work Orders Table with Inline Actions ──────────────────────────────────
    section_header(
        "Work Orders",
        f"{len(df_filtered):,} record{'s' if len(df_filtered) != 1 else ''} shown. "
        "Use ✏ to edit and 🗑 to delete.",
    )

    _render_action_table(df_filtered)

    # ── CSV Export ─────────────────────────────────────────────────────────────
    if not df_filtered.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        export_df = df_filtered[[
            "work_order_id", "product_id", "machine_type", "failure_type",
            "priority", "technician_type", "assigned_technician",
            "status", "created_date", "updated_date",
        ]].copy()
        export_df.rename(columns={
            "work_order_id": "WO #", "product_id": "Product ID",
            "machine_type": "Machine Type", "failure_type": "Failure Type",
            "priority": "Priority", "technician_type": "Technician Type",
            "assigned_technician": "Technician", "status": "Status",
            "created_date": "Created", "updated_date": "Last Updated",
        }, inplace=True)
        st.download_button(
            label="⬇ Export to CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="work_orders_export.csv",
            mime="text/csv",
            key="wom_export_btn",
        )
