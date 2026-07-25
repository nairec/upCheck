from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Incident, Monitor, MonitorStatus, MonitorType
from app.models.enums import IncidentStatus


async def _seed_incident(db_session: AsyncSession) -> Incident:
  monitor = Monitor(
    name="API",
    type=MonitorType.HTTP,
    target="https://example.com",
    interval_seconds=60,
    timeout_seconds=10,
    enabled=True,
    status=MonitorStatus.DOWN,
  )
  db_session.add(monitor)
  await db_session.commit()
  await db_session.refresh(monitor)

  incident = Incident(
    monitor_id=monitor.id,
    status=IncidentStatus.OPEN,
    started_at=datetime(2026, 7, 25, 8, 0, tzinfo=UTC),
    error_message="HTTP 503",
    failed_check_count=3,
  )
  db_session.add(incident)
  await db_session.commit()
  await db_session.refresh(incident)
  return incident


@pytest.mark.asyncio
async def test_list_incidents_empty(client: AsyncClient) -> None:
  response = await client.get("/api/v1/incidents")
  assert response.status_code == 200
  assert response.json() == []


@pytest.mark.asyncio
async def test_list_and_get_incident(client: AsyncClient, db_session: AsyncSession) -> None:
  incident = await _seed_incident(db_session)

  list_response = await client.get("/api/v1/incidents")
  assert list_response.status_code == 200
  items = list_response.json()
  assert len(items) == 1
  assert items[0]["monitor_name"] == "API"
  assert items[0]["status"] == "open"
  assert items[0]["failed_check_count"] == 3

  detail_response = await client.get(f"/api/v1/incidents/{incident.id}")
  assert detail_response.status_code == 200
  detail = detail_response.json()
  assert detail["id"] == incident.id
  assert detail["checks"] == []


@pytest.mark.asyncio
async def test_filter_incidents_by_status(client: AsyncClient, db_session: AsyncSession) -> None:
  await _seed_incident(db_session)

  open_response = await client.get("/api/v1/incidents", params={"status": "open"})
  assert open_response.status_code == 200
  assert len(open_response.json()) == 1

  resolved_response = await client.get("/api/v1/incidents", params={"status": "resolved"})
  assert resolved_response.status_code == 200
  assert resolved_response.json() == []


@pytest.mark.asyncio
async def test_get_incident_not_found(client: AsyncClient) -> None:
  response = await client.get("/api/v1/incidents/999")
  assert response.status_code == 404
