"""
pages/analytics.py — Combined Data Analytics page (Modules 1 + 2).

Organized into 5 tabs:
  Tab 1: Overview         (dataset preview + descriptive stats)
  Tab 2: Distributions    (failure dist, type dist, failure by type)
  Tab 3: Correlations     (heatmap)
  Tab 4: Sensor Analysis  (temperature, RPM, torque, tool wear)
  Tab 5: Failure          (failure mode breakdown, wear vs failure)
"""

import streamlit as st
from utils.data import (
    build_dataset_preview,
    compute_descriptive_stats,
    compute_correlation_matrix,
    compute_failure_distribution,
    compute_type_distribution,
    compute_failure_by_type,
    compute_rpm_histogram,
    compute_tool_wear_histogram,
    compute_tool_wear_by_failure,
    compute_failure_mode_breakdown,
)
from utils.charts import (
    chart_failure_dist,
    chart_type_dist,
    chart_correlation_heatmap,
    chart_failure_by_type,
    chart_rpm_histogram,
    chart_tool_wear_histogram,
    chart_tool_wear_failure,
    chart_failure_mode_breakdown,
)
from utils.styles import page_header, section_header, observation
import plotly.graph_objects as go
from utils.styles import COLORS


def render(df, raw_df) -> None:
    """Render the Data Analytics page."""

    page_header(
        "",
        "Data Analytics",
        "Comprehensive exploratory analysis of sensor data, failure patterns, and machine characteristics.",
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview",
        "Distributions",
        "Correlations",
        "Sensor Analysis",
        "Failure Analysis",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Dataset Preview", "First 10 rows of the filtered dataset.")

        preview = build_dataset_preview(df, n=10)
        shape = preview["shape"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Filtered Rows", f"{shape['rows']:,}")
        c2.metric("Columns", shape["cols"])
        c3.metric("Features", len(preview["columns"]))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df.head(10).reset_index(drop=True), width="stretch", height=380)

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Descriptive Statistics", "Count, mean, std, quartiles for all numerical features.")
        stats_df = compute_descriptive_stats(df)
        st.dataframe(stats_df.set_index("Feature"), width="stretch")
        observation(
            "<strong>Observation:</strong> Air and Process temperatures occupy a narrow range "
            "(~295–315 K), indicating controlled thermal conditions. Rotational speed has a mean "
            "of ~1,539 rpm with noticeable right-skew. Torque ranges from ~3.8 to ~76.6 Nm. "
            "Tool wear spans the full lifecycle up to ~253 minutes."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — DISTRIBUTIONS
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Failure Distribution", "Overall failure vs healthy proportion.")

        col1, col2 = st.columns(2)
        with col1:
            fail_data = compute_failure_distribution(df)
            st.plotly_chart(chart_failure_dist(fail_data), width="stretch")
            observation(
                "<strong>Observation:</strong> With only ~3.4% failures out of 10,000 records, "
                "the dataset is heavily imbalanced — typical in real-world predictive maintenance."
            )
        with col2:
            type_data = compute_type_distribution(df)
            st.plotly_chart(chart_type_dist(type_data), width="stretch")
            observation(
                "<strong>Observation:</strong> Low-grade (L) machines dominate (~60%), followed by "
                "Medium (M) and High (H), mirroring realistic production floor composition."
            )

        st.markdown("---")
        section_header("Failure Rate by Machine Type", "Which machine grade fails more often?")
        by_type = compute_failure_by_type(df)
        st.plotly_chart(chart_failure_by_type(by_type), width="stretch")
        observation(
            "<strong>Observation:</strong> Despite being fewer, High-grade (H) machines show "
            "the highest failure rate %, suggesting they operate under more demanding conditions."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — CORRELATIONS
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header(
            "Pearson Correlation Matrix",
            "Strength and direction of linear relationships between all numerical variables.",
        )

        corr = compute_correlation_matrix(df)
        st.plotly_chart(chart_correlation_heatmap(corr), width="stretch")

        observation(
            "<strong>Key observations:</strong> "
            "Air temperature and Process temperature are strongly correlated (r ≈ 0.88) because "
            "both reflect the same process heat state. Rotational speed and Torque share a strong "
            "negative correlation (r ≈ −0.88), consistent with constant-power mechanics. Tool wear "
            "shows a weak positive correlation with machine failure, consistent with physical degradation."
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Correlation table in expandable section
        with st.expander("View Raw Correlation Values"):
            import pandas as pd
            corr_df = pd.DataFrame(
                corr["values"],
                index=corr["labels"],
                columns=corr["labels"],
            ).round(3)
            st.dataframe(corr_df, width="stretch")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — SENSOR ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)

        # Temperature section
        section_header("Temperature Analysis", "Air and Process temperature distributions.")

        col1, col2 = st.columns(2)
        with col1:
            # Air temp histogram
            import numpy as np
            air_arr = df["Air temperature [K]"].dropna().values
            counts, edges = np.histogram(air_arr, bins=25)
            labels = [f"{edges[i]:.1f}–{edges[i+1]:.1f}" for i in range(len(edges) - 1)]
            fig_at = go.Figure(go.Bar(
                x=labels, y=counts,
                marker=dict(color="rgba(59,130,246,0.75)", line=dict(color=COLORS["blue"], width=0.4)),
                hovertemplate="Air Temp %{x} K: %{y:,}<extra></extra>",
            ))
            fig_at.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=20, r=20, t=40, b=50),
                title=dict(text="Air Temperature Distribution", font=dict(size=14, color="#1a2035"), x=0),
                xaxis=dict(showgrid=False, tickangle=45, nticks=8),
                yaxis=dict(gridcolor="#f1f5f9", title="Frequency"),
                font=dict(family="Inter, sans-serif", size=11, color="#64748b"),
            )
            st.plotly_chart(fig_at, width="stretch")

        with col2:
            # Process temp histogram
            proc_arr = df["Process temperature [K]"].dropna().values
            counts_p, edges_p = np.histogram(proc_arr, bins=25)
            labels_p = [f"{edges_p[i]:.1f}–{edges_p[i+1]:.1f}" for i in range(len(edges_p) - 1)]
            fig_pt = go.Figure(go.Bar(
                x=labels_p, y=counts_p,
                marker=dict(color="rgba(239,68,68,0.72)", line=dict(color=COLORS["red"], width=0.4)),
                hovertemplate="Proc Temp %{x} K: %{y:,}<extra></extra>",
            ))
            fig_pt.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=20, r=20, t=40, b=50),
                title=dict(text="Process Temperature Distribution", font=dict(size=14, color="#1a2035"), x=0),
                xaxis=dict(showgrid=False, tickangle=45, nticks=8),
                yaxis=dict(gridcolor="#f1f5f9", title="Frequency"),
                font=dict(family="Inter, sans-serif", size=11, color="#64748b"),
            )
            st.plotly_chart(fig_pt, width="stretch")

        observation(
            "<strong>Observation:</strong> Air temperature is centered around 300 K while process "
            "temperature averages ~310 K. The consistent ~10 K differential is maintained by cooling systems."
        )

        st.markdown("---")
        section_header("RPM Analysis", "Rotational speed frequency distribution.")
        rpm_data = compute_rpm_histogram(df)
        st.plotly_chart(chart_rpm_histogram(rpm_data), width="stretch")
        observation(
            "<strong>Observation:</strong> Rotational speed follows an approximately normal distribution "
            "centered around 1,500 rpm. Machines at extreme speeds (very low or very high RPM) "
            "are more prone to failure due to operating beyond design limits."
        )

        st.markdown("---")
        section_header("Torque Analysis", "Torque distribution across the dataset.")
        torque_arr = df["Torque [Nm]"].dropna().values
        counts_t, edges_t = np.histogram(torque_arr, bins=30)
        labels_t = [f"{edges_t[i]:.1f}–{edges_t[i+1]:.1f}" for i in range(len(edges_t) - 1)]
        fig_tq = go.Figure(go.Bar(
            x=labels_t, y=counts_t,
            marker=dict(color="rgba(139,92,246,0.75)", line=dict(color=COLORS["purple"], width=0.4)),
            hovertemplate="Torque %{x} Nm: %{y:,}<extra></extra>",
        ))
        fig_tq.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=20, r=20, t=40, b=50),
            title=dict(text="Torque Distribution", font=dict(size=14, color="#1a2035"), x=0),
            xaxis=dict(showgrid=False, tickangle=40, nticks=10),
            yaxis=dict(gridcolor="#f1f5f9", title="Frequency"),
            font=dict(family="Inter, sans-serif", size=11, color="#64748b"),
        )
        st.plotly_chart(fig_tq, width="stretch")
        observation(
            "<strong>Observation:</strong> Torque exhibits a roughly normal distribution centered "
            "around 40 Nm. High torque values (> 65 Nm) are associated with increased failure risk "
            "due to overstrain conditions."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — FAILURE ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Failure Mode Breakdown", "Count of each specific failure type across the dataset.")
        mode_data = compute_failure_mode_breakdown(df)
        st.plotly_chart(chart_failure_mode_breakdown(mode_data), width="stretch")
        observation(
            "<strong>Observation:</strong> Heat Dissipation Failure (HDF) and Overstrain Failure "
            "(OSF) are the most frequent failure modes. Random Failure (RNF) is the rarest, as "
            "expected for unpredictable failures."
        )

        st.markdown("---")
        section_header("Tool Wear vs Failure", "How tool degradation level correlates with failure probability.")
        col1, col2 = st.columns(2)
        with col1:
            tw_data = compute_tool_wear_histogram(df)
            st.plotly_chart(chart_tool_wear_histogram(tw_data), width="stretch")
            observation(
                "<strong>Observation:</strong> Tool wear is nearly uniformly distributed (0–253 min), "
                "capturing the full wear lifecycle from new to heavily worn."
            )
        with col2:
            twf_data = compute_tool_wear_by_failure(df)
            st.plotly_chart(chart_tool_wear_failure(twf_data), width="stretch")
            observation(
                "<strong>Observation:</strong> Failure rates increase at higher wear levels, "
                "particularly above ~200 minutes. Green bars = low risk; red bars = critical zones "
                "where tool replacement is urgent."
            )
