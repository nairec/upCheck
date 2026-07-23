from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "upCheck"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://upcheck:upcheck@localhost:5432/upcheck"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    redis_url: str = "redis://localhost:6379/0"
    dispatch_interval_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
