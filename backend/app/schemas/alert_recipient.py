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
  down_alert_cooldown_minutes: int = Field(description="Fixed for now; will be configurable in settings UI")
  recipient_count: int
