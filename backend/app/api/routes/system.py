from fastapi import APIRouter

router = APIRouter()


@router.get("/info")
async def system_info() -> dict[str, str]:
  return {
    "name": "upCheck",
    "version": "0.1.0",
    "phase": "scaffold",
  }
