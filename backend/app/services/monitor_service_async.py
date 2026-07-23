from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CheckResult, Monitor, MonitorStatus
from app.schemas.monitor import DashboardStats, MonitorCreate, MonitorRead, MonitorSummary


def _to_read(monitor: Monitor) -> MonitorRead:
  return MonitorRead.model_validate(monitor)


async def list_monitors(session: AsyncSession) -> list[MonitorRead]:
  result = await session.scalars(select(Monitor).order_by(Monitor.id))
  return [_to_read(monitor) for monitor in result.all()]


async def create_monitor(session: AsyncSession, payload: MonitorCreate) -> MonitorRead:
  monitor = Monitor(
    name=payload.name,
    type=payload.type,
    target=payload.target,
    interval_seconds=payload.interval_seconds,
    enabled=payload.enabled,
  )
  session.add(monitor)
  await session.commit()
  await session.refresh(monitor)
  return _to_read(monitor)


async def dashboard_stats(session: AsyncSession) -> DashboardStats:
  monitors = (await session.scalars(select(Monitor))).all()
  summary = MonitorSummary(
    total=len(monitors),
    up=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UP),
    down=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DOWN),
    degraded=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DEGRADED),
    unknown=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UNKNOWN),
  )

  since = datetime.now(UTC) - timedelta(hours=24)
  total_checks = await session.scalar(
    select(func.count()).select_from(CheckResult).where(CheckResult.checked_at >= since)
  )
  up_checks = await session.scalar(
    select(func.count())
    .select_from(CheckResult)
    .where(CheckResult.checked_at >= since, CheckResult.status == MonitorStatus.UP)
  )

  uptime_percent: float | None = None
  if total_checks and total_checks > 0:
    uptime_percent = round((up_checks or 0) / total_checks * 100, 1)

  return DashboardStats(monitors=summary, uptime_24h_percent=uptime_percent)
