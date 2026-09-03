"""Database tests: table creation + basic CRUD via the ORM layer."""

from __future__ import annotations

from datetime import date

from sqlalchemy import inspect

from app import crud
from app.database import engine
from app.schemas import RecordCreate


def _sample(day: date = date(2026, 1, 1)) -> RecordCreate:
    return RecordCreate(
        date=day,
        sleep_hours=7.5,
        study_hours=6.0,
        exercise_hours=0.5,
        entertainment_hours=2.0,
        social_count=2,
        spending=80.0,
        mood=7,
        stress=5,
        stay_up_late=False,
        plan_completed=True,
        weather="晴",
    )


def test_tables_created():
    tables = inspect(engine).get_table_names()
    assert "daily_records" in tables


def test_create_and_get(db):
    rec = crud.create_record(db, _sample())
    assert rec.id is not None
    got = crud.get_by_date(db, date(2026, 1, 1))
    assert got is not None
    assert got.mood == 7
    assert got.sleep_hours == 7.5


def test_date_unique_upsert(db):
    _, created = crud.upsert_record(db, _sample())
    assert created is True
    # Same date, different data -> updates instead of inserting a duplicate.
    second = _sample()
    second.mood = 9
    _, created_again = crud.upsert_record(db, second)
    assert created_again is False
    assert crud.count_records(db) == 1
    assert crud.get_by_date(db, date(2026, 1, 1)).mood == 9
