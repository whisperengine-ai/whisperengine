"""add_insights_to_user_relationships

Revision ID: 1b7697aae84c
Revises: abbcc63f93ce
Create Date: 2025-11-22 11:31:51.306394+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b7697aae84c'
down_revision: Union[str, None] = '09656c8d6eb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    op.add_column('v2_user_relationships', sa.Column('insights', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_column('v2_user_relationships', 'insights')
