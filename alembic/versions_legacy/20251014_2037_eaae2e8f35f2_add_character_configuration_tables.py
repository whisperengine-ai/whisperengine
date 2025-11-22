"""add_character_configuration_tables

Add per-character LLM and Discord configuration support for CDL web UI.
This enables database-driven configuration management where each character
can have their own LLM endpoints, Discord tokens, and deployment settings.

Revision ID: eaae2e8f35f2
Revises: emoji_personality_cols
Create Date: 2025-10-14 20:37:21.902132+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaae2e8f35f2'
down_revision: Union[str, None] = 'emoji_personality_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # Character LLM Configuration Table
    op.create_table(
        'character_llm_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        
        # LLM Provider Configuration
        sa.Column('llm_client_type', sa.String(length=100), nullable=False, server_default='openrouter'),
        sa.Column('llm_chat_api_url', sa.String(length=500), nullable=False, server_default='https://openrouter.ai/api/v1'),
        sa.Column('llm_chat_model', sa.String(length=200), nullable=False, server_default='anthropic/claude-3-haiku'),
        sa.Column('llm_chat_api_key', sa.Text(), nullable=True),
        
        # Advanced LLM Settings
        sa.Column('llm_temperature', sa.Numeric(precision=3, scale=2), server_default='0.7'),
        sa.Column('llm_max_tokens', sa.Integer(), server_default='4000'),
        sa.Column('llm_top_p', sa.Numeric(precision=3, scale=2), server_default='0.9'),
        sa.Column('llm_frequency_penalty', sa.Numeric(precision=3, scale=2), server_default='0.0'),
        sa.Column('llm_presence_penalty', sa.Numeric(precision=3, scale=2), server_default='0.0'),
        
        # Configuration metadata
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'is_active', name='uq_character_llm_config_active')
    )
    
    # Character Discord Configuration Table
    op.create_table(
        'character_discord_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        
        # Discord Bot Configuration
        sa.Column('discord_bot_token', sa.Text(), nullable=True),
        sa.Column('discord_application_id', sa.String(length=100), nullable=True),
        sa.Column('discord_guild_id', sa.String(length=100), nullable=True),
        
        # Bot Behavior Settings
        sa.Column('discord_status_message', sa.String(length=200), nullable=True),
        sa.Column('discord_activity_type', sa.String(length=50), server_default='playing'),
        sa.Column('max_message_length', sa.Integer(), server_default='2000'),
        sa.Column('typing_delay_seconds', sa.Numeric(precision=3, scale=1), server_default='2.0'),
        sa.Column('enable_reactions', sa.Boolean(), server_default='true'),
        sa.Column('enable_typing_indicator', sa.Boolean(), server_default='true'),
        
        # Configuration metadata
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'is_active', name='uq_character_discord_config_active')
    )
    
    # Character Deployment Configuration Table
    op.create_table(
        'character_deployment_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        
        # Deployment Settings
        sa.Column('container_port', sa.Integer(), nullable=True),
        sa.Column('health_check_port', sa.Integer(), nullable=True),
        sa.Column('memory_limit', sa.String(length=20), server_default='512m'),
        sa.Column('cpu_limit', sa.String(length=20), server_default='0.5'),
        sa.Column('restart_policy', sa.String(length=50), server_default='unless-stopped'),
        
        # Environment Configuration
        sa.Column('environment_variables', sa.JSON(), nullable=True),
        sa.Column('volume_mounts', sa.JSON(), nullable=True),
        sa.Column('network_mode', sa.String(length=50), server_default='whisperengine-multi_default'),
        
        # Deployment Status
        sa.Column('deployment_status', sa.String(length=50), server_default='stopped'),
        sa.Column('auto_deploy', sa.Boolean(), server_default='false'),
        sa.Column('last_deployed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Configuration metadata
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'is_active', name='uq_character_deployment_config_active')
    )
    
    # Create indexes for performance
    op.create_index('idx_character_llm_config_character_id', 'character_llm_config', ['character_id'])
    op.create_index('idx_character_llm_config_active', 'character_llm_config', ['is_active'])
    
    op.create_index('idx_character_discord_config_character_id', 'character_discord_config', ['character_id'])
    op.create_index('idx_character_discord_config_active', 'character_discord_config', ['is_active'])
    
    op.create_index('idx_character_deployment_config_character_id', 'character_deployment_config', ['character_id'])
    op.create_index('idx_character_deployment_config_active', 'character_deployment_config', ['is_active'])
    op.create_index('idx_character_deployment_config_status', 'character_deployment_config', ['deployment_status'])


def downgrade() -> None:
    """Revert migration changes."""
    
    # Drop indexes first
    op.drop_index('idx_character_deployment_config_status', 'character_deployment_config')
    op.drop_index('idx_character_deployment_config_active', 'character_deployment_config')
    op.drop_index('idx_character_deployment_config_character_id', 'character_deployment_config')
    
    op.drop_index('idx_character_discord_config_active', 'character_discord_config')
    op.drop_index('idx_character_discord_config_character_id', 'character_discord_config')
    
    op.drop_index('idx_character_llm_config_active', 'character_llm_config')
    op.drop_index('idx_character_llm_config_character_id', 'character_llm_config')
    
    # Drop tables
    op.drop_table('character_deployment_config')
    op.drop_table('character_discord_config')
    op.drop_table('character_llm_config')
