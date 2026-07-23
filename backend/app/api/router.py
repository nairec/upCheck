from fastapi import APIRouter

from app.api.routes import monitors, system

api_router = APIRouter()
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(monitors.router, prefix="/monitors", tags=["monitors"])
