from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertSettings, CheckResult, Monitor
from app.models.alert_settings import ACCOUNT_SETTINGS_ID
from app.models.enums import MonitorStatus, MonitorType


async def _seed_status_data(db_session: AsyncSession) -> Monitor:
  monitor = Monitor(
    name="API pública",
    type=MonitorType.HTTP,
    target="https://secret.internal/api",
    interval_seconds=60,
    timeout_seconds=10,
    enabled=True,
    public_on_status_page=True,
    status=MonitorStatus.DOWN,
    response_time_ms=142.5,
    last_checked_at=datetime.now(UTC),
  )
  private = Monitor(
    name="API privada",
    type=MonitorType.HTTP,
    target="https://secret.internal/private",
    interval_seconds=60,
    timeout_seconds=10,
    enabled=True,
    public_on_status_page=False,
    status=MonitorStatus.UP,
  )
  disabled = Monitor(
    name="Interno",
    type=MonitorType.TCP,
    target="10.0.0.1:5432",
    interval_seconds=60,
    timeout_seconds=10,
    enabled=False,
    status=MonitorStatus.UP,
  )
  db_session.add_all([monitor, private, disabled])
  await db_session.commit()
  await db_session.refresh(monitor)

  now = datetime.now(UTC)
  db_session.add_all(
    [
      CheckResult(
        monitor_id=monitor.id,
        status=MonitorStatus.UP,
        response_time_ms=100,
        checked_at=now - timedelta(hours=2),
      ),
      CheckResult(
        monitor_id=monitor.id,
        status=MonitorStatus.DOWN,
        response_time_ms=None,
        checked_at=now - timedelta(minutes=5),
      ),
    ]
  )
  await db_session.commit()
  return monitor


@pytest.mark.asyncio
async def test_public_status_empty(client: AsyncClient) -> None:
  response = await client.get("/api/v1/status")
  assert response.status_code == 200
  body = response.json()
  assert body["status"] == "operational"
  assert body["monitors"]["total"] == 0
  assert body["services"] == []
  assert body["open_incidents"] == []


@pytest.mark.asyncio
async def test_public_status_omits_sensitive_fields(
  client: AsyncClient, db_session: AsyncSession
) -> None:
  await _seed_status_data(db_session)

  response = await client.get("/api/v1/status")
  assert response.status_code == 200
  body = response.json()

  assert body["status"] == "major_outage"
  assert body["monitors"] == {
    "total": 1,
    "up": 0,
    "down": 1,
    "degraded": 0,
    "unknown": 0,
  }
  assert len(body["services"]) == 1
  service = body["services"][0]
  assert service["name"] == "API pública"
  assert service["status"] == "down"
  assert service["uptime_24h_percent"] == 50.0
  assert "target" not in service

  payload = response.text
  assert "secret.internal" not in payload


@pytest.mark.asyncio
async def test_public_status_excludes_private_monitors(
  client: AsyncClient, db_session: AsyncSession
) -> None:
  await _seed_status_data(db_session)

  response = await client.get("/api/v1/status")
  assert response.status_code == 200
  names = [service["name"] for service in response.json()["services"]]
  assert "API privada" not in names


@pytest.mark.asyncio
async def test_public_status_returns_404_when_page_private(
  client: AsyncClient, db_session: AsyncSession
) -> None:
  settings = AlertSettings(
    id=ACCOUNT_SETTINGS_ID,
    down_alert_cooldown_minutes=15,
    alert_on_down=True,
    alert_on_recovery=False,
    status_page_public=False,
  )
  db_session.add(settings)
  await db_session.commit()

  response = await client.get("/api/v1/status")
  assert response.status_code == 404
