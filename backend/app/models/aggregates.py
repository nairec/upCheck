from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CheckResultHourly(Base):
  __tablename__ = "check_result_hourly"
  __table_args__ = (UniqueConstraint("monitor_id", "hour", name="uq_hourly_monitor_hour"),)

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  monitor_id: Mapped[int] = mapped_column(
    ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False, index=True
  )
  hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
  total_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  up_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
  min_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
  max_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class CheckResultDaily(Base):
  __tablename__ = "check_result_daily"
  __table_args__ = (UniqueConstraint("monitor_id", "day", name="uq_daily_monitor_day"),)

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  monitor_id: Mapped[int] = mapped_column(
    ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False, index=True
  )
  day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
  total_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  up_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
  downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
