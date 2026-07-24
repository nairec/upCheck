import logging
from dataclasses import asdict

from app.core.sync_database import SyncSessionLocal
from app.services import monitor_service, retention_service
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.dispatch_due_checks")
def dispatch_due_checks() -> int:
  """Find enabled monitors past their interval and enqueue individual check tasks."""
  with SyncSessionLocal() as session:
    due_monitor_ids = [monitor.id for monitor in monitor_service.get_due_monitors(session)]

  for monitor_id in due_monitor_ids:
    run_monitor_check.delay(monitor_id)

  logger.info("Dispatched %s monitor checks", len(due_monitor_ids))
  return len(due_monitor_ids)


@celery_app.task(name="app.worker.tasks.run_monitor_check", bind=True, max_retries=2)
def run_monitor_check(self, monitor_id: int) -> str:
  with SyncSessionLocal() as session:
    monitor = monitor_service.claim_monitor_for_check(session, monitor_id)
    if monitor is None:
      existing = monitor_service.get_monitor(session, monitor_id)
      if existing is None:
        return f"monitor {monitor_id} not found"
      if not existing.enabled:
        return f"monitor {monitor_id} disabled"
      return f"monitor {monitor_id} skipped (not due or already claimed)"

    claimed_lease = monitor.lease_until
    try:
      result = monitor_service.execute_check(session, monitor, expected_lease_until=claimed_lease)
      if result is None:
        return f"monitor {monitor_id} skipped (lease lost)"
      return f"monitor {monitor_id} -> {result.status.value}"
    except Exception:
      session.rollback()
      if claimed_lease is not None:
        monitor_service.release_monitor_lease(
          session, monitor_id, expected_lease_until=claimed_lease
        )
      raise


@celery_app.task(name="app.worker.tasks.run_retention_maintenance")
def run_retention_maintenance() -> dict[str, int]:
  """Roll up expiring tiers and purge old data. Idempotent — safe to retry."""
  with SyncSessionLocal() as session:
    stats = retention_service.run_retention_maintenance(session)
  return asdict(stats)


@celery_app.task(name="app.worker.tasks.send_down_alert_email", bind=True, max_retries=2)
def send_down_alert_email(self, monitor_id: int, check_result_id: int) -> str:
  with SyncSessionLocal() as session:
    from app.services import alert_service

    sent = alert_service.deliver_down_alert(session, monitor_id, check_result_id)
  if sent:
    return f"down alert sent for monitor {monitor_id}"
  return f"down alert skipped for monitor {monitor_id}"
