"""
Database CDL Parser
WhisperEngine Character Definition Language Database Parser

Uses enhanced JSONB system for PostgreSQL database queries.
Maintains compatibility with existing CDL integration points.
"""

from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path

# Import enhanced JSONB adapter
from src.characters.enhanced_jsonb_adapter import load_character_data as jsonb_load_character_data

logger = logging.getLogger(__name__)

class DatabaseCDLParser:
    """Database-backed CDL parser using enhanced JSONB system"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_enabled = True
    
    async def initialize(self):
        """Initialize database connection (handled by adapter)"""
        logger.info("Database CDL parser with enhanced JSONB initialized")
    
    def enable_cache(self, enabled: bool = True):
        """Enable or disable character data caching"""
        self._cache_enabled = enabled
        if not enabled:
            self._cache.clear()
    
    def clear_cache(self):
        """Clear character data cache"""
        self._cache.clear()
    
    async def load_character_data(self, character_name: str) -> Optional[Dict[str, Any]]:
        """
        Load character data from enhanced JSONB database
        
        Args:
            character_name: Name of character to load (case-insensitive)
        
        Returns:
            Character data in CDL JSON format or None if not found
        """
        try:
            # Check cache first
            if self._cache_enabled and character_name in self._cache:
                logger.debug("CDL cache hit for character: %s", character_name)
                return self._cache[character_name]
            
            # Load from enhanced JSONB database
            character_data = await jsonb_load_character_data(character_name)
            
            if character_data:
                # Cache the result
                if self._cache_enabled:
                    self._cache[character_name] = character_data
                
                logger.info("✅ Loaded character %s from enhanced JSONB database", character_name)
                return character_data
            else:
                logger.warning("❌ Character not found: %s", character_name)
                return None
                
        except Exception as e:
            logger.error("❌ Failed to load character %s: %s", character_name, e)
            return None
            
        except Exception as e:
            logger.error("❌ Failed to load character %s: %s", character_name, e)
            return None

    async def load_character_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load character by file path (compatibility method)
        
        For database-backed system, extracts character name from file path
        and loads from database instead.
        """
        try:
            # Extract character name from file path
            path = Path(file_path)
            character_name = path.stem  # filename without extension
            
            logger.debug("Loading character from path %s -> name %s", file_path, character_name)
            return await self.load_character_data(character_name)
            
        except (OSError, ValueError) as e:
            logger.error("Failed to load character file %s: %s", file_path, e)
            return None
    
    async def list_available_characters(self) -> List[Dict[str, Any]]:
        """List all available characters in database"""
        try:
            if not self.db_manager:
                await self.initialize()
            
            if self.db_manager:
                characters = await self.db_manager.list_all_characters()
                logger.info("Found %d characters in database", len(characters))
                return characters
            else:
                logger.error("Database manager not available")
                return []
            
        except (RuntimeError, OSError) as e:
            logger.error("Failed to list characters: %s", e)
            return []
    
    async def character_exists(self, character_name: str) -> bool:
        """Check if character exists in database"""
        try:
            if not self.db_manager:
                await self.initialize()
            
            if self.db_manager:
                character = await self.db_manager.get_character_by_name(character_name)
                return character is not None
            else:
                logger.error("Database manager not available")
                return False
            
        except (RuntimeError, OSError) as e:
            logger.error("Failed to check character existence %s: %s", character_name, e)
            return False
    
    async def _convert_db_to_cdl_format(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database character profile to CDL JSON format"""
        try:
            # Build CDL structure matching existing JSON format
            cdl_data = {
                "name": character_profile.get("name"),
                "bot_name": character_profile.get("bot_name"),
                "character_archetype": character_profile.get("character_archetype", "real-world"),
                "allow_full_roleplay_immersion": character_profile.get("allow_full_roleplay_immersion", False),
                
                # Identity section
                "identity": {
                    "occupation": character_profile.get("occupation"),
                    "location": character_profile.get("location"),
                    "age_range": character_profile.get("age_range"),
                    "background": character_profile.get("background"),
                    "description": character_profile.get("description")
                },
                
                # Personality section - from aggregated JSON data
                "personality": self._extract_personality_section(character_profile),
                
                # Communication section - from aggregated JSON data  
                "communication": self._extract_communication_section(character_profile),
                
                # Values section - from aggregated JSON data
                "values": self._extract_values_section(character_profile),
                
                # Behavioral guidelines - extracted from anti-patterns
                "behavioral_guidelines": await self._extract_behavioral_guidelines(character_profile),
                
                # Personal information - from knowledge data
                "personal_information": await self._extract_personal_information(character_profile),
                
                # Metadata
                "metadata": {
                    "version": character_profile.get("version", 1),
                    "created_at": character_profile.get("created_at"),
                    "updated_at": character_profile.get("updated_at"),
                    "source": "database"
                }
            }
            
            return cdl_data
            
        except Exception as e:
            logger.error("Failed to convert database profile to CDL format: %s", e)
            raise
    
    def _extract_personality_section(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personality section from database profile"""
        personality_traits = character_profile.get("personality_traits", {})
        
        personality_section = {
            "big_five_traits": {},
            "custom_traits": {}
        }
        
        # Process aggregated personality traits
        if isinstance(personality_traits, dict):
            for trait_name, trait_data in personality_traits.items():
                if isinstance(trait_data, dict):
                    trait_info = {
                        "score": trait_data.get("value"),
                        "description": trait_data.get("description"),
                        "intensity": trait_data.get("intensity", "medium")
                    }
                    
                    # Determine if this is a Big Five trait
                    big_five_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                    if trait_name.lower() in big_five_traits:
                        personality_section["big_five_traits"][trait_name] = trait_info
                    else:
                        personality_section["custom_traits"][trait_name] = trait_info
        
        return personality_section
    
    def _extract_communication_section(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract communication section from database profile"""
        communication_styles = character_profile.get("communication_styles", {})
        
        communication_section = {
            "speaking_style": {},
            "interaction_preferences": {},
            "modes": {}
        }
        
        # Process aggregated communication styles
        if isinstance(communication_styles, dict):
            for style_name, style_data in communication_styles.items():
                if isinstance(style_data, dict):
                    style_value = style_data.get("value")
                    
                    # Try to parse JSON value
                    try:
                        if isinstance(style_value, str) and style_value.startswith('{'):
                            style_value = json.loads(style_value)
                    except json.JSONDecodeError:
                        pass  # Keep as string
                    
                    # Categorize by prefix or content
                    if "speaking" in style_name.lower():
                        communication_section["speaking_style"][style_name] = style_value
                    elif "interaction" in style_name.lower() or "preference" in style_name.lower():
                        communication_section["interaction_preferences"][style_name] = style_value
                    elif "mode" in style_name.lower():
                        communication_section["modes"][style_name] = style_value
                    else:
                        # Default to speaking style
                        communication_section["speaking_style"][style_name] = style_value
        
        return communication_section
    
    def _extract_values_section(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract values section from database profile"""
        values_data = character_profile.get("values_and_beliefs", {})
        
        values_section = {
            "core_values": {},
            "beliefs": {},
            "motivations": {}
        }
        
        # Process aggregated values and beliefs
        if isinstance(values_data, dict):
            for value_name, value_data in values_data.items():
                if isinstance(value_data, dict):
                    description = value_data.get("description")
                    importance = value_data.get("importance", "medium")
                    
                    # Categorize based on importance or naming
                    if importance in ["high", "critical"] or "core" in value_name.lower():
                        values_section["core_values"][value_name] = description
                    elif "belief" in value_name.lower():
                        values_section["beliefs"][value_name] = description
                    elif "motivation" in value_name.lower() or "goal" in value_name.lower():
                        values_section["motivations"][value_name] = description
                    else:
                        # Default to core values
                        values_section["core_values"][value_name] = description
        
        return values_section
    
    async def _extract_behavioral_guidelines(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral guidelines from anti-patterns data"""
        # This would require additional database queries to get anti-patterns
        # For now, return empty structure
        # NOTE: Anti-patterns extraction pending database method extension
        _ = character_profile  # Acknowledge unused parameter
        return {
            "avoid": [],
            "conversation_limits": [],
            "personality_constraints": []
        }
    
    async def _extract_personal_information(self, character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personal information from knowledge data"""
        # This would require additional database queries to get personal knowledge
        # For now, return empty structure
        # NOTE: Personal knowledge extraction pending database method extension
        _ = character_profile  # Acknowledge unused parameter
        return {
            "family": {},
            "career": {},
            "preferences": {},
            "experiences": {}
        }

# Module-level parser instance
_database_cdl_parser: Optional[DatabaseCDLParser] = None

def get_database_cdl_parser() -> DatabaseCDLParser:
    """Get module-level database CDL parser instance"""
    global _database_cdl_parser
    if _database_cdl_parser is None:
        _database_cdl_parser = DatabaseCDLParser()
    return _database_cdl_parser

async def initialize_parser() -> DatabaseCDLParser:
    """Initialize and return database CDL parser"""
    parser = get_database_cdl_parser()
    await parser.initialize()
    return parser

# Compatibility functions for existing CDL integration points

async def load_character_data(character_name: str) -> Optional[Dict[str, Any]]:
    """Load character data from enhanced JSONB database (compatibility function)"""
    return await jsonb_load_character_data(character_name)

async def load_character_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load character by file path (compatibility function)"""
    parser = await initialize_parser()
    return await parser.load_character_file(file_path)

async def character_exists(character_name: str) -> bool:
    """Check if character exists (compatibility function)"""
    parser = await initialize_parser()
    return await parser.character_exists(character_name)