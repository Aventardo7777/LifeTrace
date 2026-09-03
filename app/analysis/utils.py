"""Shared utilities and field metadata for the analysis layer."""

from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from ..models import DailyRecord

# Numeric metrics used throughout the analysis.
# Each entry: (field_name, display_label, unit, kind)
# kind: "time" | "count" | "money" | "score" | "bool"
METRICS: dict[str, dict[str, str]] = {
    "sleep_hours": {"label": "睡眠", "unit": "小时", "kind": "time"},
    "study_hours": {"label": "学习", "unit": "小时", "kind": "time"},
    "exercise_hours": {"label": "运动", "unit": "小时", "kind": "time"},
    "entertainment_hours": {"label": "娱乐", "unit": "小时", "kind": "time"},
    "social_count": {"label": "社交次数", "unit": "次", "kind": "count"},
    "spending": {"label": "消费", "unit": "元", "kind": "money"},
    "mood": {"label": "心情", "unit": "分", "kind": "score"},
    "stress": {"label": "压力", "unit": "分", "kind": "score"},
}

NUMERIC_COLUMNS = list(METRICS.keys())

# The six behavioral dimensions used for clustering (per spec).
CLUSTER_FEATURES = [
    "sleep_hours",
    "study_hours",
    "exercise_hours",
    "social_count",
    "entertainment_hours",
    "mood",
]


def records_to_dataframe(records: Sequence[DailyRecord]) -> pd.DataFrame:
    """Convert ORM records into a pandas DataFrame sorted by date ascending."""
    rows = [
        {
            "date": r.date,
            "sleep_hours": r.sleep_hours,
            "study_hours": r.study_hours,
            "exercise_hours": r.exercise_hours,
            "entertainment_hours": r.entertainment_hours,
            "social_count": r.social_count,
            "spending": r.spending,
            "mood": r.mood,
            "stress": r.stress,
            "stay_up_late": int(r.stay_up_late),
            "plan_completed": int(r.plan_completed),
            "weather": r.weather,
        }
        for r in records
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=["date"] + NUMERIC_COLUMNS + ["stay_up_late", "plan_completed", "weather"]
        )
        df["date"] = pd.to_datetime(df["date"])
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def safe_mean(values: Any) -> float:
    """Mean that returns 0.0 for empty input."""
    s = pd.Series(values, dtype="float64")
    if s.empty or s.isna().all():
        return 0.0
    return float(s.mean())


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
