"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "monitors",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("name", sa.String(length=120), nullable=False),
    sa.Column("type", sa.Enum("http", "tcp", "ping", "postgres", "redis", name="monitortype", native_enum=False), nullable=False),
    sa.Column("target", sa.String(length=500), nullable=False),
    sa.Column("interval_seconds", sa.Integer(), nullable=False),
    sa.Column("timeout_seconds", sa.Integer(), nullable=False),
    sa.Column("enabled", sa.Boolean(), nullable=False),
    sa.Column("status", sa.Enum("up", "down", "degraded", "unknown", name="monitorstatus", native_enum=False), nullable=False),
    sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("response_time_ms", sa.Float(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.PrimaryKeyConstraint("id"),
  )

  op.create_table(
    "check_results",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("monitor_id", sa.Integer(), nullable=False),
    sa.Column("status", sa.Enum("up", "down", "degraded", "unknown", name="monitorstatus", native_enum=False), nullable=False),
    sa.Column("response_time_ms", sa.Float(), nullable=True),
    sa.Column("status_code", sa.Integer(), nullable=True),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_check_results_checked_at", "check_results", ["checked_at"])
  op.create_index("ix_check_results_monitor_id", "check_results", ["monitor_id"])

  monitors = sa.table(
    "monitors",
    sa.column("name", sa.String),
    sa.column("type", sa.String),
    sa.column("target", sa.String),
    sa.column("interval_seconds", sa.Integer),
    sa.column("timeout_seconds", sa.Integer),
    sa.column("enabled", sa.Boolean),
    sa.column("status", sa.String),
  )
  op.bulk_insert(
    monitors,
    [
      {
        "name": "API Gateway",
        "type": "http",
        "target": "https://httpbin.org/status/200",
        "interval_seconds": 60,
        "timeout_seconds": 10,
        "enabled": True,
        "status": "unknown",
      },
      {
        "name": "Example TCP",
        "type": "tcp",
        "target": "httpbin.org:443",
        "interval_seconds": 120,
        "timeout_seconds": 5,
        "enabled": True,
        "status": "unknown",
      },
    ],
  )


def downgrade() -> None:
  op.drop_index("ix_check_results_monitor_id", table_name="check_results")
  op.drop_index("ix_check_results_checked_at", table_name="check_results")
  op.drop_table("check_results")
  op.drop_table("monitors")
