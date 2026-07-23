from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import CheckResult, CheckResultDaily, CheckResultHourly, Monitor, MonitorStatus, MonitorType
from app.retention import DAILY_RETENTION_DAYS, HOURLY_RETENTION_DAYS, RAW_RETENTION_DAYS
from app.services import retention_service


@pytest.fixture
def sync_session():
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
  with Session() as session:
    monitor = Monitor(
      name="Retention test",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      status=MonitorStatus.UP,
    )
    session.add(monitor)
    session.commit()
    yield session, monitor.id


def _add_raw_check(session, monitor_id: int, checked_at: datetime, *, up: bool = True) -> None:
  session.add(
    CheckResult(
      monitor_id=monitor_id,
      status=MonitorStatus.UP if up else MonitorStatus.DOWN,
      response_time_ms=120.0,
      checked_at=checked_at,
    )
  )


def test_rollup_raw_to_hourly_and_purge(sync_session) -> None:
  session, monitor_id = sync_session
  old_hour = datetime(2026, 1, 1, 10, 15, tzinfo=UTC)
  _add_raw_check(session, monitor_id, old_hour)
  _add_raw_check(session, monitor_id, old_hour.replace(minute=45), up=False)
  session.commit()

  cutoff = datetime(2026, 2, 1, tzinfo=UTC)
  upserted = retention_service.rollup_raw_to_hourly(session, before=cutoff)
  session.commit()

  assert upserted == 1
  hourly = session.scalars(select(CheckResultHourly)).all()
  assert len(hourly) == 1
  assert hourly[0].total_checks == 2
  assert hourly[0].up_checks == 1

  deleted = retention_service.purge_raw_before(session, cutoff)
  session.commit()
  assert deleted == 2
  assert session.scalars(select(CheckResult)).all() == []


def test_rollup_hourly_to_daily_and_purge(sync_session) -> None:
  session, monitor_id = sync_session
  session.add(
    CheckResultHourly(
      monitor_id=monitor_id,
      hour=datetime(2026, 1, 1, 8, tzinfo=UTC),
      total_checks=4,
      up_checks=3,
      avg_latency_ms=50.0,
      min_latency_ms=40.0,
      max_latency_ms=60.0,
    )
  )
  session.add(
    CheckResultHourly(
      monitor_id=monitor_id,
      hour=datetime(2026, 1, 1, 9, tzinfo=UTC),
      total_checks=2,
      up_checks=2,
      avg_latency_ms=70.0,
      min_latency_ms=65.0,
      max_latency_ms=75.0,
    )
  )
  session.commit()

  cutoff = datetime(2026, 2, 1, tzinfo=UTC)
  upserted = retention_service.rollup_hourly_to_daily(session, before=cutoff)
  session.commit()

  assert upserted == 1
  daily = session.scalar(
    select(CheckResultDaily).where(
      CheckResultDaily.monitor_id == monitor_id, CheckResultDaily.day == datetime(2026, 1, 1).date()
    )
  )
  assert daily is not None
  assert daily.total_checks == 6
  assert daily.up_checks == 5

  deleted = retention_service.purge_hourly_before(session, cutoff)
  session.commit()
  assert deleted == 2
  assert session.scalars(select(CheckResultHourly)).all() == []


def test_run_retention_maintenance_is_idempotent(sync_session) -> None:
  session, monitor_id = sync_session
  expired = datetime.now(UTC) - timedelta(days=RAW_RETENTION_DAYS + 1)
  _add_raw_check(session, monitor_id, expired)
  session.commit()

  stats_first = retention_service.run_retention_maintenance(session, now=datetime.now(UTC))
  stats_second = retention_service.run_retention_maintenance(session, now=datetime.now(UTC))

  assert stats_first.raw_deleted >= 1
  assert stats_second.raw_deleted == 0
  assert session.scalars(select(CheckResult)).all() == []


def test_retention_constants_ordering() -> None:
  assert RAW_RETENTION_DAYS < HOURLY_RETENTION_DAYS < DAILY_RETENTION_DAYS
