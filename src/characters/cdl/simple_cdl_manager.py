"""
Simple CDL Manager - Clean RDBMS Approach
WhisperEngine Character Definition Language Manager for pure relational schema

This replaces the complex normalized manager with a simple, direct approach
that works with our clean RDBMS schema (no JSON/JSONB).
"""

import logging
import os
import asyncio
import asyncpg
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleCDLManager:
    """Simple CDL Manager using clean RDBMS schema"""
    
    def __init__(self):
        self._pool = None
        self._character_data = None
        self._character_name = None
        self._loaded = False
        
    def _get_character_name(self) -> str:
        """Get character name from environment configuration"""
        if self._character_name is None:
            # Use bot name from environment (DISCORD_BOT_NAME/BOT_NAME)
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            self._character_name = bot_name.lower()
            logger.info("Using character name: %s from bot environment", self._character_name)
        
        return self._character_name
        
    async def _get_database_pool(self):
        """Get database connection pool"""
        if self._pool is None:
            postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
            postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
            postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
            postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')
            
            database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
            self._pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
            
        return self._pool
        
    def _run_async(self, coro):
        """Helper to run async functions in sync context"""
        try:
            # Check if we're already in an event loop
            asyncio.get_running_loop()
            # We're in an event loop, need to create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No event loop running, we can run directly
            return asyncio.run(coro)
            
    def _load_character_data(self):
        """Load character data from database"""
        if self._loaded:
            return
            
        try:
            character_name = self._get_character_name()
            logger.info("Loading character data for: %s", character_name)
            
            # Load from clean RDBMS database
            character_data = self._run_async(self._load_from_database(character_name))
            
            if character_data:
                self._character_data = character_data
                logger.info("✅ Loaded character data from database: %s", character_name)
            else:
                logger.warning("❌ No character data found in database: %s", character_name)
                self._character_data = self._get_default_character_data()
                
        except (KeyError, ConnectionError, RuntimeError) as e:
            logger.error("❌ Error loading character data: %s", e)
            self._character_data = self._get_default_character_data()
        finally:
            self._loaded = True
            
    async def _load_from_database(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Load character data from comprehensive RDBMS schema using enhanced manager"""
        try:
            pool = await self._get_database_pool()
            
            # Use enhanced CDL manager for comprehensive character data
            from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
            enhanced_manager = create_enhanced_cdl_manager(pool)
            
            # Get comprehensive character data from enhanced manager
            character_data = await enhanced_manager.get_character_by_name(character_name)
            
            if character_data:
                logger.info("✅ Enhanced manager loaded character: %s", character_name)
                logger.debug("Character data keys: %s", list(character_data.keys()))
                return character_data
            else:
                logger.warning("❌ Enhanced manager found no character data for: %s", character_name)
                return None
                
        except Exception as e:
            logger.error("Enhanced manager failed to load character: %s", e)
            return None
            
    def _build_cdl_structure(self, char_row, personality_rows, values_rows) -> Dict[str, Any]:
        """Build CDL-compatible structure from database rows"""
        
        # Build identity section
        identity = {
            'name': char_row['name'] or '',
            'occupation': char_row['occupation'] or '',
            'description': char_row['description'] or '',
            'archetype': char_row['archetype'] or 'real-world'
        }
        
        # Build personality section with Big Five traits
        big_five = {}
        for trait_row in personality_rows:
            trait_name = trait_row['trait_name']
            trait_value = float(trait_row['trait_value'] or 0.5)
            big_five[trait_name] = {
                'value': trait_value,
                'intensity': trait_row['intensity'] or 'medium',
                'description': trait_row['description'] or f'{trait_name} trait'
            }
            
        personality = {
            'big_five': big_five
        }
        
        # Build communication section
        communication = {
            'engagement_level': float(char_row['engagement_level'] or 0.7),
            'formality': {'value': char_row['formality'] or 'informal'},
            'emotional_expression': float(char_row['emotional_expression'] or 0.6),
            'response_length': char_row['response_length'] or 'medium',
            'conversation_flow_guidance': char_row['conversation_flow_guidance'] or '',
            'ai_identity_handling': char_row['ai_identity_handling'] or ''
        }
        
        # Build values and beliefs section
        values_and_beliefs = {}
        for value_row in values_rows:
            value_key = value_row['value_key']
            values_and_beliefs[value_key] = {
                'description': value_row['value_description'],
                'importance': value_row['importance_level'],
                'category': value_row['category']
            }
            
        # Return CDL structure
        return {
            'identity': identity,
            'personality': personality,
            'communication': communication,
            'values_and_beliefs': values_and_beliefs,
            'allow_full_roleplay_immersion': char_row.get('allow_full_roleplay', False)
        }
        
    def _get_default_character_data(self) -> Dict[str, Any]:
        """Return default character data when database fails"""
        return {
            'identity': {'name': 'Unknown', 'occupation': '', 'description': ''},
            'personality': {'big_five': {}},
            'communication': {},
            'values_and_beliefs': {},
            'allow_full_roleplay_immersion': False
        }
        
    # Public interface methods (what the CDL AI integration uses)
    
    def get_character_name(self) -> str:
        """Get character name"""
        self._load_character_data()
        if self._character_data is None:
            return 'Unknown'
        return self._character_data.get('identity', {}).get('name', 'Unknown')
        
    def get_character_occupation(self) -> str:
        """Get character occupation"""
        self._load_character_data()
        if self._character_data is None:
            return ''
        return self._character_data.get('identity', {}).get('occupation', '')
        
    def get_character_object(self):
        """Get character object (for compatibility with existing code)"""
        self._load_character_data()
        
        # Create a simple object with identity, personality, and communication attributes
        class SimpleCharacter:
            def __init__(self, data):
                self.identity = self._create_identity_object(data.get('identity', {}))
                self.personality = self._create_personality_object(data.get('personality', {}))
                self.communication = self._create_communication_object(data.get('communication', {}))
                self.allow_full_roleplay_immersion = data.get('allow_full_roleplay_immersion', False)
                
            def _create_identity_object(self, identity_data):
                class Identity:
                    def __init__(self, data):
                        self.name = data.get('name', 'Unknown')
                        self.occupation = data.get('occupation', '')
                        self.description = data.get('description', '')
                        self.archetype = data.get('archetype', 'real-world')
                return Identity(identity_data)
                
            def _create_personality_object(self, personality_data):
                class Personality:
                    def __init__(self, data):
                        big_five_data = data.get('big_five', {})
                        self.big_five = self._create_big_five_object(big_five_data)
                    
                    def _create_big_five_object(self, big_five_data):
                        class BigFive:
                            def __init__(self, data):
                                # Create trait objects for each Big Five trait
                                self.openness = self._create_trait_object(data.get('openness', {}))
                                self.conscientiousness = self._create_trait_object(data.get('conscientiousness', {}))
                                self.extraversion = self._create_trait_object(data.get('extraversion', {}))
                                self.agreeableness = self._create_trait_object(data.get('agreeableness', {}))
                                self.neuroticism = self._create_trait_object(data.get('neuroticism', {}))
                            
                            def _create_trait_object(self, trait_data):
                                class Trait:
                                    def __init__(self, data):
                                        self.value = data.get('value', 0.5)
                                        self.intensity = data.get('intensity', 'moderate')
                                        self.score = self.value  # Alias for compatibility
                                        self.trait_description = f"{self.intensity} level"
                                return Trait(trait_data)
                        
                        return BigFive(big_five_data)
                
                return Personality(personality_data)
            
            def _create_communication_object(self, communication_data):
                class Communication:
                    def __init__(self, data):
                        # Create message pattern triggers for scenario detection
                        self.message_pattern_triggers = self._create_message_triggers()
                        
                        # Add communication style data (defaults for now)
                        self.conversation_flow_guidance = data.get('conversation_flow_guidance', {})
                        self.ai_identity_handling = data.get('ai_identity_handling', {})
                        self.collaboration_style = data.get('collaboration_style', '')
                        self.length_management = data.get('length_management', '')
                    
                    def _create_message_triggers(self):
                        # Generic message pattern triggers (character-agnostic)
                        return {
                            'basic_greeting': {
                                'keywords': ['hello', 'hi', 'hey', 'good morning', 'good evening'],
                                'phrases': ['how are you', 'how have you been']
                            },
                            'basic_question': {
                                'keywords': ['what', 'why', 'how', 'when', 'where', 'who'],
                                'phrases': ['can you tell me', 'do you know', 'could you explain']
                            },
                            'emotional_context': {
                                'keywords': ['sad', 'happy', 'angry', 'worried', 'excited', 'frustrated'],
                                'phrases': ['feeling down', 'so excited', 'really upset']
                            }
                        }
                
                return Communication(communication_data)
                
        return SimpleCharacter(self._character_data)

# Module-level manager instance
_simple_cdl_manager = None

def get_simple_cdl_manager() -> SimpleCDLManager:
    """Get the simple CDL manager instance"""
    # pylint: disable=global-statement
    global _simple_cdl_manager
    if _simple_cdl_manager is None:
        _simple_cdl_manager = SimpleCDLManager()
    return _simple_cdl_manager