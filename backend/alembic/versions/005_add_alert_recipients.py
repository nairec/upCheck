"""add alert recipients and monitor down alert timestamp

Revision ID: 005
Revises: 004
Create Date: 2026-07-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "alert_recipients",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("email", sa.String(length=320), nullable=False),
    sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("email", name="uq_alert_recipients_email"),
  )
  op.create_index("ix_alert_recipients_email", "alert_recipients", ["email"])

  op.add_column("monitors", sa.Column("last_down_alert_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
  op.drop_column("monitors", "last_down_alert_at")
  op.drop_index("ix_alert_recipients_email", table_name="alert_recipients")
  op.drop_table("alert_recipients")
