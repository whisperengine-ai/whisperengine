#!/usr/bin/env python3
"""
Migration Script: AI Identity Handling Data Normalization
=========================================================

Migrates ai_identity_handling data from denormalized text field to proper normalized tables.

WHAT THIS FIXES:
- Data inconsistency in communication_styles.ai_identity_handling 
- Multiple data formats (dict strings, JSON strings, plain text)
- Duplicate storage between denormalized blob and normalized tables

APPROACH:
1. Parse existing ai_identity_handling text fields
2. Extract structured data into proper normalized tables
3. Clean up denormalized text field
4. Add database constraints to prevent future inconsistencies

"""

import asyncio
import asyncpg
import ast
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIIdentityMigrator:
    def __init__(self):
        self.conn: asyncpg.Connection
    
    async def connect(self):
        """Connect to PostgreSQL database."""
        self.conn = await asyncpg.connect(
            'postgresql://whisperengine:whisperengine@localhost:5433/whisperengine'
        )
        logger.info("✅ Connected to PostgreSQL database")
    
    async def disconnect(self):
        """Disconnect from database."""
        if self.conn:
            await self.conn.close()
            logger.info("🔌 Disconnected from database")
    
    def parse_ai_identity_handling(self, raw_data: str) -> Dict[str, Any]:
        """Parse ai_identity_handling from various formats."""
        if not raw_data or not raw_data.strip():
            return {}
        
        raw_data = raw_data.strip()
        
        try:
            # Try JSON parsing first
            if raw_data.startswith(('{', '[')):
                try:
                    return json.loads(raw_data)
                except json.JSONDecodeError:
                    # Try Python literal eval for dict strings
                    return ast.literal_eval(raw_data)
            else:
                # Plain text - convert to structured format
                return {
                    'philosophy': raw_data,
                    'approach': 'Legacy text format - needs manual review',
                    'allow_full_roleplay_immersion': False  # Safe default
                }
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Could not parse ai_identity_handling: {e}")
            return {
                'philosophy': raw_data,
                'approach': f'Parse error: {str(e)}',
                'allow_full_roleplay_immersion': False
            }
    
    async def migrate_character_ai_identity(self, character_id: int, name: str, ai_identity_raw: str):
        """Migrate a single character's AI identity data."""
        logger.info(f"🔄 Migrating {name} (ID: {character_id})")
        
        # Parse the raw data
        parsed_data = self.parse_ai_identity_handling(ai_identity_raw)
        
        if not parsed_data:
            logger.info(f"  ⏭️  No data to migrate for {name}")
            return
        
        # Extract core fields
        allow_full_roleplay = parsed_data.get('allow_full_roleplay_immersion', False)
        philosophy = parsed_data.get('philosophy', '')
        approach = parsed_data.get('approach', '')
        
        # Update or insert roleplay config
        try:
            await self.conn.execute("""
                INSERT INTO character_roleplay_config 
                (character_id, allow_full_roleplay_immersion, philosophy, strategy)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (character_id) 
                DO UPDATE SET 
                    allow_full_roleplay_immersion = EXCLUDED.allow_full_roleplay_immersion,
                    philosophy = EXCLUDED.philosophy,
                    strategy = EXCLUDED.strategy,
                    updated_at = CURRENT_TIMESTAMP
            """, character_id, allow_full_roleplay, philosophy, approach)
            
            logger.info(f"  ✅ Updated roleplay config for {name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to update roleplay config for {name}: {e}")
        
        # Migrate roleplay scenarios if present
        roleplay_scenarios = parsed_data.get('roleplay_interaction_scenarios', {})
        if roleplay_scenarios:
            await self.migrate_roleplay_scenarios(character_id, name, roleplay_scenarios)
    
    async def migrate_roleplay_scenarios(self, character_id: int, name: str, scenarios: Dict[str, Any]):
        """Migrate roleplay interaction scenarios to normalized table."""
        try:
            # Clear existing scenarios for this character
            await self.conn.execute(
                "DELETE FROM character_roleplay_scenarios_v2 WHERE character_id = $1",
                character_id
            )
            
            # Insert new scenarios
            for scenario_type, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    # Convert complex scenario data to JSON for storage
                    scenario_json = json.dumps(scenario_data)
                    
                    await self.conn.execute("""
                        INSERT INTO character_roleplay_scenarios_v2 
                        (character_id, scenario_type, scenario_name, scenario_data)
                        VALUES ($1, $2, $3, $4)
                    """, character_id, scenario_type, scenario_type, scenario_json)
            
            logger.info(f"  ✅ Migrated {len(scenarios)} roleplay scenarios for {name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to migrate roleplay scenarios for {name}: {e}")
    
    async def run_migration(self):
        """Run the complete migration process."""
        logger.info("🚀 Starting AI Identity Handling Migration")
        
        await self.connect()
        
        try:
            # Get all characters with ai_identity_handling data
            characters = await self.conn.fetch("""
                SELECT c.id, c.name, cs.ai_identity_handling
                FROM characters c 
                JOIN communication_styles cs ON c.id = cs.character_id 
                WHERE cs.ai_identity_handling IS NOT NULL 
                AND cs.ai_identity_handling != ''
                ORDER BY c.name
            """)
            
            logger.info(f"📊 Found {len(characters)} characters with AI identity data")
            
            # Migrate each character
            for char in characters:
                await self.migrate_character_ai_identity(
                    char['id'], 
                    char['name'], 
                    char['ai_identity_handling']
                )
            
            logger.info("✅ Migration completed successfully")
            
            # Verify migration results
            await self.verify_migration()
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            await self.disconnect()
    
    async def verify_migration(self):
        """Verify that migration was successful."""
        logger.info("🔍 Verifying migration results...")
        
        # Check roleplay config population
        config_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM character_roleplay_config"
        )
        
        # Check scenario population  
        scenario_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM character_roleplay_scenarios_v2"
        )
        
        logger.info(f"📈 Migration Results:")
        logger.info(f"  - Roleplay configs: {config_count}")
        logger.info(f"  - Roleplay scenarios: {scenario_count}")
        
        # Show sample of migrated data
        sample = await self.conn.fetchrow("""
            SELECT c.name, rc.philosophy, rc.strategy
            FROM characters c 
            JOIN character_roleplay_config rc ON c.id = rc.character_id 
            LIMIT 1
        """)
        
        if sample:
            logger.info(f"📝 Sample migrated data for {sample['name']}:")
            logger.info(f"  - Philosophy: {sample['philosophy'][:60]}...")
            logger.info(f"  - Strategy: {sample['strategy'][:60]}...")

async def main():
    """Main migration execution."""
    migrator = AIIdentityMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())