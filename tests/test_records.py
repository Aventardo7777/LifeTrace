"""Data entry tests: record CRUD behavior."""

from __future__ import annotations

from datetime import date

import pytest

from app import crud
from app.schemas import RecordCreate, RecordUpdate


def _sample(day: date = date(2026, 2, 1)) -> RecordCreate:
    return RecordCreate(date=day, sleep_hours=6.0, study_hours=5.0, mood=6, stress=6)


def test_create_record(db):
    rec = crud.create_record(db, _sample())
    assert rec.date == date(2026, 2, 1)
    assert rec.mood == 6


def test_partial_update(db):
    rec = crud.create_record(db, _sample())
    updated = crud.update_record(db, rec, RecordUpdate(mood=8, note="今天状态不错"))
    assert updated.mood == 8
    assert updated.note == "今天状态不错"
    assert updated.sleep_hours == 6.0  # unchanged


def test_delete_record(db):
    rec = crud.create_record(db, _sample())
    assert crud.delete_record(db, rec.id) is True
    assert crud.get_by_id(db, rec.id) is None
    assert crud.delete_record(db, rec.id) is False


def test_schema_validation_bounds():
    with pytest.raises(Exception):
        RecordCreate(date=date(2026, 2, 1), mood=99)  # out of 1-10 range
