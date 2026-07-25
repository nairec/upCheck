import enum


class MonitorType(str, enum.Enum):
  HTTP = "http"
  TCP = "tcp"
  PING = "ping"
  POSTGRES = "postgres"
  REDIS = "redis"


class MonitorStatus(str, enum.Enum):
  UP = "up"
  DOWN = "down"
  DEGRADED = "degraded"
  UNKNOWN = "unknown"


class IncidentStatus(str, enum.Enum):
  OPEN = "open"
  RESOLVED = "resolved"
