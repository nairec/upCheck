from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import MonitorStatus

MAX_ERROR_MESSAGE_LENGTH = 500


class CheckResultRead(BaseModel):
  id: int
  monitor_id: int
  status: MonitorStatus
  response_time_ms: float | None = None
  status_code: int | None = None
  error_message: str | None = None
  checked_at: datetime

  model_config = {"from_attributes": True}

  @field_validator("error_message")
  @classmethod
  def truncate_error_message(cls, value: str | None) -> str | None:
    if value is None:
      return None
    if len(value) <= MAX_ERROR_MESSAGE_LENGTH:
      return value
    return value[: MAX_ERROR_MESSAGE_LENGTH - 1] + "…"


class CheckResultBrief(BaseModel):
  status: MonitorStatus
  response_time_ms: float | None = None
  checked_at: datetime

  model_config = {"from_attributes": True}


class CheckResultPage(BaseModel):
  items: list[CheckResultRead]
  total: int
  limit: int
  offset: int
  has_more: bool
