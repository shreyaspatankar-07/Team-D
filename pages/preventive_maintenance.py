"""
pages/preventive_maintenance.py — Preventive Maintenance Management (Module 7).

Tabs:
  1. Overview         — KPIs + Needs Attention + Upcoming + Recent
  2. Maintenance Plans— Create / edit PM plans + integrated Checklists + WO integration
  3. Calendar         — Month-grid calendar of scheduled maintenance dates
  4. Highest-Risk Machines — AI recommendations (filtered list)
"""

from __future__ import annotations

import math
import textwrap
from datetime import datetime, timedelta, date

import pandas as pd
import streamlit as st

from utils import db
from utils.styles import page_header, section_header, divider, COLORS
from utils.pm_ai import generate_fleet_recommendations, fleet_risk_summary, generate_machine_recommendation

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════

PM_STATUS_COLORS: dict[str, tuple[str, str]] = {
    "Scheduled":   ("#dbeafe", "#1d4ed8"),
    "Upcoming":    ("#fef3c7", "#92400e"),
    "In Progress": ("#e9d5ff", "#6d28d9"),
    "Completed":   ("#dcfce7", "#15803d"),
    "Overdue":     ("#fee2e2", "#b91c1c"),
}

PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "Low":      ("#dcfce7", "#15803d"),
    "Medium":   ("#dbeafe", "#1d4ed8"),
    "High":     ("#fef3c7", "#92400e"),
    "Critical": ("#fee2e2", "#b91c1c"),
}

MACHINE_TYPE_LABELS = {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}
TASK_OPTIONS = list(db.PM_DEFAULT_CHECKLISTS.keys())

# ══════════════════════════════════════════════════════════════════════════════
# HTML helpers
# ══════════════════════════════════════════════════════════════════════════════

def _kpi_card(label: str, value: int | str | float, color: str, icon: str = "") -> str:
    return textwrap.dedent(f"""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.05);
                border-top:3px solid {color};">
        <div style="font-size:0.7rem; font-weight:700; color:#64748b;
                    text-transform:uppercase; letter-spacing:0.07em; margin-bottom:6px;">
            {icon} {label}
        </div>
        <div style="font-size:1.9rem; font-weight:800; color:#1e293b; line-height:1;">
            {value if isinstance(value, str) else f'{value:,}' if isinstance(value, int) else str(value)}
        </div>
    </div>
    """)

def _compact_row_card(s: dict) -> str:
    """Compact HTML card for a single PM schedule used in Overview tab."""
    bg, tc = PM_STATUS_COLORS.get(s.get("status", "Scheduled"), ("#f1f5f9", "#475569"))
    pbg, ptc = PRIORITY_COLORS.get(s.get("priority", "Medium"), ("#f1f5f9", "#475569"))
    next_date = s.get("next_maintenance", "—")[:10]
    
    return textwrap.dedent(f"""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px;
                padding:10px 14px; margin-bottom:8px; display:flex; 
                justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; flex-direction:column; gap:2px;">
            <div style="font-size:0.85rem; font-weight:700; color:#1e293b;">
                {s.get('product_id','—')} &nbsp;·&nbsp; {s.get('task_name','—')}
            </div>
            <div style="font-size:0.75rem; color:#64748b;">
                👷 {s.get('assigned_technician','—')} &nbsp;·&nbsp; 📅 {next_date}
            </div>
        </div>
        <div style="display:flex; gap:6px;">
            <span style="background:{bg}; color:{tc}; padding:2px 8px; border-radius:9999px;
                         font-size:0.65rem; font-weight:700; text-transform:uppercase;">{s.get('status','—')}</span>
            <span style="background:{pbg}; color:{ptc}; padding:2px 8px; border-radius:9999px;
                         font-size:0.65rem; font-weight:700;">{s.get('priority','—')}</span>
        </div>
    </div>
    """)

def _schedule_row_card(s: dict) -> str:
    """HTML card for a single PM schedule in the Plans list view."""
    bg, tc = PM_STATUS_COLORS.get(s.get("status", "Scheduled"), ("#f1f5f9", "#475569"))
    pbg, ptc = PRIORITY_COLORS.get(s.get("priority", "Medium"), ("#f1f5f9", "#475569"))
    checklist_total = s.get("checklist_total", 0)
    checklist_done  = s.get("checklist_done", 0)
    pct = int(checklist_done / checklist_total * 100) if checklist_total > 0 else 0
    next_date = s.get("next_maintenance", "—")[:10]

    bar = (
        f'<div style="background:#e2e8f0; border-radius:4px; height:6px; overflow:hidden; margin-top:4px;">'
        f'<div style="background:#22c55e; width:{pct}%; height:100%; border-radius:4px;"></div>'
        f'</div>'
        f'<div style="font-size:0.68rem; color:#64748b; margin-top:2px;">{checklist_done}/{checklist_total} items</div>'
    ) if checklist_total > 0 else '<div style="font-size:0.68rem; color:#94a3b8;">No checklist</div>'

    wo_badge = (f'<span style="background:#f3e8ff; color:#7e22ce; padding:3px 10px;'
                f' border-radius:9999px; font-size:0.71rem; font-weight:700;">'
                f'WO #{s.get("work_order_id")}</span>') if s.get("work_order_id") else ''

    # Build via concatenation — avoids Markdown treating indented lines as code blocks
    return (
        '<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px;'
        ' padding:14px 16px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
        '<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">'
        '<div>'
        f'<div style="font-size:0.92rem; font-weight:700; color:#1e293b; margin-bottom:2px;">'
        f'{s.get("task_name","—")}'
        f'<span style="font-size:0.75rem; color:#64748b; font-weight:400; margin-left:6px;">'
        f'#{s.get("schedule_id","?")}</span></div>'
        f'<div style="font-size:0.78rem; color:#64748b;">'
        f'{s.get("product_id","—")} &nbsp;·&nbsp; {s.get("assigned_technician","—")} &nbsp;·&nbsp; {s.get("frequency","—")}'
        '</div>'
        '</div>'
        '<div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">'
        + wo_badge +
        f'<span style="background:{bg}; color:{tc}; padding:3px 10px; border-radius:9999px;'
        f' font-size:0.71rem; font-weight:700; text-transform:uppercase;">{s.get("status","—")}</span>'
        f'<span style="background:{pbg}; color:{ptc}; padding:3px 10px; border-radius:9999px;'
        f' font-size:0.71rem; font-weight:700;">{s.get("priority","—")}</span>'
        f'<span style="background:#f1f5f9; color:#475569; padding:3px 10px; border-radius:9999px;'
        f' font-size:0.71rem; font-weight:700;">{next_date}</span>'
        '</div>'
        '</div>'
        f'<div style="margin-top:8px;">{bar}</div>'
        '</div>'
    )

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1: Overview
# ══════════════════════════════════════════════════════════════════════════════

def _render_overview(raw_df: pd.DataFrame) -> None:
    section_header("Operational Overview", "Live preventive maintenance status.")

    kpis = db.fetch_pm_kpis()
    upcoming = kpis.get("upcoming_count", 0)
    overdue  = kpis.get("overdue_count", 0)
    in_prog  = kpis.get("in_progress_count", 0)
    comp_mo  = kpis.get("completed_this_month", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_kpi_card("Upcoming", upcoming, "#f59e0b", ""), unsafe_allow_html=True)
    c2.markdown(_kpi_card("Overdue", overdue, "#ef4444", ""), unsafe_allow_html=True)
    c3.markdown(_kpi_card("In Progress", in_prog, "#8b5cf6", ""), unsafe_allow_html=True)
    c4.markdown(_kpi_card("Completed This Month", comp_mo, "#22c55e", ""), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    all_schedules = db.fetch_all_pm_schedules()
    today = datetime.now().date()
    
    # Needs attention: Overdue, or due today, or In Progress but overdue (if possible)
    needs_attn = [s for s in all_schedules if s.get("status") == "Overdue" or s.get("next_maintenance", "").startswith(today.isoformat())]
    # Upcoming: within next 7 days, excluding needs attention
    upcoming_list = [s for s in all_schedules if s.get("status") in ("Upcoming", "Scheduled") and s not in needs_attn]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="font-size:1.1rem; font-weight:700; color:#1e293b; margin-bottom:12px;">Needs Attention</div>', unsafe_allow_html=True)
        if not needs_attn:
            st.success("No overdue or urgent tasks! 🎉")
        else:
            for s in needs_attn[:5]:
                st.markdown(_compact_row_card(s), unsafe_allow_html=True)
            if len(needs_attn) > 5:
                st.caption(f"...and {len(needs_attn)-5} more.")

    with col2:
        st.markdown('<div style="font-size:1.1rem; font-weight:700; color:#1e293b; margin-bottom:12px;">Upcoming Maintenance</div>', unsafe_allow_html=True)
        if not upcoming_list:
            st.info("No upcoming tasks in the next 7 days.")
        else:
            for s in upcoming_list[:5]:
                st.markdown(_compact_row_card(s), unsafe_allow_html=True)
            if len(upcoming_list) > 5:
                st.caption(f"...and {len(upcoming_list)-5} more.")

    st.markdown("<br>", unsafe_allow_html=True)
    divider()
    
    st.markdown('<div style="font-size:1.1rem; font-weight:700; color:#1e293b; margin-bottom:12px;">Recent Maintenance History</div>', unsafe_allow_html=True)
    history = db.fetch_pm_history()
    if not history:
        st.info("No completed maintenance records yet.")
    else:
        rows = []
        for h in history[:10]:
            total = h.get("checklist_total", 0)
            done  = h.get("checklist_done", 0)
            rows.append({
                "Date": h.get("completed_date", "")[:10],
                "Product ID": h.get("product_id", ""),
                "Task": h.get("task_name", ""),
                "Technician": h.get("assigned_technician", ""),
                "Checklist": f"{done}/{total}" if total > 0 else "N/A",
                "Work Order": f"#{h.get('work_order_id')}" if h.get("work_order_id") else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2: Maintenance Plans
# ══════════════════════════════════════════════════════════════════════════════

def _init_pm_form_state(raw_df: pd.DataFrame) -> None:
    # Apply prefill values from AI tab BEFORE widgets are created (only once per prefill)
    if st.session_state.pop("_pm_apply_prefill", False):
        st.session_state["pm_product_id"]  = st.session_state.pop("_pm_prefill_product_id", "")
        st.session_state["pm_task_name"]   = st.session_state.pop("_pm_prefill_task_name", TASK_OPTIONS[0])
        st.session_state["pm_priority"]    = st.session_state.pop("_pm_prefill_priority", "Medium")
        # Clear any leftover prefill keys
        st.session_state.pop("_pm_prefill_product_id", None)
        st.session_state.pop("_pm_prefill_task_name", None)
        st.session_state.pop("_pm_prefill_priority", None)

    defaults = {
        "pm_product_id":     "",
        "pm_task_name":      TASK_OPTIONS[0],
        "pm_frequency":      "Monthly",
        "pm_priority":       "Medium",
        "pm_tech_type":      db.TECHNICIAN_TYPES[0],
        "pm_technician":     "",
        "pm_description":    "",
        "pm_next_date":      (datetime.now().date() + timedelta(days=30)),
        "pm_form_version":   0,
        "pm_last_saved_id":  None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _render_plans_tab(raw_df: pd.DataFrame) -> None:
    _init_pm_form_state(raw_df)
    pid_to_type = dict(zip(raw_df["Product ID"], raw_df["Type"]))
    product_options = sorted(pid_to_type.keys())

    col_form, col_list = st.columns([2, 3], gap="large")

    with col_form:
        section_header("New Maintenance Plan", "Create a recurring preventive plan.")

        if st.session_state.get("pm_last_saved_id"):
            st.success(f"Plan #{st.session_state['pm_last_saved_id']} created.")

        sel_pid = st.selectbox("Product ID *", options=[""] + product_options, key="pm_product_id")
        auto_mtype = pid_to_type.get(sel_pid, "")
        
        task_name = st.selectbox("Maintenance Task *", options=TASK_OPTIONS, key="pm_task_name")
        
        fc1, fc2 = st.columns(2)
        with fc1:
            frequency = st.selectbox("Frequency *", db.PM_FREQUENCIES, key="pm_frequency")
        with fc2:
            priority = st.selectbox("Priority *", db.PRIORITIES, key="pm_priority")

        auto_next = datetime.now().date() + timedelta(days=db.PM_FREQUENCY_DAYS.get(frequency, 30))
        next_date = st.date_input("Next Maintenance Date *", value=st.session_state.get("pm_next_date", auto_next), min_value=date.today(), key=f"pm_next_date_input_{st.session_state.get('pm_form_version', 0)}")

        tech_type = st.selectbox("Technician Type *", db.TECHNICIAN_TYPES, key="pm_tech_type")
        avail_techs = db.TECHNICIANS.get(tech_type, [])
        technician = st.selectbox("Assigned Technician *", options=["— Select —"] + avail_techs, key=f"pm_tech_{tech_type}")

        description = st.text_area("Description", height=70, key="pm_description")

        if st.button("Save Plan", type="primary", key="pm_btn_save"):
            if not sel_pid or technician == "— Select —" or not technician:
                st.error("Product ID and Technician are required.")
            else:
                sid = db.insert_pm_schedule(
                    product_id=sel_pid, machine_type=auto_mtype, task_name=task_name, description=description.strip(),
                    frequency=frequency, technician_type=tech_type, assigned_technician=technician, priority=priority,
                    next_maintenance=next_date.isoformat()
                )
                st.session_state["pm_last_saved_id"] = sid
                for k in ["pm_product_id", "pm_description", "pm_form_version"]:
                    if k == "pm_form_version":
                        st.session_state[k] = st.session_state.get(k, 0) + 1
                    elif k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    with col_list:
        section_header("Maintenance Plans", "Manage recurring maintenance schedules.")
        all_schedules = db.fetch_all_pm_schedules()
        
        f1, f2 = st.columns(2)
        filter_status = f1.selectbox("Status Filter", ["All"] + db.PM_STATUSES, key="pln_filter_status")
        search_pid = f2.text_input("Search Product ID", placeholder="M12345", key="pln_search_pid")

        filtered = all_schedules
        if filter_status != "All":
            filtered = [s for s in filtered if s.get("status") == filter_status]
        if search_pid.strip():
            filtered = [s for s in filtered if search_pid.strip().upper() in s.get("product_id", "").upper()]

        if not filtered:
            st.info("No plans found.")
        else:
            for s in filtered:
                sid = s["schedule_id"]
                st.markdown(_schedule_row_card(s), unsafe_allow_html=True)
                with st.expander(f"Manage Plan #{sid}", expanded=False):
                    _render_plan_management(s, pid_to_type)

def _render_plan_management(s: dict, pid_to_type: dict) -> None:
    sid = s["schedule_id"]
    
    tab1, tab2, tab3 = st.tabs(["Details", "Checklist", "Work Order"])
    
    with tab1:
        st.markdown("**Edit Plan Details**")
        ec1, ec2 = st.columns(2)
        with ec1:
            e_status = st.selectbox("Status", db.PM_STATUSES, index=db.PM_STATUSES.index(s.get("status", "Scheduled")) if s.get("status") in db.PM_STATUSES else 0, key=f"e_status_{sid}")
            e_freq = st.selectbox("Frequency", db.PM_FREQUENCIES, index=db.PM_FREQUENCIES.index(s.get("frequency", "Monthly")) if s.get("frequency") in db.PM_FREQUENCIES else 4, key=f"e_freq_{sid}")
        with ec2:
            try: default_next = datetime.strptime(s.get("next_maintenance", "")[:10], "%Y-%m-%d").date()
            except: default_next = datetime.now().date() + timedelta(days=30)
            e_next_date = st.date_input("Next Date", value=default_next, key=f"e_next_{sid}")
            avail = db.TECHNICIANS.get(s.get("technician_type", db.TECHNICIAN_TYPES[0]), [])
            e_tech = st.selectbox("Technician", ["— Select —"] + avail, index=(["— Select —"] + avail).index(s.get("assigned_technician")) if s.get("assigned_technician") in avail else 0, key=f"e_tech_{sid}")

        if st.button("💾 Update Plan Details", key=f"btn_upd_{sid}"):
            db.update_pm_schedule(
                schedule_id=sid, product_id=s["product_id"], machine_type=s.get("machine_type", ""), task_name=s.get("task_name", ""),
                description=s.get("description", ""), frequency=e_freq, technician_type=s.get("technician_type", ""),
                assigned_technician=e_tech if e_tech != "— Select —" else s.get("assigned_technician", ""),
                priority=s.get("priority", ""), next_maintenance=e_next_date.isoformat(), last_maintenance=s.get("last_maintenance", ""),
                status=e_status, work_order_id=s.get("work_order_id")
            )
            st.success("Updated.")
            st.rerun()

    with tab2:
        items = db.fetch_checklist_items(sid)
        if not items:
            st.info("No checklist items.")
        else:
            for item in items:
                cid = item["checklist_id"]
                done_flag = bool(item.get("is_completed", 0))
                col_cb, col_text = st.columns([0.08, 0.92])
                with col_cb:
                    checked = st.checkbox(item["item_text"], value=done_flag, key=f"cl_item_{cid}", label_visibility="collapsed")
                    if checked != done_flag:
                        db.toggle_checklist_item(cid, checked)
                        st.rerun()
                with col_text:
                    style = "text-decoration:line-through; color:#94a3b8;" if done_flag else "color:#1e293b;"
                    st.markdown(f'<p style="margin:0; padding:6px 0; font-size:0.88rem; {style}">{item["item_text"]}</p>', unsafe_allow_html=True)
            
        c1, c2 = st.columns([2,1])
        new_item = c1.text_input("New checklist item", key=f"cl_new_item_{sid}")
        if c2.button("Add Item", key=f"cl_add_btn_{sid}"):
            if new_item.strip():
                db.add_checklist_item(sid, new_item.strip())
                st.rerun()
                
        divider()
        st.markdown("**Complete Maintenance Occurrence**")
        total = s.get("checklist_total", 0)
        done = s.get("checklist_done", 0)
        if done < total:
            st.warning(f"⚠ Only {done}/{total} items completed. You can still mark as completed, but it's recommended to finish the checklist.")
            
        if st.button("Log & Reschedule Maintenance", type="primary", key=f"cl_complete_{sid}"):
            today_str = datetime.now().date().isoformat()
            db.insert_pm_history(
                schedule_id=sid, product_id=s.get("product_id", ""), machine_type=s.get("machine_type", ""),
                task_name=s.get("task_name", ""), assigned_technician=s.get("assigned_technician", ""),
                completed_date=today_str, notes="Logged from plan view.", checklist_total=total, checklist_done=done,
                work_order_id=s.get("work_order_id")
            )
            next_date = db.compute_next_maintenance_date(s.get("frequency", "Monthly"), today_str)
            db.update_pm_schedule(
                schedule_id=sid, product_id=s["product_id"], machine_type=s.get("machine_type", ""), task_name=s.get("task_name", ""),
                description=s.get("description", ""), frequency=s.get("frequency", ""), technician_type=s.get("technician_type", ""),
                assigned_technician=s.get("assigned_technician", ""), priority=s.get("priority", ""), next_maintenance=next_date,
                last_maintenance=today_str, status="Scheduled", work_order_id=None
            )
            db.reset_pm_checklists(sid)
            st.success("Maintenance logged to history and rescheduled for next occurrence!")
            st.rerun()

    with tab3:
        if s.get("work_order_id"):
            st.info(f"🔧 **Work Order #{s['work_order_id']}** is linked to this maintenance plan.")
        else:
            st.markdown("**Generate Preventive Work Order**")
            wo_desc = st.text_area("Description", value=f"[Preventive] {s.get('task_name')} for {s.get('product_id')}.", height=70, key=f"wo_desc_{sid}")
            if st.button("Generate Work Order", type="primary", key=f"gen_wo_{sid}"):
                wo_id = db.insert_work_order(
                    product_id=s["product_id"], machine_type=s.get("machine_type", ""), failure_type="TWF",
                    priority=s.get("priority", "Medium"), technician_type=s.get("technician_type", ""),
                    assigned_technician=s.get("assigned_technician", ""), description=wo_desc.strip(), status="Open"
                )
                db.update_pm_schedule(
                    schedule_id=sid, product_id=s["product_id"], machine_type=s.get("machine_type", ""), task_name=s.get("task_name", ""),
                    description=s.get("description", ""), frequency=s.get("frequency", ""), technician_type=s.get("technician_type", ""),
                    assigned_technician=s.get("assigned_technician", ""), priority=s.get("priority", ""), next_maintenance=s.get("next_maintenance", ""),
                    last_maintenance=s.get("last_maintenance", ""), status=s.get("status", ""), work_order_id=wo_id
                )
                st.success(f"Work Order #{wo_id} created!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Tab 3: Calendar
# ══════════════════════════════════════════════════════════════════════════════

def _render_calendar_tab() -> None:
    section_header("Maintenance Calendar", "Monthly view of all scheduled PM activities.")

    today = datetime.now().date()
    all_schedules = db.fetch_all_pm_schedules()

    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = today.year
    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = today.month

    with nav_col1:
        if st.button("\u25c4 Previous Month", key="cal_prev"):
            m = st.session_state["cal_month"] - 1
            y = st.session_state["cal_year"]
            if m < 1: m, y = 12, y - 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y
    with nav_col2:
        st.markdown(f'<h3 style="text-align:center; margin:0; color:#1e293b;">{datetime(st.session_state["cal_year"], st.session_state["cal_month"], 1).strftime("%B %Y")}</h3>', unsafe_allow_html=True)
    with nav_col3:
        if st.button("Next Month \u25ba", key="cal_next"):
            m = st.session_state["cal_month"] + 1
            y = st.session_state["cal_year"]
            if m > 12: m, y = 1, y + 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y

    cal_year, cal_month = st.session_state["cal_year"], st.session_state["cal_month"]
    events_by_day = {}
    for s in all_schedules:
        try:
            nd_date = datetime.strptime(s.get("next_maintenance", "")[:10], "%Y-%m-%d").date()
            if nd_date.year == cal_year and nd_date.month == cal_month:
                events_by_day.setdefault(nd_date.day, []).append(s)
        except: pass

    first_day = date(cal_year, cal_month, 1)
    last_day = date(cal_year + 1, 1, 1) - timedelta(days=1) if cal_month == 12 else date(cal_year, cal_month + 1, 1) - timedelta(days=1)
    num_days, start_weekday = last_day.day, first_day.weekday()

    legend_html = '<div style="display:flex; gap:12px; margin:10px 0 14px 0; flex-wrap:wrap;">' + "".join([f'<span style="background:{bg}; color:{tc}; padding:2px 10px; border-radius:9999px; font-size:0.7rem; font-weight:700;">{k}</span>' for k, (bg, tc) in PM_STATUS_COLORS.items()]) + '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

    days_html = "".join([f'<div style="text-align:center; font-size:0.75rem; font-weight:700; color:#64748b; padding:6px 0; background:#f8fafc; border-radius:6px;">{d}</div>' for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]])
    cells = []
    day_num = 1
    for cell_idx in range(math.ceil((num_days + start_weekday) / 7) * 7):
        if cell_idx < start_weekday or day_num > num_days:
            cells.append('<div style="min-height:80px; background:#f8fafc; border-radius:8px;"></div>')
        else:
            is_today = (day_num == today.day and cal_year == today.year and cal_month == today.month)
            bg_cell, border = ("#eff6ff", "2px solid #3b82f6") if is_today else ("#ffffff", "1px solid #e2e8f0")
            events = events_by_day.get(day_num, [])
            events_html = "".join([f'<div style="background:{PM_STATUS_COLORS.get(ev.get("status", "Scheduled"), ("#dbeafe", "#1d4ed8"))[0]}; color:{PM_STATUS_COLORS.get(ev.get("status", "Scheduled"), ("#dbeafe", "#1d4ed8"))[1]}; font-size:0.62rem; font-weight:700; border-radius:4px; padding:1px 5px; margin-top:3px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">{ev.get("product_id", "")}: {ev.get("task_name", "")[:15]}</div>' for ev in events[:3]])
            if len(events) > 3: events_html += f'<div style="font-size:0.6rem; color:#94a3b8; margin-top:2px;">+{len(events) - 3} more</div>'
            cells.append(f'<div style="min-height:80px; background:{bg_cell}; border:{border}; border-radius:8px; padding:6px 8px;"><div style="font-size:0.8rem; font-weight:700; color:#1e293b;">{day_num}</div>{events_html}</div>')
            day_num += 1

    full_grid = '<div style="display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin-bottom:6px;">' + days_html + '</div>'
    for r in range(0, len(cells), 7): full_grid += '<div style="display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin-bottom:6px;">' + "".join(cells[r:r+7]) + '</div>'
    st.markdown(full_grid, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Tab 4: Highest-Risk Machines (AI)
# ══════════════════════════════════════════════════════════════════════════════

def _render_ai_recommendations_tab(raw_df: pd.DataFrame) -> None:
    section_header("Highest-Risk Machines", "Fleet analysis powered by ML health scores and failure predictions.")
    all_schedules = db.fetch_all_pm_schedules()

    top_n = st.slider("Number of top-risk machines to analyse", 5, 100, 20, 5, key="ai_rec_top_n")
    with st.spinner("Analyzing fleet health..."):
        recs = generate_fleet_recommendations(raw_df, all_schedules, top_n=top_n)

    if not recs: return st.info("No machines found.")

    urgency_filter = st.selectbox(
        "Filter by Urgency", ["All", "critical", "high", "medium", "low"],
        format_func=lambda u: {"All": "All Urgencies", "critical": "🔴 Critical", "high": "🟠 High", "medium": "🔵 Medium", "low": "🟢 Low"}.get(u, u),
        key="ai_urgency_filter"
    )
    filtered_recs = recs if urgency_filter == "All" else [r for r in recs if r.get("urgency") == urgency_filter]

    for rec in filtered_recs:
        tier, hs, fp = rec["risk_tier"], rec["health_score"], rec["failure_probability"]
        icon = '\U0001f534' if tier == 'Critical' else '\U0001f7e0' if tier == 'High' else '\U0001f535' if tier == 'Medium' else '\U0001f7e2'
        tier_bg = {'Critical': '#fee2e2', 'High': '#fef3c7', 'Medium': '#dbeafe', 'Low': '#dcfce7'}.get(tier, '#f1f5f9')
        tier_tc = {'Critical': '#b91c1c', 'High': '#92400e', 'Medium': '#1d4ed8', 'Low': '#15803d'}.get(tier, '#475569')

        reasons_html = ''.join(
            f'<div style="margin-bottom:3px;">&bull; {r}</div>'
            for r in rec['reasons']
        )
        tasks_html = ' '.join(
            f'<span style="background:#f1f5f9; color:#475569; padding:2px 8px;'
            f' border-radius:9999px; font-size:0.68rem; font-weight:600;">{t}</span>'
            for t in rec['suggested_tasks'][:4]
        )

        # st.container(border=True) IS the card — columns inside keep button visually inside
        with st.container(border=True):
            info_col, btn_col = st.columns([5, 1], gap="small")

            with info_col:
                # Tier-colored left accent bar + machine header
                st.markdown(
                    f'<div style="border-left:4px solid {tier_tc}; padding-left:10px; margin-bottom:6px;">'
                    f'  <span style="font-size:1.05rem; font-weight:800; color:#1e293b;">'
                    f'    {icon} Machine {rec["product_id"]}'
                    f'  </span>&nbsp;&nbsp;'
                    f'  <span style="background:{tier_bg}; color:{tier_tc};'
                    f'      padding:2px 10px; border-radius:9999px;'
                    f'      font-size:0.68rem; font-weight:700; text-transform:uppercase;">'
                    f'    {tier}'
                    f'  </span>&nbsp;&nbsp;'
                    f'  <span style="font-size:0.8rem; color:#64748b; font-weight:500;">'
                    f'    {rec["primary_action"]}'
                    f'  </span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex; gap:18px; margin-bottom:8px; flex-wrap:wrap;">'
                    f'  <span style="font-size:0.82rem; color:#475569;">'
                    f'    Health Score: <strong style="color:#1e293b;">{hs}/100</strong>'
                    f'  </span>'
                    f'  <span style="font-size:0.82rem; color:#475569;">'
                    f'    Failure Risk: <strong style="color:#1e293b;">{fp}%</strong>'
                    f'  </span>'
                    f'  <span style="font-size:0.82rem; color:#475569;">'
                    f'    Type: <strong style="color:#1e293b;">{rec["machine_type"]}</strong>'
                    f'  </span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="font-size:0.76rem; color:#64748b; margin-bottom:8px; line-height:1.7;">'
                    f'  {reasons_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex; flex-wrap:wrap; gap:5px;">'
                    f'  {tasks_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with btn_col:
                if rec["suggested_tasks"]:
                    prefill_pid      = rec['product_id']
                    prefill_task     = rec['suggested_tasks'][0]
                    prefill_priority = "Critical" if tier == "Critical" else "High" if tier == "High" else "Medium"

                    def _make_create_plan_cb(_pid=prefill_pid, _task=prefill_task, _prio=prefill_priority):
                        def _cb():
                            st.session_state["_pm_prefill_product_id"] = _pid
                            st.session_state["_pm_prefill_task_name"]  = _task
                            st.session_state["_pm_prefill_priority"]   = _prio
                            st.session_state["_pm_apply_prefill"]      = True
                            # Use the string label so st.tabs(key=) can switch to it
                            st.session_state["pm_active_tab"]          = "Maintenance Plans"
                        return _cb

                    # Push button to vertical center of the card
                    st.markdown("<div style='padding-top:22px;'>", unsafe_allow_html=True)
                    st.button(
                        "Create Plan",
                        key=f"ai_btn_{rec['product_id']}_{tier}",
                        on_click=_make_create_plan_cb(),
                        type="primary",
                        use_container_width=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Main render
# ══════════════════════════════════════════════════════════════════════════════

def render(raw_df: pd.DataFrame) -> None:
    db.refresh_pm_statuses()

    page_header("", "Preventive Maintenance Management", "Schedule, track, and optimise preventive maintenance with AI-powered recommendations.")

    tab_names = ["Overview", "Maintenance Plans", "Calendar", "Highest-Risk Machines"]

    # Normalise pm_active_tab to a valid string label so st.tabs(key=) can
    # switch to the correct tab when the Create Plan callback fires.
    active = st.session_state.get("pm_active_tab")
    if isinstance(active, int):
        active = tab_names[active] if 0 <= active < len(tab_names) else tab_names[0]
    if active not in tab_names:
        active = tab_names[0]
    st.session_state["pm_active_tab"] = active

    # key= is required for Streamlit to honour the pre-set session-state value
    tabs = st.tabs(tab_names, key="pm_active_tab")

    with tabs[0]: _render_overview(raw_df)
    with tabs[1]: _render_plans_tab(raw_df)
    with tabs[2]: _render_calendar_tab()
    with tabs[3]: _render_ai_recommendations_tab(raw_df)
