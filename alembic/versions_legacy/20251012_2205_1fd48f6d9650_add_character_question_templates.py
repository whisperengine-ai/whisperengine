"""add_character_question_templates

Revision ID: 1fd48f6d9650
Revises: 11f9e26c6345
Create Date: 2025-10-12 22:05:46.967025+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fd48f6d9650'
down_revision: Union[str, None] = '11f9e26c6345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create character_question_templates table for personality-appropriate questioning styles
    op.create_table(
        'character_question_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('gap_type', sa.String(length=50), nullable=False),  # origin, experience, specifics, location, community
        sa.Column('template_text', sa.Text(), nullable=False),  # Question template with {entity_name} and {relationship} placeholders
        sa.Column('personality_style', sa.String(length=50), nullable=True),  # warm, analytical, mystical, casual, professional
        sa.Column('priority_order', sa.Integer(), nullable=False, server_default='1'),  # 1-10 priority for template selection
        sa.Column('keywords', sa.ARRAY(sa.String(length=100)), nullable=True),  # Keywords that trigger this gap type
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'gap_type', 'template_text', name='uq_character_gap_template')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_character_question_templates_character_id', 'character_question_templates', ['character_id'])
    op.create_index('idx_character_question_templates_gap_type', 'character_question_templates', ['gap_type'])
    op.create_index('idx_character_question_templates_priority', 'character_question_templates', ['priority_order'])
    op.create_index('idx_character_question_templates_style', 'character_question_templates', ['personality_style'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop indexes
    op.drop_index('idx_character_question_templates_style', table_name='character_question_templates')
    op.drop_index('idx_character_question_templates_priority', table_name='character_question_templates')
    op.drop_index('idx_character_question_templates_gap_type', table_name='character_question_templates')
    op.drop_index('idx_character_question_templates_character_id', table_name='character_question_templates')
    
    # Drop table
    op.drop_table('character_question_templates')
