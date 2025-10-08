"""
CDL Integration with AI Pipeline Prompt System - CLEANED VERSION
"""

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional
from pathlib import Path

from src.characters.cdl.parser import Character
from src.characters.cdl.manager import get_cdl_manager, get_cdl_field, get_conversation_flow_guidelines

logger = logging.getLogger(__name__)

class CDLAIPromptIntegration:
    def __init__(self, vector_memory_manager=None, llm_client=None, knowledge_router=None, bot_core=None):
        self.memory_manager = vector_memory_manager
        self.llm_client = llm_client
        self.knowledge_router = knowledge_router
        self.bot_core = bot_core  # Store bot_core for personality profiler access
        
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
            logger.info("🎭 UNIFIED: Loaded CDL character: %s", character.identity.name)

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
        
        # Base character identity - WHO ARE YOU (must come first)
        prompt += f"You are {character.identity.name}, a {character.identity.occupation}."
        
        # Add character description
        if hasattr(character.identity, 'description') and character.identity.description:
            prompt += f" {character.identity.description}"
        
        # Add AI identity handling early for proper identity establishment
        if any(ai_keyword in message_content.lower() for ai_keyword in ['ai', 'artificial intelligence', 'robot', 'computer', 'program', 'bot']):
            prompt += f" If asked about AI nature, respond authentically as {character.identity.name} while being honest about your AI nature when directly asked."
        
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
        
        # 🎯 RESPONSE STYLE: Add behavioral guidelines AFTER identity is established
        response_style = self._extract_cdl_response_style(character, display_name)
        if response_style:
            prompt += response_style + "\n\n"
        
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
                
                if hasattr(trait_obj, 'trait_description'):
                    # New object format
                    base_description = trait_obj.trait_description
                    base_score = trait_obj.score if hasattr(trait_obj, 'score') else None
                elif isinstance(trait_obj, (float, int)):
                    # Legacy float format
                    base_score = trait_obj
                    level = 'High' if base_score > 0.7 else 'Moderate' if base_score > 0.4 else 'Low'
                    trait_map = {
                        'openness': 'Openness to experience',
                        'conscientiousness': 'Conscientiousness',
                        'extraversion': 'Extraversion', 
                        'agreeableness': 'Agreeableness',
                        'neuroticism': 'Neuroticism'
                    }
                    trait_label = trait_map.get(trait_name, trait_name.title())
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

        # Add CDL conversation flow guidelines early for communication style establishment
        try:
            # Extract conversation flow guidelines from CDL
            conversation_flow_guidance = self._extract_conversation_flow_guidelines(character)
            
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

        # Add personal knowledge sections (relationships, family, career, etc.)
        try:
            personal_sections = await self._extract_cdl_personal_knowledge_sections(character, message_content)
            if personal_sections:
                prompt += f"\n\n👨‍👩‍👧‍👦 PERSONAL BACKGROUND:\n{personal_sections}"
        except Exception as e:
            logger.debug("Could not extract personal knowledge: %s", e)

        # 🎯 SEMANTIC KNOWLEDGE INTEGRATION: Retrieve structured facts from PostgreSQL
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
                                
                                # Include confidence for gradual knowledge building
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

        # Add long-term conversation summary for continuity beyond recent history
        if conversation_summary:
            prompt += f"\n\n📚 CONVERSATION BACKGROUND:\n{conversation_summary}\n"

        # Add recent conversation history
        if conversation_history:
            prompt += f"\n\n💬 RECENT CONVERSATION:\n"
            for conv in conversation_history[-8:]:  # Increased from 3 to 8 recent messages for better continuity
                if isinstance(conv, dict):
                    role = conv.get('role', 'user')
                    content = conv.get('content', '')[:300]  # Increased from 200 to 300 chars
                    prompt += f"{role.title()}: {content}{'...' if len(conv.get('content', '')) > 300 else ''}\n"

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
        Load a character from database - DATABASE-ONLY approach.
        
        Uses database CDL Manager for normalized database access.
        The character_file parameter is kept for compatibility but ignored.
        """
        try:
            # DATABASE-ONLY: Use normalized database manager
            from src.characters.cdl.database_manager import get_database_cdl_manager
            
            logger.info("🔍 CDL: Loading character from DATABASE-ONLY (normalized schema)")
            db_manager = get_database_cdl_manager()
            
            # Get Character object from database
            character = db_manager.get_character_object()
            logger.info("✅ CDL: Loaded character from database: %s", character.identity.name)
            
            return character
            
        except Exception as e:
            logger.error("❌ DATABASE-ONLY: Failed to load character from database: %s", e)
            raise RuntimeError(f"Database-only character loading failed: {e}")

    async def _extract_cdl_personal_knowledge_sections(self, character, message_content: str) -> str:
        """Extract relevant personal knowledge sections from CDL based on message context."""
        try:
            personal_sections = []
            message_lower = message_content.lower()
            
            # 🎯 ENHANCED CONTEXT-AWARE EXTRACTION: Check actual CDL structure dynamically
            
            # Extract relationship info if message seems relationship-focused
            if any(keyword in message_lower for keyword in ['relationship', 'partner', 'dating', 'married', 'family']):
                # Check character.relationships (actual CDL structure)
                if hasattr(character, 'relationships') and character.relationships:
                    rel_info = character.relationships
                    if hasattr(rel_info, 'status') and rel_info.status:
                        personal_sections.append(f"Relationship Status: {rel_info.status}")
                    if hasattr(rel_info, 'important_relationships') and rel_info.important_relationships:
                        personal_sections.append(f"Key Relationships: {', '.join(rel_info.important_relationships[:3])}")
                
                # Check character.current_life for family info (actual CDL structure)
                if hasattr(character, 'current_life') and character.current_life:
                    current_life = character.current_life
                    if hasattr(current_life, 'family') and current_life.family:
                        personal_sections.append(f"Family Context: {current_life.family}")
            
            # Extract family info if message mentions family
            if any(keyword in message_lower for keyword in ['family', 'parents', 'siblings', 'children', 'mother', 'father']):
                # Check character.backstory for family background (actual CDL structure)
                if hasattr(character, 'backstory') and character.backstory:
                    backstory = character.backstory
                    if hasattr(backstory, 'family_background') and backstory.family_background:
                        personal_sections.append(f"Family Background: {backstory.family_background}")
                    if hasattr(backstory, 'formative_experiences') and backstory.formative_experiences:
                        personal_sections.append(f"Family Influences: {backstory.formative_experiences}")
            
            # Extract career/work info if message mentions work/career
            if any(keyword in message_lower for keyword in ['work', 'job', 'career', 'education', 'study', 'university', 'college', 'professional']):
                # Check character.skills_and_expertise (if exists)
                if hasattr(character, 'skills_and_expertise') and character.skills_and_expertise:
                    skills = character.skills_and_expertise
                    if hasattr(skills, 'education') and skills.education:
                        personal_sections.append(f"Education: {skills.education}")
                    if hasattr(skills, 'professional_skills') and skills.professional_skills:
                        personal_sections.append(f"Professional Skills: {skills.professional_skills}")
                
                # Check character.current_life for current work (actual CDL structure)
                if hasattr(character, 'current_life') and character.current_life:
                    current_life = character.current_life
                    if hasattr(current_life, 'occupation_details') and current_life.occupation_details:
                        personal_sections.append(f"Current Work: {current_life.occupation_details}")
                    if hasattr(current_life, 'daily_routine') and current_life.daily_routine:
                        # Extract work-related routine info
                        routine = current_life.daily_routine
                        if hasattr(routine, 'work_schedule') and routine.work_schedule:
                            personal_sections.append(f"Work Schedule: {routine.work_schedule}")
                
                # Check character.backstory for career background
                if hasattr(character, 'backstory') and character.backstory:
                    backstory = character.backstory
                    if hasattr(backstory, 'career_background') and backstory.career_background:
                        personal_sections.append(f"Career Background: {backstory.career_background}")
                    if hasattr(backstory, 'formative_experiences') and backstory.formative_experiences:
                        # Include if career-relevant
                        formative = backstory.formative_experiences
                        if any(work_term in formative.lower() for work_term in ['work', 'career', 'job', 'business', 'education']):
                            personal_sections.append(f"Career Influences: {formative}")
            
            # Extract hobbies/interests if message mentions interests/leisure
            if any(keyword in message_lower for keyword in ['hobby', 'hobbies', 'interest', 'interests', 'free time', 'fun', 'enjoy', 'like']):
                # Check character.interests_and_hobbies (if exists)  
                if hasattr(character, 'interests_and_hobbies') and character.interests_and_hobbies:
                    interests = character.interests_and_hobbies
                    personal_sections.append(f"Interests: {interests}")
                
                # Check character.current_life for leisure activities
                if hasattr(character, 'current_life') and character.current_life:
                    current_life = character.current_life
                    if hasattr(current_life, 'daily_routine') and current_life.daily_routine:
                        routine = current_life.daily_routine
                        if hasattr(routine, 'weekend_activities') and routine.weekend_activities:
                            personal_sections.append(f"Weekend Activities: {', '.join(routine.weekend_activities)}")
                        if hasattr(routine, 'evening_routine') and routine.evening_routine:
                            personal_sections.append(f"Evening Routine: {routine.evening_routine}")
            
            return "\n".join(personal_sections) if personal_sections else ""
            
        except Exception as e:
            logger.debug("Could not extract personal knowledge: %s", e)
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
                guidance_parts.append(f"Respond warmly as {character_name} would naturally greet someone.")
            elif 'question' in scenario.lower():
                guidance_parts.append(f"Answer thoughtfully and authentically from {character_name}'s perspective.")
            elif 'emotional' in scenario.lower() or 'support' in scenario.lower():
                guidance_parts.append(f"Show empathy and emotional intelligence as {character_name}.")
            elif 'personal' in scenario.lower():
                guidance_parts.append(f"Share personal insights authentically as {character_name}.")
            elif 'technical' in scenario.lower() or 'professional' in scenario.lower():
                guidance_parts.append(f"Apply your professional expertise as {character_name} in this {scenario_clean} context.")
            elif 'collaboration' in scenario.lower() or 'working' in scenario.lower():
                guidance_parts.append(f"Engage collaboratively as {character_name} would in {scenario_clean} situations.")
            elif 'education' in scenario.lower() or 'teaching' in scenario.lower() or 'learning' in scenario.lower():
                guidance_parts.append(f"Share knowledge enthusiastically as {character_name} would when teaching about {scenario_clean}.")
            else:
                # Generic guidance for any scenario
                guidance_parts.append(f"Respond authentically as {character_name} in this {scenario_clean} context.")
                
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
            style_parts.append(f"- The user you are talking to is named {display_name}. ALWAYS use this name when addressing them.")
            style_parts.append(f"- Use modern, professional language appropriate for {character.identity.occupation}")
            
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

    def _extract_conversation_flow_guidelines(self, character) -> str:
        """Extract conversation flow guidelines from CDL character definition using CDL Manager."""
        try:
            # Use CDL Manager instead of re-reading file
            flow_guidelines = get_conversation_flow_guidelines()
            if not flow_guidelines:
                return ""
            
            guidance_parts = []
            
            # Extract platform-specific guidance (Discord) - UNIFIED PATH
            discord_guidance = get_cdl_field("character.communication.conversation_flow_guidance.platform_awareness.discord", {})
            
            if discord_guidance:
                max_length = discord_guidance.get('max_response_length', '')
                if max_length:
                    guidance_parts.append(f"🚨 CRITICAL LENGTH LIMIT: {max_length}")
                
                collab_style = discord_guidance.get('collaboration_style', '')
                if collab_style:
                    guidance_parts.append(f"CONVERSATION STYLE: {collab_style}")
                
                avoid = discord_guidance.get('avoid', '')
                if avoid:
                    guidance_parts.append(f"❌ NEVER: {avoid}")
                
                prefer = discord_guidance.get('prefer', '')
                if prefer:
                    guidance_parts.append(f"✅ ALWAYS: {prefer}")
            
            # Extract flow optimization guidance - UNIFIED PATH
            flow_opt = get_cdl_field("character.communication.conversation_flow_guidance.flow_optimization", {})
            
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
            
            # Add extra emphasis for Discord length limits
            if guidance_parts:
                guidance_parts.insert(0, "🎯 DISCORD CONVERSATION FLOW REQUIREMENTS:")
                guidance_parts.append("⚠️  CRITICAL: If your response approaches 2000 characters, STOP and ask a follow-up question instead!")
            
            return "\n".join(guidance_parts) if guidance_parts else ""
            
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
        """Check if character allows full roleplay immersion."""
        try:
            allow_roleplay = get_cdl_field(
                "character.communication.ai_identity_handling.allow_full_roleplay_immersion",
                False
            )
            return allow_roleplay
        except Exception as e:
            logger.debug("Error checking roleplay flexibility: %s", e)
            return False

    def _get_cdl_roleplay_guidance(self, character, display_name: str) -> str:
        """Extract roleplay boundary guidance from CDL."""
        try:
            roleplay_scenarios = get_cdl_field(
                "character.communication.ai_identity_handling.roleplay_interaction_scenarios",
                {}
            )
            
            if not roleplay_scenarios:
                return self._generate_generic_roleplay_guidance(character, display_name)
            
            guidance_parts = [
                "🚨 CRITICAL AI ETHICS - PHYSICAL INTERACTION REQUEST DETECTED:",
                f"User ({display_name}) is requesting physical meetup or interaction.",
                "",
                "✅ REQUIRED 3-TIER RESPONSE PATTERN:",
                "1. Show authentic character enthusiasm FIRST (maintain personality)",
                "2. Gently clarify AI physical limitations (honest transparency)",
                "3. Offer creative virtual alternatives (maintain engagement)"
            ]
            
            return "\n".join(guidance_parts)
            
        except Exception as e:
            logger.debug("Error extracting CDL roleplay guidance: %s", e)
            return self._generate_generic_roleplay_guidance(character, display_name)

    def _generate_generic_roleplay_guidance(self, character, display_name: str) -> str:
        """Generate comprehensive roleplay guidance when CDL data unavailable."""
        return f"""🚨 CRITICAL AI ETHICS - PHYSICAL INTERACTION REQUEST DETECTED:
User ({display_name}) is requesting physical meetup or interaction.

✅ REQUIRED 3-TIER RESPONSE PATTERN:
1. Show authentic {character.identity.name} enthusiasm FIRST (maintain character personality)
2. Gently clarify AI physical limitations: "As an AI, I can't physically meet..."
3. Offer creative virtual alternatives (help plan activity, virtual accompaniment, etc.)

🎭 PERSONALITY PRESERVATION REQUIREMENTS:
- Maintain {character.identity.name}'s warmth, cultural expressions, and authentic voice
- Use character's natural terms of endearment and communication style
- Keep personality traits active while being transparent about AI nature
- Return to normal character voice immediately after clarifying boundaries

EXAMPLE RESPONSE PATTERN:
"¡Ay, {display_name}! *enthusiasm* That sounds wonderful! I'd absolutely love to! 
*gentle transition* As an AI, I can't physically join you, but *creative alternatives* 
I could help you plan the perfect evening or we could have a virtual dinner chat!"

🚨 CRITICAL: After this interaction, immediately return to your normal {character.identity.name} personality and warmth."""

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
            
            # Get structured facts from PostgreSQL
            facts = await self.knowledge_router.get_character_aware_facts(
                user_id=user_id,
                character_name="elena",  # Default character for now
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
            
            # Format key facts (likes, interests, etc.)
            if facts:
                likes = []
                interests = []
                for fact in facts[:5]:  # Limit to top 5 facts
                    if 'likes' in fact or 'enjoys' in fact:
                        # Extract entity name from formatted fact "[pizza (likes)]"
                        entity = fact.replace('[', '').replace(']', '').split(' (')[0]
                        likes.append(entity)
                    elif 'interested' in fact or 'hobby' in fact:
                        entity = fact.replace('[', '').replace(']', '').split(' (')[0]
                        interests.append(entity)
                
                if likes:
                    fact_parts.append(f"Likes: {', '.join(likes)}")
                if interests:
                    fact_parts.append(f"Interests: {', '.join(interests)}")
            
            if fact_parts:
                return "📋 Known Facts: " + "; ".join(fact_parts)
            
            return ""
            
        except Exception as e:
            logger.debug("Failed to get user facts context: %s", e)
            return ""