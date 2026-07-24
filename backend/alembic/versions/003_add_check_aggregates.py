"""add hourly and daily check aggregates

Revision ID: 003
Revises: 002
Create Date: 2026-07-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "check_result_hourly",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("monitor_id", sa.Integer(), nullable=False),
    sa.Column("hour", sa.DateTime(timezone=True), nullable=False),
    sa.Column("total_checks", sa.Integer(), nullable=False),
    sa.Column("up_checks", sa.Integer(), nullable=False),
    sa.Column("avg_latency_ms", sa.Float(), nullable=True),
    sa.Column("min_latency_ms", sa.Float(), nullable=True),
    sa.Column("max_latency_ms", sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("monitor_id", "hour", name="uq_hourly_monitor_hour"),
  )
  op.create_index("ix_check_result_hourly_monitor_id", "check_result_hourly", ["monitor_id"])
  op.create_index("ix_check_result_hourly_hour", "check_result_hourly", ["hour"])

  op.create_table(
    "check_result_daily",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("monitor_id", sa.Integer(), nullable=False),
    sa.Column("day", sa.Date(), nullable=False),
    sa.Column("total_checks", sa.Integer(), nullable=False),
    sa.Column("up_checks", sa.Integer(), nullable=False),
    sa.Column("avg_latency_ms", sa.Float(), nullable=True),
    sa.Column("downtime_minutes", sa.Integer(), nullable=False, server_default="0"),
    sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("monitor_id", "day", name="uq_daily_monitor_day"),
  )
  op.create_index("ix_check_result_daily_monitor_id", "check_result_daily", ["monitor_id"])
  op.create_index("ix_check_result_daily_day", "check_result_daily", ["day"])


def downgrade() -> None:
  op.drop_index("ix_check_result_daily_day", table_name="check_result_daily")
  op.drop_index("ix_check_result_daily_monitor_id", table_name="check_result_daily")
  op.drop_table("check_result_daily")
  op.drop_index("ix_check_result_hourly_hour", table_name="check_result_hourly")
  op.drop_index("ix_check_result_hourly_monitor_id", table_name="check_result_hourly")
  op.drop_table("check_result_hourly")
