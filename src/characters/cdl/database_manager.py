"""
CDL Database Manager - PostgreSQL-backed character data management
Provides synchronous interface to database-backed CDL system for backward compatibility.
"""

import asyncio
import logging
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.characters.database_cdl_parser import DatabaseCDLParser, load_character_data
from src.memory.vector_memory_system import get_normalized_bot_name_from_env

logger = logging.getLogger(__name__)


@dataclass
class CDLFieldAccess:
    """Represents the result of accessing a CDL field"""
    value: Any
    exists: bool
    path: str


class DatabaseCDLManager:
    """
    Database-backed CDL Manager for character data.
    
    This replaces the file-based CDL Manager with database integration,
    providing a synchronous interface to async database operations.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._data: Optional[Dict[str, Any]] = None
        self._loaded = False
        self._character_name: Optional[str] = None
        self._character_object = None
    
    def _get_character_name(self) -> str:
        """
        Get character name from environment configuration.
        
        Uses bot name from environment to determine which character to load.
        """
        if self._character_name is None:
            # Get bot name from environment and map to character
            bot_name = get_normalized_bot_name_from_env()
            
            # For now, use bot name directly as character name
            # This can be enhanced later with explicit character mapping
            self._character_name = bot_name.lower()
            
            logger.info("Determined character name: %s from bot: %s", self._character_name, bot_name)
        
        return self._character_name
    
    def _run_async(self, coro):
        """Helper to run async functions in sync context"""
        try:
            # Check if we're already in an event loop
            try:
                asyncio.get_running_loop()
                # We're in an async context - use thread pool
                logger.warning("CDL Manager called from async context - using thread pool")
                import concurrent.futures
                
                def run_in_thread():
                    return asyncio.run(coro)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=10)  # 10 second timeout
                    
            except RuntimeError:
                # No event loop, we can run directly
                return asyncio.run(coro)
                
        except Exception as e:
            logger.error("Error running async operation: %s", e)
            return None
    
    def _load_character_data(self) -> None:
        """Load character data from database (synchronous wrapper)"""
        if self._loaded:
            return
        
        with self._lock:
            if self._loaded:  # Double-check locking
                return
                
            try:
                character_name = self._get_character_name()
                
                # Use the async function with sync wrapper
                self._data = self._run_async(load_character_data(character_name))
                
                if self._data:
                    logger.info("✅ CDL Database Manager: Loaded character data for: %s", character_name)
                else:
                    logger.warning("❌ CDL Database Manager: No character data found for: %s", character_name)
                    self._data = {}
                    
                # Basic schema validation
                self._validate_schema()
                
            except Exception as e:
                logger.error("❌ CDL Database Manager: Error loading character data: %s", e)
                self._data = {}
            finally:
                self._loaded = True
    
    def _validate_schema(self) -> None:
        """Basic schema validation for CDL structure"""
        if not isinstance(self._data, dict):
            raise ValueError("CDL data must be a dictionary")
        
        # Database parser returns data at root level (no 'character' wrapper)
        # Check for expected root-level keys
        expected_keys = ['name', 'identity', 'personality']
        found_keys = [key for key in expected_keys if key in self._data]
        
        if not found_keys:
            logger.warning("CDL data missing expected root keys: %s", expected_keys)
        else:
            logger.debug("CDL data has expected keys: %s", found_keys)
        
        # Validate identity if present
        if 'identity' in self._data:
            identity = self._data['identity']
            if not isinstance(identity, dict):
                logger.warning("CDL identity is not a dictionary")
            elif 'name' not in identity:
                logger.warning("CDL identity missing 'name' field")
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get a field value using dot notation path.
        
        Args:
            field_path: Dot-separated path like "character.metadata.name"
            default: Default value if field doesn't exist
            
        Returns:
            Field value or default
        """
        self._load_character_data()
        
        if not self._data:
            return default
        
        try:
            current = self._data
            parts = field_path.split('.')
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
            
        except Exception as e:
            logger.debug("Error accessing field '%s': %s", field_path, e)
            return default
    
    def get_field_with_metadata(self, field_path: str, default: Any = None) -> CDLFieldAccess:
        """
        Get field value with access metadata.
        
        Returns:
            CDLFieldAccess object with value, exists flag, and path
        """
        self._load_character_data()
        
        if not self._data:
            return CDLFieldAccess(value=default, exists=False, path=field_path)
        
        try:
            current = self._data
            parts = field_path.split('.')
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return CDLFieldAccess(value=default, exists=False, path=field_path)
            
            return CDLFieldAccess(value=current, exists=True, path=field_path)
            
        except Exception as e:
            logger.debug("Error accessing field '%s': %s", field_path, e)
            return CDLFieldAccess(value=default, exists=False, path=field_path)
    
    def has_field(self, field_path: str) -> bool:
        """Check if a field exists in the CDL data"""
        return self.get_field_with_metadata(field_path).exists
    
    def get_character_name(self) -> str:
        """Convenience method to get character name"""
        # Database structure: name at root level or identity.name
        name = self.get_field("name", default=None)
        if name:
            return name
        return self.get_field("identity.name", default="Unknown")
    
    def get_character_occupation(self) -> str:
        """Convenience method to get character occupation"""
        # Database structure: identity.occupation
        return self.get_field("identity.occupation", default="")
    
    def get_conversation_flow_guidelines(self) -> Dict[str, Any]:
        """Convenience method to get conversation flow guidelines"""
        return self.get_field("communication.conversation_flow_guidance", {})
    
    def get_response_style(self) -> Dict[str, Any]:
        """Convenience method to get response_style"""
        guidelines = self.get_field("communication.conversation_flow_guidance", {})
        return guidelines.get('response_style', {})
    
    def get_communication_style(self) -> Dict[str, Any]:
        """Convenience method to get communication style"""
        return self.get_field("identity.communication_style", default={})
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """Convenience method to get personality traits"""
        return self.get_field("personality", default={})
    
    def get_ai_identity_handling(self) -> Dict[str, Any]:
        """Convenience method to get AI identity handling"""
        return self.get_field("identity.communication_style.ai_identity_handling", default={})
    
    def reload(self) -> None:
        """Force reload of character data (for development/testing)"""
        with self._lock:
            self._loaded = False
            self._data = None
            self._character_object = None
        self._load_character_data()
        logger.info("🔄 CDL Database Manager: Reloaded character data")
    
    def get_character_object(self):
        """
        Get Character object from database data.
        Converts database CDL data into a Character object for API compatibility.
        Reconstructs complete CDL structure from normalized database tables.
        """
        if self._character_object is not None:
            return self._character_object
            
        try:
            # Load base character data
            self._load_character_data()
            
            if not self._data:
                logger.warning("No character data loaded for character object creation")
                return None
            
            # Import Character classes
            from src.characters.models.character import (
                Character,
                CharacterIdentity,
                CharacterPersonality,
                CharacterMetadata,
                CharacterBackstory,
                CharacterCurrentLife,
                CharacterCommunication,
                BigFivePersonality
            )
            
            # Reconstruct complete CDL structure from database tables
            reconstructed_data = self._reconstruct_complete_cdl_structure()
            
            # Extract basic identity information
            identity_data = reconstructed_data.get('identity', {})
            name = reconstructed_data.get('name', 'Unknown')
            
            # Create BigFive personality object
            personality_data = reconstructed_data.get('personality', {})
            big_five_data = personality_data.get('big_five', {})
            
            big_five = BigFivePersonality(
                openness=big_five_data.get('openness', 0.5),
                conscientiousness=big_five_data.get('conscientiousness', 0.5),
                extraversion=big_five_data.get('extraversion', 0.5),
                agreeableness=big_five_data.get('agreeableness', 0.5),
                neuroticism=big_five_data.get('neuroticism', 0.5)
            )
            
            # Create identity object
            identity = CharacterIdentity(
                name=name,
                occupation=identity_data.get('occupation', ''),
                location=identity_data.get('location', ''),
                description=identity_data.get('description', '')
            )
            
            # Create personality object with reconstructed data
            personality = CharacterPersonality(
                big_five=big_five,
                custom_traits=personality_data.get('custom_traits', {}),
                values=personality_data.get('values', []),
                core_beliefs=personality_data.get('core_beliefs', [])
            )
            
            # Create communication object with reconstructed data
            communication_data = reconstructed_data.get('communication', {})
            communication = CharacterCommunication(
                speaking_style=communication_data.get('speaking_style', {}),
                interaction_preferences=communication_data.get('interaction_preferences', {}),
                typical_responses=communication_data.get('typical_responses', {})
            )
            
            # Create metadata
            metadata = CharacterMetadata(
                created_by=self._data.get('created_by', 'database'),
                version=str(self._data.get('version', '1.0')),
                description=f"Database CDL character: {name}"
            )
            
            # Create Character object with complete reconstructed data
            self._character_object = Character(
                identity=identity,
                personality=personality,
                communication=communication,
                metadata=metadata,
                data=reconstructed_data  # Include complete reconstructed CDL structure
            )
            
            logger.info("✅ Created Character object from database with complete CDL structure")
            return self._character_object
            
        except Exception as e:
            logger.error("Failed to create Character object from database: %s", e)
            return None
    
    def _reconstruct_complete_cdl_structure(self) -> Dict[str, Any]:
        """
        Reconstruct complete CDL JSON structure from normalized database tables.
        This enables full compatibility with existing CDL AI integration.
        """
        try:
            character_name = self.get_character_name()
            
            # Start with base character data
            reconstructed = {
                'name': self._data.get('name'),
                'identity': {
                    'name': self._data.get('name'),
                    'occupation': self._data.get('occupation'),
                    'location': self._data.get('location'),
                    'description': self._data.get('description'),
                    'voice': {
                        'favorite_phrases': []
                    },
                    'digital_communication': {
                        'emoji_personality': {},
                        'emoji_usage_patterns': {}
                    }
                },
                'personality': {
                    'big_five': {},
                    'custom_traits': {},
                    'values': [],
                    'core_beliefs': [],
                    'dreams': [],
                    'fears': [],
                    'quirks': [],
                    'communication_style': {
                        'language_patterns': {},
                        'interaction_preferences': {},
                        'emotional_expression': {}
                    }
                },
                'speech_patterns': {
                    'vocabulary': {
                        'preferred_words': [],
                        'avoided_words': []
                    }
                },
                'communication': {
                    'typical_responses': {},
                    'ai_identity_handling': {}
                },
                'personal': {
                    'relationships': {},
                    'career': {},
                    'current_focus': [],
                    'social_circle': []
                }
            }
            
            # Reconstruct personality traits
            self._reconstruct_personality_traits(reconstructed)
            
            # Reconstruct communication styles
            self._reconstruct_communication_styles(reconstructed)
            
            # Reconstruct values and beliefs
            self._reconstruct_values(reconstructed)
            
            # Reconstruct personal knowledge
            self._reconstruct_personal_knowledge(reconstructed)
            
            logger.info("🔄 Reconstructed complete CDL structure from database tables")
            return reconstructed
            
        except Exception as e:
            logger.error("Failed to reconstruct CDL structure: %s", e)
            return self._data  # Fallback to original data
    
    def _reconstruct_personality_traits(self, reconstructed: Dict[str, Any]):
        """Reconstruct personality traits from database"""
        try:
            # This would require a database query to get traits for current character
            # For now, use existing data structure
            if 'personality_traits' in self._data:
                traits = self._data['personality_traits']
                
                # Separate Big Five from custom traits
                for trait in traits:
                    if trait.get('trait_category') == 'big_five':
                        reconstructed['personality']['big_five'][trait['trait_name']] = trait.get('trait_value', 0.5)
                    elif trait.get('trait_category') == 'custom':
                        reconstructed['personality']['custom_traits'][trait['trait_name']] = trait.get('trait_value', 0.5)
                        
        except Exception as e:
            logger.debug("Error reconstructing personality traits: %s", e)
    
    def _reconstruct_communication_styles(self, reconstructed: Dict[str, Any]):
        """Reconstruct communication styles from database"""
        try:
            if 'communication_styles' in self._data:
                styles = self._data['communication_styles']
                
                for style in styles:
                    category = style.get('style_category', '')
                    name = style.get('style_name', '')
                    value = style.get('style_value', '')
                    
                    if category == 'favorite_phrases':
                        reconstructed['identity']['voice']['favorite_phrases'].append(value)
                    elif category == 'vocabulary' and name == 'preferred_words':
                        try:
                            import json
                            words = json.loads(value) if isinstance(value, str) else value
                            if isinstance(words, list):
                                reconstructed['speech_patterns']['vocabulary']['preferred_words'] = words
                        except:
                            pass
                    elif category == 'vocabulary' and name == 'avoided_words':
                        try:
                            import json
                            words = json.loads(value) if isinstance(value, str) else value
                            if isinstance(words, list):
                                reconstructed['speech_patterns']['vocabulary']['avoided_words'] = words
                        except:
                            pass
                    elif category == 'typical_responses':
                        try:
                            import json
                            responses = json.loads(value) if isinstance(value, str) else value
                            reconstructed['communication']['typical_responses'][name] = responses
                        except:
                            reconstructed['communication']['typical_responses'][name] = value
                            
        except Exception as e:
            logger.debug("Error reconstructing communication styles: %s", e)
    
    def _reconstruct_values(self, reconstructed: Dict[str, Any]):
        """Reconstruct values and beliefs from database"""
        try:
            if 'values' in self._data:
                values = self._data['values']
                
                for value in values:
                    category = value.get('value_category', '')
                    description = value.get('value_description', '')
                    
                    if category == 'core_values':
                        reconstructed['personality']['values'].append(description)
                    elif category == 'core_beliefs':
                        reconstructed['personality']['core_beliefs'].append(description)
                    elif category == 'dreams':
                        reconstructed['personality']['dreams'].append(description)
                    elif category == 'fears':
                        reconstructed['personality']['fears'].append(description)
                    elif category == 'quirks':
                        reconstructed['personality']['quirks'].append(description)
                        
        except Exception as e:
            logger.debug("Error reconstructing values: %s", e)
    
    def _reconstruct_personal_knowledge(self, reconstructed: Dict[str, Any]):
        """Reconstruct personal knowledge from database"""
        try:
            if 'personal_knowledge' in self._data:
                knowledge = self._data['personal_knowledge']
                
                for item in knowledge:
                    category = item.get('knowledge_category', '')
                    key = item.get('knowledge_key', '')
                    value = item.get('knowledge_value', '')
                    
                    if category == 'relationships':
                        reconstructed['personal']['relationships'][key] = value
                    elif category == 'career':
                        reconstructed['personal']['career'][key] = value
                    elif category == 'interests' and 'current_focus' in key:
                        reconstructed['personal']['current_focus'].append(value)
                    elif category == 'social' and 'social_connection' in key:
                        reconstructed['personal']['social_circle'].append(value)
                        
        except Exception as e:
            logger.debug("Error reconstructing personal knowledge: %s", e)
            )
            
            # Create metadata
            metadata = CharacterMetadata(
                name=name,
                version="1.0",
                created_by="database_import"
            )
            
            # Create Character object with default objects for required fields
            self._character_object = Character(
                metadata=metadata,
                identity=identity,
                personality=personality,
                backstory=CharacterBackstory(),
                current_life=CharacterCurrentLife(),
                communication=CharacterCommunication()
            )
            
            logger.info("✅ Created Character object for: %s", name)
            return self._character_object
            
        except Exception as e:
            logger.error("Failed to create Character object: %s", e)
            import traceback
            traceback.print_exc()
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data for debugging"""
        self._load_character_data()
        
        if not self._data:
            return {"status": "no_data", "character": self._character_name}
        
        summary = {
            "status": "loaded",
            "character": self._character_name,
            "has_character": "character" in self._data,
            "data_keys": list(self._data.keys()) if isinstance(self._data, dict) else "not_dict"
        }
        
        if "character" in self._data:
            char_data = self._data["character"]
            if isinstance(char_data, dict):
                summary["character_keys"] = list(char_data.keys())
                
                # Add metadata info if available
                if "metadata" in char_data:
                    metadata = char_data["metadata"]
                    if isinstance(metadata, dict):
                        summary["character_name"] = metadata.get("name", "unknown")
                        summary["character_version"] = metadata.get("version", "unknown")
        
        return summary


# Global singleton instance
_database_cdl_manager: Optional[DatabaseCDLManager] = None
_manager_lock = threading.Lock()


def get_database_cdl_manager() -> DatabaseCDLManager:
    """
    Get the global database CDL manager instance (singleton).
    
    Returns:
        DatabaseCDLManager: Global manager instance
    """
    global _database_cdl_manager
    
    if _database_cdl_manager is None:
        with _manager_lock:
            if _database_cdl_manager is None:
                _database_cdl_manager = DatabaseCDLManager()
                logger.info("🚀 Created global Database CDL Manager instance")
    
    return _database_cdl_manager


def get_cdl_field(field_path: str, default: Any = None) -> Any:
    """
    Convenience function to get CDL field from global manager.
    
    Args:
        field_path: Dot notation field path
        default: Default value if field doesn't exist
        
    Returns:
        Field value or default
    """
    manager = get_database_cdl_manager()
    return manager.get_field(field_path, default)


def get_conversation_flow_guidelines() -> Dict[str, Any]:
    """
    Convenience function to get conversation flow guidelines.
    
    Returns:
        Dict containing conversation flow guidelines
    """
    manager = get_database_cdl_manager()
    return manager.get_conversation_flow_guidelines()