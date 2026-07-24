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
    run_migrations_on_startup: bool = True

    # Public dashboard URL for links in alert emails (optional).
    app_public_url: str | None = None

    # Email alerts — disabled until ALERTS_ENABLED=true and SMTP_HOST are set.
    alerts_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "upCheck <alerts@localhost>"
    smtp_use_tls: bool = True

    @property
    def smtp_configured(self) -> bool:
      return bool(self.smtp_host and self.smtp_host.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
