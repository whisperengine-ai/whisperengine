#!/usr/bin/env python3
"""
Data Migration: Migrate conversation_flow_guidance JSON data to normalized RDBMS tables

This script should be run AFTER the schema migration (8b77eda62e71) has been applied.
It migrates data from JSON text fields to the new normalized table structure.

Usage:
    python alembic/data_migrations/20251013_migrate_conversation_flow_data.py

Requirements:
    - Schema migration 8b77eda62e71 must be applied first
    - All characters should have their conversation_flow_guidance data ready
    - Backup database before running this migration
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import asyncpg
from typing import Dict, List, Any, Optional


class ConversationFlowDataMigrator:
    """Migrates conversation flow guidance from JSON to normalized RDBMS tables."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        
    async def connect(self):
        """Connect to the database."""
        self.conn = await asyncpg.connect(self.database_url)
        
    async def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            
    def _ensure_connected(self):
        """Ensure database connection exists."""
        if self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
            
    async def migrate_all_characters(self) -> Dict[str, Any]:
        """Migrate all characters with conversation_flow_guidance data."""
        
        self._ensure_connected()
        
        results = {
            'characters_processed': 0,
            'modes_created': 0,
            'guidance_items_created': 0,
            'examples_created': 0,
            'errors': []
        }
        
        # Get all characters with conversation_flow_guidance data
        characters_query = """
            SELECT id, normalized_name, conversation_flow_guidance 
            FROM characters 
            WHERE conversation_flow_guidance IS NOT NULL 
            AND conversation_flow_guidance != ''
        """
        
        try:
            characters = await self.conn.fetch(characters_query)  # type: ignore
            print(f"Found {len(characters)} characters with conversation flow guidance")
            
            for character in characters:
                try:
                    result = await self.migrate_character(
                        character['id'], 
                        character['normalized_name'], 
                        character['conversation_flow_guidance']
                    )
                    
                    results['characters_processed'] += 1
                    results['modes_created'] += result['modes_created']
                    results['guidance_items_created'] += result['guidance_items_created']
                    results['examples_created'] += result['examples_created']
                    
                    print(f"✅ Migrated {character['normalized_name']}: {result['modes_created']} modes, "
                          f"{result['guidance_items_created']} guidance items, {result['examples_created']} examples")
                    
                except Exception as e:
                    error_msg = f"Error migrating {character['normalized_name']}: {e}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
                    
        except Exception as e:
            error_msg = f"Database query error: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            
        return results
    
    async def migrate_character(self, character_id: int, character_name: str, 
                              conversation_flow_guidance: str) -> Dict[str, int]:
        """Migrate a single character's conversation flow guidance."""
        
        results = {
            'modes_created': 0,
            'guidance_items_created': 0,
            'examples_created': 0
        }
        
        # Parse the conversation flow guidance JSON/dict string
        try:
            if conversation_flow_guidance.strip().startswith('{'):
                # Try JSON first
                flow_data = json.loads(conversation_flow_guidance)
            else:
                # Try Python dict string
                flow_data = eval(conversation_flow_guidance)
        except Exception as e:
            raise Exception(f"Failed to parse conversation_flow_guidance: {e}")
            
        if not isinstance(flow_data, dict):
            raise Exception(f"conversation_flow_guidance is not a dictionary: {type(flow_data)}")
            
        # Migrate conversation modes (character-specific sections)
        for mode_name, mode_data in flow_data.items():
            if mode_name in ['platform_awareness', 'flow_optimization']:
                continue  # Skip these sections for now
                
            if isinstance(mode_data, dict):
                mode_id = await self.create_conversation_mode(
                    character_id, mode_name, mode_data
                )
                results['modes_created'] += 1
                
                # Migrate guidance items (avoid/encourage)
                guidance_count = await self.create_guidance_items(mode_id, mode_data)
                results['guidance_items_created'] += guidance_count
                
                # Migrate examples
                example_count = await self.create_examples(mode_id, mode_data)
                results['examples_created'] += example_count
                
        # Migrate general conversation settings
        if 'general' in flow_data:
            await self.create_general_conversation(character_id, flow_data['general'])
            
        # Migrate response style
        if 'response_style' in flow_data:
            await self.create_response_style(character_id, flow_data['response_style'])
            
        return results
    
    async def create_conversation_mode(self, character_id: int, mode_name: str, 
                                     mode_data: Dict[str, Any]) -> int:
        """Create a conversation mode record."""
        
        self._ensure_connected()
        
        insert_query = """
            INSERT INTO character_conversation_modes 
            (character_id, mode_name, energy_level, approach, transition_style)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        energy = mode_data.get('energy', '')
        approach = mode_data.get('approach', '')
        transition = mode_data.get('transition_style', '')
        
        mode_id = await self.conn.fetchval(  # type: ignore
            insert_query, character_id, mode_name, energy, approach, transition
        )
        
        if mode_id is None:
            raise RuntimeError("Failed to create conversation mode")
            
        return mode_id
    
    async def create_guidance_items(self, mode_id: int, mode_data: Dict[str, Any]) -> int:
        """Create guidance items (avoid/encourage) for a mode."""
        
        self._ensure_connected()
        count = 0
        
        # Process 'avoid' items
        avoid_items = mode_data.get('avoid', [])
        if isinstance(avoid_items, list):
            for i, item in enumerate(avoid_items):
                await self.conn.execute("""  # type: ignore
                    INSERT INTO character_mode_guidance 
                    (mode_id, guidance_type, guidance_text, sort_order)
                    VALUES ($1, $2, $3, $4)
                """, mode_id, 'avoid', str(item), i)
                count += 1
                
        # Process 'encourage' items
        encourage_items = mode_data.get('encourage', [])
        if isinstance(encourage_items, list):
            for i, item in enumerate(encourage_items):
                await self.conn.execute("""  # type: ignore
                    INSERT INTO character_mode_guidance 
                    (mode_id, guidance_type, guidance_text, sort_order)
                    VALUES ($1, $2, $3, $4)
                """, mode_id, 'encourage', str(item), i)
                count += 1
                
        return count
    
    async def create_examples(self, mode_id: int, mode_data: Dict[str, Any]) -> int:
        """Create examples for a mode."""
        
        self._ensure_connected()
        count = 0
        examples = mode_data.get('examples', [])
        
        if isinstance(examples, list):
            for i, example in enumerate(examples):
                await self.conn.execute("""  # type: ignore
                    INSERT INTO character_mode_examples 
                    (mode_id, example_text, sort_order)
                    VALUES ($1, $2, $3)
                """, mode_id, str(example), i)
                count += 1
                
        return count
    
    async def create_general_conversation(self, character_id: int, general_data: Dict[str, Any]):
        """Create general conversation settings."""
        
        self._ensure_connected()
        
        await self.conn.execute("""  # type: ignore
            INSERT INTO character_general_conversation 
            (character_id, default_energy, conversation_style, transition_approach)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (character_id) DO UPDATE SET
                default_energy = EXCLUDED.default_energy,
                conversation_style = EXCLUDED.conversation_style,
                transition_approach = EXCLUDED.transition_approach,
                updated_at = CURRENT_TIMESTAMP
        """, 
        character_id, 
        general_data.get('default_energy', ''),
        general_data.get('conversation_style', ''),
        general_data.get('transition_approach', '')
        )
    
    async def create_response_style(self, character_id: int, response_style_data: Dict[str, Any]):
        """Create response style settings."""
        
        self._ensure_connected()
        
        # Create or get response style record
        style_id = await self.conn.fetchval("""  # type: ignore
            INSERT INTO character_response_style (character_id)
            VALUES ($1)
            ON CONFLICT (character_id) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, character_id)
        
        # Create response style items
        for item_type in ['core_principles', 'formatting_rules', 'character_specific_adaptations']:
            items = response_style_data.get(item_type, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    await self.conn.execute("""  # type: ignore
                        INSERT INTO character_response_style_items 
                        (response_style_id, item_type, item_text, sort_order)
                        VALUES ($1, $2, $3, $4)
                    """, style_id, item_type, str(item), i)


async def main():
    """Main migration function."""
    
    # Database connection URL
    database_url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'whisperengine')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5433')}/"
        f"{os.getenv('POSTGRES_DB', 'whisperengine')}"
    )
    
    print("🚀 Starting conversation flow guidance data migration")
    print(f"Database: {database_url.split('@')[1]}")  # Hide password in output
    
    migrator = ConversationFlowDataMigrator(database_url)
    
    try:
        await migrator.connect()
        print("✅ Connected to database")
        
        # Run the migration
        results = await migrator.migrate_all_characters()
        
        print("\n📊 MIGRATION RESULTS:")
        print(f"  Characters Processed: {results['characters_processed']}")
        print(f"  Conversation Modes Created: {results['modes_created']}")
        print(f"  Guidance Items Created: {results['guidance_items_created']}")
        print(f"  Examples Created: {results['examples_created']}")
        
        if results['errors']:
            print(f"  Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"    ❌ {error}")
        else:
            print("  Errors: 0")
            
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1
        
    finally:
        await migrator.disconnect()
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)