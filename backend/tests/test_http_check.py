import httpx
import respx

from app.checks.http import run_http_check
from app.models.enums import MonitorStatus


@respx.mock
def test_http_check_success() -> None:
  respx.get("https://example.com/health").mock(return_value=httpx.Response(200))

  outcome = run_http_check("https://example.com/health", timeout_seconds=5)

  assert outcome.status == MonitorStatus.UP
  assert outcome.status_code == 200
  assert outcome.response_time_ms is not None


@respx.mock
def test_http_check_server_error() -> None:
  respx.get("https://example.com/health").mock(return_value=httpx.Response(503))

  outcome = run_http_check("https://example.com/health", timeout_seconds=5)

  assert outcome.status == MonitorStatus.DOWN
  assert outcome.status_code == 503


@respx.mock
def test_http_check_connection_error() -> None:
  respx.get("https://example.com/health").mock(side_effect=httpx.ConnectError("connection refused"))

  outcome = run_http_check("https://example.com/health", timeout_seconds=5)

  assert outcome.status == MonitorStatus.DOWN
  assert outcome.error_message is not None
