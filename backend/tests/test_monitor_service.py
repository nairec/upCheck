from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, or_, select, update
from sqlalchemy.orm import sessionmaker

from app.checks.base import CheckOutcome
from app.core.database import Base
from app.models import CheckResult, Monitor, MonitorStatus, MonitorType
from app.services import monitor_service


def test_get_due_monitors_respects_interval() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)

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

    due = monitor_service.get_due_monitors(session, now=datetime.now(UTC))
    assert len(due) == 1

    monitor.last_checked_at = datetime.now(UTC) - timedelta(seconds=10)
    session.commit()

    not_due = monitor_service.get_due_monitors(session, now=datetime.now(UTC))
    assert len(not_due) == 0


def test_get_due_monitors_excludes_active_lease() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="In flight",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      lease_until=now + timedelta(seconds=30),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()

    due = monitor_service.get_due_monitors(session, now=now)
    assert due == []


def test_claim_monitor_for_check_does_not_advance_last_checked_at() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)
  last_checked = now - timedelta(seconds=120)

  with Session() as session:
    monitor = Monitor(
      name="Claimable",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=last_checked,
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claimed is not None
    assert claimed.last_checked_at is not None
    assert claimed.last_checked_at.replace(tzinfo=UTC) == last_checked
    assert claimed.lease_until is not None
    assert claimed.lease_until.replace(tzinfo=UTC) > now


def test_monitor_becomes_due_after_lease_expires_without_double_interval() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)
  last_checked = now - timedelta(seconds=120)

  with Session() as session:
    monitor = Monitor(
      name="Recoverable",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=last_checked,
      lease_until=now - timedelta(seconds=1),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()

    due = monitor_service.get_due_monitors(session, now=now)
    assert len(due) == 1


def test_release_monitor_lease_discards_pending_check_results() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Orphaned result",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claimed is not None
    session.add(
      CheckResult(
        monitor_id=monitor_id,
        status=MonitorStatus.UP,
        response_time_ms=12.0,
        checked_at=now,
      )
    )
    monitor_service.release_monitor_lease(
      session, monitor_id, expected_lease_until=claimed.lease_until
    )

  with Session() as session:
    assert session.scalars(select(CheckResult)).all() == []
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    assert monitor.lease_until is None


def test_execute_check_rolls_back_on_update_failure() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Update failure",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claimed is not None
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None

    with patch(
      "app.services.monitor_service.run_check",
      return_value=CheckOutcome(status=MonitorStatus.UP, response_time_ms=12.0),
    ):
      with patch.object(session, "execute", side_effect=RuntimeError("update failed")):
        with pytest.raises(RuntimeError, match="update failed"):
          monitor_service.execute_check(
            session, monitor, expected_lease_until=claimed.lease_until
          )

  with Session() as session:
    assert session.scalars(select(CheckResult)).all() == []
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    assert monitor.lease_until is not None


def test_release_monitor_lease_allows_immediate_retry() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
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

  with Session() as session:
    claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claimed is not None
    monitor_service.release_monitor_lease(
      session, monitor_id, expected_lease_until=claimed.lease_until
    )

  with Session() as session:
    due = monitor_service.get_due_monitors(session, now=now)
    assert len(due) == 1


def test_claim_monitor_for_check_prevents_duplicate_claims() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Claimable",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    first_claim = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert first_claim is not None

  with Session() as session:
    second_claim = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert second_claim is None
    due = monitor_service.get_due_monitors(session, now=now)
    assert due == []


def test_not_due_with_expired_lease_after_recent_check() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Recently checked",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=10),
      lease_until=now - timedelta(seconds=1),
      status=MonitorStatus.UP,
    )
    session.add(monitor)
    session.commit()

    due = monitor_service.get_due_monitors(session, now=now)
    assert due == []


def test_claim_returns_none_after_another_worker_completes_check() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Race",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    monitor.last_checked_at = now
    monitor.lease_until = None
    session.commit()

  with Session() as session:
    claim = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claim is None


def test_claim_update_fails_when_last_checked_changes_between_read_and_write() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Optimistic lock",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id
    stale_last_checked = monitor.last_checked_at

  with Session() as session:
    session.execute(
      Monitor.__table__.update()
      .where(Monitor.id == monitor_id)
      .values(last_checked_at=now, lease_until=None)
    )
    session.commit()

    result = session.execute(
      update(Monitor)
      .where(
        Monitor.id == monitor_id,
        Monitor.enabled.is_(True),
        or_(Monitor.lease_until.is_(None), Monitor.lease_until <= now),
        Monitor.last_checked_at == stale_last_checked,
      )
      .values(lease_until=now + timedelta(seconds=60))
    )
    assert result.rowcount == 0


def test_release_monitor_lease_only_clears_own_lease() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Contested",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    first_claim = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert first_claim is not None
    stale_lease = first_claim.lease_until

  with Session() as session:
    session.execute(
      Monitor.__table__.update()
      .where(Monitor.id == monitor_id)
      .values(lease_until=now + timedelta(hours=1))
    )
    session.commit()

  with Session() as session:
    released = monitor_service.release_monitor_lease(
      session, monitor_id, expected_lease_until=stale_lease
    )
    assert released is False
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    assert monitor.lease_until is not None
    assert monitor.lease_until.replace(tzinfo=UTC) > now


def test_execute_check_rejects_stale_lease() -> None:
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Stale lease",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  with Session() as session:
    claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
    assert claimed is not None
    stale_lease = claimed.lease_until

  with Session() as session:
    session.execute(
      Monitor.__table__.update()
      .where(Monitor.id == monitor_id)
      .values(lease_until=now + timedelta(hours=1))
    )
    session.commit()

  with Session() as session:
    monitor = session.get(Monitor, monitor_id)
    assert monitor is not None
    with patch(
      "app.services.monitor_service.run_check",
      return_value=CheckOutcome(status=MonitorStatus.UP, response_time_ms=12.0),
    ):
      result = monitor_service.execute_check(
        session, monitor, expected_lease_until=stale_lease
      )
    assert result is None

    refreshed = session.get(Monitor, monitor_id)
    assert refreshed is not None
    assert refreshed.lease_until is not None
    assert refreshed.lease_until.replace(tzinfo=UTC) > now
    assert refreshed.last_checked_at.replace(tzinfo=UTC) == (now - timedelta(seconds=120))


def test_concurrent_claims_only_one_succeeds(tmp_path) -> None:
  db_path = tmp_path / "claims.db"
  engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
  )
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine)
  now = datetime.now(UTC)

  with Session() as session:
    monitor = Monitor(
      name="Concurrent",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      last_checked_at=now - timedelta(seconds=120),
      status=MonitorStatus.UNKNOWN,
    )
    session.add(monitor)
    session.commit()
    monitor_id = monitor.id

  results: list[bool] = []
  barrier = Barrier(8)

  def try_claim() -> None:
    barrier.wait()
    with Session() as session:
      claimed = monitor_service.claim_monitor_for_check(session, monitor_id, now=now)
      results.append(claimed is not None)

  threads = [Thread(target=try_claim) for _ in range(8)]
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()

  assert sum(results) == 1
