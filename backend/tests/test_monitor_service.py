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
