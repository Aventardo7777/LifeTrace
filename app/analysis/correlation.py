"""Pearson correlation analysis with significance testing."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from .utils import METRICS, NUMERIC_COLUMNS

# The headline pairs shown on the dashboard (per spec).
DEFAULT_PAIRS = [
    ("sleep_hours", "mood"),
    ("sleep_hours", "study_hours"),
    ("exercise_hours", "mood"),
    ("social_count", "mood"),
    ("spending", "stress"),
]


def pearson_pair(x: pd.Series, y: pd.Series) -> Optional[dict]:
    """Compute Pearson r and two-tailed p-value for two series.

    Returns None if either series has < 3 valid observations or no variance.
    """
    mask = x.notna() & y.notna()
    xs, ys = x[mask], y[mask]
    if len(xs) < 3 or xs.nunique() < 2 or ys.nunique() < 2:
        return None
    r, p = stats.pearsonr(xs, ys)
    return {"r": float(r), "p": float(p), "n": int(len(xs))}


def correlation_pairs(
    df: pd.DataFrame, pairs: Optional[list[tuple[str, str]]] = None
) -> list[dict]:
    """Compute correlations for the requested pairs (defaults to DEFAULT_PAIRS)."""
    pairs = pairs or DEFAULT_PAIRS
    results = []
    for a, b in pairs:
        if a not in df.columns or b not in df.columns:
            continue
        res = pearson_pair(df[a], df[b])
        if res is None:
            continue
        results.append(
            {
                "x": a,
                "y": b,
                "x_label": METRICS[a]["label"],
                "y_label": METRICS[b]["label"],
                "r": res["r"],
                "p": res["p"],
                "n": res["n"],
                "significant": res["p"] < 0.05,
                "strength": describe_strength(res["r"]),
            }
        )
    return results


def correlation_matrix(df: pd.DataFrame) -> dict:
    """Full numeric correlation matrix (r only) for the heatmap."""
    cols = [c for c in NUMERIC_COLUMNS if c in df.columns]
    sub = df[cols]
    corr = sub.corr().round(3).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return {
        "columns": cols,
        "labels": [METRICS[c]["label"] for c in cols],
        "values": corr.values.tolist(),
    }


def describe_strength(r: float) -> str:
    """Human-readable strength label for a correlation coefficient."""
    a = abs(r)
    if a >= 0.7:
        return "强"
    if a >= 0.4:
        return "中等"
    if a >= 0.2:
        return "弱"
    return "极弱"


def interpret_correlation(r: float) -> str:
    """A short, cautious interpretation of a correlation coefficient."""
    if abs(r) < 0.1:
        direction = "几乎无关"
    elif r > 0:
        direction = "正向相关"
    else:
        direction = "负向相关"
    return f"{direction}（{describe_strength(r)}）"
