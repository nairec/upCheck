from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Monitor, MonitorStatus, MonitorType
from app.worker.tasks import dispatch_due_checks


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
