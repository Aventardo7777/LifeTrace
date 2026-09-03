"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import date as DateType
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecordBase(BaseModel):
    date: DateType
    sleep_hours: float = Field(default=0.0, ge=0, le=24)
    study_hours: float = Field(default=0.0, ge=0, le=24)
    exercise_hours: float = Field(default=0.0, ge=0, le=24)
    entertainment_hours: float = Field(default=0.0, ge=0, le=24)
    social_count: int = Field(default=0, ge=0)
    spending: float = Field(default=0.0, ge=0)
    mood: int = Field(default=5, ge=1, le=10)
    stress: int = Field(default=5, ge=1, le=10)
    stay_up_late: bool = False
    plan_completed: bool = False
    note: str = ""
    weather: str = ""


class RecordCreate(RecordBase):
    pass


class RecordUpdate(BaseModel):
    """Partial update — only provided fields are changed."""

    date: Optional[DateType] = None
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    study_hours: Optional[float] = Field(default=None, ge=0, le=24)
    exercise_hours: Optional[float] = Field(default=None, ge=0, le=24)
    entertainment_hours: Optional[float] = Field(default=None, ge=0, le=24)
    social_count: Optional[int] = Field(default=None, ge=0)
    spending: Optional[float] = Field(default=None, ge=0)
    mood: Optional[int] = Field(default=None, ge=1, le=10)
    stress: Optional[int] = Field(default=None, ge=1, le=10)
    stay_up_late: Optional[bool] = None
    plan_completed: Optional[bool] = None
    note: Optional[str] = None
    weather: Optional[str] = None


class RecordOut(RecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class RecordListOut(BaseModel):
    total: int
    items: list[RecordOut]
