from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Monitor, MonitorStatus, MonitorType
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
    monitor_service.release_monitor_lease(session, monitor_id)

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
