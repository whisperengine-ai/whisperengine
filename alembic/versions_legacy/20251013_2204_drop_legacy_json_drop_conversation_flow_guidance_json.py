"""drop_conversation_flow_guidance_json_column

Revision ID: drop_legacy_json
Revises: 7fbfdf63fb76
Create Date: 2025-10-13 22:04:00.000000+00:00

Description:
    Drops the legacy conversation_flow_guidance JSON column from communication_styles table.
    
    This column contained 2-6KB JSON blobs that were dumping all conversation modes into prompts.
    Data has been migrated to normalized tables:
    - character_conversation_modes (mode definitions)
    - character_mode_guidance (avoid/encourage patterns)
    - character_mode_examples (usage examples)
    
    Removing this legacy field:
    1. Eliminates prompt bloat (~3KB per character)
    2. Removes data duplication
    3. Forces proper usage of normalized tables
    4. Cleans up database schema

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'drop_legacy_json'
down_revision: Union[str, None] = '7fbfdf63fb76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop legacy conversation_flow_guidance JSON column.
    
    The data in this column has been fully migrated to normalized tables:
    - character_conversation_modes
    - character_mode_guidance  
    - character_mode_examples
    
    Code has been updated to load from normalized tables only.
    This migration completes the cleanup by removing the deprecated field.
    """
    
    # Check if table and column exist before trying to drop it
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'communication_styles' in tables:
        columns = [c['name'] for c in inspector.get_columns('communication_styles')]
        if 'conversation_flow_guidance' in columns:
            # Optional: Create backup table for safety (commented out by default)
            # op.execute("""
            #     CREATE TABLE communication_styles_backup AS 
            #     SELECT * FROM communication_styles
            # """)
            
            # Drop the legacy JSON column
            op.drop_column('communication_styles', 'conversation_flow_guidance')
            
            print("✅ Dropped conversation_flow_guidance column from communication_styles")
            print("   Data is now served from normalized tables:")
            print("   - character_conversation_modes (mode definitions)")
            print("   - character_mode_guidance (avoid/encourage patterns)")
            print("   - character_mode_examples (usage examples)")
        else:
            print("✅ Column conversation_flow_guidance already removed from communication_styles")
    else:
        print("✅ Table communication_styles does not exist (skipping column drop)")


def downgrade() -> None:
    """Re-add the conversation_flow_guidance column (empty).
    
    Note: This only recreates the column structure.
    The JSON data is NOT restored - it would need to be regenerated
    from normalized tables if truly needed.
    """
    
    # Check if table exists before attempting to modify it
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'communication_styles' in tables:
        # Re-add column as TEXT (nullable)
        op.add_column(
            'communication_styles',
            sa.Column('conversation_flow_guidance', sa.Text(), nullable=True)
        )
        
        print("⚠️  Re-added conversation_flow_guidance column (empty)")
        print("   JSON data was NOT restored - would need regeneration from normalized tables")
    else:
        print("⚠️  Table communication_styles does not exist (skipping column add)")
