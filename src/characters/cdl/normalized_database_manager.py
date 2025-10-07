"""
CDL Normalized Database Manager - PostgreSQL-backed character data management
Uses proper normalized schema with hybrid JSON approach for extensibility.
"""

import asyncio
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CDLFieldAccess:
    """Represents the result of accessing a CDL field"""
    value: Any
    exists: bool
    path: str


class NormalizedCDLManager:
    """
    Normalized CDL Manager using proper RDBMS schema.
    
    Uses normalized tables for core fields with JSON columns for extensibility.
    This gives us the best of both worlds: queryable core fields + flexible extensions.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._character_data: Optional[Dict[str, Any]] = None
        self._loaded = False
        self._character_name: Optional[str] = None
        self._character_object = None
        self._pool = None
    
    def _get_character_name(self) -> str:
        """Get character name from environment configuration - DATABASE-ONLY approach."""
        if self._character_name is None:
            # DATABASE-ONLY: Use bot name from environment (DISCORD_BOT_NAME/BOT_NAME)
            # No more CDL file dependencies!
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            self._character_name = bot_name.lower()
            logger.info("DATABASE-ONLY: Using character name: %s from bot environment", self._character_name)
        
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
    
    async def _get_database_pool(self):
        """Get database connection pool"""
        if self._pool is None:
            # Use Docker network connection details
            import asyncpg
            import os
            
            postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
            postgres_port = os.getenv('POSTGRES_PORT', '5432') 
            postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')
            postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
            
            database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
            self._pool = await asyncpg.create_pool(database_url)
        return self._pool
    
    def _load_character_data(self) -> None:
        """Load character data from normalized database tables"""
        if self._loaded:
            return
        
        with self._lock:
            if self._loaded:  # Double-check locking
                return
                
            try:
                character_name = self._get_character_name()
                logger.info("Loading character data for: %s", character_name)
                
                # Load from normalized database
                character_data = self._run_async(self._load_from_normalized_db(character_name))
                
                if character_data:
                    self._character_data = character_data
                    logger.info("✅ Loaded character data from normalized database: %s", character_name)
                else:
                    logger.warning("❌ No character data found in database: %s", character_name)
                    self._character_data = {}
                    
            except Exception as e:
                logger.error("❌ Error loading character data: %s", e)
                self._character_data = {}
            finally:
                self._loaded = True
    
    async def _load_from_normalized_db(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Load character data from normalized database tables"""
        try:
            pool = await self._get_database_pool()
            
            async with pool.acquire() as conn:
                # Get character ID
                char_row = await conn.fetchrow(
                    "SELECT id, name, version FROM characters WHERE name = $1 AND active = true",
                    character_name
                )
                
                if not char_row:
                    logger.warning("Character not found in database: %s", character_name)
                    return None
                
                char_id = char_row['id']
                logger.info("Found character ID %s for %s", char_id, character_name)
                
                # Load all related data with JOINs for efficiency
                character_data = await conn.fetchrow("""
                    SELECT 
                        c.name, c.version,
                        ci.name as identity_name, ci.occupation, ci.location, ci.description, ci.extended_data as identity_extended,
                        cp.openness, cp.conscientiousness, cp.extraversion, cp.agreeableness, cp.neuroticism,
                        cp.custom_traits, cp.values, cp.core_beliefs, cp.dreams, cp.fears, cp.quirks,
                        cc.response_length, cc.communication_style, cc.typical_responses, cc.emotional_expressions,
                        cc.message_pattern_triggers, cc.conversation_flow_guidance, cc.ai_identity_handling,
                        cb.childhood, cb.education, cb.career_history, cb.key_events, cb.relationships as backstory_relationships,
                        ccl.daily_routine, ccl.current_projects, ccl.goals, ccl.challenges, ccl.social_circle, ccl.interests,
                        csp.vocabulary, csp.language_patterns, csp.favorite_phrases, csp.speech_quirks,
                        cpk.relationships, cpk.career, cpk.hobbies, cpk.preferences, cpk.memories, cpk.secrets,
                        cm.created_by, cm.source_file, cm.schema_version, cm.extended_metadata
                    FROM characters c
                    LEFT JOIN character_identity ci ON c.id = ci.character_id
                    LEFT JOIN character_personality cp ON c.id = cp.character_id
                    LEFT JOIN character_communication cc ON c.id = cc.character_id
                    LEFT JOIN character_backstory cb ON c.id = cb.character_id
                    LEFT JOIN character_current_life ccl ON c.id = ccl.character_id
                    LEFT JOIN character_speech_patterns csp ON c.id = csp.character_id
                    LEFT JOIN character_personal_knowledge cpk ON c.id = cpk.character_id
                    LEFT JOIN character_metadata cm ON c.id = cm.character_id
                    WHERE c.id = $1
                """, char_id)
                
                if not character_data:
                    logger.error("Failed to load character data for ID %s", char_id)
                    return None
                
                # Reconstruct CDL-compatible structure
                return self._reconstruct_cdl_structure(character_data)
                
        except Exception as e:
            logger.error("Error loading from normalized database: %s", e)
            return None
    
    def _reconstruct_cdl_structure(self, row) -> Dict[str, Any]:
        """Reconstruct CDL-compatible structure from normalized database row"""
        import json
        
        try:
            # Helper function to safely parse JSON
            def safe_json_loads(value, default=None):
                if value is None:
                    return default or {}
                if isinstance(value, (dict, list)):
                    return value
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return default or {}
            
            # Build identity section
            identity_extended = safe_json_loads(row['identity_extended'], {})
            identity = {
                'name': row['identity_name'] or row['name'],
                'occupation': row['occupation'] or '',
                'location': row['location'] or '',
                'description': row['description'] or '',
                **identity_extended  # Merge extended data
            }
            
            # Build personality section
            personality = {
                'big_five': {
                    'openness': float(row['openness'] or 0.5),
                    'conscientiousness': float(row['conscientiousness'] or 0.5),
                    'extraversion': float(row['extraversion'] or 0.5),
                    'agreeableness': float(row['agreeableness'] or 0.5),
                    'neuroticism': float(row['neuroticism'] or 0.5)
                },
                'custom_traits': safe_json_loads(row['custom_traits'], {}),
                'values': safe_json_loads(row['values'], []),
                'core_beliefs': safe_json_loads(row['core_beliefs'], []),
                'dreams': safe_json_loads(row['dreams'], []),
                'fears': safe_json_loads(row['fears'], []),
                'quirks': safe_json_loads(row['quirks'], [])
            }
            
            # Build communication section
            communication = {
                'response_length': row['response_length'] or 'moderate',
                'communication_style': row['communication_style'] or 'adaptive',
                'typical_responses': safe_json_loads(row['typical_responses'], {}),
                'emotional_expressions': safe_json_loads(row['emotional_expressions'], {}),
                'message_pattern_triggers': safe_json_loads(row['message_pattern_triggers'], {}),
                'conversation_flow_guidance': safe_json_loads(row['conversation_flow_guidance'], {}),
                'ai_identity_handling': safe_json_loads(row['ai_identity_handling'], {})
            }
            
            # Build backstory section
            backstory = {
                'childhood': safe_json_loads(row['childhood'], {}),
                'education': safe_json_loads(row['education'], {}),
                'career_history': safe_json_loads(row['career_history'], []),
                'key_events': safe_json_loads(row['key_events'], []),
                'relationships': safe_json_loads(row['backstory_relationships'], {})
            }
            
            # Build current_life section
            current_life = {
                'daily_routine': safe_json_loads(row['daily_routine'], {}),
                'current_projects': safe_json_loads(row['current_projects'], []),
                'goals': safe_json_loads(row['goals'], []),
                'challenges': safe_json_loads(row['challenges'], []),
                'social_circle': safe_json_loads(row['social_circle'], []),
                'interests': safe_json_loads(row['interests'], [])
            }
            
            # Build speech_patterns section
            vocabulary = safe_json_loads(row['vocabulary'], {"preferred_words": [], "avoided_words": []})
            speech_patterns = {
                'vocabulary': vocabulary,
                'language_patterns': safe_json_loads(row['language_patterns'], {}),
                'speech_quirks': safe_json_loads(row['speech_quirks'], [])
            }
            
            # Add favorite_phrases to identity.voice for compatibility
            favorite_phrases = safe_json_loads(row['favorite_phrases'], [])
            if 'voice' not in identity:
                identity['voice'] = {}
            identity['voice']['favorite_phrases'] = favorite_phrases
            
            # Build personal section
            personal = {
                'relationships': safe_json_loads(row['relationships'], {}),
                'career': safe_json_loads(row['career'], {}),
                'hobbies': safe_json_loads(row['hobbies'], {}),
                'preferences': safe_json_loads(row['preferences'], {}),
                'memories': safe_json_loads(row['memories'], []),
                'secrets': safe_json_loads(row['secrets'], [])
            }
            
            # Build metadata section
            metadata = {
                'created_by': row['created_by'] or 'system',
                'version': row['version'] or '1.0',
                'schema_version': row['schema_version'] or '1.0',
                'source_file': row['source_file'],
                **safe_json_loads(row['extended_metadata'], {})
            }
            
            # Construct complete CDL structure
            cdl_structure = {
                'name': row['name'],
                'metadata': metadata,
                'identity': identity,
                'personality': personality,
                'communication': communication,
                'backstory': backstory,
                'current_life': current_life,
                'speech_patterns': speech_patterns,
                'personal': personal
            }
            
            logger.info("✅ Reconstructed CDL structure for character: %s", row['name'])
            return cdl_structure
            
        except Exception as e:
            logger.error("Error reconstructing CDL structure: %s", e)
            return {}
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get a field value using dot notation path.
        
        Args:
            field_path: Dot-separated path like "identity.name"
            default: Default value if field doesn't exist
            
        Returns:
            Field value or default
        """
        self._load_character_data()
        
        if not self._character_data:
            return default
        
        try:
            current = self._character_data
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
        
        if not self._character_data:
            return CDLFieldAccess(value=default, exists=False, path=field_path)
        
        try:
            current = self._character_data
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
        return self.get_field("identity.name", default="Unknown")
    
    def get_character_occupation(self) -> str:
        """Convenience method to get character occupation"""
        return self.get_field("identity.occupation", default="")
    
    def get_conversation_flow_guidelines(self) -> Dict[str, Any]:
        """Convenience method to get conversation flow guidelines"""
        return self.get_field("communication.conversation_flow_guidance", {})
    
    def get_response_style(self) -> Dict[str, Any]:
        """Convenience method to get response_style"""
        guidelines = self.get_conversation_flow_guidelines()
        return guidelines.get('response_style', {})
    
    def get_communication_style(self) -> Dict[str, Any]:
        """Convenience method to get communication style"""
        return self.get_field("communication", default={})
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """Convenience method to get personality traits"""
        return self.get_field("personality", default={})
    
    def get_ai_identity_handling(self) -> Dict[str, Any]:
        """Convenience method to get AI identity handling"""
        return self.get_field("communication.ai_identity_handling", default={})
    
    def reload(self) -> None:
        """Force reload of character data (for development/testing)"""
        with self._lock:
            self._loaded = False
            self._character_data = None
            self._character_object = None
        self._load_character_data()
        logger.info("🔄 Reloaded character data from normalized database")
    
    def get_character_object(self):
        """
        Get Character object from normalized database data.
        Creates Character object compatible with existing CDL system.
        """
        if self._character_object is not None:
            return self._character_object
            
        try:
            # Load character data
            self._load_character_data()
            
            if not self._character_data:
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
            
            # Extract data sections
            identity_data = self._character_data.get('identity', {})
            personality_data = self._character_data.get('personality', {})
            communication_data = self._character_data.get('communication', {})
            backstory_data = self._character_data.get('backstory', {})
            current_life_data = self._character_data.get('current_life', {})
            metadata_data = self._character_data.get('metadata', {})
            
            # Create BigFive personality object
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
                name=identity_data.get('name', 'Unknown'),
                occupation=identity_data.get('occupation', ''),
                location=identity_data.get('location', ''),
                description=identity_data.get('description', '')
            )
            
            # Create personality object
            personality = CharacterPersonality(
                big_five=big_five,
                custom_traits=personality_data.get('custom_traits', {}),
                values=personality_data.get('values', []),
                core_beliefs=personality_data.get('core_beliefs', [])
            )
            
            # Create communication object
            communication = CharacterCommunication(
                typical_responses=communication_data.get('typical_responses', {}),
                emotional_expressions=communication_data.get('emotional_expressions', {}),
                response_length=communication_data.get('response_length', 'moderate'),
                communication_style=communication_data.get('communication_style', 'adaptive'),
                message_pattern_triggers=communication_data.get('message_pattern_triggers', {})
            )
            
            # Create backstory object
            backstory = CharacterBackstory(
                origin_story=str(backstory_data.get('childhood', {}).get('origin_story', '')),
                family_background=str(backstory_data.get('childhood', {}).get('family_background', '')),
                education=str(backstory_data.get('education', {}).get('summary', '')),
                formative_experiences=backstory_data.get('key_events', []),
                life_phases=[],  # Could be extracted from backstory_data if needed
                traumas=[],
                achievements=backstory_data.get('career_history', []),
                regrets=[]
            )
            
            # Create current life object
            current_life = CharacterCurrentLife(
                living_situation=str(current_life_data.get('living_situation', '')),
                relationships=current_life_data.get('relationships', []),
                occupation_details=str(current_life_data.get('occupation_details', '')),
                financial_status=str(current_life_data.get('financial_status', '')),
                health_status=str(current_life_data.get('health_status', '')),
                projects=[],  # Could be extracted from current_life_data if needed
                goals=current_life_data.get('goals', []),
                challenges=current_life_data.get('challenges', []),
                daily_routine=None,  # Could create DailyRoutine from data if needed
                social_circle=current_life_data.get('social_circle', [])
            )
            
            # Create metadata
            metadata = CharacterMetadata(
                created_by=metadata_data.get('created_by', 'normalized_db'),
                version=str(metadata_data.get('version', '1.0')),
                description=f"Normalized database character: {identity_data.get('name', 'Unknown')}"
            )
            
            # Create Character object
            self._character_object = Character(
                metadata=metadata,
                identity=identity,
                personality=personality,
                backstory=backstory,
                current_life=current_life,
                communication=communication
            )
            
            logger.info("✅ Created Character object from normalized database")
            return self._character_object
            
        except Exception as e:
            logger.error("Failed to create Character object from normalized database: %s", e)
            import traceback
            traceback.print_exc()
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data for debugging"""
        self._load_character_data()
        
        if not self._character_data:
            return {"status": "no_data", "character": self._character_name}
        
        summary = {
            "status": "loaded_from_normalized_db",
            "character": self._character_name,
            "data_keys": list(self._character_data.keys()) if isinstance(self._character_data, dict) else "not_dict",
            "identity_name": self._character_data.get('identity', {}).get('name', 'unknown'),
            "occupation": self._character_data.get('identity', {}).get('occupation', 'unknown'),
            "version": self._character_data.get('metadata', {}).get('version', 'unknown')
        }
        
        return summary


# Global singleton instance
_normalized_cdl_manager: Optional[NormalizedCDLManager] = None
_manager_lock = threading.Lock()


def get_normalized_cdl_manager() -> NormalizedCDLManager:
    """
    Get the global normalized CDL manager instance (singleton).
    
    Returns:
        NormalizedCDLManager: Global manager instance
    """
    global _normalized_cdl_manager
    
    if _normalized_cdl_manager is None:
        with _manager_lock:
            if _normalized_cdl_manager is None:
                _normalized_cdl_manager = NormalizedCDLManager()
                logger.info("🚀 Created global Normalized CDL Manager instance")
    
    return _normalized_cdl_manager


# Compatibility functions for existing code
def get_database_cdl_manager() -> NormalizedCDLManager:
    """Compatibility function - returns normalized manager"""
    return get_normalized_cdl_manager()


def get_cdl_field(field_path: str, default: Any = None) -> Any:
    """
    Convenience function to get CDL field from global manager.
    
    Args:
        field_path: Dot notation field path
        default: Default value if field doesn't exist
        
    Returns:
        Field value or default
    """
    manager = get_normalized_cdl_manager()
    return manager.get_field(field_path, default)


def get_conversation_flow_guidelines() -> Dict[str, Any]:
    """
    Convenience function to get conversation flow guidelines.
    
    Returns:
        Dict containing conversation flow guidelines
    """
    manager = get_normalized_cdl_manager()
    return manager.get_conversation_flow_guidelines()