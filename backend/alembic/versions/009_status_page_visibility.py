"""add status page visibility settings

Revision ID: 009
Revises: 008
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.add_column(
    "monitors",
    sa.Column(
      "public_on_status_page",
      sa.Boolean(),
      nullable=False,
      server_default=sa.text("true"),
    ),
  )
  op.add_column(
    "alert_settings",
    sa.Column(
      "status_page_public",
      sa.Boolean(),
      nullable=False,
      server_default=sa.text("true"),
    ),
  )


def downgrade() -> None:
  op.drop_column("alert_settings", "status_page_public")
  op.drop_column("monitors", "public_on_status_page")
