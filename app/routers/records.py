"""Record CRUD API + record entry/list pages."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..schemas import RecordCreate, RecordListOut, RecordOut, RecordUpdate
from ..templating import templates

router = APIRouter(tags=["records"])


# --- REST API ----------------------------------------------------------------
@router.get("/api/records", response_model=RecordListOut)
def list_records(
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    items = crud.list_records(db, start=start, end=end)
    return RecordListOut(total=len(items), items=[RecordOut.model_validate(r) for r in items])


@router.post("/api/records", response_model=RecordOut)
def upsert_record(data: RecordCreate, db: Session = Depends(get_db)):
    record, _ = crud.upsert_record(db, data)
    return record


@router.get("/api/records/date/{day}", response_model=RecordOut)
def get_record_by_date(day: date, db: Session = Depends(get_db)):
    record = crud.get_by_date(db, day)
    if record is None:
        raise HTTPException(status_code=404, detail="该日期没有记录")
    return record


@router.get("/api/records/{record_id}", response_model=RecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = crud.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.patch("/api/records/{record_id}", response_model=RecordOut)
def patch_record(record_id: int, data: RecordUpdate, db: Session = Depends(get_db)):
    record = crud.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return crud.update_record(db, record, data)


@router.delete("/api/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    if not crud.delete_record(db, record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"ok": True}


# --- Pages -------------------------------------------------------------------
@router.get("/record", response_class=HTMLResponse)
def record_page(request: Request, day: Optional[date] = None, db: Session = Depends(get_db)):
    target = day or date.today()
    record = crud.get_by_date(db, target)
    return templates.TemplateResponse(
        request,
        "record.html",
        {
            "active": "record",
            "target_date": target,
            "record": record,
        },
    )


@router.get("/records", response_class=HTMLResponse)
def records_page(request: Request, db: Session = Depends(get_db)):
    items = crud.list_records(db, order="desc")
    return templates.TemplateResponse(
        request,
        "records.html",
        {
            "active": "records",
            "records": items,
        },
    )
