"""History query helpers — granularity resolution and bounds."""

from enum import Enum

from app.retention import (
  DAILY_RETENTION_DAYS,
  HOURLY_RETENTION_DAYS,
  RAW_RETENTION_DAYS,
)

MAX_HISTORY_RAW_POINTS = 500


class HistoryGranularity(str, Enum):
  AUTO = "auto"
  RAW = "raw"
  HOURLY = "hourly"
  DAILY = "daily"


def resolve_granularity(days: int, requested: HistoryGranularity) -> HistoryGranularity:
  """Pick the best tier for a time window (auto favors fewer points for long ranges)."""
  if requested != HistoryGranularity.AUTO:
    return requested
  if days <= 7:
    return HistoryGranularity.RAW
  if days <= HOURLY_RETENTION_DAYS:
    return HistoryGranularity.HOURLY
  return HistoryGranularity.DAILY


def max_days_for(granularity: HistoryGranularity) -> int:
  if granularity == HistoryGranularity.RAW:
    return RAW_RETENTION_DAYS
  if granularity == HistoryGranularity.HOURLY:
    return HOURLY_RETENTION_DAYS
  return DAILY_RETENTION_DAYS
