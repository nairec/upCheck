"""add incidents table

Revision ID: 008
Revises: 007
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "incidents",
    sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
    sa.Column("monitor_id", sa.Integer(), nullable=False),
    sa.Column(
      "status",
      sa.Enum("open", "resolved", name="incidentstatus", native_enum=False),
      nullable=False,
    ),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column("failed_check_count", sa.Integer(), nullable=False, server_default="1"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_incidents_monitor_id", "incidents", ["monitor_id"])
  op.create_index("ix_incidents_started_at", "incidents", ["started_at"])


def downgrade() -> None:
  op.drop_index("ix_incidents_started_at", table_name="incidents")
  op.drop_index("ix_incidents_monitor_id", table_name="incidents")
  op.drop_table("incidents")
