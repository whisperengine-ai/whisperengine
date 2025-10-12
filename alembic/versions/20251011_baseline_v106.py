"""Create initial baseline schema for v1.0.6

This migration captures the database schema state at v1.0.6 release.
It includes all core tables: users, characters, CDL schema, relationships,
memories, and supporting infrastructure.

Revision ID: 20251011_baseline_v106
Revises: 
Create Date: 2025-10-11 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251011_baseline_v106'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Apply baseline schema for v1.0.6.
    
    NOTE: For existing v1.0.6 deployments, use:
        alembic stamp 20251011_baseline_v106
    
    This migration should only be run on fresh databases.
    """
    
    # =============================================================================
    # CORE TABLES
    # =============================================================================
    
    # Users table - universal identity system
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discord_user_id', sa.String(length=50), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('discord_user_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_discord', 'users', ['discord_user_id'])
    op.create_index('idx_users_username', 'users', ['username'])
    
    # Characters table - AI character definitions
    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('character_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_characters_name', 'characters', ['name'])
    
    # =============================================================================
    # CDL (Character Definition Language) SCHEMA
    # =============================================================================
    
    # Character Identity
    op.create_table(
        'character_identity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=500), nullable=True),
        sa.Column('nicknames', sa.Text(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('occupation', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id')
    )
    
    # Character Attributes (fears, dreams, quirks, values, etc.)
    op.create_table(
        'character_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('importance', sa.String(length=100), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id', 'category', 'display_order')
    )
    op.create_index('idx_attributes_char_cat', 'character_attributes', ['character_id', 'category'])
    
    # Character Communication Style
    op.create_table(
        'character_communication',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('tone', sa.String(length=500), nullable=True),
        sa.Column('humor_style', sa.String(length=500), nullable=True),
        sa.Column('conversation_pacing', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id')
    )
    
    # =============================================================================
    # RELATIONSHIP & MEMORY TABLES
    # =============================================================================
    
    # User-Character Relationships
    op.create_table(
        'user_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('bot_name', sa.String(length=100), nullable=False),
        sa.Column('affection', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('trust', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('attunement', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('first_interaction', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_interaction', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('interaction_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'bot_name')
    )
    op.create_index('idx_relationships_user_bot', 'user_relationships', ['user_id', 'bot_name'])
    
    # User Facts (knowledge graph)
    op.create_table(
        'user_facts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('bot_name', sa.String(length=100), nullable=False),
        sa.Column('fact_type', sa.String(length=100), nullable=False),
        sa.Column('fact_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_facts_user_bot', 'user_facts', ['user_id', 'bot_name'])
    op.create_index('idx_facts_type', 'user_facts', ['fact_type'])


def downgrade() -> None:
    """
    Remove baseline schema.
    
    WARNING: This will drop all tables and destroy all data!
    Only use for testing or complete system teardown.
    """
    
    # Drop tables in reverse dependency order
    op.drop_index('idx_facts_type', 'user_facts')
    op.drop_index('idx_facts_user_bot', 'user_facts')
    op.drop_table('user_facts')
    
    op.drop_index('idx_relationships_user_bot', 'user_relationships')
    op.drop_table('user_relationships')
    
    op.drop_table('character_communication')
    
    op.drop_index('idx_attributes_char_cat', 'character_attributes')
    op.drop_table('character_attributes')
    
    op.drop_table('character_identity')
    
    op.drop_index('idx_characters_name', 'characters')
    op.drop_table('characters')
    
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_discord', 'users')
    op.drop_table('users')
