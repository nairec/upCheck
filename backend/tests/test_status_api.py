from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CheckResult, Monitor
from app.models.enums import IncidentStatus, MonitorStatus, MonitorType


async def _seed_status_data(db_session: AsyncSession) -> Monitor:
  monitor = Monitor(
    name="API pública",
    type=MonitorType.HTTP,
    target="https://secret.internal/api",
    interval_seconds=60,
    timeout_seconds=10,
    enabled=True,
    status=MonitorStatus.DOWN,
    response_time_ms=142.5,
    last_checked_at=datetime.now(UTC),
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
  db_session.add_all([monitor, disabled])
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
