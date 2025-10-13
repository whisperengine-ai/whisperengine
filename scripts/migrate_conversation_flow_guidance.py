#!/usr/bin/env python3
"""
Migration Script: Extract conversation_flow_guidance JSON to normalized RDBMS tables
Converts JSON text fields to clean relational structure for web UI editing.

Usage:
    python migrate_conversation_flow_guidance.py [--dry-run] [--character=name]
"""

import asyncio
import asyncpg
import ast
import json
import argparse
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationFlowMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            'characters_processed': 0,
            'modes_created': 0,
            'guidance_items_created': 0,
            'examples_created': 0,
            'errors': 0
        }
    
    async def connect_db(self):
        """Connect to WhisperEngine database."""
        return await asyncpg.connect(
            host='localhost',
            port=5433,
            user='whisperengine',
            password='whisperengine',
            database='whisperengine'
        )
    
    async def parse_json_safely(self, json_str: str) -> Optional[Dict]:
        """Safely parse JSON or Python dict strings."""
        if not json_str or json_str.strip() == '':
            return None
            
        try:
            # Try JSON first
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                # Fall back to Python dict string
                return ast.literal_eval(json_str)
            except (ValueError, SyntaxError) as e:
                logger.error(f"Could not parse JSON/dict string: {e}")
                logger.error(f"Content: {json_str[:200]}...")
                return None
    
    async def migrate_character_modes(self, conn, character_id: int, character_name: str, data: Dict):
        """Migrate character conversation modes from JSON to tables."""
        modes_created = 0
        
        for mode_name, mode_data in data.items():
            # Skip standard sections - they go to different tables
            if mode_name in ['general', 'response_style']:
                continue
                
            if not isinstance(mode_data, dict):
                continue
                
            # Insert conversation mode
            if not self.dry_run:
                mode_id = await conn.fetchval("""
                    INSERT INTO character_conversation_modes 
                    (character_id, mode_name, energy_level, approach, transition_style)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (character_id, mode_name) DO UPDATE SET
                        energy_level = EXCLUDED.energy_level,
                        approach = EXCLUDED.approach,
                        transition_style = EXCLUDED.transition_style,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, character_id, mode_name, 
                    mode_data.get('energy', ''),
                    mode_data.get('approach', ''),
                    mode_data.get('transition_style', ''))
            else:
                logger.info(f"  [DRY RUN] Would create mode: {mode_name}")
                mode_id = 999  # Fake ID for dry run
            
            modes_created += 1
            
            # Migrate guidance items (avoid/encourage arrays)
            for guidance_type in ['avoid', 'encourage']:
                items = mode_data.get(guidance_type, [])
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        if not self.dry_run:
                            await conn.execute("""
                                INSERT INTO character_mode_guidance 
                                (mode_id, guidance_type, guidance_text, sort_order)
                                VALUES ($1, $2, $3, $4)
                            """, mode_id, guidance_type, str(item), i)
                        else:
                            logger.info(f"    [DRY RUN] Would add {guidance_type}: {str(item)[:50]}...")
                        self.stats['guidance_items_created'] += 1
            
            # Migrate examples
            examples = mode_data.get('examples', [])
            if isinstance(examples, list):
                for i, example in enumerate(examples):
                    if not self.dry_run:
                        await conn.execute("""
                            INSERT INTO character_mode_examples 
                            (mode_id, example_text, sort_order)
                            VALUES ($1, $2, $3)
                        """, mode_id, str(example), i)
                    else:
                        logger.info(f"    [DRY RUN] Would add example: {str(example)[:50]}...")
                    self.stats['examples_created'] += 1
        
        self.stats['modes_created'] += modes_created
        return modes_created
    
    async def migrate_general_settings(self, conn, character_id: int, general_data: Dict):
        """Migrate general conversation settings."""
        if not self.dry_run:
            await conn.execute("""
                INSERT INTO character_general_conversation 
                (character_id, default_energy, conversation_style, transition_approach)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (character_id) DO UPDATE SET
                    default_energy = EXCLUDED.default_energy,
                    conversation_style = EXCLUDED.conversation_style,
                    transition_approach = EXCLUDED.transition_approach,
                    updated_at = CURRENT_TIMESTAMP
            """, character_id,
                general_data.get('default_energy', ''),
                general_data.get('conversation_style', ''),
                general_data.get('transition_approach', ''))
        else:
            logger.info(f"  [DRY RUN] Would create general settings")
    
    async def migrate_response_style(self, conn, character_id: int, response_data: Dict):
        """Migrate response style settings."""
        if not self.dry_run:
            style_id = await conn.fetchval("""
                INSERT INTO character_response_style (character_id)
                VALUES ($1)
                ON CONFLICT (character_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, character_id)
        else:
            logger.info(f"  [DRY RUN] Would create response style")
            style_id = 999
        
        # Migrate response style items
        for item_type in ['core_principles', 'formatting_rules', 'character_specific_adaptations']:
            items = response_data.get(item_type, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if not self.dry_run:
                        await conn.execute("""
                            INSERT INTO character_response_style_items 
                            (response_style_id, item_type, item_text, sort_order)
                            VALUES ($1, $2, $3, $4)
                        """, style_id, item_type, str(item), i)
                    else:
                        logger.info(f"    [DRY RUN] Would add {item_type}: {str(item)[:50]}...")
    
    async def migrate_character(self, conn, character_name: str = None):
        """Migrate conversation flow guidance for specific character or all characters."""
        
        # Build query based on character filter
        if character_name:
            query = """
                SELECT c.id, c.normalized_name, cs.conversation_flow_guidance 
                FROM characters c 
                JOIN communication_styles cs ON c.id = cs.character_id 
                WHERE c.normalized_name = $1 AND cs.conversation_flow_guidance IS NOT NULL
            """
            rows = await conn.fetch(query, character_name)
        else:
            query = """
                SELECT c.id, c.normalized_name, cs.conversation_flow_guidance 
                FROM characters c 
                JOIN communication_styles cs ON c.id = cs.character_id 
                WHERE cs.conversation_flow_guidance IS NOT NULL
            """
            rows = await conn.fetch(query)
        
        logger.info(f"Found {len(rows)} characters with conversation flow guidance")
        
        for row in rows:
            character_id = row['id']
            name = row['normalized_name']
            json_data = row['conversation_flow_guidance']
            
            logger.info(f"\n--- Migrating {name.upper()} ---")
            
            try:
                # Parse JSON data
                data = await self.parse_json_safely(str(json_data))
                if not data:
                    logger.error(f"Could not parse data for {name}")
                    self.stats['errors'] += 1
                    continue
                
                # Migrate conversation modes
                modes_count = await self.migrate_character_modes(conn, character_id, name, data)
                logger.info(f"  Created {modes_count} conversation modes")
                
                # Migrate general settings
                if 'general' in data:
                    await self.migrate_general_settings(conn, character_id, data['general'])
                    logger.info(f"  Migrated general settings")
                
                # Migrate response style
                if 'response_style' in data:
                    await self.migrate_response_style(conn, character_id, data['response_style'])
                    logger.info(f"  Migrated response style")
                
                self.stats['characters_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error migrating {name}: {e}")
                self.stats['errors'] += 1
    
    async def run_migration(self, character_name: str = None):
        """Run the complete migration process."""
        logger.info("🚀 Starting conversation flow guidance migration")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        
        conn = await self.connect_db()
        
        try:
            # Run the migration
            await self.migrate_character(conn, character_name)
            
            # Print statistics
            logger.info("\n📊 MIGRATION STATISTICS:")
            for key, value in self.stats.items():
                logger.info(f"  {key.replace('_', ' ').title()}: {value}")
                
        finally:
            await conn.close()

async def main():
    parser = argparse.ArgumentParser(description='Migrate conversation flow guidance from JSON to RDBMS')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    parser.add_argument('--character', help='Migrate specific character only')
    
    args = parser.parse_args()
    
    migrator = ConversationFlowMigrator(dry_run=args.dry_run)
    await migrator.run_migration(args.character)

if __name__ == '__main__':
    asyncio.run(main())