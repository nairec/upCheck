import logging

from app.core.sync_database import SyncSessionLocal
from app.services import monitor_service
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.dispatch_due_checks")
def dispatch_due_checks() -> int:
  """Find enabled monitors past their interval and enqueue individual check tasks."""
  with SyncSessionLocal() as session:
    due_monitors = monitor_service.get_due_monitors(session)

  for monitor in due_monitors:
    run_monitor_check.delay(monitor.id)

  logger.info("Dispatched %s monitor checks", len(due_monitors))
  return len(due_monitors)


@celery_app.task(name="app.worker.tasks.run_monitor_check", bind=True, max_retries=2)
def run_monitor_check(self, monitor_id: int) -> str:
  with SyncSessionLocal() as session:
    monitor = monitor_service.get_monitor(session, monitor_id)
    if monitor is None:
      return f"monitor {monitor_id} not found"
    if not monitor.enabled:
      return f"monitor {monitor_id} disabled"

    result = monitor_service.execute_check(session, monitor)
    return f"monitor {monitor_id} -> {result.status.value}"
