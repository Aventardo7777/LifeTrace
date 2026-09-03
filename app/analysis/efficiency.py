"""Personal efficiency model.

A transparent linear-regression model that predicts the day's "状态评分"
(state score), defined here as the self-reported mood (1-10), from behavioral
inputs: sleep, study, exercise, social, entertainment, stress, and whether the
user stayed up late.

IMPORTANT: This is a *statistical* model. It is NOT a psychological or medical
diagnosis. Results reflect association in the user's own historical data only.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .utils import METRICS, clamp

MIN_RECORDS_MODEL = 12

FEATURES = [
    "sleep_hours",
    "study_hours",
    "exercise_hours",
    "social_count",
    "entertainment_hours",
    "stress",
    "stay_up_late",
]

TARGET = "mood"


def _train(df: pd.DataFrame, features: list[str]):
    X = df[features].values.astype(float)
    y = df[TARGET].values.astype(float)
    model = LinearRegression()
    model.fit(X, y)
    return model, X, y


def train_efficiency_model(df: pd.DataFrame, test_size: float = 0.2) -> dict:
    """Train the state-score model and report train/test performance."""
    features = [f for f in FEATURES if f in df.columns]
    if df.empty or TARGET not in df.columns or len(df) < MIN_RECORDS_MODEL:
        return {"trained": False, "message": "数据不足，无法训练模型"}

    X = df[features].values.astype(float)
    y = df[TARGET].values.astype(float)

    if len(df) >= MIN_RECORDS_MODEL + 5:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Standardized coefficients for fair feature-importance ranking.
    x_std = X.std(axis=0)
    x_std[x_std == 0] = 1.0
    coefs_std = model.coef_ * x_std

    ranked = sorted(
        zip(features, model.coef_.tolist(), coefs_std.tolist()),
        key=lambda t: abs(t[2]),
        reverse=True,
    )

    return {
        "trained": True,
        "n_samples": int(len(df)),
        "features": features,
        "feature_labels": [METRICS.get(f, {}).get("label", f) for f in features],
        "intercept": float(model.intercept_),
        "coefficients": {
            f: {"raw": round(float(c), 4), "standardized": round(float(cs), 4)}
            for f, c, cs in ranked
        },
        "ranked": [
            {
                "feature": f,
                "label": METRICS.get(f, {}).get("label", f),
                "coefficient": round(float(c), 4),
                "standardized": round(float(cs), 4),
                "direction": "正向" if c > 0 else "负向",
            }
            for f, c, cs in ranked
        ],
        "r2_train": round(float(r2_score(y_train, y_pred_train)), 3),
        "r2_test": round(float(r2_score(y_test, y_pred_test)), 3),
        "mae": round(float(mean_absolute_error(y_test, y_pred_test)), 2),
    }


def predict_state_score(df: pd.DataFrame, inputs: dict) -> Optional[dict]:
    """Train on the full history and predict a state score for ``inputs``."""
    features = [f for f in FEATURES if f in df.columns]
    if df.empty or TARGET not in df.columns or len(df) < MIN_RECORDS_MODEL:
        return None

    model, X, y = _train(df, features)
    x_std = X.std(axis=0)
    x_std[x_std == 0] = 1.0
    coefs_std = model.coef_ * x_std

    vec = []
    contributions = []
    for i, f in enumerate(features):
        value = float(inputs.get(f, 0.0))
        vec.append(value)
        # Contribution relative to the feature mean (interpretable).
        mean = float(X[:, i].mean())
        contrib = model.coef_[i] * (value - mean)
        contributions.append(
            {
                "feature": f,
                "label": METRICS.get(f, {}).get("label", f),
                "value": value,
                "mean": round(mean, 2),
                "contribution": round(float(contrib), 2),
            }
        )

    pred = float(model.predict([vec])[0])
    pred_clamped = clamp(round(pred, 1), 1, 10)

    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)

    return {
        "predicted": round(pred, 2),
        "predicted_clamped": pred_clamped,
        "baseline_mean": round(float(y.mean()), 2),
        "contributions": contributions,
        "note": "这是基于历史数据的统计估计，不代表因果关系或诊断。",
    }
