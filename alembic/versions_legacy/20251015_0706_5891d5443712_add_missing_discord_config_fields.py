"""add_missing_discord_config_fields

Revision ID: 5891d5443712
Revises: 5228ee1af938
Create Date: 2025-10-15 07:06:58.486372+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5891d5443712'
down_revision: Union[str, None] = '5228ee1af938'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Add missing Discord configuration fields
    
    # Add enable_discord field - boolean to enable/disable Discord integration
    op.add_column('character_discord_config', 
                  sa.Column('enable_discord', sa.Boolean(), nullable=True, server_default='true'))
    
    # Add discord_guild_restrictions field - JSON array for guild restrictions
    op.add_column('character_discord_config',
                  sa.Column('discord_guild_restrictions', sa.JSON(), nullable=True))
    
    # Add discord_channel_restrictions field - JSON array for channel restrictions  
    op.add_column('character_discord_config',
                  sa.Column('discord_channel_restrictions', sa.JSON(), nullable=True))
    
    # Add discord_status field to match web UI expectations (complement to discord_status_message)
    op.add_column('character_discord_config',
                  sa.Column('discord_status', sa.String(50), nullable=True, server_default='online'))


def downgrade() -> None:
    """Revert migration changes."""
    # Remove the added fields in reverse order
    op.drop_column('character_discord_config', 'discord_status')
    op.drop_column('character_discord_config', 'discord_channel_restrictions')
    op.drop_column('character_discord_config', 'discord_guild_restrictions')
    op.drop_column('character_discord_config', 'enable_discord')
