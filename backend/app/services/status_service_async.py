from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CheckResult, Monitor
from app.models.enums import IncidentStatus, MonitorStatus
from app.schemas.monitor import MonitorSummary
from app.schemas.status import (
  OverallStatus,
  PublicStatusIncident,
  PublicStatusResponse,
  StatusMonitorItem,
)
from app.services import incident_service_async as incident_service


def _derive_overall_status(summary: MonitorSummary) -> OverallStatus:
  if summary.down > 0:
    return "major_outage"
  if summary.degraded > 0:
    return "degraded"
  return "operational"


async def _uptime_by_monitor(session: AsyncSession, since: datetime) -> dict[int, float]:
  up_case = case((CheckResult.status == MonitorStatus.UP, 1), else_=0)
  rows = await session.execute(
    select(
      CheckResult.monitor_id,
      func.count().label("total"),
      func.sum(up_case).label("up"),
    )
    .where(CheckResult.checked_at >= since)
    .group_by(CheckResult.monitor_id)
  )
  uptime: dict[int, float] = {}
  for monitor_id, total, up in rows:
    if total and total > 0:
      uptime[monitor_id] = round((up or 0) / total * 100, 1)
  return uptime


async def get_public_status(session: AsyncSession) -> PublicStatusResponse:
  monitors = (
    await session.scalars(
      select(Monitor).where(Monitor.enabled.is_(True)).order_by(Monitor.id)
    )
  ).all()

  summary = MonitorSummary(
    total=len(monitors),
    up=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UP),
    down=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DOWN),
    degraded=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DEGRADED),
    unknown=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UNKNOWN),
  )

  since = datetime.now(UTC) - timedelta(hours=24)
  uptime_by_monitor = await _uptime_by_monitor(session, since)

  monitor_ids = [monitor.id for monitor in monitors]
  global_uptime: float | None = None
  if monitor_ids:
    up_case = case((CheckResult.status == MonitorStatus.UP, 1), else_=0)
    result = await session.execute(
      select(func.count(), func.sum(up_case))
      .select_from(CheckResult)
      .where(
        CheckResult.checked_at >= since,
        CheckResult.monitor_id.in_(monitor_ids),
      )
    )
    total_checks, up_checks = result.one()
    if total_checks and total_checks > 0:
      global_uptime = round((up_checks or 0) / total_checks * 100, 1)

  services = [
    StatusMonitorItem(
      id=monitor.id,
      name=monitor.name,
      type=monitor.type,
      status=monitor.status,
      uptime_24h_percent=uptime_by_monitor.get(monitor.id),
      response_time_ms=monitor.response_time_ms,
      last_checked_at=monitor.last_checked_at,
    )
    for monitor in monitors
  ]

  incidents = await incident_service.list_incidents(session, status=IncidentStatus.OPEN, days=30)
  open_incidents = [
    PublicStatusIncident(
      id=incident.id,
      monitor_name=incident.monitor_name,
      status=incident.status,
      started_at=incident.started_at,
      error_message=incident.error_message,
      failed_check_count=incident.failed_check_count,
    )
    for incident in incidents
  ]

  return PublicStatusResponse(
    status=_derive_overall_status(summary),
    uptime_24h_percent=global_uptime,
    monitors=summary,
    services=services,
    open_incidents=open_incidents,
    updated_at=datetime.now(UTC),
  )
