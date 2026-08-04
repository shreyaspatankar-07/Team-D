from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ai import OLLAMA_MODEL, ask_maintenance_assistant, get_available_models, machine_context, preventive_maintenance_context, stream_maintenance_report
from work_orders import VALID_FREQUENCIES, VALID_PRIORITIES, VALID_STATUSES, add_checklist_item, create_schedule, create_work_order, delete_work_order, failure_details, generate_due_work_orders, get_checklist, get_checklist_progress, get_maintenance_history, get_schedules, get_schedule_work_orders, get_work_orders, initialise_work_orders, record_maintenance_completion, required_checklist_complete, set_checklist_item, update_work_order


DATA_FILE = Path("ai4i2020.csv")
STATUS_COLORS = {"Healthy": "#2f6f73", "Failed": "#d95f4f"}
TYPE_COLORS = {"L": "#75c893", "M": "#f0b35c", "H": "#6d8fd6"}
FAILURE_MODES = {
    "TWF": "Tool wear",
    "HDF": "Heat dissipation",
    "PWF": "Power",
    "OSF": "Overstrain",
    "RNF": "Random",
}


st.set_page_config(
    page_title="Machine Failure Analysis",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #17212f;
        --muted: #6b7280;
        --line: #e5e7eb;
        --paper: #ffffff;
        --wash: #eff6f4;
        --accent: #2f6f73;
        --danger: #d95f4f;
    }
    .stApp {
        --background-color: #f7faf9;
        --secondary-background-color: #ffffff;
        --text-color: #17212f;
        --primary-color: #2f6f73;
        --border-color: #cbd5d1;
        background: linear-gradient(135deg, #d7e9e5 0%, #f7faf9 42%, #eef3f0 100%);
        color-scheme: light;
    }
    .block-container { max-width: 1320px; padding: 4.8rem 2.4rem 3.4rem; }
    header[data-testid="stHeader"] { background: rgba(255,255,255,.98) !important; border-bottom: 1px solid #d8e1df; }
    header[data-testid="stHeader"] button, header[data-testid="stHeader"] button * { color: #17212f !important; }
    header[data-testid="stHeader"] button svg { fill: #17212f !important; stroke: #17212f !important; }
    [data-testid="stMainMenu"], [data-testid="stMainMenu"] > div,
    [data-testid="stMainMenu"] [role="menu"] { background: #ffffff !important; border-color: #d8e1df !important; }
    [data-testid="stMainMenu"] *, [data-testid="stMainMenu"] button,
    [data-testid="stMainMenu"] button * { color: #17212f !important; }
    [data-testid="stMainMenu"] button svg { fill: #17212f !important; stroke: #17212f !important; }
    [data-testid="stSidebar"] { background: #171c2b; border-right: 1px solid rgba(255,255,255,.08); }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] [data-baseweb="tag"] { background: #2f6f73; }
    .shell {
        background: rgba(255,255,255,.86);
        border: 1px solid rgba(255,255,255,.72);
        border-radius: 22px;
        box-shadow: 0 24px 70px rgba(23,33,47,.16);
        padding: 1.35rem;
    }
    .hero {
        display: flex;
        justify-content: space-between;
        gap: 1.25rem;
        align-items: flex-start;
        padding: .25rem .15rem 1rem;
    }
    .eyebrow { color: var(--accent); font-size: .74rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    .hero h1 { color: var(--ink); font-size: 2.05rem; line-height: 1.05; margin: .2rem 0 .35rem; letter-spacing: 0; }
    .hero p { color: var(--muted); max-width: 720px; margin: 0; font-size: .96rem; }
    .badge {
        color: var(--ink);
        background: #e9f4f0;
        border: 1px solid #cbe2dc;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 750;
        padding: .55rem .8rem;
        white-space: nowrap;
    }
    .kpi {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem;
        min-height: 124px;
        box-shadow: 0 10px 28px rgba(23,33,47,.06);
    }
    .kpi small { display:block; color: var(--muted); font-size:.73rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .kpi strong { display:block; color: var(--ink); font-size:1.8rem; line-height:1.1; margin:.45rem 0 .25rem; }
    .kpi span { color: var(--muted); font-size:.82rem; }
    .kpi.warn strong { color: var(--danger); }
    .panel {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1rem .55rem;
        box-shadow: 0 10px 28px rgba(23,33,47,.05);
    }
    .panel-title {
        color: var(--ink);
        font-size: .84rem;
        font-weight: 850;
        letter-spacing: .05em;
        text-transform: uppercase;
        margin-bottom: .35rem;
    }
    .insight {
        background: #17212f;
        color: white;
        border-radius: 16px;
        padding: 1rem;
        min-height: 122px;
    }
    .insight small { color: #9fb3b1; font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .insight strong { display:block; font-size:1.45rem; margin:.38rem 0 .2rem; }
    .insight span { color:#dbe7e4; font-size:.85rem; }
    .explorer-status {
        border-radius: 16px; padding: 1rem 1.1rem; margin: .2rem 0 .15rem;
        border: 1px solid var(--line); background: #f8fafc;
    }
    .explorer-status.healthy { background:#e9f4f0; border-color:#cbe2dc; }
    .explorer-status.attention { background:#fff6e7; border-color:#f3d7a6; }
    .explorer-status.critical { background:#fff0ed; border-color:#f2c3ba; }
    .explorer-status small { color:var(--muted); font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .explorer-status strong { display:block; color:var(--ink); font-size:1.55rem; margin:.22rem 0; }
    .explorer-status p { color:var(--muted); font-size:.87rem; margin:0; }
    .sensor-label { color:var(--ink); font-size:.82rem; font-weight:800; text-align:center; margin-top:.15rem; }
    .sensor-note { color:var(--muted); font-size:.72rem; text-align:center; margin-top:-.25rem; }
    .mode-chip { display:inline-block; border-radius:999px; padding:.46rem .7rem; margin:.16rem .25rem .1rem 0; font-size:.78rem; font-weight:700; }
    .mode-chip.normal { color:#246b5a; background:#e9f4f0; border:1px solid #cbe2dc; }
    .mode-chip.triggered { color:#a43b2d; background:#fff0ed; border:1px solid #f2c3ba; }
    .assistant-note { color:var(--muted); font-size:.84rem; line-height:1.55; }
    .assistant-ready { color:#246b5a; background:#e9f4f0; border:1px solid #cbe2dc; border-radius:999px; padding:.42rem .7rem; font-size:.76rem; font-weight:800; }
    .assistant-offline { color:#a43b2d; background:#fff0ed; border:1px solid #f2c3ba; border-radius:999px; padding:.42rem .7rem; font-size:.76rem; font-weight:800; }
    .signal-card { background:#f8fafc; border:1px solid var(--line); border-left:4px solid #2f6f73; border-radius:12px; padding:.76rem .8rem; min-height:96px; }
    .signal-card.attention { border-left-color:#f0a11a; background:#fffaf0; }
    .signal-card.critical { border-left-color:#d95f4f; background:#fff5f3; }
    .signal-card small { display:block; color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    .signal-card strong { display:block; color:var(--ink); font-size:1.18rem; margin:.28rem 0 .14rem; }
    .signal-card span { color:var(--muted); font-size:.74rem; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border: 1px solid #cbd5d1 !important;
        border-radius: 16px !important;
        box-shadow: 0 0 0 1px #cbd5d1, 0 12px 30px rgba(23,33,47,.08) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div { padding: 1rem !important; }
    /* Keep the intentionally light dashboard surfaces legible when Streamlit uses a dark theme. */
    [data-testid="stAppViewContainer"] { color: var(--ink); }
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] .stAlert p { color: var(--ink) !important; }
    [data-testid="stAppViewContainer"] [data-baseweb="input"] input,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
    [data-testid="stAppViewContainer"] [data-baseweb="base-input"] {
        color: var(--ink) !important; background: #ffffff !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] svg { fill: var(--ink) !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background: #ffffff !important; }
    [data-baseweb="popover"] *, [data-baseweb="menu"] *, [role="listbox"] *, [role="option"] { color: var(--ink) !important; }
    [role="option"] { background: #ffffff !important; }
    [role="option"][aria-selected="true"], [role="option"]:hover { background: #e9f4f0 !important; }
    [data-testid="stAppViewContainer"] [data-testid="stDataFrame"] * { color: var(--ink) !important; }
    [data-testid="stAppViewContainer"] [data-testid="stDataFrame"] {
        --background-color: #ffffff !important;
        --secondary-background-color: #f8fafc !important;
        --text-color: #17212f !important;
        --border-color: #d8e1df !important;
        background: #ffffff !important;
        color-scheme: light !important;
    }
    /* Plotly SVG labels otherwise inherit low-contrast dark-theme text colors. */
    [data-testid="stAppViewContainer"] .js-plotly-plot .xtick text,
    [data-testid="stAppViewContainer"] .js-plotly-plot .ytick text,
    [data-testid="stAppViewContainer"] .js-plotly-plot .legendtext,
    [data-testid="stAppViewContainer"] .js-plotly-plot .gtitle text,
    [data-testid="stAppViewContainer"] .js-plotly-plot .axis-title text { fill: #17212f !important; }
    .section-gap { height: .7rem; }
    div[data-testid="stVerticalBlock"] { gap: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_FILE)
    data["Status"] = data["Machine failure"].map({0: "Healthy", 1: "Failed"})
    data["Temperature gap [K]"] = data["Process temperature [K]"] - data["Air temperature [K]"]
    data["Workload"] = data["Rotational speed [rpm]"] * data["Torque [Nm]"] / 1000
    return data


def metric_card(label: str, value: str, note: str, warn: bool = False) -> None:
    st.markdown(
        f"""
        <div class="kpi {'warn' if warn else ''}">
            <small>{label}</small>
            <strong>{value}</strong>
            <span>{note}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_chart(fig, height: int = 320) -> None:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=12, t=36, b=30),
        font=dict(family="Inter, Segoe UI, Arial", size=12, color="#17212f"),
        legend=dict(title_text="", font=dict(color="#17212f")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#17212f"), title_font=dict(color="#17212f"))
    fig.update_yaxes(gridcolor="#edf1f0", zeroline=False, tickfont=dict(color="#17212f"), title_font=dict(color="#17212f"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_eda(data: pd.DataFrame, full_data: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div>
                <div class="eyebrow">Module 1</div>
                <h1>Data Analysis (EDA)</h1>
                <p>Loaded dataset, null-value review, descriptive statistics, correlation analysis, heatmap, and histograms for the AI4I maintenance records.</p>
            </div>
            <div class="badge">{len(data):,} filtered rows</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card("Rows loaded", f"{len(full_data):,}", "Original dataset")
    with c2:
        metric_card("Columns", f"{full_data.shape[1]:,}", "Including derived fields")
    with c3:
        metric_card("Null values", f"{int(full_data.isna().sum().sum()):,}", "Across all columns")
    with c4:
        metric_card("Numeric fields", f"{len(full_data.select_dtypes('number').columns):,}", "For statistics")

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 1], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Loaded dataset</div>', unsafe_allow_html=True)
            st.dataframe(data.head(25), width="stretch", hide_index=True)
    with right:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Checked null values</div>', unsafe_allow_html=True)
            nulls = (
                full_data.isna()
                .sum()
                .rename("Missing values")
                .reset_index()
                .rename(columns={"index": "Column"})
            )
            st.dataframe(nulls, width="stretch", hide_index=True)

    with st.container(border=True):
        st.markdown('<div class="panel-title">Descriptive statistics</div>', unsafe_allow_html=True)
        st.dataframe(data.describe(include="all").transpose(), width="stretch")

    numeric_cols = data.select_dtypes("number").columns.tolist()
    default_corr = [
        col
        for col in [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
            "Temperature gap [K]",
            "Workload",
            "Machine failure",
        ]
        if col in numeric_cols
    ]

    heatmap_col, corr_col = st.columns([1.15, 1], gap="medium")
    with heatmap_col:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Heatmap</div>', unsafe_allow_html=True)
            selected_corr_cols = st.multiselect(
                "Correlation fields", numeric_cols, default=default_corr, key="eda_corr_cols"
            )
            if len(selected_corr_cols) >= 2:
                corr = data[selected_corr_cols].corr()
                fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                fig.update_layout(coloraxis_colorbar=dict(thickness=10), xaxis_tickangle=-35)
                show_chart(fig, 420)
            else:
                st.info("Select at least two numeric fields for the correlation heatmap.")
    with corr_col:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Correlation analysis</div>', unsafe_allow_html=True)
            if len(default_corr) >= 2:
                corr_pairs = (
                    data[default_corr].corr()["Machine failure"].drop("Machine failure", errors="ignore")
                    .sort_values(key=lambda series: series.abs(), ascending=False).rename("Correlation with failure")
                    .reset_index().rename(columns={"index": "Feature"})
                )
                st.dataframe(corr_pairs, width="stretch", hide_index=True)
            else:
                st.info("Not enough numeric fields for correlation analysis.")

    histogram_options = [
        col
        for col in [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
            "Temperature gap [K]",
            "Workload",
        ]
        if col in numeric_cols
    ]
    with st.container(border=True):
        st.markdown('<div class="panel-title">Histograms</div>', unsafe_allow_html=True)
        selected_hist_cols = st.multiselect(
            "Histogram fields", histogram_options, default=histogram_options[:4], key="eda_hist_cols"
        )
        if selected_hist_cols:
            hist_cols = st.columns(2, gap="medium")
            for index, column in enumerate(selected_hist_cols):
                with hist_cols[index % 2]:
                    fig = px.histogram(data, x=column, color="Status", nbins=35, color_discrete_map=STATUS_COLORS)
                    fig.update_layout(xaxis_title=column, yaxis_title="Records")
                    show_chart(fig, 300)
        else:
            st.info("Select at least one field to display histograms.")

def render_dashboard(data: pd.DataFrame) -> None:
    total = len(data)
    failures = int(data["Machine failure"].sum())
    healthy = total - failures
    failure_rate = failures / total * 100
    avg_wear = data["Tool wear [min]"].mean()

    type_summary = (
        data.groupby("Type", as_index=False)
        .agg(machines=("UDI", "count"), failures=("Machine failure", "sum"), wear=("Tool wear [min]", "mean"))
        .assign(failure_rate=lambda values: values["failures"] / values["machines"] * 100)
    )
    risk_type = type_summary.sort_values("failure_rate", ascending=False).iloc[0]

    st.markdown(
        f"""
        <section class="hero">
            <div>
                <div class="eyebrow">Module 2</div>
                <h1>Machine Failure Dashboard</h1>
                <p>Interactive maintenance overview with KPI cards, sidebar filters, Plotly charts, failure distribution, machine type distribution, and RPM/tool-wear analysis.</p>
            </div>
            <div class="badge">{total:,} selected records</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5 = st.columns([1, 1, 1, 1, 1.25], gap="medium")
    with k1:
        metric_card("Machines", f"{total:,}", "Filtered population")
    with k2:
        metric_card("Healthy", f"{healthy:,}", "Machines without failure")
    with k3:
        metric_card("Failures", f"{failures:,}", "Failure events", warn=failures > 0)
    with k4:
        metric_card("Avg wear", f"{avg_wear:.0f} min", "Tool wear")
    with k5:
        st.markdown(
            f"""
            <div class="insight">
                <small>Highest risk type</small>
                <strong>Type {risk_type['Type']} - {risk_type['failure_rate']:.2f}%</strong>
                <span>{int(risk_type['failures'])} failures across {int(risk_type['machines']):,} machines</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    data = data.copy()
    data["Segment"] = pd.qcut(data["UDI"], q=min(12, data["UDI"].nunique()), duplicates="drop", labels=False) + 1
    trend = (
        data.groupby("Segment", as_index=False)
        .agg(failure_rate=("Machine failure", "mean"), avg_wear=("Tool wear [min]", "mean"))
        .assign(failure_rate=lambda values: values["failure_rate"] * 100)
    )
    mode_counts = pd.Series({name: int(data[col].sum()) for col, name in FAILURE_MODES.items()}).reset_index()
    mode_counts.columns = ["Failure mode", "Count"]

    left, right = st.columns([1.6, 1], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Failure rate trend</div>', unsafe_allow_html=True)
            fig = px.line(trend, x="Segment", y="failure_rate", markers=True)
            fig.update_traces(line_color="#2f6f73", marker=dict(size=8, color="#d95f4f"))
            fig.update_layout(xaxis_title="Production segment", yaxis_title="Failure rate (%)")
            show_chart(fig, 330)
    with right:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Machine failure distribution</div>', unsafe_allow_html=True)
            counts = data["Status"].value_counts().rename_axis("Status").reset_index(name="Machines")
            fig = px.pie(counts, names="Status", values="Machines", hole=0.62, color="Status", color_discrete_map=STATUS_COLORS)
            fig.update_traces(textinfo="percent+label", textposition="inside")
            show_chart(fig, 330)

    mid_left, mid_right = st.columns([1, 1.35], gap="medium")
    with mid_left:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Failure modes</div>', unsafe_allow_html=True)
            fig = px.bar(mode_counts.sort_values("Count"), x="Count", y="Failure mode", orientation="h", text_auto=True)
            fig.update_traces(marker_color="#d95f4f", textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_title="Events", yaxis_title="")
            show_chart(fig, 310)
    with mid_right:
        with st.container(border=True):
            st.markdown('<div class="panel-title">RPM and tool wear analysis</div>', unsafe_allow_html=True)
            fig = px.scatter(data, x="Rotational speed [rpm]", y="Torque [Nm]", size="Tool wear [min]", color="Status", color_discrete_map=STATUS_COLORS, hover_data=["Product ID", "Type", "Temperature gap [K]", "Workload"], opacity=0.72)
            fig.update_layout(xaxis_title="Rotational speed (rpm)", yaxis_title="Torque (Nm)")
            show_chart(fig, 310)

    bottom_left, bottom_right = st.columns([1, 1], gap="medium")
    with bottom_left:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Machine type distribution</div>', unsafe_allow_html=True)
            type_counts = data["Type"].value_counts().rename_axis("Type").reset_index(name="Machines")
            fig = px.bar(type_counts, x="Type", y="Machines", color="Type", text_auto=True, color_discrete_map=TYPE_COLORS)
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title="Machine type", yaxis_title="Machines")
            show_chart(fig, 290)
    with bottom_right:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Failure rate by type</div>', unsafe_allow_html=True)
            fig = px.bar(type_summary.sort_values("failure_rate", ascending=False), x="Type", y="failure_rate", color="Type", text_auto=".2f", color_discrete_map=TYPE_COLORS)
            fig.update_traces(texttemplate="%{y:.2f}%", textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title="Machine type", yaxis_title="Failure rate (%)")
            show_chart(fig, 290)

def health_assessment(machine: pd.Series) -> tuple[str, str, str, int]:
    """Return a simple, visible assessment based on the recorded row."""
    active_modes = [name for code, name in FAILURE_MODES.items() if machine[code] == 1]
    if machine["Machine failure"] == 1:
        note = "Recorded failure event"
        if active_modes:
            note += f": {', '.join(active_modes)}."
        return "Critical", "critical", note, 0

    score = 100
    signals = []
    if machine["Tool wear [min]"] >= 200:
        score -= 25
        signals.append("high tool wear")
    if machine["Temperature gap [K]"] >= 12:
        score -= 20
        signals.append("elevated temperature gap")
    if machine["Torque [Nm]"] >= 60:
        score -= 15
        signals.append("high torque")
    if machine["Rotational speed [rpm]"] >= 2000:
        score -= 10
        signals.append("high rotational speed")
    if score < 70:
        return "Needs attention", "attention", f"Watch: {', '.join(signals)}.", score
    return "Healthy", "healthy", "No recorded failure or elevated sensor risk under the current rule set.", score


def sensor_gauge(label: str, value: float, maximum: float, unit: str, color: str) -> None:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"font": {"size": 29, "color": "#17212f"}, "suffix": unit},
            gauge={
                "axis": {"range": [0, maximum], "tickwidth": 1, "tickcolor": "#9ca3af", "tickfont": {"size": 9}},
                "bar": {"color": color, "thickness": 0.27},
                "bgcolor": "#f8fafc",
                "borderwidth": 0,
                "steps": [{"range": [0, maximum], "color": "#eef3f0"}],
            },
        )
    )
    fig.update_layout(height=185, margin=dict(l=4, r=4, t=8, b=0), paper_bgcolor="rgba(0,0,0,0)")
    st.markdown(f'<div class="sensor-label">{label}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_machine_explorer(data: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div>
                <div class="eyebrow">Module 3</div>
                <h1>Machine Explorer</h1>
                <p>Search an individual machine or use the sidebar filters to retrieve a focused group. Sensor readings are recorded AI4I dataset values.</p>
            </div>
            <div class="badge">{len(data):,} matching machines</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<div class="panel-title">Find a machine</div>', unsafe_allow_html=True)
        search_col, select_col = st.columns([1, 1.25], gap="medium")
        with search_col:
            searched_id = st.text_input("Search by Product ID", placeholder="For example: M14860").strip().upper()
        with select_col:
            product_options = ["Select a machine", *data["Product ID"].tolist()]
            selected_id = st.selectbox("Or select from the filtered group", product_options)

    chosen_id = searched_id or (selected_id if selected_id != "Select a machine" else "")
    if not chosen_id:
        st.info("Search a Product ID or select a machine from the filtered group to view its condition.")
        return

    selected = data[data["Product ID"].str.upper() == chosen_id]
    if selected.empty:
        st.warning(f"Product ID '{chosen_id}' is not in the current filtered group. Adjust the sidebar filters or select another machine.")
        return

    machine = selected.iloc[0]
    status, status_class, explanation, score = health_assessment(machine)
    st.markdown(
        f"""
        <div class="explorer-status {status_class}">
            <small>Machine health status</small>
            <strong>{status} · {score}/100</strong>
            <p><b>{machine['Product ID']}</b> · Type {machine['Type']} · UDI {int(machine['UDI']):,} &nbsp;—&nbsp; {explanation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<div class="panel-title">Recorded sensor values</div>', unsafe_allow_html=True)
        gauges = st.columns(5, gap="small")
        gauge_specs = [
            ("Air temperature", machine["Air temperature [K]"], 350, " K", "#5b8def"),
            ("Process temperature", machine["Process temperature [K]"], 350, " K", "#f0a11a"),
            ("Rotational speed", machine["Rotational speed [rpm]"], 3000, " rpm", "#8b5cf6"),
            ("Torque", machine["Torque [Nm]"], 100, " Nm", "#d95f9f"),
            ("Tool wear", machine["Tool wear [min]"], 260, " min", "#2f6f73"),
        ]
        for column, spec in zip(gauges, gauge_specs):
            with column:
                sensor_gauge(*spec)
        st.caption("Recorded values from the selected row — not a live sensor feed.")

    with st.container(border=True):
        st.markdown('<div class="panel-title">Failure analysis</div>', unsafe_allow_html=True)
        triggered = []
        chips = []
        for code, label in FAILURE_MODES.items():
            is_triggered = machine[code] == 1
            chips.append(f'<span class="mode-chip {"triggered" if is_triggered else "normal"}">{"●" if is_triggered else "✓"} {code} · {label}</span>')
            if is_triggered:
                triggered.append(label)
        st.markdown("".join(chips), unsafe_allow_html=True)
        if triggered:
            st.error("Recorded failure cause: " + ", ".join(triggered) + ".")
        else:
            st.success("No failure mode is recorded for this machine.")


def assessment_details(machine: pd.Series) -> tuple[str, str, str]:
    """Return a rule-based condition, visual style, and action focus."""
    if int(machine["Machine failure"]) == 1:
        reason, action = failure_details(machine)
        return "Critical", "critical", f"{reason}: {action}"
    signals = []
    if machine["Tool wear [min]"] >= 200:
        signals.append("tool wear")
    if machine["Temperature gap [K]"] >= 10:
        signals.append("temperature gap")
    if machine["Torque [Nm]"] >= 60:
        signals.append("torque")
    if signals:
        return "Attention", "attention", f"Inspect elevated {', '.join(signals)} during the next planned maintenance check."
    return "Healthy", "healthy", "Continue routine inspection; no recorded failure is present in this dataset row."


def signal_card(label: str, value: str, note: str, state: str = "healthy") -> None:
    st.markdown(
        f'<div class="signal-card {state}"><small>{label}</small><strong>{value}</strong><span>{note}</span></div>',
        unsafe_allow_html=True,
    )


def signal_state(value: float, attention: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= attention:
        return "attention"
    return "healthy"


def render_work_order_queue() -> None:
    initialise_work_orders()
    st.markdown('<div class="panel-title">Work-order register</div>', unsafe_allow_html=True)
    search = st.text_input(
        "Search work orders",
        placeholder="Search by order ID, product ID, failure reason, or recommended action",
        key="work_order_search",
    )
    filter_one, filter_two = st.columns(2)
    with filter_one:
        status_filter = st.selectbox("Order status", ["All", *VALID_STATUSES], key="order_status_filter")
    with filter_two:
        priority_filter = st.selectbox("Priority", ["All", *VALID_PRIORITIES], key="order_priority_filter")
    orders = get_work_orders(status_filter, priority_filter, search)

    total = len(orders)
    open_orders = int((orders["status"] == "Open").sum()) if not orders.empty else 0
    in_progress = int((orders["status"] == "In Progress").sum()) if not orders.empty else 0
    closed = int((orders["status"] == "Closed").sum()) if not orders.empty else 0
    critical = int((orders["priority"] == "Critical").sum()) if not orders.empty else 0
    kpi_one, kpi_two, kpi_three, kpi_four, kpi_five = st.columns(5, gap="medium")
    with kpi_one:
        metric_card("Total orders", f"{total:,}", "Current results")
    with kpi_two:
        metric_card("Open", f"{open_orders:,}", "Awaiting action", warn=open_orders > 0)
    with kpi_three:
        metric_card("In progress", f"{in_progress:,}", "Under maintenance")
    with kpi_four:
        metric_card("Closed", f"{closed:,}", "Completed orders")
    with kpi_five:
        metric_card("Critical", f"{critical:,}", "Current results", warn=critical > 0)

    if orders.empty:
        st.info("No work orders match the current search and filters. Create one from a machine with a recorded failure.")
        return

    st.dataframe(
        orders[["order_id", "product_id", "failure_reason", "priority", "status", "created_at"]],
        width="stretch",
        hide_index=True,
    )
    st.markdown('<div class="panel-title">Export work-order data</div>', unsafe_allow_html=True)
    export_json, export_csv = st.columns(2)
    with export_json:
        st.download_button(
            "Download JSON",
            orders.to_json(orient="records", indent=2),
            file_name="work_orders.json",
            mime="application/json",
            width="stretch",
        )
    with export_csv:
        st.download_button(
            "Download CSV",
            orders.to_csv(index=False),
            file_name="work_orders.csv",
            mime="text/csv",
            width="stretch",
        )
    for order in orders.itertuples(index=False):
        with st.expander(f"Work order #{order.order_id} · {order.product_id} · {order.status}"):
            st.write(order.recommended_action)
            control_one, control_two, control_three = st.columns([1, 1, 0.8])
            with control_one:
                priority = st.selectbox("Priority", VALID_PRIORITIES, index=VALID_PRIORITIES.index(order.priority), key=f"priority_{order.order_id}")
            with control_two:
                status = st.selectbox("Status", VALID_STATUSES, index=VALID_STATUSES.index(order.status), key=f"status_{order.order_id}")
            with control_three:
                st.write("")
                if st.button("Save", key=f"save_{order.order_id}", width="stretch"):
                    update_work_order(order.order_id, priority, status)
                    st.rerun()


def render_preventive_maintenance(machine_data: pd.DataFrame) -> None:
    if machine_data.empty:
        st.warning("No machines match the current sidebar filters. Adjust the filters to create a schedule for a machine.")
        return
    initialise_work_orders()
    generated = generate_due_work_orders()
    schedules = get_schedules(active_only=True)
    today = date.today().isoformat()
    upcoming = schedules[schedules["next_due_date"] >= today] if not schedules.empty else schedules
    overdue = schedules[schedules["next_due_date"] < today] if not schedules.empty else schedules
    preventive_orders = get_work_orders(search="")
    if not preventive_orders.empty:
        preventive_orders = preventive_orders[preventive_orders["work_order_type"] == "Preventive"]
    open_preventive = int((preventive_orders["status"] != "Closed").sum()) if not preventive_orders.empty else 0
    history = get_maintenance_history()

    st.markdown(
        """
        <section class="hero">
            <div><div class="eyebrow">Module 7</div><h1>Preventive Maintenance</h1>
            <p>Schedule recurring maintenance, manage checklists, and track execution history.</p></div>
            <div class="badge">Schedule-driven maintenance</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if generated:
        st.success(f"Generated {generated} preventive work order(s) from due schedules.")

    kpi_one, kpi_two, kpi_three, kpi_four, kpi_five = st.columns(5, gap="medium")
    with kpi_one:
        metric_card("Active schedules", f"{len(schedules):,}", "Recurring plans")
    with kpi_two:
        metric_card("Due soon", f"{len(upcoming):,}", "Upcoming maintenance")
    with kpi_three:
        metric_card("Overdue", f"{len(overdue):,}", "Needs attention", warn=len(overdue) > 0)
    with kpi_four:
        metric_card("Open preventive", f"{open_preventive:,}", "Generated work orders", warn=open_preventive > 0)
    with kpi_five:
        metric_card("Completed", f"{len(history):,}", "Maintenance history")

    create_tab, schedule_tab, history_tab = st.tabs(["Create schedule", "Schedules and checklists", "Maintenance history"])
    with create_tab:
        with st.form("create_maintenance_schedule"):
            form_one, form_two = st.columns(2)
            with form_one:
                machine_options = machine_data[["Product ID", "Type", "Status"]].copy()
                machine_options["Product ID"] = machine_options["Product ID"].astype(str)
                machine_options = machine_options.drop_duplicates("Product ID").sort_values("Product ID")
                product_ids = machine_options["Product ID"].tolist()
                machine_labels = {
                    row["Product ID"]: f"{row['Product ID']} · {row['Type']} machine · {row['Status']}"
                    for _, row in machine_options.iterrows()
                }
                product_id = st.selectbox(
                    "Product ID",
                    product_ids,
                    format_func=machine_labels.get,
                    help="Type to search the product list, filtered by the sidebar selections.",
                )
                title = st.text_input("Maintenance task", placeholder="Lubrication and inspection")
                frequency = st.selectbox("Frequency", VALID_FREQUENCIES)
                next_due = st.date_input("First due date", value=date.today())
            with form_two:
                technician = st.text_input("Assigned technician")
                description = st.text_area("Instructions or recommendation", height=125)
                selected_machine = machine_options[machine_options["Product ID"].eq(product_id)].iloc[0]
                st.caption(f"Machine type: {selected_machine['Type']} · Health: {selected_machine['Status']}")
                st.caption("Schedules automatically generate one preventive work order when due.")
            submitted = st.form_submit_button("Create schedule", type="primary")
        if submitted:
            if not product_id.strip() or not title.strip():
                st.error("Product ID and maintenance task are required.")
            else:
                create_schedule(product_id, title, description, frequency, next_due.isoformat(), technician)
                st.success("Preventive maintenance schedule created.")
                st.rerun()

    with schedule_tab:
        if schedules.empty:
            st.info("No preventive schedules exist yet.")
        else:
            st.subheader("Maintenance calendar")
            calendar_view = schedules[["next_due_date", "product_id", "title", "frequency", "technician"]].rename(columns={"next_due_date": "Due date", "product_id": "Product ID", "title": "Task", "frequency": "Frequency", "technician": "Technician"})
            st.dataframe(calendar_view, width="stretch", hide_index=True)
            if not overdue.empty:
                st.warning(f"{len(overdue)} schedule(s) are overdue.")
            for schedule in schedules.itertuples(index=False):
                with st.expander(f"{schedule.title} · {schedule.product_id} · due {schedule.next_due_date}"):
                    st.write(schedule.description or "No additional instructions provided.")
                    st.caption(f"Frequency: {schedule.frequency} · Technician: {schedule.technician or 'Unassigned'}")
                    if st.button("Generate AI maintenance recommendation", key=f"recommend_{schedule.schedule_id}"):
                        installed_models = get_available_models()
                        model = OLLAMA_MODEL if OLLAMA_MODEL in installed_models else (installed_models[0] if installed_models else OLLAMA_MODEL)
                        context = preventive_maintenance_context(schedule, history, get_checklist(schedule.schedule_id))
                        with st.spinner("Preparing a schedule-based recommendation..."):
                            try:
                                recommendation = ask_maintenance_assistant("Review this preventive maintenance schedule and recommend practical next actions, priority, and any checklist improvements.", context, model)
                                st.session_state[f"recommendation_{schedule.schedule_id}"] = recommendation
                            except ConnectionError as error:
                                st.warning(str(error))
                    if st.session_state.get(f"recommendation_{schedule.schedule_id}"):
                        st.info(st.session_state[f"recommendation_{schedule.schedule_id}"])
                    checklist = get_checklist(schedule.schedule_id)
                    st.markdown("**Checklist**")
                    if checklist.empty:
                        st.caption("No checklist items configured.")
                    else:
                        for item in checklist.itertuples(index=False):
                            st.write(f"{'Required' if item.required else 'Optional'} · {item.item}")
                    with st.form(f"checklist_{schedule.schedule_id}"):
                        checklist_item = st.text_input("Add checklist item", key=f"new_item_{schedule.schedule_id}")
                        required = st.checkbox("Required item", value=True, key=f"required_{schedule.schedule_id}")
                        if st.form_submit_button("Add checklist item"):
                            if checklist_item.strip():
                                add_checklist_item(schedule.schedule_id, checklist_item, required)
                                st.success("Checklist item added.")
                                st.rerun()
                            else:
                                st.error("Enter a checklist item first.")
                    schedule_orders = get_schedule_work_orders(schedule.schedule_id)
                    if not schedule_orders.empty:
                        st.markdown("**Generated work orders**")
                        st.dataframe(schedule_orders[["order_id", "status", "technician", "due_date", "completed_at"]], width="stretch", hide_index=True)
                        for order in schedule_orders.itertuples(index=False):
                            progress = get_checklist_progress(order.order_id)
                            if not progress.empty:
                                st.markdown(f"Checklist for work order #{order.order_id}")
                                for item in progress.itertuples(index=False):
                                    checked = st.checkbox(item.item, value=bool(item.completed), key=f"item_{order.order_id}_{item.checklist_id}")
                                    if checked != bool(item.completed):
                                        set_checklist_item(order.order_id, item.checklist_id, checked)
                            if order.status != "Closed":
                                with st.form(f"complete_{order.order_id}"):
                                    completion_technician = st.text_input("Technician", value=order.technician or schedule.technician, key=f"tech_{order.order_id}")
                                    notes = st.text_area("Completion notes", key=f"notes_{order.order_id}")
                                    if st.form_submit_button("Complete maintenance"):
                                        try:
                                            record_maintenance_completion(order.order_id, completion_technician, notes)
                                            st.success("Maintenance completed and recorded in history.")
                                            st.rerun()
                                        except ValueError as error:
                                            st.error(str(error))

    with history_tab:
        if history.empty:
            st.info("Completed preventive maintenance will appear here.")
        else:
            st.dataframe(history, width="stretch", hide_index=True)
            confirm_delete = st.checkbox("Confirm deletion", key=f"confirm_delete_{order.order_id}")
            if st.button("Delete work order", key=f"delete_{order.order_id}", disabled=not confirm_delete):
                if delete_work_order(order.order_id):
                    st.success(f"Work order #{order.order_id} deleted.")
                    st.rerun()


def render_ai_assistant(data: pd.DataFrame) -> None:
    """Render the streamlined assistant and persistent work-order queue."""
    installed_models = get_available_models()
    model = OLLAMA_MODEL if OLLAMA_MODEL in installed_models else (installed_models[0] if installed_models else OLLAMA_MODEL)
    connection_badge = '<span class="assistant-ready">Ollama connected</span>' if installed_models else '<span class="assistant-offline">Ollama unavailable</span>'
    st.markdown(
        f"""
        <section class="hero">
            <div><div class="eyebrow">Module 4</div><h1>AI Maintenance Assistant</h1>
            <p>Fast local guidance, streamed detailed reports, and persistent work orders for recorded failures.</p></div>
            <div class="badge">{connection_badge}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        product_id = st.selectbox("Choose a machine", data["Product ID"].tolist(), key="ai_machine")
        machine = data.loc[data["Product ID"] == product_id].iloc[0]
        if st.session_state.get("ai_context_product") != product_id:
            st.session_state.ai_context_product = product_id
            st.session_state.ai_messages = []
            st.session_state.pop("ai_quick_assessment", None)
            st.session_state.pop("ai_report", None)
            st.session_state.pop("ai_report_machine", None)

        condition, condition_style, focus = assessment_details(machine)
        active_modes = [label for code, label in FAILURE_MODES.items() if int(machine[code]) == 1]
        overview = st.columns(4, gap="medium")
        with overview[0]:
            signal_card("Recorded status", condition, "Dataset-based assessment", condition_style)
        with overview[1]:
            signal_card("Work order", "Eligible" if int(machine["Machine failure"]) else "Not required", "Recorded failure only", "critical" if int(machine["Machine failure"]) else "healthy")
        with overview[2]:
            signal_card("Default priority", "High" if int(machine["Machine failure"]) else "Monitor", "Human review required", "attention" if int(machine["Machine failure"]) else "healthy")
        with overview[3]:
            signal_card("Failure modes", ", ".join(active_modes) if active_modes else "None", "Recorded event labels", "critical" if active_modes else "healthy")

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Technical indicators</div>', unsafe_allow_html=True)
        indicators = st.columns(5, gap="small")
        indicator_specs = [
            ("Temperature gap", machine["Temperature gap [K]"], "K", 8, 12),
            ("Rotational speed", machine["Rotational speed [rpm]"], "rpm", 2000, 2500),
            ("Torque", machine["Torque [Nm]"], "Nm", 55, 70),
            ("Tool wear", machine["Tool wear [min]"], "min", 180, 220),
            ("Workload", machine["Workload"], "", 55, 70),
        ]
        for column, (label, value, unit, attention, critical) in zip(indicators, indicator_specs):
            with column:
                precision = ".1f" if label in {"Temperature gap", "Torque", "Workload"} else ".0f"
                signal_card(label, f"{value:{precision}} {unit}".strip(), f"Attention ≥ {attention:g}", signal_state(value, attention, critical))

        with st.expander("Technical details and maintenance focus", expanded=False):
            st.caption(f"Product ID {machine['Product ID']} · Type {machine['Type']} · UDI {int(machine['UDI']):,}")
            st.markdown(f"**Immediate maintenance focus:** {focus}")
            st.dataframe(
                pd.DataFrame({
                    "Recorded signal": ["Air temperature", "Process temperature", "Temperature gap", "RPM", "Torque", "Tool wear", "Workload"],
                    "Value": [f"{machine['Air temperature [K]']:.1f} K", f"{machine['Process temperature [K]']:.1f} K", f"{machine['Temperature gap [K]']:.1f} K", f"{machine['Rotational speed [rpm]']:.0f} rpm", f"{machine['Torque [Nm]']:.1f} Nm", f"{machine['Tool wear [min]']:.0f} min", f"{machine['Workload']:.1f}"],
                }),
                width="stretch", hide_index=True,
            )

        context = machine_context(machine)
        action_one, action_two, action_three = st.columns([1, 1, 1.15], gap="medium")
        with action_one:
            quick_requested = st.button("Quick assessment", width="stretch", disabled=not installed_models)
        with action_two:
            report_requested = st.button("Stream detailed report", type="primary", width="stretch", disabled=not installed_models)
        with action_three:
            work_order_requested = st.button("Create work order", width="stretch", disabled=int(machine["Machine failure"]) != 1)

        if work_order_requested:
            created, message = create_work_order(machine)
            (st.success if created else st.warning)(message)
        if quick_requested:
            with st.spinner("Preparing a quick assessment..."):
                try:
                    st.session_state.ai_quick_assessment = ask_maintenance_assistant("Give a concise risk assessment and the first two inspection actions for this machine.", context, model)
                except ConnectionError as error:
                    st.error(str(error))
        if st.session_state.get("ai_quick_assessment"):
            with st.container(border=True):
                st.markdown('<div class="panel-title">Quick assessment</div>', unsafe_allow_html=True)
                st.markdown(st.session_state.ai_quick_assessment)

        if report_requested:
            with st.container(border=True):
                st.markdown('<div class="panel-title">Streamed maintenance report</div>', unsafe_allow_html=True)
                try:
                    report = st.write_stream(stream_maintenance_report(context, model))
                except ConnectionError as error:
                    st.error(str(error))
                else:
                    st.session_state.ai_report = report
                    st.session_state.ai_report_machine = product_id
        if st.session_state.get("ai_report"):
            report_words = len(st.session_state.ai_report.replace("#", "").split())
            with st.container(border=True):
                st.markdown('<div class="panel-title">Latest maintenance report</div>', unsafe_allow_html=True)
                st.caption(f"{report_words} words · generated locally with Llama 3.2")
                st.markdown(st.session_state.ai_report)
                st.download_button("Download report (.md)", st.session_state.ai_report, file_name=f"maintenance_report_{st.session_state.get('ai_report_machine', 'machine')}.md", mime="text/markdown", width="stretch")

        with st.container(border=True):
            st.markdown('<div class="panel-title">Ask the assistant</div>', unsafe_allow_html=True)
            if "ai_messages" not in st.session_state:
                st.session_state.ai_messages = []
            for message in st.session_state.ai_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            question = st.chat_input("Ask about this machine", disabled=not installed_models)
            if question:
                st.session_state.ai_messages.append({"role": "user", "content": question})
                with st.chat_message("assistant"):
                    with st.spinner("Llama 3.2 is reviewing the record..."):
                        try:
                            answer = ask_maintenance_assistant(question, context, model)
                        except ConnectionError as error:
                            answer = str(error)
                    st.markdown(answer)
                st.session_state.ai_messages.append({"role": "assistant", "content": answer})

df = load_data()

with st.sidebar:
    st.title("Agentic Facility Operations ")
    st.caption("Module navigation")
    section = st.radio("Section", ["Module 1: EDA", "Module 2: Dashboard", "Module 3: Machine Explorer", "Module 4: AI Assistant", "Module 5 & 6: Work Order Management", "Module 7: Preventive Maintenance"])

    st.divider()
    st.caption("Filters")
    selected_types = st.multiselect("Machine type", sorted(df["Type"].unique()), default=sorted(df["Type"].unique()))
    selected_status = st.multiselect("Status", ["Healthy", "Failed"], default=["Healthy", "Failed"])
    wear_min, wear_max = st.slider(
        "Tool wear range",
        int(df["Tool wear [min]"].min()),
        int(df["Tool wear [min]"].max()),
        (int(df["Tool wear [min]"].min()), int(df["Tool wear [min]"].max())),
    )
    selected_failure_modes = ["Any failure mode"]
    if section == "Module 3: Machine Explorer":
        st.divider()
        st.caption("Explorer group filter")
        selected_failure_modes = st.multiselect(
            "Failure mode",
            ["Any failure mode", *FAILURE_MODES.values()],
            default=["Any failure mode"],
            help="Narrow the machine group by one or more recorded failure modes.",
        )

filtered_df = df[
    df["Type"].isin(selected_types)
    & df["Status"].isin(selected_status)
    & df["Tool wear [min]"].between(wear_min, wear_max)
].copy()

if "Any failure mode" not in selected_failure_modes:
    selected_mode_columns = [code for code, label in FAILURE_MODES.items() if label in selected_failure_modes]
    if selected_mode_columns:
        filtered_df = filtered_df[filtered_df[selected_mode_columns].eq(1).any(axis=1)].copy()

if filtered_df.empty and section not in ("Module 5 & 6: Work Order Management", "Module 7: Preventive Maintenance"):
    st.warning("No records match the current filters.")
    st.stop()

if section == "Module 1: EDA":
    render_eda(filtered_df, df)
elif section == "Module 2: Dashboard":
    render_dashboard(filtered_df)
elif section == "Module 3: Machine Explorer":
    render_machine_explorer(filtered_df)
elif section == "Module 5 & 6: Work Order Management":
    st.markdown(
        """
        <section class="hero">
            <div>
                <div class="eyebrow">Module 5 &amp; 6</div>
                <h1>Work Order Management</h1>
                <p>Search, filter, update, export, and remove persistent maintenance work orders.</p>
            </div>
            <div class="badge">Persistent register</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        render_work_order_queue()
elif section == "Module 7: Preventive Maintenance":
    render_preventive_maintenance(filtered_df)
else:
    render_ai_assistant(filtered_df)
