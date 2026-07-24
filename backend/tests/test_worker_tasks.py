from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import CheckResult, Monitor, MonitorStatus, MonitorType
from app.worker.tasks import dispatch_due_checks, run_monitor_check, run_retention_maintenance


def test_dispatch_due_checks_reads_ids_before_session_closes() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

  with Session() as session:
    monitor = Monitor(
      name="Due",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=datetime.now(UTC) - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with patch("app.worker.tasks.SyncSessionLocal", Session):
    with patch("app.worker.tasks.run_monitor_check") as mock_run_monitor_check:
      mock_run_monitor_check.delay = MagicMock()
      dispatched = dispatch_due_checks()

  assert dispatched == 1
  mock_run_monitor_check.delay.assert_called_once_with(monitor_id)


def test_run_monitor_check_does_not_persist_orphaned_result_on_execute_failure() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Failed check",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  def failing_execute_check(session, monitor, *, expected_lease_until=None):
    session.add(
      CheckResult(
        monitor_id=monitor.id,
        status=MonitorStatus.UP,
        response_time_ms=12.0,
        checked_at=now,
      )
    )
    raise RuntimeError("simulated execute_check failure")

  with patch("app.worker.tasks.SyncSessionLocal", Session):
    with patch(
      "app.worker.tasks.monitor_service.execute_check",
      side_effect=failing_execute_check,
    ):
      with pytest.raises(RuntimeError, match="simulated execute_check failure"):
        run_monitor_check(monitor_id)

  with Session() as session:
    assert session.scalars(select(CheckResult)).all() == []
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    assert monitor.lease_until is None


def test_run_retention_maintenance_returns_stats() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

  with patch("app.worker.tasks.SyncSessionLocal", Session):
    result = run_retention_maintenance()

  assert result == {
    "hourly_buckets_upserted": 0,
    "daily_buckets_upserted": 0,
    "raw_deleted": 0,
    "hourly_deleted": 0,
    "daily_deleted": 0,
  }
