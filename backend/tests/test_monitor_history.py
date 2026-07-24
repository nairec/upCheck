from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CheckResult, MonitorStatus


async def _create_monitor(client: AsyncClient, name: str = "Test") -> dict:
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


async def _seed_results(
  db_session: AsyncSession,
  monitor_id: int,
  count: int,
  *,
  status: MonitorStatus = MonitorStatus.UP,
) -> None:
  for index in range(count):
    db_session.add(
      CheckResult(
        monitor_id=monitor_id,
        status=status,
        response_time_ms=100.0 + index,
        status_code=200,
        checked_at=datetime(2026, 1, 1, 12, index % 60, tzinfo=UTC),
      )
    )
  await db_session.commit()


@pytest.mark.asyncio
async def test_get_monitor_success(client: AsyncClient) -> None:
  created = await _create_monitor(client)
  response = await client.get(f"/api/v1/monitors/{created['id']}")
  assert response.status_code == 200
  assert response.json()["name"] == "Test"


@pytest.mark.asyncio
async def test_get_monitor_not_found(client: AsyncClient) -> None:
  response = await client.get("/api/v1/monitors/99999")
  assert response.status_code == 404
  assert response.json()["detail"] == "Monitor not found"


@pytest.mark.asyncio
async def test_get_monitor_invalid_id(client: AsyncClient) -> None:
  response = await client.get("/api/v1/monitors/0")
  assert response.status_code == 422

  response = await client.get("/api/v1/monitors/not-a-number")
  assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_results_empty(client: AsyncClient, db_session: AsyncSession) -> None:
  created = await _create_monitor(client)
  response = await client.get(f"/api/v1/monitors/{created['id']}/results")
  assert response.status_code == 200
  body = response.json()
  assert body["items"] == []
  assert body["total"] == 0
  assert body["has_more"] is False


@pytest.mark.asyncio
async def test_list_results_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
  created = await _create_monitor(client)
  await _seed_results(db_session, created["id"], 5)

  page1 = await client.get(f"/api/v1/monitors/{created['id']}/results?limit=2&offset=0")
  assert page1.status_code == 200
  body1 = page1.json()
  assert len(body1["items"]) == 2
  assert body1["total"] == 5
  assert body1["has_more"] is True

  page2 = await client.get(f"/api/v1/monitors/{created['id']}/results?limit=2&offset=2")
  body2 = page2.json()
  assert len(body2["items"]) == 2
  assert body2["has_more"] is True

  page3 = await client.get(f"/api/v1/monitors/{created['id']}/results?limit=2&offset=4")
  body3 = page3.json()
  assert len(body3["items"]) == 1
  assert body3["has_more"] is False

  ids_page1 = {item["id"] for item in body1["items"]}
  ids_page2 = {item["id"] for item in body2["items"]}
  assert ids_page1.isdisjoint(ids_page2)


@pytest.mark.asyncio
async def test_list_results_not_found(client: AsyncClient) -> None:
  response = await client.get("/api/v1/monitors/424242/results")
  assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_results_invalid_pagination(client: AsyncClient) -> None:
  created = await _create_monitor(client)
  base = f"/api/v1/monitors/{created['id']}/results"

  assert (await client.get(f"{base}?limit=0")).status_code == 422
  assert (await client.get(f"{base}?limit=101")).status_code == 422
  assert (await client.get(f"{base}?offset=-1")).status_code == 422
  assert (await client.get(f"{base}?offset=5001")).status_code == 422


@pytest.mark.asyncio
async def test_results_scoped_to_monitor(client: AsyncClient, db_session: AsyncSession) -> None:
  first = await _create_monitor(client, "First")
  second = await _create_monitor(client, "Second")
  await _seed_results(db_session, first["id"], 3)
  await _seed_results(db_session, second["id"], 1, status=MonitorStatus.DOWN)

  response = await client.get(f"/api/v1/monitors/{first['id']}/results")
  body = response.json()
  assert body["total"] == 3
  assert all(item["monitor_id"] == first["id"] for item in body["items"])


@pytest.mark.asyncio
async def test_error_message_truncated(client: AsyncClient, db_session: AsyncSession) -> None:
  created = await _create_monitor(client)
  long_message = "x" * 600
  db_session.add(
    CheckResult(
      monitor_id=created["id"],
      status=MonitorStatus.DOWN,
      error_message=long_message,
      checked_at=datetime.now(UTC),
    )
  )
  await db_session.commit()

  response = await client.get(f"/api/v1/monitors/{created['id']}/results")
  message = response.json()["items"][0]["error_message"]
  assert message is not None
  assert len(message) <= 500
  assert message.endswith("…")


@pytest.mark.asyncio
async def test_list_monitors_includes_recent_checks(
  client: AsyncClient, db_session: AsyncSession
) -> None:
  created = await _create_monitor(client)
  await _seed_results(db_session, created["id"], 3)

  response = await client.get("/api/v1/monitors")
  assert response.status_code == 200
  monitor = response.json()[0]
  assert "recent_checks" in monitor
  assert len(monitor["recent_checks"]) == 3
  assert monitor["recent_checks"][0]["status"] == "up"
