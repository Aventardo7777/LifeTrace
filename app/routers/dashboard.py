"""Dashboard page and stats API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..templating import templates

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    payload = services.dashboard_payload(db)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"active": "dashboard", **payload},
    )


@router.get("/api/dashboard")
def dashboard_api(db: Session = Depends(get_db)):
    return services.dashboard_payload(db)
