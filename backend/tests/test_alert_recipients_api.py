import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_alert_settings_defaults(client: AsyncClient) -> None:
  response = await client.get("/api/v1/alerts/settings")
  assert response.status_code == 200
  body = response.json()
  assert body["alerts_enabled"] is False
  assert body["smtp_configured"] is False
  assert body["down_alert_cooldown_minutes"] == 15
  assert body["recipient_count"] == 0


@pytest.mark.asyncio
async def test_create_and_list_recipients(client: AsyncClient) -> None:
  create = await client.post("/api/v1/alerts/recipients", json={"email": "ops@example.com"})
  assert create.status_code == 201
  assert create.json()["email"] == "ops@example.com"

  listing = await client.get("/api/v1/alerts/recipients")
  assert listing.status_code == 200
  assert len(listing.json()) == 1

  settings = await client.get("/api/v1/alerts/settings")
  assert settings.json()["recipient_count"] == 1


@pytest.mark.asyncio
async def test_disable_and_delete_recipient(client: AsyncClient) -> None:
  created = await client.post("/api/v1/alerts/recipients", json={"email": "oncall@example.com"})
  recipient_id = created.json()["id"]

  patched = await client.patch(
    f"/api/v1/alerts/recipients/{recipient_id}",
    json={"enabled": False},
  )
  assert patched.status_code == 200
  assert patched.json()["enabled"] is False

  deleted = await client.delete(f"/api/v1/alerts/recipients/{recipient_id}")
  assert deleted.status_code == 204

  listing = await client.get("/api/v1/alerts/recipients")
  assert listing.json() == []


@pytest.mark.asyncio
async def test_create_recipient_invalid_email(client: AsyncClient) -> None:
  response = await client.post("/api/v1/alerts/recipients", json={"email": "not-an-email"})
  assert response.status_code == 422
