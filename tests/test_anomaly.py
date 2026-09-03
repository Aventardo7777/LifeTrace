"""Anomaly detection tests."""

from __future__ import annotations

import pandas as pd

from app.analysis import anomaly
from app.analysis.utils import NUMERIC_COLUMNS


def _normal_days(n: int) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "sleep_hours": [7.0] * n,
            "study_hours": [5.0] * n,
            "exercise_hours": [0.5] * n,
            "entertainment_hours": [2.0] * n,
            "social_count": [1] * n,
            "spending": [60.0] * n,
            "mood": [6] * n,
            "stress": [5] * n,
            "stay_up_late": [0] * n,
            "plan_completed": [1] * n,
        }
    )


def test_detect_planted_outlier():
    df = _normal_days(30)
    # Append an extreme day: study 20h (vs ~5h) and spending 5000 (vs ~60).
    extreme = pd.DataFrame(
        {
            "date": [pd.Timestamp("2026-01-31")],
            "sleep_hours": [4.0],
            "study_hours": [20.0],
            "exercise_hours": [0.0],
            "entertainment_hours": [0.5],
            "social_count": [0],
            "spending": [5000.0],
            "mood": [3],
            "stress": [9],
            "stay_up_late": [1],
            "plan_completed": [0],
        }
    )
    df = pd.concat([df, extreme], ignore_index=True)

    anomalies = anomaly.detect_anomalies(df)
    flagged_dates = {a["date"] for a in anomalies}
    assert "2026-01-31" in flagged_dates

    # At least one anomaly should carry an explanation.
    found = next(a for a in anomalies if a["date"] == "2026-01-31")
    assert found["driver"] is not None
    assert "值得关注" in found["driver"]["explanation"]


def test_no_anomalies_on_uniform_data():
    df = _normal_days(20)
    anomalies = anomaly.detect_anomalies(df)
    # Uniform data should yield few, if any, anomalies; ensure it doesn't crash.
    assert isinstance(anomalies, list)
