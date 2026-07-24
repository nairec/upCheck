from sqlalchemy.orm import Session

from app.alerts import DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES
from app.models.alert_settings import ACCOUNT_SETTINGS_ID, AlertSettings


def get_account_alert_settings(session: Session) -> AlertSettings:
  row = session.get(AlertSettings, ACCOUNT_SETTINGS_ID)
  if row is None:
    row = AlertSettings(
      id=ACCOUNT_SETTINGS_ID,
      down_alert_cooldown_minutes=DEFAULT_DOWN_ALERT_COOLDOWN_MINUTES,
      alert_on_down=True,
      alert_on_recovery=False,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
  return row
