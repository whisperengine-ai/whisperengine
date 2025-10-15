"""add_bot_deployments_table

Revision ID: 5228ee1af938
Revises: eaae2e8f35f2
Create Date: 2025-10-15 05:03:31.496008+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5228ee1af938'
down_revision: Union[str, None] = 'eaae2e8f35f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # Create bot_deployments table for tracking deployed bot containers
    op.create_table(
        'bot_deployments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('container_name', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='deploying'),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        
        # Unique constraints
        sa.UniqueConstraint('character_id', name='unique_character_deployment'),
        sa.UniqueConstraint('container_name', name='unique_container_name'),
        sa.UniqueConstraint('port', name='unique_port')
    )
    
    # Create indexes for performance
    op.create_index('idx_bot_deployments_character_id', 'bot_deployments', ['character_id'])
    op.create_index('idx_bot_deployments_status', 'bot_deployments', ['status'])
    op.create_index('idx_bot_deployments_port', 'bot_deployments', ['port'])


def downgrade() -> None:
    """Revert migration changes."""
    
    # Drop indexes
    op.drop_index('idx_bot_deployments_port', 'bot_deployments')
    op.drop_index('idx_bot_deployments_status', 'bot_deployments')
    op.drop_index('idx_bot_deployments_character_id', 'bot_deployments')
    
    # Drop table
    op.drop_table('bot_deployments')
