"""
Enhanced JSONB CDL Manager
Simplified character data management using PostgreSQL JSONB approach
"""

import json
import logging
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

class EnhancedJSONBCDLManager:
    """
    Enhanced CDL Manager using PostgreSQL JSONB storage
    Provides document-store flexibility with RDBMS reliability
    """
    
    def __init__(self, postgres_pool):
        self.pool = postgres_pool
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_enabled = True
        
    async def get_character_data(self, normalized_name: str) -> Optional[Dict[str, Any]]:
        """Get complete character data from JSONB storage"""
        try:
            # Check cache first
            if self._cache_enabled and normalized_name in self._cache:
                logger.debug("🎭 CACHE HIT: Retrieved %s from cache", normalized_name)
                return self._cache[normalized_name]
            
            # Query database using materialized view for performance
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT cdl_data, workflow_data, metadata, active_workflows
                    FROM character_profiles_v2 
                    WHERE normalized_name = $1
                """, normalized_name)
                
                if not result:
                    logger.warning("Character not found: %s", normalized_name)
                    return None
                
                # Combine all character data
                character_data = {
                    'cdl_data': result['cdl_data'],
                    'workflow_data': result['workflow_data'] or {},
                    'metadata': result['metadata'] or {},
                    'active_workflows': result['active_workflows'] or []
                }
                
                # Cache the result
                if self._cache_enabled:
                    self._cache[normalized_name] = character_data
                    logger.debug("🎭 CACHE STORE: Cached %s", normalized_name)
                
                logger.info("🎭 DATABASE: Loaded character %s from JSONB storage", normalized_name)
                return character_data
                
        except (ConnectionError, ValueError) as e:
            logger.error("Failed to load character %s: %s", normalized_name, e)
            return None
    
    async def upsert_character(self, character_data: Dict[str, Any]) -> Optional[int]:
        """Insert or update character using JSONB storage"""
        try:
            # Extract basic fields
            cdl_data = character_data.get('character', {})
            metadata = cdl_data.get('metadata', {})
            name = metadata.get('name')
            
            if not name:
                raise ValueError("Character name is required")
            
            normalized_name = name.lower().replace(' ', '_')
            bot_name = metadata.get('bot_name')
            archetype = character_data.get('character_archetype', 'real_world')
            
            async with self.pool.acquire() as conn:
                char_id = await conn.fetchval("""
                    SELECT upsert_character_v2($1, $2, $3, $4, $5, $6, $7)
                """, 
                    name,
                    normalized_name, 
                    bot_name,
                    archetype,
                    json.dumps(cdl_data),  # Store entire CDL as JSONB
                    json.dumps({}),        # Empty workflow data initially
                    json.dumps(metadata)   # Metadata
                )
                
                # Clear cache for this character
                if normalized_name in self._cache:
                    del self._cache[normalized_name]
                
                logger.info("🎭 UPSERT: Character %s (ID: %s) updated in JSONB storage", name, char_id)
                return char_id
                
        except (ConnectionError, ValueError) as e:
            logger.error("Failed to upsert character: %s", e)
            return None
    
    async def search_characters(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search characters using full-text search on JSONB data"""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT normalized_name, name, cdl_data->>'occupation' as occupation,
                           cdl_data->>'description' as description
                    FROM characters_v2 
                    WHERE 
                        to_tsvector('english', cdl_data::text) @@ plainto_tsquery('english', $1)
                        OR name ILIKE $2
                        OR normalized_name ILIKE $2
                    ORDER BY 
                        CASE WHEN name ILIKE $2 THEN 1 ELSE 2 END,
                        ts_rank(to_tsvector('english', cdl_data::text), plainto_tsquery('english', $1)) DESC
                    LIMIT $3
                """, query, f'%{query}%', limit)
                
                return [dict(row) for row in results]
                
        except (ConnectionError, ValueError) as e:
            logger.error("Character search failed: %s", e)
            return []


def create_enhanced_cdl_manager(postgres_pool) -> EnhancedJSONBCDLManager:
    """Factory function to create enhanced CDL manager"""
    return EnhancedJSONBCDLManager(postgres_pool)