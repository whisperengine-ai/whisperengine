"""add_character_learning_persistence_tables

Revision ID: 336ce8830dfe
Revises: 20251017_104918
Create Date: 2025-10-17 19:19:40.290194+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '336ce8830dfe'
down_revision: Union[str, None] = '20251017_104918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Table 1: Character Insights - Core insight storage
    op.create_table(
        'character_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('insight_content', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('discovery_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('conversation_context', sa.Text(), nullable=True),
        sa.Column('importance_level', sa.Integer(), nullable=False, server_default=sa.text('5')),
        sa.Column('emotional_valence', sa.Float(), nullable=True),
        sa.Column('triggers', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('supporting_evidence', sa.ARRAY(sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'insight_content', name='uq_character_insight_content')
    )
    
    # Create indexes for character_insights
    op.create_index('idx_character_insights_character_id', 'character_insights', ['character_id'])
    op.create_index('idx_character_insights_insight_type', 'character_insights', ['insight_type'])
    op.create_index('idx_character_insights_discovery_date', 'character_insights', ['discovery_date'])
    op.create_index('idx_character_insights_confidence_score', 'character_insights', ['confidence_score'])
    op.create_index('idx_character_insights_importance_level', 'character_insights', ['importance_level'])
    
    # Table 2: Character Insight Relationships - Graph connections
    op.create_table(
        'character_insight_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_insight_id', sa.Integer(), nullable=False),
        sa.Column('to_insight_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False, server_default=sa.text('0.5')),
        sa.Column('created_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_insight_id'], ['character_insights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_insight_id'], ['character_insights.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('from_insight_id', 'to_insight_id', 'relationship_type', name='uq_insight_relationship')
    )
    
    # Create indexes for character_insight_relationships
    op.create_index('idx_char_insight_rel_from_id', 'character_insight_relationships', ['from_insight_id'])
    op.create_index('idx_char_insight_rel_to_id', 'character_insight_relationships', ['to_insight_id'])
    op.create_index('idx_char_insight_rel_type', 'character_insight_relationships', ['relationship_type'])
    
    # Table 3: Character Learning Timeline - Evolution history
    op.create_table(
        'character_learning_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('learning_event', sa.Text(), nullable=False),
        sa.Column('learning_type', sa.String(50), nullable=False),
        sa.Column('before_state', sa.Text(), nullable=True),
        sa.Column('after_state', sa.Text(), nullable=True),
        sa.Column('trigger_conversation', sa.Text(), nullable=True),
        sa.Column('learning_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('significance_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE')
    )
    
    # Create indexes for character_learning_timeline
    op.create_index('idx_char_learning_timeline_character_id', 'character_learning_timeline', ['character_id'])
    op.create_index('idx_char_learning_timeline_learning_date', 'character_learning_timeline', ['learning_date'])
    op.create_index('idx_char_learning_timeline_learning_type', 'character_learning_timeline', ['learning_type'])
    op.create_index('idx_char_learning_timeline_significance', 'character_learning_timeline', ['significance_score'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('character_learning_timeline')
    op.drop_table('character_insight_relationships')
    op.drop_table('character_insights')
