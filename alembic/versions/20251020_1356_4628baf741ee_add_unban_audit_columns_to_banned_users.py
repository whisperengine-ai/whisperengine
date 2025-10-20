"""add_unban_audit_columns_to_banned_users

Revision ID: 4628baf741ee
Revises: c64001afbd46
Create Date: 2025-10-20 13:56:03.961638+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4628baf741ee'
down_revision: Union[str, None] = 'c64001afbd46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unban audit columns to banned_users table.
    
    Adds proper audit trail columns for unban operations instead of
    cramming information into the notes field.
    """
    # Add unbanned_at timestamp column
    op.add_column(
        'banned_users',
        sa.Column('unbanned_at', sa.TIMESTAMP(), nullable=True)
    )
    
    # Add unbanned_by column to track who performed the unban
    op.add_column(
        'banned_users',
        sa.Column('unbanned_by', sa.TEXT(), nullable=True)
    )
    
    # Add unban_reason column for documenting why user was unbanned
    op.add_column(
        'banned_users',
        sa.Column('unban_reason', sa.TEXT(), nullable=True)
    )
    
    # Add index on unbanned_at for efficient queries on unban history
    op.create_index(
        'idx_banned_users_unbanned_at',
        'banned_users',
        ['unbanned_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove unban audit columns from banned_users table."""
    # Drop index first
    op.drop_index('idx_banned_users_unbanned_at', table_name='banned_users')
    
    # Drop columns in reverse order
    op.drop_column('banned_users', 'unban_reason')
    op.drop_column('banned_users', 'unbanned_by')
    op.drop_column('banned_users', 'unbanned_at')
