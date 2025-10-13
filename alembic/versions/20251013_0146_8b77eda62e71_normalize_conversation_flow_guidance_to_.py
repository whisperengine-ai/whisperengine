"""normalize_conversation_flow_guidance_to_rdbms

Revision ID: 8b77eda62e71
Revises: 2230add_keyword_templates
Create Date: 2025-10-13 01:46:58.270478+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b77eda62e71'
down_revision: Union[str, None] = '2230add_keyword_templates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Normalize conversation_flow_guidance JSON into proper RDBMS tables.
    
    This replaces JSON text fields with clean relational structure for web UI editing.
    Creates 7 new tables for normalized conversation flow guidance data.
    """
    
    # 1. Character Conversation Modes (replaces character-specific top-level keys)
    op.create_table(
        'character_conversation_modes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('mode_name', sa.String(100), nullable=False),  # e.g., 'technical_education', 'romantic_interest'
        sa.Column('energy_level', sa.String(50), nullable=True),  # e.g., 'thoughtful', 'enthusiastic'
        sa.Column('approach', sa.Text(), nullable=True),  # Main approach description
        sa.Column('transition_style', sa.Text(), nullable=True),  # How to transition to this mode
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'mode_name')
    )
    
    # 2. Mode Guidance Items (replaces 'avoid' and 'encourage' arrays)
    op.create_table(
        'character_mode_guidance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mode_id', sa.Integer(), nullable=False),
        sa.Column('guidance_type', sa.String(20), nullable=False),  # 'avoid' or 'encourage'
        sa.Column('guidance_text', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['mode_id'], ['character_conversation_modes.id'], ondelete='CASCADE'),
        sa.CheckConstraint("guidance_type IN ('avoid', 'encourage')", name='ck_guidance_type')
    )
    
    # 3. Mode Examples (replaces 'examples' arrays)
    op.create_table(
        'character_mode_examples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mode_id', sa.Integer(), nullable=False),
        sa.Column('example_text', sa.Text(), nullable=False),
        sa.Column('example_type', sa.String(50), nullable=True),  # e.g., 'response', 'question', 'transition'
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['mode_id'], ['character_conversation_modes.id'], ondelete='CASCADE')
    )
    
    # 4. General Conversation Settings (replaces 'general' section)
    op.create_table(
        'character_general_conversation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('default_energy', sa.String(50), nullable=True),
        sa.Column('conversation_style', sa.Text(), nullable=True),
        sa.Column('transition_approach', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id')
    )
    
    # 5. Response Style Settings (replaces 'response_style' section)
    op.create_table(
        'character_response_style',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id')
    )
    
    # 6. Response Style Items (replaces core_principles, formatting_rules arrays)
    op.create_table(
        'character_response_style_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('response_style_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),  # 'core_principle', 'formatting_rule', 'character_adaptation'
        sa.Column('item_text', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['response_style_id'], ['character_response_style.id'], ondelete='CASCADE')
    )
    
    # 7. Response Patterns (replaces response_patterns from general)
    op.create_table(
        'character_response_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('general_conversation_id', sa.Integer(), nullable=False),
        sa.Column('pattern_name', sa.String(100), nullable=True),
        sa.Column('pattern_description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['general_conversation_id'], ['character_general_conversation.id'], ondelete='CASCADE')
    )
    
    # Create indexes for performance
    op.create_index('idx_conversation_modes_character', 'character_conversation_modes', ['character_id'])
    op.create_index('idx_mode_guidance_mode', 'character_mode_guidance', ['mode_id'])
    op.create_index('idx_mode_examples_mode', 'character_mode_examples', ['mode_id'])
    op.create_index('idx_response_style_items_style', 'character_response_style_items', ['response_style_id'])
    op.create_index('idx_response_patterns_general', 'character_response_patterns', ['general_conversation_id'])


def downgrade() -> None:
    """Remove normalized conversation flow guidance tables and revert to JSON fields."""
    
    # Drop indexes first
    op.drop_index('idx_response_patterns_general')
    op.drop_index('idx_response_style_items_style')
    op.drop_index('idx_mode_examples_mode')
    op.drop_index('idx_mode_guidance_mode')
    op.drop_index('idx_conversation_modes_character')
    
    # Drop tables in reverse dependency order
    op.drop_table('character_response_patterns')
    op.drop_table('character_response_style_items')
    op.drop_table('character_response_style')
    op.drop_table('character_general_conversation')
    op.drop_table('character_mode_examples')
    op.drop_table('character_mode_guidance')
    op.drop_table('character_conversation_modes')
