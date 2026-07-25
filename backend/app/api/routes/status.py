from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.status import PublicStatusResponse
from app.services import status_service_async as status_service

router = APIRouter()


@router.get("", response_model=PublicStatusResponse)
async def public_status(db: AsyncSession = Depends(get_db)) -> PublicStatusResponse:
  """Public status page data — no sensitive fields (targets, credentials)."""
  return await status_service.get_public_status(db)
