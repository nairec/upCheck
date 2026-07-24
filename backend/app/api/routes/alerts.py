from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert_recipient import (
  AlertRecipientCreate,
  AlertRecipientRead,
  AlertRecipientUpdate,
  AlertSettingsRead,
)
from app.services import alert_recipient_service_async as alert_service

router = APIRouter()

RecipientIdPath = Annotated[int, Path(ge=1, le=2_147_483_647, description="Recipient ID")]


@router.get("/settings", response_model=AlertSettingsRead)
async def get_alert_settings(db: AsyncSession = Depends(get_db)) -> AlertSettingsRead:
  return await alert_service.get_alert_settings(db)


@router.get("/recipients", response_model=list[AlertRecipientRead])
async def list_recipients(db: AsyncSession = Depends(get_db)) -> list[AlertRecipientRead]:
  return await alert_service.list_recipients(db)


@router.post("/recipients", response_model=AlertRecipientRead, status_code=status.HTTP_201_CREATED)
async def create_recipient(
  payload: AlertRecipientCreate, db: AsyncSession = Depends(get_db)
) -> AlertRecipientRead:
  return await alert_service.create_recipient(db, payload)


@router.patch("/recipients/{recipient_id}", response_model=AlertRecipientRead)
async def update_recipient(
  recipient_id: RecipientIdPath,
  payload: AlertRecipientUpdate,
  db: AsyncSession = Depends(get_db),
) -> AlertRecipientRead:
  recipient = await alert_service.update_recipient(db, recipient_id, payload)
  if recipient is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
  return recipient


@router.delete("/recipients/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipient(recipient_id: RecipientIdPath, db: AsyncSession = Depends(get_db)) -> None:
  deleted = await alert_service.delete_recipient(db, recipient_id)
  if not deleted:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
