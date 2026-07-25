from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.status import PublicStatusResponse
from app.services import alert_recipient_service_async as alert_settings_service
from app.services import status_service_async as status_service

router = APIRouter()


@router.get("", response_model=PublicStatusResponse)
async def public_status(db: AsyncSession = Depends(get_db)) -> PublicStatusResponse:
  """Public status page data — no sensitive fields (targets, credentials)."""
  if not await alert_settings_service.is_status_page_public(db):
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="La página de estado no está disponible públicamente",
    )
  return await status_service.get_public_status(db)
