from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MonitorStatus

if TYPE_CHECKING:
  from app.models.monitor import Monitor


class CheckResult(Base):
  __tablename__ = "check_results"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  monitor_id: Mapped[int] = mapped_column(
    ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False, index=True
  )
  status: Mapped[MonitorStatus] = mapped_column(
    Enum(MonitorStatus, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
    nullable=False,
  )
  response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
  status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
  error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
  checked_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
  )

  monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="check_results")
