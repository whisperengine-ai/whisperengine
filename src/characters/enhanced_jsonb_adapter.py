"""
Enhanced JSONB CDL Database Adapter
Adapter to integrate enhanced JSONB manager with existing CDL system
"""

import logging
import json
import asyncpg
from typing import Dict, Any, Optional

from src.characters.enhanced_jsonb_manager import create_enhanced_cdl_manager

logger = logging.getLogger(__name__)

class EnhancedJSONBCDLAdapter:
    """Adapter to use enhanced JSONB CDL manager with existing CDL integration"""
    
    def __init__(self):
        self.jsonb_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the enhanced JSONB CDL manager"""
        if self._initialized:
            return
            
        try:
            import os
            
            # Use environment variables for database connection
            postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
            postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
            postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
            postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')
            
            logger.info("Connecting to PostgreSQL: host=%s, port=%s, user=%s, db=%s", 
                       postgres_host, postgres_port, postgres_user, postgres_db)
            
            # Create PostgreSQL connection pool using environment variables
            postgres_pool = await asyncpg.create_pool(
                host=postgres_host,
                port=postgres_port,
                user=postgres_user,
                password=postgres_password,
                database=postgres_db,
                min_size=1,
                max_size=10
            )
            
            # Create enhanced JSONB manager
            self.jsonb_manager = create_enhanced_cdl_manager(postgres_pool)
            
            self._initialized = True
            logger.info("✅ Enhanced JSONB CDL adapter initialized")
            
        except (ConnectionError, ValueError) as e:
            logger.error("❌ Failed to initialize enhanced JSONB CDL adapter: %s", e)
            raise
    
    async def load_character_data(self, character_name: str) -> Optional[Dict[str, Any]]:
        """
        Load character data using enhanced JSONB manager
        Returns data in format compatible with existing CDL integration
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Map common character name variations to normalized names
            normalized_name = self._normalize_character_name(character_name)
            
            # Load from enhanced JSONB database
            if self.jsonb_manager:
                character_data = await self.jsonb_manager.get_character_data(normalized_name)
            else:
                logger.error("JSONB manager not initialized")
                return None
            
            if not character_data:
                logger.warning("Character not found: %s (normalized: %s)", character_name, normalized_name)
                return None
            
            # Extract CDL data
            cdl_data = character_data.get('cdl_data', {})
            
            # Parse JSON string if needed
            if isinstance(cdl_data, str):
                cdl_data = json.loads(cdl_data)
            
            # Return in format expected by existing CDL integration
            result = {
                'character': cdl_data,
                'metadata': character_data.get('metadata', {}),
                'workflow_data': character_data.get('workflow_data', {}),
                'active_workflows': character_data.get('active_workflows', [])
            }
            
            logger.info("✅ Loaded character data for: %s via enhanced JSONB", character_name)
            return result
            
        except (ConnectionError, ValueError, json.JSONDecodeError) as e:
            logger.error("❌ Failed to load character data for %s: %s", character_name, e)
            return None
    
    def _normalize_character_name(self, character_name: str) -> str:
        """Normalize character name - simple cleanup without hardcoded mappings"""
        # No hardcoded character mappings - use character_name as-is with basic normalization
        return character_name.lower().strip().replace(' ', '_')

# Module-level adapter instance
_jsonb_adapter = None

async def get_enhanced_jsonb_adapter() -> EnhancedJSONBCDLAdapter:
    """Get the enhanced JSONB CDL adapter"""
    global _jsonb_adapter
    if _jsonb_adapter is None:
        _jsonb_adapter = EnhancedJSONBCDLAdapter()
        await _jsonb_adapter.initialize()
    return _jsonb_adapter

# Function to load character data (backward compatible interface)
async def load_character_data(character_name: str) -> Optional[Dict[str, Any]]:
    """Load character data using enhanced JSONB system"""
    adapter = await get_enhanced_jsonb_adapter()
    return await adapter.load_character_data(character_name)