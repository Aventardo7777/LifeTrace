"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class DailyRecord(Base):
    """A single day of personal life data."""

    __tablename__ = "daily_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)

    # Time (hours, float) — supports partial hours.
    sleep_hours: Mapped[float] = mapped_column(Float, default=0.0)
    study_hours: Mapped[float] = mapped_column(Float, default=0.0)
    exercise_hours: Mapped[float] = mapped_column(Float, default=0.0)
    entertainment_hours: Mapped[float] = mapped_column(Float, default=0.0)

    social_count: Mapped[int] = mapped_column(Integer, default=0)
    spending: Mapped[float] = mapped_column(Float, default=0.0)

    # Subjective scores (1-10).
    mood: Mapped[int] = mapped_column(Integer, default=5)
    stress: Mapped[int] = mapped_column(Integer, default=5)

    stay_up_late: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    note: Mapped[str] = mapped_column(Text, default="")
    weather: Mapped[str] = mapped_column(String(64), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DailyRecord {self.date} mood={self.mood}>"
