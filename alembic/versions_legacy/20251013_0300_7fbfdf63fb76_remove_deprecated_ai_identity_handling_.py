"""remove_deprecated_ai_identity_handling_column

Revision ID: 7fbfdf63fb76
Revises: 8b77eda62e71
Create Date: 2025-10-13 03:00:24.299209+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '7fbfdf63fb76'
down_revision: Union[str, None] = '8b77eda62e71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Remove the deprecated ai_identity_handling column from communication_styles
    # This column was causing data consistency issues due to multiple formats:
    # - Plain text strings (Elena: "Honest about AI nature when directly asked...")  
    # - JSON strings (Sophia: {"allow_full_roleplay_immersion": false, ...})
    # - Python dict strings (Marcus: {'allow_full_roleplay_immersion': False, ...})
    #
    # All data has been migrated to the normalized character_roleplay_config table
    
    # Check if table exists before attempting to modify it
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'communication_styles' in tables:
        columns = [c['name'] for c in inspector.get_columns('communication_styles')]
        if 'ai_identity_handling' in columns:
            op.drop_column('communication_styles', 'ai_identity_handling')
    else:
        print("Skipping drop_column: table 'communication_styles' does not exist")


def downgrade() -> None:
    """Revert migration changes."""
    # Re-add the ai_identity_handling column if needed
    
    # Check if table exists before attempting to modify it
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'communication_styles' in tables:
        op.add_column('communication_styles', 
                      sa.Column('ai_identity_handling', sa.Text(), nullable=True))
    
    # Note: This downgrade does NOT restore the data that was in this column
    # The data has been migrated to normalized tables and would need manual restoration
