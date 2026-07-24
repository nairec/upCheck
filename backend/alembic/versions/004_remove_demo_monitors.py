"""remove demo monitor seeds

Revision ID: 004
Revises: 003
Create Date: 2026-07-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.execute(
    """
    DELETE FROM monitors
    WHERE target IN ('https://httpbin.org/status/200', 'httpbin.org:443')
    """
  )


def downgrade() -> None:
  pass
