from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
  # Database init and scheduler wiring will live here in later phases.
  yield


def create_app() -> FastAPI:
  settings = get_settings()

  app = FastAPI(
    title=settings.app_name,
    description="Infrastructure monitoring for servers, services, and databases.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
  )

  app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  app.include_router(api_router, prefix=settings.api_prefix)

  @app.get("/health", tags=["system"])
  async def health() -> dict[str, str]:
    return {"status": "ok"}

  return app


app = create_app()
