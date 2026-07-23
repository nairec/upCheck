from app.checks.runner import run_tcp_check
from app.models.enums import MonitorStatus


def test_tcp_check_invalid_port_returns_down() -> None:
  outcome = run_tcp_check("example.com:abc", timeout_seconds=5)

  assert outcome.status == MonitorStatus.DOWN
  assert outcome.error_message == "Invalid port in target 'example.com:abc'"
