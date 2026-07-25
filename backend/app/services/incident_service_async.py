from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import CheckResult, Incident, Monitor
from app.models.enums import IncidentStatus
from app.schemas.check_result import CheckResultRead
from app.schemas.incident import IncidentDetail, IncidentRead


def _ensure_utc(value: datetime) -> datetime:
  if value.tzinfo is None:
    return value.replace(tzinfo=UTC)
  return value.astimezone(UTC)


async def list_incidents(
  session: AsyncSession,
  *,
  status: IncidentStatus | None = None,
  monitor_id: int | None = None,
  days: int = 30,
) -> list[IncidentRead]:
  since = datetime.now(UTC) - timedelta(days=days)
  query = (
    select(Incident)
    .options(joinedload(Incident.monitor))
    .where(Incident.started_at >= since)
    .order_by(Incident.started_at.desc())
  )
  if status is not None:
    query = query.where(Incident.status == status)
  if monitor_id is not None:
    query = query.where(Incident.monitor_id == monitor_id)

  incidents = (await session.scalars(query)).unique().all()
  return [_to_read(incident) for incident in incidents]


async def get_incident(session: AsyncSession, incident_id: int) -> IncidentDetail | None:
  incident = await session.scalar(
    select(Incident)
    .options(joinedload(Incident.monitor))
    .where(Incident.id == incident_id)
  )
  if incident is None:
    return None

  end_at = incident.ended_at or datetime.now(UTC)
  checks = (
    await session.scalars(
      select(CheckResult)
      .where(
        CheckResult.monitor_id == incident.monitor_id,
        CheckResult.checked_at >= incident.started_at,
        CheckResult.checked_at <= end_at,
      )
      .order_by(CheckResult.checked_at.desc())
      .limit(100)
    )
  ).all()

  detail = IncidentDetail.model_validate(_to_read(incident))
  detail.checks = [CheckResultRead.model_validate(check) for check in checks]
  return detail


def _to_read(incident: Incident) -> IncidentRead:
  monitor = incident.monitor
  return IncidentRead(
    id=incident.id,
    monitor_id=incident.monitor_id,
    monitor_name=monitor.name if monitor else "",
    monitor_target=monitor.target if monitor else "",
    status=incident.status,
    started_at=incident.started_at,
    ended_at=incident.ended_at,
    error_message=incident.error_message,
    failed_check_count=incident.failed_check_count,
  )
