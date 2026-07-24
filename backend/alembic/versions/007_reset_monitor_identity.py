"""reset monitor identity after demo cleanup

Revision ID: 007
Revises: 006
Create Date: 2026-07-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.execute(
    """
    DELETE FROM monitors
    WHERE target IN ('https://httpbin.org/status/200', 'httpbin.org:443')
    """
  )
  op.execute(
    """
    SELECT setval(
      pg_get_serial_sequence('monitors', 'id'),
      GREATEST(COALESCE((SELECT MAX(id) FROM monitors), 0), 1)
    )
    """
  )


def downgrade() -> None:
  pass
