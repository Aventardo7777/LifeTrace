"""CRUD helpers for DailyRecord."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DailyRecord
from .schemas import RecordCreate, RecordUpdate


def get_by_id(db: Session, record_id: int) -> Optional[DailyRecord]:
    return db.get(DailyRecord, record_id)


def get_by_date(db: Session, day: date) -> Optional[DailyRecord]:
    return db.scalar(select(DailyRecord).where(DailyRecord.date == day))


def list_records(
    db: Session,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    order: str = "desc",
) -> Sequence[DailyRecord]:
    stmt = select(DailyRecord)
    if start is not None:
        stmt = stmt.where(DailyRecord.date >= start)
    if end is not None:
        stmt = stmt.where(DailyRecord.date <= end)
    stmt = stmt.order_by(
        DailyRecord.date.desc() if order == "desc" else DailyRecord.date.asc()
    )
    return db.scalars(stmt).all()


def count_records(db: Session) -> int:
    from sqlalchemy import func

    return db.scalar(select(func.count(DailyRecord.id))) or 0


def create_record(db: Session, data: RecordCreate) -> DailyRecord:
    record = DailyRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_record(db: Session, record: DailyRecord, data: RecordUpdate) -> DailyRecord:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def upsert_record(db: Session, data: RecordCreate) -> tuple[DailyRecord, bool]:
    """Create or update the record for ``data.date``. Returns (record, created)."""
    existing = get_by_date(db, data.date)
    if existing is None:
        return create_record(db, data), True
    updated = update_record(db, existing, RecordUpdate(**data.model_dump()))
    return updated, False


def delete_record(db: Session, record_id: int) -> bool:
    record = get_by_id(db, record_id)
    if record is None:
        return False
    db.delete(record)
    db.commit()
    return True


def compute_streak(db: Session) -> int:
    """Number of consecutive days (ending today/yesterday) with a record."""
    records = list_records(db, order="asc")
    if not records:
        return 0
    dates = {r.date for r in records}
    # The streak may end today or yesterday (if today not yet logged).
    anchor = date.today()
    if anchor not in dates:
        anchor -= timedelta(days=1)
    streak = 0
    while anchor in dates:
        streak += 1
        anchor -= timedelta(days=1)
    return streak
