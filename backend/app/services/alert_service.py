from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerts import DOWN_ALERT_COOLDOWN_MINUTES
from app.config import get_settings
from app.models import AlertRecipient, CheckResult, Monitor, MonitorStatus
from app.services.email_service import EmailPayload, send_email

logger = logging.getLogger(__name__)


def _ensure_utc(value: datetime) -> datetime:
  if value.tzinfo is None:
    return value.replace(tzinfo=UTC)
  return value.astimezone(UTC)


def get_enabled_recipient_emails(session: Session) -> list[str]:
  rows = session.scalars(
    select(AlertRecipient.email).where(AlertRecipient.enabled.is_(True)).order_by(AlertRecipient.email)
  ).all()
  return list(rows)


def handle_status_change(
  session: Session,
  *,
  monitor: Monitor,
  previous_status: MonitorStatus,
  new_status: MonitorStatus,
  check_result: CheckResult,
  now: datetime | None = None,
) -> bool:
  """React to a completed check. Returns True if a down alert was enqueued."""
  current_time = _ensure_utc(now or datetime.now(UTC))

  if new_status == MonitorStatus.UP:
    if monitor.last_down_alert_at is not None:
      monitor.last_down_alert_at = None
      session.commit()
    return False

  if not (previous_status == MonitorStatus.UP and new_status == MonitorStatus.DOWN):
    return False

  if not _cooldown_elapsed(monitor, current_time):
    logger.info("Down alert cooldown active for monitor %s — skipping", monitor.id)
    return False

  from app.worker.tasks import send_down_alert_email

  send_down_alert_email.delay(monitor.id, check_result.id)
  monitor.last_down_alert_at = current_time
  session.commit()
  return True


def _cooldown_elapsed(monitor: Monitor, now: datetime) -> bool:
  if monitor.last_down_alert_at is None:
    return True
  cooldown = timedelta(minutes=DOWN_ALERT_COOLDOWN_MINUTES)
  return _ensure_utc(monitor.last_down_alert_at) + cooldown <= now


def build_down_alert_email(
  session: Session, monitor_id: int, check_result_id: int
) -> EmailPayload | None:
  monitor = session.get(Monitor, monitor_id)
  check_result = session.get(CheckResult, check_result_id)
  if monitor is None or check_result is None:
    return None

  recipients = get_enabled_recipient_emails(session)
  if not recipients:
    logger.warning("No alert recipients configured — cannot send down alert for monitor %s", monitor_id)
    return None

  settings = get_settings()
  checked_at = _ensure_utc(check_result.checked_at).strftime("%Y-%m-%d %H:%M:%S UTC")
  error_line = check_result.error_message or "Sin detalle"
  latency_line = (
    f"{check_result.response_time_ms:.0f} ms" if check_result.response_time_ms is not None else "—"
  )

  detail_url = ""
  if settings.app_public_url:
    base = settings.app_public_url.rstrip("/")
    detail_url = f"\nVer monitor: {base}/monitors/{monitor.id}\n"

  body = (
    f"El monitor «{monitor.name}» ha pasado a DOWN.\n\n"
    f"Target: {monitor.target}\n"
    f"Tipo: {monitor.type.value.upper()}\n"
    f"Hora del check: {checked_at}\n"
    f"Latencia: {latency_line}\n"
    f"Error: {error_line}\n"
    f"{detail_url}\n"
    "— upCheck"
  )

  return EmailPayload(
    to=recipients,
    subject=f"[upCheck] DOWN — {monitor.name}",
    body=body,
  )


def deliver_down_alert(session: Session, monitor_id: int, check_result_id: int) -> bool:
  payload = build_down_alert_email(session, monitor_id, check_result_id)
  if payload is None:
    return False
  return send_email(payload)
