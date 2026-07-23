from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.monitor import DashboardStats, MonitorCreate, MonitorRead
from app.services import monitor_service_async as monitor_service

router = APIRouter()


@router.get("", response_model=list[MonitorRead])
async def list_monitors(db: AsyncSession = Depends(get_db)) -> list[MonitorRead]:
  return await monitor_service.list_monitors(db)


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
  payload: MonitorCreate, db: AsyncSession = Depends(get_db)
) -> MonitorRead:
  return await monitor_service.create_monitor(db, payload)


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
  return await monitor_service.dashboard_stats(db)
