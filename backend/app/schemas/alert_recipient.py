from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AlertRecipientCreate(BaseModel):
  email: EmailStr
  enabled: bool = True


class AlertRecipientRead(BaseModel):
  id: int
  email: EmailStr
  enabled: bool
  created_at: datetime

  model_config = {"from_attributes": True}


class AlertRecipientUpdate(BaseModel):
  enabled: bool


class AlertSettingsRead(BaseModel):
  alerts_enabled: bool
  smtp_configured: bool
  down_alert_cooldown_minutes: int
  alert_on_down: bool
  alert_on_recovery: bool
  recipient_count: int


class AlertSettingsUpdate(BaseModel):
  down_alert_cooldown_minutes: int | None = Field(default=None, ge=1, le=1440)
  alert_on_down: bool | None = None
  alert_on_recovery: bool | None = None
