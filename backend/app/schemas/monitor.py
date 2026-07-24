from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import MonitorStatus, MonitorType
from app.schemas.check_result import CheckResultBrief
from app.schemas.monitor_validation import ensure_supported_type, validate_monitor_target


class MonitorBase(BaseModel):
  name: str = Field(min_length=1, max_length=120)
  type: MonitorType
  target: str = Field(min_length=1, max_length=500)
  interval_seconds: int = Field(default=60, ge=30, le=3600)
  timeout_seconds: int = Field(default=10, ge=1, le=300)
  enabled: bool = True

  @field_validator("type")
  @classmethod
  def supported_type(cls, value: MonitorType) -> MonitorType:
    return ensure_supported_type(value)

  @field_validator("name", "target")
  @classmethod
  def strip_whitespace(cls, value: str) -> str:
    return value.strip()

  @model_validator(mode="after")
  def validate_target_for_type(self) -> "MonitorBase":
    self.target = validate_monitor_target(self.type, self.target)
    return self


class MonitorCreate(MonitorBase):
  pass


class MonitorUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=120)
  type: MonitorType | None = None
  target: str | None = Field(default=None, min_length=1, max_length=500)
  interval_seconds: int | None = Field(default=None, ge=30, le=3600)
  timeout_seconds: int | None = Field(default=None, ge=1, le=300)
  enabled: bool | None = None

  @field_validator("type")
  @classmethod
  def supported_type(cls, value: MonitorType | None) -> MonitorType | None:
    if value is None:
      return None
    return ensure_supported_type(value)

  @field_validator("name", "target")
  @classmethod
  def strip_whitespace(cls, value: str | None) -> str | None:
    if value is None:
      return None
    return value.strip()


class MonitorRead(MonitorBase):
  id: int
  status: MonitorStatus = MonitorStatus.UNKNOWN
  last_checked_at: datetime | None = None
  response_time_ms: float | None = None

  model_config = {"from_attributes": True}


class MonitorListItem(MonitorRead):
  recent_checks: list[CheckResultBrief] = Field(default_factory=list)


class MonitorSummary(BaseModel):
  total: int
  up: int
  down: int
  degraded: int
  unknown: int


class DashboardStats(BaseModel):
  monitors: MonitorSummary
  uptime_24h_percent: float | None = None
