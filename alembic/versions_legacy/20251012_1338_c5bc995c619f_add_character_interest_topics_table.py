"""add_character_interest_topics_table

Revision ID: c5bc995c619f
Revises: 20251011_baseline_v106
Create Date: 2025-10-12 13:38:51.071942+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5bc995c619f'
down_revision: Union[str, None] = '20251011_baseline_v106'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create character_interest_topics table
    op.create_table(
        'character_interest_topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('topic_keyword', sa.String(length=100), nullable=False),
        sa.Column('boost_weight', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('gap_type_preference', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True, server_default='general'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'topic_keyword', name='uq_character_topic')
    )
    
    # Create indexes
    op.create_index('idx_character_interest_topics_character_id', 'character_interest_topics', ['character_id'])
    op.create_index('idx_character_interest_topics_keyword', 'character_interest_topics', ['topic_keyword'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop indexes
    op.drop_index('idx_character_interest_topics_keyword', table_name='character_interest_topics')
    op.drop_index('idx_character_interest_topics_character_id', table_name='character_interest_topics')
    
    # Drop table
    op.drop_table('character_interest_topics')
