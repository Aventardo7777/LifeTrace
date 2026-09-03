"""Statistics tests: correlation, moving average, streak, clustering,
efficiency model, and what-if simulation."""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.analysis import clustering, correlation, efficiency, timeseries, whatif
from app.analysis.utils import records_to_dataframe
from app.demo import generate_demo_data
from app.stats import streak_from_dates


def _demo_df(days: int = 60) -> pd.DataFrame:
    records = generate_demo_data(days=days)
    # Records are dicts; convert to a DataFrame directly via records_to_dataframe
    # by wrapping into a lightweight namespace-like object is unnecessary — we
    # build the DataFrame from the dicts directly here for speed.
    from app.analysis.utils import NUMERIC_COLUMNS

    rows = []
    for r in records:
        rows.append(
            {
                "date": pd.to_datetime(r["date"]),
                "sleep_hours": r["sleep_hours"],
                "study_hours": r["study_hours"],
                "exercise_hours": r["exercise_hours"],
                "entertainment_hours": r["entertainment_hours"],
                "social_count": r["social_count"],
                "spending": r["spending"],
                "mood": r["mood"],
                "stress": r["stress"],
                "stay_up_late": int(r["stay_up_late"]),
                "plan_completed": int(r["plan_completed"]),
                "weather": r["weather"],
            }
        )
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def test_pearson_perfect_positive():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    res = correlation.pearson_pair(df["x"], df["y"])
    assert res is not None
    assert abs(res["r"] - 1.0) < 1e-6


def test_moving_average_length():
    df = _demo_df(30)
    s = timeseries.daily_series(df, "mood")
    assert len(s["values"]) == 30
    assert len(s["ma"]) == 30


def test_streak_ends_today():
    days = [date(2026, 3, 3), date(2026, 3, 4), date(2026, 3, 5)]
    assert streak_from_dates(days, today=date(2026, 3, 5)) == 3


def test_streak_breaks():
    days = [date(2026, 3, 1), date(2026, 3, 2), date(2026, 3, 5)]
    assert streak_from_dates(days, today=date(2026, 3, 5)) == 1


def test_clustering_produces_labels():
    df = _demo_df(60)
    result = clustering.cluster_days(df)
    assert result["k"] >= 2
    assert len(result["clusters"]) == result["k"]
    for c in result["clusters"]:
        assert c["name"].endswith("日")
        assert c["size"] > 0


def test_efficiency_model_trains():
    df = _demo_df(60)
    result = efficiency.train_efficiency_model(df)
    assert result["trained"] is True
    assert "r2_train" in result
    assert len(result["ranked"]) > 0


def test_whatif_returns_outcomes_and_disclaimer():
    df = _demo_df(60)
    result = whatif.run_whatif(df, "sleep_hours", 5.0, 7.0)
    assert "error" not in result
    assert len(result["outcomes"]) > 0
    assert "因果关系" in result["disclaimer"]
