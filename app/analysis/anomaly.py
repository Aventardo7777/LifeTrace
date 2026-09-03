"""Anomaly detection for daily records.

Combines two complementary signals:
1. IsolationForest on the standardized numeric feature space (global outliers).
2. Per-metric z-score vs. a trailing 30-day baseline (metric-level outliers).

Each flagged day receives a plain-language, evidence-based explanation such as
"你的学习时长比过去 30 天平均水平低 42%。"
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .utils import METRICS, NUMERIC_COLUMNS

MIN_RECORDS_ISOFOREST = 14
BASELINE_WINDOW = 30
MIN_BASELINE = 7
Z_THRESHOLD = 2.5
DEFAULT_CONTAMINATION = 0.1


def _trailing_baseline(df: pd.DataFrame, idx: int, metric: str) -> tuple[float, float]:
    """Mean and std of ``metric`` over the BASELINE_WINDOW days before idx."""
    start = max(0, idx - BASELINE_WINDOW)
    window = df.iloc[start:idx][metric]
    if len(window) < MIN_BASELINE:
        # Fall back to the whole series excluding the current day.
        window = pd.concat([df.iloc[:idx][metric], df.iloc[idx + 1 :][metric]])
    window = window.dropna()
    if len(window) < MIN_BASELINE:
        return float("nan"), float("nan")
    return float(window.mean()), float(window.std())


def detect_anomalies(
    df: pd.DataFrame, contamination: float = DEFAULT_CONTAMINATION
) -> list[dict]:
    """Return a list of anomalous-day dictionaries, newest first."""
    if df.empty or "date" not in df.columns:
        return []

    numeric = [c for c in NUMERIC_COLUMNS if c in df.columns]
    feature_matrix = df[numeric].values.astype(float)

    iso_outliers: set[int] = set()
    if len(df) >= MIN_RECORDS_ISOFOREST and feature_matrix.shape[1] >= 2:
        X = StandardScaler().fit_transform(feature_matrix)
        clf = IsolationForest(
            random_state=42, contamination=contamination, n_estimators=200
        )
        labels = clf.fit_predict(X)
        iso_outliers = {i for i, lab in enumerate(labels) if lab == -1}

    anomalies: list[dict] = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        day = row["date"]

        metric_flags = []
        z_all = []
        for metric in numeric:
            value = float(row[metric])
            mean, std = _trailing_baseline(df, idx, metric)
            if np.isnan(mean) or np.isnan(std):
                continue
            if std == 0:
                # Degenerate baseline (all identical): any deviation is extreme.
                z = 0.0 if value == mean else 4.0
            else:
                z = (value - mean) / std
            z_all.append((metric, value, mean, std, z))
            if abs(z) >= Z_THRESHOLD:
                metric_flags.append((metric, value, mean, std, z))

        is_anomaly = (idx in iso_outliers) or bool(metric_flags)

        if not is_anomaly:
            continue

        # Choose the single most informative "driver" metric.
        driver = None
        candidates = metric_flags or z_all
        if candidates:
            _, value, mean, std, z = max(candidates, key=lambda t: abs(t[4]))
            pct = ((value - mean) / mean) * 100 if mean != 0 else 0.0
            direction = "低" if pct < 0 else "高"
            hard = bool(metric_flags)
            driver = {
                "metric": _,
                "label": METRICS[_]["label"],
                "unit": METRICS[_]["unit"],
                "value": round(value, 2),
                "baseline_mean": round(mean, 2),
                "pct_change": round(abs(pct), 1),
                "direction": direction,
                "z": round(z, 2),
                "explanation": (
                    f"你的 {day.strftime('%m月%d日')} 的「{METRICS[_]['label']}」为 "
                    f"{value:.2f} {METRICS[_]['unit']}，比过去 {BASELINE_WINDOW} 天"
                    f"平均水平（{mean:.2f} {METRICS[_]['unit']}）{direction} "
                    f"{abs(pct):.1f}%。"
                    f"{'值得关注。' if hard else '同时，多项指标的组合也与近期模式不同。'}"
                ),
            }

        anomalies.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "is_isoforest": idx in iso_outliers,
                "n_metric_flags": len(metric_flags),
                "driver": driver,
                "flags": [
                    {
                        "metric": m,
                        "label": METRICS[m]["label"],
                        "value": round(float(v), 2),
                        "z": round(float(z), 2),
                    }
                    for m, v, _, _, z in sorted(
                        metric_flags, key=lambda t: abs(t[4]), reverse=True
                    )[:3]
                ],
            }
        )

    return anomalies


def anomaly_summary(anomalies: list[dict]) -> dict:
    """Roll up anomaly results for the dashboard."""
    return {
        "count": len(anomalies),
        "recent": anomalies[:3],
        "all": anomalies,
    }
