from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import (
  DEFAULT_PAGE_LIMIT,
  MAX_PAGE_LIMIT,
  MAX_PAGE_OFFSET,
)
from app.core.database import get_db
from app.history import HistoryGranularity, max_days_for
from app.schemas.check_result import CheckResultPage
from app.schemas.history import MonitorHistoryResponse
from app.schemas.monitor import DashboardStats, MonitorCreate, MonitorListItem, MonitorRead, MonitorUpdate
from app.services import monitor_service_async as monitor_service

router = APIRouter()

MonitorIdPath = Annotated[int, Path(ge=1, le=2_147_483_647, description="Monitor ID")]
PageLimit = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT, description="Results per page")]
PageOffset = Annotated[int, Query(ge=0, le=MAX_PAGE_OFFSET, description="Results to skip")]
HistoryDays = Annotated[
  int,
  Query(ge=1, le=max_days_for(HistoryGranularity.DAILY), description="Days of history to return"),
]
HistoryGranularityQuery = Annotated[
  HistoryGranularity,
  Query(description="Data tier: auto picks raw/hourly/daily by window size"),
]


@router.get("", response_model=list[MonitorListItem])
async def list_monitors(db: AsyncSession = Depends(get_db)) -> list[MonitorListItem]:
  return await monitor_service.list_monitors(db)


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
  payload: MonitorCreate, db: AsyncSession = Depends(get_db)
) -> MonitorRead:
  return await monitor_service.create_monitor(db, payload)


@router.patch("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
  monitor_id: MonitorIdPath,
  payload: MonitorUpdate,
  db: AsyncSession = Depends(get_db),
) -> MonitorRead:
  monitor = await monitor_service.update_monitor(db, monitor_id, payload)
  if monitor is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
  return monitor


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(monitor_id: MonitorIdPath, db: AsyncSession = Depends(get_db)) -> None:
  deleted = await monitor_service.delete_monitor(db, monitor_id)
  if not deleted:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
  return await monitor_service.dashboard_stats(db)


@router.get("/{monitor_id}", response_model=MonitorRead)
async def get_monitor(
  monitor_id: MonitorIdPath, db: AsyncSession = Depends(get_db)
) -> MonitorRead:
  monitor = await monitor_service.get_monitor(db, monitor_id)
  if monitor is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
  return MonitorRead.model_validate(monitor)


@router.get("/{monitor_id}/results", response_model=CheckResultPage)
async def list_monitor_results(
  monitor_id: MonitorIdPath,
  db: AsyncSession = Depends(get_db),
  limit: PageLimit = DEFAULT_PAGE_LIMIT,
  offset: PageOffset = 0,
) -> CheckResultPage:
  page = await monitor_service.list_check_results(db, monitor_id, limit=limit, offset=offset)
  if page is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
  return page


@router.get("/{monitor_id}/history", response_model=MonitorHistoryResponse)
async def get_monitor_history(
  monitor_id: MonitorIdPath,
  db: AsyncSession = Depends(get_db),
  days: HistoryDays = 7,
  granularity: HistoryGranularityQuery = HistoryGranularity.AUTO,
) -> MonitorHistoryResponse:
  history = await monitor_service.get_monitor_history(
    db, monitor_id, days=days, granularity=granularity
  )
  if history is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
  return history
