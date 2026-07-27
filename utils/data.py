"""
utils/data.py — Data loading, filtering, and all compute helper functions.

All logic preserved from the original app.py. Extended with failure-type filter.
"""

import numpy as np
import pandas as pd
import streamlit as st

CSV_PATH = "ai4i2020.csv"

FAILURE_TYPE_COLS = {
    "TWF": "Tool Wear (TWF)",
    "HDF": "Heat Dissipation (HDF)",
    "PWF": "Power Failure (PWF)",
    "OSF": "Overstrain (OSF)",
    "RNF": "Random (RNF)",
}

# ── Data Loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and deduplicate the dataset once; cached across reruns."""
    df = pd.read_csv(CSV_PATH)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ── Filtering ─────────────────────────────────────────────────────────────────

def filter_dataframe(
    df: pd.DataFrame,
    machine_types=None,
    failure_status: str = "all",
    failure_types=None,
) -> pd.DataFrame:
    """Return a filtered copy of the dataset based on sidebar selections."""
    result = df.copy()

    # Machine type filter
    if machine_types:
        result = result[result["Type"].isin(machine_types)]

    # Failure status filter
    if failure_status == "failed":
        result = result[result["Machine failure"] == 1]
    elif failure_status == "no_failure":
        result = result[result["Machine failure"] == 0]

    # Failure type filter — only meaningful when failure_status == "failed"
    if (
        failure_types
        and failure_status == "failed"
        and set(failure_types) != set(FAILURE_TYPE_COLS.keys())
    ):
        mask = pd.Series(False, index=result.index)
        for ft in failure_types:
            if ft in result.columns:
                mask = mask | (result[ft] == 1)
        result = result[mask]

    return result


# ── KPI Computations ──────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    """Return top-level KPI numbers for the dashboard cards."""
    return {
        "total_records":  len(df),
        "total_features": df.shape[1],
        "total_failures": int(df["Machine failure"].sum()),
        "machine_types":  int(df["Type"].nunique()),
        "failure_rate":   round(df["Machine failure"].mean() * 100, 2),
        "healthy_count":  int((df["Machine failure"] == 0).sum()),
    }


def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics as a DataFrame."""
    num_cols = [
        "Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
    ]
    stats = df[num_cols].describe().round(3).T.reset_index()
    stats.columns = ["Feature", "Count", "Mean", "Std", "Min", "25%", "50%", "75%", "Max"]
    return stats


def compute_correlation_matrix(df: pd.DataFrame) -> dict:
    """Return the Pearson correlation matrix for all numerical features."""
    num_cols = [
        "Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
        "Machine failure",
    ]
    corr = df[num_cols].corr().round(3)
    short_labels = ["Air Temp", "Proc Temp", "RPM", "Torque", "Tool Wear", "Failure"]
    return {
        "labels":      short_labels,
        "values":      corr.values.tolist(),
        "full_labels": num_cols,
    }


def compute_failure_distribution(df: pd.DataFrame) -> dict:
    """Return counts for failure vs no-failure."""
    counts = df["Machine failure"].value_counts().sort_index()
    return {
        "labels": ["No Failure", "Failure"],
        "values": [int(counts.get(0, 0)), int(counts.get(1, 0))],
    }


def compute_type_distribution(df: pd.DataFrame) -> dict:
    """Return machine type counts sorted consistently."""
    counts = df["Type"].value_counts()
    order = [t for t in ["L", "M", "H"] if t in counts.index]
    label_map = {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}
    return {
        "labels": [label_map[t] for t in order],
        "values": [int(counts[t]) for t in order],
    }


def compute_rpm_histogram(df: pd.DataFrame, bins: int = 30) -> dict:
    """Bin rotational speed values for a histogram chart."""
    col = df["Rotational speed [rpm]"].dropna()
    counts, edges = np.histogram(col, bins=bins)
    labels = [f"{int(edges[i])}–{int(edges[i+1])}" for i in range(len(edges) - 1)]
    return {"labels": labels, "values": counts.tolist()}


def compute_tool_wear_histogram(df: pd.DataFrame, bins: int = 30) -> dict:
    """Bin tool wear values for a histogram chart."""
    col = df["Tool wear [min]"].dropna()
    counts, edges = np.histogram(col, bins=bins)
    labels = [f"{int(edges[i])}–{int(edges[i+1])}" for i in range(len(edges) - 1)]
    return {"labels": labels, "values": counts.tolist()}


def compute_failure_by_type(df: pd.DataFrame) -> dict:
    """Return failure rate per machine type."""
    result = (
        df.groupby("Type")["Machine failure"]
        .agg(failures="sum", total="count")
        .reset_index()
    )
    result["rate"] = (result["failures"] / result["total"] * 100).round(2)
    order_map = {"L": "Low (L)", "M": "Medium (M)", "H": "High (H)"}
    return {
        "labels":   [order_map.get(t, t) for t in result["Type"]],
        "failures": result["failures"].tolist(),
        "rates":    result["rate"].tolist(),
    }


def compute_tool_wear_by_failure(df: pd.DataFrame) -> dict:
    """Return binned tool wear ranges and the failure rate within each bin."""
    tmp = df.copy()
    tmp["Wear Bin"] = pd.cut(tmp["Tool wear [min]"], bins=10)
    grouped = tmp.groupby("Wear Bin", observed=True)["Machine failure"].agg(["mean", "count"])
    grouped["failure_rate"] = (grouped["mean"] * 100).round(2)
    return {
        "labels":        [str(idx) for idx in grouped.index],
        "failure_rates": grouped["failure_rate"].tolist(),
        "counts":        grouped["count"].tolist(),
    }


def build_dataset_preview(df: pd.DataFrame, n: int = 10) -> dict:
    """Return the first n rows and column metadata for the preview table."""
    preview = df.head(n).replace({float("nan"): None})
    return {
        "columns": list(preview.columns),
        "rows":    preview.values.tolist(),
        "shape":   {"rows": len(df), "cols": df.shape[1]},
    }


def compute_failure_mode_breakdown(df: pd.DataFrame) -> dict:
    """Count occurrences of each failure mode flag."""
    mode_map = {
        "TWF": "Tool Wear (TWF)",
        "HDF": "Heat Dissipation (HDF)",
        "PWF": "Power (PWF)",
        "OSF": "Overstrain (OSF)",
        "RNF": "Random (RNF)",
    }
    counts = {label: int(df[col].sum()) for col, label in mode_map.items()}
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "labels": [item[0] for item in sorted_items],
        "values": [item[1] for item in sorted_items],
    }


def compute_temperature_analysis(df: pd.DataFrame) -> dict:
    """Return grouped temperature stats for box-plot style analysis."""
    return {
        "air_temp":  df["Air temperature [K]"].dropna().tolist(),
        "proc_temp": df["Process temperature [K]"].dropna().tolist(),
        "air_by_failure": {
            "failed": df[df["Machine failure"] == 1]["Air temperature [K]"].dropna().tolist(),
            "ok":     df[df["Machine failure"] == 0]["Air temperature [K]"].dropna().tolist(),
        },
        "proc_by_failure": {
            "failed": df[df["Machine failure"] == 1]["Process temperature [K]"].dropna().tolist(),
            "ok":     df[df["Machine failure"] == 0]["Process temperature [K]"].dropna().tolist(),
        },
    }


def compute_torque_analysis(df: pd.DataFrame) -> dict:
    """Return torque data for analysis."""
    return {
        "torque": df["Torque [Nm]"].dropna().tolist(),
        "torque_by_failure": {
            "failed": df[df["Machine failure"] == 1]["Torque [Nm]"].dropna().tolist(),
            "ok":     df[df["Machine failure"] == 0]["Torque [Nm]"].dropna().tolist(),
        },
    }
