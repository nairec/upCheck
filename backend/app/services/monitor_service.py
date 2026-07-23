from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update
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


def _has_active_lease(monitor: Monitor, current_time: datetime) -> bool:
  if monitor.lease_until is None:
    return False
  return _ensure_utc(monitor.lease_until) > current_time


def _lease_duration(monitor: Monitor) -> timedelta:
  return timedelta(seconds=max(monitor.timeout_seconds + 30, 60))


def _is_due(monitor: Monitor, current_time: datetime) -> bool:
  if _has_active_lease(monitor, current_time):
    return False

  if monitor.last_checked_at is None:
    return True

  last_checked = _ensure_utc(monitor.last_checked_at)
  next_check_at = last_checked + timedelta(seconds=monitor.interval_seconds)
  return next_check_at <= current_time


def get_due_monitors(session: Session, *, now: datetime | None = None) -> list[Monitor]:
  current_time = now or datetime.now(UTC)
  monitors = session.scalars(select(Monitor).where(Monitor.enabled.is_(True))).all()
  return [monitor for monitor in monitors if _is_due(monitor, current_time)]


def claim_monitor_for_check(session: Session, monitor_id: int, *, now: datetime | None = None) -> Monitor | None:
  """Atomically reserve a due monitor so concurrent workers cannot run duplicate checks."""
  current_time = now or datetime.now(UTC)
  monitor = session.get(Monitor, monitor_id)
  if monitor is None or not monitor.enabled or not _is_due(monitor, current_time):
    return None

  lease_until = current_time + _lease_duration(monitor)
  last_checked = monitor.last_checked_at
  conditions = [
    Monitor.id == monitor_id,
    Monitor.enabled.is_(True),
    or_(Monitor.lease_until.is_(None), Monitor.lease_until <= current_time),
  ]
  if last_checked is None:
    conditions.append(Monitor.last_checked_at.is_(None))
  else:
    conditions.append(Monitor.last_checked_at == last_checked)

  result = session.execute(update(Monitor).where(*conditions).values(lease_until=lease_until))
  if result.rowcount != 1:
    session.rollback()
    return None

  session.commit()
  session.refresh(monitor)
  return monitor


def release_monitor_lease(
  session: Session,
  monitor_id: int,
  *,
  expected_lease_until: datetime,
) -> bool:
  """Clear an in-flight lease only if it still belongs to the caller."""
  session.rollback()
  result = session.execute(
    update(Monitor)
    .where(Monitor.id == monitor_id, Monitor.lease_until == expected_lease_until)
    .values(lease_until=None)
  )
  session.commit()
  return result.rowcount == 1


def execute_check(
  session: Session,
  monitor: Monitor,
  *,
  expected_lease_until: datetime | None = None,
) -> CheckResult | None:
  claimed_lease = expected_lease_until if expected_lease_until is not None else monitor.lease_until
  if claimed_lease is None:
    return None

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

  try:
    update_result = session.execute(
      update(Monitor)
      .where(Monitor.id == monitor.id, Monitor.lease_until == claimed_lease)
      .values(
        status=outcome.status,
        response_time_ms=outcome.response_time_ms,
        last_checked_at=checked_at,
        lease_until=None,
      )
    )
    if update_result.rowcount != 1:
      session.rollback()
      return None

    session.commit()
    session.refresh(result)
    return result
  except Exception:
    session.rollback()
    raise


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
