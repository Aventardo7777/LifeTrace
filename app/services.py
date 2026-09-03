"""Service layer: compose dashboard & analysis payloads from the database."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from . import crud, stats, visualization
from .analysis import anomaly, clustering, correlation, efficiency, timeseries, whatif
from .analysis.utils import METRICS, records_to_dataframe
from .models import DailyRecord


def load_df(db: Session) -> "object":
    records = crud.list_records(db, order="asc")
    return records_to_dataframe(records)


def _latest_record(db: Session):
    records = crud.list_records(db, order="desc")
    return records[0] if records else None


def dashboard_payload(db: Session) -> dict:
    """Everything the dashboard page needs."""
    df = load_df(db)
    total = int(len(df))
    today = date.today()

    latest = _latest_record(db)
    today_record = None
    if latest and latest.date == today:
        today_record = latest

    week = stats.summary_stats(df, 7)
    month = stats.summary_stats(df, 30)
    prev_week = stats.summary_stats(df.iloc[:-7] if len(df) > 7 else df.head(0), 7)

    anomalies = anomaly.detect_anomalies(df)

    sleep_series = timeseries.daily_series(df, "sleep_hours")
    study_series = timeseries.daily_series(df, "study_hours")
    mood_series = timeseries.daily_series(df, "mood")
    spending_series = timeseries.daily_series(df, "spending")

    return {
        "total_records": total,
        "streak": stats.streak_from_dates([r.date for r in crud.list_records(db, order="asc")]),
        "today_record": today_record,
        "week": week,
        "month": month,
        "prev_week": prev_week,
        "deltas": {
            "avg_sleep": stats.compare_to_previous(week, prev_week, "avg_sleep"),
            "avg_study": stats.compare_to_previous(week, prev_week, "avg_study"),
            "avg_mood": stats.compare_to_previous(week, prev_week, "avg_mood"),
        },
        "anomaly_summary": {
            "count": len(anomalies),
            "recent": anomalies[:3],
        },
        "correlations": correlation.correlation_pairs(df),
        "charts": {
            "sleep": visualization.to_json(visualization.trend_chart(sleep_series)),
            "study": visualization.to_json(visualization.trend_chart(study_series)),
            "mood": visualization.to_json(visualization.trend_chart(mood_series)),
            "spending": visualization.to_json(visualization.trend_chart(spending_series)),
            "heatmap": visualization.to_json(visualization.correlation_heatmap(correlation.correlation_matrix(df))),
        },
    }


def analysis_payload(db: Session) -> dict:
    """Everything the analysis page needs."""
    df = load_df(db)

    corr_matrix = correlation.correlation_matrix(df)
    corr_pairs = correlation.correlation_pairs(df)
    clusters = clustering.cluster_days(df)
    anomalies = anomaly.detect_anomalies(df)
    eff = efficiency.train_efficiency_model(df)
    initial_scatter = visualization.scatter_chart(df, "sleep_hours", "mood")
    initial_series = timeseries.daily_series(df, "sleep_hours")

    return {
        "n": int(len(df)),
        "correlation_pairs": corr_pairs,
        "correlation_columns": corr_matrix["columns"],
        "charts": {
            "heatmap": visualization.to_json(visualization.correlation_heatmap(corr_matrix)),
            "cluster": visualization.to_json(visualization.cluster_projection(df, clusters)),
            "anomaly": visualization.to_json(visualization.anomaly_timeline(df, anomalies)),
            "radar": visualization.to_json(visualization.monthly_radar(df)),
            "importance": visualization.to_json(visualization.feature_importance_bar(eff.get("ranked", []))),
            "scatter": visualization.to_json(initial_scatter),
            "timeseries": visualization.to_json(visualization.trend_chart(initial_series)),
        },
        "clusters": clusters,
        "anomalies": anomalies,
        "efficiency": eff,
        "metrics": METRICS,
        "modifiable": whatif.MODIFIABLE,
    }


def timeseries_payload(db: Session, metric: str, granularity: str) -> dict:
    df = load_df(db)
    series = timeseries.resample_series(df, metric, granularity)
    return {
        "series": series,
        "chart": visualization.to_json(visualization.trend_chart(series)),
    }


def scatter_payload(db: Session, x: str, y: str) -> dict:
    df = load_df(db)
    return {
        "chart": visualization.to_json(visualization.scatter_chart(df, x, y)),
        "x": x,
        "y": y,
    }


def whatif_payload(db: Session, feature: str, current: float, target: float) -> dict:
    df = load_df(db)
    result = whatif.run_whatif(df, feature, current, target)
    if "error" not in result:
        result["chart"] = visualization.to_json(visualization.whatif_bar(result))
    return result


def efficiency_predict_payload(db: Session, inputs: dict) -> dict:
    df = load_df(db)
    return efficiency.predict_state_score(df, inputs)
