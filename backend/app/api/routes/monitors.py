from fastapi import APIRouter

from app.schemas.monitor import DashboardStats, MonitorRead, MonitorStatus, MonitorSummary

router = APIRouter()

# Placeholder data until the database layer is implemented.
_MOCK_MONITORS: list[MonitorRead] = [
  MonitorRead(
    id=1,
    name="API Gateway",
    type="http",
    target="https://httpbin.org/status/200",
    interval_seconds=60,
    enabled=True,
    status=MonitorStatus.UP,
    response_time_ms=142.5,
  ),
  MonitorRead(
    id=2,
    name="PostgreSQL Primary",
    type="postgres",
    target="postgresql://localhost:5432/upcheck",
    interval_seconds=60,
    enabled=True,
    status=MonitorStatus.UNKNOWN,
  ),
]


@router.get("", response_model=list[MonitorRead])
async def list_monitors() -> list[MonitorRead]:
  return _MOCK_MONITORS


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats() -> DashboardStats:
  summary = MonitorSummary(
    total=len(_MOCK_MONITORS),
    up=sum(1 for monitor in _MOCK_MONITORS if monitor.status == MonitorStatus.UP),
    down=sum(1 for monitor in _MOCK_MONITORS if monitor.status == MonitorStatus.DOWN),
    degraded=sum(1 for monitor in _MOCK_MONITORS if monitor.status == MonitorStatus.DEGRADED),
    unknown=sum(1 for monitor in _MOCK_MONITORS if monitor.status == MonitorStatus.UNKNOWN),
  )
  return DashboardStats(monitors=summary, uptime_24h_percent=99.2)
