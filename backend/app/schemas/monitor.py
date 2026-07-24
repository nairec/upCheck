from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import MonitorStatus, MonitorType
from app.schemas.check_result import CheckResultBrief


class MonitorBase(BaseModel):
  name: str = Field(min_length=1, max_length=120)
  type: MonitorType
  target: str = Field(min_length=1, max_length=500)
  interval_seconds: int = Field(default=60, ge=30, le=3600)
  timeout_seconds: int = Field(default=10, ge=1, le=300)
  enabled: bool = True


class MonitorCreate(MonitorBase):
  pass


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
