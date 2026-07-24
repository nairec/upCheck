from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings


def _run_migrations() -> None:
  settings = get_settings()
  backend_dir = Path(__file__).resolve().parent.parent
  alembic_cfg = Config(str(backend_dir / "alembic.ini"))
  sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
  alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
  command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
  settings = get_settings()
  if settings.run_migrations_on_startup:
    _run_migrations()
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
