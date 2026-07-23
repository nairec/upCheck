from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# Celery workers run synchronously; psycopg2 replaces asyncpg in the URL.
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

sync_engine = create_engine(sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def get_sync_session() -> Generator[Session, None, None]:
  session = SyncSessionLocal()
  try:
    yield session
  finally:
    session.close()
