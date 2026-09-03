"""Pure, unit-testable statistics helpers (no database access)."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from .analysis.utils import METRICS


def streak_from_dates(dates: list[date], today: date | None = None) -> int:
    """Consecutive-day streak ending today (or yesterday if today is missing)."""
    if not dates:
        return 0
    present = set(dates)
    anchor = today or date.today()
    if anchor not in present:
        anchor -= timedelta(days=1)
    streak = 0
    while anchor in present:
        streak += 1
        anchor -= timedelta(days=1)
    return streak


def last_n(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """Return the most recent ``days`` rows (by date)."""
    if df.empty:
        return df
    return df.tail(days)


def mean_of(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return round(float(df[col].mean()), 2)


def plan_completion_rate(df: pd.DataFrame) -> float:
    if df.empty or "plan_completed" not in df.columns:
        return 0.0
    return round(float(df["plan_completed"].mean()) * 100, 1)


def exercise_days(df: pd.DataFrame, threshold: float = 0.5) -> int:
    if df.empty or "exercise_hours" not in df.columns:
        return 0
    return int((df["exercise_hours"] >= threshold).sum())


def spending_total(df: pd.DataFrame) -> float:
    if df.empty or "spending" not in df.columns:
        return 0.0
    return round(float(df["spending"].sum()), 2)


def summary_stats(df: pd.DataFrame, days: int | None = None) -> dict:
    """Aggregate statistics over the last ``days`` (or all if None)."""
    window = last_n(df, days) if days else df
    return {
        "n": int(len(window)),
        "avg_sleep": mean_of(window, "sleep_hours"),
        "avg_study": mean_of(window, "study_hours"),
        "avg_exercise": mean_of(window, "exercise_hours"),
        "avg_entertainment": mean_of(window, "entertainment_hours"),
        "avg_mood": mean_of(window, "mood"),
        "avg_stress": mean_of(window, "stress"),
        "total_spending": spending_total(window),
        "exercise_days": exercise_days(window),
        "plan_completion_rate": plan_completion_rate(window),
        "stay_up_rate": round(float(window["stay_up_late"].mean()) * 100, 1) if not window.empty and "stay_up_late" in window.columns else 0.0,
    }


def compare_to_previous(current: dict, previous: dict, key: str) -> float:
    """Percentage change of ``current[key]`` vs ``previous[key]``."""
    if not previous.get(key):
        return 0.0
    return round((current[key] - previous[key]) / previous[key] * 100, 1)
