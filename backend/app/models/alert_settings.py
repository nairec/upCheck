from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.alerts import DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES
from app.core.database import Base

ACCOUNT_SETTINGS_ID = 1


class AlertSettings(Base):
  """Singleton account alert preferences. account_id FK will be added for multi-tenant."""

  __tablename__ = "alert_settings"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  down_alert_cooldown_minutes: Mapped[int] = mapped_column(
    Integer, nullable=False, default=DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES
  )
  alert_on_down: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  alert_on_recovery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
  status_page_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
  )
