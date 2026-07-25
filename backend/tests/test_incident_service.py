from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Incident, Monitor, MonitorStatus, MonitorType
from app.models.enums import IncidentStatus
from app.services import incident_service


@pytest.fixture
def session():
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  factory = sessionmaker(bind=engine)
  with factory() as db:
    monitor = Monitor(
      name="API",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      timeout_seconds=10,
      enabled=True,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    yield db, monitor


def test_opens_incident_on_transition_to_down(session) -> None:
  db, monitor = session
  now = datetime(2026, 7, 25, 10, 0, tzinfo=UTC)

  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.UP,
    new_status=MonitorStatus.DOWN,
    error_message="HTTP 503",
    now=now,
  )

  incident = db.query(Incident).one()
  assert incident.status == IncidentStatus.OPEN
  assert incident.failed_check_count == 1
  assert incident.error_message == "HTTP 503"
  assert incident.ended_at is None


def test_updates_open_incident_while_down(session) -> None:
  db, monitor = session
  started = datetime(2026, 7, 25, 10, 0, tzinfo=UTC)
  later = datetime(2026, 7, 25, 10, 1, tzinfo=UTC)

  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.UP,
    new_status=MonitorStatus.DOWN,
    error_message="HTTP 503",
    now=started,
  )
  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.DOWN,
    new_status=MonitorStatus.DOWN,
    error_message="Timeout",
    now=later,
  )

  incidents = db.query(Incident).all()
  assert len(incidents) == 1
  assert incidents[0].failed_check_count == 2
  assert incidents[0].error_message == "Timeout"


def test_resolves_incident_on_recovery(session) -> None:
  db, monitor = session
  started = datetime(2026, 7, 25, 10, 0, tzinfo=UTC)
  recovered = datetime(2026, 7, 25, 10, 15, tzinfo=UTC)

  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.UP,
    new_status=MonitorStatus.DOWN,
    error_message="HTTP 503",
    now=started,
  )
  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.DOWN,
    new_status=MonitorStatus.UP,
    error_message=None,
    now=recovered,
  )

  incident = db.query(Incident).one()
  assert incident.status == IncidentStatus.RESOLVED
  assert incident.ended_at is not None


def test_degraded_to_down_opens_incident(session) -> None:
  db, monitor = session
  now = datetime(2026, 7, 25, 10, 0, tzinfo=UTC)

  incident_service.handle_status_change(
    db,
    monitor_id=monitor.id,
    previous_status=MonitorStatus.DEGRADED,
    new_status=MonitorStatus.DOWN,
    error_message="HTTP 500",
    now=now,
  )

  assert db.query(Incident).count() == 1
