from dataclasses import dataclass

from app.models.enums import MonitorStatus


@dataclass(frozen=True, slots=True)
class CheckOutcome:
  status: MonitorStatus
  response_time_ms: float | None = None
  status_code: int | None = None
  error_message: str | None = None
