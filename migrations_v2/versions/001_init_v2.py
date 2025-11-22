"""init_v2_schema

Revision ID: 001_init_v2
Revises: 
Create Date: 2025-11-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_init_v2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table exists to avoid errors on re-runs
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if not inspector.has_table('v2_chat_history'):
        # Create v2_chat_history table
        op.create_table(
            'v2_chat_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('character_name', sa.Text(), nullable=False),
            sa.Column('role', sa.Text(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create index
        op.create_index(
            'idx_v2_chat_history_user_char',
            'v2_chat_history',
            ['user_id', 'character_name'],
            unique=False
        )


def downgrade() -> None:
    op.drop_index('idx_v2_chat_history_user_char', table_name='v2_chat_history')
    op.drop_table('v2_chat_history')
