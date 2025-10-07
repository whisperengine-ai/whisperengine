"""
Enhanced JSONB CDL Manager
Simplified CDL management using PostgreSQL JSONB storage
"""

import asyncio
import asyncpg
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedJSONBCDLManager:
    """
    Enhanced CDL Manager using PostgreSQL JSONB storage.
    Provides simple, flexible character data management.
    """
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps = {}
    
    async def load_character_data(self, normalized_name: str) -> Optional[Dict[str, Any]]:
        """
        Load complete character data from database.
        Uses caching for performance.
        """
        # Check cache first
        if self._is_cached(normalized_name):
            logger.debug("Loading character from cache: %s", normalized_name)
            return self._cache[normalized_name]
        
        async with self.pool.acquire() as conn:
            # Use materialized view for fast loading
            row = await conn.fetchrow("""
                SELECT id, name, normalized_name, bot_name, archetype, 
                       allow_full_roleplay, status, version, cdl_data, 
                       workflow_data, metadata, updated_at
                FROM character_profiles_fast
                WHERE normalized_name = $1
            """, normalized_name)
            
            if not row:
                logger.warning("Character not found: %s", normalized_name)
                return None
            
            character_data = {
                "id": row["id"],
                "name": row["name"],
                "normalized_name": row["normalized_name"],
                "bot_name": row["bot_name"],
                "archetype": row["archetype"],
                "allow_full_roleplay": row["allow_full_roleplay"],
                "status": row["status"],
                "version": row["version"],
                "cdl_data": row["cdl_data"],
                "workflow_data": row["workflow_data"],
                "metadata": row["metadata"],
                "updated_at": row["updated_at"]
            }
            
            # Cache the result
            self._cache[normalized_name] = character_data
            self._cache_timestamps[normalized_name] = datetime.now()
            
            logger.info("Loaded character from database: %s", normalized_name)
            return character_data
    
    def get_cdl_field(self, character_data: Dict[str, Any], field_path: str, default=None):
        """
        Get a nested CDL field using dot notation.
        Example: get_cdl_field(char, 'personality.traits.openness')
        """
        try:
            cdl_data = character_data.get("cdl_data", {})
            path_parts = field_path.split('.')
            
            value = cdl_data
            for part in path_parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default
            
            return value if value is not None else default
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Error getting CDL field %s: %s", field_path, e)
            return default
    
    async def update_cdl_field(self, normalized_name: str, field_path: str, 
                              value: Any, change_reason: str = "manual_update") -> bool:
        """
        Update a specific CDL field using dot notation.
        """
        try:
            async with self.pool.acquire() as conn:
                # Use the stored function
                result = await conn.fetchval("""
                    SELECT upsert_character_cdl_field($1, $2, $3, $4)
                """, normalized_name, field_path, json.dumps(value), change_reason)
                
                # Invalidate cache
                self._invalidate_cache(normalized_name)
                
                logger.info("Updated CDL field %s for %s", field_path, normalized_name)
                return result
        except (asyncpg.PostgresError, json.JSONDecodeError) as e:
            logger.error("Error updating CDL field %s for %s: %s", field_path, normalized_name, e)
            return False
    
    async def get_character_workflows(self, normalized_name: str) -> Dict[str, Any]:
        """Get workflow data for a character."""
        character_data = await self.load_character_data(normalized_name)
        if not character_data:
            return {}
        
        return character_data.get("workflow_data", {})
    
    async def start_workflow(self, user_id: str, normalized_name: str, 
                           workflow_name: str, context: Dict[str, Any] = None) -> Optional[int]:
        """Start a workflow instance for a user."""
        if context is None:
            context = {}
        
        try:
            async with self.pool.acquire() as conn:
                instance_id = await conn.fetchval("""
                    SELECT start_workflow_instance($1, $2, $3, $4)
                """, user_id, normalized_name, workflow_name, json.dumps(context))
                
                logger.info("Started workflow %s for user %s with character %s", 
                           workflow_name, user_id, normalized_name)
                return instance_id
        except Exception as e:
            logger.error("Error starting workflow: %s", e)
            return None
    
    async def get_user_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active workflows for a user."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT get_user_active_workflows($1)
                """, user_id)
                
                return result if result else []
        except Exception as e:
            logger.error("Error getting user workflows: %s", e)
            return []
    
    async def import_character_from_json(self, character_json: Dict[str, Any]) -> Optional[int]:
        """Import a character from JSON structure."""
        try:
            async with self.pool.acquire() as conn:
                char_id = await conn.fetchval("""
                    SELECT import_character_from_json($1, $2)
                """, json.dumps(character_json), "json_import")
                
                # Invalidate cache
                normalized_name = character_json.get("character", {}).get("metadata", {}).get("name", "").lower().replace(" ", "_")
                self._invalidate_cache(normalized_name)
                
                logger.info("Imported character from JSON: %s", char_id)
                return char_id
        except Exception as e:
            logger.error("Error importing character from JSON: %s", e)
            return None
    
    async def list_characters(self, status: str = "active") -> List[Dict[str, Any]]:
        """List all characters with basic info."""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT name, normalized_name, bot_name, archetype, 
                           occupation, location, active_workflows_count,
                           updated_at
                    FROM character_profiles_fast
                    WHERE status = $1
                    ORDER BY name
                """, status)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Error listing characters: %s", e)
            return []
    
    async def get_character_analytics(self, normalized_name: str) -> Dict[str, Any]:
        """Get analytics data for a character."""
        try:
            async with self.pool.acquire() as conn:
                # Get workflow usage stats
                workflow_stats = await conn.fetch("""
                    SELECT workflow_name, status, COUNT(*) as count,
                           AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
                    FROM workflow_instances wi
                    JOIN characters c ON wi.character_id = c.id
                    WHERE c.normalized_name = $1
                    GROUP BY workflow_name, status
                """, normalized_name)
                
                # Get recent changes
                recent_changes = await conn.fetch("""
                    SELECT change_type, field_path, change_reason, created_at
                    FROM character_change_log ccl
                    JOIN characters c ON ccl.character_id = c.id
                    WHERE c.normalized_name = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """, normalized_name)
                
                return {
                    "workflow_stats": [dict(row) for row in workflow_stats],
                    "recent_changes": [dict(row) for row in recent_changes]
                }
        except Exception as e:
            logger.error("Error getting character analytics: %s", e)
            return {"workflow_stats": [], "recent_changes": []}
    
    def _is_cached(self, normalized_name: str) -> bool:
        """Check if character data is cached and still valid."""
        if normalized_name not in self._cache:
            return False
        
        timestamp = self._cache_timestamps.get(normalized_name)
        if not timestamp:
            return False
        
        age = (datetime.now() - timestamp).total_seconds()
        return age < self._cache_ttl
    
    def _invalidate_cache(self, normalized_name: str):
        """Invalidate cache for a character."""
        self._cache.pop(normalized_name, None)
        self._cache_timestamps.pop(normalized_name, None)
    
    def clear_cache(self):
        """Clear entire cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("CDL cache cleared")


# Factory function for creating CDL manager
def create_enhanced_jsonb_cdl_manager(db_pool) -> EnhancedJSONBCDLManager:
    """Create an Enhanced JSONB CDL Manager instance."""
    return EnhancedJSONBCDLManager(db_pool)


# Compatibility adapter for existing code
class CDLManagerAdapter:
    """
    Adapter to maintain compatibility with existing CDL manager interface.
    """
    
    def __init__(self, enhanced_manager: EnhancedJSONBCDLManager):
        self.enhanced_manager = enhanced_manager
    
    async def load_character_data(self, character_file: str) -> Optional[Dict[str, Any]]:
        """Load character data - adapted to work with normalized names."""
        # Extract normalized name from file path
        if "/" in character_file:
            filename = character_file.split("/")[-1]
        else:
            filename = character_file
        
        # Remove .json extension if present
        normalized_name = filename.replace(".json", "").lower()
        
        character_data = await self.enhanced_manager.load_character_data(normalized_name)
        if not character_data:
            return None
        
        # Return in format expected by existing code
        return character_data.get("cdl_data", {})
    
    def get_cdl_field(self, character_data: Dict[str, Any], field_path: str, default=None):
        """Get CDL field - compatible interface."""
        return self.enhanced_manager.get_cdl_field({"cdl_data": character_data}, field_path, default)


async def migrate_existing_system():
    """Example migration function for existing WhisperEngine systems."""
    
    # This would be called during system startup to migrate to new schema
    import os
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://whisperengine:your_password@localhost:5433/whisperengine')
    pool = await asyncpg.create_pool(db_url)
    
    try:
        # Create enhanced manager
        cdl_manager = create_enhanced_jsonb_cdl_manager(pool)
        
        # Test loading a character
        elena_data = await cdl_manager.load_character_data("elena")
        if elena_data:
            logger.info("Successfully loaded Elena with enhanced JSONB manager")
            
            # Test getting specific fields
            occupation = cdl_manager.get_cdl_field(elena_data, "identity.occupation")
            openness = cdl_manager.get_cdl_field(elena_data, "personality.big_five.openness.value")
            
            logger.info("Elena's occupation: %s", occupation)
            logger.info("Elena's openness score: %s", openness)
        
        # Test listing characters
        characters = await cdl_manager.list_characters()
        logger.info("Found %d active characters", len(characters))
        
    finally:
        await pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate_existing_system())