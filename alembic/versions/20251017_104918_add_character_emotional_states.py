"""Add character_emotional_states table

Revision ID: 20251017_104918
Revises: 
Create Date: 2025-10-17 10:49:18.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251017_104918'
down_revision = 'a1b2c3d4e5f6'  # Previous: add_cdl_table_and_column_comments
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create character_emotional_states table for bot emotional state tracking."""
    op.create_table(
        'character_emotional_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_name', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('state_data', postgresql.JSONB(), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_name', 'user_id', name='unique_character_user_state')
    )
    
    # Index for faster lookups
    op.create_index(
        'idx_character_emotional_states_lookup',
        'character_emotional_states',
        ['character_name', 'user_id']
    )
    
    # Index for cleanup/maintenance queries (find old states)
    op.create_index(
        'idx_character_emotional_states_last_updated',
        'character_emotional_states',
        ['last_updated']
    )


def downgrade() -> None:
    """Drop character_emotional_states table."""
    op.drop_index('idx_character_emotional_states_last_updated', table_name='character_emotional_states')
    op.drop_index('idx_character_emotional_states_lookup', table_name='character_emotional_states')
    op.drop_table('character_emotional_states')
