from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MonitorStatus, MonitorType

if TYPE_CHECKING:
  from app.models.check_result import CheckResult


class Monitor(Base):
  __tablename__ = "monitors"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(120), nullable=False)
  type: Mapped[MonitorType] = mapped_column(
    Enum(MonitorType, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
    nullable=False,
  )
  target: Mapped[str] = mapped_column(String(500), nullable=False)
  interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
  timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
  enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  status: Mapped[MonitorStatus] = mapped_column(
    Enum(MonitorStatus, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
    nullable=False,
    default=MonitorStatus.UNKNOWN,
  )
  last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
  )

  check_results: Mapped[list["CheckResult"]] = relationship(
    "CheckResult", back_populates="monitor", cascade="all, delete-orphan"
  )
