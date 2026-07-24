from app.models.enums import MonitorType

SUPPORTED_MONITOR_TYPES = frozenset({MonitorType.HTTP, MonitorType.TCP})


def validate_monitor_target(monitor_type: MonitorType, target: str) -> str:
  normalized = target.strip()
  if not normalized:
    raise ValueError("Target cannot be empty")

  if monitor_type == MonitorType.HTTP:
    if not normalized.startswith(("http://", "https://")):
      raise ValueError("HTTP targets must start with http:// or https://")
    return normalized

  if monitor_type == MonitorType.TCP:
    if ":" not in normalized:
      raise ValueError("TCP targets must use host:port format")
    host, port_str = normalized.rsplit(":", 1)
    if not host.strip():
      raise ValueError("TCP host cannot be empty")
    try:
      port = int(port_str)
    except ValueError as exc:
      raise ValueError("TCP port must be a number") from exc
    if port < 1 or port > 65535:
      raise ValueError("TCP port must be between 1 and 65535")
    return f"{host.strip()}:{port}"

  raise ValueError(f"Monitor type '{monitor_type.value}' is not supported yet")


def ensure_supported_type(monitor_type: MonitorType) -> MonitorType:
  if monitor_type not in SUPPORTED_MONITOR_TYPES:
    supported = ", ".join(t.value for t in sorted(SUPPORTED_MONITOR_TYPES, key=lambda t: t.value))
    raise ValueError(f"Only {supported} monitors are supported")
  return monitor_type
