import socket
import time

from app.checks.base import CheckOutcome
from app.models.enums import MonitorStatus, MonitorType
from app.checks.http import run_http_check


def _parse_host_port(target: str, default_port: int) -> tuple[str, int] | None:
  if ":" in target:
    host, port_str = target.rsplit(":", 1)
    try:
      port = int(port_str)
    except ValueError:
      return None
    return host, port
  return target, default_port


def run_tcp_check(target: str, timeout_seconds: int) -> CheckOutcome:
  parsed = _parse_host_port(target, 80)
  if parsed is None:
    return CheckOutcome(
      status=MonitorStatus.DOWN,
      error_message=f"Invalid port in target '{target}'",
    )
  host, port = parsed
  started = time.perf_counter()
  try:
    with socket.create_connection((host, port), timeout=timeout_seconds):
      elapsed_ms = (time.perf_counter() - started) * 1000
      return CheckOutcome(status=MonitorStatus.UP, response_time_ms=elapsed_ms)
  except OSError as exc:
    return CheckOutcome(status=MonitorStatus.DOWN, error_message=str(exc))


def run_check(monitor_type: MonitorType, target: str, timeout_seconds: int) -> CheckOutcome:
  if monitor_type == MonitorType.HTTP:
    return run_http_check(target, timeout_seconds)
  if monitor_type == MonitorType.TCP:
    return run_tcp_check(target, timeout_seconds)

  return CheckOutcome(
    status=MonitorStatus.UNKNOWN,
    error_message=f"Check type '{monitor_type.value}' not implemented yet",
  )
