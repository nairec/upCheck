from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CheckResult, CheckResultDaily, CheckResultHourly, MonitorStatus


async def _create_monitor(client: AsyncClient, name: str = "History") -> dict:
  response = await client.post(
    "/api/v1/monitors",
    json={
      "name": name,
      "type": "http",
      "target": "https://example.com",
      "interval_seconds": 60,
      "enabled": True,
    },
  )
  assert response.status_code == 201
  return response.json()


@pytest.mark.asyncio
async def test_history_raw_window(client: AsyncClient, db_session: AsyncSession) -> None:
  created = await _create_monitor(client)
  now = datetime.now(UTC)
  db_session.add(
    CheckResult(
      monitor_id=created["id"],
      status=MonitorStatus.UP,
      response_time_ms=42.0,
      checked_at=now - timedelta(hours=2),
    )
  )
  db_session.add(
    CheckResult(
      monitor_id=created["id"],
      status=MonitorStatus.DOWN,
      response_time_ms=None,
      checked_at=now - timedelta(days=10),
    )
  )
  await db_session.commit()

  response = await client.get(f"/api/v1/monitors/{created['id']}/history?days=1&granularity=raw")
  assert response.status_code == 200
  body = response.json()
  assert body["granularity"] == "raw"
  assert body["total"] == 1
  assert len(body["points"]) == 1
  assert body["points"][0]["status"] == "up"


@pytest.mark.asyncio
async def test_history_hourly_buckets(client: AsyncClient, db_session: AsyncSession) -> None:
  created = await _create_monitor(client)
  hour = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(days=2)
  db_session.add(
    CheckResultHourly(
      monitor_id=created["id"],
      hour=hour,
      total_checks=10,
      up_checks=8,
      avg_latency_ms=90.0,
      min_latency_ms=80.0,
      max_latency_ms=100.0,
    )
  )
  await db_session.commit()

  response = await client.get(
    f"/api/v1/monitors/{created['id']}/history?days=30&granularity=hourly"
  )
  assert response.status_code == 200
  body = response.json()
  assert body["granularity"] == "hourly"
  assert body["total"] == 1
  assert body["points"][0]["uptime_percent"] == 80.0
  assert body["points"][0]["avg_latency_ms"] == 90.0


@pytest.mark.asyncio
async def test_history_auto_picks_hourly_for_long_window(
  client: AsyncClient, db_session: AsyncSession
) -> None:
  created = await _create_monitor(client)
  day = (datetime.now(UTC) - timedelta(days=5)).date()
  db_session.add(
    CheckResultDaily(
      monitor_id=created["id"],
      day=day,
      total_checks=24,
      up_checks=24,
      avg_latency_ms=55.0,
      downtime_minutes=0,
    )
  )
  await db_session.commit()

  response = await client.get(f"/api/v1/monitors/{created['id']}/history?days=90")
  assert response.status_code == 200
  assert response.json()["granularity"] == "hourly"


@pytest.mark.asyncio
async def test_history_not_found(client: AsyncClient) -> None:
  response = await client.get("/api/v1/monitors/99999/history?days=7")
  assert response.status_code == 404


@pytest.mark.asyncio
async def test_history_invalid_days(client: AsyncClient) -> None:
  created = await _create_monitor(client)
  response = await client.get(f"/api/v1/monitors/{created['id']}/history?days=0")
  assert response.status_code == 422

  response = await client.get(f"/api/v1/monitors/{created['id']}/history?days=9999")
  assert response.status_code == 422
