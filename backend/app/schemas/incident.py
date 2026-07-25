from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IncidentStatus
from app.schemas.check_result import CheckResultRead


class IncidentRead(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  monitor_id: int
  monitor_name: str
  monitor_target: str
  status: IncidentStatus
  started_at: datetime
  ended_at: datetime | None
  error_message: str | None
  failed_check_count: int = Field(ge=1)


class IncidentDetail(IncidentRead):
  checks: list[CheckResultRead] = Field(default_factory=list)
