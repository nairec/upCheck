from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EmailPayload:
  to: list[str]
  subject: str
  body: str


def send_email(payload: EmailPayload, *, settings: Settings | None = None) -> bool:
  """Send a plain-text email via SMTP. Returns True if sent, False if skipped."""
  config = settings or get_settings()

  if not config.alerts_enabled:
    logger.info("Alerts disabled — email not sent (%s)", payload.subject)
    return False

  if not config.smtp_configured:
    logger.warning("SMTP not configured — email not sent (%s)", payload.subject)
    return False

  if not payload.to:
    logger.warning("No recipients — email not sent (%s)", payload.subject)
    return False

  message = EmailMessage()
  message["Subject"] = payload.subject
  message["From"] = config.smtp_from
  message["To"] = ", ".join(payload.to)
  message.set_content(payload.body)

  try:
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
      if config.smtp_use_tls:
        smtp.starttls()
      if config.smtp_user and config.smtp_password:
        smtp.login(config.smtp_user, config.smtp_password)
      smtp.send_message(message)
  except smtplib.SMTPException:
    logger.exception("SMTP delivery failed for subject: %s", payload.subject)
    raise

  logger.info("Alert email sent to %s — %s", payload.to, payload.subject)
  return True
