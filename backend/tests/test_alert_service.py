from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.alerts import DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES
from app.config import Settings
from app.core.database import Base
from app.models import AlertRecipient, AlertSettings, CheckResult, Monitor, MonitorStatus, MonitorType
from app.models.alert_settings import ACCOUNT_SETTINGS_ID
from app.services import alert_service
from app.services.email_service import EmailPayload, send_email


def test_send_email_skipped_when_disabled() -> None:
  settings = Settings(alerts_enabled=False, smtp_host="smtp.example.com")
  sent = send_email(
    EmailPayload(to=["a@example.com"], subject="Test", body="Hi"),
    settings=settings,
  )
  assert sent is False


def test_send_email_skipped_without_smtp_host() -> None:
  settings = Settings(alerts_enabled=True, smtp_host=None)
  sent = send_email(
    EmailPayload(to=["a@example.com"], subject="Test", body="Hi"),
    settings=settings,
  )
  assert sent is False


@patch("app.services.email_service.smtplib.SMTP")
def test_send_email_via_smtp(mock_smtp_class: MagicMock) -> None:
  mock_smtp = MagicMock()
  mock_smtp_class.return_value.__enter__.return_value = mock_smtp

  settings = Settings(
    alerts_enabled=True,
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_user="user",
    smtp_password="pass",
    smtp_from="upCheck <alerts@example.com>",
    smtp_use_tls=True,
  )
  sent = send_email(
    EmailPayload(to=["ops@example.com"], subject="[upCheck] DOWN", body="Monitor down"),
    settings=settings,
  )

  assert sent is True
  mock_smtp.starttls.assert_called_once()
  mock_smtp.login.assert_called_once_with("user", "pass")
  mock_smtp.send_message.assert_called_once()


@pytest.fixture
def sync_session():
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
  with Session() as session:
    monitor = Monitor(
      name="API",
      type=MonitorType.HTTP,
      target="https://example.com",
      interval_seconds=60,
      status=MonitorStatus.UP,
    )
    session.add(monitor)
    session.add(AlertRecipient(email="ops@example.com", enabled=True))
    session.add(
      AlertSettings(
        id=ACCOUNT_SETTINGS_ID,
        down_alert_cooldown_minutes=DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES,
        alert_on_down=True,
        alert_on_recovery=False,
      )
    )
    session.commit()
    yield session, monitor.id


def test_handle_status_change_enqueues_on_up_to_down(sync_session) -> None:
  session, monitor_id = sync_session
  monitor = session.get(Monitor, monitor_id)
  assert monitor is not None
  check = CheckResult(
    monitor_id=monitor_id,
    status=MonitorStatus.DOWN,
    error_message="HTTP 503",
    checked_at=datetime.now(UTC),
  )
  session.add(check)
  session.commit()

  with patch("app.worker.tasks.send_down_alert_email") as mock_task:
    mock_task.delay = MagicMock()
    enqueued = alert_service.handle_status_change(
      session,
      monitor=monitor,
      previous_status=MonitorStatus.UP,
      new_status=MonitorStatus.DOWN,
      check_result=check,
    )

  assert enqueued is True
  mock_task.delay.assert_called_once_with(monitor_id, check.id)
  session.refresh(monitor)
  assert monitor.last_down_alert_at is not None


def test_handle_status_change_skips_when_alert_on_down_disabled(sync_session) -> None:
  session, monitor_id = sync_session
  account = session.get(AlertSettings, ACCOUNT_SETTINGS_ID)
  assert account is not None
  account.alert_on_down = False
  session.commit()
  monitor = session.get(Monitor, monitor_id)
  assert monitor is not None
  check = CheckResult(
    monitor_id=monitor_id,
    status=MonitorStatus.DOWN,
    checked_at=datetime.now(UTC),
  )
  session.add(check)
  session.commit()

  with patch("app.worker.tasks.send_down_alert_email") as mock_task:
    mock_task.delay = MagicMock()
    enqueued = alert_service.handle_status_change(
      session,
      monitor=monitor,
      previous_status=MonitorStatus.UP,
      new_status=MonitorStatus.DOWN,
      check_result=check,
    )

  assert enqueued is False
  mock_task.delay.assert_not_called()


def test_handle_status_change_respects_cooldown(sync_session) -> None:
  session, monitor_id = sync_session
  monitor = session.get(Monitor, monitor_id)
  assert monitor is not None
  now = datetime.now(UTC)
  monitor.last_down_alert_at = now - timedelta(minutes=DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES - 1)
  session.commit()
  check = CheckResult(
    monitor_id=monitor_id,
    status=MonitorStatus.DOWN,
    checked_at=now,
  )
  session.add(check)
  session.commit()

  with patch("app.worker.tasks.send_down_alert_email") as mock_task:
    mock_task.delay = MagicMock()
    enqueued = alert_service.handle_status_change(
      session,
      monitor=monitor,
      previous_status=MonitorStatus.UP,
      new_status=MonitorStatus.DOWN,
      check_result=check,
      now=now,
    )

  assert enqueued is False
  mock_task.delay.assert_not_called()


def test_recovery_alert_when_enabled(sync_session) -> None:
  session, monitor_id = sync_session
  account = session.get(AlertSettings, ACCOUNT_SETTINGS_ID)
  assert account is not None
  account.alert_on_recovery = True
  session.commit()
  monitor = session.get(Monitor, monitor_id)
  assert monitor is not None
  monitor.status = MonitorStatus.DOWN
  monitor.last_down_alert_at = datetime.now(UTC)
  session.commit()
  check = CheckResult(
    monitor_id=monitor_id,
    status=MonitorStatus.UP,
    checked_at=datetime.now(UTC),
  )
  session.add(check)
  session.commit()

  with patch("app.worker.tasks.send_recovery_alert_email") as mock_task:
    mock_task.delay = MagicMock()
    enqueued = alert_service.handle_status_change(
      session,
      monitor=monitor,
      previous_status=MonitorStatus.DOWN,
      new_status=MonitorStatus.UP,
      check_result=check,
    )

  assert enqueued is True
  mock_task.delay.assert_called_once_with(monitor_id, check.id)
  session.refresh(monitor)
  assert monitor.last_down_alert_at is None


def test_deliver_down_alert_builds_recipient_list(sync_session) -> None:
  session, monitor_id = sync_session
  check = CheckResult(
    monitor_id=monitor_id,
    status=MonitorStatus.DOWN,
    error_message="timeout",
    checked_at=datetime.now(UTC),
  )
  session.add(check)
  session.commit()

  with patch("app.services.alert_service.send_email", return_value=True) as mock_send:
    sent = alert_service.deliver_down_alert(session, monitor_id, check.id)

  assert sent is True
  payload = mock_send.call_args.args[0]
  assert payload.to == ["ops@example.com"]
  assert "DOWN" in payload.subject
