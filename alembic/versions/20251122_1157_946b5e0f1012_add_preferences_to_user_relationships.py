"""add preferences to user relationships

Revision ID: 946b5e0f1012
Revises: 1b7697aae84c
Create Date: 2025-11-22 11:57:36.990415+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '946b5e0f1012'
down_revision: Union[str, None] = '1b7697aae84c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    op.add_column('v2_user_relationships', sa.Column('preferences', sa.JSON(), server_default='{}', nullable=False))


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_column('v2_user_relationships', 'preferences')
