"""add singleton alert_settings for account preferences

Revision ID: 006
Revises: 005
Create Date: 2026-07-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "alert_settings",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("down_alert_cooldown_minutes", sa.Integer(), nullable=False, server_default="15"),
    sa.Column("alert_on_down", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    sa.Column("alert_on_recovery", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.PrimaryKeyConstraint("id"),
  )
  op.execute(
    """
    INSERT INTO alert_settings (id, down_alert_cooldown_minutes, alert_on_down, alert_on_recovery)
    VALUES (1, 15, true, false)
    """
  )


def downgrade() -> None:
  op.drop_table("alert_settings")
