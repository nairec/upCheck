from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import DEFAULT_PAGE_LIMIT, MAX_SPARKLINE_POINTS
from app.history import (
  MAX_HISTORY_RAW_POINTS,
  HistoryGranularity,
  max_days_for,
  resolve_granularity,
)
from app.models import CheckResult, CheckResultDaily, CheckResultHourly, Monitor, MonitorStatus
from app.schemas.check_result import CheckResultBrief, CheckResultPage, CheckResultRead
from app.schemas.history import HistoryPoint, MonitorHistoryResponse
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


def _uptime_percent(up_checks: int, total_checks: int) -> float:
  if total_checks <= 0:
    return 0.0
  return round(up_checks / total_checks * 100, 1)


async def get_monitor_history(
  session: AsyncSession,
  monitor_id: int,
  *,
  days: int,
  granularity: HistoryGranularity = HistoryGranularity.AUTO,
) -> MonitorHistoryResponse | None:
  monitor = await session.get(Monitor, monitor_id)
  if monitor is None:
    return None

  resolved = resolve_granularity(days, granularity)
  capped_days = min(days, max_days_for(resolved))
  since = datetime.now(UTC) - timedelta(days=capped_days)

  if resolved == HistoryGranularity.RAW:
    total = await session.scalar(
      select(func.count())
      .select_from(CheckResult)
      .where(CheckResult.monitor_id == monitor_id, CheckResult.checked_at >= since)
    )
    total = total or 0
    rows = (
      await session.scalars(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id, CheckResult.checked_at >= since)
        .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
        .limit(MAX_HISTORY_RAW_POINTS)
      )
    ).all()
    points = [
      HistoryPoint(
        at=row.checked_at,
        total_checks=1,
        up_checks=1 if row.status == MonitorStatus.UP else 0,
        uptime_percent=100.0 if row.status == MonitorStatus.UP else 0.0,
        avg_latency_ms=row.response_time_ms,
        status=row.status,
        status_code=row.status_code,
        error_message=CheckResultRead.model_validate(row).error_message,
        id=row.id,
      )
      for row in reversed(rows)
    ]
    return MonitorHistoryResponse(
      granularity=resolved,
      days=capped_days,
      points=points,
      total=total,
    )

  if resolved == HistoryGranularity.HOURLY:
    total = await session.scalar(
      select(func.count())
      .select_from(CheckResultHourly)
      .where(CheckResultHourly.monitor_id == monitor_id, CheckResultHourly.hour >= since)
    )
    total = total or 0
    rows = (
      await session.scalars(
        select(CheckResultHourly)
        .where(CheckResultHourly.monitor_id == monitor_id, CheckResultHourly.hour >= since)
        .order_by(CheckResultHourly.hour.asc())
      )
    ).all()
    points = [
      HistoryPoint(
        at=row.hour,
        total_checks=row.total_checks,
        up_checks=row.up_checks,
        uptime_percent=_uptime_percent(row.up_checks, row.total_checks),
        avg_latency_ms=row.avg_latency_ms,
        min_latency_ms=row.min_latency_ms,
        max_latency_ms=row.max_latency_ms,
      )
      for row in rows
    ]
    return MonitorHistoryResponse(
      granularity=resolved,
      days=capped_days,
      points=points,
      total=total,
    )

  since_day = since.date()
  total = await session.scalar(
    select(func.count())
    .select_from(CheckResultDaily)
    .where(CheckResultDaily.monitor_id == monitor_id, CheckResultDaily.day >= since_day)
  )
  total = total or 0
  rows = (
    await session.scalars(
      select(CheckResultDaily)
      .where(CheckResultDaily.monitor_id == monitor_id, CheckResultDaily.day >= since_day)
      .order_by(CheckResultDaily.day.asc())
    )
  ).all()
  points = [
    HistoryPoint(
      at=datetime.combine(row.day, datetime.min.time(), tzinfo=UTC),
      total_checks=row.total_checks,
      up_checks=row.up_checks,
      uptime_percent=_uptime_percent(row.up_checks, row.total_checks),
      avg_latency_ms=row.avg_latency_ms,
      downtime_minutes=row.downtime_minutes,
    )
    for row in rows
  ]
  return MonitorHistoryResponse(
    granularity=resolved,
    days=capped_days,
    points=points,
    total=total,
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
