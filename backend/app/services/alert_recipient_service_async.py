from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts import DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES
from app.config import get_settings
from app.models import AlertRecipient, AlertSettings
from app.models.alert_settings import ACCOUNT_SETTINGS_ID
from app.schemas.alert_recipient import (
  AlertRecipientCreate,
  AlertRecipientRead,
  AlertRecipientUpdate,
  AlertSettingsRead,
  AlertSettingsUpdate,
)


async def _get_or_create_settings(session: AsyncSession) -> AlertSettings:
  row = await session.get(AlertSettings, ACCOUNT_SETTINGS_ID)
  if row is None:
    row = AlertSettings(
      id=ACCOUNT_SETTINGS_ID,
      down_alert_cooldown_minutes=DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES,
      alert_on_down=True,
      alert_on_recovery=False,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
  return row


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
  env = get_settings()
  account = await _get_or_create_settings(session)
  count = await session.scalar(
    select(func.count()).select_from(AlertRecipient).where(AlertRecipient.enabled.is_(True))
  )
  return AlertSettingsRead(
    alerts_enabled=env.alerts_enabled,
    smtp_configured=env.smtp_configured,
    down_alert_cooldown_minutes=account.down_alert_cooldown_minutes,
    alert_on_down=account.alert_on_down,
    alert_on_recovery=account.alert_on_recovery,
    recipient_count=count or 0,
  )


async def update_alert_settings(
  session: AsyncSession, payload: AlertSettingsUpdate
) -> AlertSettingsRead:
  account = await _get_or_create_settings(session)
  updates = payload.model_dump(exclude_unset=True)
  for field, value in updates.items():
    setattr(account, field, value)
  await session.commit()
  await session.refresh(account)
  return await get_alert_settings(session)
