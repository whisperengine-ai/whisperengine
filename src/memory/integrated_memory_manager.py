"""
Memory Manager Bridge for Graph-Integrated Emotion System

This bridges the existing memory manager with the graph-integrated emotion manager
to provide comprehensive context awareness while preserving existing functionality.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any
from src.metrics import metrics_collector as metrics
from src.utils.performance_monitor import monitor_performance

from src.graph_database.neo4j_connector import get_neo4j_connector
from src.memory.memory_manager import UserMemoryManager

logger = logging.getLogger(__name__)


class IntegratedMemoryManager:
    """Enhanced memory manager that integrates ChromaDB and graph database"""

    def __init__(
        self,
        memory_manager=None,
        emotion_manager=None,
        enable_graph_sync: bool | None = None,
        llm_client=None,
    ):
        """Initialize integrated memory manager"""

        # Use provided memory manager or create new one with proper local embedding setup
        if memory_manager is None:
            # Initialize with the same local embedding configuration as main system
            self.memory_manager = UserMemoryManager(llm_client=llm_client)
        else:
            self.memory_manager = memory_manager

        self.emotion_manager = emotion_manager

        # Configure graph database integration
        self.enable_graph_sync = enable_graph_sync
        if self.enable_graph_sync is None:
            self.enable_graph_sync = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"

        self._graph_connector = None

        logger.info(
            "Integrated memory manager initialized (graph sync: %s)", self.enable_graph_sync
        )

    # ========================================================================
    # PROXY METHODS - Forward all UserMemoryManager methods and attributes
    # ========================================================================

    def __getattr__(self, name):
        """Proxy all missing attributes to the underlying memory manager"""
        if hasattr(self.memory_manager, name):
            return getattr(self.memory_manager, name)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")

    # Explicit proxy properties for commonly accessed attributes
    @property
    def enable_emotions(self):
        """Check if emotions are enabled"""
        return hasattr(self, "emotion_manager") and self.emotion_manager is not None

    @property
    def enable_auto_facts(self):
        """Proxy to memory manager's enable_auto_facts"""
        return getattr(self.memory_manager, "enable_auto_facts", False)

    @property
    def fact_extractor(self):
        """⚠️ DEPRECATED: Legacy fact extractor property - replaced by Phase 4 Dynamic Personality Profiler"""
        logger.warning(
            "fact_extractor property is deprecated. Phase 4 Dynamic Personality Profiler "
            "now handles conversation analysis automatically in the memory manager."
        )
        return None  # Always return None since fact extraction is handled by Phase 4

    @property
    def enable_graph_memory(self):
        """Alias for enable_graph_sync"""
        return self.enable_graph_sync

    # Explicit proxy methods for core functionality
    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        channel_id: str | None = None,
        pre_analyzed_emotion_data: dict | None = None,
        metadata: dict | None = None,
    ):
        """Proxy to memory manager's store_conversation method"""
        return self.memory_manager.store_conversation(
            user_id,
            user_message,
            bot_response,
            channel_id or "",
            pre_analyzed_emotion_data or {},
            metadata or {},
        )

    def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10):
        """Proxy to memory manager's retrieve_relevant_memories method"""
        return self.memory_manager.retrieve_relevant_memories(user_id, query, limit)

    def store_user_fact(self, user_id: str, fact: str, metadata: dict | None = None):
        """Proxy to memory manager's store_user_fact method"""
        func = getattr(self.memory_manager, "store_user_fact", None)
        if callable(func):
            return func(user_id, fact, str(metadata or {}))
        return None

    def get_user_facts(self, user_id: str, limit: int = 10):
        """Proxy to memory manager's get_user_facts method"""
        # UserMemoryManager doesn't have get_user_facts, return empty list
        return []

    # ========================================================================
    # ENHANCED METHODS - New functionality with graph integration
    # ========================================================================

    def store_conversation_with_full_context(
        self, user_id: str, message: str, response: str, display_name: str | None = None
    ) -> str:
        """Store conversation with full emotion and graph context"""

        try:
            # Process interaction through emotion manager (gets emotion + relationship context)
            if self.emotion_manager:
                profile, emotion_profile = self.emotion_manager.process_interaction_enhanced(
                    user_id, message, display_name
                )
            else:
                profile, emotion_profile = None, {}

            # Store in ChromaDB using existing functionality
            conversation_memory_id = self.store_conversation(user_id, message, response)

            # Legacy fact extraction system has been replaced by Phase 4 Dynamic Personality Profiler
            # which provides superior conversation analysis integrated into the memory manager
            
            # Link memory to graph database if enabled
            if self.enable_graph_memory and conversation_memory_id:
                # Use thread worker pattern consistent with WhisperEngine architecture
                try:
                    import asyncio
                    import threading
                    
                    def run_graph_link():
                        """Run graph linking in background thread"""
                        try:
                            # Create new event loop for the thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Run the async operation
                            loop.run_until_complete(
                                self._link_memory_to_graph(
                                    memory_id=str(conversation_memory_id),
                                    user_id=user_id,
                                    message=message,
                                    response=response,
                                    profile=profile,
                                    emotion_profile=emotion_profile or {},
                                )
                            )
                        except Exception as e:
                            logger.debug(f"Graph linking completed in background: {e}")
                        finally:
                            loop.close()
                    
                    # Schedule in background thread consistent with scatter-gather pattern
                    thread = threading.Thread(target=run_graph_link, daemon=True)
                    thread.start()
                    
                except Exception as e:
                    logger.debug(f"Could not schedule graph linking: {e}")
                    # Continue without graph linking to maintain functionality

            logger.debug("Stored conversation with full context for user %s", user_id)
            return str(conversation_memory_id) if conversation_memory_id else ""

        except (RuntimeError, ValueError) as e:
            logger.error("Error storing conversation with full context: %s", e)
            # Fallback to basic storage
            fallback_result = self.store_conversation(user_id, message, response)
            return str(fallback_result) if fallback_result else ""

    async def _link_memory_to_graph(
        self, memory_id: str, user_id: str, message: str, response: str, profile, emotion_profile
    ):
        """Link memory to graph database with emotion and relationship context"""

        try:
            graph_connector = await get_neo4j_connector()
            if not graph_connector:
                return

            # Create memory node in graph
            summary = f"{message[:80]}..." if len(message) > 80 else message
            importance = self._calculate_memory_importance(message, emotion_profile, profile)

            # Extract topics if emotion manager is available
            topics = []
            if self.emotion_manager:
                try:
                    topics = await self.emotion_manager._extract_topics_from_message(message)
                except (RuntimeError, ValueError) as e:
                    logger.warning("Topic extraction failed: %s", e)

            await graph_connector.create_memory_with_relationships(
                memory_id=memory_id,
                user_id=user_id,
                chromadb_id=memory_id,  # Link to ChromaDB storage
                summary=summary,
                topics=topics,
                emotion_data={
                    "emotion": emotion_profile.detected_emotion.value,
                    "intensity": emotion_profile.intensity,
                    "confidence": emotion_profile.confidence,
                    "triggers": emotion_profile.triggers,
                    "context": f"conversation_at_{profile.relationship_level.value}_level",
                },
                importance=importance,
            )

            logger.debug("Linked memory %s to graph database", memory_id)

        except (RuntimeError, ValueError) as e:
            logger.warning("Failed to link memory to graph: %s", e)

    def _calculate_memory_importance(self, message: str, emotion_profile, user_profile) -> float:
        """Calculate memory importance based on multiple factors"""
        start_ts = datetime.now().timestamp()
        importance = 0.5  # Base importance

        # Emotional intensity increases importance
        importance += getattr(emotion_profile, "intensity", 0.0) * 0.3

        # High confidence emotions are more important
        if emotion_profile and hasattr(emotion_profile, "confidence"):
            importance += emotion_profile.confidence * 0.2

        # Relationship milestones increase importance
        if (
            user_profile
            and hasattr(user_profile, "relationship_level")
            and hasattr(user_profile.relationship_level, "value")
        ):
            if user_profile.relationship_level.value in ["friend", "close_friend"]:
                importance += 0.2

        # Personal sharing increases importance
        personal_indicators = ["my", "i feel", "personal", "secret", "private", "important to me"]
        if any(indicator in message.lower() for indicator in personal_indicators):
            importance += 0.3

        # Questions and help requests are important
        if any(word in message.lower() for word in ["help", "how", "what", "why", "?", "advice"]):
            importance += 0.2

        # Strong emotions are important
        if (
            emotion_profile
            and hasattr(emotion_profile, "detected_emotion")
            and hasattr(emotion_profile.detected_emotion, "value")
        ):
            if emotion_profile.detected_emotion.value in [
                "angry",
                "frustrated",
                "sad",
                "excited",
                "grateful",
            ]:
                importance += 0.2

        # Length can indicate importance (detailed messages)
        if len(message) > 200:
            importance += 0.1

        # Return the calculated importance value
        final_val = min(importance, 1.0)  # Cap at 1.0

        # Metrics: timing + bucket distribution
        if metrics and metrics.metrics_enabled():
            duration = datetime.now().timestamp() - start_ts
            try:
                metrics.record_timing(
                    "memory_importance_calc_seconds",
                    duration,
                    emotion=getattr(
                        getattr(emotion_profile, "detected_emotion", None), "value", "unknown"
                    ),
                    relationship=getattr(
                        getattr(user_profile, "relationship_level", None), "value", "unknown"
                    ),
                )
                bucket = (
                    "high"
                    if final_val >= 0.75
                    else "medium"
                    if final_val >= 0.5
                    else "low"
                    if final_val >= 0.25
                    else "very_low"
                )
                metrics.incr("memory_importance_bucket", bucket=bucket)
            except (ValueError, RuntimeError, TypeError) as metrics_err:
                logger.debug("Memory importance metrics skipped: %s", metrics_err)

        return final_val

    async def get_memories_by_user(self, user_id: str) -> list[dict]:
        """
        Retrieve all memories for a specific user

        Args:
            user_id: User identifier

        Returns:
            List of memory dictionaries
        """
        try:
            # Get all memories from ChromaDB for this user using the collection
            if not hasattr(self.memory_manager, "collection"):
                logger.error("Memory manager has no collection attribute")
                return []

            # Use a safer get approach
            try:
                result = self.memory_manager.collection.get(where={"user_id": user_id})
            except (RuntimeError, ValueError) as e:
                logger.error("Error querying collection: %s", e)
                return []

            # Check if result exists and has expected properties
            if not result or "ids" not in result:
                logger.warning(f"No results found for user {user_id}")
                return []

            # Format memories for consistent processing
            memories = []

            # Process each memory safely
            for i in range(len(result["ids"])):
                memory_id = result["ids"][i]
                try:
                    # Safely access metadatas and documents
                    metadatas = result.get("metadatas", [])
                    metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

                    documents = result.get("documents", [])
                    document = documents[i] if documents and i < len(documents) else ""

                    # Convert metadata from string to dict if needed
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except Exception:
                            metadata = {"error": "Failed to parse metadata"}
                    elif not isinstance(metadata, dict):
                        metadata = {"error": "Invalid metadata type"}

                    # Create formatted memory
                    memory = {
                        "id": memory_id,
                        "memory_id": memory_id,
                        "content": document,
                        "topic": metadata.get("topic", ""),
                        "emotional_context": metadata.get("emotional_context", {}),
                        "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                        "importance_score": metadata.get("importance_score", 0.5),
                        "metadata": metadata,
                    }
                    memories.append(memory)
                except (ValueError, RuntimeError) as e:
                    logger.error("Error formatting memory %s: %s", memory_id, e)

            logger.debug("Retrieved %d memories for user %s", len(memories), user_id)
            return memories

        except (RuntimeError, ValueError) as e:
            logger.error("Error retrieving memories for user %s: %s", user_id, e)
            return []

    @monitor_performance("memory_retrieval", timeout_ms=5000)
    async def retrieve_contextual_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve memories with enhanced context from emotion and graph systems"""
        import time as _time
        _start = _time.perf_counter()
        error_flag = False
        # Get standard ChromaDB memories (existing functionality)
        # NOTE: Uses proxy to memory_manager.retrieve_relevant_memories() which is
        # automatically enhanced via patch system in EnhancedMemoryManager
        chromadb_memories = self.retrieve_relevant_memories(user_id, query, limit)

        # Enhance with graph context if available
        enhanced_memories = []

        if self.enable_graph_memory and self.emotion_manager:
            try:
                # Get emotion context for query
                current_emotion_context = await self.emotion_manager.get_enhanced_emotion_context(
                    user_id, query
                )

                # Get contextual memories from graph
                graph_memories_text = await self.emotion_manager.get_contextual_memories_for_prompt(
                    user_id, query, limit=5
                )

                # Combine contexts
                for memory in chromadb_memories:
                    enhanced_memory = memory.copy()
                    enhanced_memory["emotion_context"] = current_emotion_context
                    enhanced_memory["graph_memories"] = graph_memories_text
                    enhanced_memories.append(enhanced_memory)

                duration = _time.perf_counter() - _start
                try:
                    metrics.record_timing(
                        "memory_retrieval_seconds", duration,
                        mode="graph_enhanced", base=len(chromadb_memories), enhanced=len(enhanced_memories)
                    )
                    metrics.incr("memory_retrieval_requests", mode="graph_enhanced")
                except (ValueError, RuntimeError, TypeError):
                    pass
                return enhanced_memories

            except (RuntimeError, ValueError) as e:
                logger.warning(
                    "Graph memory enhancement failed, using ChromaDB only: %s", e
                )
                error_flag = True

        duration = _time.perf_counter() - _start
        try:
            metrics.record_timing(
                "memory_retrieval_seconds", duration,
                mode="chromadb_only", base=len(chromadb_memories), error=error_flag
            )
            metrics.incr("memory_retrieval_requests", mode="chromadb_only", error=str(error_flag).lower())
        except (ValueError, RuntimeError, TypeError):
            pass
        return chromadb_memories

    def get_comprehensive_user_context(
        self, user_id: str, current_message: str = ""
    ) -> dict[str, Any]:
        """Get comprehensive user context combining all systems"""

        context = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "systems_active": [],
        }

        try:
            # Get emotion manager context (existing + graph enhanced)
            if self.emotion_manager:
                if self.enable_graph_memory:
                    # Use enhanced context
                    emotion_context = asyncio.run(
                        self.emotion_manager.get_enhanced_emotion_context(user_id, current_message)
                    )
                    context["systems_active"].append("graph_enhanced_emotion")
                else:
                    # Use existing context
                    emotion_context = self.emotion_manager.get_emotion_context(user_id)
                    context["systems_active"].append("emotion_manager")

                context["emotion_context"] = emotion_context

                # Get user profile details
                profile = self.emotion_manager.get_or_create_profile(user_id)
                context["relationship_level"] = profile.relationship_level.value
                context["interaction_count"] = profile.interaction_count
                context["current_emotion"] = profile.current_emotion.value
                context["escalation_count"] = profile.escalation_count

        except (RuntimeError, ValueError) as e:
            logger.warning("Failed to get emotion context: %s", e)
            context["emotion_context"] = "Emotion system unavailable"

        try:
            # Get memory system context
            # NOTE: Could potentially use retrieve_contextual_memories() for enhanced context,
            # but that method is async and this method is sync. Uses basic retrieval with
            # automatic enhancement via memory_manager patch system.
            recent_memories = self.retrieve_relevant_memories(
                user_id, current_message or "recent conversation", limit=3
            )
            context["recent_memories"] = [m.get("content", "")[:100] for m in recent_memories]
            context["systems_active"].append("chromadb_memory")

        except (RuntimeError, ValueError) as e:
            logger.warning("Failed to get memory context: %s", e)
            context["recent_memories"] = []

        try:
            # Get facts context if available
            if self.enable_auto_facts:
                recent_facts = self.get_user_facts(user_id, limit=5)
                context["user_facts"] = recent_facts
                context["systems_active"].append("fact_extraction")

        except (RuntimeError, ValueError) as e:
            logger.warning("Failed to get facts context: %s", e)
            context["user_facts"] = []

        try:
            # Get graph insights if available
            if self.enable_graph_memory and self.emotion_manager:
                graph_memories = asyncio.run(
                    self.emotion_manager.get_contextual_memories_for_prompt(
                        user_id, current_message, limit=3
                    )
                )
                if graph_memories:
                    context["graph_insights"] = graph_memories
                    context["systems_active"].append("neo4j_graph")

        except (RuntimeError, ValueError) as e:
            logger.warning("Failed to get graph insights: %s", e)

        return context

    def generate_system_prompt_context(self, user_id: str, current_message: str = "") -> str:
        """Generate context for system prompt using all available systems"""

        try:
            # Get comprehensive context
            context = self.get_comprehensive_user_context(user_id, current_message)

            # Build system prompt context
            prompt_parts = []

            # Add emotion context
            if context.get("emotion_context"):
                prompt_parts.append("=== USER CONTEXT ===")
                prompt_parts.append(context["emotion_context"])

            # Add relationship insights
            relationship_level = context.get("relationship_level", "stranger")
            interaction_count = context.get("interaction_count", 0)

            if relationship_level != "stranger":
                prompt_parts.append("\n=== RELATIONSHIP STATUS ===")
                prompt_parts.append(
                    f"Relationship: {relationship_level.title()} ({interaction_count} interactions)"
                )

                if context.get("escalation_count", 0) > 0:
                    prompt_parts.append(
                        f"⚠️  User has shown {context['escalation_count']} negative emotional episodes"
                    )

            # Add recent memories
            if context.get("recent_memories"):
                prompt_parts.append("\n=== RECENT CONVERSATIONS ===")
                for i, memory in enumerate(context["recent_memories"][:3], 1):
                    prompt_parts.append(f"{i}. {memory}")

            # Add user facts
            if context.get("user_facts"):
                prompt_parts.append("\n=== USER FACTS ===")
                for fact in context["user_facts"][:5]:
                    prompt_parts.append(f"- {fact}")

            # Add graph insights
            if context.get("graph_insights"):
                prompt_parts.append("\n=== CONTEXTUAL INSIGHTS ===")
                prompt_parts.append(context["graph_insights"])

            # Add system status
            active_systems = context.get("systems_active", [])
            if active_systems:
                prompt_parts.append("\n=== ACTIVE SYSTEMS ===")
                prompt_parts.append(f"Using: {', '.join(active_systems)}")

            return "\n".join(prompt_parts)

        except (RuntimeError, ValueError) as e:
            logger.error("Failed to generate system prompt context: %s", e)
            return "Error: Unable to generate user context"

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check of all integrated systems"""

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
        }

        # Check base memory manager
        try:
            self.retrieve_relevant_memories("health_check", "test", limit=1)
            health_status["components"]["chromadb"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["chromadb"] = {"status": "error", "error": str(e)}

        # Check emotion manager
        if self.emotion_manager:
            try:
                emotion_health = await self.emotion_manager.health_check()
                health_status["components"]["emotion_manager"] = emotion_health
            except Exception as e:
                health_status["components"]["emotion_manager"] = {
                    "status": "error",
                    "error": str(e),
                }

        # Legacy fact extraction check - now replaced by Phase 4
        health_status["components"]["fact_extraction"] = {
            "status": "replaced",
            "info": "Legacy fact extraction replaced by Phase 4 Dynamic Personality Profiler",
        }

        # Overall status
        component_statuses = [
            comp.get("status", "unknown") for comp in health_status["components"].values()
        ]
        if "error" in component_statuses:
            health_status["overall_status"] = "degraded"
        elif "unknown" in component_statuses:
            health_status["overall_status"] = "partial"

        return health_status

    # Preserve all existing methods through inheritance
    # This ensures full backward compatibility
