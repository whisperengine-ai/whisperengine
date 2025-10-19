"""merge enrichment and personality fix migrations

Revision ID: ab68d77b5088
Revises: c64001afbd46, 27e207ded5a0
Create Date: 2025-10-19 23:16:52.332602+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab68d77b5088'
down_revision: Union[str, None] = ('c64001afbd46', '27e207ded5a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    pass


def downgrade() -> None:
    """Revert migration changes."""
    pass
