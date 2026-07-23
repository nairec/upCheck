import time

import httpx

from app.checks.base import CheckOutcome
from app.models.enums import MonitorStatus


def run_http_check(target: str, timeout_seconds: int) -> CheckOutcome:
  started = time.perf_counter()
  try:
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
      response = client.get(target)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if response.status_code < 400:
      return CheckOutcome(
        status=MonitorStatus.UP,
        response_time_ms=elapsed_ms,
        status_code=response.status_code,
      )

    return CheckOutcome(
      status=MonitorStatus.DOWN,
      response_time_ms=elapsed_ms,
      status_code=response.status_code,
      error_message=f"HTTP {response.status_code}",
    )
  except httpx.TimeoutException:
    return CheckOutcome(
      status=MonitorStatus.DOWN,
      error_message=f"Timeout after {timeout_seconds}s",
    )
  except httpx.RequestError as exc:
    return CheckOutcome(
      status=MonitorStatus.DOWN,
      error_message=str(exc),
    )
