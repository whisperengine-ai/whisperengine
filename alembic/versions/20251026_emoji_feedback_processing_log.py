"""Add enrichment_processing_log table for emoji feedback tracking

Revision ID: 20251026_emoji_log
Revises: 20251019_1858_27e207ded5a0
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251026_emoji_log'
down_revision = '4628baf741ee'  # 20251020_1356 - Add unban audit columns
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add enrichment_processing_log table to track processed records.
    
    Prevents duplicate processing of emoji reactions, conversation summaries,
    fact extractions, and other enrichment tasks that use LLM calls.
    
    CRITICAL: Prevents wasting LLM API calls on already-processed data!
    """
    
    op.create_table(
        'enrichment_processing_log',
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('bot_name', sa.String(length=100), nullable=False),
        sa.Column('point_id', sa.String(length=255), nullable=False),
        sa.Column('processing_type', sa.String(length=50), nullable=False),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        
        # Optional metadata for debugging
        sa.Column('feedback_type', sa.String(length=50), nullable=True),  # RATING, AGREEMENT, etc.
        sa.Column('confidence', sa.Float(), nullable=True),
        
        sa.PrimaryKeyConstraint('user_id', 'bot_name', 'point_id', 'processing_type',
                               name='pk_enrichment_processing_log')
    )
    
    # Index for fast lookups during enrichment cycles
    op.create_index('idx_enrichment_log_lookup', 'enrichment_processing_log',
                   ['user_id', 'bot_name', 'processing_type'])
    
    # Index for cleanup queries (find old processed records)
    op.create_index('idx_enrichment_log_processed_at', 'enrichment_processing_log',
                   ['processed_at'])


def downgrade() -> None:
    """
    Remove enrichment_processing_log table.
    
    WARNING: This will cause duplicate LLM calls on already-processed emojis!
    """
    op.drop_index('idx_enrichment_log_processed_at', 'enrichment_processing_log')
    op.drop_index('idx_enrichment_log_lookup', 'enrichment_processing_log')
    op.drop_table('enrichment_processing_log')
