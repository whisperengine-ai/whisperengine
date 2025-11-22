"""add_sessions_and_summaries

Revision ID: 3355f3fac3fd
Revises: 001_init_v2
Create Date: 2025-11-22 09:10:16.171320+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3355f3fac3fd'
down_revision: Union[str, None] = '001_init_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.dialects.postgresql import UUID

    # 1. Create v2_conversation_sessions table
    op.create_table(
        'v2_conversation_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('character_name', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Index for fast lookup of active sessions
    op.create_index(
        'idx_v2_sessions_active',
        'v2_conversation_sessions',
        ['user_id', 'character_name', 'is_active']
    )

    # 2. Create v2_summaries table
    op.create_table(
        'v2_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('v2_conversation_sessions.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meaningfulness_score', sa.Integer(), nullable=True, comment='1-5 score of conversation depth'),
        sa.Column('embedding_id', UUID(as_uuid=True), nullable=True, comment='Link to Qdrant point ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Index for finding summaries by session
    op.create_index(
        'idx_v2_summaries_session',
        'v2_summaries',
        ['session_id']
    )


def downgrade() -> None:
    op.drop_index('idx_v2_summaries_session', table_name='v2_summaries')
    op.drop_table('v2_summaries')
    op.drop_index('idx_v2_sessions_active', table_name='v2_conversation_sessions')
    op.drop_table('v2_conversation_sessions')
