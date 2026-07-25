from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.enums import IncidentStatus
from app.schemas.incident import IncidentDetail, IncidentRead
from app.services import incident_service_async as incident_service

router = APIRouter()

IncidentIdPath = Annotated[int, Path(ge=1, le=2_147_483_647, description="Incident ID")]


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
  db: AsyncSession = Depends(get_db),
  status: Literal["open", "resolved"] | None = Query(default=None),
  monitor_id: Annotated[int | None, Query(ge=1)] = None,
  days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> list[IncidentRead]:
  incident_status = IncidentStatus(status) if status is not None else None
  return await incident_service.list_incidents(
    db,
    status=incident_status,
    monitor_id=monitor_id,
    days=days,
  )


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(incident_id: IncidentIdPath, db: AsyncSession = Depends(get_db)) -> IncidentDetail:
  incident = await incident_service.get_incident(db, incident_id)
  if incident is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
  return incident
