"""add_channel_id_to_history

Revision ID: 0f730db0c65e
Revises: 3355f3fac3fd
Create Date: 2025-11-22 09:38:00.455627+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f730db0c65e'
down_revision: Union[str, None] = '3355f3fac3fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('v2_chat_history', sa.Column('channel_id', sa.Text(), nullable=True))
    op.create_index('idx_v2_chat_history_channel', 'v2_chat_history', ['channel_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_v2_chat_history_channel', table_name='v2_chat_history')
    op.drop_column('v2_chat_history', 'channel_id')
