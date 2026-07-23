"""Rollup and purge check history across retention tiers."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from app.models import CheckResult, CheckResultDaily, CheckResultHourly, MonitorStatus
from app.retention import (
  DAILY_RETENTION_DAYS,
  HOURLY_RETENTION_DAYS,
  PURGE_BATCH_SIZE,
  RAW_RETENTION_DAYS,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetentionStats:
  hourly_buckets_upserted: int = 0
  daily_buckets_upserted: int = 0
  raw_deleted: int = 0
  hourly_deleted: int = 0
  daily_deleted: int = 0


def _ensure_utc(value: datetime) -> datetime:
  if value.tzinfo is None:
    return value.replace(tzinfo=UTC)
  return value.astimezone(UTC)


def _truncate_hour(value: datetime) -> datetime:
  value = _ensure_utc(value)
  return value.replace(minute=0, second=0, microsecond=0)


def _latency_stats(latencies: list[float]) -> tuple[float | None, float | None, float | None]:
  if not latencies:
    return None, None, None
  return sum(latencies) / len(latencies), min(latencies), max(latencies)


def run_retention_maintenance(session: Session, *, now: datetime | None = None) -> RetentionStats:
  """Roll up expiring data, then purge each tier. Safe to run repeatedly (idempotent upserts)."""
  current_time = _ensure_utc(now or datetime.now(UTC))
  raw_cutoff = current_time - timedelta(days=RAW_RETENTION_DAYS)
  hourly_cutoff = current_time - timedelta(days=HOURLY_RETENTION_DAYS)
  daily_cutoff = current_time - timedelta(days=DAILY_RETENTION_DAYS)

  hourly_upserted = rollup_raw_to_hourly(session, before=raw_cutoff)
  daily_upserted = rollup_hourly_to_daily(session, before=hourly_cutoff)
  raw_deleted = purge_raw_before(session, raw_cutoff)
  hourly_deleted = purge_hourly_before(session, hourly_cutoff)
  daily_deleted = purge_daily_before(session, daily_cutoff)
  session.commit()

  stats = RetentionStats(
    hourly_buckets_upserted=hourly_upserted,
    daily_buckets_upserted=daily_upserted,
    raw_deleted=raw_deleted,
    hourly_deleted=hourly_deleted,
    daily_deleted=daily_deleted,
  )
  logger.info("Retention maintenance complete: %s", stats)
  return stats


def rollup_raw_to_hourly(session: Session, *, before: datetime) -> int:
  """Aggregate raw checks older than `before` into hourly buckets."""
  before = _ensure_utc(before)
  dialect = session.bind.dialect.name if session.bind else "sqlite"

  if dialect == "postgresql":
    return _rollup_raw_to_hourly_postgres(session, before)

  return _rollup_raw_to_hourly_python(session, before)


def _rollup_raw_to_hourly_python(session: Session, before: datetime) -> int:
  rows = session.scalars(select(CheckResult).where(CheckResult.checked_at < before)).all()
  buckets: dict[tuple[int, datetime], list[CheckResult]] = defaultdict(list)
  for row in rows:
    buckets[(row.monitor_id, _truncate_hour(row.checked_at))].append(row)

  upserted = 0
  for (monitor_id, hour), checks in buckets.items():
    _upsert_hourly_bucket(session, monitor_id, hour, checks)
    upserted += 1
  return upserted


def _rollup_raw_to_hourly_postgres(session: Session, before: datetime) -> int:
  hour_expr = func.date_trunc("hour", CheckResult.checked_at)
  aggregated = session.execute(
    select(
      CheckResult.monitor_id,
      hour_expr.label("hour"),
      func.count().label("total_checks"),
      func.sum(case((CheckResult.status == MonitorStatus.UP, 1), else_=0)).label("up_checks"),
      func.avg(CheckResult.response_time_ms).label("avg_latency_ms"),
      func.min(CheckResult.response_time_ms).label("min_latency_ms"),
      func.max(CheckResult.response_time_ms).label("max_latency_ms"),
    )
    .where(CheckResult.checked_at < before)
    .group_by(CheckResult.monitor_id, hour_expr)
  ).all()

  for row in aggregated:
    _upsert_hourly_values(
      session,
      monitor_id=row.monitor_id,
      hour=_ensure_utc(row.hour),
      total_checks=int(row.total_checks),
      up_checks=int(row.up_checks or 0),
      avg_latency_ms=row.avg_latency_ms,
      min_latency_ms=row.min_latency_ms,
      max_latency_ms=row.max_latency_ms,
    )
  return len(aggregated)


def _upsert_hourly_bucket(
  session: Session, monitor_id: int, hour: datetime, checks: list[CheckResult]
) -> None:
  latencies = [c.response_time_ms for c in checks if c.response_time_ms is not None]
  avg_ms, min_ms, max_ms = _latency_stats(latencies)
  up_checks = sum(1 for check in checks if check.status == MonitorStatus.UP)
  _upsert_hourly_values(
    session,
    monitor_id=monitor_id,
    hour=hour,
    total_checks=len(checks),
    up_checks=up_checks,
    avg_latency_ms=avg_ms,
    min_latency_ms=min_ms,
    max_latency_ms=max_ms,
  )


def _upsert_hourly_values(
  session: Session,
  *,
  monitor_id: int,
  hour: datetime,
  total_checks: int,
  up_checks: int,
  avg_latency_ms: float | None,
  min_latency_ms: float | None,
  max_latency_ms: float | None,
) -> None:
  existing = session.scalar(
    select(CheckResultHourly).where(
      CheckResultHourly.monitor_id == monitor_id, CheckResultHourly.hour == hour
    )
  )
  if existing is None:
    session.add(
      CheckResultHourly(
        monitor_id=monitor_id,
        hour=hour,
        total_checks=total_checks,
        up_checks=up_checks,
        avg_latency_ms=avg_latency_ms,
        min_latency_ms=min_latency_ms,
        max_latency_ms=max_latency_ms,
      )
    )
    return

  existing.total_checks += total_checks
  existing.up_checks += up_checks
  if avg_latency_ms is not None:
    if existing.avg_latency_ms is None:
      existing.avg_latency_ms = avg_latency_ms
    else:
      existing.avg_latency_ms = (existing.avg_latency_ms + avg_latency_ms) / 2
  if min_latency_ms is not None:
    existing.min_latency_ms = (
      min(existing.min_latency_ms, min_latency_ms)
      if existing.min_latency_ms is not None
      else min_latency_ms
    )
  if max_latency_ms is not None:
    existing.max_latency_ms = (
      max(existing.max_latency_ms, max_latency_ms)
      if existing.max_latency_ms is not None
      else max_latency_ms
    )


def rollup_hourly_to_daily(session: Session, *, before: datetime) -> int:
  before = _ensure_utc(before)
  rows = session.scalars(select(CheckResultHourly).where(CheckResultHourly.hour < before)).all()
  buckets: dict[tuple[int, date], list[CheckResultHourly]] = defaultdict(list)
  for row in rows:
    buckets[(row.monitor_id, _ensure_utc(row.hour).date())].append(row)

  upserted = 0
  for (monitor_id, day), hourlies in buckets.items():
    total = sum(h.total_checks for h in hourlies)
    up = sum(h.up_checks for h in hourlies)
    weighted_latency = [
      h.avg_latency_ms for h in hourlies if h.avg_latency_ms is not None and h.total_checks > 0
    ]
    avg_latency = (
      sum(h.avg_latency_ms * h.total_checks for h in hourlies if h.avg_latency_ms is not None)
      / max(sum(h.total_checks for h in hourlies if h.avg_latency_ms is not None), 1)
      if weighted_latency
      else None
    )
    down_checks = total - up
    downtime_minutes = sum(
      max(0, h.total_checks - h.up_checks) * 60 // max(h.total_checks, 1) for h in hourlies
    )

    existing = session.scalar(
      select(CheckResultDaily).where(CheckResultDaily.monitor_id == monitor_id, CheckResultDaily.day == day)
    )
    if existing is None:
      session.add(
        CheckResultDaily(
          monitor_id=monitor_id,
          day=day,
          total_checks=total,
          up_checks=up,
          avg_latency_ms=avg_latency,
          downtime_minutes=downtime_minutes,
        )
      )
    else:
      existing.total_checks += total
      existing.up_checks += up
      existing.downtime_minutes += downtime_minutes
      if avg_latency is not None and existing.avg_latency_ms is not None:
        existing.avg_latency_ms = (existing.avg_latency_ms + avg_latency) / 2
      elif avg_latency is not None:
        existing.avg_latency_ms = avg_latency
    upserted += 1
  return upserted


def purge_raw_before(session: Session, cutoff: datetime) -> int:
  return _batched_delete(session, CheckResult, CheckResult.checked_at < cutoff)


def purge_hourly_before(session: Session, cutoff: datetime) -> int:
  return _batched_delete(session, CheckResultHourly, CheckResultHourly.hour < cutoff)


def purge_daily_before(session: Session, cutoff: datetime) -> int:
  cutoff_date = _ensure_utc(cutoff).date()
  return _batched_delete(session, CheckResultDaily, CheckResultDaily.day < cutoff_date)


def _batched_delete(session: Session, model, condition) -> int:
  deleted = 0
  while True:
    ids = session.scalars(select(model.id).where(condition).limit(PURGE_BATCH_SIZE)).all()
    if not ids:
      break
    session.execute(delete(model).where(model.id.in_(ids)))
    session.flush()
    deleted += len(ids)
  return deleted
