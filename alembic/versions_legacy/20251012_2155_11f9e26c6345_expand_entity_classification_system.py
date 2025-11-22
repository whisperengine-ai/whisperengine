"""expand_entity_classification_system

Revision ID: 11f9e26c6345
Revises: c5bc995c619f
Create Date: 2025-10-12 21:55:17.460225+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11f9e26c6345'
down_revision: Union[str, None] = 'c5bc995c619f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create character_entity_categories table for organized entity classification
    op.create_table(
        'character_entity_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('entity_keyword', sa.String(length=100), nullable=False),
        sa.Column('category_type', sa.String(length=50), nullable=False),  # activity, food, topic, hobby, professional, etc.
        sa.Column('question_preference', sa.String(length=50), nullable=True),  # origin, experience, location, specifics, community
        sa.Column('priority_level', sa.Integer(), nullable=False, server_default='3'),  # 1-5 priority for character
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'entity_keyword', name='uq_character_entity_keyword')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_character_entity_categories_character_id', 'character_entity_categories', ['character_id'])
    op.create_index('idx_character_entity_categories_keyword', 'character_entity_categories', ['entity_keyword'])
    op.create_index('idx_character_entity_categories_type', 'character_entity_categories', ['category_type'])
    op.create_index('idx_character_entity_categories_priority', 'character_entity_categories', ['priority_level'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop indexes
    op.drop_index('idx_character_entity_categories_priority', table_name='character_entity_categories')
    op.drop_index('idx_character_entity_categories_type', table_name='character_entity_categories')
    op.drop_index('idx_character_entity_categories_keyword', table_name='character_entity_categories')
    op.drop_index('idx_character_entity_categories_character_id', table_name='character_entity_categories')
    
    # Drop table
    op.drop_table('character_entity_categories')
