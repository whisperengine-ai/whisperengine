"""merge_heads_before_enrichment_schema

Revision ID: b06ced8ecd14
Revises: 336ce8830dfe, 20251019_conv_summaries
Create Date: 2025-10-19 18:57:49.461150+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b06ced8ecd14'
down_revision: Union[str, None] = ('336ce8830dfe', '20251019_conv_summaries')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    pass


def downgrade() -> None:
    """Revert migration changes."""
    pass
