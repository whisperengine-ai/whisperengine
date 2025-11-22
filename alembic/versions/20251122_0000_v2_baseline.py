"""v2 baseline schema

Revision ID: v2_baseline
Revises: 
Create Date: 2025-11-22 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'v2_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply V2 baseline schema."""
    
    # Enable UUID extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # =============================================================================
    # V2 CHAT HISTORY
    # =============================================================================
    op.create_table(
        'v2_chat_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('character_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel_id', sa.String(length=255), nullable=True),
        sa.Column('message_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_v2_chat_history_user_char', 'v2_chat_history', ['user_id', 'character_name'])
    op.create_index('idx_v2_chat_history_created_at', 'v2_chat_history', ['created_at'])

    # =============================================================================
    # V2 SUMMARIES
    # =============================================================================
    op.create_table(
        'v2_summaries',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meaningfulness_score', sa.Float(), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_v2_summaries_session', 'v2_summaries', ['session_id'])

    # =============================================================================
    # V2 USER RELATIONSHIPS (Character Evolution)
    # =============================================================================
    op.create_table(
        'v2_user_relationships',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('character_name', sa.String(length=100), nullable=False),
        sa.Column('trust_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('unlocked_traits', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'character_name', name='unique_v2_user_character_relationship')
    )
    op.create_index('idx_v2_user_relationships_lookup', 'v2_user_relationships', ['user_id', 'character_name'])


def downgrade() -> None:
    """Revert V2 baseline schema."""
    op.drop_table('v2_user_relationships')
    op.drop_table('v2_summaries')
    op.drop_table('v2_chat_history')
