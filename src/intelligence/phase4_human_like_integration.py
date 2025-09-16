"""
Phase 4: Human-Like Conversation Intelligence Integration

This module provides the highest level of conversational AI by integrating:
- Phase 2: Predictive Emotional Intelligence
- Phase 3: Multi-Dimensional Memory Networks
- Human-Like Conversation Optimization
- Advanced Query Processing

The Phase 4 integration harmonizes all systems to create truly human-like interactions
while maintaining the sophisticated capabilities of existing phases.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..memory.phase3_integration import Phase3MemoryNetworks
from ..utils.enhanced_query_processor import EnhancedQueryProcessor
from ..utils.human_like_llm_processor import HumanLikeLLMProcessor

# Import existing Phase systems
from . import Phase2Integration

logger = logging.getLogger(__name__)


class ConversationMode(Enum):
    """Different modes of conversation processing"""

    HUMAN_LIKE = "human_like"  # Prioritize emotional intelligence and natural flow
    ANALYTICAL = "analytical"  # Prioritize factual accuracy and detailed analysis
    BALANCED = "balanced"  # Balance between human-like and analytical
    ADAPTIVE = "adaptive"  # Automatically adapt based on context


class InteractionType(Enum):
    """Types of user interactions"""

    CASUAL_CHAT = "casual_chat"
    PROBLEM_SOLVING = "problem_solving"
    EMOTIONAL_SUPPORT = "emotional_support"
    INFORMATION_SEEKING = "information_seeking"
    CREATIVE_COLLABORATION = "creative_collaboration"


@dataclass
class Phase4Context:
    """Unified context for Phase 4 processing"""

    user_id: str
    message: str
    conversation_mode: ConversationMode
    interaction_type: InteractionType
    phase2_results: dict[str, Any] | None = None
    phase3_results: dict[str, Any] | None = None
    human_like_results: Any | None = None  # Changed to Any to accept different types
    memory_enhancement_results: dict[str, Any] | None = None
    processing_metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.processing_metadata is None:
            self.processing_metadata = {"phases_executed": [], "performance_metrics": {}}


class Phase4HumanLikeIntegration:
    """
    Phase 4: Ultimate Human-Like Conversation Intelligence

    Integrates all previous phases with human-like optimization to create
    the most natural and emotionally intelligent chatbot experience.
    """

    def __init__(
        self,
        phase2_integration: Phase2Integration | None = None,
        phase3_memory_networks: Phase3MemoryNetworks | None = None,
        memory_manager=None,
        llm_client=None,
        enable_adaptive_mode: bool = True,
        conversation_mode: str = "adaptive",
        memory_optimization: bool = True,
        emotional_resonance: bool = True,
        max_memory_queries: int = 15,
        max_conversation_history: int = 25,
        relationship_tracking: str = "enhanced",
        query_optimization: bool = True,
    ):
        """
        Initialize Phase 4 integration

        Args:
            phase2_integration: Phase 2 emotional intelligence system
            phase3_memory_networks: Phase 3 memory networks system
            memory_manager: Base memory manager
            llm_client: LLM client for processing
            enable_adaptive_mode: Whether to use adaptive conversation modes
            conversation_mode: Default conversation mode for Phase 4
            memory_optimization: Enable memory optimization features
            emotional_resonance: Enable emotional resonance features
            max_memory_queries: Maximum number of memory queries per interaction
            max_conversation_history: Maximum conversation history to maintain
            relationship_tracking: Level of relationship tracking (basic/enhanced)
            query_optimization: Enable query optimization
        """
        self.phase2_integration = phase2_integration
        self.phase3_memory_networks = phase3_memory_networks
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.enable_adaptive_mode = enable_adaptive_mode

        # Store configuration parameters
        self.conversation_mode = conversation_mode
        self.memory_optimization = memory_optimization
        self.emotional_resonance = emotional_resonance
        self.max_memory_queries = max_memory_queries
        self.max_conversation_history = max_conversation_history
        self.relationship_tracking = relationship_tracking
        self.query_optimization = query_optimization

        # Initialize human-like processor if LLM client available
        self.human_like_processor = None
        if llm_client:
            try:
                self.human_like_processor = HumanLikeLLMProcessor(
                    llm_client=llm_client, personality_type="caring_friend"
                )
                logger.info("✅ Human-like LLM processor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize human-like processor: {e}")

        # Initialize enhanced query processor for memory optimization
        self.enhanced_query_processor = None
        if memory_manager:
            try:
                self.enhanced_query_processor = EnhancedQueryProcessor()
                logger.info("✅ Enhanced query processor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced query processor: {e}")

        # Conversation state tracking
        self.conversation_modes = {}  # user_id -> ConversationMode
        self.interaction_history = {}  # user_id -> List[InteractionType]
        self.relationship_depth = {}  # user_id -> relationship level

        logger.info("🤖 Phase 4: Human-Like Integration initialized")

    async def process_comprehensive_message(
        self,
        user_id: str,
        message: str,
        conversation_context: list[dict] | None = None,
        discord_context: dict | None = None,
    ) -> Phase4Context:
        """
        Comprehensive message processing that integrates all phases

        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Full conversation context
            discord_context: Discord-specific context (channel, guild, etc.)

        Returns:
            Phase4Context with all analysis results
        """
        processing_start = datetime.now(UTC)
        logger.debug(f"Starting Phase 4 comprehensive processing for user {user_id}")

        try:
            # Step 1: Determine conversation mode and interaction type
            conversation_mode = await self._determine_conversation_mode(
                user_id, message, conversation_context
            )
            interaction_type = await self._classify_interaction_type(message, conversation_context)

            # Initialize Phase 4 context
            phase4_context = Phase4Context(
                user_id=user_id,
                message=message,
                conversation_mode=conversation_mode,
                interaction_type=interaction_type,
                processing_metadata={
                    "start_time": processing_start,
                    "phases_executed": [],
                    "performance_metrics": {},
                },
            )

            # Step 2: Execute Phase 2 (Emotional Intelligence) if available
            if self.phase2_integration:
                try:
                    logger.debug("Executing Phase 2: Emotional Intelligence Analysis")
                    phase2_start = datetime.now(UTC)

                    phase2_context = {
                        "topic": self._extract_topic_hint(message),
                        "communication_style": "adaptive",
                        "user_id": user_id,
                        "message_length": len(message),
                        "timestamp": processing_start.isoformat(),
                        "interaction_type": interaction_type.value,
                        "conversation_mode": conversation_mode.value,
                    }

                    phase2_results = (
                        await self.phase2_integration.process_message_with_emotional_intelligence(
                            user_id=user_id, message=message, conversation_context=phase2_context
                        )
                    )

                    phase4_context.phase2_results = phase2_results
                    phase4_context.processing_metadata["phases_executed"].append("phase2")
                    phase4_context.processing_metadata["performance_metrics"]["phase2_duration"] = (
                        datetime.now(UTC) - phase2_start
                    ).total_seconds()

                    logger.debug("✅ Phase 2 analysis completed")

                except Exception as e:
                    logger.error(f"Phase 2 processing failed: {e}")
                    phase4_context.phase2_results = None

            # Step 3: Execute Phase 3 (Memory Networks) if available
            if self.phase3_memory_networks and self.memory_manager:
                try:
                    logger.debug("Executing Phase 3: Memory Networks Analysis")
                    phase3_start = datetime.now(UTC)

                    # Trigger memory network analysis for user
                    phase3_results = (
                        await self.phase3_memory_networks.analyze_complete_memory_network(
                            user_id=user_id, memory_manager=self.memory_manager
                        )
                    )

                    phase4_context.phase3_results = phase3_results
                    phase4_context.processing_metadata["phases_executed"].append("phase3")
                    phase4_context.processing_metadata["performance_metrics"]["phase3_duration"] = (
                        datetime.now(UTC) - phase3_start
                    ).total_seconds()

                    logger.debug("✅ Phase 3 analysis completed")

                except Exception as e:
                    logger.error(f"Phase 3 processing failed: {e}")
                    phase4_context.phase3_results = None

            # Step 4: Execute Human-Like Processing
            if self.human_like_processor:
                try:
                    logger.debug("Executing Phase 4: Human-Like Conversation Processing")
                    human_like_start = datetime.now(UTC)

                    # Prepare enhanced context with Phase 2 & 3 results
                    enhanced_context = self._prepare_human_like_context(
                        phase4_context, conversation_context, discord_context
                    )

                    human_like_results = (
                        await self.human_like_processor.process_for_human_conversation(
                            message=message,
                            user_id=user_id,
                            conversation_history=enhanced_context.get("conversation_history", []),
                            relationship_context=enhanced_context.get("relationship_context"),
                            emotional_state=enhanced_context.get("emotional_state"),
                        )
                    )

                    phase4_context.human_like_results = human_like_results
                    phase4_context.processing_metadata["phases_executed"].append("human_like")
                    phase4_context.processing_metadata["performance_metrics"][
                        "human_like_duration"
                    ] = (datetime.now(UTC) - human_like_start).total_seconds()

                    logger.debug("✅ Human-like processing completed")

                except Exception as e:
                    logger.error(f"Human-like processing failed: {e}")
                    phase4_context.human_like_results = None

            # Step 5: Execute Enhanced Memory Query Processing
            if self.enhanced_query_processor:
                try:
                    logger.debug("Executing Enhanced Memory Query Processing")
                    memory_enhancement_start = datetime.now(UTC)

                    # Generate optimized memory queries based on all available context
                    enhanced_queries = await self._generate_enhanced_memory_queries(
                        phase4_context, message
                    )

                    # Process queries and get enhanced memory results
                    memory_enhancement_results = {}
                    for query_type, query_data in enhanced_queries.items():
                        try:
                            query_results = self.enhanced_query_processor.process_enhanced_query(
                                user_id=user_id,
                                original_query=query_data["query"],
                                context=query_data["context"],
                                limit=query_data.get("limit", 10),
                            )
                            memory_enhancement_results[query_type] = query_results
                        except Exception as e:
                            logger.warning(
                                f"Enhanced query processing failed for {query_type}: {e}"
                            )
                            memory_enhancement_results[query_type] = None

                    phase4_context.memory_enhancement_results = memory_enhancement_results
                    phase4_context.processing_metadata["phases_executed"].append(
                        "memory_enhancement"
                    )
                    phase4_context.processing_metadata["performance_metrics"][
                        "memory_enhancement_duration"
                    ] = (datetime.now(UTC) - memory_enhancement_start).total_seconds()

                    logger.debug("✅ Enhanced memory processing completed")

                except Exception as e:
                    logger.error(f"Enhanced memory processing failed: {e}")
                    phase4_context.memory_enhancement_results = None

            # Step 6: Calculate total processing time and update conversation state
            total_duration = (datetime.now(UTC) - processing_start).total_seconds()
            phase4_context.processing_metadata["total_duration"] = total_duration
            phase4_context.processing_metadata["phases_completed"] = len(
                phase4_context.processing_metadata["phases_executed"]
            )

            # Update conversation state for future interactions
            self._update_conversation_state(user_id, phase4_context)

            logger.info(
                f"✅ Phase 4 comprehensive processing completed for user {user_id} "
                f"in {total_duration:.2f}s (phases: {', '.join(phase4_context.processing_metadata['phases_executed'])})"
            )

            return phase4_context

        except Exception as e:
            logger.error(f"Phase 4 comprehensive processing failed for user {user_id}: {e}")
            # Return minimal context with error information
            return Phase4Context(
                user_id=user_id,
                message=message,
                conversation_mode=ConversationMode.BALANCED,
                interaction_type=InteractionType.CASUAL_CHAT,
                processing_metadata={
                    "error": str(e),
                    "phases_executed": [],
                    "total_duration": (datetime.now(UTC) - processing_start).total_seconds(),
                },
            )

    async def _determine_conversation_mode(
        self, user_id: str, message: str, conversation_context: list[dict] | None = None
    ) -> ConversationMode:
        """Determine the optimal conversation mode for this interaction"""

        if not self.enable_adaptive_mode:
            return self.conversation_modes.get(user_id, ConversationMode.BALANCED)

        # Analyze message characteristics
        message_lower = message.lower()

        # Emotional support indicators
        emotional_keywords = [
            "feel",
            "feeling",
            "sad",
            "happy",
            "worried",
            "stressed",
            "excited",
            "anxious",
        ]
        if any(keyword in message_lower for keyword in emotional_keywords):
            return ConversationMode.HUMAN_LIKE

        # Analytical/technical indicators
        technical_keywords = ["how", "what", "why", "explain", "analyze", "calculate", "research"]
        if any(keyword in message_lower for keyword in technical_keywords):
            return ConversationMode.ANALYTICAL

        # Check conversation history for patterns
        if user_id in self.conversation_modes:
            return self.conversation_modes[user_id]

        return ConversationMode.BALANCED

    async def _classify_interaction_type(
        self, message: str, conversation_context: list[dict] | None = None
    ) -> InteractionType:
        """Classify the type of interaction based on message content and context"""

        message_lower = message.lower()

        # Problem solving indicators
        problem_keywords = ["help", "problem", "issue", "stuck", "error", "fix", "solve"]
        if any(keyword in message_lower for keyword in problem_keywords):
            return InteractionType.PROBLEM_SOLVING

        # Emotional support indicators
        emotion_keywords = ["feel", "feeling", "worried", "stressed", "sad", "anxious", "upset"]
        if any(keyword in message_lower for keyword in emotion_keywords):
            return InteractionType.EMOTIONAL_SUPPORT

        # Information seeking indicators
        info_keywords = ["what", "how", "when", "where", "why", "tell me", "explain"]
        if any(keyword in message_lower for keyword in info_keywords):
            return InteractionType.INFORMATION_SEEKING

        # Creative collaboration indicators
        creative_keywords = ["create", "design", "build", "make", "idea", "brainstorm"]
        if any(keyword in message_lower for keyword in creative_keywords):
            return InteractionType.CREATIVE_COLLABORATION

        return InteractionType.CASUAL_CHAT

    def _extract_topic_hint(self, message: str) -> str:
        """Extract a topic hint from the message for Phase 2 context"""
        message_lower = message.lower()

        # Simple topic extraction based on keywords
        if any(word in message_lower for word in ["code", "programming", "software"]):
            return "technology"
        elif any(word in message_lower for word in ["feel", "emotion", "mood"]):
            return "emotional"
        elif any(word in message_lower for word in ["work", "job", "career"]):
            return "professional"
        elif any(word in message_lower for word in ["friend", "relationship", "family"]):
            return "social"
        else:
            return "general"

    def _prepare_human_like_context(
        self,
        phase4_context: Phase4Context,
        conversation_context: list[dict] | None = None,
        discord_context: dict | None = None,
    ) -> dict[str, Any]:
        """Prepare enhanced context for human-like processing"""

        context = {
            "conversation_mode": phase4_context.conversation_mode.value,
            "interaction_type": phase4_context.interaction_type.value,
            "user_id": phase4_context.user_id,
        }

        # Add Phase 2 emotional intelligence insights
        if phase4_context.phase2_results:
            context["emotional_intelligence"] = {
                "mood_assessment": phase4_context.phase2_results.get("mood_assessment"),
                "stress_assessment": phase4_context.phase2_results.get("stress_assessment"),
                "emotional_alerts": phase4_context.phase2_results.get("emotional_alerts"),
                "proactive_support": phase4_context.phase2_results.get("proactive_support"),
            }

        # Add Phase 3 memory network insights
        if phase4_context.phase3_results:
            context["memory_networks"] = {
                "network_insights": phase4_context.phase3_results.get("network_insights"),
                "memory_clusters": phase4_context.phase3_results.get("memory_clusters"),
                "importance_analysis": phase4_context.phase3_results.get("importance_analysis"),
                "pattern_detection": phase4_context.phase3_results.get("pattern_detection"),
            }

        # Add conversation context
        if conversation_context:
            context["conversation_history"] = conversation_context[-10:]  # Last 10 messages

        # Add Discord context
        if discord_context:
            context["discord_context"] = discord_context

        return context

    async def _generate_enhanced_memory_queries(
        self, phase4_context: Phase4Context, original_message: str
    ) -> dict[str, dict[str, Any]]:
        """Generate enhanced memory queries based on comprehensive analysis"""

        enhanced_queries = {}

        # Base query for general memory retrieval
        enhanced_queries["general"] = {
            "query": original_message,
            "context": {
                "interaction_type": phase4_context.interaction_type.value,
                "conversation_mode": phase4_context.conversation_mode.value,
            },
            "limit": 15,
        }

        # Emotional context query if Phase 2 results available
        if phase4_context.phase2_results and phase4_context.phase2_results.get("mood_assessment"):
            mood = phase4_context.phase2_results["mood_assessment"].get("current_mood", "neutral")
            enhanced_queries["emotional"] = {
                "query": f"emotional context mood {mood} feelings",
                "context": {"type": "emotional_memory", "mood": mood},
                "limit": 10,
            }

        # Pattern-based query if Phase 3 results available
        if phase4_context.phase3_results and phase4_context.phase3_results.get("pattern_detection"):
            patterns = phase4_context.phase3_results["pattern_detection"]
            if patterns.get("detected_patterns"):
                pattern_topics = [
                    p.get("pattern_type", "") for p in patterns["detected_patterns"][:3]
                ]
                pattern_query = " ".join(pattern_topics)
                enhanced_queries["patterns"] = {
                    "query": f"conversation patterns {pattern_query}",
                    "context": {"type": "pattern_memory", "patterns": pattern_topics},
                    "limit": 8,
                }

        # Relationship context query
        relationship_level = self.relationship_depth.get(phase4_context.user_id, "new")
        enhanced_queries["relationship"] = {
            "query": f"user relationship personal information {relationship_level}",
            "context": {"type": "relationship_memory", "relationship_level": relationship_level},
            "limit": 12,
        }

        return enhanced_queries

    def _update_conversation_state(self, user_id: str, phase4_context: Phase4Context):
        """Update conversation state for future interactions"""

        # Update conversation mode
        self.conversation_modes[user_id] = phase4_context.conversation_mode

        # Update interaction history
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []
        self.interaction_history[user_id].append(phase4_context.interaction_type)

        # Keep only last 20 interactions to prevent memory bloat
        if len(self.interaction_history[user_id]) > 20:
            self.interaction_history[user_id] = self.interaction_history[user_id][-20:]

        # Update relationship depth based on interaction patterns
        self._update_relationship_depth(user_id, phase4_context)

    def _update_relationship_depth(self, user_id: str, phase4_context: Phase4Context):
        """Update relationship depth based on interaction patterns"""

        current_level = self.relationship_depth.get(user_id, "new")
        interaction_count = len(self.interaction_history.get(user_id, []))

        # Simple relationship progression based on interaction count and types
        if interaction_count < 5:
            new_level = "new"
        elif interaction_count < 15:
            new_level = "developing"
        elif interaction_count < 50:
            new_level = "established"
        else:
            new_level = "deep"

        # Consider emotional support interactions for deeper relationships
        if user_id in self.interaction_history:
            emotional_interactions = sum(
                1
                for interaction in self.interaction_history[user_id]
                if interaction == InteractionType.EMOTIONAL_SUPPORT
            )
            if emotional_interactions >= 3 and new_level in ["developing", "established"]:
                if new_level == "developing":
                    new_level = "established"
                elif new_level == "established":
                    new_level = "deep"

        self.relationship_depth[user_id] = new_level

        if new_level != current_level:
            logger.debug(
                f"Relationship depth updated for user {user_id}: {current_level} -> {new_level}"
            )

    def get_comprehensive_context_for_response(
        self, phase4_context: Phase4Context
    ) -> dict[str, Any]:
        """
        Generate comprehensive context for LLM response generation

        This method combines all Phase results into a unified context that can be used
        to generate the most appropriate and human-like response.
        """

        response_context = {
            "user_id": phase4_context.user_id,
            "conversation_mode": phase4_context.conversation_mode.value,
            "interaction_type": phase4_context.interaction_type.value,
            "relationship_level": self.relationship_depth.get(phase4_context.user_id, "new"),
            "processing_summary": {
                "phases_executed": phase4_context.processing_metadata.get("phases_executed", []),
                "total_duration": phase4_context.processing_metadata.get("total_duration", 0),
                "phases_completed": phase4_context.processing_metadata.get("phases_completed", 0),
            },
        }

        # Add Phase 2 emotional intelligence guidance
        if phase4_context.phase2_results:
            response_context["emotional_guidance"] = {
                "tone_adjustments": [],
                "content_suggestions": [],
                "avoid_topics": [],
                "priority_focus": [],
            }

            # Extract guidance from Phase 2 results
            if "mood_assessment" in phase4_context.phase2_results:
                mood = phase4_context.phase2_results["mood_assessment"]
                response_context["emotional_guidance"]["current_mood"] = mood.get(
                    "current_mood", "neutral"
                )

                # Add mood-specific guidance
                if mood.get("current_mood") in ["sad", "anxious", "stressed"]:
                    response_context["emotional_guidance"]["tone_adjustments"].extend(
                        ["empathetic", "supportive", "gentle"]
                    )
                    response_context["emotional_guidance"]["content_suggestions"].extend(
                        ["offer_support", "validate_feelings", "provide_comfort"]
                    )
                elif mood.get("current_mood") in ["happy", "excited", "positive"]:
                    response_context["emotional_guidance"]["tone_adjustments"].extend(
                        ["enthusiastic", "celebratory", "encouraging"]
                    )

        # Add Phase 3 memory network insights for contextualized responses
        if phase4_context.phase3_results:
            response_context["memory_insights"] = {
                "important_topics": [],
                "relationship_patterns": [],
                "conversation_clusters": [],
            }

            # Extract key insights from Phase 3 results
            if "network_insights" in phase4_context.phase3_results:
                insights = phase4_context.phase3_results["network_insights"]
                response_context["memory_insights"]["network_strength"] = insights.get(
                    "network_strength", 0
                )
                response_context["memory_insights"]["key_topics"] = insights.get(
                    "primary_topics", []
                )

        # Add human-like processing results
        if phase4_context.human_like_results:
            response_context["human_like_insights"] = {
                "conversation_stage": phase4_context.human_like_results.get("conversation_stage"),
                "emotional_resonance": phase4_context.human_like_results.get("emotional_resonance"),
                "personality_adaptation": phase4_context.human_like_results.get(
                    "personality_adaptation"
                ),
                "response_style": phase4_context.human_like_results.get("response_style"),
            }

        # Add enhanced memory query results
        if phase4_context.memory_enhancement_results:
            response_context["enhanced_memory"] = {
                "relevant_contexts": [],
                "emotional_memories": [],
                "pattern_memories": [],
                "relationship_memories": [],
            }

            # Process enhanced memory results
            for query_type, results in phase4_context.memory_enhancement_results.items():
                if results and results.get("relevant_memories"):
                    response_context["enhanced_memory"][f"{query_type}_memories"] = [
                        {
                            "content": mem.get("content", "")[:200],  # Truncated for context
                            "importance": mem.get("importance_score", 0),
                            "timestamp": mem.get("timestamp", ""),
                        }
                        for mem in results["relevant_memories"][:5]  # Top 5 memories per type
                    ]

        return response_context

    async def cleanup(self):
        """Cleanup resources and connections"""
        try:
            if self.human_like_processor:
                await self.human_like_processor.cleanup()

            # Clear conversation state (keep relationship depth for persistence)
            self.conversation_modes.clear()

            logger.info("Phase 4 Human-Like Integration cleanup completed")

        except Exception as e:
            logger.error(f"Error during Phase 4 cleanup: {e}")

    def get_integration_status(self) -> dict[str, Any]:
        """Get the current status of all integrated systems"""
        return {
            "phase4_status": "active",
            "phase2_available": self.phase2_integration is not None,
            "phase3_available": self.phase3_memory_networks is not None,
            "human_like_processor_available": self.human_like_processor is not None,
            "enhanced_query_processor_available": self.enhanced_query_processor is not None,
            "adaptive_mode_enabled": self.enable_adaptive_mode,
            "tracked_users": {
                "conversation_modes": len(self.conversation_modes),
                "interaction_histories": len(self.interaction_history),
                "relationship_depths": len(self.relationship_depth),
            },
            "integration_health": self._check_integration_health(),
        }

    def _check_integration_health(self) -> str:
        """Check the health of all integrated systems"""
        available_systems = 0
        total_systems = 4  # Phase2, Phase3, HumanLike, EnhancedQuery

        if self.phase2_integration:
            available_systems += 1
        if self.phase3_memory_networks:
            available_systems += 1
        if self.human_like_processor:
            available_systems += 1
        if self.enhanced_query_processor:
            available_systems += 1

        health_percentage = (available_systems / total_systems) * 100

        if health_percentage >= 75:
            return "excellent"
        elif health_percentage >= 50:
            return "good"
        elif health_percentage >= 25:
            return "fair"
        else:
            return "poor"
