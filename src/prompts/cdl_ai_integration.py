"""
CDL Integration with AI Pipeline Prompt System - CLEANED VERSION
"""

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional, Any
from pathlib import Path

from src.characters.cdl.parser import Character
from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager
from src.prompts.trigger_mode_controller import TriggerModeController

logger = logging.getLogger(__name__)

class CDLAIPromptIntegration:
    def __init__(self, vector_memory_manager=None, llm_client=None, knowledge_router=None, bot_core=None, semantic_router=None, enhanced_manager=None):
        self.memory_manager = vector_memory_manager
        self.llm_client = llm_client
        self.knowledge_router = knowledge_router
        self.semantic_router = semantic_router  # NEW: Store semantic router for user facts cross-pollination
        self.bot_core = bot_core  # Store bot_core for personality profiler access
        self.enhanced_manager = enhanced_manager  # NEW: Enhanced CDL manager for rich character data
        self._graph_manager = None  # Cache for CharacterGraphManager
        self._graph_manager_initialized = False
        self._context_enhancer = None  # Cache for CharacterContextEnhancer (Phase 2B)
        
        # 🎭 TRIGGER-BASED MODE CONTROL: Initialize intelligent mode switching
        self.trigger_mode_controller = TriggerModeController(enhanced_manager=enhanced_manager)
        self._previous_mode = None  # Track mode changes for transition detection
        
        # Initialize the optimized prompt builder for size management
        from src.prompts.optimized_prompt_builder import create_optimized_prompt_builder
        self.optimized_builder = create_optimized_prompt_builder(
            max_words=3000,  # Increased from 2000 to 3000 to match backup version
            llm_client=llm_client,
            memory_manager=vector_memory_manager
        )
        
        # Initialize fidelity metrics collector
        try:
            from src.monitoring.fidelity_metrics_collector import get_fidelity_metrics_collector
            self.fidelity_metrics = get_fidelity_metrics_collector()
        except ImportError:
            self.fidelity_metrics = None

    def _record_fidelity_optimization_metrics(self, operation: str, original_word_count: int, 
                                            optimized_word_count: int, optimization_ratio: float,
                                            character_preservation_score: float, context_quality_score: float,
                                            full_fidelity_used: bool, intelligent_trimming_applied: bool):
        """Record fidelity optimization metrics to InfluxDB."""
        if not self.fidelity_metrics:
            return
        
        try:
            from src.monitoring.fidelity_metrics_collector import FidelityOptimizationMetric
            from datetime import datetime, timezone
            
            optimization_metric = FidelityOptimizationMetric(
                operation=operation,
                original_word_count=original_word_count,
                optimized_word_count=optimized_word_count,
                optimization_ratio=optimization_ratio,
                character_preservation_score=character_preservation_score,
                context_quality_score=context_quality_score,
                full_fidelity_used=full_fidelity_used,
                intelligent_trimming_applied=intelligent_trimming_applied,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.fidelity_metrics.record_fidelity_optimization(optimization_metric)
            logger.debug("📊 Recorded fidelity optimization metrics: %s (%.1f%% optimization ratio)", 
                        operation, optimization_ratio * 100)
        except Exception as e:
            logger.warning("Failed to record fidelity optimization metrics: %s", str(e))

    def _get_safe_bot_name(self, character=None):
        """Helper method to get safe bot name with fallback."""
        fallback = "unknown"
        if character and hasattr(character, 'identity') and hasattr(character.identity, 'name'):
            fallback = character.identity.name
        return os.getenv('DISCORD_BOT_NAME', fallback).lower()

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 PROMPT QUALITY: Numeric Scale Translation Helpers
    # ═══════════════════════════════════════════════════════════════════════════════
    # These functions translate internal numeric scales (0.0-1.0) into clear,
    # actionable natural language that LLMs can actually understand and act on.
    # Added: October 2025 - System Prompt Quality Audit
    # ═══════════════════════════════════════════════════════════════════════════════

    def _translate_engagement_level(self, value: float) -> str:
        """Translate numeric engagement level to actionable LLM guidance"""
        try:
            val = float(value)
            if val >= 0.8:
                return "High - be very warm and actively engaged in the conversation"
            elif val >= 0.6:
                return "Moderately high - be warm and engaged with natural enthusiasm"
            elif val >= 0.4:
                return "Moderate - balanced engagement without being overwhelming"
            elif val >= 0.2:
                return "Reserved - be respectful but not overly enthusiastic"
            else:
                return "Minimal - respond professionally but briefly"
        except (ValueError, TypeError):
            return f"{value}"  # Fallback to original if not numeric

    def _translate_emotional_expression(self, value: float) -> str:
        """Translate numeric emotional expression to actionable LLM guidance"""
        try:
            val = float(value)
            if val >= 0.8:
                return "Very expressive - show emotions openly and enthusiastically"
            elif val >= 0.6:
                return "Moderately expressive - show warmth and enthusiasm naturally"
            elif val >= 0.4:
                return "Balanced - show appropriate emotion for the context"
            elif val >= 0.2:
                return "Reserved - be measured and calm in emotional expression"
            else:
                return "Minimal - maintain professional composure"
        except (ValueError, TypeError):
            return f"{value}"  # Fallback to original if not numeric

    def _translate_emotion_confidence(self, emotion: str, confidence: float) -> str:
        """Translate emotion detection confidence to natural language guidance"""
        try:
            conf = float(confidence)
            if conf >= 0.8:
                return f"{emotion}"  # High confidence - state directly
            elif conf >= 0.5:
                return f"{emotion} (likely)"  # Medium confidence - add qualifier
            else:
                return f"{emotion} (uncertain)"  # Low confidence - acknowledge uncertainty
        except (ValueError, TypeError):
            return emotion  # Fallback to just emotion name

    async def _load_and_format_big_five(self, character_id: int, tactical_shifts: dict = None) -> str:
        """Load Big Five personality traits from database and format in natural language
        
        Args:
            character_id: Database ID of character
            tactical_shifts: Optional dict of emotional adaptation adjustments like {"extraversion": -0.1, "agreeableness": +0.15}
        """
        try:
            from src.database.postgres_pool_manager import get_postgres_pool
            pool = await get_postgres_pool()
            if not pool:
                return ""
            
            async with pool.acquire() as conn:
                # Load Big Five traits from database
                query = """
                    SELECT trait_name, trait_value, intensity, description
                    FROM personality_traits
                    WHERE character_id = $1
                    AND trait_name IN ('openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism')
                    ORDER BY trait_name
                """
                rows = await conn.fetch(query, character_id)
                
                if not rows:
                    return ""  # No Big Five data
                
                # Build natural language personality profile
                lines = ["\n\n🧠 PERSONALITY CORE:"]
                
                trait_descriptions = {
                    'openness': {
                        'very_high': "Extremely curious and creative - loves exploring new ideas and perspectives",
                        'high': "Open-minded and intellectually curious - enjoys new experiences",
                        'medium': "Balanced between tradition and innovation",
                        'low': "Prefers familiar approaches and proven methods"
                    },
                    'conscientiousness': {
                        'very_high': "Extremely organized, thorough, and detail-oriented in all work",
                        'high': "Organized and reliable with strong attention to detail",
                        'medium': "Balanced organization and flexibility",
                        'low': "Spontaneous and flexible, less focused on rigid planning"
                    },
                    'extraversion': {
                        'very_high': "Highly energetic, outgoing, and socially enthusiastic",
                        'high': "Energetic and sociable, especially when discussing passion topics",
                        'medium': "Ambivert - balanced between social and reflective modes",
                        'low': "Thoughtful and reserved, prefers deeper one-on-one conversations"
                    },
                    'agreeableness': {
                        'very_high': "Extremely warm, empathetic, and collaborative with others",
                        'high': "Warm, compassionate, and supportive in interactions",
                        'medium': "Balanced between empathy and directness",
                        'low': "Direct and straightforward, values truth over harmony"
                    },
                    'neuroticism': {
                        'very_high': "Emotionally sensitive with strong reactions to stress",
                        'high': "Emotionally responsive, shows feelings openly",
                        'medium': "Generally stable with normal emotional responses",
                        'low': "Very emotionally stable and resilient under pressure"
                    }
                }
                
                for row in rows:
                    trait_name = row['trait_name']
                    # Convert Decimal to float for arithmetic operations
                    trait_value = float(row['trait_value']) if row['trait_value'] is not None else 0.5
                    intensity = row['intensity']
                    
                    # Use database description if available, otherwise use translation
                    if row['description']:
                        description = row['description']
                    elif trait_name in trait_descriptions and intensity in trait_descriptions[trait_name]:
                        description = trait_descriptions[trait_name][intensity]
                    else:
                        description = f"{intensity} {trait_name}"
                    
                    # Check for tactical emotional adaptation shifts
                    if tactical_shifts and trait_name in tactical_shifts:
                        shift = tactical_shifts[trait_name]
                        adjusted_value = max(0.0, min(1.0, trait_value + shift))  # Clamp to 0-1
                        direction = "⚡↗" if shift > 0 else "⚡↘" if shift < 0 else "⚡→"
                        lines.append(
                            f"• {trait_name.title()}: {description} "
                            f"({trait_value:.2f} {direction} {adjusted_value:.2f} - emotionally adapted for this conversation)"
                        )
                    else:
                        lines.append(f"• {trait_name.title()}: {description}")
                
                return "\n".join(lines)
                
        except Exception as e:
            logger.warning(f"Could not load Big Five personality: {e}")
            return ""

    async def build_confidence_aware_context(
        self,
        user_facts: list,
        confidence_threshold_high: float = 0.9,
        confidence_threshold_medium: float = 0.6
    ) -> str:
        """
        🎚️ STEP 6: Confidence-Aware Conversations
        
        Format user facts with confidence-aware language:
        - High confidence (0.9+): "The user loves pizza"
        - Medium confidence (0.6-0.8): "The user mentioned liking pizza"  
        - Low confidence (<0.6): "The user may like pizza (unconfirmed)"
        
        Args:
            user_facts: List of fact dictionaries with 'entity_name', 'relationship_type', 'confidence'
            confidence_threshold_high: Threshold for high confidence statements (default 0.9)
            confidence_threshold_medium: Threshold for medium confidence statements (default 0.6)
            
        Returns:
            Formatted confidence-aware context string
        """
        if not user_facts:
            return ""
        
        context_parts = []
        for fact in user_facts:
            confidence = fact.get('confidence', 0.0)
            entity = fact.get('entity_name', '')
            entity_type = fact.get('entity_type', '')
            relationship = fact.get('relationship_type', 'related to')
            
            if not entity:
                continue
            
            # Add entity type context when available (e.g., "pizza (food)")
            entity_display = f"{entity} ({entity_type})" if entity_type else entity
                
            # Format based on confidence levels for natural conversation
            if confidence >= confidence_threshold_high:
                # High confidence: Definitive statements
                if 'likes' in relationship.lower() or 'loves' in relationship.lower():
                    context_parts.append(f"The user loves {entity_display}")
                elif 'enjoys' in relationship.lower():
                    context_parts.append(f"The user enjoys {entity_display}")
                elif 'interested' in relationship.lower():
                    context_parts.append(f"The user is interested in {entity_display}")
                elif 'favorite' in relationship.lower():
                    context_parts.append(f"The user's favorite {entity_type or 'thing'} is {entity}")
                else:
                    context_parts.append(f"The user {relationship} {entity_display}")
                    
            elif confidence >= confidence_threshold_medium:
                # Medium confidence: Tentative but acknowledged
                if 'likes' in relationship.lower():
                    context_parts.append(f"The user mentioned liking {entity_display}")
                elif 'enjoys' in relationship.lower():
                    context_parts.append(f"The user mentioned enjoying {entity_display}")
                elif 'interested' in relationship.lower():
                    context_parts.append(f"The user expressed interest in {entity_display}")
                elif 'favorite' in relationship.lower():
                    context_parts.append(f"The user mentioned {entity} as a favorite {entity_type or 'item'}")
                else:
                    context_parts.append(f"The user mentioned {relationship} {entity_display}")
                    
            else:
                # Low confidence: Uncertain/questioning
                if 'likes' in relationship.lower():
                    context_parts.append(f"The user may like {entity} (unconfirmed)")
                elif 'interested' in relationship.lower():
                    context_parts.append(f"The user might be interested in {entity} (tentative)")
                else:
                    context_parts.append(f"The user possibly {relationship} {entity} (low confidence)")
        
        if context_parts:
            # Return single formatted fact for integration
            return context_parts[0]  # Return first fact formatted
        
        return ""

    async def generate_curiosity_questions(
        self,
        user_id: str,
        character_name: str,
        semantic_router=None
    ) -> list:
        """
        🎯 STEP 7: Intelligent Question Generation
        
        Analyze user facts for knowledge gaps and generate natural follow-up questions.
        Characters ask deeper questions about established interests to build richer understanding.
        
        Examples:
        - Known: User loves marine biology (confidence 0.9) → Unknown: How they learned about it
        - Generate: "How did you first get interested in marine biology?"
        
        Args:
            user_id: User identifier
            character_name: Character asking questions (for personality matching)
            semantic_router: Router for fact retrieval (optional, uses self.semantic_router if available)
            
        Returns:
            List of generated curiosity questions with metadata
        """
        if not semantic_router and not self.semantic_router:
            return []
        
        router = semantic_router or self.semantic_router
        
        try:
            # Get user facts to identify knowledge gaps
            facts = await router.get_character_aware_facts(
                user_id=user_id,
                character_name=character_name,
                limit=50
            )
            
            if not facts:
                return []
            
            # Filter for high-confidence facts (established interests)
            high_confidence_facts = []
            for fact in facts:
                confidence = fact.get('confidence', 0.0)
                if confidence > 0.8:  # High confidence threshold
                    high_confidence_facts.append(fact)
            
            if not high_confidence_facts:
                return []
            
            # Generate gap analysis questions
            curiosity_questions = []
            
            for fact in high_confidence_facts[:5]:  # Limit to top 5 facts
                entity_name = fact.get('entity_name', '')
                relationship = fact.get('relationship_type', '')
                confidence = fact.get('confidence', 0.0)
                
                if not entity_name:
                    continue
                
                # Analyze what we DON'T know about this entity
                gap_questions = await self._identify_knowledge_gaps(
                    entity_name, relationship, confidence, facts, character_name
                )
                
                curiosity_questions.extend(gap_questions)
            
            # Character-specific filtering and personality matching
            personality_matched_questions = await self._filter_questions_by_character_personality(
                curiosity_questions, character_name
            )
            
            # Remove duplicates and prioritize
            unique_questions = self._deduplicate_and_prioritize_questions(personality_matched_questions)
            
            return unique_questions[:3]  # Return top 3 questions
            
        except Exception as e:
            logger.debug(f"Failed to generate curiosity questions: {e}")
            return []

    async def _identify_knowledge_gaps(
        self, 
        entity_name: str, 
        relationship: str, 
        confidence: float,
        all_facts: list,
        character_name: str
    ) -> list:
        """Identify specific knowledge gaps around an entity - DATABASE DRIVEN"""
        gap_questions = []
        
        # Get character-specific gap patterns from database
        gap_patterns = await self._get_character_gap_patterns(character_name)
        
        if not gap_patterns:
            # Fallback to minimal default patterns if database query fails
            logger.warning(f"⚠️ No gap patterns found for {character_name}, using fallback")
            gap_patterns = {
                'origin': {
                    'keywords': ['learned', 'discovered', 'started'],
                    'question_templates': [f"How did you get interested in {entity_name}?"]
                }
            }
        
        # Check which gaps exist
        for gap_type, pattern in gap_patterns.items():
            # Look for existing facts that would fill this gap
            gap_filled = False
            for fact in all_facts:
                fact_text = f"{fact.get('entity_name', '')} {fact.get('relationship_type', '')}"
                if any(keyword in fact_text.lower() for keyword in pattern['keywords']):
                    if entity_name.lower() in fact_text.lower():
                        gap_filled = True
                        break
            
            # If gap not filled, generate question
            if not gap_filled:
                # Choose appropriate template based on entity and relationship
                template = await self._select_best_question_template(
                    pattern['question_templates'], entity_name, relationship, character_name
                )
                
                if template:
                    gap_questions.append({
                        'question': template,
                        'gap_type': gap_type,
                        'entity': entity_name,
                        'confidence_score': confidence,
                        'relevance': self._calculate_question_relevance(gap_type, entity_name, character_name)
                    })
        
        return gap_questions

    async def _get_character_gap_patterns(self, character_name: str) -> dict:
        """Get character-specific gap patterns from database - personality-driven questioning"""
        try:
            if not self.enhanced_manager:
                return {}
            
            # Get character ID from normalized bot name
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Get database pool for direct query
            from src.database.postgres_pool_manager import get_postgres_pool
            pool = await get_postgres_pool()
            
            async with pool.acquire() as conn:
                # Query character_question_templates for this character
                templates = await conn.fetch("""
                    SELECT cqt.gap_type, cqt.template_text, cqt.keywords, cqt.priority_order
                    FROM character_question_templates cqt
                    JOIN characters c ON c.id = cqt.character_id
                    WHERE LOWER(c.name) LIKE $1
                    ORDER BY cqt.gap_type, cqt.priority_order
                """, f'%{bot_name}%')
                
                if not templates:
                    logger.debug(f"🔍 GAP PATTERNS: No database templates found for character '{character_name}'")
                    return {}
                
                # Build gap_patterns structure from database results
                gap_patterns = {}
                for template in templates:
                    gap_type = template['gap_type']
                    template_text = template['template_text']
                    keywords = template['keywords'] or []
                    
                    if gap_type not in gap_patterns:
                        gap_patterns[gap_type] = {
                            'keywords': keywords,
                            'question_templates': []
                        }
                    
                    # Add template to the list
                    gap_patterns[gap_type]['question_templates'].append(template_text)
                    
                    # Merge keywords (avoiding duplicates)
                    existing_keywords = set(gap_patterns[gap_type]['keywords'])
                    new_keywords = set(keywords)
                    gap_patterns[gap_type]['keywords'] = list(existing_keywords.union(new_keywords))
                
                logger.info(f"✅ GAP PATTERNS: Loaded {len(templates)} database templates across {len(gap_patterns)} gap types for {character_name}")
                return gap_patterns
                
        except Exception as e:
            logger.debug(f"Could not get character gap patterns from database: {e}")
            return {}

    async def _select_best_question_template(
        self, 
        templates: list, 
        entity_name: str, 
        relationship: str,
        character_name: str
    ) -> str:
        """Select the best question template based on entity type and character personality - DATABASE DRIVEN"""
        
        if not templates:
            return ""
        
        # Get database-driven entity classification for this character
        question_preference = await self._get_entity_question_preference(entity_name, character_name)
        
        if question_preference:
            # Use database-driven preference to select appropriate template
            return self._select_template_by_preference(templates, question_preference)
        
        # Fallback to first template if no database preference found
        return templates[0]

    async def _get_entity_question_preference(self, entity_name: str, character_name: str) -> str:
        """Get question preference for entity from database - character-specific and extensible"""
        try:
            if not self.enhanced_manager:
                return ""
            
            # Get character ID from normalized bot name
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Get database pool for direct query
            from src.database.postgres_pool_manager import get_postgres_pool
            pool = await get_postgres_pool()
            
            async with pool.acquire() as conn:
                # Query character_entity_categories for this character and entity
                entity_lower = entity_name.lower()
                
                # Find matching entity category with highest priority
                result = await conn.fetchrow("""
                    SELECT cec.question_preference, cec.priority_level, cec.category_type
                    FROM character_entity_categories cec
                    JOIN characters c ON c.id = cec.character_id
                    WHERE LOWER(c.name) LIKE $1
                    AND (
                        LOWER(cec.entity_keyword) = $2 
                        OR $2 LIKE ('%' || LOWER(cec.entity_keyword) || '%')
                        OR LOWER(cec.entity_keyword) LIKE ('%' || $2 || '%')
                    )
                    ORDER BY cec.priority_level DESC, cec.category_type
                    LIMIT 1
                """, f'%{bot_name}%', entity_lower)
                
                if result:
                    logger.info(f"🎯 ENTITY CLASSIFICATION: Found '{entity_name}' -> question_preference='{result['question_preference']}' for {character_name}")
                    return result['question_preference']
                
                logger.debug(f"🔍 ENTITY CLASSIFICATION: No database match for '{entity_name}' and character '{character_name}'")
                return ""
                
        except Exception as e:
            logger.debug(f"Could not get entity question preference from database: {e}")
            return ""

    def _select_template_by_preference(self, templates: list, preference: str) -> str:
        """Select template based on database-driven question preference"""
        if not templates:
            return ""
        
        # Map preferences to template selection logic
        preference_lower = preference.lower()
        
        if preference_lower == 'origin' or preference_lower == 'experience':
            # Prefer "How did you" templates for origin/experience questions
            for template in templates:
                if 'How did you' in template or 'What got you' in template:
                    return template
        
        elif preference_lower == 'specifics':
            # Prefer "What aspects" or "What's your favorite" for specifics
            for template in templates:
                if 'What aspects' in template or 'favorite' in template or 'type of' in template:
                    return template
        
        elif preference_lower == 'location':
            # Prefer "Where do you" templates for location questions
            for template in templates:
                if 'Where do you' in template or 'place for' in template:
                    return template
        
        elif preference_lower == 'community':
            # Prefer community/social templates
            for template in templates:
                if 'others' in template or 'people' in template or 'share' in template:
                    return template
        
        # Fallback to first template
        return templates[0]

    async def _filter_questions_by_character_personality(self, questions: list, character_name: str) -> list:
        """Filter questions to match character personality and expertise - DYNAMIC DATABASE VERSION"""
        if not questions:
            return []
        
        # Load character interest topics from database (character-agnostic)
        interest_topics = []
        if self.enhanced_manager:
            try:
                from src.memory.vector_memory_system import get_normalized_bot_name_from_env
                bot_name = get_normalized_bot_name_from_env()
                interest_topics = await self.enhanced_manager.get_interest_topics(bot_name)
                logger.info(f"🔍 Loaded {len(interest_topics)} interest topics for {bot_name} from database")
            except Exception as e:
                logger.warning(f"⚠️ Could not load interest topics from database: {e}")
        
        # Build topic keyword map for quick lookup
        topic_keywords = {}
        gap_type_preferences = {}
        for topic in interest_topics:
            topic_keywords[topic.topic_keyword.lower()] = topic.boost_weight
            if topic.gap_type_preference:
                gap_type_preferences[topic.gap_type_preference] = topic.boost_weight * 0.67  # Secondary boost (2/3 of primary)
        
        filtered_questions = []
        
        for question_data in questions:
            question = question_data['question']
            entity = question_data['entity']
            gap_type = question_data['gap_type']
            
            # Dynamic personality boost based on database topics
            personality_boost = 0.0
            
            # Check if entity matches any character interest topics
            entity_lower = entity.lower()
            for topic_keyword, boost_weight in topic_keywords.items():
                if topic_keyword in entity_lower:
                    personality_boost = max(personality_boost, boost_weight)
                    logger.debug(f"✅ Topic match: '{topic_keyword}' in '{entity}' - boost={boost_weight}")
                    break
            
            # Check if gap_type matches character preferences
            if gap_type in gap_type_preferences:
                personality_boost = max(personality_boost, gap_type_preferences[gap_type])
                logger.debug(f"✅ Gap type match: '{gap_type}' - boost={gap_type_preferences[gap_type]}")
            
            # General curiosity boost for all characters (origin questions are universally interesting)
            if gap_type == 'origin':
                personality_boost += 0.1
            
            # Update relevance score with personality matching
            question_data['relevance'] += personality_boost
            
            filtered_questions.append(question_data)
        
        return filtered_questions

    def _calculate_question_relevance(self, gap_type: str, entity_name: str, character_name: str) -> float:
        """Calculate relevance score for a question (0.0-1.0)"""
        base_relevance = {
            'origin': 0.8,      # How they got started - high value
            'experience': 0.7,   # How long they've been doing it
            'specifics': 0.6,    # What aspects they like
            'location': 0.5,     # Where they do it
            'community': 0.4     # Social aspects
        }
        
        return base_relevance.get(gap_type, 0.5)

    def _deduplicate_and_prioritize_questions(self, questions: list) -> list:
        """Remove similar questions and prioritize by relevance"""
        if not questions:
            return []
        
        # Sort by relevance score (highest first)
        sorted_questions = sorted(questions, key=lambda q: q['relevance'], reverse=True)
        
        # Remove duplicates based on entity and gap type
        seen_combinations = set()
        unique_questions = []
        
        for question_data in sorted_questions:
            combination = (question_data['entity'], question_data['gap_type'])
            
            if combination not in seen_combinations:
                seen_combinations.add(combination)
                unique_questions.append(question_data)
        
        return unique_questions

    async def load_character(self, character_file: Optional[str] = None) -> Character:
        """
        Load a character from database using bot name from environment.
        
        🚀 ENHANCED APPROACH: Use comprehensive enhanced CDL manager for full character data
        including personality traits, communication patterns, relationships, memories, etc.
        The character_file parameter is kept for compatibility but ignored.
        
        🚀 PERFORMANCE: Caching implemented for improved performance.
        """
        try:
            # Get bot name from environment
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            logger.info("🔍 CDL: Loading character for bot: %s", bot_name)
            
            # 🚀 ENHANCED: Use comprehensive enhanced CDL manager instead of minimal query
            from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
            from src.database.postgres_pool_manager import get_postgres_pool
            
            pool = await get_postgres_pool()
            if not pool:
                logger.error("❌ CDL: No database pool available")
                raise RuntimeError("Database pool not available")
                
            enhanced_manager = create_enhanced_cdl_manager(pool)
            
            # Load complete character data from all CDL tables
            character_data = await enhanced_manager.get_character_by_name(bot_name)
            
            if not character_data:
                logger.error("❌ CDL: Character '%s' not found in database", bot_name)
                # Return fallback character
                class FallbackCharacter:
                    def __init__(self):
                        self.identity = self._create_identity()
                        self.allow_full_roleplay_immersion = False
                            
                    def _create_identity(self):
                        class Identity:
                            def __init__(self):
                                self.name = "Unknown"
                                self.occupation = ""
                                self.description = ""
                        return Identity()
                
                return FallbackCharacter()
            
            # Extract core identity data
            identity_data = character_data.get('identity', {})
            character_name = identity_data.get('name', 'Unknown')
            character_occupation = identity_data.get('occupation', '')
            character_description = identity_data.get('description', '')
            allow_roleplay = character_data.get('allow_full_roleplay_immersion', False)
            
            logger.info("✅ CDL: Found character: %s (%s)", character_name, character_occupation)
            
            # 🚀 ENHANCED: Create rich character object with complete CDL data access
            class EnhancedCharacter:
                def __init__(self, character_data):
                    self.identity = self._create_identity(character_data.get('identity', {}))
                    self.allow_full_roleplay_immersion = character_data.get('allow_full_roleplay_immersion', False)
                    
                    # Store complete character data for access to personality, communication, etc.
                    self._character_data = character_data
                    self.personality = character_data.get('personality', {})
                    self.communication = character_data.get('communication', {})
                    self.relationships = character_data.get('relationships', {})
                    self.memories = character_data.get('key_memories', {})
                    self.behavioral_triggers = character_data.get('behavioral_triggers', {})
                    
                def _create_identity(self, identity_data):
                    class Identity:
                        def __init__(self, data):
                            self.name = data.get('name', 'Unknown')
                            self.occupation = data.get('occupation', '')
                            self.description = data.get('description', '')
                            self.archetype = data.get('archetype', '')
                    return Identity(identity_data)
                
                def get_full_character_data(self):
                    """Access to complete character data for advanced integrations"""
                    return self._character_data
            
            character = EnhancedCharacter(character_data)
            
            logger.info("✅ CDL: Created enhanced character object - name: '%s', occupation: '%s', data sections: %s", 
                       character.identity.name, character.identity.occupation, list(character_data.keys()))
            
            return character
            
        except Exception as e:
            logger.error("❌ CDL: Failed to load character: %s", e)
            # Return fallback character
            class FallbackCharacter:
                def __init__(self):
                    self.identity = self._create_identity()
                    
                def _create_identity(self):
                    class Identity:
                        def __init__(self):
                            self.name = "Unknown"
                            self.occupation = ""
                            self.description = ""
                    return Identity()
            
            return FallbackCharacter()

    async def _get_graph_manager(self):
        """Get or initialize CharacterGraphManager (cached)"""
        if not self._graph_manager_initialized:
            try:
                print("🎯 GRAPH INIT: Starting CharacterGraphManager initialization...", flush=True)
                logger.info("🎯 GRAPH INIT: Starting CharacterGraphManager initialization...")
                from src.characters.cdl.character_graph_manager import create_character_graph_manager
                
                # Use bot's existing PostgreSQL pool instead of creating a new one
                postgres_pool = None
                if self.bot_core and hasattr(self.bot_core, 'postgres_pool'):
                    postgres_pool = self.bot_core.postgres_pool
                    print("🎯 GRAPH INIT: Using bot's existing PostgreSQL pool", flush=True)
                    logger.info("🎯 GRAPH INIT: Using bot's existing PostgreSQL pool")
                
                # If bot pool not available, try centralized pool manager
                if not postgres_pool:
                    try:
                        from src.database.postgres_pool_manager import get_postgres_pool
                        postgres_pool = await get_postgres_pool()
                        if postgres_pool:
                            print("🎯 GRAPH INIT: Using centralized PostgreSQL pool", flush=True)
                            logger.info("🎯 GRAPH INIT: Using centralized PostgreSQL pool")
                        else:
                            print("🎯 GRAPH INIT: Centralized pool not available", flush=True)
                            logger.warning("🎯 GRAPH INIT: Centralized pool not available")
                    except Exception as e:
                        print(f"🎯 GRAPH INIT: Failed to get centralized pool: {e}", flush=True)
                        logger.warning("🎯 GRAPH INIT: Failed to get centralized pool: %s", str(e))
                
                # 🚀 FIXED: Use centralized database pool instead of CDL manager bypass
                if not postgres_pool:
                    print("🎯 GRAPH INIT: Using centralized database pool fallback...", flush=True)
                    logger.warning("🎯 GRAPH INIT: Using centralized database pool fallback...")
                    from src.database.postgres_pool_manager import get_postgres_pool
                    postgres_pool = await get_postgres_pool()
                
                if not postgres_pool:
                    logger.error("❌ GRAPH INIT: No PostgreSQL pool available")
                    return None
                
                print("🎯 GRAPH INIT: Creating CharacterGraphManager...", flush=True)
                logger.info("🎯 GRAPH INIT: Creating CharacterGraphManager...")
                
                # PRODUCTION INTEGRATION: Pass memory_manager for emotional context synchronization
                self._graph_manager = create_character_graph_manager(
                    postgres_pool, 
                    semantic_router=self.semantic_router,
                    memory_manager=self.memory_manager  # NEW: Enables emotional context synchronization
                )
                
                self._graph_manager_initialized = True
                print("✅ GRAPH INIT: CharacterGraphManager initialized successfully!", flush=True)
                logger.info("✅ GRAPH INIT: CharacterGraphManager initialized with memory_manager for emotional sync!")
            except Exception as e:
                print(f"❌ GRAPH INIT FAILED: {e}", flush=True)
                logger.error(f"❌ GRAPH INIT FAILED: Could not initialize CharacterGraphManager: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
                self._graph_manager = None
                self._graph_manager_initialized = True  # Mark as initialized to avoid retrying
        
        return self._graph_manager

    async def _is_character_background_question(self, message: str) -> bool:
        """
        Detect if message is asking about character background using semantic analysis.
        Replaces keyword matching with intelligent intent detection.
        """
        # Semantic patterns for background questions
        background_patterns = [
            'where do you live', 'where are you from', 'what do you do',
            'tell me about yourself', 'your background', 'your story',
            'who are you', 'about yourself', 'introduce yourself',
            'what\'s your job', 'where do you work', 'what do you work on',
            'your occupation', 'your profession', 'what you do for work'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in background_patterns)
    
    async def _is_relationship_question(self, message: str) -> bool:
        """Detect if message is asking about relationships."""
        relationship_patterns = [
            'relationship', 'relationships', 'friend', 'friends',
            'colleague', 'colleagues', 'partner', 'spouse', 'mentor',
            'connection', 'connected', 'dating', 'married', 'family'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in relationship_patterns)
    
    async def _is_career_question(self, message: str) -> bool:
        """Detect if message is asking about career/work."""
        career_patterns = [
            'work', 'job', 'career', 'education', 'study',
            'university', 'college', 'professional', 'occupation',
            'profession', 'what do you do', 'where do you work'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in career_patterns)
    
    async def _is_memory_question(self, message: str) -> bool:
        """Detect if message is asking about memories/experiences."""
        memory_patterns = [
            'remember', 'memory', 'memories', 'experience', 'experiences',
            'happened', 'past', 'story', 'stories', 'recall', 'event'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in memory_patterns)
    
    async def _is_hobby_question(self, message: str) -> bool:
        """Detect if message is asking about hobbies/interests."""
        hobby_patterns = [
            'hobby', 'hobbies', 'interest', 'interests', 'free time',
            'fun', 'enjoy', 'like to do', 'passion', 'pastime',
            'leisure', 'recreation', 'for fun', 'when not working'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in hobby_patterns)
    
    async def _is_education_question(self, message: str) -> bool:
        """Detect if message is asking about education/learning."""
        education_patterns = [
            'education', 'school', 'college', 'university', 'degree',
            'study', 'studied', 'learning', 'training', 'certification',
            'academic', 'graduated', 'major', 'minor', 'doctorate',
            'bachelor', 'master', 'phd', 'qualification'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in education_patterns)
    
    async def _is_skills_question(self, message: str) -> bool:
        """Detect if message is asking about skills/abilities."""
        skills_patterns = [
            'skill', 'skills', 'good at', 'expertise', 'expert',
            'ability', 'abilities', 'talented', 'proficient', 'capable',
            'competent', 'strengths', 'what can you do', 'specialized',
            'talent', 'gifted', 'mastery', 'proficiency'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in skills_patterns)
    
    async def _is_general_overview_question(self, message: str) -> bool:
        """Detect if message is asking for comprehensive/general information."""
        general_patterns = [
            'everything', 'anything', 'general', 'overview', 'summary',
            'all about', 'comprehensive', 'complete', 'full picture',
            'everything about', 'tell me more', 'know about you',
            'get to know', 'learn about', 'understand you better'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in general_patterns)

    def _calculate_trigger_relevance(self, trigger, context_factors: Dict[str, Any]) -> float:
        """
        Calculate relevance of an emotional trigger based on AI decision context.
        Uses semantic analysis instead of keyword matching.
        """
        relevance = 0.0
        
        # Base relevance from trigger type
        if hasattr(trigger, 'trigger_type'):
            trigger_type = trigger.trigger_type.lower()
            
            # Check if context factors suggest this trigger type
            for factor_name, factor_data in context_factors.items():
                if isinstance(factor_data, dict):
                    # Look for emotional alignment
                    primary_emotion = factor_data.get('primary_emotion', '').lower()
                    if trigger_type in primary_emotion or primary_emotion in trigger_type:
                        relevance += 0.7
                    
                    # Check for intensity alignment
                    emotional_intensity = factor_data.get('emotional_intensity', 0.0)
                    if emotional_intensity > 0.7 and 'intense' in trigger_type:
                        relevance += 0.3
                    elif emotional_intensity < 0.4 and 'gentle' in trigger_type:
                        relevance += 0.3
        
        return min(relevance, 1.0)
    
    def _calculate_domain_relevance(self, domain, context_factors: Dict[str, Any], message_content: str) -> float:
        """
        Calculate relevance of an expertise domain based on AI decision context.
        Uses semantic and contextual analysis instead of keyword matching.
        """
        relevance = 0.0
        domain_name_lower = domain.domain_name.lower()
        
        # Check conversation intelligence signals
        for factor_name, factor_data in context_factors.items():
            if isinstance(factor_data, dict):
                # Topic evolution signals
                topic_evolution = factor_data.get('topic_evolution', '')
                if isinstance(topic_evolution, str):
                    if 'technical' in topic_evolution and any(term in domain_name_lower for term in ['science', 'research', 'analysis', 'technology']):
                        relevance += 0.8
                    elif 'creative' in topic_evolution and any(term in domain_name_lower for term in ['art', 'design', 'creative', 'writing']):
                        relevance += 0.8
                
                # Learning emotion signals
                if factor_data.get('detected_learning_pattern'):
                    # Any domain is relevant when user is in learning mode
                    relevance += 0.6
                
                # Primary emotion alignment
                primary_emotion = factor_data.get('primary_emotion', '').lower()
                if primary_emotion in ['curiosity', 'interest'] and hasattr(domain, 'passion_level'):
                    # High passion domains more relevant for curious users
                    passion_boost = min(domain.passion_level / 10.0, 0.4)
                    relevance += passion_boost
        
        # Semantic content analysis (simple but effective)
        message_lower = message_content.lower()
        domain_keywords = domain_name_lower.split()
        
        # Look for domain-related terms in message
        for keyword in domain_keywords:
            if len(keyword) > 3 and keyword in message_lower:
                relevance += 0.3
        
        # Check for related terms (basic semantic expansion)
        domain_semantic_map = {
            'marine': ['ocean', 'sea', 'water', 'fish', 'coral', 'underwater'],
            'biology': ['life', 'organism', 'science', 'nature', 'ecosystem'],
            'computer': ['tech', 'software', 'programming', 'digital', 'code'],
            'art': ['creative', 'design', 'visual', 'aesthetic', 'beauty'],
            'music': ['sound', 'song', 'melody', 'rhythm', 'audio']
        }
        
        for domain_term, related_terms in domain_semantic_map.items():
            if domain_term in domain_name_lower:
                for related_term in related_terms:
                    if related_term in message_lower:
                        relevance += 0.2
                        break  # Only add bonus once per domain term
        
        return min(relevance, 1.0)

    async def _get_context_enhancer(self):
        """Get or initialize CharacterContextEnhancer (cached) - Phase 2B"""
        if not self._context_enhancer:
            try:
                logger.info("🎭 CONTEXT ENHANCER INIT: Starting CharacterContextEnhancer initialization...")
                
                # First get the graph manager (required for context enhancer)
                graph_manager = await self._get_graph_manager()
                
                if graph_manager:
                    from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
                    
                    # Initialize context enhancer with graph manager
                    self._context_enhancer = create_character_context_enhancer(
                        character_graph_manager=graph_manager
                    )
                    
                    logger.info("✅ CONTEXT ENHANCER INIT: CharacterContextEnhancer initialized successfully!")
                else:
                    logger.warning("❌ CONTEXT ENHANCER INIT: No graph manager available - proactive context disabled")
                    self._context_enhancer = None
                    
            except Exception as e:
                logger.error(f"❌ CONTEXT ENHANCER INIT FAILED: Could not initialize CharacterContextEnhancer: {e}")
                import traceback
                logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
                self._context_enhancer = None
        
        return self._context_enhancer

    async def _extract_cdl_personal_knowledge_sections(self, character, message_content: str, user_id: Optional[str] = None) -> str:
        """
        Extract relevant personal knowledge sections using CharacterGraphManager.
        
        STEP 1: Basic graph intelligence integration - replaces direct property access
        with importance-weighted, multi-dimensional graph queries.
        
        STEP 2: Cross-pollination with user facts - connects character knowledge
        with user interests and mentioned entities.
        
        Args:
            character: Character object
            message_content: User message content
            user_id: Optional user ID for cross-pollination with user facts
        """
        print(f"🔍 EXTRACTION START: Called for character={character.identity.name}, message='{message_content[:50]}...'", flush=True)
        logger.info(f"🔍 EXTRACTION START: Called for character={character.identity.name}, message='{message_content[:50]}...'")
        try:
            # 🎯 STEP 1: Get CharacterGraphManager (cached)
            print("🎯 Getting graph manager...", flush=True)
            graph_manager = await self._get_graph_manager()
            
            if not graph_manager:
                print("⚠️ GRAPH: Manager not available, using fallback", flush=True)
                logger.warning("📊 GRAPH: Manager not available, using fallback")
                return await self._extract_personal_knowledge_fallback(character, message_content)
            
            logger.info(f"📊 GRAPH: Starting personal knowledge extraction for message: '{message_content[:50]}...'")
            personal_sections = []
            message_lower = message_content.lower()
            
            # 🎯 SEMANTIC DETECTION: Use semantic router for intent detection instead of keywords
            is_background_question = await self._is_character_background_question(message_content)
            is_relationship_question = await self._is_relationship_question(message_content)
            is_career_question = await self._is_career_question(message_content)
            is_memory_question = await self._is_memory_question(message_content)
            
            # 🎯 GRAPH INTELLIGENCE: Use intent detection and graph queries
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            # 📖 BACKGROUND QUESTION: "Where do you live?", "What do you do?", "Tell me about yourself"
            if is_background_question:
                logger.info("📊 GRAPH: Background question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.BACKGROUND,
                    limit=5,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Background query returned - Background: {len(result.background)}, Relationships: {len(result.relationships)}, Memories: {len(result.memories)}")
                
                if not result.is_empty():
                    # Add high-importance background entries
                    for bg in result.background[:5]:
                        importance = bg.get('importance_level', 5)
                        stars = '⭐' * min(importance, 5)
                        background_entry = f"{stars} {bg['description']}"
                        personal_sections.append(background_entry)
                        logger.info(f"📊 GRAPH: Added background: {bg['description'][:80]}...")
                    
                    # Add abilities if relevant
                    for ability in result.abilities[:3]:
                        proficiency = ability.get('proficiency_level', 5)
                        if proficiency >= 6:
                            personal_sections.append(f"⚡ {ability['ability_name']} (proficiency: {proficiency}/10)")
            
            # 🤝 RELATIONSHIP QUESTION: "Tell me about your relationships", "Who are your friends?"
            if is_relationship_question:
                logger.info("📊 GRAPH: Relationship question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.RELATIONSHIPS,
                    limit=5,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Relationships query returned - Relationships: {len(result.relationships)}, Background: {len(result.background)}")
                
                if not result.is_empty():
                    # Format relationships with strength weighting
                    for rel in result.relationships[:5]:
                        strength = rel.get('relationship_strength', 5)
                        rel_type = rel.get('relationship_type', 'connection')
                        stars = '⭐' * min(strength, 5)
                        relationship_entry = f"{stars} {rel_type.title()}: {rel['related_entity']} - {rel.get('description', '')}"
                        personal_sections.append(relationship_entry)
                        logger.info(f"📊 GRAPH: Added relationship: {rel['related_entity']} ({rel_type})")
                    
                    # Add relationship-relevant background entries
                    for bg in result.background[:3]:
                        importance = bg.get('importance_level', 5)
                        personal_sections.append(f"Relationship Context ({importance}/10): {bg['description']}")
            
            # 💼 CAREER QUESTION: "What do you do for work?", "Tell me about your job"
            if is_career_question:
                logger.info("📊 GRAPH: Career question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.RELATIONSHIPS,
                    limit=5,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Relationships query returned - Relationships: {len(result.relationships)}, Background: {len(result.background)}")
                
                if not result.is_empty():
                    # Format relationships with strength weighting
                    for rel in result.relationships:
                        strength = rel.get('relationship_strength', 5)
                        rel_type = rel.get('relationship_type', 'connection')
                        stars = '⭐' * min(strength, 5)
                        relationship_entry = f"{stars} {rel_type.title()}: {rel['related_entity']} - {rel.get('description', '')}"
                        personal_sections.append(relationship_entry)
                        logger.info(f"📊 GRAPH: Added relationship: {rel['related_entity']} ({rel_type})")
                    
                    # Add relationship-relevant background entries
                    for bg in result.background:
                        if any(rel_keyword in bg['description'].lower() for rel_keyword in ['relationship', 'friend', 'colleague', 'partner', 'mentor']):
                            importance = bg.get('importance_level', 5)
                            personal_sections.append(f"Relationship Context ({importance}/10): {bg['description']}")
            
            # Extract career/work info if message mentions work/career
            if await self._is_career_question(message_content):
                logger.info("📊 GRAPH: Career question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.CAREER,
                    limit=3,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Career query returned - Background: {len(result.background)}, Abilities: {len(result.abilities)}, Memories: {len(result.memories)}")
                
                if not result.is_empty():
                    # Format career background with importance
                    for bg in result.background:
                        importance = bg.get('importance_level', 5)
                        career_entry = f"Career ({importance}/10 importance): {bg['description']}"
                        personal_sections.append(career_entry)
                        logger.info(f"📊 GRAPH: Added career background: {career_entry[:80]}...")
                    
                    # Format professional abilities with proficiency
                    for ability in result.abilities:
                        proficiency = ability.get('proficiency_level', 5)
                        ability_entry = f"Professional Skill: {ability['ability_name']} (proficiency: {proficiency}/10)"
                        personal_sections.append(ability_entry)
                        logger.info(f"📊 GRAPH: Added ability: {ability_entry}")
                else:
                    logger.warning("📊 GRAPH: Career query returned empty results!")
            
            # Extract hobbies/interests if message mentions interests/leisure
            if await self._is_hobby_question(message_content):
                logger.info("📊 GRAPH: Hobby question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.HOBBIES,
                    limit=3,
                    user_id=user_id
                )
                
                if not result.is_empty():
                    for bg in result.background:
                        personal_sections.append(f"Interest: {bg['description']}")
                    
                    for ability in result.abilities:
                        if ability.get('category') in ['hobby', 'personal', 'recreation']:
                            personal_sections.append(f"Hobby Skill: {ability['ability_name']}")
            
            # 🎓 PHASE 2A ENHANCEMENT: Extract education info if message mentions school/learning
            if await self._is_education_question(message_content):
                logger.info("📊 GRAPH: Education question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.EDUCATION,
                    limit=3,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Education query returned - Background: {len(result.background)}, Abilities: {len(result.abilities)}")
                
                if not result.is_empty():
                    for bg in result.background:
                        importance = bg.get('importance_level', 5)
                        education_entry = f"Education ({importance}/10 importance): {bg['description']}"
                        personal_sections.append(education_entry)
                        logger.info(f"📊 GRAPH: Added education background: {education_entry[:80]}...")
            
            # 💪 PHASE 2A ENHANCEMENT: Extract skills/abilities if message mentions expertise/talent
            if await self._is_skills_question(message_content):
                logger.info("📊 GRAPH: Skills question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.SKILLS,
                    limit=5,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Skills query returned - Abilities: {len(result.abilities)}, Background: {len(result.background)}")
                
                if not result.is_empty():
                    for ability in result.abilities:
                        proficiency = ability.get('proficiency_level', 5)
                        skill_entry = f"Skill: {ability['ability_name']} (proficiency: {proficiency}/10)"
                        personal_sections.append(skill_entry)
                        logger.info(f"📊 GRAPH: Added skill: {skill_entry}")
                    
                    for bg in result.background:
                        if 'skill' in bg['description'].lower() or 'ability' in bg['description'].lower():
                            personal_sections.append(f"Skill Background: {bg['description']}")
            
            # 🧠 PHASE 2A ENHANCEMENT: Extract memories if message asks about experiences/past
            if await self._is_memory_question(message_content):
                logger.info("📊 GRAPH: Memory question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.MEMORIES,
                    limit=3,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Memory query returned - Memories: {len(result.memories)}, Background: {len(result.background)}")
                
                if not result.is_empty():
                    for memory in result.memories:
                        importance = memory.get('importance_level', 5)
                        emotional_impact = memory.get('emotional_impact', 5)
                        memory_title = memory.get('title', 'Memory')
                        memory_desc = memory.get('description', '')
                        memory_entry = f"Memory ({importance}/10 importance, {emotional_impact}/10 emotional): {memory_title} - {memory_desc}"
                        personal_sections.append(memory_entry)
                        logger.info(f"📊 GRAPH: Added memory: {memory_title[:50]}...")
            
            # 📖 PHASE 2A ENHANCEMENT: Extract general background if message asks about character generally
            if await self._is_character_background_question(message_content):
                logger.info("📊 GRAPH: Background question detected (semantic), querying character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.BACKGROUND,
                    limit=5,
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: Background query returned - Background: {len(result.background)}, Memories: {len(result.memories)}, Relationships: {len(result.relationships)}")
                
                if not result.is_empty():
                    # Add high-importance background entries
                    for bg in result.background[:5]:
                        importance = bg.get('importance_level', 5)
                        stars = '⭐' * min(importance, 5)
                        background_entry = f"{stars} {bg['description']}"
                        personal_sections.append(background_entry)
                        logger.info(f"📊 GRAPH: Added background: {bg['description'][:80]}...")
            
            # 🌐 PHASE 2A ENHANCEMENT: Extract comprehensive character information for general inquiries
            if await self._is_general_overview_question(message_content):
                logger.info("📊 GRAPH: General overview question detected (semantic), querying comprehensive character knowledge...")
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.GENERAL,
                    limit=10,  # More comprehensive results
                    user_id=user_id
                )
                
                logger.info(f"📊 GRAPH: General query returned - Background: {len(result.background)}, Abilities: {len(result.abilities)}, Relationships: {len(result.relationships)}, Memories: {len(result.memories)}")
                
                if not result.is_empty():
                    # Add comprehensive background (top importance)
                    background_added = 0
                    for bg in sorted(result.background, key=lambda x: x.get('importance_level', 0), reverse=True)[:6]:
                        importance = bg.get('importance_level', 5)
                        if importance >= 7:  # Only high-importance for general overview
                            stars = '⭐' * min(importance, 5)
                            personal_sections.append(f"{stars} Overview: {bg['description']}")
                            background_added += 1
                    
                    # Add key abilities/skills
                    abilities_added = 0
                    for ability in sorted(result.abilities, key=lambda x: x.get('proficiency_level', 0), reverse=True)[:4]:
                        proficiency = ability.get('proficiency_level', 5)
                        if proficiency >= 7:  # Only high-proficiency skills
                            skill_entry = f"⚡ Key Skill: {ability['ability_name']} (expert level: {proficiency}/10)"
                            personal_sections.append(skill_entry)
                            abilities_added += 1
                    
                    # Add important relationships (top 3)
                    relationships_added = 0
                    for rel in sorted(result.relationships, key=lambda x: x.get('relationship_strength', 0), reverse=True)[:3]:
                        strength = rel.get('relationship_strength', 5)
                        if strength >= 6:  # Only meaningful relationships
                            rel_type = rel.get('relationship_type', 'connection')
                            personal_sections.append(f"🤝 {rel_type.title()}: {rel['related_entity']} (significant)")
                            relationships_added += 1
                    
                    # Add formative memories (top 2)
                    memories_added = 0
                    for memory in sorted(result.memories, key=lambda x: x.get('importance_level', 0), reverse=True)[:2]:
                        importance = memory.get('importance_level', 5)
                        if importance >= 8:  # Only very important memories
                            memory_title = memory.get('title', 'Significant Experience')
                            personal_sections.append(f"🧠 Formative: {memory_title}")
                            memories_added += 1
                    
                    logger.info(f"📊 GRAPH: General overview added - Background: {background_added}, Abilities: {abilities_added}, Relationships: {relationships_added}, Memories: {memories_added}")
            
            # � STEP 2: CROSS-POLLINATION - Connect character knowledge with user facts
            has_postgres = hasattr(graph_manager, 'postgres') if graph_manager else False
            postgres_value = graph_manager.postgres if graph_manager and hasattr(graph_manager, 'postgres') else None
            print(f"🔍 DEBUG: Checking cross-pollination conditions - user_id={user_id}, graph_manager={graph_manager is not None}, has_postgres={has_postgres}, postgres_value={postgres_value}", flush=True)
            logger.info(f"🔍 DEBUG: Checking cross-pollination conditions - user_id={user_id}, graph_manager={graph_manager is not None}, has_postgres={has_postgres}")
            
            if user_id and graph_manager and hasattr(graph_manager, 'postgres') and graph_manager.postgres:
                try:
                    logger.info(f"🔗 CROSS-POLLINATION: Querying character-user connections for user_id={user_id}")
                    print(f"🔗 CROSS-POLLINATION: Querying character-user connections for user_id={user_id}", flush=True)
                    
                    # Get character ID from database
                    character_id_result = await graph_manager.postgres.fetchval(
                        "SELECT id FROM characters WHERE name = $1",
                        character.identity.name
                    )
                    
                    if character_id_result:
                        cross_poll_results = await graph_manager.query_cross_pollination(
                            character_id=character_id_result,
                            user_id=user_id,
                            limit=3
                        )
                        
                        # Add shared interests
                        for interest in cross_poll_results.get('shared_interests', []):
                            personal_sections.append(
                                f"🔗 Shared Interest: {interest.get('description', '')} "
                                f"(connects with your interest in {interest.get('user_entity', '')})"
                            )
                            logger.info(f"🔗 CROSS-POLL: Added shared interest: {interest.get('description', '')[:50]}...")
                        
                        # Add relevant abilities
                        for ability in cross_poll_results.get('relevant_abilities', []):
                            personal_sections.append(
                                f"🔗 Relevant Skill: {ability.get('ability_name', '')} "
                                f"(relates to your {ability.get('user_entity', '')})"
                            )
                            logger.info(f"🔗 CROSS-POLL: Added relevant ability: {ability.get('ability_name', '')}")
                        
                        # Add character knowledge about user facts
                        for knowledge in cross_poll_results.get('character_knowledge_about_user_facts', []):
                            personal_sections.append(
                                f"🔗 Related Knowledge: {knowledge.get('description', '')} "
                                f"(relevant to your {knowledge.get('user_entity', '')})"
                            )
                            logger.info(f"🔗 CROSS-POLL: Added related knowledge: {knowledge.get('description', '')[:50]}...")
                        
                        if any(cross_poll_results.values()):
                            logger.info(f"🔗 CROSS-POLLINATION: Successfully added {sum(len(v) for v in cross_poll_results.values())} cross-pollinated sections")
                        else:
                            logger.info("🔗 CROSS-POLLINATION: No connections found between character and user facts")
                    else:
                        logger.warning(f"🔗 CROSS-POLLINATION: Could not find character ID for {character.identity.name}")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "another operation is in progress" in error_msg:
                        logger.warning(f"🔗 CROSS-POLLINATION: PostgreSQL pool busy, skipping cross-pollination for this request")
                        print(f"🔗 CROSS-POLLINATION: PostgreSQL pool busy, skipping cross-pollination for this request", flush=True)
                    else:
                        logger.warning(f"🔗 CROSS-POLLINATION: Error querying connections: {e}")
                        print(f"🔗 CROSS-POLLINATION: Error querying connections: {e}", flush=True)
            else:
                logger.info(f"🔗 CROSS-POLLINATION: Conditions not met - user_id={user_id is not None}, graph_manager={graph_manager is not None}, has_postgres={has_postgres}")
                print(f"🔗 CROSS-POLLINATION: Conditions not met - user_id={user_id is not None}, graph_manager={graph_manager is not None}, has_postgres={has_postgres}", flush=True)
            
            # �📊 FALLBACK: If no graph results, use direct property access (legacy compatibility)
            if not personal_sections:
                logger.debug("📊 GRAPH: No graph results found, triggering fallback method")
                return await self._extract_personal_knowledge_fallback(character, message_content)
            
            result_text = "\n".join(personal_sections) if personal_sections else ""
            if result_text:
                logger.info(f"📊 GRAPH: Successfully extracted {len(personal_sections)} personal knowledge sections using graph intelligence")
            
            return result_text
            
        except Exception as e:
            logger.warning("Could not extract personal knowledge via graph manager: %s", e)
            # Final fallback
            return await self._extract_personal_knowledge_fallback(character, message_content)

    async def _extract_personal_knowledge_fallback(self, character, message_content: str) -> str:
        """Fallback: Direct property access for personal knowledge extraction"""
        try:
            personal_sections = []
            message_lower = message_content.lower()
            
            # Original direct property access code
            if any(keyword in message_lower for keyword in ['family', 'parents']):
                if hasattr(character, 'backstory') and character.backstory:
                    if hasattr(character.backstory, 'family_background') and character.backstory.family_background:
                        personal_sections.append(f"Family: {character.backstory.family_background}")
            
            if any(keyword in message_lower for keyword in ['work', 'career']):
                if hasattr(character, 'skills_and_expertise') and character.skills_and_expertise:
                    if hasattr(character.skills_and_expertise, 'education') and character.skills_and_expertise.education:
                        personal_sections.append(f"Education: {character.skills_and_expertise.education}")
            
            return "\n".join(personal_sections) if personal_sections else ""
        except Exception as e:
            logger.debug("Fallback extraction failed: %s", e)
            return ""

    def _detect_communication_scenarios(self, message_content: str, character, display_name: str) -> list:
        """Detect communication scenarios using CDL message_pattern_triggers."""
        scenarios = []
        message_lower = message_content.lower()
        
        # Get message pattern triggers from CDL character data
        try:
            # Access character.communication.message_pattern_triggers directly
            message_triggers = getattr(character.communication, 'message_pattern_triggers', {})
            
            # Check each pattern trigger
            for scenario_name, trigger_data in message_triggers.items():
                keywords = trigger_data.get('keywords', [])
                phrases = trigger_data.get('phrases', [])
                
                # Check keywords
                keyword_matches = sum(1 for keyword in keywords if keyword.lower() in message_lower)
                
                # Check phrases
                phrase_matches = sum(1 for phrase in phrases if phrase.lower() in message_lower)
                
                # If we have matches, add this scenario
                if keyword_matches > 0 or phrase_matches > 0:
                    scenarios.append(scenario_name)
                    logger.debug("🎯 CDL Pattern Match: '%s' triggered by message: %s", scenario_name, message_content[:50])
                    
        except Exception as e:
            logger.debug("Error checking message pattern triggers: %s", e)
        
        # Fallback to basic pattern detection if no CDL triggers matched
        if not scenarios:
            # Generic fallback patterns (character-agnostic)
            if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
                scenarios.append('basic_greeting')
            
            # Check for question scenarios
            if '?' in message_content:
                scenarios.append('basic_question')
                
            # Check for emotional scenarios
            if any(emotion in message_lower for emotion in ['sad', 'happy', 'angry', 'worried', 'excited', 'frustrated']):
                scenarios.append('emotional_context')
                
            # Check for personal scenarios
            if any(personal in message_lower for personal in ['tell me about', 'what do you', 'how do you', 'your']):
                scenarios.append('personal_context')
                
        return scenarios

    def _get_cdl_conversation_flow_guidance(self, character_name: str, scenarios: list) -> str:
        """Get conversation flow guidance based on detected scenarios - fully character-agnostic."""
        if not scenarios:
            return ""
            
        guidance_parts = []
        
        # Generate dynamic guidance based on scenario names (character-agnostic)
        for scenario in scenarios:
            # Convert scenario names to natural guidance
            scenario_clean = scenario.replace('_', ' ').title()
            
            if 'greeting' in scenario.lower():
                guidance_parts.append(f"Greet warmly as {character_name}.")
            elif 'question' in scenario.lower():
                guidance_parts.append(f"Answer from {character_name}'s perspective.")
            elif 'emotional' in scenario.lower() or 'support' in scenario.lower():
                guidance_parts.append(f"Show empathy as {character_name}.")
            elif 'personal' in scenario.lower():
                guidance_parts.append(f"Share personal insights as {character_name}.")
            elif 'technical' in scenario.lower() or 'professional' in scenario.lower():
                guidance_parts.append(f"Apply professional expertise as {character_name}.")
            elif 'collaboration' in scenario.lower() or 'working' in scenario.lower():
                guidance_parts.append(f"Engage collaboratively as {character_name}.")
            elif 'education' in scenario.lower() or 'teaching' in scenario.lower() or 'learning' in scenario.lower():
                guidance_parts.append(f"Share knowledge as {character_name} would when teaching.")
            else:
                # Generic guidance for any scenario
                guidance_parts.append(f"Respond as {character_name} in {scenario_clean} context.")
                
        return " ".join(guidance_parts)

    def _extract_cdl_response_style(self, character, display_name: str) -> str:
        """Extract response style guidance from CDL character definition."""
        try:
            from src.characters.cdl.manager import get_response_style
            response_style = get_response_style()
            
            if not response_style:
                return ""
            
            style_parts = []
            style_parts.append("🎤 RESPONSE REQUIREMENTS:")
            style_parts.append(f"- Address the user as {display_name} naturally in conversation")
            style_parts.append(f"- Match the communication style of a {character.identity.occupation}")
            
            # Add formatting rules from CDL
            formatting_rules = response_style.get('formatting_rules', [])
            if formatting_rules:
                for rule in formatting_rules:
                    style_parts.append(f"- {rule}")
            
            # Add core principles from CDL  
            core_principles = response_style.get('core_principles', [])
            if core_principles:
                style_parts.append("🚨 CONVERSATIONAL RESPONSE STYLE:")
                for principle in core_principles:
                    style_parts.append(f"- {principle}")
            
            # Add character-specific adaptations from CDL (generic field name)
            char_adaptations = response_style.get('character_specific_adaptations', [])
            if char_adaptations:
                style_parts.append(f"🎯 {character.identity.name.upper()}-SPECIFIC GUIDANCE:")
                for adaptation in char_adaptations:
                    style_parts.append(f"- {adaptation}")
            
            return "\n".join(style_parts) if style_parts else ""
            
        except Exception as e:
            logger.debug("Could not extract CDL response style: %s", e)
            return ""

    def _extract_conversation_flow_guidelines(self, character, active_mode=None) -> str:
        """
        Extract conversation flow guidelines - ONLY for ACTIVE mode (trigger-aware).
        
        🎯 OPTIMIZATION: Only inject guidance for the currently active conversation mode,
        not ALL modes. Uses normalized database tables, NOT JSON fields.
        This reduces prompt size by ~2000 chars (85% reduction).
        
        🚨 CRITICAL: This function should ONLY use the active_mode parameter (InteractionMode object)
        which contains data from normalized tables (character_conversation_modes, character_mode_guidance).
        Do NOT load from conversation_flow_guidance JSON field - that's deprecated legacy data.
        """
        try:
            guidance_parts = []
            
            # 🎯 TRIGGER-AWARE: Only inject ACTIVE mode guidance from normalized database
            if active_mode:
                # active_mode is an InteractionMode object from get_interaction_modes() 
                # which queries normalized tables: character_conversation_modes + character_mode_guidance
                
                # Format mode name for display
                mode_name = active_mode.mode_name
                display_name = mode_name.replace('_', ' ').title()
                
                # Build active mode description from normalized data
                mode_desc_parts = [f"🎭 ACTIVE MODE: {display_name}"]
                
                # Add mode description (from character_conversation_modes.approach)
                if active_mode.mode_description:
                    mode_desc_parts.append(f"({active_mode.mode_description})")
                
                # Add response guidelines (from character_conversation_modes.energy_level)
                if active_mode.response_guidelines:
                    mode_desc_parts.append(f"- Energy: {active_mode.response_guidelines}")
                
                guidance_parts.append(" ".join(mode_desc_parts))
                
                # Add encourage patterns (from character_mode_guidance WHERE guidance_type='encourage')
                # Limit to top 3 for prompt efficiency
                if active_mode.response_guidelines and isinstance(active_mode.response_guidelines, str):
                    # response_guidelines from energy_level field
                    guidance_parts.append(f"✅ Approach: {active_mode.response_guidelines}")
                
                # Add avoid patterns (from character_mode_guidance WHERE guidance_type='avoid')
                # Limit to top 3 for prompt efficiency
                if active_mode.avoid_patterns and len(active_mode.avoid_patterns) > 0:
                    guidance_parts.append("❌ Avoid:")
                    for pattern in active_mode.avoid_patterns[:3]:  # Top 3 only
                        guidance_parts.append(f"  • {pattern}")
                
                logger.info(f"✅ CONVERSATION FLOW: Using active mode '{mode_name}' from normalized database (NOT JSON)")
            
            else:
                # No active mode detected - use minimal generic guidance
                logger.info(f"ℹ️ CONVERSATION FLOW: No active mode detected, using minimal generic guidance")
                guidance_parts.append("🎭 CONVERSATION MODE: General conversational engagement")
            
            # Only add header if we have guidance
            if guidance_parts:
                guidance_parts.insert(0, "🎯 CONVERSATION FLOW REQUIREMENTS:")
                return "\n".join(guidance_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting conversation flow guidelines: {e}", exc_info=True)
            return ""

    def _detect_physical_interaction_request(self, message: str) -> bool:
        """Detect requests for physical meetings or interactions."""
        message_lower = message.lower()
        
        meetup_triggers = [
            "meet up", "meet you", "meetup", "get together", "hang out",
            "grab coffee", "get coffee", "coffee together", "have coffee",
            "grab lunch", "grab dinner", "at the pier", "at the beach",
            "meet for dinner", "meet for lunch", "meet for coffee", "meet for",
            "can we meet", "want to meet", "should we meet", "let's meet"
        ]
        
        interaction_triggers = [
            "hug you", "kiss you", "hold you", "touch you",
            "hold hands", "cuddle", "embrace", "physical"
        ]
        
        activity_triggers = [
            "let's go", "want to go", "wanna go", "should we go",
            "come with me", "join me", "accompany me"
        ]
        
        all_triggers = meetup_triggers + interaction_triggers + activity_triggers
        detected = any(trigger in message_lower for trigger in all_triggers)
        
        # Enhanced debug logging
        if detected:
            matching_triggers = [trigger for trigger in all_triggers if trigger in message_lower]
            logger.info("🛡️ PHYSICAL INTERACTION DETECTED in '%s': triggers=%s", message_lower, matching_triggers)
        else:
            logger.info("🛡️ No physical interaction detected in: '%s'", message_lower)
            # Debug: check specific patterns that should have matched
            should_match = ["can we meet", "meet for dinner", "meet for"]
            matching_should = [trigger for trigger in should_match if trigger in message_lower]
            if matching_should:
                logger.warning("🛡️ DEBUG: Should have matched but didn't: %s", matching_should)
        
        return detected

    def _check_roleplay_flexibility(self, character) -> bool:
        """Check if character allows full roleplay immersion directly from character object."""
        try:
            # Check character object's allow_full_roleplay_immersion attribute directly
            return getattr(character, 'allow_full_roleplay_immersion', False)
        except Exception as e:
            logger.debug("Error checking roleplay flexibility: %s", e)
            return False

    def _get_cdl_roleplay_guidance(self, character, display_name: str) -> str:
        """Extract roleplay boundary guidance directly from character object."""
        try:
            # Access AI identity handling from character communication
            roleplay_scenarios = {}
            if hasattr(character, 'communication'):
                comm = character.communication
                if hasattr(comm, 'ai_identity_handling'):
                    ai_handling = comm.ai_identity_handling
                    roleplay_scenarios = ai_handling.get('roleplay_interaction_scenarios', {})
            
            if not roleplay_scenarios:
                return self._generate_generic_roleplay_guidance(character, display_name)
            
            guidance_parts = [
                "🚨 PHYSICAL INTERACTION REQUEST DETECTED:",
                "",
                "RESPONSE APPROACH:",
                "1. Match character enthusiasm naturally",
                "2. Acknowledge AI limitations honestly",
                "3. Suggest engaging alternatives"
            ]
            
            return "\n".join(guidance_parts)
            
        except Exception as e:
            logger.debug("Error extracting CDL roleplay guidance: %s", e)
            return self._generate_generic_roleplay_guidance(character, display_name)

    def _generate_generic_roleplay_guidance(self, character, display_name: str) -> str:
        """Generate comprehensive roleplay guidance when CDL data unavailable."""
        return f"""🚨 PHYSICAL INTERACTION REQUEST DETECTED:

RESPONSE APPROACH:
1. Match {character.identity.name}'s enthusiasm naturally
2. Acknowledge AI limitations honestly when appropriate
3. Suggest engaging alternatives

Stay authentic to {character.identity.name}'s personality while being transparent about physical limitations."""

    async def _build_voice_communication_section(self, character) -> str:
        """
        Build consolidated VOICE & COMMUNICATION STYLE section matching complete_prompt_examples format.
        
        Queries extended data tables:
        - character_voice_traits: tone, pace, accent
        - character_cultural_expressions: favorite phrases, cultural expressions  
        - character_message_triggers: speech patterns keywords
        
        Returns formatted section matching Elena example structure.
        """
        try:
            bot_name = self._get_safe_bot_name(character)
            
            voice_parts = []
            voice_parts.append("VOICE & COMMUNICATION STYLE:")
            
            # Query voice traits and build groups dynamically from database
            voice_trait_groups = {}  # Build dynamically based on actual database content
            
            if self.enhanced_manager:
                try:
                    voice_traits = await self.enhanced_manager.get_voice_traits(bot_name)
                    
                    # Build groups dynamically - no hardcoded trait types!
                    for trait in voice_traits:
                        trait_type = trait.trait_type.lower()
                        trait_value = trait.trait_value
                        
                        # Create group if it doesn't exist
                        if trait_type not in voice_trait_groups:
                            voice_trait_groups[trait_type] = []
                        
                        # Add value to the appropriate group
                        voice_trait_groups[trait_type].append(trait_value)
                    
                    logger.info(f"✅ VOICE SECTION: Retrieved {len(voice_traits)} voice traits across {len(voice_trait_groups)} trait types: {list(voice_trait_groups.keys())}")
                    
                except Exception as e:
                    logger.debug(f"Could not query voice traits: {e}")
            
            # Add voice traits dynamically - handle ANY trait types from database
            
            # Priority order for common trait types (optional - for consistent ordering)
            priority_traits = ['tone', 'pace', 'accent', 'preferred_word', 'avoided_word', 
                             'sentence_structure', 'philosophical_terms', 'poetic_language',
                             'punctuation_style', 'response_length']
            
            # Add priority traits first (if they exist)
            for trait_type in priority_traits:
                if trait_type in voice_trait_groups and voice_trait_groups[trait_type]:
                    values = voice_trait_groups[trait_type]
                    
                    # Format based on trait type semantics
                    if trait_type == 'preferred_word':
                        if len(values) > 0:
                            vocab_text = ", ".join(values[:8])  # Show all preferred words
                            voice_parts.append(f"- Preferred words: {vocab_text}")
                    elif trait_type == 'avoided_word':
                        if len(values) > 0:
                            avoid_text = ", ".join(values[:4])  # Show avoided words
                            voice_parts.append(f"- Words to avoid: {avoid_text}")
                    elif trait_type in ['sentence_structure', 'philosophical_terms', 'poetic_language']:
                        patterns_text = ", ".join(values[:3])  # Combine into speech patterns
                        voice_parts.append(f"- Speech patterns: {patterns_text}")
                    elif trait_type == 'response_length':
                        voice_parts.append(f"- Response style: {values[0]}")  # Take first entry
                    elif trait_type == 'punctuation_style':
                        voice_parts.append(f"- Punctuation: {values[0]}")  # Take first entry
                    else:
                        # Standard formatting for tone, pace, accent, etc.
                        trait_label = trait_type.replace('_', ' ').title()
                        trait_text = ", ".join(values)
                        voice_parts.append(f"- {trait_label}: {trait_text}")
            
            # Add any remaining trait types not in priority list
            for trait_type, values in voice_trait_groups.items():
                if trait_type not in priority_traits and values:
                    trait_label = trait_type.replace('_', ' ').title()
                    trait_text = ", ".join(values[:3])  # Limit to 3 for unknown types
                    voice_parts.append(f"- {trait_label}: {trait_text}")
            
            # Query cultural expressions for favorite phrases
            favorite_phrases = []
            
            if self.enhanced_manager:
                try:
                    cultural_expressions = await self.enhanced_manager.get_cultural_expressions(bot_name)
                    
                    for expr in cultural_expressions:
                        expr_type = expr.expression_type.lower()
                        
                        if 'favorite' in expr_type or 'signature' in expr_type:
                            favorite_phrases.append(expr.expression_value)
                    
                    logger.info(f"✅ VOICE SECTION: Retrieved {len(favorite_phrases)} favorite phrases")
                    
                except Exception as e:
                    logger.debug(f"Could not query cultural expressions: {e}")
            
            # Add Favorite phrases
            if favorite_phrases:
                phrases_text = ", ".join(favorite_phrases[:5])  # Top 5
                voice_parts.append(f"- Favorite phrases: {phrases_text}")
            
            # Return formatted section if we have content
            if len(voice_parts) > 1:  # More than just the header
                return "\n".join(voice_parts)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Failed to build voice communication section: {e}")
            return ""

    async def _build_user_context_section(self, user_id: str, display_name: str) -> str:
        """
        Build user context section combining personality profile and personal facts.
        
        Integrates:
        - DynamicPersonalityProfiler data (Big Five traits, communication style)
        - PostgreSQL stored facts and preferences
        - User conversation patterns and preferences
        
        Returns formatted context for character response adaptation.
        """
        try:
            context_parts = []
            
            # 1. Get user personality profile from DynamicPersonalityProfiler
            personality_context = await self._get_user_personality_context(user_id)
            if personality_context:
                context_parts.append(personality_context)
            
            # 2. Get user facts and preferences from PostgreSQL
            facts_context = await self._get_user_facts_context(user_id, display_name)
            if facts_context:
                context_parts.append(facts_context)
            
            if context_parts:
                return f"👤 USER CONTEXT:\n" + "\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            logger.debug("Failed to build user context section: %s", e)
            return ""
    
    async def _get_user_personality_context(self, user_id: str) -> str:
        """Get user personality context from DynamicPersonalityProfiler."""
        try:
            # Try to access personality profiler from bot_core if available
            if (self.bot_core and 
                hasattr(self.bot_core, 'dynamic_personality_profiler')):
                profiler = self.bot_core.dynamic_personality_profiler
                
                if profiler and hasattr(profiler, 'profiles') and user_id in profiler.profiles:
                    profile = profiler.profiles[user_id]
                    
                    personality_parts = []
                    
                    # Add communication style
                    if hasattr(profile, 'traits'):
                        personality_parts.append(f"Communication Style: Adaptive to user preferences")
                    
                    # Add relationship depth
                    if hasattr(profile, 'relationship_depth'):
                        depth = profile.relationship_depth
                        if depth > 0.8:
                            personality_parts.append("Relationship Level: Close connection")
                        elif depth > 0.5:
                            personality_parts.append("Relationship Level: Growing relationship")
                        else:
                            personality_parts.append("Relationship Level: New connection")
                    
                    # Add trust level
                    if hasattr(profile, 'trust_level'):
                        trust = profile.trust_level
                        if trust > 0.7:
                            personality_parts.append("Trust Level: High trust established")
                        elif trust > 0.4:
                            personality_parts.append("Trust Level: Building trust")
                        else:
                            personality_parts.append("Trust Level: Establishing rapport")
                    
                    if personality_parts:
                        return "🧠 User Personality: " + ", ".join(personality_parts)
            
            return ""
            
        except Exception as e:
            logger.debug("Failed to get user personality context: %s", e)
            return ""
    
    async def _get_user_facts_context(self, user_id: str, display_name: str) -> str:
        """Get user facts and preferences from PostgreSQL."""
        try:
            if not self.knowledge_router:
                return ""
            
            # Get character name from environment (character-agnostic)
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            character_name = get_normalized_bot_name_from_env()
            
            # Get structured facts from PostgreSQL
            facts = await self.knowledge_router.get_character_aware_facts(
                user_id=user_id,
                character_name=character_name,
                limit=10
            )
            
            # Get user preferences from PostgreSQL
            preferences = await self.knowledge_router.get_all_user_preferences(
                user_id=user_id
            )
            
            fact_parts = []
            
            # Format preferences (like preferred name)
            if preferences:
                for pref_key, pref_data in preferences.items():
                    if isinstance(pref_data, dict):
                        pref_value = pref_data.get('value', '')
                        confidence = pref_data.get('confidence', 0.0)
                        
                        if confidence >= 0.7 and pref_value:
                            if pref_key == "preferred_name":
                                fact_parts.append(f"Prefers to be called: {pref_value}")
                            else:
                                fact_parts.append(f"{pref_key.replace('_', ' ').title()}: {pref_value}")
            
            # Format key facts (likes, interests, etc.) with STEP 6: Confidence-Aware Conversations
            if facts:
                # Use confidence-aware formatting for all facts
                confidence_aware_facts = []
                for fact in facts[:5]:  # Limit to top 5 facts
                    # Try to parse fact structure - handle both dict and string formats
                    if isinstance(fact, dict):
                        entity_name = fact.get('entity_name', '')
                        entity_type = fact.get('entity_type', '')
                        relationship = fact.get('relationship_type', 'related to')
                        confidence = fact.get('confidence', 0.0)
                    else:
                        # Handle string format like "[pizza (likes)]"
                        entity = fact.replace('[', '').replace(']', '').split(' (')[0]
                        if 'likes' in fact or 'enjoys' in fact:
                            relationship = 'likes'
                        elif 'interested' in fact or 'hobby' in fact:
                            relationship = 'interested in'
                        else:
                            relationship = 'related to'
                        entity_name = entity
                        entity_type = ''
                        confidence = 0.7  # Default confidence for legacy format
                    
                    if entity_name:
                        # Get confidence-aware formatting with entity type
                        confidence_text = await self.build_confidence_aware_context([{
                            'entity_name': entity_name,
                            'entity_type': entity_type,
                            'relationship_type': relationship,
                            'confidence': confidence
                        }])
                        if confidence_text:
                            confidence_aware_facts.append(confidence_text)
                
                if confidence_aware_facts:
                    fact_parts.extend(confidence_aware_facts)
            
            if fact_parts:
                return "📋 Known Facts: " + "; ".join(fact_parts)
            
            return ""
            
        except Exception as e:
            logger.debug("Failed to get user facts context: %s", e)
            return ""

    async def _get_response_guidelines(self, character) -> str:  # character param kept for API compatibility
        """Get response guidelines including length constraints and formatting rules"""
        try:
            from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            from src.database.postgres_pool_manager import get_postgres_pool
            
            # Use cached connection pool from centralized manager
            pool = await get_postgres_pool()
            if not pool:
                logger.warning("⚠️ CDL AI Integration: No cached connection pool available")
                return ""
            
            enhanced_manager = create_enhanced_cdl_manager(pool)
            
            # Get bot name from environment (e.g., "elena", "marcus") - this is the database key
            bot_name = get_normalized_bot_name_from_env()
            logger.info(f"🔍 _get_response_guidelines: bot_name={bot_name}")
            
            if not bot_name:
                logger.warning("⚠️ _get_response_guidelines: No bot name found")
                return ""
            
            # Get response guidelines from database using bot name as key
            guidelines = await enhanced_manager.get_response_guidelines(bot_name)
            logger.info(f"🔍 _get_response_guidelines: Retrieved {len(guidelines)} guidelines from database")
            
            if not guidelines:
                logger.debug(f"📝 _get_response_guidelines: No guidelines found for bot_name={bot_name} (guidelines are optional)")
                return ""
            
            # Format guidelines dynamically - character-agnostic approach
            # Pull ALL guideline types from database, not just hardcoded ones
            critical_guidelines = []
            other_guidelines = []
            
            for guideline in guidelines:
                logger.info(f"🔍 Processing guideline: type={guideline.guideline_type}, critical={guideline.is_critical}, content={guideline.guideline_content[:50]}...")
                
                # Add emoji prefix based on type for readability
                type_emoji = {
                    'response_length': '📏',
                    'core_principle': '🎯',
                    'formatting_rule': '📝',
                    'formatting': '📝',
                    'emotional_tone': '💝',
                    'style': '🎨',
                }.get(guideline.guideline_type, '▪️')
                
                formatted_guideline = f"{type_emoji} {guideline.guideline_content}"
                
                # Separate critical vs non-critical for prioritization
                if guideline.is_critical:
                    critical_guidelines.append(formatted_guideline)
                else:
                    other_guidelines.append(formatted_guideline)
            
            # Build response guidelines section with critical guidelines first
            guidelines_text = []
            
            logger.info(f"🔍 DEBUG: critical_guidelines count={len(critical_guidelines)}, other_guidelines count={len(other_guidelines)}")
            
            # Add all critical guidelines (these are most important)
            if critical_guidelines:
                guidelines_text.extend(critical_guidelines)
                logger.info(f"✅ Added {len(critical_guidelines)} critical guidelines to prompt")
            
            # Add up to 5 non-critical guidelines (to avoid prompt bloat)
            if other_guidelines:
                guidelines_text.extend(other_guidelines[:5])
                logger.info(f"✅ Added {len(other_guidelines[:5])} additional guidelines to prompt")
            
            logger.info(f"🔍 DEBUG: Final guidelines_text length={len(guidelines_text)}")
            
            if guidelines_text:
                return "\n" + "\n".join(guidelines_text)
            
            return ""
            
            # Note: No pool.close() needed - using shared cached pool
                
        except Exception as e:
            logger.debug("Could not load response guidelines: %s", e)
            return ""

    async def _build_dynamic_custom_fields(self, full_character_data: dict, character_name: str, message_content: str = "") -> str:
        """🚀 DYNAMIC FIELD BUILDER: Build prompt sections from all available custom fields
        
        OPTIMIZATION: Context-aware section insertion - only include sections when relevant
        to reduce prompt bloat and improve token efficiency.
        """
        dynamic_sections = []
        
        # Sections that are handled by specialized logic, not dumped as prompt text
        skip_sections = [
            'identity',  # Handled separately as character identity
            'personality',  # Handled separately with Big Five trait optimization (line ~768)
            'behavioral_triggers',  # Now handled by trigger-based mode controller
            'message_triggers',  # Now handled by trigger-based mode controller
            'interaction_modes'  # Now handled by trigger-based mode controller
        ]
        
        # 🚨 OPTIMIZATION: Sections that are rarely needed - skip unless empty or low-value
        # These bloat prompts without adding conversational value in most contexts
        conditional_skip_sections = [
            'metadata',  # Version/tags/author - not useful for character responses
            'communication_patterns',  # Redundant with VOICE & COMMUNICATION STYLE section
        ]
        
        # 🎯 CONTEXT-AWARE: Sections only inserted when message content suggests relevance
        contextual_sections = {
            'values_and_beliefs': ['value', 'belief', 'fear', 'principle', 'ethic', 'moral', 'important to you', 'care about'],
            'abilities': ['skill', 'ability', 'expertise', 'can you', 'know how to', 'experience in', 'good at'],
            'background': ['history', 'past', 'grew up', 'background', 'education', 'career', 'where did you', 'family'],
        }
        
        # Process each data section dynamically with smart filtering
        for section_name, section_data in full_character_data.items():
            if section_name in skip_sections:
                continue
            
            # Skip low-value metadata sections
            if section_name in conditional_skip_sections:
                logger.debug(f"⏭️ OPTIMIZATION: Skipping low-value section: {section_name}")
                continue
            
            # 🎯 CONTEXT-AWARE: Check if contextual section should be included
            if section_name in contextual_sections:
                keywords = contextual_sections[section_name]
                message_lower = message_content.lower()
                
                # Only include if message contains relevant keywords
                if not any(keyword in message_lower for keyword in keywords):
                    logger.debug(f"⏭️ CONTEXT: Skipping {section_name} (not relevant to message)")
                    continue
                else:
                    logger.info(f"✅ CONTEXT: Including {section_name} (message matches keywords)")
            
            # Skip sections with empty/None data to avoid prompt bloat
            if not section_data:
                logger.debug(f"⏭️ EMPTY: Skipping empty section: {section_name}")
                continue
            
            # Skip background section if all entries have empty descriptions (common issue)
            if section_name == 'background' and isinstance(section_data, dict):
                has_content = False
                for category, entries in section_data.items():
                    if isinstance(entries, list) and any(entry.get('description') for entry in entries):
                        has_content = True
                        break
                if not has_content:
                    logger.debug(f"⏭️ EMPTY: Skipping background section (no actual content)")
                    continue
                
            section_content = await self._process_data_section(section_name, section_data, character_name)
            if section_content:
                dynamic_sections.append(section_content)
        
        return ''.join(dynamic_sections) if dynamic_sections else ""
    
    async def _process_data_section(self, section_name: str, section_data, character_name: str) -> str:
        """Process individual data section into prompt content"""
        if not section_data:
            return ""
        
        try:
            # Handle different data types
            if isinstance(section_data, dict):
                return await self._process_dict_section(section_name, section_data, character_name)
            elif isinstance(section_data, list):
                return await self._process_list_section(section_name, section_data, character_name)
            elif isinstance(section_data, str):
                return f"\n\n🎯 {section_name.upper().replace('_', ' ')}: {section_data}"
            elif isinstance(section_data, bool):
                if section_data:  # Only add if True
                    return f"\n\n✅ {section_name.upper().replace('_', ' ')}: Enabled"
            else:
                return f"\n\n📋 {section_name.upper().replace('_', ' ')}: {str(section_data)}"
        except Exception as e:
            logger.debug(f"Could not process section {section_name}: {e}")
            return ""
    
    async def _process_dict_section(self, section_name: str, section_data: dict, character_name: str) -> str:
        """Process dictionary data sections with nested custom fields"""
        if not section_data:
            return ""
        
        section_parts = []
        section_header = f"\n\n🎯 {section_name.upper().replace('_', ' ')}:"
        
        for field_name, field_value in section_data.items():
            if not field_value:
                continue
                
            field_title = field_name.replace('_', ' ').title()
            
            if isinstance(field_value, dict):
                # 🚨 FIX: Properly format nested dicts (values_and_beliefs, ai_identity_handling, communication_style)
                # Check if dict has standard keys like 'value', 'description', 'philosophy', etc.
                if 'value' in field_value and 'description' in field_value:
                    # Communication style format: {'value': 'High', 'description': 'Engagement level'}
                    value = field_value.get('value', '')
                    if value:  # Only show if there's an actual value
                        # 🎯 PROMPT QUALITY: Translate numeric scales to natural language
                        if field_name == 'engagement_level':
                            try:
                                numeric_val = float(value)
                                translated_value = self._translate_engagement_level(numeric_val)
                                section_parts.append(f"\n📋 Engagement: {translated_value}")
                            except (ValueError, TypeError):
                                section_parts.append(f"\n📋 {field_title}: {value}")
                        elif field_name == 'emotional_expression':
                            try:
                                numeric_val = float(value)
                                translated_value = self._translate_emotional_expression(numeric_val)
                                section_parts.append(f"\n📋 Emotional Expression: {translated_value}")
                            except (ValueError, TypeError):
                                section_parts.append(f"\n📋 {field_title}: {value}")
                        else:
                            section_parts.append(f"\n📋 {field_title}: {value}")
                elif 'description' in field_value:
                    # Values/beliefs format: {'key': 'fear_1', 'description': 'text', 'importance': 'high'}
                    desc = field_value.get('description', '')
                    importance = field_value.get('importance', '')
                    if importance:
                        section_parts.append(f"\n📋 {field_title}:  • {desc} (Importance: {importance})")
                    else:
                        section_parts.append(f"\n📋 {field_title}:  • {desc}")
                elif 'philosophy' in field_value or 'approach' in field_value:
                    # AI identity handling format: {'philosophy': '...', 'approach': '...', ...}
                    nested_parts = []
                    for sub_key, sub_value in field_value.items():
                        if sub_value and sub_key not in ['tier_1_response', 'tier_2_response', 'tier_3_response', 'response_pattern']:
                            # Skip tier responses - too verbose for main prompt
                            sub_title = sub_key.replace('_', ' ').title()
                            # Truncate long values for readability
                            if isinstance(sub_value, str) and len(sub_value) > 150:
                                sub_value = sub_value[:147] + "..."
                            nested_parts.append(f"  • {sub_title}: {sub_value}")
                    
                    if nested_parts:
                        section_parts.append(f"\n📋 {field_title}:")
                        section_parts.extend(nested_parts)
                else:
                    # Generic nested dictionary - format as sub-sections
                    nested_parts = []
                    for sub_key, sub_value in field_value.items():
                        if sub_value:
                            sub_title = sub_key.replace('_', ' ').title()
                            # 🚨 FIX: Handle nested dicts/lists properly, don't just stringify
                            if isinstance(sub_value, dict):
                                # Further nested - create compact representation
                                compact = ', '.join([f"{k}: {v}" for k, v in sub_value.items() if v][:3])
                                nested_parts.append(f"  • {sub_title}: {compact}")
                            elif isinstance(sub_value, list):
                                # Nested list - show first few items
                                items = ', '.join([str(item) for item in sub_value[:3]])
                                if len(sub_value) > 3:
                                    items += f" (and {len(sub_value) - 3} more)"
                                nested_parts.append(f"  • {sub_title}: {items}")
                            else:
                                nested_parts.append(f"  • {sub_title}: {sub_value}")
                    
                    if nested_parts:
                        section_parts.append(f"\n📋 {field_title}:")
                        section_parts.extend(nested_parts)
            
            elif isinstance(field_value, list):
                # 🚨 FIX: Properly format lists (don't dump raw dict objects)
                if field_value:
                    section_parts.append(f"\n📋 {field_title}:")
                    for item in field_value:
                        if isinstance(item, dict):
                            # List of dicts (common in values_and_beliefs)
                            if 'description' in item:
                                desc = item.get('description', '')
                                importance = item.get('importance', '')
                                if importance:
                                    section_parts.append(f"  • {desc} (Importance: {importance})")
                                else:
                                    section_parts.append(f"  • {desc}")
                            else:
                                # Generic dict in list - create compact representation
                                compact = ', '.join([f"{k}: {v}" for k, v in item.items() if v][:3])
                                section_parts.append(f"  • {compact}")
                        else:
                            # Simple item
                            section_parts.append(f"  • {item}")
            
            else:
                # Simple field
                section_parts.append(f"\n📋 {field_title}: {field_value}")
        
        if section_parts:
            return section_header + ''.join(section_parts)
        return ""
    
    async def _process_list_section(self, section_name: str, section_data: list, character_name: str) -> str:
        """Process list data sections (behavioral triggers, relationships, etc.)"""
        if not section_data:
            return ""
        
        section_header = f"\n\n🎯 {section_name.upper().replace('_', ' ')}:"
        items = []
        
        for item in section_data:
            if hasattr(item, '__dict__'):
                # Object with attributes
                item_parts = []
                for attr_name, attr_value in item.__dict__.items():
                    if attr_value and not attr_name.startswith('_'):
                        attr_title = attr_name.replace('_', ' ').title()
                        item_parts.append(f"{attr_title}: {attr_value}")
                
                if item_parts:
                    items.append(f"\n  • {' | '.join(item_parts)}")
            
            elif isinstance(item, dict):
                # Dictionary item
                item_parts = []
                for key, value in item.items():
                    if value:
                        key_title = key.replace('_', ' ').title()
                        item_parts.append(f"{key_title}: {value}")
                
                if item_parts:
                    items.append(f"\n  • {' | '.join(item_parts)}")
            
            else:
                # Simple item
                items.append(f"\n  • {item}")
        
        if items:
            return section_header + ''.join(items)
        return ""