"""
app.py — Main entry point for the Machine Failure Analysis Platform.
"""

import streamlit as st
from utils.styles import inject_css
from utils.data import load_data, filter_dataframe, compute_kpis
from utils import db
from utils import ollama_service

# Ensure SQLite tables exist before any page renders
db.init_db()

# ── Page Configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Machine Failure Analysis Platform",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Data Loading ──────────────────────────────────────────────────────────────

raw_df = load_data()

# ── Session State Defaults ────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "selected_machine_id" not in st.session_state:
    st.session_state["selected_machine_id"] = sorted(raw_df["Product ID"].unique().tolist())[0]
if "ai_reports"      not in st.session_state:
    st.session_state["ai_reports"] = {}
if "ai_report_metas" not in st.session_state:
    st.session_state["ai_report_metas"] = {}
if "chat_histories"  not in st.session_state:
    st.session_state["chat_histories"] = {}

# ── Ollama Auto-start ──────────────────────────────────────────────────────────────
# Run only once for the entire application lifecycle.
@st.cache_resource
def initialize_ollama():
    return ollama_service.ensure_ollama_running()

st.session_state["_ollama_available"] = initialize_ollama()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:

    # Brand / Logo
    st.markdown(
        """
        <div style="padding:4px 0 18px 0; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                <div style="font-size:1.5rem; line-height:1;">⚙️</div>
                <div>
                    <div style="font-size:1.0rem; font-weight:800; color:#ffffff; line-height:1.2;">
                        Machine Failure
                    </div>
                    <div style="font-size:0.78rem; font-weight:600; color:#93c5fd; line-height:1.2;">
                        Analysis Platform
                    </div>
                </div>
            </div>
            <div style="font-size:0.7rem; color:#64748b;">AI4I 2020 Predictive Maintenance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation buttons
    def _nav_to(page_key: str) -> None:
        st.session_state["page"] = page_key

    NAV_ITEMS = [
        ("dashboard",              "🏠  Dashboard"),
        ("analytics",              "📊  Data Analytics"),
        ("explorer",               "🔍  Machine Explorer"),
        ("ai_assistant",           "🤖  AI Assistant"),
        ("work_order_creation",    "🔧  Work Order Creation"),
        ("work_order_management",  "📋  Work Order Management"),
        ("preventive_maintenance", "🛡️  Preventive Maintenance"),
    ]

    # Ollama status warning (only shown when auto-start failed)
    if not st.session_state.get("_ollama_available", True):
        st.warning(
            "Ollama could not be started automatically. "
            "Please ensure Ollama is installed and available on your PATH.\n\n"
            "The AI Assistant will be unavailable until Ollama is running.",
            icon=None,
        )

    for key, label in NAV_ITEMS:
        btn_type = "primary" if st.session_state["page"] == key else "secondary"
        st.button(
            label,
            key=f"nav_{key}",
            type=btn_type,
            width="stretch",
            on_click=_nav_to,
            args=(key,),
        )

    st.markdown(
        '<hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:14px 0;">',
        unsafe_allow_html=True,
    )

    # Filters
    st.markdown(
        '<p style="font-size:0.7rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.09em; margin-bottom:8px;">Filters</p>',
        unsafe_allow_html=True,
    )

    machine_types = st.multiselect(
        "Machine Type",
        options=["L", "M", "H"],
        default=["L", "M", "H"],
        format_func=lambda t: {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}[t],
        key="filter_machine_types",
    )

    failure_status = st.radio(
        "Failure Status",
        options=["all", "failed", "no_failure"],
        format_func=lambda v: {
            "all":        "All Records",
            "failed":     "Failed Only",
            "no_failure": "Healthy Only",
        }[v],
        key="filter_failure_status",
    )

    # Apply filters
    filtered_df = filter_dataframe(
        raw_df,
        machine_types=machine_types if machine_types else None,
        failure_status=failure_status,
        failure_types=None,
    )

    st.markdown(
        f'<p style="font-size:0.75rem; color:#64748b; margin-top:6px;"><strong style="color:#93c5fd;">{len(filtered_df):,}</strong> records matched</p>',
        unsafe_allow_html=True,
    )



# ── Page Routing ──────────────────────────────────────────────────────────────

current_page = st.session_state.get("page", "dashboard")

if current_page == "dashboard":
    from pages import dashboard
    dashboard.render(filtered_df, raw_df)

elif current_page == "analytics":
    from pages import analytics
    analytics.render(filtered_df, raw_df)

elif current_page == "explorer":
    from pages import machine_explorer
    machine_explorer.render(raw_df, raw_df)

elif current_page == "ai_assistant":
    from pages import ai_assistant
    ai_assistant.render(raw_df, raw_df)

elif current_page == "work_order_creation":
    from pages import work_order_creation
    work_order_creation.render(raw_df)

elif current_page == "work_order_management":
    from pages import work_order_management
    work_order_management.render()

elif current_page == "preventive_maintenance":
    from pages import preventive_maintenance
    preventive_maintenance.render(raw_df)
