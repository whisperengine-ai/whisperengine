#!/usr/bin/env python3
"""
Export Character SQL Scripts
=============================
Generates SQL insert scripts for each character in the database.
Useful for backup, restore, and deployment of character configurations.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Character CDL tables to export (in dependency order)
CDL_TABLES = [
    'character_llm_config',
    'character_discord_config',
    'character_identity_details',
    'character_attributes',
    'character_values',
    'character_speech_patterns',
    'character_conversation_flows',
    'character_behavioral_triggers',
    'character_background',
    'character_interests',
    'character_relationships',
    'character_conversation_modes',
    'character_response_modes',
    'character_emotional_states',
    'character_communication_patterns',
    'character_response_patterns',
    'character_context_guidance',
    'character_conversation_contexts',
    'character_conversation_directives',
    'character_cultural_expressions',
    'character_directives',
    'character_emoji_patterns',
    'character_emotion_profile',
    'character_emotion_range',
    'character_emotional_triggers',
    'character_entity_categories',
    'character_essence',
    'character_expertise_domains',
    'character_general_conversation',
    'character_insights',
    'character_insight_relationships',
    'character_instructions',
    'character_interest_topics',
    'character_learning_timeline',
    'character_memories',
    'character_message_triggers',
    'character_metadata',
    'character_mode_examples',
    'character_mode_guidance',
    'character_question_templates',
    'character_response_guidelines',
    'character_response_style',
    'character_response_style_items',
    'character_roleplay_config',
    'character_vocabulary',
    'character_voice_profile',
    'character_voice_traits',
    'character_abilities',
    'character_ai_scenarios',
    'character_appearance',
    'character_current_context',
    'character_current_goals',
    'character_deployment_config',
]


def format_sql_value(value: Any) -> str:
    """Format a Python value as SQL literal"""
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape single quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    else:
        # For other types, convert to string and escape
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"


async def export_character(pool: asyncpg.Pool, normalized_name: str, output_dir: Path):
    """Export a single character to SQL insert script"""
    
    async with pool.acquire() as conn:
        # Get character base record
        character = await conn.fetchrow(
            "SELECT * FROM characters WHERE normalized_name = $1",
            normalized_name
        )
        
        if not character:
            print(f"❌ Character '{normalized_name}' not found in database")
            return False
        
        character_id = character['id']
        character_name = character['name']
        
        print(f"\n📝 Exporting character: {character_name} (ID: {character_id}, normalized: {normalized_name})")
        
        # Build SQL script
        sql_lines = [
            "-- =======================================================",
            f"-- Character: {character_name}",
            f"-- Normalized Name: {normalized_name}",
            f"-- Generated: {datetime.utcnow().isoformat()}Z",
            "-- =======================================================",
            "-- This script inserts a complete character configuration",
            "-- into the WhisperEngine CDL database system.",
            "-- =======================================================",
            "",
            "BEGIN;",
            "",
            "-- =======================================================",
            "-- 1. INSERT CHARACTER BASE RECORD",
            "-- =======================================================",
        ]
        
        # Insert character base record
        columns = list(character.keys())
        # Exclude 'id' from insert (auto-generated)
        columns = [col for col in columns if col != 'id']
        
        column_names = ', '.join(columns)
        values = ', '.join(format_sql_value(character[col]) for col in columns)
        
        sql_lines.extend([
            "INSERT INTO characters (",
            f"    {column_names}",
            ") VALUES (",
            f"    {values}",
            ") ON CONFLICT (normalized_name) DO UPDATE SET",
        ])
        
        # Add ON CONFLICT update clauses
        update_clauses = [f"    {col} = EXCLUDED.{col}" for col in columns if col != 'normalized_name']
        sql_lines.append(',\n'.join(update_clauses) + ';')
        sql_lines.append("")
        
        # Export each CDL table
        for table_name in CDL_TABLES:
            try:
                records = await conn.fetch(
                    f"SELECT * FROM {table_name} WHERE character_id = $1 ORDER BY id",
                    character_id
                )
            except asyncpg.UndefinedColumnError:
                # Table doesn't have character_id column, skip it
                print(f"  ⚠️  Skipping {table_name} (no character_id column)")
                continue
            except Exception as e:
                print(f"  ⚠️  Error querying {table_name}: {e}")
                continue
            
            if not records:
                continue
            
            sql_lines.extend([
                f"-- =======================================================",
                f"-- {table_name.upper().replace('_', ' ')} ({len(records)} records)",
                f"-- =======================================================",
            ])
            
            for record in records:
                record_dict = dict(record)
                columns = list(record_dict.keys())
                # Exclude 'id' and 'character_id' from insert
                columns = [col for col in columns if col not in ('id', 'character_id')]
                
                if not columns:
                    continue
                
                column_names = ', '.join(columns)
                values = ', '.join(format_sql_value(record_dict[col]) for col in columns)
                
                sql_lines.extend([
                    f"INSERT INTO {table_name} (",
                    f"    character_id, {column_names}",
                    ") VALUES (",
                    f"    (SELECT id FROM characters WHERE normalized_name = '{normalized_name}'),",
                    f"    {values}",
                    ");",
                    ""
                ])
        
        sql_lines.extend([
            "COMMIT;",
            "",
            f"-- Character '{character_name}' exported successfully!",
            ""
        ])
        
        # Write to file
        output_file = output_dir / f"insert_{normalized_name}_character.sql"
        output_file.write_text('\n'.join(sql_lines))
        
        print(f"✅ Exported to: {output_file}")
        return True


async def main():
    """Export all active characters to SQL scripts"""
    
    # Database connection
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5433')
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    
    print("=" * 60)
    print("WhisperEngine Character SQL Export Tool")
    print("=" * 60)
    print(f"Database: {db_host}:{db_port}/{db_name}")
    
    # Output directory
    output_dir = Path(__file__).parent.parent / 'sql' / 'characters'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}")
    
    # Active characters (from multi-bot system)
    active_characters = [
        'aetheris',
        'aethys',
        'dotty',
        'dream',
        'elena',
        'gabriel',
        'jake',
        'marcus',
        'nottaylor',
        'ryan',
        'sophia'
    ]
    
    # Connect to database
    pool = await asyncpg.create_pool(
        host=db_host,
        port=int(db_port),
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5
    )
    
    try:
        success_count = 0
        fail_count = 0
        
        for normalized_name in active_characters:
            try:
                if await export_character(pool, normalized_name, output_dir):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"❌ Error exporting {normalized_name}: {e}")
                fail_count += 1
        
        print("\n" + "=" * 60)
        print(f"Export complete: {success_count} successful, {fail_count} failed")
        print(f"SQL scripts saved to: {output_dir}")
        print("=" * 60)
        
    finally:
        await pool.close()


if __name__ == '__main__':
    asyncio.run(main())
