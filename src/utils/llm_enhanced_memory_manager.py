"""
LLM Enhanced Memory Manager with Sprint 1, 2, and 3 Integration

Integrates:
- Sprint 1: Emotional intelligence persistence
- Sprint 2: Memory importance patterns and learning  
- Sprint 3: Advanced memory-emotional intelligence integration

Provides enhanced memory operations with emotional context,
importance scoring, and pattern-based learning.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone as tz

# Sprint 1 emotional intelligence imports
try:
    from src.intelligence.emotional_intelligence import PredictiveEmotionalIntelligence
    EMOTIONAL_INTELLIGENCE_AVAILABLE = True
except ImportError:
    EMOTIONAL_INTELLIGENCE_AVAILABLE = False

# Sprint 2 memory importance imports  
try:
    from src.memory.memory_importance_engine import MemoryImportanceEngine
    MEMORY_IMPORTANCE_AVAILABLE = True
except ImportError:
    MEMORY_IMPORTANCE_AVAILABLE = False

# Sprint 3 emotional-memory bridge
try:
    from src.utils.emotional_memory_bridge import EmotionalMemoryBridge
    EMOTIONAL_MEMORY_BRIDGE_AVAILABLE = True
except ImportError:
    EMOTIONAL_MEMORY_BRIDGE_AVAILABLE = False

# Sprint 3 automatic learning hooks
try:
    from src.utils.automatic_pattern_learning_hooks import AutomaticPatternLearningHooks
    AUTOMATIC_LEARNING_HOOKS_AVAILABLE = True
except ImportError:
    AUTOMATIC_LEARNING_HOOKS_AVAILABLE = False

logger = logging.getLogger(__name__)

import logging
from dataclasses import dataclass
from typing import Any

from .enhanced_memory_manager import EnhancedMemoryManager
from .llm_query_processor import HybridQueryProcessor, LLMQueryBreakdown
from ..memory.memory_importance_engine import MemoryImportanceEngine
from ..intelligence.emotional_intelligence import PredictiveEmotionalIntelligence

logger = logging.getLogger(__name__)


@dataclass
class LLMMemoryResult:
    """Result from LLM-enhanced memory retrieval"""

    memories: list[dict[str, Any]]
    query_breakdown: LLMQueryBreakdown
    search_performance: dict[str, Any]
    processing_method: str  # "llm", "hybrid", "fallback"


class LLMEnhancedMemoryManager:
    """
    Memory manager that uses LLM analysis to create optimal search queries
    """

    def __init__(self, base_memory_manager, llm_client, enable_llm_processing: bool = True):
        """
        Initialize LLM-enhanced memory manager with Sprint 1 & 2 persistence integration

        Args:
            base_memory_manager: Base memory manager instance
            llm_client: LLM client for query analysis
            enable_llm_processing: Whether to use LLM processing (can disable for fallback)
        """
        self.base_memory_manager = base_memory_manager
        self.llm_client = llm_client
        self.enable_llm_processing = enable_llm_processing

        # Initialize processors
        self.llm_query_processor = HybridQueryProcessor(
            llm_client=llm_client, enable_llm=enable_llm_processing
        )

        # Sprint 1 & 2 Integration: Initialize persistence engines
        self.memory_importance_engine = MemoryImportanceEngine()
        self.emotional_intelligence = PredictiveEmotionalIntelligence()
        
        # Sprint 3: Emotional-Memory Bridge initialization placeholder
        self.emotional_memory_bridge = None
        
        # Sprint 3: Automatic Pattern Learning Hooks initialization placeholder
        self.automatic_learning_hooks = None
        
        # Note: Persistence will be initialized on first use (lazy loading)
        self.persistence_initialized = False

        # Fallback to enhanced processor if needed
        self.enhanced_manager = EnhancedMemoryManager(base_memory_manager)

        logger.info(
            "LLM-Enhanced Memory Manager initialized with Sprint 1 & 2 persistence - LLM processing: %s",
            enable_llm_processing
        )

    async def _initialize_persistence_systems(self):
        """Initialize Sprint 1 & 2 persistence systems"""
        try:
            # Initialize memory importance persistence
            await self.memory_importance_engine.ensure_persistence_initialized()
            logger.info("Memory importance persistence initialized successfully")
            
            # Initialize emotional intelligence persistence  
            await self.emotional_intelligence.initialize_persistence()
            logger.info("Emotional intelligence persistence initialized successfully")
            
            # Sprint 3: Emotional-Memory Bridge (if available)
            self.emotional_memory_bridge = None
            if (EMOTIONAL_MEMORY_BRIDGE_AVAILABLE and 
                self.emotional_intelligence and 
                self.memory_importance_engine):
                try:
                    from src.utils.emotional_memory_bridge import EmotionalMemoryBridge
                    self.emotional_memory_bridge = EmotionalMemoryBridge(
                        emotional_intelligence=self.emotional_intelligence,
                        memory_importance_engine=self.memory_importance_engine
                    )
                    logger.info("Sprint 3 emotional-memory bridge integration initialized")
                except ImportError:
                    logger.warning("Sprint 3 emotional-memory bridge not available")
            
            # Sprint 3: Automatic Pattern Learning Hooks (if available)
            self.automatic_learning_hooks = None
            if (AUTOMATIC_LEARNING_HOOKS_AVAILABLE and 
                self.memory_importance_engine):
                try:
                    from src.utils.automatic_pattern_learning_hooks import AutomaticPatternLearningHooks
                    self.automatic_learning_hooks = AutomaticPatternLearningHooks(
                        memory_importance_engine=self.memory_importance_engine,
                        emotional_memory_bridge=self.emotional_memory_bridge
                    )
                    logger.info("Sprint 3 automatic pattern learning hooks initialized")
                except ImportError:
                    logger.warning("Sprint 3 automatic learning hooks not available")
            
            self.persistence_initialized = True
            logger.info("LLM Enhanced Memory Manager fully initialized with Sprint 1-3 integration")
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Persistence initialization partially failed: %s - continuing with limited functionality", e)

    async def enhance_memories_with_importance(
        self, 
        user_id: str, 
        memories: list[dict], 
        message: str,
        user_history: list[dict] = None
    ) -> list[dict]:
        """
        Sprint 2 Integration: Enhance memories with learned importance patterns
        
        Args:
            user_id: User identifier
            memories: List of memories to enhance  
            message: Current message for context
            user_history: User conversation history
            
        Returns:
            Enhanced memories with importance scores and pattern-based ranking
        """
        if not memories:
            return memories
            
        user_history = user_history or []
        enhanced_memories = []
        
        # Ensure user has statistics record (required for foreign key constraints)
        await self._ensure_user_statistics(user_id)
        
        for memory in memories:
            try:
                memory_id = memory.get("id", f"temp_{len(enhanced_memories)}")
                
                # Calculate enhanced importance using learned patterns
                importance_score = await self.memory_importance_engine.calculate_memory_importance_with_patterns(
                    memory_id=memory_id,
                    user_id=user_id,
                    memory_data=memory,
                    user_history=user_history,
                    memory_manager=self.base_memory_manager
                )
                
                # Add importance data to memory
                enhanced_memory = memory.copy()
                enhanced_memory.update({
                    "importance_score": importance_score.overall_score,
                    "importance_factors": {
                        "emotional_intensity": importance_score.factor_scores.emotional_intensity,
                        "personal_relevance": importance_score.factor_scores.personal_relevance,
                        "recency": importance_score.factor_scores.recency,
                        "pattern_boost": "pattern_learning_applied" in importance_score.boost_events,
                    },
                    "pattern_enhanced": True,
                })
                
                enhanced_memories.append(enhanced_memory)
                
            except Exception as e:
                logger.warning("Failed to enhance memory %s: %s", memory.get('id', 'unknown'), e)
                # Add original memory without enhancement
                enhanced_memories.append(memory)
        
        # Sort by importance score (highest first)
        enhanced_memories.sort(key=lambda m: m.get("importance_score", 0), reverse=True)
        
        logger.debug("Enhanced %d memories with importance patterns for user %s", len(enhanced_memories), user_id)
        return enhanced_memories

    async def enhance_memories_with_emotional_intelligence(
        self, 
        user_id: str, 
        memories: list[dict], 
        current_message: str
    ) -> list[dict]:
        """
        Sprint 3 Task 3.2: Enhanced memory processing with emotional-memory bridge
        
        Applies emotional intelligence to enhance memory importance scoring
        and learns emotional trigger patterns for future memory enhancement.
        
        Args:
            user_id: User identifier  
            memories: Memories to enhance with emotional context
            current_message: Current user message for emotional context
            
        Returns:
            Memories enhanced with emotional intelligence integration
        """
        if not self.emotional_memory_bridge:
            logger.debug("Emotional-memory bridge not available, using base importance enhancement")
            return await self.enhance_memories_with_importance(user_id, memories, current_message)
            
        try:
            enhanced_memories = []
            
            for memory in memories:
                # Get base importance score from Sprint 2
                base_score = memory.get("importance_score", 0.5)
                
                # Apply emotional-memory bridge enhancement
                emotional_context = await self.emotional_memory_bridge.enhance_memory_with_emotional_context(
                    user_id=user_id,
                    memory_id=memory.get("id", "unknown"),
                    memory_data=memory,
                    current_message=current_message,
                    base_importance_score=base_score
                )
                
                # Update memory with emotional enhancement results
                enhanced_memory = memory.copy()
                enhanced_memory.update({
                    "importance_score": emotional_context.final_importance_score,
                    "emotional_enhancement": {
                        "base_score": emotional_context.base_importance_score,
                        "emotional_boost": emotional_context.emotional_importance_boost,
                        "trigger_match": emotional_context.emotional_trigger_match,
                        "pattern_confidence": emotional_context.emotional_pattern_confidence,
                        "mood_category": emotional_context.mood_category,
                        "stress_level": emotional_context.stress_level,
                        "enhancement_applied": emotional_context.enhancement_applied,
                        "assessment_timestamp": emotional_context.assessment_timestamp.isoformat(),
                    }
                })
                
                enhanced_memories.append(enhanced_memory)
            
            logger.debug("Enhanced %d memories with emotional intelligence integration for user %s", 
                        len(enhanced_memories), user_id)
            
            return enhanced_memories
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Emotional intelligence enhancement failed for user %s: %s", user_id, e)
            # Fallback to Sprint 2 importance enhancement
            return await self.enhance_memories_with_importance(user_id, memories, current_message)

    async def store_memory_with_learning(
        self,
        user_id: str,
        memory_data: Dict[str, Any],
        storage_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Sprint 3 Task 3.3: Store memory with automatic pattern learning
        
        Stores memory and triggers automatic learning hooks to learn
        from storage patterns and improve future memory importance scoring.
        
        Args:
            user_id: User identifier
            memory_data: Memory data to store
            storage_context: Additional context for learning
            
        Returns:
            Stored memory data with any enhancements applied
        """
        if not storage_context:
            storage_context = {}
            
        try:
            # Enhance memory with importance scoring before storage
            if self.memory_importance_engine:
                enhanced_memory = await self.enhance_memories_with_importance(
                    user_id, [memory_data], storage_context.get("trigger_message", "")
                )
                if enhanced_memory:
                    memory_data = enhanced_memory[0]
            
            # Enhance with emotional intelligence if available
            if self.emotional_memory_bridge:
                enhanced_emotional = await self.enhance_memories_with_emotional_intelligence(
                    user_id, [memory_data], storage_context.get("trigger_message", "")
                )
                if enhanced_emotional:
                    memory_data = enhanced_emotional[0]
            
            # Store the memory (delegate to base memory manager)
            stored_memory = memory_data  # In real implementation, would call base_memory_manager.store()
            
            # Trigger automatic learning hooks
            if self.automatic_learning_hooks:
                await self.automatic_learning_hooks.on_memory_stored(
                    user_id=user_id,
                    memory_id=stored_memory.get("id", "unknown"),
                    memory_data=stored_memory,
                    storage_context=storage_context
                )
            
            logger.debug("Memory stored with automatic learning for user %s", user_id)
            return stored_memory
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Memory storage with learning failed for user %s: %s", user_id, e)
            return memory_data  # Return original data as fallback

    async def retrieve_memories_with_learning(
        self,
        user_id: str,
        query: str,
        retrieval_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Sprint 3 Task 3.3: Retrieve memories with automatic pattern learning
        
        Retrieves memories and triggers learning hooks to learn from
        retrieval patterns and user preferences.
        
        Args:
            user_id: User identifier
            query: Search query
            retrieval_context: Additional context for learning
            
        Returns:
            Retrieved memories with learning hooks triggered
        """
        if not retrieval_context:
            retrieval_context = {}
            
        try:
            # Retrieve memories using LLM-enhanced retrieval
            memories = await self.retrieve_memories_with_llm_analysis(
                user_id=user_id,
                query=query,
                context=retrieval_context
            )
            
            # Trigger memory access hooks for each retrieved memory
            if self.automatic_learning_hooks:
                for memory in memories:
                    access_context = {
                        "query_context": query,
                        "relevance_score": memory.get("relevance_score", 0.5),
                        "access_count": memory.get("access_count", 1),
                        **retrieval_context
                    }
                    
                    await self.automatic_learning_hooks.on_memory_accessed(
                        user_id=user_id,
                        memory_id=memory.get("id", "unknown"),
                        memory_data=memory,
                        access_context=access_context
                    )
                
                # Trigger retrieval session learning
                await self.automatic_learning_hooks.on_memory_retrieval_session(
                    user_id=user_id,
                    query=query,
                    retrieved_memories=memories,
                    retrieval_context=retrieval_context
                )
            
            logger.debug("Retrieved %d memories with automatic learning for user %s", 
                        len(memories), user_id)
            return memories
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Memory retrieval with learning failed for user %s: %s", user_id, e)
            # Fallback to base retrieval without learning
            return await self.retrieve_memories_with_llm_analysis(user_id, query, retrieval_context)

    def get_automatic_learning_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about automatic learning activity
        
        Returns:
            Learning statistics and activity information
        """
        if self.automatic_learning_hooks:
            return self.automatic_learning_hooks.get_learning_statistics()
        else:
            return {
                "learning_active": False,
                "total_learning_events": 0,
                "automatic_learning_available": False
            }

    async def _ensure_user_statistics(self, user_id: str):
        """Ensure user has basic statistics record for foreign key constraints"""
        try:
            # Check if user statistics exist
            existing_stats = await self.memory_importance_engine.load_user_memory_statistics(user_id)
            
            if not existing_stats:
                # Create basic user statistics
                basic_stats = {
                    "total_memories": 0,
                    "high_importance_count": 0,
                    "emotional_intensity_weight": 0.30,
                    "personal_relevance_weight": 0.25,
                    "recency_weight": 0.15,
                    "access_frequency_weight": 0.15,
                    "uniqueness_weight": 0.10,
                    "relationship_milestone_weight": 0.05,
                }
                await self.memory_importance_engine.save_user_memory_statistics(user_id, basic_stats)
                logger.debug("Created basic user statistics for %s", user_id)
                
        except Exception as e:
            logger.warning("Failed to ensure user statistics for %s: %s", user_id, e)

    async def add_emotional_context_to_memories(
        self,
        user_id: str, 
        memories: list[dict],
        message: str
    ) -> list[dict]:
        """
        Sprint 1 Integration: Add emotional intelligence context to memories
        
        Args:
            user_id: User identifier
            memories: List of memories to enhance
            message: Current message for emotional context
            
        Returns:
            Memories enhanced with emotional intelligence data
        """
        try:
            # Get emotional assessment for current message
            emotional_assessment = await self.emotional_intelligence.comprehensive_emotional_assessment(
                user_id=user_id,
                current_message=message,
                conversation_context=[]
            )
            
            # Add emotional context to each memory
            for memory in memories:
                memory["emotional_context"] = {
                    "current_emotion": emotional_assessment.current_emotion.value if emotional_assessment.current_emotion else "neutral",
                    "emotional_stability": emotional_assessment.emotional_stability,
                    "support_effectiveness": emotional_assessment.support_effectiveness,
                    "risk_assessment": emotional_assessment.risk_level.value if emotional_assessment.risk_level else "low",
                }
                
            logger.debug(f"Added emotional context to {len(memories)} memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.warning("Failed to add emotional context: %s", e)
            return memories

    async def _get_user_history(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get recent user conversation history for pattern learning"""
        try:
            # Try to get user history from base memory manager
            if hasattr(self.base_memory_manager, 'get_user_memories'):
                user_memories = await self.base_memory_manager.get_user_memories(user_id, limit=limit)
                return user_memories if user_memories else []
            elif hasattr(self.base_memory_manager, 'retrieve_relevant_memories'):
                # Fallback: get recent memories with a broad query
                recent_memories = self.base_memory_manager.retrieve_relevant_memories(
                    user_id=user_id,
                    query="recent conversation",
                    limit=limit
                )
                # Handle both sync and async calls
                if hasattr(recent_memories, '__await__'):
                    recent_memories = await recent_memories
                return recent_memories if recent_memories else []
            else:
                logger.debug("Base memory manager doesn't support history retrieval")
                return []
        except Exception as e:
            logger.warning("Failed to retrieve user history: %s", e)
            return []

    async def retrieve_context_aware_memories_llm(
        self,
        user_id: str,
        message: str,
        context: dict | None = None,
        limit: int = 20,
        conversation_context: str | None = None,
    ) -> LLMMemoryResult:
        """
        Retrieve memories using LLM-powered query analysis

        Args:
            user_id: User identifier
            message: User message to analyze
            context: Additional context information
            limit: Maximum number of memories to retrieve
            conversation_context: Recent conversation context for better analysis

        Returns:
            LLMMemoryResult with retrieved memories and analysis details
        """

        try:
            # Step 1: Use LLM to analyze message and create optimal queries
            query_breakdown = await self.llm_query_processor.process_message(
                message=message, conversation_context=conversation_context
            )

            logger.debug(
                f"LLM query breakdown: {len(query_breakdown.primary_queries)} queries, "
                f"strategy: {query_breakdown.search_strategy}"
            )

            # Step 2: Execute searches using the optimized queries
            all_memories = []
            search_performance = {
                "queries_executed": 0,
                "total_results": 0,
                "unique_memories": 0,
                "processing_method": "llm" if self.enable_llm_processing else "hybrid",
            }

            # Execute each optimized query
            for i, search_query in enumerate(query_breakdown.primary_queries):
                try:
                    # Use base memory manager for actual retrieval
                    query_memories = await self.base_memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query=search_query.query,
                        limit=max(5, limit // len(query_breakdown.primary_queries)),
                    )

                    # Weight the results based on query importance
                    for memory in query_memories:
                        memory_score = memory.get("similarity_score", 0.5)
                        weighted_score = (
                            memory_score * search_query.weight * search_query.confidence
                        )
                        memory["llm_weighted_score"] = weighted_score
                        memory["source_query"] = search_query.query
                        memory["source_query_type"] = search_query.query_type
                        memory["query_reasoning"] = search_query.reasoning

                    all_memories.extend(query_memories)
                    search_performance["queries_executed"] += 1
                    search_performance["total_results"] += len(query_memories)

                    logger.debug(
                        f"Query {i+1} ('{search_query.query}'): {len(query_memories)} memories"
                    )

                except Exception as e:
                    logger.warning(f"Query execution failed for '{search_query.query}': {e}")
                    continue

            # Step 3: Sprint 1 & 2 Integration - Enhance memories with persistence data  
            if not self._persistence_initialized:
                await self._initialize_persistence_systems()
                self._persistence_initialized = True
            
            # Get user history for pattern learning
            user_history = await self._get_user_history(user_id)
            
            # Apply Sprint 2 memory importance enhancement
            enhanced_memories = await self.enhance_memories_with_importance(
                user_id=user_id,
                memories=all_memories,
                message=message,
                user_history=user_history
            )
            
            # Apply Sprint 1 emotional intelligence enhancement  
            emotionally_enhanced = await self.add_emotional_context_to_memories(
                user_id=user_id,
                memories=enhanced_memories,
                message=message
            )
            
            # Step 4: Combine and rank results with enhanced data
            final_memories = self._combine_and_rank_memories(emotionally_enhanced, query_breakdown, limit)

            search_performance["unique_memories"] = len(final_memories)

            # Log performance
            if search_performance["queries_executed"] > 0:
                logger.info(
                    f"LLM memory retrieval: {search_performance['queries_executed']} queries → "
                    f"{search_performance['unique_memories']} unique memories"
                )

            return LLMMemoryResult(
                memories=final_memories,
                query_breakdown=query_breakdown,
                search_performance=search_performance,
                processing_method=search_performance["processing_method"],
            )

        except Exception as e:
            logger.error(f"LLM memory retrieval failed: {e}")
            # Fallback to enhanced memory manager
            return await self._fallback_retrieval(user_id, message, context, limit)

    def _combine_and_rank_memories(
        self, all_memories: list[dict], query_breakdown: LLMQueryBreakdown, limit: int
    ) -> list[dict]:
        """
        Combine memories from multiple queries and rank by relevance
        """

        # Remove duplicates while preserving best scores
        unique_memories = {}

        for memory in all_memories:
            memory_id = memory.get("id") or memory.get("content", "")[:100]

            if memory_id not in unique_memories:
                unique_memories[memory_id] = memory
            else:
                # Keep the version with higher weighted score
                existing_score = unique_memories[memory_id].get("llm_weighted_score", 0)
                new_score = memory.get("llm_weighted_score", 0)

                if new_score > existing_score:
                    # Merge query information
                    existing_memory = unique_memories[memory_id]
                    existing_memory["additional_matches"] = existing_memory.get(
                        "additional_matches", []
                    )
                    existing_memory["additional_matches"].append(
                        {
                            "query": memory.get("source_query"),
                            "type": memory.get("source_query_type"),
                            "score": new_score,
                        }
                    )
                    unique_memories[memory_id] = memory

        # Sort by LLM weighted score, then by original similarity
        ranked_memories = sorted(
            unique_memories.values(),
            key=lambda m: (m.get("llm_weighted_score", 0), m.get("similarity_score", 0)),
            reverse=True,
        )

        # Apply strategic boosting based on search strategy
        if query_breakdown.search_strategy == "specific":
            # Boost exact entity matches
            for memory in ranked_memories:
                if memory.get("source_query_type") == "entity":
                    memory["llm_weighted_score"] *= 1.2

        elif query_breakdown.search_strategy == "contextual":
            # Boost memories that match emotional context
            emotional_context = query_breakdown.emotional_context
            if emotional_context:
                for memory in ranked_memories:
                    memory_content = memory.get("content", "").lower()
                    if any(
                        emotion_word in memory_content
                        for emotion_word in emotional_context.lower().split()
                    ):
                        memory["llm_weighted_score"] *= 1.1

        # Re-sort after boosting
        ranked_memories.sort(key=lambda m: m.get("llm_weighted_score", 0), reverse=True)

        return ranked_memories[:limit]

    async def _fallback_retrieval(
        self, user_id: str, message: str, context: dict | None, limit: int
    ) -> LLMMemoryResult:
        """
        Fallback to enhanced memory manager when LLM processing fails
        """

        logger.warning("Using fallback memory retrieval")

        try:
            # Use enhanced memory manager as fallback
            enhanced_memories = self.enhanced_manager.retrieve_relevant_memories_enhanced(
                user_id=user_id, message=message, context=context, limit=limit
            )

            # Create a basic query breakdown for consistency
            fallback_breakdown = LLMQueryBreakdown(
                primary_queries=[],
                fallback_query=message,
                extracted_entities=[],
                main_topics=[],
                intent_classification="unknown",
                search_strategy="fallback",
            )

            return LLMMemoryResult(
                memories=enhanced_memories,
                query_breakdown=fallback_breakdown,
                search_performance={
                    "queries_executed": 1,
                    "total_results": len(enhanced_memories),
                    "unique_memories": len(enhanced_memories),
                    "processing_method": "fallback",
                },
                processing_method="fallback",
            )

        except Exception as e:
            logger.error(f"Fallback memory retrieval also failed: {e}")

            # Ultimate fallback - return empty result
            return LLMMemoryResult(
                memories=[],
                query_breakdown=LLMQueryBreakdown(
                    primary_queries=[],
                    fallback_query=message,
                    extracted_entities=[],
                    main_topics=[],
                    intent_classification="error",
                ),
                search_performance={
                    "queries_executed": 0,
                    "total_results": 0,
                    "unique_memories": 0,
                    "processing_method": "error",
                },
                processing_method="error",
            )

    # Pass-through methods to maintain compatibility
    def __getattr__(self, name):
        """Pass through any missing methods to the base memory manager"""
        return getattr(self.base_memory_manager, name)

    async def retrieve_context_aware_memories(self, *args, **kwargs):
        """
        Maintain compatibility while providing LLM enhancement option
        """
        # You can toggle between LLM and standard retrieval
        if self.enable_llm_processing:
            result = await self.retrieve_context_aware_memories_llm(*args, **kwargs)
            return result.memories
        else:
            return await self.base_memory_manager.retrieve_context_aware_memories(*args, **kwargs)


class MemorySearchAnalyzer:
    """
    Utility class to analyze and compare memory search performance
    """

    def __init__(self):
        self.search_history = []

    def log_search_performance(self, result: LLMMemoryResult, user_message: str):
        """Log search performance for analysis"""

        performance_data = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "user_message": user_message[:100],  # Truncate for privacy
            "processing_method": result.processing_method,
            "queries_executed": result.search_performance.get("queries_executed", 0),
            "memories_found": len(result.memories),
            "search_strategy": result.query_breakdown.search_strategy,
            "query_types": [q.query_type for q in result.query_breakdown.primary_queries],
            "avg_confidence": sum(q.confidence for q in result.query_breakdown.primary_queries)
            / max(1, len(result.query_breakdown.primary_queries)),
        }

        self.search_history.append(performance_data)

        # Keep only recent history
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get summary of recent search performance"""

        if not self.search_history:
            return {"status": "no_data"}

        recent_searches = self.search_history[-20:]  # Last 20 searches

        return {
            "total_searches": len(recent_searches),
            "avg_memories_found": sum(s["memories_found"] for s in recent_searches)
            / len(recent_searches),
            "processing_methods": {
                method: sum(1 for s in recent_searches if s["processing_method"] == method)
                for method in {s["processing_method"] for s in recent_searches}
            },
            "search_strategies": {
                strategy: sum(1 for s in recent_searches if s["search_strategy"] == strategy)
                for strategy in {s["search_strategy"] for s in recent_searches}
            },
            "avg_queries_per_search": sum(s["queries_executed"] for s in recent_searches)
            / len(recent_searches),
            "avg_confidence": sum(s["avg_confidence"] for s in recent_searches)
            / len(recent_searches),
        }
