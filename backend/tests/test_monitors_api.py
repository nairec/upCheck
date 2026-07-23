import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_monitors_empty(client: AsyncClient) -> None:
  response = await client.get("/api/v1/monitors")
  assert response.status_code == 200
  assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_list_monitor(client: AsyncClient) -> None:
  payload = {
    "name": "Test API",
    "type": "http",
    "target": "https://httpbin.org/status/200",
    "interval_seconds": 60,
    "enabled": True,
  }

  create_response = await client.post("/api/v1/monitors", json=payload)
  assert create_response.status_code == 201
  created = create_response.json()
  assert created["name"] == "Test API"
  assert created["status"] == "unknown"

  list_response = await client.get("/api/v1/monitors")
  assert list_response.status_code == 200
  monitors = list_response.json()
  assert len(monitors) == 1
  assert monitors[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_create_monitor_persists_timeout_seconds(client: AsyncClient) -> None:
  payload = {
    "name": "Slow endpoint",
    "type": "http",
    "target": "https://example.com",
    "interval_seconds": 60,
    "timeout_seconds": 25,
    "enabled": True,
  }

  response = await client.post("/api/v1/monitors", json=payload)
  assert response.status_code == 201
  created = response.json()
  assert created["timeout_seconds"] == 25


@pytest.mark.asyncio
async def test_dashboard_stats(client: AsyncClient) -> None:
  await client.post(
    "/api/v1/monitors",
    json={
      "name": "Stats Monitor",
      "type": "http",
      "target": "https://example.com",
      "interval_seconds": 60,
      "enabled": True,
    },
  )

  response = await client.get("/api/v1/monitors/stats")
  assert response.status_code == 200
  stats = response.json()
  assert stats["monitors"]["total"] == 1
  assert stats["monitors"]["unknown"] == 1
