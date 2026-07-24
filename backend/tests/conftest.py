import os

os.environ.setdefault("RUN_MIGRATIONS_ON_STARTUP", "false")

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
  engine = create_async_engine(TEST_DATABASE_URL)
  async with engine.begin() as connection:
    await connection.run_sync(Base.metadata.create_all)

  session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

  async with session_factory() as session:
    yield session

  await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
  async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    yield db_session

  app.dependency_overrides[get_db] = override_get_db

  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as http_client:
    yield http_client

  app.dependency_overrides.clear()
