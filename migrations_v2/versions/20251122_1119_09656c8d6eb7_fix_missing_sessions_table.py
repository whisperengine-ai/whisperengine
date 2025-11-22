"""fix_missing_sessions_table

Revision ID: 09656c8d6eb7
Revises: abf9d9bf9c0d
Create Date: 2025-11-22 11:19:30.886652+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09656c8d6eb7'
down_revision: Union[str, None] = 'abf9d9bf9c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # V2 CONVERSATION SESSIONS
    if not inspector.has_table('v2_conversation_sessions'):
        op.create_table(
            'v2_conversation_sessions',
            sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('character_name', sa.String(), nullable=False),
            sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(
            'idx_v2_sessions_active',
            'v2_conversation_sessions',
            ['user_id', 'character_name', 'is_active']
        )

    # V2 SUMMARIES (Ensure it exists, might have been missed)
    if not inspector.has_table('v2_summaries'):
        op.create_table(
            'v2_summaries',
            sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('session_id', sa.UUID(), nullable=False), # FK added later or loosely coupled
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('meaningfulness_score', sa.Integer(), nullable=True),
            sa.Column('embedding_id', sa.UUID(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    pass
