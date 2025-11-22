"""add_message_id_to_history

Revision ID: b554c4b8d413
Revises: 0f730db0c65e
Create Date: 2025-11-22 09:42:44.978238+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b554c4b8d413'
down_revision: Union[str, None] = '0f730db0c65e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('v2_chat_history', sa.Column('message_id', sa.Text(), nullable=True))
    op.create_index('idx_v2_chat_history_message_id', 'v2_chat_history', ['message_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_v2_chat_history_message_id', table_name='v2_chat_history')
    op.drop_column('v2_chat_history', 'message_id')
