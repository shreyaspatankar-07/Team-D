"""
pages/dashboard.py — Landing dashboard page.

Shows KPI cards, failure distribution, machine type breakdown,
failure mode analysis, and high-level observations.
"""

import streamlit as st
from utils.data import (
    compute_kpis,
    compute_failure_distribution,
    compute_type_distribution,
    compute_failure_mode_breakdown,
    compute_failure_by_type,
)
from utils.charts import (
    chart_failure_dist,
    chart_type_dist,
    chart_failure_mode_breakdown,
    chart_failure_by_type,
)
from utils.styles import page_header, section_header, observation, COLORS


def render(df, raw_df) -> None:
    """Render the Dashboard page. df is filtered; raw_df is always the full dataset."""

    # ── Page Header ────────────────────────────────────────────────────────────
    page_header(
        "🏠",
        "Industrial Monitoring Dashboard",
        "Real-time overview of the AI4I 2020 predictive maintenance dataset.",
    )

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    section_header("Key Performance Indicators", "Aggregated metrics for the current filter selection.")

    kpis = compute_kpis(df)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Records", f"{kpis['total_records']:,}", help="After deduplication")
    with c2:
        st.metric("Total Features", kpis["total_features"], help="Including all sensor + target columns")
    with c3:
        st.metric(
            "Machine Failures",
            f"{kpis['total_failures']:,}",
            delta=f"{kpis['failure_rate']}% failure rate",
            delta_color="inverse",
        )
    with c4:
        st.metric("Healthy Machines", f"{kpis['healthy_count']:,}", help="Records with no failure")
    with c5:
        st.metric("Machine Types", kpis["machine_types"], help="L · M · H quality grades")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 1 ───────────────────────────────────────────────────────────
    section_header("Failure Overview", "Distribution of failures and machine type composition.")

    col1, col2 = st.columns(2)
    with col1:
        fail_data = compute_failure_distribution(df)
        st.plotly_chart(chart_failure_dist(fail_data), use_container_width=True)
        observation(
            "<strong>Observation:</strong> Only ~3.4% of all records are machine failures, "
            "highlighting a significant class imbalance. This is typical in real-world "
            "predictive maintenance scenarios where failures are rare events."
        )
    with col2:
        type_data = compute_type_distribution(df)
        st.plotly_chart(chart_type_dist(type_data), use_container_width=True)
        observation(
            "<strong>Observation:</strong> Low-quality (L) machines dominate at ~60% of "
            "the dataset, followed by Medium (M) at ~30% and High (H) at ~10%, "
            "reflecting a realistic production floor composition."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 2 ───────────────────────────────────────────────────────────
    section_header("Failure Deep Dive", "Failure mode distribution and failure rate per machine type.")

    col3, col4 = st.columns(2)
    with col3:
        mode_data = compute_failure_mode_breakdown(df)
        st.plotly_chart(chart_failure_mode_breakdown(mode_data), use_container_width=True)
        observation(
            "<strong>Observation:</strong> Heat Dissipation Failure (HDF) and Overstrain "
            "Failure (OSF) are the most frequent failure modes. Random Failure (RNF) is the "
            "rarest, as expected. Understanding which modes dominate guides preventive "
            "maintenance priorities."
        )
    with col4:
        by_type = compute_failure_by_type(df)
        st.plotly_chart(chart_failure_by_type(by_type), use_container_width=True)
        observation(
            "<strong>Observation:</strong> High-quality (H) machines show the highest failure "
            "rate percentage despite being fewer in count, suggesting they operate under more "
            "demanding conditions requiring closer monitoring."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Dataset Summary ────────────────────────────────────────────────────────
    section_header("Dataset Summary", "At-a-glance summary of the AI4I 2020 Predictive Maintenance dataset.")
    st.markdown(
        """
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                    padding:20px 24px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <table style="width:100%; border-collapse:collapse; font-size:0.88rem; color:#1e293b;">
                <thead>
                    <tr style="border-bottom:1px solid #e2e8f0;">
                        <th style="text-align:left; padding:8px 0; color:#64748b; font-size:0.72rem;
                                   text-transform:uppercase; letter-spacing:0.06em;">Attribute</th>
                        <th style="text-align:left; padding:8px 0; color:#64748b; font-size:0.72rem;
                                   text-transform:uppercase; letter-spacing:0.06em;">Detail</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td style="padding:7px 0; color:#64748b;">Dataset Name</td>
                        <td style="padding:7px 0; font-weight:600;">AI4I 2020 Predictive Maintenance</td></tr>
                    <tr style="background:#f8fafc;"><td style="padding:7px 6px; color:#64748b;">Sensors</td>
                        <td style="padding:7px 6px; font-weight:600;">Air Temp · Process Temp · RPM · Torque · Tool Wear</td></tr>
                    <tr><td style="padding:7px 0; color:#64748b;">Target Variable</td>
                        <td style="padding:7px 0; font-weight:600;">Machine failure (binary)</td></tr>
                    <tr style="background:#f8fafc;"><td style="padding:7px 6px; color:#64748b;">Failure Modes</td>
                        <td style="padding:7px 6px; font-weight:600;">TWF · HDF · PWF · OSF · RNF</td></tr>
                    <tr><td style="padding:7px 0; color:#64748b;">Machine Grades</td>
                        <td style="padding:7px 0; font-weight:600;">Low (L) · Medium (M) · High (H)</td></tr>
                    <tr style="background:#f8fafc;"><td style="padding:7px 6px; color:#64748b;">Source</td>
                        <td style="padding:7px 6px; font-weight:600;">UCI Machine Learning Repository / Kaggle</td></tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
