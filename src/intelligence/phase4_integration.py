"""
Main Integration Module for Phase 4 Human-Like Intelligence

This module integrates Phase 4 Human-Like Intelligence with the existing bot system,
harmonizing Phase 1, 2, 3 systems with human-like conversation optimization.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

# Import Phase 4 integration
from .phase4_simple_integration import Phase4HumanLikeIntegration, Phase4Context

logger = logging.getLogger(__name__)


class HumanLikeMemoryOptimizer:
    """
    Optimizes memory retrieval to be more human-like and emotionally intelligent
    """

    def __init__(self, phase4_integration: Phase4HumanLikeIntegration):
        self.phase4_integration = phase4_integration

    async def optimize_memory_search(
        self, user_id: str, original_query: str, memory_manager, limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Use Phase 4 intelligence to optimize memory search for human-like results

        Args:
            user_id: User identifier
            original_query: Original user message
            memory_manager: Memory manager instance
            limit: Maximum number of memories to return

        Returns:
            List of optimized memory results
        """
        try:
            # Use enhanced query processing from Phase 4 if available
            if self.phase4_integration.enhanced_query_processor:
                logger.debug(f"Using Phase 4 enhanced query processing for user {user_id}")

                # Process the query to get optimized search terms
                query_result = self.phase4_integration.enhanced_query_processor.process_message(
                    original_query
                )

                # Use the primary queries for memory search
                all_memories = []
                used_memory_ids = set()

                for search_query in query_result.primary_queries[:3]:  # Use top 3 queries
                    try:
                        memories = memory_manager.retrieve_relevant_memories(
                            user_id=user_id,
                            query=search_query.query,
                            limit=limit // len(query_result.primary_queries) + 2,
                        )

                        # Add unique memories with query type metadata
                        for memory in memories:
                            memory_id = memory.get("id", memory.get("memory_id", ""))
                            if memory_id and memory_id not in used_memory_ids:
                                memory["query_type"] = search_query.query_type
                                memory["search_weight"] = search_query.weight
                                all_memories.append(memory)
                                used_memory_ids.add(memory_id)

                    except Exception as e:
                        logger.warning(f"Enhanced query '{search_query.query}' failed: {e}")
                        continue

                # If we didn't get enough memories, use fallback query
                if len(all_memories) < limit and query_result.fallback_query:
                    try:
                        fallback_memories = memory_manager.retrieve_relevant_memories(
                            user_id=user_id,
                            query=query_result.fallback_query,
                            limit=limit - len(all_memories),
                        )

                        for memory in fallback_memories:
                            memory_id = memory.get("id", memory.get("memory_id", ""))
                            if memory_id and memory_id not in used_memory_ids:
                                memory["query_type"] = "fallback"
                                memory["search_weight"] = 0.5
                                all_memories.append(memory)
                                used_memory_ids.add(memory_id)

                    except Exception as e:
                        logger.warning(f"Fallback query failed: {e}")

                # Sort by relevance score and search weight
                all_memories.sort(
                    key=lambda m: (m.get("search_weight", 0.5) * m.get("score", 0.5)), reverse=True
                )

                result_memories = all_memories[:limit]
                logger.debug(
                    f"Phase 4 memory optimization returned {len(result_memories)} memories for user {user_id}"
                )
                return result_memories

            else:
                # Fallback to standard memory retrieval
                logger.debug(
                    f"Phase 4 enhanced query processor not available, using standard retrieval for user {user_id}"
                )
                return memory_manager.retrieve_relevant_memories(
                    user_id=user_id, query=original_query, limit=limit
                )

        except Exception as e:
            logger.error(f"Phase 4 memory optimization failed for user {user_id}: {e}")
            # Fallback to standard memory retrieval
            try:
                return memory_manager.retrieve_relevant_memories(
                    user_id=user_id, query=original_query, limit=limit
                )
            except Exception as fallback_error:
                logger.error(f"Fallback memory retrieval also failed: {fallback_error}")
                return []


def apply_phase4_integration_patch(
    memory_manager,
    phase2_integration=None,
    phase3_memory_networks=None,
    llm_client=None,
    memory_optimization=True,
    emotional_resonance=True,
    adaptive_mode=True,
    max_memory_queries=15,
    max_conversation_history=25,
    relationship_tracking="enhanced",
    query_optimization=True,
    **kwargs,
):
    """
    Apply Phase 4 human-like integration patch to existing memory manager

    This function enhances the existing memory system with Phase 4 capabilities
    while maintaining backward compatibility with the existing codebase.

    Args:
        memory_manager: Existing memory manager to enhance
        phase2_integration: Phase 2 emotional intelligence system
        phase3_memory_networks: Phase 3 memory networks system
        llm_client: LLM client for processing
        memory_optimization: Enable memory optimization features
        emotional_resonance: Enable emotional resonance features
        adaptive_mode: Enable adaptive learning mode
        max_memory_queries: Maximum number of memory queries per interaction
        max_conversation_history: Maximum conversation history to maintain
        relationship_tracking: Level of relationship tracking (basic/enhanced)
        query_optimization: Enable query optimization
        **kwargs: Additional configuration parameters

    Returns:
        Enhanced memory manager with Phase 4 capabilities
    """
    try:
        logger.info("🚀 Applying Phase 4 Human-Like Integration patch...")

        # Initialize Phase 4 integration with configuration
        phase4_integration = Phase4HumanLikeIntegration(
            phase2_integration=phase2_integration,
            phase3_memory_networks=phase3_memory_networks,
            memory_manager=memory_manager,
            llm_client=llm_client,
            enable_adaptive_mode=adaptive_mode,
            memory_optimization=memory_optimization,
            emotional_resonance=emotional_resonance,
            max_memory_queries=max_memory_queries,
            max_conversation_history=max_conversation_history,
            relationship_tracking=relationship_tracking,
            query_optimization=query_optimization,
        )

        # Initialize human-like memory optimizer
        human_like_optimizer = HumanLikeMemoryOptimizer(phase4_integration)

        # Store original method
        original_retrieve_memories = memory_manager.retrieve_relevant_memories

        # Create enhanced retrieve method
        def enhanced_retrieve_relevant_memories(
            user_id: str, query: str, limit: int = 10, **kwargs
        ):
            """Enhanced memory retrieval with Phase 4 human-like optimization"""
            try:
                # Use asyncio to run the async optimization method
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a new task
                    task = asyncio.create_task(
                        human_like_optimizer.optimize_memory_search(
                            user_id, query, memory_manager, limit
                        )
                    )
                    # Note: This approach may need adjustment based on actual async context
                    return task
                else:
                    # If no event loop is running, run the coroutine
                    return loop.run_until_complete(
                        human_like_optimizer.optimize_memory_search(
                            user_id, query, memory_manager, limit
                        )
                    )
            except Exception as e:
                logger.warning(f"Phase 4 optimization failed, using original method: {e}")
                return original_retrieve_memories(user_id, query, limit, **kwargs)

        # Create enhanced async retrieve method
        async def enhanced_retrieve_relevant_memories_async(
            user_id: str, query: str, limit: int = 10, **kwargs
        ):
            """Enhanced async memory retrieval with Phase 4 human-like optimization"""
            try:
                return await human_like_optimizer.optimize_memory_search(
                    user_id, query, memory_manager, limit
                )
            except Exception as e:
                logger.warning(f"Phase 4 optimization failed, using original method: {e}")
                if hasattr(memory_manager, "retrieve_relevant_memories_async"):
                    return await memory_manager.retrieve_relevant_memories_async(
                        user_id, query, limit, **kwargs
                    )
                else:
                    return original_retrieve_memories(user_id, query, limit, **kwargs)

        # Add Phase 4 methods to memory manager
        memory_manager.phase4_integration = phase4_integration
        memory_manager.human_like_optimizer = human_like_optimizer
        memory_manager.retrieve_relevant_memories_phase4 = enhanced_retrieve_relevant_memories_async

        # Add comprehensive message processing method
        async def process_with_phase4_intelligence(
            user_id: str,
            message: str,
            conversation_context: Optional[List[Dict]] = None,
            discord_context: Optional[Dict] = None,
        ) -> Phase4Context:
            """Process message with full Phase 4 intelligence"""
            return await phase4_integration.process_comprehensive_message(
                user_id=user_id,
                message=message,
                conversation_context=conversation_context,
                discord_context=discord_context,
            )

        memory_manager.process_with_phase4_intelligence = process_with_phase4_intelligence

        # Add method to get comprehensive response context
        def get_phase4_response_context(phase4_context: Phase4Context) -> Dict[str, Any]:
            """Get comprehensive context for response generation"""
            return phase4_integration.get_comprehensive_context_for_response(phase4_context)

        memory_manager.get_phase4_response_context = get_phase4_response_context

        # Add Phase 4 status method
        def get_phase4_status() -> Dict[str, Any]:
            """Get Phase 4 integration status"""
            return phase4_integration.get_integration_status()

        memory_manager.get_phase4_status = get_phase4_status

        logger.info("✅ Phase 4 Human-Like Integration patch applied successfully")
        logger.info(
            f"🎯 Available phases: {', '.join(phase4_integration.get_integration_status()['tracked_users'].keys())}"
        )
        logger.info(
            f"🧠 Integration health: {phase4_integration.get_integration_status()['integration_health']}"
        )

        return memory_manager

    except Exception as e:
        logger.error(f"Failed to apply Phase 4 integration patch: {e}")
        logger.warning("Continuing with standard memory manager")
        return memory_manager


def create_phase4_enhanced_system_prompt(
    phase4_context: Phase4Context, base_system_prompt: str, comprehensive_context: Dict[str, Any]
) -> str:
    """
    Create an enhanced system prompt that incorporates Phase 4 intelligence

    Args:
        phase4_context: Phase 4 processing results
        base_system_prompt: Original system prompt
        comprehensive_context: Comprehensive context from Phase 4

    Returns:
        Enhanced system prompt with Phase 4 intelligence
    """
    try:
        enhancements = []

        # Add conversation mode guidance based on interaction type
        interaction = phase4_context.interaction_type.value
        if interaction == "emotional_support":
            enhancements.append(
                "CONVERSATION MODE: Prioritize emotional intelligence, empathy, and natural conversation flow. Respond like a caring, understanding friend."
            )
        elif interaction == "information_seeking":
            enhancements.append(
                "CONVERSATION MODE: Focus on accuracy, detailed analysis, and comprehensive information. Be thorough and precise."
            )
        else:
            enhancements.append(
                "CONVERSATION MODE: Balance emotional intelligence with accuracy. Be both caring and informative."
            )

        # Add interaction type guidance
        if interaction == "emotional_support":
            enhancements.append(
                "INTERACTION TYPE: The user needs emotional support. Be empathetic, validating, and comforting."
            )
        elif interaction == "problem_solving":
            enhancements.append(
                "INTERACTION TYPE: The user needs help solving a problem. Be solution-focused and helpful."
            )
        elif interaction == "information_seeking":
            enhancements.append(
                "INTERACTION TYPE: The user is seeking information. Be clear, accurate, and comprehensive."
            )
        elif interaction == "creative_collaboration":
            enhancements.append(
                "INTERACTION TYPE: The user wants to collaborate creatively. Be imaginative, supportive, and encouraging."
            )

        # Add emotional guidance if available
        if "emotional_guidance" in comprehensive_context:
            emotional = comprehensive_context["emotional_guidance"]
            if emotional.get("current_mood"):
                enhancements.append(
                    f"USER'S CURRENT MOOD: {emotional['current_mood']}. Adjust your tone and approach accordingly."
                )

            if emotional.get("tone_adjustments"):
                enhancements.append(f"TONE ADJUSTMENTS: {', '.join(emotional['tone_adjustments'])}")

        # Add memory insights if available
        if "memory_insights" in comprehensive_context:
            memory = comprehensive_context["memory_insights"]
            if memory.get("key_topics"):
                enhancements.append(
                    f"KEY CONVERSATION TOPICS: {', '.join(memory['key_topics'][:3])}"
                )

        # Add relationship context
        relationship_level = comprehensive_context.get("relationship_level", "new")
        if relationship_level == "new":
            enhancements.append(
                "RELATIONSHIP: This is a new or early interaction. Be welcoming and establish rapport."
            )
        elif relationship_level == "developing":
            enhancements.append(
                "RELATIONSHIP: You're getting to know this user. Build on previous conversations."
            )
        elif relationship_level == "established":
            enhancements.append(
                "RELATIONSHIP: You have an established relationship. Reference shared history and be more personal."
            )
        elif relationship_level == "deep":
            enhancements.append(
                "RELATIONSHIP: You have a deep relationship with this user. Be familiar, caring, and personally invested."
            )

        # Combine enhancements with base prompt
        if enhancements:
            enhanced_prompt = (
                base_system_prompt
                + "\n\n"
                + "PHASE 4 HUMAN-LIKE INTELLIGENCE CONTEXT:\n"
                + "\n".join(f"- {enhancement}" for enhancement in enhancements)
            )
        else:
            enhanced_prompt = base_system_prompt

        return enhanced_prompt

    except Exception as e:
        logger.error(f"Failed to create Phase 4 enhanced system prompt: {e}")
        return base_system_prompt
