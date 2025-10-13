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
        
        # 🚀 PERFORMANCE: Character caching for load_character performance
        self._cached_character = None
        self._cached_character_bot_name = None
        
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

    async def create_unified_character_prompt(
        self,
        user_id: str,
        message_content: str,
        pipeline_result=None,  # Accept any type - will be converted to dict if needed
        user_name: Optional[str] = None,
        character_file: Optional[str] = None  # Legacy compatibility - ignored in database-only mode
    ) -> str:
        """
        🎯 UNIFIED CHARACTER PROMPT CREATION - ALL FEATURES IN ONE PATH
        
        This method consolidates ALL intelligence features into one fidelity-first path:
        ✅ CDL character loading and personality integration  
        ✅ Memory retrieval and emotional analysis integration
        ✅ Personal knowledge extraction (relationships, family, work, etc.)
        ✅ AI identity handling and conversation flow
        ✅ Fidelity-first size management with intelligent optimization
        ✅ All intelligence components (context switching, empathy, etc.)
        """
        try:
            # STEP 1: Load CDL character and determine context
            character = await self.load_character(character_file)
            # Safe character name/occupation access for logging
            safe_name = character.identity.name if character.identity.name else "Unknown Character"
            safe_occupation = character.identity.occupation if character.identity.occupation else "Unknown Occupation"
            safe_description = character.identity.description[:100] if character.identity.description else "No description"
            
            logger.info("🎭 UNIFIED: Loaded CDL character: %s", safe_name)
            print(f"🔍 DEBUG: Character loaded - name: '{safe_name}', occupation: '{safe_occupation}', description: '{safe_description}...'", flush=True)

            # STEP 2: Get user's preferred name with Discord username fallback
            preferred_name = None
            if user_name:
                try:
                    # Use memory manager to get preferred name
                    if self.memory_manager:
                        from src.utils.user_preferences import get_user_preferred_name
                        preferred_name = await get_user_preferred_name(user_id, self.memory_manager, user_name)
                        logger.debug("🔄 PREFERENCE: Retrieved preferred name '%s'", preferred_name)
                except Exception as e:
                    logger.debug("Could not retrieve preferred name: %s", e)

            display_name = preferred_name or user_name or "User"
            logger.info("🎭 UNIFIED: Using display name: %s", display_name)
            
            # STEP 3: Retrieve relevant memories, conversation history, and long-term summaries
            relevant_memories = []
            conversation_history = []
            conversation_summary = ""
            
            if self.memory_manager:
                try:
                    relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                        user_id=user_id, query=message_content, limit=10
                    )
                    conversation_history = await self.memory_manager.get_conversation_history(
                        user_id=user_id, limit=3
                    )
                    
                    # LONG-TERM MEMORY: Get conversation summary for context beyond the limit
                    if hasattr(self.memory_manager, 'get_conversation_summary_with_recommendations'):
                        summary_data = await self.memory_manager.get_conversation_summary_with_recommendations(
                            user_id=user_id, limit=20  # Get broader context for summary
                        )
                        if summary_data and summary_data.get('topic_summary'):
                            conversation_summary = summary_data['topic_summary']
                            logger.info("🧠 LONG-TERM: Retrieved conversation summary: %s", conversation_summary[:100])
                    
                    logger.info("🧠 UNIFIED: Retrieved %d memories, %d conversation entries, summary: %s", 
                               len(relevant_memories), len(conversation_history), 
                               "Yes" if conversation_summary else "No")
                        
                except Exception as e:
                    logger.error("❌ MEMORY ERROR: Could not retrieve memories: %s", e)

            # STEP 4: Build comprehensive prompt with ALL intelligence
            prompt = await self._build_unified_prompt(
                character=character,
                user_id=user_id,
                display_name=display_name,
                message_content=message_content,
                pipeline_result=pipeline_result,
                relevant_memories=relevant_memories,
                conversation_history=conversation_history,
                conversation_summary=conversation_summary
            )

            # STEP 5: Apply fidelity-first size management
            return await self._apply_unified_fidelity_first_optimization(
                prompt=prompt,
                character=character,
                message_content=message_content,
                relevant_memories=relevant_memories,
                conversation_history=conversation_history,
                pipeline_result=pipeline_result
            )

        except Exception as e:
            logger.error("🚨 UNIFIED: CDL integration failed: %s", str(e))
            
            # 🔍 Import traceback to get exact line where error occurred
            import traceback
            logger.error(f"🔍 TRACEBACK: {traceback.format_exc()}")
            
            raise

    async def _build_unified_prompt(
        self,
        character,
        user_id: str,
        display_name: str,
        message_content: str,
        pipeline_result,  # Accept any type
        relevant_memories: list,
        conversation_history: list,
        conversation_summary: str = ""
    ) -> str:
        """🏗️ Build comprehensive prompt with ALL intelligence features in one place."""
        
        # Convert pipeline_result to dict if it's not already
        if pipeline_result and hasattr(pipeline_result, '__dict__'):
            # Convert object to dict for consistent access
            pipeline_dict = pipeline_result.__dict__
        elif isinstance(pipeline_result, dict):
            pipeline_dict = pipeline_result
        else:
            pipeline_dict = {}
        
        # 🎭 CRITICAL: Start with character identity FIRST for proper foundation
        prompt = ""
        
        # Base character identity - WHO ARE YOU (must come first) - with null safety
        character_name = character.identity.name if character.identity.name else "AI Character"
        character_occupation = character.identity.occupation if character.identity.occupation else "AI Assistant"
        
        # Safe bot name helper for database queries (prevents None default in os.getenv)
        safe_bot_name_fallback = character_name if character_name != "AI Character" else "unknown"
        
        character_identity_line = f"You are {character_name}, a {character_occupation}."
        print(f"🔍 DEBUG: Building character identity line: '{character_identity_line}'", flush=True)
        prompt += character_identity_line
        
        # Add character description
        if hasattr(character.identity, 'description') and character.identity.description:
            prompt += f" {character.identity.description}"
        
        # 🎭 TRIGGER-BASED MODE DETECTION: Detect and apply appropriate interaction mode
        mode_detection_result = None
        active_mode = None  # 🎯 OPTIMIZATION: Track active mode for conversation flow filtering
        try:
            mode_detection_result = await self.trigger_mode_controller.detect_active_mode(
                character_name=character_name,
                message_content=message_content,
                previous_mode=self._previous_mode
            )
            
            if mode_detection_result.active_mode:
                # 🎯 OPTIMIZATION: Extract active mode for conversation flow filtering
                active_mode = mode_detection_result.active_mode.mode_name
                
                # Apply mode to prompt
                prompt = self.trigger_mode_controller.apply_mode_to_prompt(
                    base_prompt=prompt,
                    active_mode=mode_detection_result.active_mode,
                    mode_switched=mode_detection_result.mode_switched
                )
                
                # Update previous mode for next interaction
                self._previous_mode = mode_detection_result.active_mode.mode_name
                
                logger.info(f"🎭 MODE APPLIED: {active_mode} "
                           f"(source: {mode_detection_result.active_mode.trigger_source}, "
                           f"confidence: {mode_detection_result.active_mode.confidence:.2f}, "
                           f"triggers: {mode_detection_result.detected_triggers})")
        except Exception as e:
            logger.debug(f"Could not detect interaction mode: {e}")
        
        # 🚀 DYNAMIC CUSTOM FIELDS: Build from all available character data sections
        try:
            full_character_data = character.get_full_character_data()
            prompt += await self._build_dynamic_custom_fields(full_character_data, character_name)
            logger.info(f"✅ DYNAMIC FIELDS: Built custom field sections from {len(full_character_data)} data sections")
        except Exception as e:
            logger.debug(f"Could not build dynamic custom fields: {e}")
        
        # Add AI identity handling early for proper identity establishment (DATABASE-DRIVEN)
        try:
            from src.prompts.generic_keyword_manager import get_keyword_manager
            keyword_manager = get_keyword_manager()
            
            if await keyword_manager.check_message_for_category(message_content, 'ai_identity'):
                # Use safe character name (already defined above)
                prompt += f" If asked about AI nature, respond authentically as {character_name} while being honest about your AI nature when directly asked."
                logger.debug("🤖 AI IDENTITY: Detected AI-related keywords in message")
        except Exception as e:
            # Fallback to basic detection if database unavailable
            if any(ai_keyword in message_content.lower() for ai_keyword in ['ai', 'artificial intelligence', 'robot', 'computer', 'program', 'bot']):
                # Use safe character name (already defined above)
                prompt += f" If asked about AI nature, respond authentically as {character_name} while being honest about your AI nature when directly asked."
                logger.debug("🤖 AI IDENTITY: Used fallback keyword detection")
        
        # 🕒 TEMPORAL AWARENESS: Add current date/time context 
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        prompt += f"\n\nCURRENT DATE & TIME: {time_context}\n\n"
        
        # 🧠 USER PERSONALITY & FACTS INTEGRATION - NEW!
        try:
            user_context = await self._build_user_context_section(user_id, display_name)
            if user_context:
                prompt += f"\n\n{user_context}"
        except Exception as e:
            logger.debug("Could not extract user personality/facts context: %s", e)
        
        # 🎯 OPTIMIZATION: Response style guidelines removed from here - they're injected at END
        # of prompt (line ~1778) for maximum LLM recency bias impact. No duplication needed.
        # See: ✨ RESPONSE STYLE REMINDER ✨ section at end of prompt
        
        # Add Big Five personality integration with Sprint 4 CharacterEvolution optimization
        if hasattr(character, 'personality') and hasattr(character.personality, 'big_five'):
            big_five = character.personality.big_five
            prompt += f"\n\n🧬 PERSONALITY PROFILE:\n"
            
            # 🎯 SPRINT 4: Extract CharacterEvolution optimization data from pipeline
            character_optimization = None
            try:
                if pipeline_dict and 'ai_components' in pipeline_dict:
                    ai_components = pipeline_dict['ai_components']
                    # Check for character_optimization (actual field name used in message processor)
                    if isinstance(ai_components, dict) and 'character_optimization' in ai_components:
                        character_optimization = ai_components['character_optimization']
                        logger.info(f"🎭 CHARACTER: Found Sprint 4 optimization data: {character_optimization}")
                    # Also check for character_evolution (legacy/alternative field name)
                    elif isinstance(ai_components, dict) and 'character_evolution' in ai_components:
                        character_optimization = ai_components['character_evolution']
                        logger.info(f"🎭 CHARACTER: Found Sprint 4 evolution data: {character_optimization}")
                    else:
                        logger.info(f"🎭 CHARACTER: No character_optimization found in ai_components: {list(ai_components.keys()) if ai_components else 'None'}")
                else:
                    logger.info(f"🎭 CHARACTER: No ai_components in pipeline_dict: {list(pipeline_dict.keys()) if pipeline_dict else 'None'}")
            except Exception as e:
                logger.info(f"🎭 CHARACTER: Could not extract optimization data: {e}")
            
            # Helper function to get adaptive trait description with Sprint 4 optimization
            def get_adaptive_trait_info(trait_obj, trait_name):
                # Get base CDL trait value
                base_score = None
                base_description = ""
                
                # Trait name mapping
                trait_map = {
                    'openness': 'Openness to experience',
                    'conscientiousness': 'Conscientiousness',
                    'extraversion': 'Extraversion', 
                    'agreeableness': 'Agreeableness',
                    'neuroticism': 'Neuroticism'
                }
                trait_label = trait_map.get(trait_name, trait_name.title())
                
                if hasattr(trait_obj, 'trait_description'):
                    # New object format from database
                    base_score = trait_obj.score if hasattr(trait_obj, 'score') else None
                    if base_score is None and hasattr(trait_obj, 'value'):
                        base_score = trait_obj.value
                    # Build proper description with trait name
                    level = 'High' if base_score and base_score > 0.7 else 'Moderate' if base_score and base_score > 0.4 else 'Low'
                    base_description = f"{trait_label}: {level}"
                elif isinstance(trait_obj, (float, int)):
                    # Legacy float format
                    base_score = trait_obj
                    level = 'High' if base_score > 0.7 else 'Moderate' if base_score > 0.4 else 'Low'
                    base_description = f"{trait_label}: {level}"
                
                # 🎯 SPRINT 4: Apply optimization adjustments if available
                if character_optimization and isinstance(character_optimization, dict):
                    # Check for direct personality_optimizations field
                    optimizations = character_optimization.get('personality_optimizations', {})
                    
                    # If no direct optimizations, generate from optimization_opportunities
                    if not optimizations and 'optimization_opportunities' in character_optimization:
                        opportunities = character_optimization.get('optimization_opportunities', [])
                        for opp in opportunities:
                            if opp.get('category') == 'educational_approach' and 'affected_traits' in opp:
                                # Convert educational traits to personality adjustments
                                affected_traits = opp.get('affected_traits', [])
                                if 'teaching_patience' in affected_traits:
                                    optimizations['conscientiousness'] = 0.05  # More patient = higher conscientiousness
                                if 'explanation_style' in affected_traits or 'metaphor_usage' in affected_traits:
                                    optimizations['openness'] = 0.03  # Better explanations = higher openness
                    
                    if trait_name in optimizations and base_score is not None:
                        adjustment = optimizations[trait_name]
                        adjusted_score = base_score + adjustment
                        
                        # Apply Sprint 4 constraint: max 15% trait boundary adjustment
                        max_adjustment = 0.15
                        if abs(adjustment) <= max_adjustment:
                            # Show adaptive personality with optimization
                            direction = "↗" if adjustment > 0 else "↘" if adjustment < 0 else "→"
                            adaptation_reason = character_optimization.get('adaptation_reasoning', 'improved conversation effectiveness')
                            return f"{base_description} ({base_score:.1f} {direction} {adjusted_score:.2f}) - Adapted for {adaptation_reason}"
                        else:
                            # Constraint exceeded - show warning but apply capped adjustment
                            capped_adjustment = max_adjustment if adjustment > 0 else -max_adjustment
                            capped_score = base_score + capped_adjustment
                            return f"{base_description} ({base_score:.1f} → {capped_score:.2f}) - Optimization capped at 15% boundary"
                
                # No optimization available - show static CDL trait
                if base_score is not None:
                    return f"{base_description} ({base_score})"
                else:
                    return base_description or f"{trait_name}: Unknown format"
            
            if hasattr(big_five, 'openness'):
                prompt += f"- {get_adaptive_trait_info(big_five.openness, 'openness')}\n"
            if hasattr(big_five, 'conscientiousness'):
                prompt += f"- {get_adaptive_trait_info(big_five.conscientiousness, 'conscientiousness')}\n"
            if hasattr(big_five, 'extraversion'):
                prompt += f"- {get_adaptive_trait_info(big_five.extraversion, 'extraversion')}\n"
            if hasattr(big_five, 'agreeableness'):
                prompt += f"- {get_adaptive_trait_info(big_five.agreeableness, 'agreeableness')}\n"
            if hasattr(big_five, 'neuroticism'):
                prompt += f"- {get_adaptive_trait_info(big_five.neuroticism, 'neuroticism')}\n"

        # � VOICE & COMMUNICATION STYLE: Consolidated section matching complete_prompt_examples format
        voice_section = await self._build_voice_communication_section(character)
        if voice_section:
            prompt += f"\n\n{voice_section}"

        # �🆕 PHASE 2: ADD RICH CHARACTER DATA FROM DATABASE
        # This integrates the migrated data from legacy JSON into system prompts
        
        # 💕 RELATIONSHIPS: Add character relationships (e.g., Gabriel-Cynthia)
        if self.enhanced_manager:
            try:
                bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
                relationships = await self.enhanced_manager.get_relationships(bot_name)
                if relationships:
                    prompt += f"\n\n💕 RELATIONSHIP CONTEXT:\n"
                    for rel in relationships:
                        if rel.relationship_strength >= 8:  # High-priority relationships
                            prompt += f"- **{rel.related_entity}** ({rel.relationship_type}): {rel.description}\n"
                            logger.info(f"✅ RELATIONSHIPS: Added high-priority relationship: {rel.related_entity}")
                        elif rel.relationship_strength >= 5:  # Medium-priority relationships
                            prompt += f"- {rel.related_entity}: {rel.description}\n"
                            logger.info(f"✅ RELATIONSHIPS: Added medium-priority relationship: {rel.related_entity}")
                    logger.info(f"✅ RELATIONSHIPS: Total {len(relationships)} relationship entries added to prompt")
            except Exception as e:
                logger.debug(f"Could not extract relationships: {e}")
        
        # ⚡ BEHAVIORAL TRIGGERS: Now handled by trigger-based mode controller above
        # Recognition responses and interaction patterns are applied through mode switching logic
        # instead of being dumped as prompt text. This provides intelligent behavior control
        # rather than raw data injection.
        
        # NOTE: 💬 SIGNATURE EXPRESSIONS, 🌍 AUTHENTIC VOICE PATTERNS, and 🎤 VOICE CHARACTERISTICS sections
        # have been consolidated into the unified VOICE & COMMUNICATION STYLE section above (line ~710)
        # to match complete_prompt_examples format. Keeping these original sections commented for reference:
        
        # # 💬 SPEECH PATTERNS: Add signature expressions and vocabulary (MOVED TO VOICE SECTION)
        # # 🌍 CULTURAL EXPRESSIONS: Add authentic voice patterns and phrases (MOVED TO VOICE SECTION)
        # # 🎤 VOICE TRAITS: Add tone, rhythm, and style characteristics (MOVED TO VOICE SECTION)
        
        # 🗣️ CONVERSATION FLOWS: Now handled by trigger-based mode controller above
        # Conversation flow guidance is intelligently selected based on message context and triggers.
        # The active mode detection system applies only relevant guidance instead of dumping all flows.
        # This prevents prompt bloat and ensures contextually appropriate responses.
        
        # 🎨 MESSAGE TRIGGERS: Now handled by trigger-based mode controller above
        # Message pattern triggers are used for mode switching logic instead of prompt dumping.
        # Active triggers are detected and applied through intelligent mode selection.
        
        # NOTE: 🌍 AUTHENTIC VOICE PATTERNS and 🎤 VOICE CHARACTERISTICS sections
        # consolidated into VOICE & COMMUNICATION STYLE section (see above)
        
        # 💭 EMOTIONAL TRIGGERS: Intelligent multi-source trigger system
        if self.enhanced_manager:
            try:
                bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
                emotional_triggers = await self.enhanced_manager.get_emotional_triggers(bot_name)
                if emotional_triggers:
                    # 🧠 INTELLIGENT TRIGGER FUSION: Use AI components instead of keyword matching
                    try:
                        from src.prompts.intelligent_trigger_fusion import get_intelligent_trigger_fusion
                        trigger_fusion = get_intelligent_trigger_fusion()
                        
                        # Get AI components from pipeline_result
                        ai_components = {}
                        if hasattr(pipeline_result, 'metadata') and pipeline_result.metadata:
                            ai_components = pipeline_result.metadata.get('ai_components', {})
                        
                        # Intelligent emotional trigger decision
                        trigger_decision = await trigger_fusion.should_trigger_emotional_guidance(ai_components, message_content)
                        
                        if trigger_decision.should_trigger:
                            # Get contextually relevant triggers based on decision evidence
                            relevant_triggers = []
                            for trigger in emotional_triggers:
                                # Use decision context to filter relevant triggers
                                trigger_relevance = self._calculate_trigger_relevance(trigger, trigger_decision.context_factors)
                                if trigger_relevance > 0.5:
                                    relevant_triggers.append(trigger)
                            
                            if relevant_triggers:
                                prompt += f"\n\n💭 EMOTIONAL RESPONSE GUIDANCE (AI-detected context):\n"
                                for trigger in relevant_triggers[:3]:  # Top 3 most relevant
                                    prompt += f"- {trigger.trigger_type.title()}: {trigger.emotional_response}\n"
                                logger.info(f"✅ EMOTIONAL TRIGGERS: AI fusion activated {len(relevant_triggers)} triggers "
                                           f"(confidence: {trigger_decision.confidence:.2f}, reason: {trigger_decision.trigger_reason})")
                            else:
                                logger.debug(f"💭 EMOTIONAL TRIGGERS: AI fusion suggested trigger but no relevant patterns found")
                        else:
                            # No active emotional triggers - character will use base personality
                            logger.debug(f"💭 EMOTIONAL TRIGGERS: AI fusion decided against triggering "
                                       f"(confidence: {trigger_decision.confidence:.2f}, reason: {trigger_decision.trigger_reason})")
                    
                    except ImportError:
                        # Fallback to keyword matching if fusion system unavailable
                        logger.debug("Intelligent trigger fusion unavailable, using keyword fallback")
                        message_lower = message_content.lower()
                        active_emotional_triggers = []
                        
                        for trigger in emotional_triggers:
                            # Check if trigger content keywords appear in message
                            trigger_keywords = trigger.trigger_content.lower().split()
                            if any(keyword in message_lower for keyword in trigger_keywords if len(keyword) > 3):
                                active_emotional_triggers.append(trigger)
                        
                        if active_emotional_triggers:
                            prompt += f"\n\n💭 EMOTIONAL RESPONSE GUIDANCE (keyword fallback):\n"
                            for trigger in active_emotional_triggers[:3]:  # Top 3 most relevant
                                prompt += f"- {trigger.trigger_type.title()}: {trigger.emotional_response}\n"
                            logger.info(f"✅ EMOTIONAL TRIGGERS: Keyword fallback activated {len(active_emotional_triggers)} triggers")
                        else:
                            # No active emotional triggers - character will use base personality
                            logger.debug(f"💭 EMOTIONAL TRIGGERS: No keyword triggers activated from {len(emotional_triggers)} available patterns")
            except Exception as e:
                logger.debug(f"Could not extract emotional triggers: {e}")
        
        # 🎓 EXPERTISE DOMAINS: Intelligent multi-source activation system
        if self.enhanced_manager:
            try:
                bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
                expertise_domains = await self.enhanced_manager.get_expertise_domains(bot_name)
                if expertise_domains:
                    # 🧠 INTELLIGENT TRIGGER FUSION: Use AI components instead of keyword matching
                    try:
                        from src.prompts.intelligent_trigger_fusion import get_intelligent_trigger_fusion
                        trigger_fusion = get_intelligent_trigger_fusion()
                        
                        # Get AI components from pipeline_result
                        ai_components = {}
                        if hasattr(pipeline_result, 'metadata') and pipeline_result.metadata:
                            ai_components = pipeline_result.metadata.get('ai_components', {})
                        
                        # Intelligent expertise trigger decision
                        trigger_decision = await trigger_fusion.should_trigger_expertise_domain(ai_components, message_content)
                        
                        if trigger_decision.should_trigger:
                            # Get contextually relevant domains based on decision evidence
                            relevant_domains = []
                            for domain in expertise_domains:
                                # Use semantic relevance instead of keyword matching
                                domain_relevance = self._calculate_domain_relevance(domain, trigger_decision.context_factors, message_content)
                                if domain_relevance > 0.4:  # Lower threshold since it's semantic
                                    relevant_domains.append(domain)
                            
                            if relevant_domains:
                                prompt += f"\n\n🎓 RELEVANT EXPERTISE (AI-detected context):\n"
                                for domain in relevant_domains[:3]:  # Top 3 most relevant
                                    prompt += f"- **{domain.domain_name}** (Level: {domain.expertise_level}, Passion: {domain.passion_level}/10)\n"
                                    if domain.teaching_approach:
                                        prompt += f"  Teaching approach: {domain.teaching_approach}\n"
                                logger.info(f"✅ EXPERTISE DOMAINS: AI fusion activated {len(relevant_domains)} domains "
                                           f"(confidence: {trigger_decision.confidence:.2f}, reason: {trigger_decision.trigger_reason})")
                            else:
                                logger.debug(f"🎓 EXPERTISE DOMAINS: AI fusion suggested trigger but no relevant domains found")
                        else:
                            # No relevant expertise domains - character will use general knowledge
                            logger.debug(f"🎓 EXPERTISE DOMAINS: AI fusion decided against triggering "
                                       f"(confidence: {trigger_decision.confidence:.2f}, reason: {trigger_decision.trigger_reason})")
                    
                    except ImportError:
                        # Fallback to keyword matching if fusion system unavailable
                        logger.debug("Intelligent trigger fusion unavailable, using keyword fallback")
                        message_lower = message_content.lower()
                        relevant_domains = []
                        
                        for domain in expertise_domains:
                            domain_keywords = domain.domain_name.lower().split()
                            if any(keyword in message_lower for keyword in domain_keywords if len(keyword) > 3):
                                relevant_domains.append(domain)
                        
                        if relevant_domains:
                            prompt += f"\n\n🎓 RELEVANT EXPERTISE (keyword fallback):\n"
                            for domain in relevant_domains[:3]:  # Top 3 most relevant
                                prompt += f"- **{domain.domain_name}** (Level: {domain.expertise_level}, Passion: {domain.passion_level}/10)\n"
                                if domain.teaching_approach:
                                    prompt += f"  Teaching approach: {domain.teaching_approach}\n"
                            logger.info(f"✅ EXPERTISE DOMAINS: Keyword fallback activated {len(relevant_domains)} domains")
                        else:
                            # No relevant expertise domains - character will use general knowledge
                            logger.debug(f"🎓 EXPERTISE DOMAINS: No keyword domains activated from {len(expertise_domains)} available areas")
            except Exception as e:
                logger.debug(f"Could not extract expertise domains: {e}")
        
        # 😊 EMOJI PATTERNS: Add digital communication style
        if self.enhanced_manager:
            try:
                bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
                emoji_patterns = await self.enhanced_manager.get_emoji_patterns(bot_name)
                if emoji_patterns:
                    # Group by pattern category
                    excitement_emojis = [e for e in emoji_patterns if 'excitement' in e.pattern_category.lower()]
                    context_emojis = [e for e in emoji_patterns if e.pattern_category not in ['excitement_level', 'general']]
                    
                    if excitement_emojis or context_emojis:
                        prompt += f"\n\n😊 EMOJI USAGE PATTERNS:\n"
                        
                        if excitement_emojis:
                            # Show excitement level guidance
                            for emoji_pattern in excitement_emojis[:3]:  # Low, medium, high
                                prompt += f"- {emoji_pattern.pattern_name}: {emoji_pattern.emoji_sequence}\n"
                        
                        if context_emojis:
                            # Show context-specific emoji usage
                            context_list = ', '.join([f"{e.pattern_name}: {e.emoji_sequence}" for e in context_emojis[:5]])
                            prompt += f"- Context-specific: {context_list}\n"
                        
                        logger.info(f"✅ EMOJI PATTERNS: Added {len(emoji_patterns)} emoji usage patterns")
            except Exception as e:
                logger.debug(f"Could not extract emoji patterns: {e}")
        
        # 🎭 AI SCENARIOS: Add physical interaction handling guidance (DATABASE-DRIVEN)
        if self.enhanced_manager:
            try:
                bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
                ai_scenarios = await self.enhanced_manager.get_ai_scenarios(bot_name)
                if ai_scenarios:
                    # Check if message contains physical interaction requests (DATABASE-DRIVEN)
                    try:
                        from src.prompts.generic_keyword_manager import get_keyword_manager
                        keyword_manager = get_keyword_manager()
                        
                        if await keyword_manager.check_message_for_category(message_content, 'physical_interaction'):
                            prompt += f"\n\n🎭 PHYSICAL INTERACTION GUIDANCE (roleplay request detected):\n"
                            for scenario in ai_scenarios:
                                if scenario.tier_responses:  # Has tiered response strategy
                                    prompt += f"- {scenario.scenario_name}: Use tier-appropriate response based on roleplay_immersion_level\n"
                            logger.info(f"✅ AI SCENARIOS: Activated physical interaction guidance ({len(ai_scenarios)} scenarios)")
                    except Exception as e:
                        # Fallback to basic detection if database unavailable
                        physical_keywords = ['hug', 'kiss', 'touch', 'hold', 'cuddle', 'pet', 'pat', 'embrace']
                        message_lower = message_content.lower()
                        
                        if any(keyword in message_lower for keyword in physical_keywords):
                            prompt += f"\n\n🎭 PHYSICAL INTERACTION GUIDANCE (roleplay request detected):\n"
                            for scenario in ai_scenarios:
                                if scenario.tier_responses:  # Has tiered response strategy
                                    prompt += f"- {scenario.scenario_name}: Use tier-appropriate response based on roleplay_immersion_level\n"
                            logger.info(f"✅ AI SCENARIOS: Activated physical interaction guidance ({len(ai_scenarios)} scenarios) - fallback")
            except Exception as e:
                logger.debug(f"Could not extract AI scenarios: {e}")

        # Add CDL conversation flow guidelines early for communication style establishment
        try:
            # 🎯 OPTIMIZATION: Pass active_mode to only inject ACTIVE mode guidance (not ALL modes)
            conversation_flow_guidance = self._extract_conversation_flow_guidelines(character, active_mode=active_mode)
            
            # Detect communication scenarios for context
            communication_scenarios = self._detect_communication_scenarios(message_content, character, display_name)
            scenario_guidance = self._get_cdl_conversation_flow_guidance(character.identity.name, communication_scenarios)
            
            # Combine flow guidelines with scenario guidance
            combined_guidance = []
            if conversation_flow_guidance:
                combined_guidance.append(conversation_flow_guidance)
            if scenario_guidance:
                combined_guidance.append(scenario_guidance)
                
            if combined_guidance:
                prompt += f"\n\n🎬 CONVERSATION FLOW & CONTEXT:\n{' '.join(combined_guidance)}"
        except Exception as e:
            logger.debug("Could not extract conversation flow guidance: %s", e)

        # 🚨 GUIDELINE OVERRIDE: Response guidelines are injected at END of prompt (see line ~1586)
        # This ensures they override memory patterns and conversation examples
        # DO NOT inject guidelines here - they need to be positioned AFTER memories and conversation history
        logger.info("📋 GUIDELINE POSITIONING: Response guidelines will be injected at END of prompt for maximum impact")

        # Add personal knowledge sections (relationships, family, career, etc.)
        try:
            personal_sections = await self._extract_cdl_personal_knowledge_sections(character, message_content, user_id)
            if personal_sections:
                prompt += f"\n\n👨‍👩‍👧‍👦 PERSONAL BACKGROUND:\n{personal_sections}"
                logger.info(f"✅ PERSONAL KNOWLEDGE: Added {len(personal_sections)} chars to prompt")
            else:
                logger.warning("⚠️ PERSONAL KNOWLEDGE: No sections returned from extraction")
        except Exception as e:
            logger.error(f"❌ PERSONAL KNOWLEDGE ERROR: Could not extract personal knowledge: {e}")
            import traceback
            logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")

        # � PHASE 2B: PROACTIVE CONTEXT INJECTION - Automatically inject relevant character knowledge when topics arise
        try:
            context_enhancer = await self._get_context_enhancer()
            if context_enhancer:
                # Use the existing API from CharacterContextEnhancer
                injection_result = await context_enhancer.detect_and_inject_context(
                    user_message=message_content,
                    character_name=character.identity.name,
                    base_system_prompt=prompt,
                    relevance_threshold=0.3  # Lower threshold for more context injection
                )
                
                if injection_result.injection_score > 0:
                    prompt = injection_result.enhanced_prompt
                    context_count = (len(injection_result.relevant_background) + 
                                   len(injection_result.relevant_abilities) + 
                                   len(injection_result.relevant_memories))
                    
                    logger.info(f"🎭 PROACTIVE CONTEXT: Injected {context_count} context items (score: {injection_result.injection_score:.2f})")
                    logger.info(f"🎭 DETECTED TOPICS: {injection_result.detected_topics}")
                    
                    # Log what was injected for debugging
                    if injection_result.relevant_background:
                        logger.debug(f"🎭 Background contexts: {len(injection_result.relevant_background)}")
                    if injection_result.relevant_abilities:
                        logger.debug(f"🎭 Ability contexts: {len(injection_result.relevant_abilities)}")
                    if injection_result.relevant_memories:
                        logger.debug(f"🎭 Memory contexts: {len(injection_result.relevant_memories)}")
                else:
                    logger.debug("🎭 PROACTIVE CONTEXT: No relevant context found for user message")
            else:
                logger.debug("🎭 PROACTIVE CONTEXT: CharacterContextEnhancer not available")
        except Exception as e:
            logger.error(f"❌ PROACTIVE CONTEXT ERROR: Context injection failed: {e}")
            import traceback
            logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")

        # �🎯 SEMANTIC KNOWLEDGE INTEGRATION: Retrieve structured facts from PostgreSQL
        if self.knowledge_router:
            try:
                # Analyze query intent to determine what facts to retrieve
                intent = await self.knowledge_router.analyze_query_intent(message_content)
                logger.info(f"🎯 KNOWLEDGE: Query intent detected: {intent.intent_type.value} (confidence: {intent.confidence:.2f})")
                
                # Lower confidence threshold for more liberal memory sprinkling (ChatGPT-like)
                if intent.confidence > 0.2 and intent.intent_type.value in ['factual_recall', 'relationship_discovery', 'entity_search']:
                    # Get character name from CDL for character-aware retrieval
                    character_name = character.identity.name.lower().split()[0] if character and hasattr(character, 'identity') else 'unknown'
                    
                    # Route to appropriate search method based on intent
                    if intent.intent_type.value == 'entity_search':
                        # Use full-text search for entity discovery
                        facts = await self.knowledge_router.search_entities(
                            search_query=message_content,
                            entity_type=intent.entity_type,
                            limit=15
                        )
                    else:
                        # Use character-aware facts for direct recall
                        facts = await self.knowledge_router.get_character_aware_facts(
                            user_id=user_id,
                            character_name=character_name,
                            entity_type=intent.entity_type,
                            limit=15
                        )
                    
                    if facts:
                        # Format facts for character-aware synthesis
                        prompt += f"\n\n📊 KNOWN FACTS ABOUT {display_name}:\n"
                        
                        # Group facts by entity type for better organization
                        facts_by_type = {}
                        for fact in facts:
                            entity_type = fact.get('entity_type', 'general')
                            if entity_type not in facts_by_type:
                                facts_by_type[entity_type] = []
                            facts_by_type[entity_type].append(fact)
                        
                        # Add facts with personality-first synthesis guidance
                        for entity_type, type_facts in sorted(facts_by_type.items()):
                            type_label = entity_type.replace('_', ' ').title()
                            prompt += f"\n{type_label}:\n"
                            for fact in type_facts[:5]:  # Limit per type
                                entity_name = fact.get('entity_name', 'unknown')
                                relationship = fact.get('relationship_type', 'related to')
                                confidence = fact.get('confidence', 0.0)
                                
                                # Include confidence for gradual knowledge building - STEP 6: Confidence-Aware Conversations
                                confidence_aware_text = await self.build_confidence_aware_context([{
                                    'entity_name': entity_name,
                                    'relationship_type': relationship,
                                    'confidence': confidence
                                }])
                                if confidence_aware_text:
                                    prompt += f"  {confidence_aware_text}\n"
                                else:
                                    # Fallback to original format
                                    confidence_marker = "✓" if confidence > 0.8 else "~" if confidence > 0.5 else "?"
                                    prompt += f"  {confidence_marker} {relationship}: {entity_name}\n"
                        
                        # Add personality-first synthesis instruction
                        prompt += f"\nInterpret these facts through {character.identity.name}'s personality and communication style."
                        prompt += " Weave them naturally into conversation, not as robotic data delivery."
                        
                        logger.info(f"🎯 KNOWLEDGE: Added {len(facts)} structured facts across {len(facts_by_type)} categories")
                    else:
                        logger.debug("🎯 KNOWLEDGE: No facts found for query intent")
                else:
                    # ChatGPT-style contextual memory sprinkling for all other queries
                    # Even if intent confidence is low, try to find relevant memories
                    character_name = character.identity.name.lower().split()[0] if character and hasattr(character, 'identity') else 'unknown'
                    
                    # Try multiple search approaches for better memory coverage
                    contextual_facts = []
                    
                    # 1. Try keyword-based search
                    try:
                        keyword_facts = await self.knowledge_router.search_entities(
                            search_query=message_content,
                            limit=5
                        )
                        contextual_facts.extend(keyword_facts)
                    except:
                        pass
                    
                    # 2. Try general user facts if no specific matches
                    if len(contextual_facts) < 3:
                        try:
                            general_facts = await self.knowledge_router.get_character_aware_facts(
                                user_id=user_id,
                                character_name=character_name,
                                limit=8
                            )
                            contextual_facts.extend(general_facts)
                        except:
                            pass
                    
                    # Add contextual facts if found (ChatGPT-style subtle integration)
                    if contextual_facts:
                        unique_facts = []
                        seen_entities = set()
                        for fact in contextual_facts:
                            entity_name = fact.get('entity_name', '')
                            if entity_name and entity_name not in seen_entities:
                                unique_facts.append(fact)
                                seen_entities.add(entity_name)
                                if len(unique_facts) >= 5:  # Limit for natural integration
                                    break
                        
                        if unique_facts:
                            prompt += f"\n\n💭 CONTEXTUAL MEMORIES:\n"
                            for fact in unique_facts:
                                entity_name = fact.get('entity_name', 'unknown')
                                relationship = fact.get('relationship_type', 'related to')
                                prompt += f"  • {relationship}: {entity_name}\n"
                            
                            prompt += "\nWeave these memories naturally into conversation when relevant - don't force them."
                            logger.debug(f"🎯 CONTEXTUAL: Added {len(unique_facts)} background memories")
                
                    logger.debug(f"🎯 KNOWLEDGE: Skipping primary fact retrieval (intent: {intent.intent_type.value}, confidence: {intent.confidence:.2f})")
            except Exception as e:
                logger.error(f"❌ KNOWLEDGE: Fact retrieval failed: {e}")
                
        # 🤖 AI INTELLIGENCE GUIDANCE: Include comprehensive intelligence analysis
        if pipeline_result:
            try:
                # Convert pipeline_result to dict for access
                pipeline_dict = pipeline_result
                if hasattr(pipeline_result, '__dict__'):
                    pipeline_dict = pipeline_result.__dict__
                
                # Extract comprehensive context from enhanced_context (where it's actually stored)
                comprehensive_context = pipeline_dict.get('enhanced_context', {})
                if not comprehensive_context:
                    # Fallback: Try direct comprehensive_context attribute
                    comprehensive_context = pipeline_dict.get('comprehensive_context', {})
                
                logger.debug(f"🔍 CDL DEBUG: pipeline_dict keys: {list(pipeline_dict.keys())}")
                logger.debug(f"🔍 CDL DEBUG: comprehensive_context found: {bool(comprehensive_context)}, keys: {list(comprehensive_context.keys()) if isinstance(comprehensive_context, dict) else 'N/A'}")
                
                # 🔍 CRITICAL DEBUGGING: Check comprehensive_context type before processing
                logger.debug(f"🔍 CDL DEBUG: comprehensive_context type: {type(comprehensive_context)}")
                if not isinstance(comprehensive_context, dict):
                    logger.error(f"🚨 FOUND ISSUE: comprehensive_context is {type(comprehensive_context)}, not dict: {comprehensive_context}")
                    raise TypeError(f"comprehensive_context should be dict but is {type(comprehensive_context)}: {comprehensive_context}")
                
                if comprehensive_context:
                    guidance_parts = []
                    
                    # 🎭 BOT EMOTIONAL SELF-AWARENESS (Phase 7.6 - NEW)
                    bot_emotional_state = comprehensive_context.get('bot_emotional_state')
                    if bot_emotional_state and isinstance(bot_emotional_state, dict):
                        current_emotion = bot_emotional_state.get('current_emotion', 'neutral')
                        current_intensity = bot_emotional_state.get('current_intensity', 0.0)
                        trajectory = bot_emotional_state.get('trajectory_direction', 'stable')
                        emotional_context = bot_emotional_state.get('emotional_context', '')
                        mixed_emotions = bot_emotional_state.get('current_mixed_emotions', [])
                        
                        # Build bot emotional awareness guidance
                        emotion_guidance = f"🎭 YOUR EMOTIONAL STATE: You are currently feeling {current_emotion}"
                        if current_intensity > 0.7:
                            emotion_guidance += f" (strongly, intensity: {current_intensity:.2f})"
                        elif current_intensity > 0.4:
                            emotion_guidance += f" (moderately, intensity: {current_intensity:.2f})"
                        
                        # Add mixed emotions if present
                        if mixed_emotions:
                            mixed_str = ", ".join([f"{e} ({i:.2f})" for e, i in mixed_emotions[:2]])
                            emotion_guidance += f" with undertones of {mixed_str}"
                        
                        # Add emotional trajectory awareness
                        if trajectory == "intensifying":
                            emotion_guidance += ". Your emotions have been intensifying in recent conversations"
                        elif trajectory == "calming":
                            emotion_guidance += ". Your emotions have been calming down recently"
                        
                        emotion_guidance += ". Be authentic to this emotional state in your response - let it naturally influence your tone and word choice"
                        
                        guidance_parts.append(emotion_guidance)
                        logger.debug(f"🎭 BOT SELF-AWARE: Added emotional state to prompt - {emotional_context}")
                    
                    # Context Switch Detection (Phase 3)
                    context_switches = comprehensive_context.get('context_switches')
                    if context_switches and isinstance(context_switches, dict):
                        switch_type = context_switches.get('switch_type', 'none')
                        confidence = context_switches.get('confidence', 0)
                        if switch_type != 'none' and confidence > 0.6:
                            guidance_parts.append(f"🔄 TOPIC TRANSITION: {switch_type} detected (confidence: {confidence:.2f}) - acknowledge the shift naturally")
                    
                    # Mode Switching Detection (Phase 3) - Check if conversation mode changed
                    conversation_analysis = comprehensive_context.get('conversation_analysis')
                    if conversation_analysis and isinstance(conversation_analysis, dict):
                        conversation_mode = conversation_analysis.get('conversation_mode', 'standard')
                        previous_mode = conversation_analysis.get('previous_mode')
                        if previous_mode and previous_mode != conversation_mode:
                            guidance_parts.append(f"🎭 MODE SWITCH: {previous_mode} → {conversation_mode} - adapt your response style accordingly")
                    
                    # Urgency Detection (Phase 3)
                    urgency_analysis = comprehensive_context.get('urgency_analysis')
                    if urgency_analysis and isinstance(urgency_analysis, dict):
                        urgency_level = urgency_analysis.get('urgency_level', 0.3)
                        if urgency_level > 0.7:
                            guidance_parts.append(f"⚡ HIGH URGENCY: Level {urgency_level:.2f} - respond quickly and directly")
                        elif urgency_level > 0.5:
                            guidance_parts.append(f"⏰ MODERATE URGENCY: Level {urgency_level:.2f} - acknowledge time sensitivity")
                    
                    # Empathy Calibration (Phase 3)
                    empathy_analysis = comprehensive_context.get('empathy_analysis')
                    if empathy_analysis and isinstance(empathy_analysis, dict):
                        empathy_style = empathy_analysis.get('empathy_style')
                        confidence = empathy_analysis.get('confidence', 0)
                        if empathy_style and confidence > 0.6:
                            guidance_parts.append(f"💝 EMPATHY: Use {empathy_style} approach (confidence: {confidence:.2f})")
                    
                    # Intent Change Detection (Phase 3)
                    intent_analysis = comprehensive_context.get('intent_analysis')  
                    if intent_analysis and isinstance(intent_analysis, dict):
                        current_intent = intent_analysis.get('current_intent')
                        previous_intent = intent_analysis.get('previous_intent')
                        if previous_intent and previous_intent != current_intent:
                            guidance_parts.append(f"🎯 INTENT SHIFT: {previous_intent} → {current_intent} - adjust response focus")
                    
                    # Proactive Engagement Analysis (Phase 4.3)
                    proactive_engagement_analysis = comprehensive_context.get('proactive_engagement_analysis')
                    if proactive_engagement_analysis and isinstance(proactive_engagement_analysis, dict):
                        intervention_needed = proactive_engagement_analysis.get('intervention_needed', False)
                        engagement_strategy = proactive_engagement_analysis.get('recommended_strategy')
                        if intervention_needed and engagement_strategy:
                            guidance_parts.append(f"🎯 ENGAGEMENT: Use {engagement_strategy} strategy to enhance conversation quality")
                    
                    # Conversation Analysis with Response Guidance
                    conversation_analysis = comprehensive_context.get('conversation_analysis')
                    if conversation_analysis and isinstance(conversation_analysis, dict):
                        response_guidance = conversation_analysis.get('response_guidance')
                        conversation_mode = conversation_analysis.get('conversation_mode', 'standard')
                        relationship_level = conversation_analysis.get('relationship_level', 'acquaintance')
                        
                        if response_guidance:
                            guidance_parts.append(f"💬 CONVERSATION: Mode={conversation_mode}, Level={relationship_level} - {response_guidance}")
                        else:
                            # Fallback basic guidance
                            guidance_parts.append(f"💬 CONVERSATION: Mode={conversation_mode}, Level={relationship_level} - Respond naturally and authentically")
                    
                    # Human-like Memory Optimization
                    human_like_optimization = comprehensive_context.get('human_like_memory_optimization')
                    if human_like_optimization and isinstance(human_like_optimization, dict):
                        memory_insights = human_like_optimization.get('memory_insights')
                        if memory_insights:
                            guidance_parts.append(f"🧠 MEMORY: {memory_insights}")
                    
                    # Emotional Intelligence Context
                    emotion_analysis = comprehensive_context.get('emotion_analysis')
                    if emotion_analysis and isinstance(emotion_analysis, dict):
                        primary_emotion = emotion_analysis.get('primary_emotion')
                        confidence = emotion_analysis.get('confidence', 0)
                        if primary_emotion and confidence > 0.5:
                            guidance_parts.append(f"🎭 EMOTION: Detected {primary_emotion} (confidence: {confidence:.2f}) - respond with appropriate empathy")
                    
                    # 🎯 ADAPTIVE LEARNING INTELLIGENCE
                    # Inject relationship depth, conversation quality, and confidence metrics
                    relationship_data = comprehensive_context.get('relationship_state')
                    if relationship_data and isinstance(relationship_data, dict):
                        relationship_depth = relationship_data.get('relationship_depth', 'new_connection')
                        trust = relationship_data.get('trust', 0.5)
                        affection = relationship_data.get('affection', 0.5)
                        attunement = relationship_data.get('attunement', 0.5)
                        interactions = relationship_data.get('interaction_count', 0)
                        
                        # Build human-readable relationship guidance
                        depth_descriptions = {
                            'deep_bond': 'You share a deep, established bond - be warm, personal, and deeply attuned',
                            'strong_connection': 'You have a strong connection - be friendly, comfortable, and supportive',
                            'growing_relationship': 'Your relationship is developing - be engaging, open, and attentive',
                            'acquaintance': 'You are becoming acquainted - be welcoming, respectful, and encouraging',
                            'new_connection': 'This is a new connection - be inviting, warm, and establish rapport'
                        }
                        
                        depth_guidance = depth_descriptions.get(relationship_depth, 'Respond authentically')
                        
                        guidance_parts.append(
                            f"💝 RELATIONSHIP: {depth_guidance} "
                            f"(Trust: {trust:.2f}, Affection: {affection:.2f}, Attunement: {attunement:.2f}, "
                            f"Interactions: {interactions})"
                        )
                    
                    confidence_data = comprehensive_context.get('conversation_confidence')
                    if confidence_data and isinstance(confidence_data, dict):
                        overall_conf = confidence_data.get('overall_confidence', 0.7)
                        context_conf = confidence_data.get('context_confidence', 0.7)
                        
                        if overall_conf > 0.8:
                            conf_guidance = "high confidence conversation - feel comfortable being detailed and specific"
                        elif overall_conf > 0.6:
                            conf_guidance = "moderate confidence - balance clarity with openness to exploration"
                        else:
                            conf_guidance = "exploratory conversation - ask clarifying questions and build understanding"
                        
                        guidance_parts.append(
                            f"📊 CONFIDENCE: {conf_guidance} "
                            f"(Overall: {overall_conf:.2f}, Context: {context_conf:.2f})"
                        )
                    
                    # 🎭 SPRINT 4: CHARACTER PERFORMANCE INTELLIGENCE
                    # Adaptive character optimization based on conversation effectiveness
                    character_performance = comprehensive_context.get('character_performance_intelligence')
                    if character_performance and isinstance(character_performance, dict):
                        performance_status = character_performance.get('performance_status', 'unknown')
                        overall_score = character_performance.get('overall_score', 0.5)
                        optimization_opportunities = character_performance.get('optimization_opportunities', [])
                        
                        # Build character optimization guidance
                        if performance_status == 'excellent':
                            perf_guidance = "Your character performance is excellent - maintain your current approach"
                        elif performance_status == 'good':
                            perf_guidance = "Your character performance is good - continue with minor refinements"
                        elif performance_status == 'fair':
                            perf_guidance = "Your character performance needs attention - focus on improvement areas"
                        elif performance_status == 'needs_improvement':
                            perf_guidance = "Your character performance needs significant improvement - adapt your approach"
                        else:
                            perf_guidance = "Character performance analysis in progress"
                        
                        # Add specific optimization opportunities
                        if optimization_opportunities:
                            top_opportunities = optimization_opportunities[:2]  # Use top 2 opportunities
                            optimization_text = ", ".join([opp.get('recommendation', 'optimize approach') for opp in top_opportunities])
                            perf_guidance += f". Focus on: {optimization_text}"
                        
                        guidance_parts.append(
                            f"🎭 CHARACTER: {perf_guidance} "
                            f"(Performance Score: {overall_score:.2f}, Status: {performance_status})"
                        )
                    
                    # 🎯 STEP 7: Intelligent Question Generation - Add curiosity questions
                    try:
                        if self.semantic_router:
                            curiosity_questions = await self.generate_curiosity_questions(
                                user_id=user_id,
                                character_name=character.identity.name.lower().split()[0],
                                semantic_router=self.semantic_router
                            )
                            
                            if curiosity_questions:
                                # Add question generation guidance
                                questions_text = []
                                for q in curiosity_questions[:2]:  # Limit to 2 for prompt space
                                    gap_type = q.get('gap_type', 'unknown')
                                    question = q.get('question', '')
                                    if question:
                                        questions_text.append(f"{question} (exploring {gap_type})")
                                
                                if questions_text:
                                    guidance_parts.append(
                                        f"❓ CURIOSITY: Consider naturally weaving in: {' OR '.join(questions_text[:1])}"
                                    )
                                    logger.info("🎯 QUESTION GENERATION: Added %d curiosity questions to guidance", len(questions_text))
                    except Exception as e:
                        logger.debug("Could not generate curiosity questions: %s", e)
                    
                    if guidance_parts:
                        prompt += f"\n\n🤖 AI INTELLIGENCE GUIDANCE:\n" + "\n".join(f"• {part}" for part in guidance_parts) + "\n"
                        logger.info("🤖 AI INTELLIGENCE: Included comprehensive guidance (%d items)", len(guidance_parts))
                    else:
                        # Fallback if no specific guidance found
                        prompt += f"\n\n🤖 AI INTELLIGENCE GUIDANCE:\n• 💬 CONVERSATION: Mode=standard, Level=acquaintance - Respond naturally and authentically\n"
                        logger.info("🤖 AI INTELLIGENCE: Used fallback guidance")
                else:
                    # Fallback if no comprehensive_context
                    prompt += f"\n\n🤖 AI INTELLIGENCE GUIDANCE:\n• 💬 CONVERSATION: Mode=standard, Level=acquaintance - Respond naturally and authentically\n"
                    logger.info("🤖 AI INTELLIGENCE: Used basic fallback guidance")
                    
            except Exception as e:
                logger.debug("Could not extract AI intelligence guidance: %s", e)
                # Fallback guidance
                prompt += f"\n\n🤖 AI INTELLIGENCE GUIDANCE:\n• 💬 CONVERSATION: Mode=standard, Level=acquaintance - Respond naturally and authentically\n"
                
                # 🔗 PHASE 6: Entity relationship recommendations
                # Detect "similar to" or "like" queries and provide recommendations
                similarity_keywords = ['similar to', 'like', 'related to', 'compared to', 'alternative to']
                if any(keyword in message_content.lower() for keyword in similarity_keywords):
                    # Extract entity name from query (simple pattern matching)
                    import re
                    patterns = [
                        r"similar to (\w+)",
                        r"like (\w+)",
                        r"compared to (\w+)",
                        r"alternative to (\w+)"
                    ]
                    
                    target_entity = None
                    for pattern in patterns:
                        match = re.search(pattern, message_content.lower())
                        if match:
                            target_entity = match.group(1)
                            break
                    
                    if target_entity:
                        # Get related entities via graph traversal
                        related_entities = await self.knowledge_router.get_related_entities(
                            entity_name=target_entity,
                            relationship_type='similar_to',
                            max_hops=2,
                            min_weight=0.3
                        )
                        
                        if related_entities:
                            prompt += f"\n\n🔗 RELATED TO '{target_entity.upper()}':\n"
                            
                            # Group by hop distance
                            direct = [e for e in related_entities if e['hops'] == 1]
                            extended = [e for e in related_entities if e['hops'] == 2]
                            
                            if direct:
                                prompt += f"Direct matches:\n"
                                for entity in direct[:3]:
                                    prompt += f"  • {entity['entity_name']} (relevance: {entity['weight']:.0%})\n"
                            
                            if extended:
                                prompt += f"You might also like:\n"
                                for entity in extended[:3]:
                                    prompt += f"  • {entity['entity_name']} (extended match)\n"
                            
                            prompt += f"\nUse these recommendations naturally in your response, matching {character.identity.name}'s personality."
                            logger.info(f"🔗 RECOMMENDATIONS: Found {len(related_entities)} entities related to '{target_entity}'")
                    
            except Exception as e:
                logger.error(f"❌ KNOWLEDGE: Fact retrieval failed: {e}")
                # Continue without facts - don't break conversation flow

        # Add enhanced emotional intelligence context using Sprint 5 Advanced Emotional Intelligence
        if pipeline_dict:
            emotion_data = pipeline_dict.get('emotion_analysis', {})
            logger.debug(f"🔍 CDL DEBUG: emotion_data type: {type(emotion_data)}, is_dict: {isinstance(emotion_data, dict)}")
            if emotion_data and isinstance(emotion_data, dict):
                primary_emotion = emotion_data.get('primary_emotion', '')
                confidence = emotion_data.get('confidence', 0)
                
                if primary_emotion:
                    # Extract Sprint 5 advanced emotional intelligence data
                    advanced_analysis = emotion_data.get('advanced_analysis', {})
                    logger.debug(f"🔍 CDL DEBUG: advanced_analysis type: {type(advanced_analysis)}, is_dict: {isinstance(advanced_analysis, dict)}")
                    
                    if isinstance(advanced_analysis, dict):
                        secondary_emotions = advanced_analysis.get('secondary_emotions', [])
                        emotional_trajectory = advanced_analysis.get('emotional_trajectory', [])
                        cultural_context = advanced_analysis.get('cultural_context', {})
                    else:
                        logger.warning(f"🚨 CDL WARNING: advanced_analysis is not a dict: {type(advanced_analysis)}")
                        secondary_emotions = []
                        emotional_trajectory = []
                        cultural_context = {}
                    
                    is_multi_modal = emotion_data.get('multi_modal', False)
                    
                    # Build rich emotional context prompt
                    if secondary_emotions and len(secondary_emotions) > 0:
                        secondary_str = ', '.join(secondary_emotions[:2])  # Limit to 2 for clarity
                        prompt += f"\n\n🎭 USER EMOTIONAL STATE: {primary_emotion} with undertones of {secondary_str} (confidence: {confidence:.2f})"
                    else:
                        prompt += f"\n\n🎭 USER EMOTIONAL STATE: {primary_emotion} (confidence: {confidence:.2f})"
                    
                    # Add emotional trajectory context
                    if emotional_trajectory and len(emotional_trajectory) > 0:
                        trajectory_pattern = emotional_trajectory[-1] if emotional_trajectory else 'stable'
                        if trajectory_pattern in ['intensifying', 'escalating']:
                            prompt += f"\n📈 EMOTIONAL TREND: Their emotions are intensifying - respond with extra sensitivity"
                        elif trajectory_pattern in ['calming', 'settling']:
                            prompt += f"\n📉 EMOTIONAL TREND: Their emotions are calming - provide gentle support"
                        elif trajectory_pattern in ['fluctuating', 'mixed']:
                            prompt += f"\n🌊 EMOTIONAL TREND: Complex emotional state - be especially attentive to nuances"
                    
                    # Add cultural context awareness
                    if cultural_context and isinstance(cultural_context, dict):
                        expression_style = cultural_context.get('expression_style', '')
                        if expression_style == 'direct':
                            prompt += f"\n🗺️ CULTURAL CONTEXT: Direct communication style - be clear and straightforward"
                        elif expression_style == 'indirect':
                            prompt += f"\n🗺️ CULTURAL CONTEXT: Indirect communication style - read between the lines"
                    elif cultural_context and isinstance(cultural_context, str):
                        # Handle case where cultural_context is a string (like "western")
                        prompt += f"\n🗺️ CULTURAL CONTEXT: {cultural_context} communication style"
                    
                    # Add multi-modal analysis indicator
                    if is_multi_modal:
                        prompt += f"\n📱 ANALYSIS: Multi-modal emotion detection (text + emoji + patterns) - high accuracy"
                    
                    prompt += f"\nRespond with nuanced empathy matching their emotional complexity and communication style."

        # Add memory context intelligence
        if relevant_memories:
            prompt += f"\n\n🧠 RELEVANT CONVERSATION CONTEXT:\n"
            for i, memory in enumerate(relevant_memories[:7], 1):  # Increased from 3 to 7
                # Handle both dict and object memory formats
                if hasattr(memory, 'content'):
                    content = memory.content[:300]  # Object format
                elif isinstance(memory, dict) and 'content' in memory:
                    content = memory['content'][:300]  # Dict format
                elif isinstance(memory, dict) and 'payload' in memory and isinstance(memory['payload'], dict):
                    # Qdrant format: content might be in payload
                    content = memory['payload'].get('content', str(memory)[:300])
                else:
                    content = str(memory)[:300]  # Fallback
                    
                prompt += f"{i}. {content}{'...' if len(str(memory)) > 300 else ''}\n"

        # 🌟 EPISODIC INTELLIGENCE: Character reflective thoughts based on memorable moments
        try:
            graph_manager = await self._get_graph_manager()
            if graph_manager and hasattr(graph_manager, 'extract_episodic_memories'):
                # Extract memorable moments for character reflection
                episodic_memories = await graph_manager.extract_episodic_memories(
                    character_name=character.identity.name,
                    limit=2,  # Just a few memorable moments
                    min_confidence=0.7,  # High confidence memories
                    min_intensity=0.6   # Emotionally significant moments
                )
                
                if episodic_memories:
                    prompt += f"\n\n✨ CHARACTER EPISODIC MEMORIES (for natural reflection):\n"
                    prompt += f"You remember these emotionally significant moments from past conversations:\n"
                    
                    for i, memory in enumerate(episodic_memories, 1):
                        emotion_context = memory.get('primary_emotion', 'neutral')
                        confidence = memory.get('roberta_confidence', 0.0)
                        intensity = memory.get('emotional_intensity', 0.0)
                        content = memory.get('content', '')[:200]
                        
                        # Add emotional context for character awareness
                        if memory.get('is_multi_emotion', False):
                            mixed_emotions = memory.get('mixed_emotions', [])
                            if mixed_emotions:
                                emotion_context += f" (with {mixed_emotions[0][0]})"
                        
                        prompt += f"{i}. {emotion_context.title()} moment: \"{content}{'...' if len(memory.get('content', '')) > 200 else ''}\"\n"
                        prompt += f"   (Emotional significance: {intensity:.1f}/1.0, Confidence: {confidence:.1f}/1.0)\n"
                    
                    prompt += f"\nYou may naturally reference these memories if relevant to the current conversation.\n"
                    logger.info("✨ EPISODIC INTELLIGENCE: Added %d memorable moments to character prompt", len(episodic_memories))
                else:
                    logger.debug("✨ EPISODIC INTELLIGENCE: No memorable moments found for %s", character.identity.name)
            else:
                logger.debug("✨ EPISODIC INTELLIGENCE: Graph manager not available or missing episodic methods")
        except Exception as e:
            logger.debug("✨ EPISODIC INTELLIGENCE: Failed to extract episodic memories: %s", str(e))

        # Add long-term conversation summary for continuity beyond recent history
        if conversation_summary:
            prompt += f"\n\n📚 CONVERSATION BACKGROUND:\n{conversation_summary}\n"

        # Add recent conversation history
        if conversation_history:
            prompt += f"\n\n💬 RECENT CONVERSATION:\n"
            # REDUCED: Only show last 2-3 messages with shorter truncation to prevent pattern-matching on verbose examples
            # This helps characters follow response length guidelines instead of mimicking long conversation history
            for conv in conversation_history[-3:]:  # Reduced from 8 to 3 messages
                if isinstance(conv, dict):
                    role = conv.get('role', 'user')
                    content = conv.get('content', '')[:150]  # Reduced from 300 to 150 chars to minimize verbose example influence
                    prompt += f"{role.title()}: {content}{'...' if len(conv.get('content', '')) > 150 else ''}\n"

        # 🚨 CRITICAL AI ETHICS LAYER: Physical interaction detection
        if self._detect_physical_interaction_request(message_content):
            allows_full_roleplay = self._check_roleplay_flexibility(character)
            
            if not allows_full_roleplay:
                ai_ethics_guidance = self._get_cdl_roleplay_guidance(character, display_name)
                if ai_ethics_guidance:
                    prompt += f"\n\n{ai_ethics_guidance}"
                    logger.info("🛡️ AI ETHICS: Physical interaction detected, injecting guidance for %s", character.identity.name)
            else:
                logger.info("🎭 ROLEPLAY IMMERSION: %s allows full roleplay - skipping AI ethics layer", character.identity.name)

        # Remove duplicate AI identity and conversation flow sections (moved up earlier)
        
        # 🚨 CRITICAL GUIDELINE OVERRIDE: Position guidelines at END of prompt to override memory patterns
        # LLMs are influenced most by RECENT context (recency bias) - guidelines placed here will
        # override patterns learned from memory examples and conversation history
        # This prevents memory pattern contamination where imported conversations teach bad habits
        response_guidelines = await self._get_response_guidelines(character)
        if response_guidelines:
            # Gentle guideline reminder positioned for maximum influence
            prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ RESPONSE STYLE REMINDER ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

As you respond, keep these character guidelines in mind:

{response_guidelines.strip()}

Remember to stay true to your authentic voice and character.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            logger.info(f"✅ GUIDELINE REMINDER: Injected {len(response_guidelines)} chars at END of prompt")
        else:
            logger.debug("📋 GUIDELINE REMINDER: No guidelines to inject")
        
        prompt += f"\nRespond as {character.identity.name} to {display_name}:"

        return prompt

    async def _apply_unified_fidelity_first_optimization(
        self,
        prompt: str,
        character,
        message_content: str,
        relevant_memories: list,
        conversation_history: list,
        pipeline_result
    ) -> str:
        """📏 Apply unified fidelity-first size management - only optimize if absolutely necessary."""
        
        word_count = len(prompt.split())
        
        if word_count <= self.optimized_builder.max_words:
            logger.info("📏 UNIFIED FULL FIDELITY: %d words (within %d limit) - using complete intelligence", 
                       word_count, self.optimized_builder.max_words)
            
            # Record fidelity metrics for full fidelity case
            self._record_fidelity_optimization_metrics(
                operation="full_fidelity_unified",
                original_word_count=word_count,
                optimized_word_count=word_count,
                optimization_ratio=1.0,  # No optimization applied
                character_preservation_score=1.0,  # Full character context preserved
                context_quality_score=1.0,  # Full context quality preserved
                full_fidelity_used=True,
                intelligent_trimming_applied=False
            )
            
            return prompt
        else:
            logger.warning("📏 UNIFIED OPTIMIZATION TRIGGERED: %d words > %d limit, applying intelligent fidelity-first trimming", 
                       word_count, self.optimized_builder.max_words)
            try:
                # 🚨 CRITICAL FIX: Preserve character identity from original prompt
                # Extract character identity line from the original prompt (first meaningful line)
                character_identity = ""
                prompt_lines = prompt.split('\n')
                for line in prompt_lines:
                    if line.strip() and line.startswith(f"You are {character.identity.name}"):
                        character_identity = line.strip()
                        break
                
                # Convert pipeline_result to dict for compatibility with build_character_prompt
                pipeline_dict = {}
                if pipeline_result and hasattr(pipeline_result, '__dict__'):
                    pipeline_dict = pipeline_result.__dict__
                elif isinstance(pipeline_result, dict):
                    pipeline_dict = pipeline_result
                
                # Use the existing fidelity-first optimizer for intelligent trimming
                optimized_prompt = self.optimized_builder.build_character_prompt(
                    character=character,
                    message_content=message_content,
                    context={
                        'conversation_history': conversation_history,
                        'memories': relevant_memories,
                        'pipeline_result': pipeline_dict,
                        'needs_personality': True,
                        'needs_voice_style': True,
                        'needs_ai_guidance': True,
                        'needs_memory_context': bool(relevant_memories or conversation_history)
                    }
                )
                
                # 🚨 CRITICAL FIX: Ensure character identity is preserved at the start
                if character_identity and not optimized_prompt.startswith(character_identity):
                    # If we extracted a character identity and the optimized prompt doesn't start with it,
                    # prepend it to maintain character identity
                    optimized_prompt = f"{character_identity}\n\n{optimized_prompt}"
                    logger.info("🎭 CHARACTER IDENTITY: Preserved character identity in optimized prompt")
                elif not character_identity:
                    # Fallback: ensure some form of character identity exists
                    identity_check = f"You are {character.identity.name}"
                    if not optimized_prompt.startswith(identity_check):
                        optimized_prompt = f"{identity_check}, a {character.identity.occupation}.\n\n{optimized_prompt}"
                        logger.info("🎭 CHARACTER IDENTITY: Added fallback character identity to optimized prompt")
                
                # Record fidelity metrics for intelligent optimization
                optimized_word_count = len(optimized_prompt.split())
                optimization_ratio = optimized_word_count / word_count if word_count > 0 else 0.0
                
                self._record_fidelity_optimization_metrics(
                    operation="intelligent_optimization",
                    original_word_count=word_count,
                    optimized_word_count=optimized_word_count,
                    optimization_ratio=optimization_ratio,
                    character_preservation_score=0.85,  # High preservation due to intelligent algorithm
                    context_quality_score=0.80,  # Good context quality retained
                    full_fidelity_used=False,
                    intelligent_trimming_applied=True
                )
                
                logger.info("📏 UNIFIED SUCCESS: Intelligent optimization completed")
                return optimized_prompt
            except Exception as e:
                logger.error("Unified optimization failed: %s, using emergency truncation", str(e))
                # Emergency fallback: smart truncation while preserving structure
                words = prompt.split()
                if len(words) > self.optimized_builder.max_words:
                    # Keep first 80% and last 10% to preserve intro and conclusion
                    keep_start = int(self.optimized_builder.max_words * 0.8)
                    keep_end = int(self.optimized_builder.max_words * 0.1)
                    truncated_words = words[:keep_start] + ["...\n\n"] + words[-keep_end:]
                    truncated_prompt = ' '.join(truncated_words)
                    # Ensure character instruction remains
                    if not truncated_prompt.endswith(':'):
                        truncated_prompt += f"\n\nRespond as {character.identity.name}:"
                    
                    # Record fidelity metrics for emergency truncation
                    truncated_word_count = len(truncated_prompt.split())
                    optimization_ratio = truncated_word_count / word_count if word_count > 0 else 0.0
                    
                    self._record_fidelity_optimization_metrics(
                        operation="emergency_truncation",
                        original_word_count=word_count,
                        optimized_word_count=truncated_word_count,
                        optimization_ratio=optimization_ratio,
                        character_preservation_score=0.60,  # Lower preservation due to emergency truncation
                        context_quality_score=0.50,  # Reduced context quality
                        full_fidelity_used=False,
                        intelligent_trimming_applied=False
                    )
                    
                    return truncated_prompt
                return prompt

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
            
            # 🚀 PERFORMANCE: Check cache first
            if (self._cached_character is not None and 
                self._cached_character_bot_name == bot_name):
                logger.debug("🚀 CDL: Using cached character for bot: %s", bot_name)
                return self._cached_character
            
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
            
            # 🚀 PERFORMANCE: Cache the character for future calls
            self._cached_character = character
            self._cached_character_bot_name = bot_name
            
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
            
            # 🎯 GRAPH INTELLIGENCE: Use intent detection and graph queries
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            # Extract relationship info if message seems relationship-focused
            if any(keyword in message_lower for keyword in ['relationship', 'partner', 'dating', 'married', 'family']):
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.FAMILY,
                    limit=3,
                    user_id=user_id
                )
                
                if not result.is_empty():
                    # Format background entries with importance weighting
                    for bg in result.background[:3]:
                        importance = bg.get('importance_level', 5)
                        stars = '⭐' * min(importance, 5)
                        personal_sections.append(f"{stars} {bg['description']}")
                    
                    # Format relationships with strength weighting
                    for rel in result.relationships[:3]:
                        strength = rel.get('relationship_strength', 5)
                        personal_sections.append(f"Relationship: {rel['related_entity']} (strength: {strength}/10) - {rel.get('description', '')}")
            
            # Extract family info if message mentions family
            if any(keyword in message_lower for keyword in ['family', 'parents', 'siblings', 'children', 'mother', 'father']):
                result = await graph_manager.query_character_knowledge(
                    character_name=character.identity.name,
                    query_text=message_content,
                    intent=CharacterKnowledgeIntent.FAMILY,
                    limit=3,
                    user_id=user_id
                )
                
                if not result.is_empty():
                    for bg in result.background:
                        importance = bg.get('importance_level', 5)
                        personal_sections.append(f"Family ({importance}/10 importance): {bg['description']}")
                    
                    # Include family relationships
                    for rel in result.relationships:
                        if any(family_term in rel['related_entity'].lower() for family_term in ['mother', 'father', 'sister', 'brother', 'parent']):
                            personal_sections.append(f"Family: {rel['related_entity']} - {rel.get('description', '')}")
            
            # 🤝 PHASE 2A ENHANCEMENT: Extract relationships if message mentions relationships/connections
            if any(keyword in message_lower for keyword in ['relationship', 'relationships', 'friend', 'friends', 'colleague', 'colleagues', 'partner', 'spouse', 'mentor', 'connection', 'connected', 'know', 'knows']):
                logger.info("📊 GRAPH: Relationship keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['work', 'job', 'career', 'education', 'study', 'university', 'college', 'professional']):
                logger.info("📊 GRAPH: Career keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['hobby', 'hobbies', 'interest', 'interests', 'free time', 'fun', 'enjoy', 'like']):
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
            if any(keyword in message_lower for keyword in ['education', 'school', 'college', 'university', 'degree', 'study', 'studied', 'learning', 'training', 'certification']):
                logger.info("📊 GRAPH: Education keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['skill', 'skills', 'good at', 'expertise', 'expert', 'ability', 'abilities', 'talented', 'proficient', 'capable', 'competent']):
                logger.info("📊 GRAPH: Skills keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['remember', 'memory', 'memories', 'experience', 'experiences', 'happened', 'past', 'story', 'stories', 'recall', 'event']):
                logger.info("📊 GRAPH: Memory keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['about you', 'who are you', 'tell me about yourself', 'your background', 'your story', 'yourself', 'introduce yourself']):
                logger.info("📊 GRAPH: Background keywords detected, querying character knowledge...")
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
            if any(keyword in message_lower for keyword in ['everything', 'anything', 'general', 'overview', 'summary', 'all about', 'comprehensive', 'complete', 'full picture', 'everything about']):
                logger.info("📊 GRAPH: General keywords detected, querying comprehensive character knowledge...")
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
                logger.warning("📊 GRAPH: No graph results found, triggering fallback method")
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
        not ALL modes. This reduces prompt size by ~2000 chars (85% reduction).
        """
        try:
            guidance_parts = []
            
            # Access communication data directly from character object
            if hasattr(character, 'communication'):
                comm = character.communication
                
                # Extract conversation flow guidance from communication object
                if hasattr(comm, 'conversation_flow_guidance'):
                    flow_guidance = comm.conversation_flow_guidance
                    
                    # Platform-specific guidance (Discord) - always include
                    platform_discord = flow_guidance.get('platform_awareness', {}).get('discord', {})
                    if platform_discord:
                        max_length = platform_discord.get('max_response_length', '')
                        if max_length:
                            guidance_parts.append(f"🚨 CRITICAL LENGTH LIMIT: {max_length}")
                        
                        collab_style = platform_discord.get('collaboration_style', '')
                        if collab_style:
                            guidance_parts.append(f"CONVERSATION STYLE: {collab_style}")
                        
                        avoid = platform_discord.get('avoid', '')
                        if avoid:
                            guidance_parts.append(f"❌ NEVER: {avoid}")
                        
                        prefer = platform_discord.get('prefer', '')
                        if prefer:
                            guidance_parts.append(f"✅ ALWAYS: {prefer}")
                    
                    # Flow optimization guidance - always include
                    flow_opt = flow_guidance.get('flow_optimization', {})
                    if flow_opt:
                        auth_engagement = flow_opt.get('character_authentic_engagement', '')
                        if auth_engagement:
                            guidance_parts.append(f"ENGAGEMENT PATTERN: {auth_engagement}")
                        
                        length_mgmt = flow_opt.get('length_management', '')
                        if length_mgmt:
                            guidance_parts.append(f"LENGTH STRATEGY: {length_mgmt}")
                        
                        rhythm = flow_opt.get('conversation_rhythm', '')
                        if rhythm:
                            guidance_parts.append(f"CONVERSATION RHYTHM: {rhythm}")
                    
                    # 🎯 TRIGGER-AWARE: Only inject ACTIVE mode guidance, not ALL modes
                    if active_mode and hasattr(active_mode, 'mode_name'):
                        active_mode_name = active_mode.mode_name
                        
                        # Look for matching mode in flow_guidance
                        mode_data = flow_guidance.get(active_mode_name)
                        
                        if mode_data and isinstance(mode_data, dict):
                            # Extract key mode information
                            energy = mode_data.get('energy', '')
                            approach = mode_data.get('approach', '')
                            
                            # Format mode name for display
                            display_name = active_mode_name.replace('_', ' ').title()
                            
                            if energy or approach:
                                mode_desc = f"🎭 ACTIVE MODE: {display_name}"
                                if energy:
                                    mode_desc += f" ({energy})"
                                if approach:
                                    mode_desc += f": {approach}"
                                guidance_parts.append(mode_desc)
                            
                            # Add specific guidance arrays if present (limit to 2 each)
                            encourage = mode_data.get('encourage', [])
                            if encourage and isinstance(encourage, list):
                                for item in encourage[:2]:
                                    guidance_parts.append(f"  ✅ {item}")
                            
                            avoid = mode_data.get('avoid', [])
                            if avoid and isinstance(avoid, list):
                                for item in avoid[:2]:
                                    guidance_parts.append(f"  ❌ {item}")
            
            # Only add header if we have database-driven guidance
            if guidance_parts:
                guidance_parts.insert(0, "🎯 CONVERSATION FLOW REQUIREMENTS:")
                return "\n".join(guidance_parts)
            
            # No hardcoded fallbacks - let database drive all guidance
            return ""
            
        except Exception as e:
            logger.debug("Error extracting conversation flow guidelines: %s", e)
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
            import asyncpg
            
            # Create database connection
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
            pool = await asyncpg.create_pool(DATABASE_URL)
            
            try:
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
                    logger.warning(f"⚠️ _get_response_guidelines: No guidelines found for bot_name={bot_name}")
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
                
            finally:
                await pool.close()
                
        except Exception as e:
            logger.debug("Could not load response guidelines: %s", e)
            return ""

    async def _build_dynamic_custom_fields(self, full_character_data: dict, character_name: str) -> str:
        """🚀 DYNAMIC FIELD BUILDER: Build prompt sections from all available custom fields"""
        dynamic_sections = []
        
        # Sections that are handled by specialized logic, not dumped as prompt text
        skip_sections = [
            'identity',  # Handled separately as character identity
            'behavioral_triggers',  # Now handled by trigger-based mode controller
            'message_triggers',  # Now handled by trigger-based mode controller
            'interaction_modes'  # Now handled by trigger-based mode controller
        ]
        
        # Process each data section dynamically
        for section_name, section_data in full_character_data.items():
            if section_name in skip_sections:
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
                # Nested dictionary - format as sub-sections
                nested_parts = []
                for sub_key, sub_value in field_value.items():
                    if sub_value:
                        sub_title = sub_key.replace('_', ' ').title()
                        nested_parts.append(f"  • {sub_title}: {sub_value}")
                
                if nested_parts:
                    section_parts.append(f"\n📋 {field_title}:")
                    section_parts.extend(nested_parts)
            
            elif isinstance(field_value, list):
                # List of items
                if field_value:
                    section_parts.append(f"\n📋 {field_title}:")
                    for item in field_value:
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