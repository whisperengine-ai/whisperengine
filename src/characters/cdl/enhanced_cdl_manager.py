"""
Enhanced CDL Manager for Comprehensive RDBMS Schema
WhisperEngine Character Definition Language Manager
Version: 2.0 - October 2025

Maintains backward compatibility with CDL AI Integration while providing
access to rich character data through clean relational design.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncpg
from dataclasses import dataclass, asdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CharacterAppearance:
    category: str  # 'physical', 'digital', 'voice', 'presence'
    attribute: str  # 'height', 'build', 'hair_color', 'avatar_style'
    value: str
    description: Optional[str] = None

@dataclass
class CharacterBackground:
    category: str  # 'education', 'career', 'personal', 'cultural', 'mystical'
    period: Optional[str]  # 'childhood', 'university', 'early_career'
    title: Optional[str]
    description: str
    date_range: Optional[str]
    importance_level: int = 5

@dataclass
class CharacterRelationship:
    related_entity: str
    relationship_type: str  # 'colleague', 'mentor', 'rival', 'family'
    relationship_strength: int = 5
    description: Optional[str] = None
    status: str = 'active'

@dataclass
class CharacterMemory:
    memory_type: str  # 'formative', 'traumatic', 'joyful', 'professional'
    title: str
    description: str
    emotional_impact: int = 5
    time_period: Optional[str] = None
    importance_level: int = 5
    triggers: Optional[List[str]] = None

@dataclass
class ResponseGuideline:
    guideline_type: str  # 'response_length', 'formatting_rule', 'core_principle'
    guideline_name: str
    guideline_content: str
    priority: int
    context: str  # 'discord', 'general', 'all'
    is_critical: bool

@dataclass
class ConversationFlow:
    flow_type: str  # 'marine_science_discussion', 'personal_connection', 'general'
    flow_name: str
    energy_level: str
    approach_description: str
    transition_style: str
    priority: int
    context: Optional[str] = None  # Additional context for when this flow applies

@dataclass
class MessageTrigger:
    trigger_category: str  # 'marine_science_discussion', 'personal_connection'
    trigger_type: str  # 'keyword', 'phrase', 'pattern'
    trigger_value: str
    response_mode: str
    priority: int
    is_active: bool

@dataclass
class ResponseMode:
    mode_name: str  # 'technical', 'creative', 'brief'
    mode_description: str
    response_style: str
    length_guideline: str
    tone_adjustment: str
    conflict_resolution_priority: int

@dataclass
class EmojiPattern:
    pattern_category: str  # 'excitement_level', 'topic_specific'
    pattern_name: str  # 'high_excitement', 'ocean_marine_life'
    emoji_sequence: str
    usage_context: str
    frequency: str

@dataclass
class SpeechPattern:
    pattern_type: str  # 'preferred_words', 'avoided_words', 'sentence_structure'
    pattern_value: str
    usage_frequency: str
    context: str
    priority: int
    time_period: Optional[str] = None
    importance_level: int = 5
    triggers: Optional[List[str]] = None

@dataclass
class CharacterAbility:
    category: str  # 'professional', 'mystical', 'digital', 'social'
    ability_name: str
    proficiency_level: int = 5
    description: Optional[str] = None
    development_method: Optional[str] = None
    usage_frequency: str = 'regular'

@dataclass
class CommunicationPattern:
    pattern_type: str  # 'emoji', 'humor', 'technical', 'emotional'
    pattern_name: str
    pattern_value: str
    context: Optional[str] = None
    frequency: str = 'regular'
    description: Optional[str] = None

@dataclass
class BehavioralTrigger:
    trigger_type: str  # 'topic', 'emotion', 'situation', 'word'
    trigger_value: str
    response_type: str  # 'enthusiasm', 'expertise', 'caution'
    response_description: str
    intensity_level: int = 5

@dataclass
class CharacterEssence:
    essence_type: str  # 'nature', 'existence_method', 'core_power'
    essence_name: str
    description: str
    manifestation: Optional[str] = None
    power_level: Optional[int] = None

@dataclass
class CharacterInstruction:
    instruction_type: str  # 'introduction', 'override', 'special_behavior'
    instruction_text: str
    priority: int = 5
    context: Optional[str] = None
    active: bool = True

@dataclass
class AIScenario:
    scenario_type: str  # 'physical_interaction', 'activity_participation', 'example_scenario'
    scenario_name: str
    trigger_phrases: Optional[str] = None
    response_pattern: Optional[str] = None
    tier_1_response: Optional[str] = None
    tier_2_response: Optional[str] = None
    tier_3_response: Optional[str] = None
    example_usage: Optional[str] = None

@dataclass
class CulturalExpression:
    expression_type: str  # 'spanish_expression', 'favorite_phrase', 'speech_pattern', 'cultural_background'
    expression_value: str
    meaning: Optional[str] = None
    usage_context: Optional[str] = None
    emotional_context: Optional[str] = None
    frequency: Optional[str] = None

@dataclass
class VoiceTrait:
    trait_type: str  # 'tone', 'pace', 'volume', 'accent', 'vocabulary_level'
    trait_value: str
    situational_context: Optional[str] = None
    examples: Optional[str] = None

@dataclass
class EmotionalTrigger:
    trigger_type: str  # 'enthusiasm', 'concern', 'support', 'joy', 'worry'
    trigger_content: str
    trigger_category: Optional[str] = None
    emotional_response: Optional[str] = None
    response_intensity: Optional[str] = None
    response_examples: Optional[str] = None

@dataclass
class ExpertiseDomain:
    domain_name: str
    expertise_level: Optional[str] = None
    domain_description: Optional[str] = None
    key_concepts: Optional[str] = None
    teaching_approach: Optional[str] = None
    passion_level: Optional[int] = None
    examples: Optional[str] = None

class EnhancedCDLManager:
    """Enhanced CDL Manager with comprehensive character data access"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        
    async def get_character_by_name(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Get complete character data (backward compatible with CDL AI Integration)"""
        try:
            logger.info("🔍 ENHANCED CDL: get_character_by_name called with: '%s'", character_name)
            async with self.pool.acquire() as conn:
                # Core character data - search by normalized name (bot_name) or full name (case insensitive)
                core_query = """
                    SELECT c.*, 
                           COALESCE(c.created_date, CURRENT_TIMESTAMP) as created_date,
                           COALESCE(c.updated_date, CURRENT_TIMESTAMP) as updated_date
                    FROM characters c 
                    WHERE LOWER(c.normalized_name) = LOWER($1) OR LOWER(c.name) = LOWER($1)
                """
                logger.info("🔍 ENHANCED CDL: Executing query for character: '%s'", character_name)
                character_row = await conn.fetchrow(core_query, character_name)
                logger.info("🔍 ENHANCED CDL: Query result: %s", character_row)
                
                if not character_row:
                    logger.warning("🔍 ENHANCED CDL: Character '%s' not found in database", character_name)
                    return None
                
                logger.info("🔍 ENHANCED CDL: Found character row with name: '%s'", character_row['name'])
                character_id = character_row['id']
                
                # Build backward-compatible CDL structure
                cdl_data = await self._build_cdl_structure(conn, character_row, character_id)
                
                # Add rich character data (new functionality) with error handling
                try:
                    rich_data = await self._get_rich_character_data(conn, character_id)
                    cdl_data.update(rich_data)
                except Exception as rich_error:
                    logger.warning(f"Failed to load rich character data for {character_name}, using basic data only: {rich_error}")
                
                return cdl_data
                
        except Exception as e:
            logger.error(f"Error loading character data for {character_name}: {e}")
            return None

    async def get_response_guidelines(self, character_name: str) -> List[ResponseGuideline]:
        """Get response guidelines including length constraints and formatting rules"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT guideline_type, guideline_name, guideline_content, 
                           priority, context, is_critical
                    FROM character_response_guidelines 
                    WHERE character_id = $1
                    ORDER BY priority DESC, is_critical DESC
                """, character_id)

                return [ResponseGuideline(
                    guideline_type=row['guideline_type'],
                    guideline_name=row['guideline_name'],
                    guideline_content=row['guideline_content'],
                    priority=row['priority'],
                    context=row['context'],
                    is_critical=row['is_critical']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving response guidelines for {character_name}: {e}")
            return []

    async def get_conversation_flows(self, character_name: str) -> List[ConversationFlow]:
        """Get conversation flow guidance for different interaction types"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT flow_type, flow_name, energy_level, approach_description, 
                           transition_style, priority, context
                    FROM character_conversation_flows 
                    WHERE character_id = $1
                    ORDER BY priority DESC
                """, character_id)

                return [ConversationFlow(
                    flow_type=row['flow_type'],
                    flow_name=row['flow_name'],
                    energy_level=row['energy_level'],
                    approach_description=row['approach_description'],
                    transition_style=row['transition_style'],
                    priority=row['priority'],
                    context=row['context']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving conversation flows for {character_name}: {e}")
            return []

    async def get_message_triggers(self, character_name: str) -> List[MessageTrigger]:
        """Get message pattern triggers for different response modes"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT trigger_category, trigger_type, trigger_value, 
                           response_mode, priority, is_active
                    FROM character_message_triggers 
                    WHERE character_id = $1 AND is_active = true
                    ORDER BY priority DESC
                """, character_id)

                return [MessageTrigger(
                    trigger_category=row['trigger_category'],
                    trigger_type=row['trigger_type'],
                    trigger_value=row['trigger_value'],
                    response_mode=row['response_mode'],
                    priority=row['priority'],
                    is_active=row['is_active']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving message triggers for {character_name}: {e}")
            return []

    async def get_speech_patterns(self, character_name: str) -> List[SpeechPattern]:
        """Get speech patterns and vocabulary preferences"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT pattern_type, pattern_value, usage_frequency, context, priority
                    FROM character_speech_patterns 
                    WHERE character_id = $1
                    ORDER BY priority DESC
                """, character_id)

                return [SpeechPattern(
                    pattern_type=row['pattern_type'],
                    pattern_value=row['pattern_value'],
                    usage_frequency=row['usage_frequency'],
                    context=row['context'],
                    priority=row['priority']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving speech patterns for {character_name}: {e}")
            return []

    async def get_relationships(self, character_name: str) -> List[CharacterRelationship]:
        """Get character relationships including special connections like Cynthia for Gabriel"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT related_entity, relationship_type, relationship_strength, 
                           description, status, communication_style, connection_nature, recognition_pattern
                    FROM character_relationships 
                    WHERE character_id = $1
                    ORDER BY relationship_strength DESC
                """, character_id)

                return [CharacterRelationship(
                    related_entity=row['related_entity'],
                    relationship_type=row['relationship_type'],
                    relationship_strength=row['relationship_strength'],
                    description=row['description'],
                    status=row['status']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving relationships for {character_name}: {e}")
            return []

    async def get_behavioral_triggers(self, character_name: str) -> List[BehavioralTrigger]:
        """Get behavioral triggers including recognition responses and interaction patterns"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT trigger_type, trigger_value, response_type, response_description, intensity_level
                    FROM character_behavioral_triggers 
                    WHERE character_id = $1
                    ORDER BY intensity_level DESC, trigger_type
                """, character_id)

                return [BehavioralTrigger(
                    trigger_type=row['trigger_type'],
                    trigger_value=row['trigger_value'],
                    response_type=row['response_type'],
                    response_description=row['response_description'],
                    intensity_level=row['intensity_level']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving behavioral triggers for {character_name}: {e}")
            return []

    async def get_communication_patterns(self, character_name: str) -> List[CommunicationPattern]:
        """Get communication patterns including emoji usage and style"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT pattern_type, pattern_name, pattern_value, context, frequency, description
                    FROM character_communication_patterns 
                    WHERE character_id = $1
                    ORDER BY frequency DESC, pattern_type
                """, character_id)

                return [CommunicationPattern(
                    pattern_type=row['pattern_type'],
                    pattern_name=row['pattern_name'],
                    pattern_value=row['pattern_value'],
                    context=row['context'],
                    frequency=row['frequency'],
                    description=row['description']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving communication patterns for {character_name}: {e}")
            return []

    async def get_emoji_patterns(self, character_name: str) -> List[EmojiPattern]:
        """Get emoji usage patterns for different contexts and emotions"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT pattern_category, pattern_name, emoji_sequence, usage_context, frequency
                    FROM character_emoji_patterns 
                    WHERE character_id = $1
                    ORDER BY pattern_category, frequency DESC
                """, character_id)

                return [EmojiPattern(
                    pattern_category=row['pattern_category'],
                    pattern_name=row['pattern_name'],
                    emoji_sequence=row['emoji_sequence'],
                    usage_context=row['usage_context'],
                    frequency=row['frequency']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving emoji patterns for {character_name}: {e}")
            return []

    async def get_ai_scenarios(self, character_name: str) -> List[AIScenario]:
        """Get AI identity handling scenarios for physical interaction requests"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT scenario_type, scenario_name, trigger_phrases, response_pattern,
                           tier_1_response, tier_2_response, tier_3_response, example_usage
                    FROM character_ai_scenarios 
                    WHERE character_id = $1
                    ORDER BY scenario_type, scenario_name
                """, character_id)

                return [AIScenario(
                    scenario_type=row['scenario_type'],
                    scenario_name=row['scenario_name'],
                    trigger_phrases=row['trigger_phrases'],
                    response_pattern=row['response_pattern'],
                    tier_1_response=row['tier_1_response'],
                    tier_2_response=row['tier_2_response'],
                    tier_3_response=row['tier_3_response'],
                    example_usage=row['example_usage']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving AI scenarios for {character_name}: {e}")
            return []

    async def get_cultural_expressions(self, character_name: str) -> List[CulturalExpression]:
        """Get cultural expressions, language patterns, and heritage-specific phrases"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT expression_type, expression_value, meaning, usage_context, 
                           emotional_context, frequency
                    FROM character_cultural_expressions 
                    WHERE character_id = $1
                    ORDER BY frequency DESC, expression_type
                """, character_id)

                return [CulturalExpression(
                    expression_type=row['expression_type'],
                    expression_value=row['expression_value'],
                    meaning=row['meaning'],
                    usage_context=row['usage_context'],
                    emotional_context=row['emotional_context'],
                    frequency=row['frequency']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving cultural expressions for {character_name}: {e}")
            return []

    async def get_voice_traits(self, character_name: str) -> List[VoiceTrait]:
        """Get voice characteristics including tone, pace, accent, and vocabulary"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT trait_type, trait_value, situational_context, examples
                    FROM character_voice_traits 
                    WHERE character_id = $1
                    ORDER BY trait_type
                """, character_id)

                return [VoiceTrait(
                    trait_type=row['trait_type'],
                    trait_value=row['trait_value'],
                    situational_context=row['situational_context'],
                    examples=row['examples']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving voice traits for {character_name}: {e}")
            return []

    async def get_emotional_triggers(self, character_name: str) -> List[EmotionalTrigger]:
        """Get emotional triggers and appropriate character responses"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT trigger_type, trigger_category, trigger_content, 
                           emotional_response, response_intensity, response_examples
                    FROM character_emotional_triggers 
                    WHERE character_id = $1
                    ORDER BY trigger_type, response_intensity DESC
                """, character_id)

                return [EmotionalTrigger(
                    trigger_type=row['trigger_type'],
                    trigger_content=row['trigger_content'],
                    trigger_category=row['trigger_category'],
                    emotional_response=row['emotional_response'],
                    response_intensity=row['response_intensity'],
                    response_examples=row['response_examples']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving emotional triggers for {character_name}: {e}")
            return []

    async def get_expertise_domains(self, character_name: str) -> List[ExpertiseDomain]:
        """Get expertise domains, knowledge areas, and teaching approaches"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT domain_name, expertise_level, domain_description, 
                           key_concepts, teaching_approach, passion_level, examples
                    FROM character_expertise_domains 
                    WHERE character_id = $1
                    ORDER BY passion_level DESC NULLS LAST, expertise_level
                """, character_id)

                return [ExpertiseDomain(
                    domain_name=row['domain_name'],
                    expertise_level=row['expertise_level'],
                    domain_description=row['domain_description'],
                    key_concepts=row['key_concepts'],
                    teaching_approach=row['teaching_approach'],
                    passion_level=row['passion_level'],
                    examples=row['examples']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving expertise domains for {character_name}: {e}")
            return []

# ========================================================================================
            return None
    
    async def _build_cdl_structure(self, conn: asyncpg.Connection, character_row, character_id: int) -> Dict[str, Any]:
        """Build backward-compatible CDL structure (maintains API compatibility)"""
        
        # Core identity
        cdl_data = {
            'identity': {
                'name': character_row['name'],
                'occupation': character_row['occupation'] or '',
                'description': character_row['description'] or '',
                'archetype': character_row['archetype'] or ''
            },
            'allow_full_roleplay_immersion': character_row['allow_full_roleplay'] or False
        }
        
        # Personality traits
        traits_query = """
            SELECT trait_name, trait_value, intensity 
            FROM personality_traits 
            WHERE character_id = $1
        """
        traits_rows = await conn.fetch(traits_query, character_id)
        
        if traits_rows:
            cdl_data['personality'] = {'big_five': {}}
            for trait in traits_rows:
                cdl_data['personality']['big_five'][trait['trait_name']] = {
                    'value': float(trait['trait_value']) if trait['trait_value'] else 0.0,
                    'intensity': trait['intensity'] or ''
                }
        
        # Communication style
        comm_query = """
            SELECT engagement_level, formality, emotional_expression, 
                   response_length, conversation_flow_guidance, ai_identity_handling 
            FROM communication_styles 
            WHERE character_id = $1
        """
        comm_row = await conn.fetchrow(comm_query, character_id)
        
        if comm_row:
            cdl_data['communication_style'] = {
                'engagement_level': {
                    'value': float(comm_row['engagement_level']) if comm_row['engagement_level'] else 0.0,
                    'description': 'Engagement level'
                },
                'formality': {
                    'value': comm_row['formality'] or '',
                    'description': 'Communication formality'
                },
                'emotional_expression': {
                    'value': float(comm_row['emotional_expression']) if comm_row['emotional_expression'] else 0.0,
                    'description': 'Emotional expression level'
                },
                'response_length': {
                    'value': comm_row['response_length'] or '',
                    'description': 'Preferred response length'
                }
            }
            
            # Add additional fields if they exist
            if comm_row['conversation_flow_guidance']:
                cdl_data['communication_style']['conversation_flow_guidance'] = {
                    'value': comm_row['conversation_flow_guidance'],
                    'description': 'Conversation flow guidance'
                }
            if comm_row['ai_identity_handling']:
                cdl_data['communication_style']['ai_identity_handling'] = {
                    'value': comm_row['ai_identity_handling'], 
                    'description': 'AI identity handling approach'
                }
        
        # Values and beliefs
        values_query = """
            SELECT category, value_key, value_description, importance_level 
            FROM character_values 
            WHERE character_id = $1
        """
        values_rows = await conn.fetch(values_query, character_id)
        
        if values_rows:
            cdl_data['values_and_beliefs'] = {}
            for value in values_rows:
                category = value['category'] or 'general'
                if category not in cdl_data['values_and_beliefs']:
                    cdl_data['values_and_beliefs'][category] = []
                cdl_data['values_and_beliefs'][category].append({
                    'key': value['value_key'],
                    'description': value['value_description'],
                    'importance': value['importance_level']
                })
        
        return cdl_data
    
    async def _get_rich_character_data(self, conn: asyncpg.Connection, character_id: int) -> Dict[str, Any]:
        """Get comprehensive character data from new schema tables"""
        rich_data = {}
        
        # Character metadata
        metadata_query = """
            SELECT version, character_tags, created_date, updated_date, author, notes
            FROM character_metadata 
            WHERE character_id = $1
            ORDER BY version DESC LIMIT 1
        """
        metadata_row = await conn.fetchrow(metadata_query, character_id)
        if metadata_row:
            rich_data['metadata'] = dict(metadata_row)
        
        # Appearance data
        appearance_query = """
            SELECT category, attribute, value, description 
            FROM character_appearance 
            WHERE character_id = $1
            ORDER BY category, attribute
        """
        appearance_rows = await conn.fetch(appearance_query, character_id)
        if appearance_rows:
            rich_data['appearance'] = {}
            for row in appearance_rows:
                category = row['category']
                if category not in rich_data['appearance']:
                    rich_data['appearance'][category] = {}
                rich_data['appearance'][category][row['attribute']] = {
                    'value': row['value'],
                    'description': row['description']
                }
        
        # Background and history
        background_query = """
            SELECT category, period, title, description, date_range, importance_level
            FROM character_background 
            WHERE character_id = $1
            ORDER BY importance_level DESC, category
        """
        background_rows = await conn.fetch(background_query, character_id)
        if background_rows:
            rich_data['background'] = {}
            for row in background_rows:
                category = row['category']
                if category not in rich_data['background']:
                    rich_data['background'][category] = []
                rich_data['background'][category].append({
                    'period': row['period'],
                    'title': row['title'],
                    'description': row['description'],
                    'date_range': row['date_range'],
                    'importance_level': row['importance_level']
                })
        
        # Relationships
        relationships_query = """
            SELECT related_entity, relationship_type, relationship_strength, description, status
            FROM character_relationships 
            WHERE character_id = $1
            ORDER BY relationship_strength DESC
        """
        relationships_rows = await conn.fetch(relationships_query, character_id)
        if relationships_rows:
            rich_data['relationships'] = [dict(row) for row in relationships_rows]
        
        # Key memories
        memories_query = """
            SELECT memory_type, title, description, emotional_impact, time_period, importance_level, triggers
            FROM character_memories 
            WHERE character_id = $1
            ORDER BY importance_level DESC, emotional_impact DESC
        """
        memories_rows = await conn.fetch(memories_query, character_id)
        if memories_rows:
            rich_data['key_memories'] = [dict(row) for row in memories_rows]
        
        # Abilities
        abilities_query = """
            SELECT category, ability_name, proficiency_level, description, development_method, usage_frequency
            FROM character_abilities 
            WHERE character_id = $1
            ORDER BY category, proficiency_level DESC
        """
        abilities_rows = await conn.fetch(abilities_query, character_id)
        if abilities_rows:
            rich_data['abilities'] = {}
            for row in abilities_rows:
                category = row['category']
                if category not in rich_data['abilities']:
                    rich_data['abilities'][category] = []
                rich_data['abilities'][category].append(dict(row))
        
        # Communication patterns
        patterns_query = """
            SELECT pattern_type, pattern_name, pattern_value, context, frequency, description
            FROM character_communication_patterns 
            WHERE character_id = $1
            ORDER BY pattern_type, frequency DESC
        """
        patterns_rows = await conn.fetch(patterns_query, character_id)
        if patterns_rows:
            rich_data['communication_patterns'] = {}
            for row in patterns_rows:
                pattern_type = row['pattern_type']
                if pattern_type not in rich_data['communication_patterns']:
                    rich_data['communication_patterns'][pattern_type] = []
                rich_data['communication_patterns'][pattern_type].append(dict(row))
        
        # Behavioral triggers
        triggers_query = """
            SELECT trigger_type, trigger_value, response_type, response_description, intensity_level
            FROM character_behavioral_triggers 
            WHERE character_id = $1
            ORDER BY intensity_level DESC
        """
        triggers_rows = await conn.fetch(triggers_query, character_id)
        if triggers_rows:
            rich_data['behavioral_triggers'] = [dict(row) for row in triggers_rows]
        
        # Essence (for mystical characters)
        essence_query = """
            SELECT essence_type, essence_name, description, manifestation, power_level
            FROM character_essence 
            WHERE character_id = $1
            ORDER BY essence_type
        """
        essence_rows = await conn.fetch(essence_query, character_id)
        if essence_rows:
            rich_data['essence'] = {}
            for row in essence_rows:
                essence_type = row['essence_type']
                if essence_type not in rich_data['essence']:
                    rich_data['essence'][essence_type] = []
                rich_data['essence'][essence_type].append(dict(row))
        
        # Custom instructions
        instructions_query = """
            SELECT instruction_type, instruction_text, priority, context, active
            FROM character_instructions 
            WHERE character_id = $1 AND active = true
            ORDER BY priority DESC, instruction_type
        """
        instructions_rows = await conn.fetch(instructions_query, character_id)
        if instructions_rows:
            rich_data['custom_instructions'] = {}
            for row in instructions_rows:
                instruction_type = row['instruction_type']
                if instruction_type not in rich_data['custom_instructions']:
                    rich_data['custom_instructions'][instruction_type] = []
                rich_data['custom_instructions'][instruction_type].append(dict(row))
        
        return rich_data
    
    # ========================================================================================
    # RICH DATA MANAGEMENT METHODS (New functionality for comprehensive character management)
    # ========================================================================================
    
    async def add_character_appearance(self, character_name: str, appearances: List[CharacterAppearance]) -> bool:
        """Add appearance data for a character"""
        try:
            async with self.pool.acquire() as conn:
                # Get character ID
                char_id = await self._get_character_id(conn, character_name)
                if not char_id:
                    return False
                
                # Insert appearance data
                for appearance in appearances:
                    await conn.execute("""
                        INSERT INTO character_appearance (character_id, category, attribute, value, description)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (character_id, category, attribute) 
                        DO UPDATE SET value = $4, description = $5
                    """, char_id, appearance.category, appearance.attribute, 
                         appearance.value, appearance.description)
                
                return True
        except Exception as e:
            logger.error(f"Error adding appearance for {character_name}: {e}")
            return False
    
    async def add_character_background(self, character_name: str, background_items: List[CharacterBackground]) -> bool:
        """Add background/history data for a character"""
        try:
            async with self.pool.acquire() as conn:
                char_id = await self._get_character_id(conn, character_name)
                if not char_id:
                    return False
                
                for bg in background_items:
                    await conn.execute("""
                        INSERT INTO character_background 
                        (character_id, category, period, title, description, date_range, importance_level)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, char_id, bg.category, bg.period, bg.title, 
                         bg.description, bg.date_range, bg.importance_level)
                
                return True
        except Exception as e:
            logger.error(f"Error adding background for {character_name}: {e}")
            return False
    
    async def add_character_memories(self, character_name: str, memories: List[CharacterMemory]) -> bool:
        """Add key memories for a character"""
        try:
            async with self.pool.acquire() as conn:
                char_id = await self._get_character_id(conn, character_name)
                if not char_id:
                    return False
                
                for memory in memories:
                    await conn.execute("""
                        INSERT INTO character_memories 
                        (character_id, memory_type, title, description, emotional_impact, 
                         time_period, importance_level, triggers)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, char_id, memory.memory_type, memory.title, memory.description,
                         memory.emotional_impact, memory.time_period, memory.importance_level,
                         memory.triggers)
                
                return True
        except Exception as e:
            logger.error(f"Error adding memories for {character_name}: {e}")
            return False
    
    async def add_character_abilities(self, character_name: str, abilities: List[CharacterAbility]) -> bool:
        """Add abilities/skills for a character"""
        try:
            async with self.pool.acquire() as conn:
                char_id = await self._get_character_id(conn, character_name)
                if not char_id:
                    return False
                
                for ability in abilities:
                    await conn.execute("""
                        INSERT INTO character_abilities 
                        (character_id, category, ability_name, proficiency_level, description, 
                         development_method, usage_frequency)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (character_id, category, ability_name) 
                        DO UPDATE SET proficiency_level = $4, description = $5, 
                                     development_method = $6, usage_frequency = $7
                    """, char_id, ability.category, ability.ability_name, ability.proficiency_level,
                         ability.description, ability.development_method, ability.usage_frequency)
                
                return True
        except Exception as e:
            logger.error(f"Error adding abilities for {character_name}: {e}")
            return False
    
    async def _get_character_id(self, conn: asyncpg.Connection, character_name: str) -> Optional[int]:
        """Helper to get character ID by name or normalized name (bot_name)"""
        # Try normalized_name first (for bot_name lookups like "elena")
        row = await conn.fetchrow("SELECT id FROM characters WHERE LOWER(normalized_name) = LOWER($1)", character_name)
        if row:
            return row['id']
        # Fallback to full name match for backward compatibility
        row = await conn.fetchrow("SELECT id FROM characters WHERE LOWER(name) = LOWER($1)", character_name)
        return row['id'] if row else None
    
    # ========================================================================================
    # BACKWARD COMPATIBILITY METHODS (maintain existing API)
    # ========================================================================================
    
    async def get_character_by_bot_name(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """Get character by bot name from environment - maintains backward compatibility"""
        if bot_name.startswith('bot_'):
            bot_name = bot_name[4:]  # Remove bot_ prefix
        return await self.get_character_by_name(bot_name)

# ========================================================================================
# FACTORY FUNCTION (maintains same API as simple manager)
# ========================================================================================

def create_enhanced_cdl_manager(pool: asyncpg.Pool) -> EnhancedCDLManager:
    """Factory function to create enhanced CDL manager"""
    return EnhancedCDLManager(pool)

# Alias for backward compatibility
create_cdl_manager = create_enhanced_cdl_manager

# ========================================================================================
# TESTING AND VALIDATION
# ========================================================================================

async def test_enhanced_manager():
    """Test the enhanced CDL manager functionality"""
    import asyncpg
    
    # Database connection
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        manager = create_enhanced_cdl_manager(pool)
        
        # Test with character from environment (character-agnostic)
        character_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
        character_data = await manager.get_character_by_name(character_name)
        if character_data:
            print(f"✅ Enhanced manager successfully loaded {character_name}")
            print(f"  Core CDL structure: {list(character_data.keys())}")
            
            # Show rich data if available
            if 'appearance' in character_data:
                print(f"  🆕 Rich appearance data: {list(character_data['appearance'].keys())}")
            if 'background' in character_data:
                print(f"  🆕 Rich background data: {list(character_data['background'].keys())}")
            if 'abilities' in character_data:
                print(f"  🆕 Rich abilities data: {list(character_data['abilities'].keys())}")
        else:
            print(f"❌ Could not load {character_name} data")
        
        await pool.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_manager())