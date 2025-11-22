"""add_v2_goal_system_tables

Revision ID: abbcc63f93ce
Revises: v2_baseline
Create Date: 2025-11-22 11:04:15.623632+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'abbcc63f93ce'
down_revision: Union[str, None] = 'v2_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # =============================================================================
    # V2 GOALS (Definitions)
    # =============================================================================
    op.create_table(
        'v2_goals',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('character_name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('success_criteria', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_name', 'slug', name='unique_character_goal_slug')
    )
    op.create_index('idx_v2_goals_character', 'v2_goals', ['character_name'])

    # =============================================================================
    # V2 USER GOAL PROGRESS (Tracking)
    # =============================================================================
    op.create_table(
        'v2_user_goal_progress',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('goal_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='not_started', nullable=False),
        sa.Column('progress_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['goal_id'], ['v2_goals.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'goal_id', name='unique_user_goal_progress')
    )
    op.create_index('idx_v2_goal_progress_user', 'v2_user_goal_progress', ['user_id'])
    op.create_index('idx_v2_goal_progress_status', 'v2_user_goal_progress', ['status'])


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_table('v2_user_goal_progress')
    op.drop_table('v2_goals')
