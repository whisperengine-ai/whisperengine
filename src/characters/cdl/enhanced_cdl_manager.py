"""
Enhanced CDL Manager for Comprehensive RDBMS Schema
WhisperEngine Character Definition Language Manager
Version: 2.0 - October 2025

Maintains backward compatibility with CDL AI Integration while providing
access to rich character data through clean relational design.
"""

import os
import json
import ast
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

@dataclass 
class InteractionMode:
    mode_name: str  # 'creative', 'technical', 'educational', 'casual'
    mode_description: str
    trigger_keywords: List[str]  # Keywords that activate this mode
    response_guidelines: str  # How to respond in this mode
    avoid_patterns: List[str]  # What to avoid in this mode
    is_default: bool  # Whether this is the default mode
    priority: int

@dataclass
class InterestTopic:
    topic_keyword: str
    boost_weight: float
    category: str = 'general'  # 'primary_interest', 'secondary_interest', 'general'
    gap_type_preference: Optional[str] = None  # 'origin', 'experience', 'specifics', 'location'

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
            
            # Import and use proper normalization function
            from src.utils.bot_name_utils import normalize_bot_name
            normalized_name = normalize_bot_name(character_name)
            
            async with self.pool.acquire() as conn:
                # Core character data - search by normalized name ONLY (the primary key)
                core_query = """
                    SELECT c.*, 
                           COALESCE(c.created_date, CURRENT_TIMESTAMP) as created_date,
                           COALESCE(c.updated_date, CURRENT_TIMESTAMP) as updated_date
                    FROM characters c 
                    WHERE c.normalized_name = $1
                """
                logger.info("🔍 ENHANCED CDL: Executing query for character: '%s' (normalized: '%s')", character_name, normalized_name)
                character_row = await conn.fetchrow(core_query, normalized_name)
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

    async def get_interest_topics(self, character_name: str) -> List[InterestTopic]:
        """Get character interest topics for personality-based question filtering"""
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    return []

                rows = await conn.fetch("""
                    SELECT topic_keyword, boost_weight, gap_type_preference, category
                    FROM character_interest_topics 
                    WHERE character_id = $1
                    ORDER BY boost_weight DESC, topic_keyword
                """, character_id)

                return [InterestTopic(
                    topic_keyword=row['topic_keyword'],
                    boost_weight=row['boost_weight'],
                    category=row['category'],
                    gap_type_preference=row['gap_type_preference']
                ) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving interest topics for {character_name}: {e}")
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

    async def get_interaction_modes(self, character_name: str) -> List[InteractionMode]:
        """
        Get interaction modes for context-aware response switching.
        Uses existing character_conversation_modes, character_mode_guidance, and character_message_triggers tables.
        """
        logger.info(f"🎭 GET_INTERACTION_MODES: Called for character '{character_name}'")
        try:
            async with self.pool.acquire() as conn:
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    logger.warning(f"🎭 GET_INTERACTION_MODES: No character ID found for '{character_name}'")
                    return []

                logger.info(f"🎭 GET_INTERACTION_MODES: Querying database for character_id={character_id}")
                
                # Query actual database schema (character_conversation_modes + character_mode_guidance + character_message_triggers)
                rows = await conn.fetch("""
                    SELECT DISTINCT
                        ccm.mode_name,
                        ccm.approach as mode_description,
                        ccm.energy_level as response_guidelines,
                        COALESCE(
                            array_agg(DISTINCT cmt.trigger_value) FILTER (WHERE cmt.trigger_value IS NOT NULL),
                            ARRAY[]::text[]
                        ) as trigger_keywords,
                        COALESCE(
                            array_agg(DISTINCT cmg.guidance_text) FILTER (WHERE cmg.guidance_type = 'avoid'),
                            ARRAY[]::text[]
                        ) as avoid_patterns,
                        false as is_default,
                        1 as priority
                    FROM character_conversation_modes ccm
                    LEFT JOIN character_mode_guidance cmg ON ccm.id = cmg.mode_id
                    LEFT JOIN character_message_triggers cmt ON cmt.character_id = ccm.character_id 
                        AND (cmt.response_mode = ccm.mode_name OR cmt.trigger_category LIKE '%' || ccm.mode_name || '%')
                    WHERE ccm.character_id = $1
                    GROUP BY ccm.id, ccm.mode_name, ccm.approach, ccm.energy_level
                    ORDER BY ccm.mode_name
                """, character_id)

                logger.info(f"🎭 GET_INTERACTION_MODES: Query returned {len(rows)} rows")

                modes = []
                for row in rows:
                    modes.append(InteractionMode(
                        mode_name=row['mode_name'],
                        mode_description=row['mode_description'] or '',
                        trigger_keywords=row['trigger_keywords'] or [],
                        response_guidelines=row['response_guidelines'] or '',
                        avoid_patterns=row['avoid_patterns'] or [],
                        is_default=row['is_default'],
                        priority=row['priority']
                    ))
                
                logger.info(f"✅ INTERACTION MODES: Loaded {len(modes)} modes for {character_name}: {[m.mode_name for m in modes]}")
                return modes

        except Exception as e:
            logger.error(f"❌ ERROR retrieving interaction modes for {character_name}: {e}", exc_info=True)
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
        
        # Core identity - include emoji configuration from character_row
        cdl_data = {
            'id': character_id,  # Include character ID for persistence operations
            'identity': {
                'name': character_row['name'],
                'occupation': character_row['occupation'] or '',
                'description': character_row['description'] or '',
                'archetype': character_row['archetype'] or '',
                'emoji_frequency': character_row.get('emoji_frequency', 'moderate'),
                'emoji_style': character_row.get('emoji_style', 'general'),
                'emoji_combination': character_row.get('emoji_combination', 'text_with_accent_emoji'),
                'emoji_placement': character_row.get('emoji_placement', 'end_of_message'),
                'emoji_age_demographic': character_row.get('emoji_age_demographic', 'millennial'),
                'emoji_cultural_influence': character_row.get('emoji_cultural_influence', 'general')
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
                trait_name = trait['trait_name']
                trait_value = float(trait['trait_value']) if trait['trait_value'] else 0.0
                intensity = trait['intensity'] or 'medium'
                
                # 🚨 FIX: Generate human-readable trait description instead of raw dict
                level = 'Very High' if trait_value >= 0.9 else 'High' if trait_value >= 0.7 else 'Moderate' if trait_value >= 0.4 else 'Low'
                trait_display = trait_name.replace('_', ' ').title()
                
                cdl_data['personality']['big_five'][trait_name] = f"{trait_display}: {level} ({trait_value:.2f}) - {intensity} intensity"
        
        # Communication style
        comm_query = """
            SELECT engagement_level, formality, emotional_expression, 
                   response_length
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
            
            # 🚨 DEPRECATED: conversation_flow_guidance loading removed (no longer used in prompts)
            # Conversation flow data is accessed directly via get_interaction_modes() which queries:
            # - character_conversation_modes (mode definitions)
            # - character_mode_guidance (avoid/encourage patterns)
            # - character_mode_examples (usage examples)
            # This is only loaded when needed during prompt building, not during character object initialization.
            # Data still exists in normalized tables for web UI editing.
                    
            # 🚀 NEW: Load AI identity handling from normalized roleplay config table
            # This replaces complex parsing of denormalized ai_identity_handling text field
            cdl_data['communication_style']['ai_identity_handling'] = await self._load_ai_identity_from_normalized_tables(conn, character_id)
        
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
        """Helper to get character ID by normalized name (the primary key)"""
        # Import and use proper normalization function
        from src.utils.bot_name_utils import normalize_bot_name
        normalized_name = normalize_bot_name(character_name)
        
        # Use normalized name only - it's the primary key
        row = await conn.fetchrow("SELECT id FROM characters WHERE normalized_name = $1", normalized_name)
        return row['id'] if row else None
    
    # ========================================================================================
    # BACKWARD COMPATIBILITY METHODS (maintain existing API)
    # ========================================================================================
    
    async def get_character_by_bot_name(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """Get character by bot name from environment - maintains backward compatibility"""
        if bot_name.startswith('bot_'):
            bot_name = bot_name[4:]  # Remove bot_ prefix
        return await self.get_character_by_name(bot_name)

    def _format_conversation_guidance(self, json_string: str) -> str:
        """🚨 FIX: Convert raw JSON conversation guidance to human-readable format"""
        try:
            import json
            if not json_string or json_string == '{}':
                return "Standard conversation approach"
                
            data = json.loads(json_string) if isinstance(json_string, str) else json_string
            if not isinstance(data, dict):
                return str(data)
                
            # Format key conversation modes
            formatted_parts = []
            for mode, details in data.items():
                if isinstance(details, dict):
                    energy = details.get('energy', '')
                    approach = details.get('approach', '')
                    if energy and approach:
                        formatted_parts.append(f"• {mode.replace('_', ' ').title()}: {energy} - {approach}")
                        
            return "; ".join(formatted_parts) if formatted_parts else "Adaptive conversation style"
        except:
            return "Standard conversation approach"
    
    async def _load_conversation_flow_guidance(self, conn, character_id: int) -> Dict[str, Any]:
        """Load conversation flow guidance from normalized RDBMS tables (replaces JSON parsing)."""
        guidance_data = {}
        
        try:
            # Load conversation modes
            modes_query = """
                SELECT mode_name, energy_level, approach, transition_style
                FROM character_conversation_modes 
                WHERE character_id = $1
                ORDER BY mode_name
            """
            mode_rows = await conn.fetch(modes_query, character_id)
            
            for mode_row in mode_rows:
                mode_name = mode_row['mode_name']
                mode_data = {
                    'energy': mode_row['energy_level'] or '',
                    'approach': mode_row['approach'] or '',
                    'transition_style': mode_row['transition_style'] or '',
                    'avoid': [],
                    'encourage': [],
                    'examples': []
                }
                
                # Load guidance items for this mode
                guidance_query = """
                    SELECT guidance_type, guidance_text
                    FROM character_mode_guidance mg
                    JOIN character_conversation_modes cm ON mg.mode_id = cm.id
                    WHERE cm.character_id = $1 AND cm.mode_name = $2
                    ORDER BY mg.sort_order
                """
                guidance_rows = await conn.fetch(guidance_query, character_id, mode_name)
                
                for guidance_row in guidance_rows:
                    guidance_type = guidance_row['guidance_type']
                    guidance_text = guidance_row['guidance_text']
                    
                    if guidance_type in ['avoid', 'encourage']:
                        mode_data[guidance_type].append(guidance_text)
                
                # Load examples for this mode
                examples_query = """
                    SELECT example_text
                    FROM character_mode_examples me
                    JOIN character_conversation_modes cm ON me.mode_id = cm.id
                    WHERE cm.character_id = $1 AND cm.mode_name = $2
                    ORDER BY me.sort_order
                """
                example_rows = await conn.fetch(examples_query, character_id, mode_name)
                
                for example_row in example_rows:
                    mode_data['examples'].append(example_row['example_text'])
                
                guidance_data[mode_name] = mode_data
            
            # Load general conversation settings
            general_query = """
                SELECT default_energy, conversation_style, transition_approach
                FROM character_general_conversation
                WHERE character_id = $1
            """
            general_row = await conn.fetchrow(general_query, character_id)
            
            if general_row:
                guidance_data['general'] = {
                    'default_energy': general_row['default_energy'] or '',
                    'conversation_style': general_row['conversation_style'] or '',
                    'transition_approach': general_row['transition_approach'] or ''
                }
            
            # Load response style
            response_style_query = """
                SELECT item_type, item_text
                FROM character_response_style_items rsi
                JOIN character_response_style rs ON rsi.response_style_id = rs.id
                WHERE rs.character_id = $1
                ORDER BY rsi.item_type, rsi.sort_order
            """
            response_rows = await conn.fetch(response_style_query, character_id)
            
            if response_rows:
                response_style = {
                    'core_principles': [],
                    'formatting_rules': [],
                    'character_specific_adaptations': []
                }
                
                for response_row in response_rows:
                    item_type = response_row['item_type']
                    item_text = response_row['item_text']
                    
                    if item_type in response_style:
                        response_style[item_type].append(item_text)
                
                guidance_data['response_style'] = response_style
            
            logger.info(f"✅ NORMALIZED: Loaded conversation flow guidance for character {character_id} from RDBMS tables")
            return guidance_data
            
        except Exception as e:
            logger.error(f"Error loading conversation flow guidance from RDBMS: {e}")
            return {}

    async def _load_ai_identity_from_normalized_tables(self, conn, character_id: int) -> Dict[str, Any]:
        """Load AI identity handling from normalized roleplay config tables (replaces text field parsing)."""
        try:
            # Load core roleplay configuration
            roleplay_query = """
                SELECT allow_full_roleplay_immersion, philosophy, strategy
                FROM character_roleplay_config 
                WHERE character_id = $1
            """
            roleplay_row = await conn.fetchrow(roleplay_query, character_id)
            
            if not roleplay_row:
                logger.warning(f"No roleplay config found for character {character_id}, using defaults")
                return {
                    'allow_full_roleplay_immersion': False,
                    'philosophy': '',
                    'approach': ''
                }
            
            # Build core AI identity structure
            # NOTE: Removed legacy roleplay_interaction_scenarios loading from character_roleplay_scenarios table
            # Modern system uses character_ai_scenarios table with generic_keyword_templates for trigger detection
            # See get_ai_scenarios() method and cdl_ai_integration.py line 1092 for active implementation
            ai_identity = {
                'allow_full_roleplay_immersion': roleplay_row['allow_full_roleplay_immersion'] or False,
                'philosophy': roleplay_row['philosophy'] or '',
                'approach': roleplay_row['strategy'] or ''
            }
            
            logger.info(f"✅ NORMALIZED: Loaded AI identity config for character {character_id} from roleplay_config table")
            return ai_identity
            
        except Exception as e:
            logger.error(f"Error loading AI identity from normalized tables: {e}")
            # Return safe defaults on error
            return {
                'allow_full_roleplay_immersion': False,
                'philosophy': '',
                'approach': ''
            }

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
    # ========================================================================================
# FACTORY FUNCTION (maintains same API as simple manager)
# ========================================================================================

        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_manager())