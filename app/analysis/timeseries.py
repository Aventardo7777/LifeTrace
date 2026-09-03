"""Time-series aggregation and moving-average computation."""

from __future__ import annotations

import pandas as pd

from .utils import METRICS

# Display window size for the moving average (days).
DEFAULT_MA_WINDOW = 7


def daily_series(df: pd.DataFrame, metric: str, window: int = DEFAULT_MA_WINDOW) -> dict:
    """Daily values + a moving average for a single metric."""
    if metric not in df.columns:
        return {"dates": [], "values": [], "ma": []}
    series = df.set_index("date")[metric].sort_index()
    ma = series.rolling(window=window, min_periods=1).mean()
    return {
        "metric": metric,
        "label": METRICS[metric]["label"],
        "unit": METRICS[metric]["unit"],
        "dates": [d.strftime("%Y-%m-%d") for d in series.index],
        "values": [round(float(v), 2) for v in series.values],
        "ma": [round(float(v), 2) for v in ma.values],
    }


def weekly_series(df: pd.DataFrame, metric: str) -> dict:
    """Weekly means (ISO weeks) for a single metric."""
    if df.empty or metric not in df.columns:
        return {"dates": [], "values": []}
    g = df.set_index("date")[metric].resample("W-MON").mean().dropna()
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in g.index],
        "values": [round(float(v), 2) for v in g.values],
    }


def monthly_series(df: pd.DataFrame, metric: str) -> dict:
    """Monthly means for a single metric."""
    if df.empty or metric not in df.columns:
        return {"dates": [], "values": []}
    g = df.set_index("date")[metric].resample("ME").mean().dropna()
    return {
        "dates": [d.strftime("%Y-%m") for d in g.index],
        "values": [round(float(v), 2) for v in g.values],
    }


def resample_series(df: pd.DataFrame, metric: str, granularity: str) -> dict:
    """Dispatch to daily/weekly/monthly series builders."""
    granularity = (granularity or "day").lower()
    if granularity == "week":
        return weekly_series(df, metric)
    if granularity == "month":
        return monthly_series(df, metric)
    return daily_series(df, metric)
