from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts import DOWN_ALERT_COOLDOWN_MINUTES
from app.config import get_settings
from app.models import AlertRecipient
from app.schemas.alert_recipient import (
  AlertRecipientCreate,
  AlertRecipientRead,
  AlertRecipientUpdate,
  AlertSettingsRead,
)


async def list_recipients(session: AsyncSession) -> list[AlertRecipientRead]:
  rows = (await session.scalars(select(AlertRecipient).order_by(AlertRecipient.email))).all()
  return [AlertRecipientRead.model_validate(row) for row in rows]


async def create_recipient(session: AsyncSession, payload: AlertRecipientCreate) -> AlertRecipientRead:
  recipient = AlertRecipient(email=str(payload.email).lower(), enabled=payload.enabled)
  session.add(recipient)
  await session.commit()
  await session.refresh(recipient)
  return AlertRecipientRead.model_validate(recipient)


async def update_recipient(
  session: AsyncSession, recipient_id: int, payload: AlertRecipientUpdate
) -> AlertRecipientRead | None:
  recipient = await session.get(AlertRecipient, recipient_id)
  if recipient is None:
    return None
  recipient.enabled = payload.enabled
  await session.commit()
  await session.refresh(recipient)
  return AlertRecipientRead.model_validate(recipient)


async def delete_recipient(session: AsyncSession, recipient_id: int) -> bool:
  recipient = await session.get(AlertRecipient, recipient_id)
  if recipient is None:
    return False
  await session.delete(recipient)
  await session.commit()
  return True


async def get_alert_settings(session: AsyncSession) -> AlertSettingsRead:
  settings = get_settings()
  count = await session.scalar(select(func.count()).select_from(AlertRecipient).where(AlertRecipient.enabled.is_(True)))
  return AlertSettingsRead(
    alerts_enabled=settings.alerts_enabled,
    smtp_configured=settings.smtp_configured,
    down_alert_cooldown_minutes=DOWN_ALERT_COOLDOWN_MINUTES,
    recipient_count=count or 0,
  )
