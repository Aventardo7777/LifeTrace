"""Plotly figure builders.

Every figure is returned as a ``plotly.graph_objects.Figure``. Templates
serialize them to JSON and render them client-side with plotly.js, so no
server-side rendering or external CDN is required at runtime.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .analysis.utils import METRICS

# --- Design tokens (light, modern, data-product aesthetic) -------------------
PRIMARY = "#4F46E5"
SECONDARY = "#10B981"
ACCENT = "#F59E0B"
NEGATIVE = "#EF4444"
POSITIVE = "#10B981"
INK = "#0F172A"
MUTED = "#64748B"
GRID = "#E2E8F0"

SERIES_COLORS = [
    "#4F46E5", "#10B981", "#F59E0B", "#EF4444",
    "#06B6D4", "#8B5CF6", "#EC4899", "#84CC16",
]

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def _base_layout(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        font=dict(family="Inter, 'Segoe UI', sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID),
        hoverlabel=dict(bgcolor="white", font_color=INK),
    )
    return fig


def to_json(fig: go.Figure) -> str:
    return fig.to_json()


# --- Trend line --------------------------------------------------------------
def trend_chart(series: dict, moving_avg: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=series.get("dates", []),
            y=series.get("values", []),
            mode="lines+markers",
            name=series.get("label", "数值"),
            line=dict(color=PRIMARY, width=2),
            marker=dict(size=5, color=PRIMARY),
            hovertemplate="%{x}<br>%{y} " + series.get("unit", "") + "<extra></extra>",
        )
    )
    if moving_avg and series.get("ma"):
        fig.add_trace(
            go.Scatter(
                x=series.get("dates", []),
                y=series.get("ma", []),
                mode="lines",
                name="移动平均",
                line=dict(color=ACCENT, width=2, dash="dash"),
                hovertemplate="移动平均 %{y}<extra></extra>",
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0))
    return _base_layout(fig, height=300)


# --- Correlation heatmap -----------------------------------------------------
def correlation_heatmap(matrix: dict) -> go.Figure:
    labels = matrix.get("labels", [])
    values = matrix.get("values", [])
    fig = go.Figure(
        go.Heatmap(
            z=values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, "#EF4444"],
                [0.5, "#F8FAFC"],
                [1.0, "#4F46E5"],
            ],
            colorbar=dict(title="r", thickness=12, len=0.8),
            hovertemplate="%{y} × %{x}<br>r = %{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(height=380, margin=dict(l=8, r=8, t=20, b=8))
    return _base_layout(fig, height=380)


# --- Scatter with trend line -------------------------------------------------
def scatter_chart(
    df: pd.DataFrame, x: str, y: str, color: str = PRIMARY
) -> go.Figure:
    x_label = METRICS.get(x, {}).get("label", x)
    y_label = METRICS.get(y, {}).get("label", y)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="markers",
            name="记录",
            marker=dict(size=8, color=color, opacity=0.65, line=dict(width=0)),
            hovertemplate=f"{x_label} %{{x}}<br>{y_label} %{{y}}<extra></extra>",
        )
    )
    # OLS trend line (simple, associative).
    if len(df) >= 3:
        slope, intercept = np.polyfit(df[x], df[y], 1)
        xs = np.linspace(df[x].min(), df[x].max(), 50)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=slope * xs + intercept,
                mode="lines",
                name="趋势线",
                line=dict(color=ACCENT, width=2, dash="dot"),
                hovertemplate="趋势<extra></extra>",
            )
        )
    fig.update_xaxes(title=x_label)
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, height=320)


# --- Cluster projection ------------------------------------------------------
def cluster_projection(df: pd.DataFrame, clusters: dict) -> go.Figure:
    features = clusters.get("features", [])
    if df.empty or len(features) < 2:
        return _base_layout(go.Figure(), height=340)

    X = StandardScaler().fit_transform(df[features].values.astype(float))
    proj = PCA(n_components=2, random_state=42).fit_transform(X)
    labels = clusters.get("labels", [])
    label_names = clusters.get("label_names", {})

    fig = go.Figure()
    if labels:
        unique = sorted(set(labels))
        for i, cid in enumerate(unique):
            mask = np.array(labels) == cid
            name = label_names.get(int(cid), f"类别 {cid}")
            fig.add_trace(
                go.Scatter(
                    x=proj[mask, 0],
                    y=proj[mask, 1],
                    mode="markers",
                    name=name,
                    marker=dict(size=10, opacity=0.75, color=SERIES_COLORS[i % len(SERIES_COLORS)]),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=[d for d, m in zip(clusters.get("dates", []), mask) if m],
                )
            )
    fig.update_xaxes(title="主成分 1", showticklabels=False)
    fig.update_yaxes(title="主成分 2", showticklabels=False)
    return _base_layout(fig, height=340)


# --- Anomaly timeline --------------------------------------------------------
def anomaly_timeline(df: pd.DataFrame, anomalies: list[dict]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["mood"] if "mood" in df.columns else df["study_hours"],
            mode="lines",
            name="心情",
            line=dict(color=MUTED, width=1.5),
            hovertemplate="%{x}<br>心情 %{y}<extra></extra>",
        )
    )
    if anomalies:
        anom_dates = [a["date"] for a in anomalies]
        anom_df = df[df["date"].dt.strftime("%Y-%m-%d").isin(anom_dates)]
        fig.add_trace(
            go.Scatter(
                x=anom_df["date"],
                y=anom_df["mood"] if "mood" in anom_df.columns else anom_df["study_hours"],
                mode="markers",
                name="异常日",
                marker=dict(size=10, color=NEGATIVE, symbol="x", line=dict(width=1, color="white")),
                hovertemplate="%{x}<br>异常日<extra></extra>",
            )
        )
    return _base_layout(fig, height=300)


# --- Monthly radar -----------------------------------------------------------
def monthly_radar(df: pd.DataFrame) -> go.Figure:
    """Radar comparing the current month vs. the previous month (normalized)."""
    metrics = ["sleep_hours", "study_hours", "exercise_hours",
               "social_count", "entertainment_hours", "mood"]
    if df.empty:
        return _base_layout(go.Figure(), height=340)

    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    months = sorted(df["month"].unique())
    if len(months) < 1:
        return _base_layout(go.Figure(), height=340)

    current = months[-1]
    previous = months[-2] if len(months) >= 2 else None

    # Normalize each metric by its dataset max -> 0..100.
    maxes = {m: float(df[m].max()) or 1.0 for m in metrics}

    def profile(month):
        sub = df[df["month"] == month]
        return [round(float(sub[m].mean()) / maxes[m] * 100, 1) for m in metrics]

    labels = [METRICS[m]["label"] for m in metrics]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=profile(current) + [profile(current)[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=f"本月（{current}）",
            line=dict(color=PRIMARY),
            fillcolor="rgba(79,70,229,0.18)",
        )
    )
    if previous:
        fig.add_trace(
            go.Scatterpolar(
                r=profile(previous) + [profile(previous)[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name=f"上月（{previous}）",
                line=dict(color=MUTED, dash="dash"),
                fillcolor="rgba(100,116,139,0.10)",
            )
        )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[25, 50, 75, 100],
                            ticktext=["25", "50", "75", "100"], color=MUTED),
            angularaxis=dict(color=INK),
        ),
        legend=dict(orientation="h", y=1.15),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_layout(template="plotly_white", font=dict(family="Inter, sans-serif", color=INK, size=12),
                      paper_bgcolor="rgba(0,0,0,0)", height=360)
    return fig


# --- What-if comparison ------------------------------------------------------
def whatif_bar(result: dict) -> go.Figure:
    outcomes = result.get("outcomes", [])
    if not outcomes:
        return _base_layout(go.Figure(), height=300)
    labels = [o["label"] for o in outcomes]
    baseline = [o["baseline"] for o in outcomes]
    cf = [o["counterfactual"] for o in outcomes]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="当前", x=labels, y=baseline, marker_color=MUTED, opacity=0.85))
    fig.add_trace(go.Bar(name="调整后（估计）", x=labels, y=cf, marker_color=PRIMARY))
    fig.update_layout(barmode="group", legend=dict(orientation="h", y=1.12))
    return _base_layout(fig, height=320)


# --- Feature importance ------------------------------------------------------
def feature_importance_bar(ranked: list[dict]) -> go.Figure:
    if not ranked:
        return _base_layout(go.Figure(), height=300)
    labels = [r["label"] for r in ranked]
    vals = [r["standardized"] for r in ranked]
    colors = [POSITIVE if v >= 0 else NEGATIVE for v in vals]
    fig = go.Figure(
        go.Bar(
            x=vals,
            y=labels,
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}: %{x:.2f}<extra></extra>",
        )
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _base_layout(fig, height=300)
