from datetime import datetime

from pydantic import BaseModel, Field

from app.history import ResolvedHistoryGranularity
from app.models.enums import MonitorStatus


class HistoryPoint(BaseModel):
  at: datetime
  total_checks: int = 1
  up_checks: int
  uptime_percent: float
  avg_latency_ms: float | None = None
  min_latency_ms: float | None = None
  max_latency_ms: float | None = None
  downtime_minutes: int | None = None
  status: MonitorStatus | None = None
  status_code: int | None = None
  error_message: str | None = None
  id: int | None = None


class MonitorHistoryResponse(BaseModel):
  granularity: ResolvedHistoryGranularity
  days: int
  points: list[HistoryPoint]
  total: int = Field(description="Total matching buckets/checks in the requested window")
