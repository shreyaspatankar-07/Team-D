"""
utils/charts.py — All Plotly chart builders (original + new gauges).

All original chart functions are preserved verbatim.
New functions: gauge charts, health indicator, temperature comparison.
"""

import numpy as np
import plotly.graph_objects as go
from utils.styles import COLORS, PALETTE

# ── Shared Layout Defaults ────────────────────────────────────────────────────

_CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#64748b"),
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
)
_DEFAULT_MARGIN = dict(l=20, r=20, t=40, b=40)


# ══════════════════════════════════════════════════════════════════════════════
# ORIGINAL CHARTS — preserved verbatim from app.py
# ══════════════════════════════════════════════════════════════════════════════

def chart_failure_dist(data: dict) -> go.Figure:
    """Doughnut chart — Failure vs No-Failure."""
    fig = go.Figure(go.Pie(
        labels=data["labels"],
        values=data["values"],
        hole=0.60,
        marker=dict(
            colors=[COLORS["blue"], COLORS["red"]],
            line=dict(color="#ffffff", width=2),
        ),
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="Failure Distribution", font=dict(size=14, color="#1a2035"), x=0),
        showlegend=True,
    )
    return fig


def chart_type_dist(data: dict) -> go.Figure:
    """Bar chart — Machine type count distribution."""
    colors = [COLORS["blue"], COLORS["amber"], COLORS["red"]][:len(data["labels"])]
    fig = go.Figure(go.Bar(
        x=data["labels"],
        y=data["values"],
        marker=dict(color=colors, line=dict(width=0)),
        text=data["values"],
        textposition="outside",
        hovertemplate="%{x}: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="Machine Type Distribution", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f1f5f9", showgrid=True),
        showlegend=False,
    )
    return fig


def chart_correlation_heatmap(corr: dict) -> go.Figure:
    """Colour-coded Pearson correlation heatmap."""
    labels = corr["labels"]
    values = corr["values"]

    colorscale = [
        [0.0, "#d94f3b"],
        [0.5, "#ffffff"],
        [1.0, "#1a6eb5"],
    ]

    annotations = []
    for i, row in enumerate(values):
        for j, val in enumerate(row):
            abs_val = abs(val)
            text_color = "#ffffff" if abs_val > 0.55 else "#1a202c"
            annotations.append(dict(
                x=labels[j], y=labels[i],
                text=f"{val:.2f}",
                font=dict(color=text_color, size=11, family="Inter, sans-serif"),
                showarrow=False,
            ))

    fig = go.Figure(go.Heatmap(
        z=values,
        x=labels,
        y=labels,
        colorscale=colorscale,
        zmin=-1, zmax=1,
        showscale=True,
        colorbar=dict(title="r", tickvals=[-1, -0.5, 0, 0.5, 1], thickness=14, len=0.85),
        hovertemplate="%{y} × %{x}: %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=dict(l=100, r=60, t=50, b=80),
        title=dict(text="Correlation Heatmap", font=dict(size=14, color="#1a2035"), x=0),
        annotations=annotations,
        xaxis=dict(side="bottom", tickangle=-30),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def chart_rpm_histogram(data: dict) -> go.Figure:
    """Bar histogram — Rotational speed frequency distribution."""
    fig = go.Figure(go.Bar(
        x=data["labels"],
        y=data["values"],
        marker=dict(
            color="rgba(59, 130, 246, 0.75)",
            line=dict(color=COLORS["blue"], width=0.5),
        ),
        hovertemplate="RPM %{x}: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="RPM Frequency Distribution", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(showgrid=False, tickangle=40, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", title="Frequency"),
        showlegend=False,
        bargap=0.05,
    )
    return fig


def chart_tool_wear_histogram(data: dict) -> go.Figure:
    """Bar histogram — Tool wear frequency distribution."""
    fig = go.Figure(go.Bar(
        x=data["labels"],
        y=data["values"],
        marker=dict(
            color="rgba(34, 197, 94, 0.75)",
            line=dict(color=COLORS["green"], width=0.5),
        ),
        hovertemplate="Wear %{x}: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="Tool Wear Distribution", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(showgrid=False, tickangle=40, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", title="Frequency"),
        showlegend=False,
        bargap=0.05,
    )
    return fig


def chart_failure_by_type(data: dict) -> go.Figure:
    """Bar chart — Failure rate (%) per machine type."""
    colors = [COLORS["blue"], COLORS["amber"], COLORS["red"]][:len(data["labels"])]
    fig = go.Figure(go.Bar(
        x=data["labels"],
        y=data["rates"],
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{r}%" for r in data["rates"]],
        textposition="outside",
        hovertemplate="%{x} — Failure Rate: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="Failure Rate by Machine Type", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f1f5f9", title="Failure Rate (%)", ticksuffix="%"),
        showlegend=False,
    )
    return fig


def chart_tool_wear_failure(data: dict) -> go.Figure:
    """Bar chart — Failure rate (%) per tool wear bin."""
    def bar_color(rate):
        if rate < 2:
            return "rgba(34, 197, 94, 0.72)"
        elif rate < 5:
            return "rgba(245, 158, 11, 0.72)"
        return "rgba(239, 68, 68, 0.72)"

    bar_colors = [bar_color(r) for r in data["failure_rates"]]

    fig = go.Figure(go.Bar(
        x=data["labels"],
        y=data["failure_rates"],
        marker=dict(color=bar_colors, line=dict(width=0)),
        hovertemplate="Wear %{x}<br>Failure Rate: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=_DEFAULT_MARGIN,
        title=dict(text="Failure Rate by Tool Wear Range", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(showgrid=False, tickangle=40, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", title="Failure Rate (%)", ticksuffix="%"),
        showlegend=False,
        bargap=0.08,
    )
    return fig


def chart_failure_mode_breakdown(data: dict) -> go.Figure:
    """Horizontal bar chart — count of each failure mode."""
    colors = [COLORS["blue"], COLORS["red"], COLORS["green"],
              COLORS["amber"], COLORS["purple"]][:len(data["labels"])]
    fig = go.Figure(go.Bar(
        y=data["labels"],
        x=data["values"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=data["values"],
        textposition="outside",
        hovertemplate="%{y}: %{x:,} cases<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=dict(l=180, r=60, t=40, b=40),
        title=dict(text="Failure Mode Breakdown", font=dict(size=14, color="#1a2035"), x=0),
        xaxis=dict(gridcolor="#f1f5f9", title="Count"),
        yaxis=dict(showgrid=False),
        showlegend=False,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# NEW CHARTS — Machine Explorer Gauges and Indicators
# ══════════════════════════════════════════════════════════════════════════════

def _gauge_layout(height: int = 220) -> dict:
    return dict(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=70, b=20),
        height=height,
        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#64748b"),
    )


def chart_gauge_temperature(value: float, label: str, unit: str = "K") -> go.Figure:
    """Gauge chart for Air or Process Temperature."""
    # Normal: 295–309, Warning: 309–312, Critical: >312
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": label, "font": {"size": 13, "color": "#1e293b"}},
        number={"suffix": f" {unit}", "font": {"size": 18, "color": "#1e293b"}},
        gauge={
            "axis": {"range": [290, 320], "tickwidth": 1, "tickcolor": "#cbd5e1"},
            "bar": {"color": "#3b82f6", "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [290, 309], "color": "#dcfce7"},
                {"range": [309, 312], "color": "#fef3c7"},
                {"range": [312, 320], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#ef4444", "width": 3},
                "thickness": 0.75,
                "value": 312,
            },
        },
    ))
    fig.update_layout(**_gauge_layout())
    return fig


def chart_gauge_rpm(value: float) -> go.Figure:
    """Gauge chart for Rotational Speed (RPM)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": "Rotational Speed", "font": {"size": 13, "color": "#1e293b"}},
        number={"suffix": " rpm", "font": {"size": 18, "color": "#1e293b"}},
        gauge={
            "axis": {"range": [0, 3000], "tickwidth": 1, "tickcolor": "#cbd5e1"},
            "bar": {"color": "#8b5cf6", "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 1000],   "color": "#fee2e2"},
                {"range": [1000, 1200], "color": "#fef3c7"},
                {"range": [1200, 2000], "color": "#dcfce7"},
                {"range": [2000, 2500], "color": "#fef3c7"},
                {"range": [2500, 3000], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#ef4444", "width": 3},
                "thickness": 0.75,
                "value": 2500,
            },
        },
    ))
    fig.update_layout(**_gauge_layout())
    return fig


def chart_gauge_torque(value: float) -> go.Figure:
    """Gauge chart for Torque."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": "Torque", "font": {"size": 13, "color": "#1e293b"}},
        number={"suffix": " Nm", "font": {"size": 18, "color": "#1e293b"}},
        gauge={
            "axis": {"range": [0, 80], "tickwidth": 1, "tickcolor": "#cbd5e1"},
            "bar": {"color": "#f59e0b", "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 8],  "color": "#dbeafe"},
                {"range": [8, 50], "color": "#dcfce7"},
                {"range": [50, 65], "color": "#fef3c7"},
                {"range": [65, 80], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#ef4444", "width": 3},
                "thickness": 0.75,
                "value": 65,
            },
        },
    ))
    fig.update_layout(**_gauge_layout())
    return fig


def chart_tool_wear_gauge(value: float) -> go.Figure:
    """Gauge / indicator for Tool Wear as a progress-style gauge."""
    # Tool wear max at ~253 min in this dataset
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={"reference": 160, "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#22c55e"}},
        title={"text": "Tool Wear", "font": {"size": 13, "color": "#1e293b"}},
        number={"suffix": " min", "font": {"size": 18, "color": "#1e293b"}},
        gauge={
            "axis": {"range": [0, 253], "tickwidth": 1, "tickcolor": "#cbd5e1"},
            "bar": {"color": "#22c55e" if value <= 100 else "#f59e0b" if value <= 200 else "#ef4444",
                    "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 100],   "color": "#dcfce7"},
                {"range": [100, 160], "color": "#fef9c3"},
                {"range": [160, 220], "color": "#fef3c7"},
                {"range": [220, 253], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#ef4444", "width": 3},
                "thickness": 0.75,
                "value": 220,
            },
        },
    ))
    fig.update_layout(**_gauge_layout())
    return fig


def chart_health_gauge(score: int, category: str, color: str) -> go.Figure:
    """Large health score gauge indicator."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": f"Health Score<br><b>{category}</b>",
               "font": {"size": 14, "color": "#1e293b"}},
        number={"suffix": " / 100", "font": {"size": 24, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#cbd5e1",
                     "tickvals": [0, 25, 50, 75, 100]},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],   "color": "#fee2e2"},
                {"range": [50, 70],  "color": "#fef3c7"},
                {"range": [70, 85],  "color": "#dbeafe"},
                {"range": [85, 100], "color": "#dcfce7"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=80, b=20),
        height=250,
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#64748b"),
    )
    return fig


def chart_temperature_comparison(air_temp: float, proc_temp: float) -> go.Figure:
    """Bar chart comparing air vs process temperature."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Air Temperature", "Process Temperature"],
        y=[air_temp, proc_temp],
        marker=dict(
            color=[
                "#3b82f6" if air_temp <= 309 else "#f59e0b" if air_temp <= 312 else "#ef4444",
                "#22c55e" if proc_temp <= 314 else "#f59e0b" if proc_temp <= 316 else "#ef4444",
            ],
            line=dict(width=0),
        ),
        text=[f"{air_temp:.1f} K", f"{proc_temp:.1f} K"],
        textposition="outside",
        hovertemplate="%{x}: %{y:.1f} K<extra></extra>",
    ))
    # Normal range reference lines
    fig.add_hline(y=309, line_dash="dot", line_color="#f59e0b",
                  annotation_text="Air Warning (309K)", annotation_position="right")
    fig.add_hline(y=314, line_dash="dot", line_color="#f59e0b",
                  annotation_text="Proc Warning (314K)", annotation_position="left")
    fig.update_layout(
        **_CHART_LAYOUT,
        margin=dict(l=20, r=80, t=40, b=40),
        title=dict(text="Temperature Comparison", font=dict(size=14, color="#1a2035"), x=0),
        yaxis=dict(gridcolor="#f1f5f9", title="Temperature (K)", range=[280, max(air_temp, proc_temp) + 10]),
        xaxis=dict(showgrid=False),
        showlegend=False,
        height=280,
    )
    return fig
