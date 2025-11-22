"""add_personality_traits_and_communication_tables

Create the personality_traits, communication_styles, and character_values tables
that are required by the CDL system and actively queried by cdl_ai_integration.py.

These tables were previously created by legacy SQL file 
src/database/migrations/003_clean_rdbms_cdl_schema.sql but were never added
to Alembic migrations. This migration brings them into the Alembic system.

Schema source: 003_clean_rdbms_cdl_schema.sql (lines 35-72)

Revision ID: 9c23e4e81011
Revises: ab68d77b5088
Create Date: 2025-10-20 00:19:31.293738+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9c23e4e81011'
down_revision: Union[str, None] = 'ab68d77b5088'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create personality_traits, communication_styles, and character_values tables.
    
    These tables are CRITICAL for CDL AI integration:
    - personality_traits: Big Five personality traits (what cdl_ai_integration.py queries)
    - communication_styles: Communication preferences and style guidelines
    - character_values: Core values, beliefs, and fears that drive character behavior
    
    SAFE FOR EXISTING DATABASES: Uses IF NOT EXISTS to handle databases where
    these tables were created by legacy SQL files (src/database/migrations/003_clean_rdbms_cdl_schema.sql)
    """
    
    # Check if tables already exist (from legacy SQL migrations)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # personality_traits - Big Five personality traits
    if 'personality_traits' not in existing_tables:
        op.create_table(
            'personality_traits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('character_id', sa.Integer(), nullable=True),
            sa.Column('trait_name', sa.String(length=50), nullable=False),
            sa.Column('trait_value', sa.Numeric(precision=3, scale=2), nullable=True),
            sa.Column('intensity', sa.String(length=20), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('character_id', 'trait_name', name='personality_traits_character_id_trait_name_key')
        )
        op.create_index('idx_personality_traits_character', 'personality_traits', ['character_id'])
    
    # communication_styles - Communication preferences
    if 'communication_styles' not in existing_tables:
        op.create_table(
            'communication_styles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('character_id', sa.Integer(), nullable=True),
            sa.Column('engagement_level', sa.Numeric(precision=3, scale=2), nullable=True),
            sa.Column('formality', sa.String(length=100), nullable=True),
            sa.Column('emotional_expression', sa.Numeric(precision=3, scale=2), nullable=True),
            sa.Column('response_length', sa.String(length=50), nullable=True),
            sa.Column('conversation_flow_guidance', sa.Text(), nullable=True),
            sa.Column('ai_identity_handling', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_communication_styles_character', 'communication_styles', ['character_id'])
    
    # character_values - Core values, beliefs, fears
    if 'character_values' not in existing_tables:
        op.create_table(
            'character_values',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('character_id', sa.Integer(), nullable=True),
            sa.Column('value_key', sa.String(length=100), nullable=False),
            sa.Column('value_description', sa.Text(), nullable=False),
            sa.Column('importance_level', sa.String(length=20), server_default='medium', nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('character_id', 'value_key', name='character_values_character_id_value_key_key')
        )
        op.create_index('idx_character_values_character', 'character_values', ['character_id'])


def downgrade() -> None:
    """Drop the personality, communication, and values tables."""
    op.drop_index('idx_character_values_character', table_name='character_values')
    op.drop_table('character_values')
    
    op.drop_index('idx_communication_styles_character', table_name='communication_styles')
    op.drop_table('communication_styles')
    
    op.drop_index('idx_personality_traits_character', table_name='personality_traits')
    op.drop_table('personality_traits')
