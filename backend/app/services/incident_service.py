from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CheckResult, Incident, MonitorStatus
from app.models.enums import IncidentStatus


def _get_open_incident(session: Session, monitor_id: int) -> Incident | None:
  return session.scalars(
    select(Incident).where(
      Incident.monitor_id == monitor_id,
      Incident.status == IncidentStatus.OPEN,
    )
  ).first()


def handle_status_change(
  session: Session,
  *,
  monitor_id: int,
  previous_status: MonitorStatus,
  new_status: MonitorStatus,
  error_message: str | None,
  now: datetime,
) -> None:
  """Open, update or resolve an incident from a monitor status transition."""
  if new_status == MonitorStatus.DOWN:
    if previous_status == MonitorStatus.DOWN:
      incident = _get_open_incident(session, monitor_id)
      if incident is None:
        return
      incident.failed_check_count += 1
      if error_message:
        incident.error_message = error_message
    else:
      session.add(
        Incident(
          monitor_id=monitor_id,
          status=IncidentStatus.OPEN,
          started_at=now,
          error_message=error_message,
          failed_check_count=1,
        )
      )
    session.commit()
    return

  if previous_status == MonitorStatus.DOWN and new_status == MonitorStatus.UP:
    incident = _get_open_incident(session, monitor_id)
    if incident is None:
      return
    incident.status = IncidentStatus.RESOLVED
    incident.ended_at = now
    session.commit()
