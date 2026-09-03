"""Analysis endpoints: correlation, time series, anomaly, clustering,
efficiency model, and the counterfactual "what-if" simulation."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import services
from ..analysis.whatif import MODIFIABLE
from ..database import get_db
from ..templating import templates

router = APIRouter(tags=["analysis"])


@router.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request, db: Session = Depends(get_db)):
    payload = services.analysis_payload(db)
    return templates.TemplateResponse(
        request,
        "analysis.html",
        {"active": "analysis", **payload},
    )


@router.get("/api/analysis")
def analysis_api(db: Session = Depends(get_db)):
    return services.analysis_payload(db)


@router.get("/api/analysis/timeseries")
def timeseries(metric: str = "sleep_hours", granularity: str = "day", db: Session = Depends(get_db)):
    return services.timeseries_payload(db, metric, granularity)


@router.get("/api/analysis/scatter")
def scatter(x: str = "sleep_hours", y: str = "mood", db: Session = Depends(get_db)):
    return services.scatter_payload(db, x, y)


@router.get("/api/analysis/whatif")
def whatif(
    feature: str,
    current: float,
    target: float,
    db: Session = Depends(get_db),
):
    if feature not in MODIFIABLE:
        raise HTTPException(status_code=400, detail=f"不支持的变量: {feature}")
    return services.whatif_payload(db, feature, current, target)


@router.get("/api/analysis/efficiency/predict")
def efficiency_predict(
    sleep_hours: float = 7.0,
    study_hours: float = 5.0,
    exercise_hours: float = 0.5,
    social_count: int = 1,
    entertainment_hours: float = 2.0,
    stress: int = 5,
    stay_up_late: int = 0,
    db: Session = Depends(get_db),
):
    inputs = {
        "sleep_hours": sleep_hours,
        "study_hours": study_hours,
        "exercise_hours": exercise_hours,
        "social_count": social_count,
        "entertainment_hours": entertainment_hours,
        "stress": stress,
        "stay_up_late": stay_up_late,
    }
    result = services.efficiency_predict_payload(db, inputs)
    if result is None:
        raise HTTPException(status_code=400, detail="数据不足，无法预测")
    return result
