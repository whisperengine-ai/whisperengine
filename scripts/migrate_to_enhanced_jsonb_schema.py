#!/usr/bin/env python3
"""
Migration Script: Normalized CDL to Enhanced JSONB Schema
Migrates from current normalized CDL tables to simplified JSONB approach
"""

import asyncio
import asyncpg
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CDLSchemaMigration:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(self.db_url)
        logger.info("Database connection pool initialized")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def get_current_characters(self) -> List[Dict[str, Any]]:
        """Extract all character data from current normalized schema."""
        async with self.pool.acquire() as conn:
            # Get all characters with their data
            characters = []
            
            # Get basic character info
            char_rows = await conn.fetch("""
                SELECT id, name, normalized_name, bot_name, occupation, location,
                       age_range, background, description, character_archetype,
                       allow_full_roleplay_immersion, created_by, notes, version,
                       created_at, updated_at
                FROM cdl_characters
                WHERE is_active = true
            """)
            
            for char_row in char_rows:
                char_id = char_row['id']
                logger.info(f"Processing character: {char_row['name']}")
                
                # Build CDL data structure
                cdl_data = {
                    "metadata": {
                        "character_id": f"{char_row['normalized_name']}-001",
                        "name": char_row['name'],
                        "version": f"{char_row.get('version', 1)}.0.0",
                        "created_by": char_row.get('created_by', 'migration'),
                        "created_date": char_row['created_at'].isoformat() if char_row['created_at'] else None,
                        "license": "open"
                    },
                    "identity": {
                        "name": char_row['name'],
                        "occupation": char_row.get('occupation'),
                        "location": char_row.get('location'),
                        "age_range": char_row.get('age_range'),
                        "background": char_row.get('background'),
                        "description": char_row.get('description')
                    },
                    "personality": await self._get_personality_data(conn, char_id),
                    "communication": await self._get_communication_data(conn, char_id),
                    "values": await self._get_values_data(conn, char_id),
                    "behavioral_guidelines": await self._get_anti_patterns_data(conn, char_id),
                    "personal_knowledge": await self._get_personal_knowledge_data(conn, char_id)
                }
                
                character = {
                    "name": char_row['name'],
                    "normalized_name": char_row['normalized_name'],
                    "bot_name": char_row.get('bot_name'),
                    "archetype": char_row.get('character_archetype', 'real_world'),
                    "allow_full_roleplay": char_row.get('allow_full_roleplay_immersion', False),
                    "cdl_data": cdl_data,
                    "metadata": {
                        "original_id": char_id,
                        "migration_date": datetime.now().isoformat(),
                        "notes": char_row.get('notes')
                    }
                }
                
                characters.append(character)
            
            logger.info(f"Extracted {len(characters)} characters")
            return characters
    
    async def _get_personality_data(self, conn, char_id: int) -> Dict[str, Any]:
        """Extract personality traits for a character."""
        traits_rows = await conn.fetch("""
            SELECT trait_category, trait_name, trait_value, trait_description, intensity
            FROM cdl_personality_traits
            WHERE character_id = $1
        """, char_id)
        
        personality = {
            "big_five": {},
            "traits": {},
            "custom_traits": {}
        }
        
        for row in traits_rows:
            trait_data = {
                "value": float(row['trait_value']) if row['trait_value'] else None,
                "description": row['trait_description'],
                "intensity": row['intensity']
            }
            
            if row['trait_category'] == 'big_five':
                personality["big_five"][row['trait_name']] = trait_data
            else:
                personality["traits"][row['trait_name']] = trait_data
        
        return personality
    
    async def _get_communication_data(self, conn, char_id: int) -> Dict[str, Any]:
        """Extract communication styles for a character."""
        comm_rows = await conn.fetch("""
            SELECT style_category, style_name, style_value, description, priority
            FROM cdl_communication_styles
            WHERE character_id = $1
            ORDER BY priority DESC
        """, char_id)
        
        communication = {
            "speaking_style": {},
            "interaction_preferences": {},
            "modes": {},
            "patterns": {}
        }
        
        for row in comm_rows:
            style_value = row['style_value']
            
            # Try to parse JSON if it looks like JSON
            try:
                if style_value and (style_value.startswith('{') or style_value.startswith('[')):
                    style_value = json.loads(style_value)
            except json.JSONDecodeError:
                pass  # Keep as string
            
            category = row['style_category']
            if category not in communication:
                communication[category] = {}
            
            communication[category][row['style_name']] = {
                "value": style_value,
                "description": row['description'],
                "priority": row['priority']
            }
        
        return communication
    
    async def _get_values_data(self, conn, char_id: int) -> Dict[str, Any]:
        """Extract values and beliefs for a character."""
        values_rows = await conn.fetch("""
            SELECT value_category, value_name, value_description, importance_level
            FROM cdl_values
            WHERE character_id = $1
        """, char_id)
        
        values = {
            "core_values": {},
            "beliefs": {},
            "motivations": {}
        }
        
        for row in values_rows:
            category = row['value_category']
            if category not in values:
                values[category] = {}
            
            values[category][row['value_name']] = {
                "description": row['value_description'],
                "importance": row['importance_level']
            }
        
        return values
    
    async def _get_anti_patterns_data(self, conn, char_id: int) -> Dict[str, Any]:
        """Extract anti-patterns and behavioral guidelines for a character."""
        anti_rows = await conn.fetch("""
            SELECT pattern_category, pattern_name, pattern_description, severity
            FROM cdl_anti_patterns
            WHERE character_id = $1
        """, char_id)
        
        guidelines = {
            "avoid": [],
            "conversation_limits": [],
            "personality_constraints": []
        }
        
        for row in anti_rows:
            guideline = {
                "name": row['pattern_name'],
                "description": row['pattern_description'],
                "severity": row['severity']
            }
            
            category = row['pattern_category']
            if category == 'avoid_behaviors':
                guidelines["avoid"].append(guideline)
            elif category == 'conversation_limits':
                guidelines["conversation_limits"].append(guideline)
            else:
                guidelines["personality_constraints"].append(guideline)
        
        return guidelines
    
    async def _get_personal_knowledge_data(self, conn, char_id: int) -> Dict[str, Any]:
        """Extract personal knowledge for a character."""
        knowledge_rows = await conn.fetch("""
            SELECT knowledge_category, knowledge_type, knowledge_key, 
                   knowledge_value, knowledge_context, confidence_level
            FROM cdl_personal_knowledge
            WHERE character_id = $1
        """, char_id)
        
        knowledge = {}
        
        for row in knowledge_rows:
            category = row['knowledge_category']
            if category not in knowledge:
                knowledge[category] = {}
            
            knowledge[category][row['knowledge_key']] = {
                "value": row['knowledge_value'],
                "type": row['knowledge_type'],
                "context": row['knowledge_context'],
                "confidence": float(row['confidence_level']) if row['confidence_level'] else 1.0
            }
        
        return knowledge
    
    async def apply_new_schema(self):
        """Apply the new enhanced JSONB schema."""
        async with self.pool.acquire() as conn:
            # Read and execute the new schema
            schema_path = Path(__file__).parent / "002_enhanced_jsonb_cdl_schema.sql"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            logger.info("Applying new enhanced JSONB schema...")
            await conn.execute(schema_sql)
            logger.info("New schema applied successfully")
    
    async def migrate_characters(self, characters: List[Dict[str, Any]]):
        """Migrate characters to new JSONB schema."""
        async with self.pool.acquire() as conn:
            logger.info(f"Migrating {len(characters)} characters to new schema...")
            
            for char in characters:
                logger.info(f"Migrating character: {char['name']}")
                
                # Insert character with JSONB data
                await conn.execute("""
                    INSERT INTO characters (
                        name, normalized_name, bot_name, archetype, allow_full_roleplay,
                        cdl_data, metadata, created_by, status
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (normalized_name) 
                    DO UPDATE SET
                        cdl_data = EXCLUDED.cdl_data,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """, 
                    char['name'],
                    char['normalized_name'],
                    char.get('bot_name'),
                    char.get('archetype', 'real_world'),
                    char.get('allow_full_roleplay', False),
                    json.dumps(char['cdl_data']),  # Convert to JSON string
                    json.dumps(char['metadata']),
                    'migration_script',
                    'active'
                )
            
            logger.info("Character migration completed")
    
    async def verify_migration(self):
        """Verify the migration was successful."""
        async with self.pool.acquire() as conn:
            # Count characters in new schema
            new_count = await conn.fetchval("SELECT COUNT(*) FROM characters WHERE status = 'active'")
            logger.info(f"Characters in new schema: {new_count}")
            
            # Sample a character to verify structure
            sample = await conn.fetchrow("""
                SELECT name, normalized_name, cdl_data->'personality'->'big_five' as big_five_traits
                FROM characters 
                WHERE status = 'active' 
                LIMIT 1
            """)
            
            if sample:
                logger.info(f"Sample character: {sample['name']}")
                logger.info(f"Big Five traits found: {bool(sample['big_five_traits'])}")
            
            # Verify materialized view
            await conn.execute("REFRESH MATERIALIZED VIEW character_profiles_fast")
            view_count = await conn.fetchval("SELECT COUNT(*) FROM character_profiles_fast")
            logger.info(f"Characters in materialized view: {view_count}")
    
    async def backup_old_schema(self):
        """Create backup of old schema data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"cdl_migration_backup_{timestamp}.json"
        
        characters = await self.get_current_characters()
        
        backup_data = {
            "migration_timestamp": timestamp,
            "source_schema": "normalized_cdl",
            "target_schema": "enhanced_jsonb",
            "character_count": len(characters),
            "characters": characters
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        logger.info(f"Backup created: {backup_file}")
        return backup_file

async def main():
    """Main migration function."""
    import os
    
    # Database connection
    db_url = os.getenv('DATABASE_URL', 'postgresql://whisperengine:your_password@localhost:5433/whisperengine')
    
    migration = CDLSchemaMigration(db_url)
    
    try:
        await migration.initialize()
        
        logger.info("Starting CDL schema migration...")
        
        # Step 1: Backup old data
        backup_file = await migration.backup_old_schema()
        
        # Step 2: Extract current character data
        characters = await migration.get_current_characters()
        
        # Step 3: Apply new schema
        await migration.apply_new_schema()
        
        # Step 4: Migrate characters
        await migration.migrate_characters(characters)
        
        # Step 5: Verify migration
        await migration.verify_migration()
        
        logger.info("Migration completed successfully!")
        logger.info(f"Backup file: {backup_file}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await migration.close()

if __name__ == "__main__":
    asyncio.run(main())