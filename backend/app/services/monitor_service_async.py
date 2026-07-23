from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import DEFAULT_PAGE_LIMIT, MAX_SPARKLINE_POINTS
from app.models import CheckResult, Monitor, MonitorStatus
from app.schemas.check_result import CheckResultBrief, CheckResultPage, CheckResultRead
from app.schemas.monitor import DashboardStats, MonitorCreate, MonitorListItem, MonitorRead, MonitorSummary


def _to_read(monitor: Monitor) -> MonitorRead:
  return MonitorRead.model_validate(monitor)


async def get_monitor(session: AsyncSession, monitor_id: int) -> Monitor | None:
  return await session.get(Monitor, monitor_id)


async def list_monitors(session: AsyncSession) -> list[MonitorListItem]:
  monitors = (await session.scalars(select(Monitor).order_by(Monitor.id))).all()
  if not monitors:
    return []

  recent_by_monitor = await _recent_checks_by_monitor(
    session, [monitor.id for monitor in monitors], limit=MAX_SPARKLINE_POINTS
  )

  items: list[MonitorListItem] = []
  for monitor in monitors:
    item = MonitorListItem.model_validate(monitor)
    item.recent_checks = [
      CheckResultBrief.model_validate(result) for result in recent_by_monitor.get(monitor.id, [])
    ]
    items.append(item)
  return items


async def create_monitor(session: AsyncSession, payload: MonitorCreate) -> MonitorRead:
  monitor = Monitor(
    name=payload.name,
    type=payload.type,
    target=payload.target,
    interval_seconds=payload.interval_seconds,
    timeout_seconds=payload.timeout_seconds,
    enabled=payload.enabled,
  )
  session.add(monitor)
  await session.commit()
  await session.refresh(monitor)
  return _to_read(monitor)


async def list_check_results(
  session: AsyncSession,
  monitor_id: int,
  *,
  limit: int = DEFAULT_PAGE_LIMIT,
  offset: int = 0,
) -> CheckResultPage | None:
  monitor = await session.get(Monitor, monitor_id)
  if monitor is None:
    return None

  total = await session.scalar(
    select(func.count()).select_from(CheckResult).where(CheckResult.monitor_id == monitor_id)
  )
  total = total or 0

  rows = (
    await session.scalars(
      select(CheckResult)
      .where(CheckResult.monitor_id == monitor_id)
      .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
      .limit(limit)
      .offset(offset)
    )
  ).all()

  items = [CheckResultRead.model_validate(row) for row in rows]
  return CheckResultPage(
    items=items,
    total=total,
    limit=limit,
    offset=offset,
    has_more=offset + len(items) < total,
  )


async def _recent_checks_by_monitor(
  session: AsyncSession,
  monitor_ids: list[int],
  *,
  limit: int,
) -> dict[int, list[CheckResult]]:
  if not monitor_ids or limit <= 0:
    return {}

  grouped: dict[int, list[CheckResult]] = {monitor_id: [] for monitor_id in monitor_ids}
  for monitor_id in monitor_ids:
    rows = (
      await session.scalars(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
        .limit(limit)
      )
    ).all()
    grouped[monitor_id] = list(reversed(rows))
  return grouped


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
