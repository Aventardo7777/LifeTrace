"""Database seeding (demo data) and auto-seed on first run."""

from __future__ import annotations

from sqlalchemy.orm import Session

from . import crud
from .config import AUTO_SEED_DEMO, DEMO_DAYS
from .demo import generate_demo_data
from .schemas import RecordCreate


def seed_demo_data(db: Session, days: int = DEMO_DAYS) -> int:
    """Insert demo records, skipping dates that already exist."""
    records = generate_demo_data(days=days)
    created = 0
    for rec in records:
        if crud.get_by_date(db, rec["date"]) is None:
            crud.create_record(db, RecordCreate(**rec))
            created += 1
    return created


def ensure_seed(db: Session) -> bool:
    """Auto-seed demo data if enabled and the database is empty."""
    if not AUTO_SEED_DEMO:
        return False
    if crud.count_records(db) > 0:
        return False
    return seed_demo_data(db) > 0
