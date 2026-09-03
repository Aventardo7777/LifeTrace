"""Life-pattern clustering (K-Means) with data-driven labeling.

Cluster labels are NOT hardcoded to specific cluster indices. Instead, the
label is derived from each cluster's measured feature profile: we standardize
features, compute each cluster's mean per feature, and compose a name from the
traits that actually stand out in the data (e.g. high study -> "高效专注",
low mood + low activity -> "低能量"). See docs/statistics.md for details.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .utils import CLUSTER_FEATURES, METRICS

MIN_RECORDS_CLUSTER = 10
MAX_K = 6
MIN_K = 2

# Labels used to compose a cluster name from its dominant dimension.
# (feature, label when high, label when low). Names are applied *after*
# measuring each cluster's standardized feature means — never hardcoded to a
# cluster index.
DOMINANT_LABELS = {
    "study_hours": ("高效专注日", "低投入日"),
    "social_count": ("社交活跃日", "独处日"),
    "exercise_hours": ("运动活力日", "低运动日"),
    "entertainment_hours": ("放松娱乐日", "克制自律日"),
    "sleep_hours": ("充足睡眠日", "睡眠不足日"),
    "mood": ("愉悦日", "低能量日"),
}


def _best_k(X_scaled: np.ndarray, n_samples: int) -> int:
    """Pick the number of clusters with the best silhouette score."""
    upper = min(MAX_K, max(MIN_K, n_samples - 1))
    best_k, best_score = MIN_K, -1.0
    for k in range(MIN_K, upper + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X_scaled, labels)
        if score > best_score:
            best_k, best_score = k, score
    return best_k


def _name_cluster(means: dict[str, float], scaler: StandardScaler, df: pd.DataFrame) -> str:
    """Compose a cluster name from its measured feature profile."""
    features = [f for f in CLUSTER_FEATURES if f in df.columns]
    z = {}
    for i, f in enumerate(features):
        scale = scaler.scale_[i]
        z[f] = 0.0 if scale == 0 else (means[f] - scaler.mean_[i]) / scale

    # Composite rule 1: low mood + low productive activity -> "低能量日".
    if z.get("mood", 0.0) < -0.4 and z.get("study_hours", 0.0) < 0.2 and z.get("exercise_hours", 0.0) < 0.2:
        return "低能量日"
    # Composite rule 2: long sleep + not much study -> "恢复日".
    if z.get("sleep_hours", 0.0) > 0.5 and z.get("study_hours", 0.0) < 0.0:
        return "恢复日"

    # Otherwise, name after the single most dominant dimension.
    dominant = max(features, key=lambda f: abs(z[f]))
    high, low = DOMINANT_LABELS[dominant]
    return high if z[dominant] > 0 else low


def cluster_days(df: pd.DataFrame) -> dict:
    """Cluster days into life patterns and return labels + per-cluster stats."""
    features = [f for f in CLUSTER_FEATURES if f in df.columns]
    if df.empty or len(df) < MIN_RECORDS_CLUSTER or len(features) < 2:
        return {"clusters": [], "k": 0, "silhouette": None, "message": "数据不足，无法聚类"}

    X = df[features].values.astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k = _best_k(X_scaled, len(df))
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    silhouette = float(silhouette_score(X_scaled, labels)) if k > 1 else None

    # Build per-cluster summaries and assign data-driven names.
    df_labelled = df.copy()
    df_labelled["cluster"] = labels

    cluster_ids = sorted({int(x) for x in labels})
    id_to_index = {cid: i for i, cid in enumerate(cluster_ids)}

    clusters = []
    for cid in cluster_ids:
        sub = df_labelled[df_labelled["cluster"] == cid]
        means = {f: float(sub[f].mean()) for f in features}
        # Recompute z relative to the whole sample for labeling.
        name = _name_cluster(means, scaler, df)
        clusters.append(
            {
                "id": int(cid),
                "name": name,
                "size": int(len(sub)),
                "pct": round(len(sub) / len(df) * 100, 1),
                "means": {f: round(means[f], 2) for f in features},
                "feature_labels": {f: METRICS[f]["label"] for f in features},
                "dates": [d.strftime("%Y-%m-%d") for d in sub["date"]],
            }
        )

    # Sort clusters by size for stable display.
    clusters.sort(key=lambda c: c["size"], reverse=True)

    return {
        "clusters": clusters,
        "k": k,
        "silhouette": round(silhouette, 3) if silhouette is not None else None,
        "labels": [int(x) for x in labels],
        "dates": [d.strftime("%Y-%m-%d") for d in df["date"]],
        "label_names": {int(cid): clusters[id_to_index[cid]]["name"] for cid in cluster_ids},
        "features": features,
    }
