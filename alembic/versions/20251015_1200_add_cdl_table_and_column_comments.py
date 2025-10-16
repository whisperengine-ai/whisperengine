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
import re

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5891d5443712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply PostgreSQL COMMENT statements to CDL tables and columns.
    
    This migration executes each COMMENT statement individually and skips
    any statements that fail (e.g., if a column doesn't exist yet).
    This makes the migration more resilient to schema variations.
    """
    
    # Load the SQL file with all COMMENT statements
    sql_file_path = Path(__file__).parent.parent.parent / 'sql' / 'add_cdl_table_comments.sql'
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Get database connection
    connection = op.get_bind()
    
    # Split the SQL content into individual statements
    # We need to execute each COMMENT statement separately to handle missing columns gracefully
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip comments and empty lines
        if line.strip().startswith('--') or not line.strip():
            continue
        
        # Collect lines that are part of a COMMENT statement
        if line.strip().upper().startswith('COMMENT ON'):
            if current_statement:
                statements.append(' '.join(current_statement))
            current_statement = [line.strip()]
        elif current_statement:
            current_statement.append(line.strip())
            # Check if this line ends the statement (ends with semicolon)
            if line.strip().endswith(';'):
                statements.append(' '.join(current_statement))
                current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statements.append(' '.join(current_statement))
    
    # Execute each COMMENT statement individually
    successful = 0
    skipped = 0
    
    for stmt in statements:
        if not stmt or stmt.startswith('SELECT'):
            continue
        
        try:
            connection.execute(sa.text(stmt))
            successful += 1
        except Exception as e:
            # Skip comments on non-existent columns
            error_msg = str(e)
            if 'does not exist' in error_msg:
                # Extract column/table name from error message
                match = re.search(r'column "(\w+)" of relation "(\w+)"', error_msg)
                if match:
                    column_name, table_name = match.groups()
                    print(f"⚠️  Skipped comment for {table_name}.{column_name} (column does not exist)")
                else:
                    print(f"⚠️  Skipped statement due to missing object: {error_msg.split('DETAIL:')[0].strip()}")
                skipped += 1
            else:
                # Re-raise other errors
                raise
    
    print(f"✅ Applied {successful} PostgreSQL COMMENT statements to CDL tables and columns")
    if skipped > 0:
        print(f"⚠️  Skipped {skipped} comments for non-existent columns (will be added in future migrations)")


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
