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
                
                # Store enhanced data for lazy-loading personal knowledge sections
                self._enhanced_data = data
                self._relationships = None
                self._backstory = None
                self._current_life = None
                self._skills_and_expertise = None
                self._interests_and_hobbies = None
            
            # Lazy-loading properties for personal knowledge extraction
            
            @property
            def relationships(self):
                """Lazy-load relationships from enhanced data"""
                if self._relationships is None:
                    self._relationships = self._create_relationships_object()
                    logger.debug("🔗 Lazy-loaded relationships: %s important relationships", 
                               len(self._relationships.important_relationships) if self._relationships else 0)
                return self._relationships
            
            @property
            def backstory(self):
                """Lazy-load backstory from enhanced data"""
                if self._backstory is None:
                    self._backstory = self._create_backstory_object()
                    logger.debug("📖 Lazy-loaded backstory: family=%s, career=%s", 
                               bool(self._backstory.family_background) if self._backstory else False,
                               bool(self._backstory.career_background) if self._backstory else False)
                return self._backstory
            
            @property
            def current_life(self):
                """Lazy-load current_life from enhanced data"""
                if self._current_life is None:
                    self._current_life = self._create_current_life_object()
                return self._current_life
            
            @property
            def skills_and_expertise(self):
                """Lazy-load skills_and_expertise from enhanced data"""
                if self._skills_and_expertise is None:
                    self._skills_and_expertise = self._create_skills_and_expertise_object()
                return self._skills_and_expertise
            
            @property
            def interests_and_hobbies(self):
                """Lazy-load interests_and_hobbies from enhanced data"""
                if self._interests_and_hobbies is None:
                    self._interests_and_hobbies = self._create_interests_and_hobbies_object()
                return self._interests_and_hobbies
            
            # Object creation methods for lazy-loaded properties
            
            def _create_relationships_object(self):
                """Create relationships object from enhanced data"""
                class Relationships:
                    def __init__(self, enhanced_data):
                        relationships_list = enhanced_data.get('relationships', [])
                        # Extract relationship status from first relationship if available
                        self.status = None
                        if relationships_list and len(relationships_list) > 0:
                            # Derive status from relationship types
                            rel_types = [r.get('relationship_type', '') for r in relationships_list]
                            if any('partner' in rt.lower() or 'spouse' in rt.lower() for rt in rel_types):
                                self.status = 'In a relationship'
                            elif any('family' in rt.lower() for rt in rel_types):
                                self.status = 'Single with family connections'
                            else:
                                self.status = 'Single'
                        
                        # Extract important relationships
                        self.important_relationships = [
                            f"{r.get('related_entity', 'Unknown')} ({r.get('relationship_type', 'Unknown')})"
                            for r in relationships_list[:5]  # Top 5 relationships
                        ] if relationships_list else []
                
                return Relationships(self._enhanced_data)
            
            def _create_backstory_object(self):
                """Create backstory object from enhanced data"""
                class Backstory:
                    def __init__(self, enhanced_data):
                        background_dict = enhanced_data.get('background', {})
                        
                        # Extract family background
                        self.family_background = self._extract_background('personal', background_dict)
                        
                        # Extract career background
                        self.career_background = self._extract_background('career', background_dict)
                        
                        # Extract formative experiences (combine education and early experiences)
                        education_bg = self._extract_background('education', background_dict)
                        personal_bg = self._extract_background('personal', background_dict)
                        self.formative_experiences = f"{education_bg}; {personal_bg}" if education_bg and personal_bg else (education_bg or personal_bg)
                    
                    def _extract_background(self, category, background_dict):
                        """Extract background entries for a specific category"""
                        if not background_dict or category not in background_dict:
                            return None
                        
                        category_entries = background_dict.get(category, [])
                        if not category_entries:
                            return None
                        
                        # Combine descriptions from all entries in category
                        descriptions = [
                            entry.get('description', '') 
                            for entry in category_entries 
                            if entry.get('description')
                        ]
                        return '; '.join(descriptions) if descriptions else None
                
                return Backstory(self._enhanced_data)
            
            def _create_current_life_object(self):
                """Create current_life object from enhanced data"""
                class CurrentLife:
                    def __init__(self, enhanced_data):
                        # Extract family info from relationships
                        relationships_list = enhanced_data.get('relationships', [])
                        family_rels = [
                            r for r in relationships_list 
                            if 'family' in r.get('relationship_type', '').lower()
                        ]
                        self.family = ', '.join([
                            f"{r.get('related_entity')} ({r.get('relationship_type')})"
                            for r in family_rels[:3]
                        ]) if family_rels else None
                        
                        # Extract occupation details from abilities/background
                        abilities_dict = enhanced_data.get('abilities', {})
                        professional_abilities = abilities_dict.get('professional', [])
                        self.occupation_details = ', '.join([
                            a.get('ability_name', '')
                            for a in professional_abilities[:3]
                        ]) if professional_abilities else None
                        
                        # Create daily routine object
                        self.daily_routine = self._create_daily_routine(enhanced_data)
                    
                    def _create_daily_routine(self, enhanced_data):
                        """Create daily routine from background/abilities data"""
                        class DailyRoutine:
                            def __init__(self, enhanced_data):
                                # Extract work schedule from background
                                background_dict = enhanced_data.get('background', {})
                                career_entries = background_dict.get('career', [])
                                self.work_schedule = career_entries[0].get('description') if career_entries else None
                                
                                # Extract weekend/evening activities from interests
                                # (This will be populated once we query character_interests)
                                self.weekend_activities = []
                                self.evening_routine = None
                        
                        return DailyRoutine(enhanced_data)
                
                return CurrentLife(self._enhanced_data)
            
            def _create_skills_and_expertise_object(self):
                """Create skills_and_expertise object from enhanced data"""
                class SkillsAndExpertise:
                    def __init__(self, enhanced_data):
                        # Extract education from background
                        background_dict = enhanced_data.get('background', {})
                        education_entries = background_dict.get('education', [])
                        self.education = '; '.join([
                            entry.get('description', '')
                            for entry in education_entries
                            if entry.get('description')
                        ]) if education_entries else None
                        
                        # Extract professional skills from abilities
                        abilities_dict = enhanced_data.get('abilities', {})
                        professional_abilities = abilities_dict.get('professional', [])
                        self.professional_skills = ', '.join([
                            f"{a.get('ability_name')} (Level {a.get('proficiency_level', 5)})"
                            for a in professional_abilities
                        ]) if professional_abilities else None
                
                return SkillsAndExpertise(self._enhanced_data)
            
            def _create_interests_and_hobbies_object(self):
                """Create interests_and_hobbies object from enhanced data"""
                # Check if enhanced data has interests
                # Note: Enhanced manager doesn't currently query character_interests table
                # We'll return a simple string summarizing any interest-related data
                
                # For now, create a simple string representation
                # This can be enhanced once we integrate character_interests table query
                abilities_dict = self._enhanced_data.get('abilities', {})
                
                # Look for non-professional abilities that might indicate hobbies
                hobby_categories = ['personal', 'social', 'creative', 'physical']
                hobbies = []
                for category in hobby_categories:
                    if category in abilities_dict:
                        category_abilities = abilities_dict[category]
                        hobbies.extend([
                            a.get('ability_name', '')
                            for a in category_abilities
                        ])
                
                return ', '.join(hobbies) if hobbies else 'Various personal interests'
                
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
        
        # Log available enhanced data sections
        if self._character_data:
            enhanced_keys = [k for k in self._character_data.keys() if k not in ['identity', 'personality', 'communication_style', 'values_and_beliefs', 'allow_full_roleplay_immersion']]
            logger.info("✨ SimpleCharacter created with enhanced data sections: %s", enhanced_keys)
                
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