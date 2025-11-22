"""change preferences to jsonb

Revision ID: 368c9b120274
Revises: 946b5e0f1012
Create Date: 2025-11-22 12:01:27.896458+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '368c9b120274'
down_revision: Union[str, None] = '946b5e0f1012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects.postgresql import JSONB

def upgrade() -> None:
    """Apply migration changes."""
    op.alter_column('v2_user_relationships', 'preferences',
               existing_type=sa.JSON(),
               type_=JSONB(),
               postgresql_using='preferences::jsonb')


def downgrade() -> None:
    """Revert migration changes."""
    op.alter_column('v2_user_relationships', 'preferences',
               existing_type=JSONB(),
               type_=sa.JSON(),
               postgresql_using='preferences::json')
