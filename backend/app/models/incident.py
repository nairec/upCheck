from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IncidentStatus


class Incident(Base):
  __tablename__ = "incidents"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  monitor_id: Mapped[int] = mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"), index=True)
  status: Mapped[IncidentStatus] = mapped_column(
    Enum(IncidentStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
    nullable=False,
  )
  started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
  failed_check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

  monitor = relationship("Monitor", back_populates="incidents")
