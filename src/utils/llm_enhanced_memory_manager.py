"""
LLM-Enhanced Memory Manager

This module integrates LLM-powered query processing with the existing
memory system for even better topic recall and contextual awareness.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .enhanced_memory_manager import EnhancedMemoryManager
from .llm_query_processor import HybridQueryProcessor, LLMQueryBreakdown

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
        Initialize LLM-enhanced memory manager

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

        # Fallback to enhanced processor if needed
        self.enhanced_manager = EnhancedMemoryManager(base_memory_manager)

        logger.info(
            f"LLM-Enhanced Memory Manager initialized - LLM processing: {enable_llm_processing}"
        )

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

            # Step 3: Combine and rank results
            final_memories = self._combine_and_rank_memories(all_memories, query_breakdown, limit)

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
