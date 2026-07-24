from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
  "upcheck",
  broker=settings.redis_url,
  backend=settings.redis_url,
  include=["app.worker.tasks"],
)
celery_app.conf.update(
  task_serializer="json",
  accept_content=["json"],
  result_serializer="json",
  timezone="UTC",
  enable_utc=True,
  task_track_started=True,
  beat_schedule={
    "dispatch-due-checks": {
      "task": "app.worker.tasks.dispatch_due_checks",
      "schedule": settings.dispatch_interval_seconds,
    },
    "retention-maintenance": {
      "task": "app.worker.tasks.run_retention_maintenance",
      "schedule": crontab(hour=3, minute=0),
    },
  },
)

