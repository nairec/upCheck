from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import IncidentStatus, MonitorStatus, MonitorType
from app.schemas.monitor import MonitorSummary

OverallStatus = Literal["operational", "degraded", "major_outage"]


class StatusMonitorItem(BaseModel):
  id: int
  name: str
  type: MonitorType
  status: MonitorStatus
  uptime_24h_percent: float | None = None
  response_time_ms: float | None = None
  last_checked_at: datetime | None = None


class PublicStatusIncident(BaseModel):
  id: int
  monitor_name: str
  status: IncidentStatus
  started_at: datetime
  error_message: str | None = None
  failed_check_count: int = Field(ge=1)


class PublicStatusResponse(BaseModel):
  status: OverallStatus
  uptime_24h_percent: float | None = None
  monitors: MonitorSummary
  services: list[StatusMonitorItem]
  open_incidents: list[PublicStatusIncident] = Field(default_factory=list)
  updated_at: datetime
