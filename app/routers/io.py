"""Data import / export / backup."""

from __future__ import annotations

import io as _io
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from .. import crud
from ..config import DEFAULT_DB_PATH
from ..database import get_db
from ..models import DailyRecord
from ..schemas import RecordCreate
from ..templating import templates

router = APIRouter(tags=["data"])

# Accept both English field names and common Chinese aliases on import.
COLUMN_ALIASES = {
    "date": ["date", "日期", "时间"],
    "sleep_hours": ["sleep_hours", "睡眠", "睡眠时长", "睡眠时间"],
    "study_hours": ["study_hours", "学习", "学习时长", "学习时间"],
    "exercise_hours": ["exercise_hours", "运动", "运动时长", "运动时间"],
    "entertainment_hours": ["entertainment_hours", "娱乐", "娱乐时长", "娱乐时间"],
    "social_count": ["social_count", "社交", "社交次数"],
    "spending": ["spending", "消费", "消费金额"],
    "mood": ["mood", "心情", "心情评分"],
    "stress": ["stress", "压力", "压力评分"],
    "stay_up_late": ["stay_up_late", "熬夜", "是否熬夜"],
    "plan_completed": ["plan_completed", "完成计划", "是否完成计划"],
    "note": ["note", "备注"],
    "weather": ["weather", "天气"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns using COLUMN_ALIASES (case-insensitive)."""
    rename = {}
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = alias.lower()
            if key in lowered:
                rename[lowered[key]] = field
                break
    return df.rename(columns=rename)


# --- Pages -------------------------------------------------------------------
@router.get("/data", response_class=HTMLResponse)
def data_page(request: Request, db: Session = Depends(get_db)):
    total = crud.count_records(db)
    return templates.TemplateResponse(
        request,
        "data.html",
        {"active": "data", "total": total},
    )


# --- Export ------------------------------------------------------------------
@router.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    records = crud.list_records(db, order="asc")
    rows = [
        {
            "date": r.date.isoformat(),
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
            "note": r.note,
            "weather": r.weather,
        }
        for r in records
    ]
    df = pd.DataFrame(rows)
    buf = _io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    filename = f"lifetrace_export_{datetime.now():%Y%m%d}.csv"
    return Response(
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/export/json")
def export_json(db: Session = Depends(get_db)):
    records = crud.list_records(db, order="asc")
    data = {
        "exported_at": datetime.now().isoformat(),
        "count": len(records),
        "records": [
            {
                "date": r.date.isoformat(),
                "sleep_hours": r.sleep_hours,
                "study_hours": r.study_hours,
                "exercise_hours": r.exercise_hours,
                "entertainment_hours": r.entertainment_hours,
                "social_count": r.social_count,
                "spending": r.spending,
                "mood": r.mood,
                "stress": r.stress,
                "stay_up_late": r.stay_up_late,
                "plan_completed": r.plan_completed,
                "note": r.note,
                "weather": r.weather,
            }
            for r in records
        ],
    }
    filename = f"lifetrace_export_{datetime.now():%Y%m%d}.json"
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Import ------------------------------------------------------------------
@router.post("/api/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    try:
        df = pd.read_csv(_io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"无法解析 CSV 文件: {exc}"}

    df = _normalize_columns(df)
    if "date" not in df.columns:
        return {"ok": False, "error": "CSV 缺少日期列（date / 日期）"}

    created, updated, skipped = 0, 0, 0
    errors = []
    for _, row in df.iterrows():
        try:
            data = {
                "date": pd.to_datetime(row["date"]).date(),
                "sleep_hours": float(row.get("sleep_hours", 0) or 0),
                "study_hours": float(row.get("study_hours", 0) or 0),
                "exercise_hours": float(row.get("exercise_hours", 0) or 0),
                "entertainment_hours": float(row.get("entertainment_hours", 0) or 0),
                "social_count": int(float(row.get("social_count", 0) or 0)),
                "spending": float(row.get("spending", 0) or 0),
                "mood": int(float(row.get("mood", 5) or 5)),
                "stress": int(float(row.get("stress", 5) or 5)),
                "stay_up_late": _to_bool(row.get("stay_up_late")),
                "plan_completed": _to_bool(row.get("plan_completed")),
                "note": "" if pd.isna(row.get("note")) else str(row.get("note", "")),
                "weather": "" if pd.isna(row.get("weather")) else str(row.get("weather", "")),
            }
            record, is_new = crud.upsert_record(db, RecordCreate(**data))
            if is_new:
                created += 1
            else:
                updated += 1
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            errors.append(str(exc))

    return {
        "ok": True,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors[:5],
    }


def _to_bool(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    s = str(value).strip().lower()
    return s in {"1", "true", "yes", "y", "是", "真"}


# --- Backup ------------------------------------------------------------------
@router.get("/api/backup")
def backup():
    src = Path(DEFAULT_DB_PATH)
    if not src.exists():
        return Response(content="数据库文件不存在", status_code=404)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lifetrace_backup_{stamp}.db"
    buf = _io.BytesIO()
    with open(src, "rb") as f:
        shutil.copyfileobj(f, buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
