"""add_cdl_table_and_column_comments

Revision ID: a1b2c3d4e5f6
Revises: 5891d5443712
Create Date: 2025-10-15 12:00:00.000000+00:00

This migration adds PostgreSQL COMMENT statements to all CDL tables and columns.
These comments provide inline documentation that appears in database tools like
pgAdmin, DBeaver, and psql commands, helping developers understand the schema
without needing external documentation.

Comments are non-destructive and do not affect data or performance.
"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5891d5443712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply PostgreSQL COMMENT statements to CDL tables and columns."""
    
    # Load the SQL file with all COMMENT statements
    sql_file_path = Path(__file__).parent.parent.parent / 'sql' / 'add_cdl_table_comments.sql'
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Execute the SQL file
    # Note: This uses raw SQL execution which is safe for COMMENT statements
    connection = op.get_bind()
    connection.execute(sa.text(sql_content))
    
    print("✅ Successfully applied PostgreSQL COMMENT statements to CDL tables and columns")


def downgrade() -> None:
    """Remove PostgreSQL COMMENT statements from CDL tables and columns.
    
    Note: Removing comments is optional since they are non-destructive.
    This downgrade removes all comments from character-related tables.
    """
    
    # List of all CDL tables
    cdl_tables = [
        'characters',
        'personality_traits',
        'character_values',
        'character_identity_details',
        'character_speech_patterns',
        'character_conversation_flows',
        'character_behavioral_triggers',
        'character_background',
        'character_interests',
        'character_relationships',
        'character_llm_config',
        'character_discord_config',
        'character_deployment_config',
        'character_appearance',
        'character_memories',
        'character_abilities',
        'character_instructions',
        'character_essence',
    ]
    
    # Get database connection
    connection = op.get_bind()
    
    # Remove table comments
    for table_name in cdl_tables:
        connection.execute(sa.text(f"COMMENT ON TABLE {table_name} IS NULL"))
    
    # Remove column comments (PostgreSQL will remove all column comments when table comment is NULL)
    # But for completeness, we could also explicitly remove them:
    for table_name in cdl_tables:
        # Get all columns for this table
        result = connection.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = '{table_name}'
        """))
        
        for row in result:
            column_name = row[0]
            connection.execute(sa.text(f"COMMENT ON COLUMN {table_name}.{column_name} IS NULL"))
    
    print("✅ Removed PostgreSQL COMMENT statements from CDL tables and columns")
