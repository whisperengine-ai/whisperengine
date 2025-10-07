"""
CDL Database Connection and Utilities
WhisperEngine Character Definition Language Database Management

Provides PostgreSQL connection utilities specifically for CDL operations.
"""

import os
import asyncpg
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

class CDLDatabaseManager:
    """Database connection manager for CDL operations"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = self._get_database_url()
    
    def _get_database_url(self) -> str:
        """Get PostgreSQL connection URL from environment"""
        # Use WhisperEngine's existing PostgreSQL configuration
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5433')
        database = os.getenv('POSTGRES_DB', 'whisperengine')
        user = os.getenv('POSTGRES_USER', 'whisperengine')
        password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60
            )
            logger.info("CDL database pool initialized successfully")
        except (asyncpg.PostgresError, OSError) as e:
            logger.error("Failed to initialize CDL database pool: %s", e)
            raise
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("CDL database pool closed")
    
    async def execute_migration(self, migration_file: str):
        """Execute a SQL migration file"""
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute(sql_content)
                logger.info("Migration %s executed successfully", migration_file)
        except (OSError, RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Migration %s failed: %s", migration_file, e)
            raise
    
    async def check_schema_exists(self) -> bool:
        """Check if CDL schema tables exist"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'cdl_characters'
                    );
                """)
                return result
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error checking CDL schema: %s", e)
            return False
    
    async def get_character_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get character by normalized name"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM cdl_character_profiles 
                    WHERE normalized_name = $1
                """, name.lower())
                
                if row:
                    result = dict(row)
                    
                    # Parse JSON fields that come as strings from the view
                    json_fields = ['personality_traits', 'communication_styles', 'values_and_beliefs']
                    
                    for field in json_fields:
                        if field in result and isinstance(result[field], str):
                            try:
                                if result[field].strip():  # Check if not empty
                                    result[field] = json.loads(result[field])
                                else:
                                    result[field] = {}
                            except json.JSONDecodeError as e:
                                logger.warning("Failed to parse JSON field %s: %s", field, e)
                                result[field] = {}
                    
                    return result
                return None
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error fetching character %s: %s", name, e)
            return None
    
    async def list_all_characters(self) -> List[Dict[str, Any]]:
        """List all active characters"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, name, normalized_name, bot_name, occupation, 
                           character_archetype, created_at, updated_at
                    FROM cdl_characters 
                    WHERE is_active = true
                    ORDER BY name
                """)
                
                return [dict(row) for row in rows]
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error listing characters: %s", e)
            return []
    
    async def create_character(self, character_data: Dict[str, Any]) -> int:
        """Create new character and return ID"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                character_id = await conn.fetchval("""
                    INSERT INTO cdl_characters (
                        name, normalized_name, bot_name, occupation, location,
                        age_range, background, description, character_archetype,
                        allow_full_roleplay_immersion, created_by, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """, 
                    character_data.get('name'),
                    character_data.get('name', '').lower(),
                    character_data.get('bot_name'),
                    character_data.get('occupation'),
                    character_data.get('location'),
                    character_data.get('age_range'),
                    character_data.get('background'),
                    character_data.get('description'),
                    character_data.get('character_archetype', 'real-world'),
                    character_data.get('allow_full_roleplay_immersion', False),
                    character_data.get('created_by', 'system'),
                    character_data.get('notes')
                )
                
                logger.info("Created character %s with ID %s", 
                           character_data.get('name'), character_id)
                return character_id
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error creating character: %s", e)
            raise
    
    async def update_character(self, character_id: int, updates: Dict[str, Any]) -> bool:
        """Update character data"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            # Build dynamic update query
            update_fields = []
            values = []
            param_index = 1
            
            for field, value in updates.items():
                if field not in ['id', 'created_at', 'updated_at']:
                    update_fields.append(f"{field} = ${param_index}")
                    values.append(value)
                    param_index += 1
            
            if not update_fields:
                return False
            
            query = f"""
                UPDATE cdl_characters 
                SET {', '.join(update_fields)}
                WHERE id = ${param_index}
            """
            values.append(character_id)
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *values)
                success = result.split()[-1] == '1'  # Check if one row was updated
                
                if success:
                    logger.info("Updated character ID %s", character_id)
                return success
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error updating character %s: %s", character_id, e)
            return False
    
    async def add_personality_trait(self, character_id: int, trait_data: Dict[str, Any]) -> bool:
        """Add personality trait to character"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_personality_traits (
                        character_id, trait_category, trait_name, trait_value,
                        trait_description, intensity
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (character_id, trait_category, trait_name)
                    DO UPDATE SET 
                        trait_value = EXCLUDED.trait_value,
                        trait_description = EXCLUDED.trait_description,
                        intensity = EXCLUDED.intensity
                """, 
                    character_id,
                    trait_data.get('category', 'custom'),
                    trait_data.get('name'),
                    trait_data.get('value'),
                    trait_data.get('description'),
                    trait_data.get('intensity', 'medium')
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error adding personality trait: %s", e)
            return False
    
    async def log_character_evolution(self, character_id: int, change_data: Dict[str, Any]) -> bool:
        """Log character evolution/change"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_evolution_history (
                        character_id, change_type, change_description,
                        old_value, new_value, change_reason, changed_by,
                        performance_metrics
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    character_id,
                    change_data.get('change_type'),
                    change_data.get('description'),
                    json.dumps(change_data.get('old_value')) if change_data.get('old_value') else None,
                    json.dumps(change_data.get('new_value')) if change_data.get('new_value') else None,
                    change_data.get('reason'),
                    change_data.get('changed_by', 'system'),
                    json.dumps(change_data.get('metrics')) if change_data.get('metrics') else None
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error logging character evolution: %s", e)
            return False
    
    async def add_communication_style(self, character_id: int, style_data: Dict[str, Any]) -> bool:
        """Add communication style to character"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_communication_styles (
                        character_id, style_category, style_name, style_value, 
                        description, priority
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    character_id,
                    style_data.get('category'),
                    style_data.get('name'),
                    style_data.get('value'),
                    style_data.get('description'),
                    style_data.get('priority', 0)
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error adding communication style: %s", e)
            return False
    
    async def add_value(self, character_id: int, value_data: Dict[str, Any]) -> bool:
        """Add value/belief to character"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_values (
                        character_id, value_category, value_name, value_description, 
                        importance_level
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    character_id,
                    value_data.get('category'),
                    value_data.get('name'),
                    value_data.get('description'),
                    value_data.get('importance_level', 'medium')
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error adding value: %s", e)
            return False
    
    async def add_anti_pattern(self, character_id: int, pattern_data: Dict[str, Any]) -> bool:
        """Add anti-pattern to character"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_anti_patterns (
                        character_id, pattern_category, pattern_name, pattern_description, 
                        severity
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    character_id,
                    pattern_data.get('category'),
                    pattern_data.get('name'),
                    pattern_data.get('description'),
                    pattern_data.get('severity', 'medium')
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error adding anti-pattern: %s", e)
            return False
    
    async def add_personal_knowledge(self, character_id: int, knowledge_data: Dict[str, Any]) -> bool:
        """Add personal knowledge to character"""
        try:
            if self.pool is None:
                raise RuntimeError("Database pool not initialized")
                
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cdl_personal_knowledge (
                        character_id, knowledge_category, knowledge_type, knowledge_key, 
                        knowledge_value, knowledge_context, confidence_level, is_public
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    character_id,
                    knowledge_data.get('category'),
                    knowledge_data.get('type'),
                    knowledge_data.get('key'),
                    knowledge_data.get('value'),
                    knowledge_data.get('context'),
                    knowledge_data.get('confidence_level', 1.0),
                    knowledge_data.get('is_public', True)
                )
                return True
        except (RuntimeError, asyncpg.PostgresError) as e:
            logger.error("Error adding personal knowledge: %s", e)
            return False

# Global CDL database manager instance
cdl_db_manager = CDLDatabaseManager()

async def get_cdl_database() -> CDLDatabaseManager:
    """Get CDL database manager instance"""
    if not cdl_db_manager.pool:
        await cdl_db_manager.initialize_pool()
    return cdl_db_manager

async def close_cdl_database():
    """Close CDL database connections"""
    await cdl_db_manager.close_pool()