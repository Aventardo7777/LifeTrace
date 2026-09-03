"""Counterfactual "what-if" simulation.

Given a chosen variable and a target value, we look for historical days whose
value of that variable is close to the target, and report the *observed* mean
outcomes on those days versus days close to the current value. This is a
matching-based, associative estimate — never a causal claim.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .utils import METRICS

# Variables the user may modify.
MODIFIABLE = [
    "sleep_hours",
    "study_hours",
    "exercise_hours",
    "social_count",
    "entertainment_hours",
    "stress",
]

# Outcome variables we report (excludes the modified variable itself).
OUTCOMES = [
    "sleep_hours",
    "study_hours",
    "exercise_hours",
    "social_count",
    "entertainment_hours",
    "spending",
    "mood",
    "stress",
]

MIN_GROUP = 3

# Default tolerance band per metric kind.
def _tolerance(feature: str) -> float:
    kind = METRICS[feature]["kind"]
    if kind == "time":
        return 0.5
    if kind == "score":
        return 1.0
    if kind == "count":
        return 1.0
    if kind == "money":
        return 30.0
    return 0.5


def _matching_group(df: pd.DataFrame, feature: str, target: float) -> pd.DataFrame:
    """Days whose ``feature`` is closest to ``target`` (at least MIN_GROUP)."""
    if df.empty:
        return df
    tol = _tolerance(feature)
    group = df[(df[feature] - target).abs() <= tol]
    # If too few matches, expand the tolerance progressively.
    factor = 2
    while len(group) < MIN_GROUP and factor <= 16:
        group = df[(df[feature] - target).abs() <= tol * factor]
        factor *= 2
    # Still too few -> take nearest neighbors.
    if len(group) < MIN_GROUP:
        idx = (df[feature] - target).abs().nsmallest(MIN_GROUP).index
        group = df.loc[idx]
    return group


def run_whatif(df: pd.DataFrame, feature: str, current_value: float, target_value: float) -> dict:
    """Compare historical outcomes around ``current_value`` vs ``target_value``."""
    if feature not in MODIFIABLE or feature not in df.columns:
        return {"error": "该变量不可用于模拟"}

    baseline = _matching_group(df, feature, float(current_value))
    counterfactual = _matching_group(df, feature, float(target_value))

    if len(baseline) < MIN_GROUP or len(counterfactual) < MIN_GROUP:
        return {
            "error": "历史数据中匹配的样本不足，无法进行可靠的估计",
            "baseline_n": int(len(baseline)),
            "counterfactual_n": int(len(counterfactual)),
        }

    outcomes = []
    for metric in OUTCOMES:
        if metric == feature or metric not in df.columns:
            continue
        base_mean = float(baseline[metric].mean())
        cf_mean = float(counterfactual[metric].mean())
        delta = cf_mean - base_mean
        pct = (delta / base_mean * 100) if base_mean != 0 else 0.0
        outcomes.append(
            {
                "metric": metric,
                "label": METRICS[metric]["label"],
                "unit": METRICS[metric]["unit"],
                "baseline": round(base_mean, 2),
                "counterfactual": round(cf_mean, 2),
                "delta": round(delta, 2),
                "pct": round(pct, 1),
                "direction": "上升" if delta > 0 else ("下降" if delta < 0 else "基本不变"),
            }
        )

    return {
        "feature": feature,
        "feature_label": METRICS[feature]["label"],
        "feature_unit": METRICS[feature]["unit"],
        "current_value": float(current_value),
        "target_value": float(target_value),
        "baseline_n": int(len(baseline)),
        "counterfactual_n": int(len(counterfactual)),
        "baseline_dates": [d.strftime("%Y-%m-%d") for d in baseline["date"]][:10],
        "counterfactual_dates": [d.strftime("%Y-%m-%d") for d in counterfactual["date"]][:10],
        "outcomes": outcomes,
        "disclaimer": (
            "以上结果是基于历史数据中「相似日期」的平均值对比得出的相关性估计，"
            "不代表因果关系，也不构成任何建议。"
        ),
    }
