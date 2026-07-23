from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.checks.runner import run_check
from app.models import CheckResult, Monitor, MonitorStatus
from app.schemas.monitor import DashboardStats, MonitorCreate, MonitorRead, MonitorSummary


def _ensure_utc(value: datetime) -> datetime:
  if value.tzinfo is None:
    return value.replace(tzinfo=UTC)
  return value.astimezone(UTC)


def _to_read(monitor: Monitor) -> MonitorRead:
  return MonitorRead.model_validate(monitor)


def list_monitors(session: Session) -> list[MonitorRead]:
  monitors = session.scalars(select(Monitor).order_by(Monitor.id)).all()
  return [_to_read(monitor) for monitor in monitors]


def get_monitor(session: Session, monitor_id: int) -> Monitor | None:
  return session.get(Monitor, monitor_id)


def create_monitor(session: Session, payload: MonitorCreate) -> MonitorRead:
  monitor = Monitor(
    name=payload.name,
    type=payload.type,
    target=payload.target,
    interval_seconds=payload.interval_seconds,
    enabled=payload.enabled,
  )
  session.add(monitor)
  session.commit()
  session.refresh(monitor)
  return _to_read(monitor)


def get_due_monitors(session: Session, *, now: datetime | None = None) -> list[Monitor]:
  current_time = now or datetime.now(UTC)
  monitors = session.scalars(select(Monitor).where(Monitor.enabled.is_(True))).all()

  due: list[Monitor] = []
  for monitor in monitors:
    if monitor.last_checked_at is None:
      due.append(monitor)
      continue

    next_check_at = _ensure_utc(monitor.last_checked_at) + timedelta(seconds=monitor.interval_seconds)
    if next_check_at <= current_time:
      due.append(monitor)

  return due


def execute_check(session: Session, monitor: Monitor) -> CheckResult:
  outcome = run_check(monitor.type, monitor.target, monitor.timeout_seconds)
  checked_at = datetime.now(UTC)

  result = CheckResult(
    monitor_id=monitor.id,
    status=outcome.status,
    response_time_ms=outcome.response_time_ms,
    status_code=outcome.status_code,
    error_message=outcome.error_message,
    checked_at=checked_at,
  )
  session.add(result)

  monitor.status = outcome.status
  monitor.response_time_ms = outcome.response_time_ms
  monitor.last_checked_at = checked_at

  session.commit()
  session.refresh(result)
  return result


def dashboard_stats(session: Session) -> DashboardStats:
  monitors = session.scalars(select(Monitor)).all()
  summary = MonitorSummary(
    total=len(monitors),
    up=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UP),
    down=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DOWN),
    degraded=sum(1 for monitor in monitors if monitor.status == MonitorStatus.DEGRADED),
    unknown=sum(1 for monitor in monitors if monitor.status == MonitorStatus.UNKNOWN),
  )

  since = datetime.now(UTC) - timedelta(hours=24)
  total_checks = session.scalar(
    select(func.count())
    .select_from(CheckResult)
    .where(CheckResult.checked_at >= since)
  )
  up_checks = session.scalar(
    select(func.count())
    .select_from(CheckResult)
    .where(CheckResult.checked_at >= since, CheckResult.status == MonitorStatus.UP)
  )

  uptime_percent: float | None = None
  if total_checks and total_checks > 0:
    uptime_percent = round((up_checks or 0) / total_checks * 100, 1)

  return DashboardStats(monitors=summary, uptime_24h_percent=uptime_percent)
