"""
Enhanced Memory Manager with Optimized Query Processing

This module extends the existing memory manager to use optimized queries
for better semantic search and memory retrieval.
"""

import logging
from typing import Any

from .enhanced_query_processor import EnhancedQueryProcessor, QueryResult

logger = logging.getLogger(__name__)


class EnhancedMemoryManager:
    """
    Enhanced memory manager that uses optimized query processing
    for better memory retrieval and reduced "forgetting" issues.
    """

    def __init__(self, base_memory_manager):
        """
        Initialize with base memory manager

        Args:
            base_memory_manager: The existing memory manager instance
        """
        self.base_memory_manager = base_memory_manager
        self.query_processor = EnhancedQueryProcessor()

        # Configuration for multi-query search
        self.max_queries_per_search = 3  # Limit to avoid overwhelming the search
        self.min_query_weight = 0.5  # Minimum weight threshold for queries
        self.combine_results = True  # Whether to combine results from multiple queries

        logger.info("Enhanced memory manager initialized with optimized query processing")

    def retrieve_relevant_memories_enhanced(
        self, user_id: str, message: str, limit: int = 10, context: Any | None = None
    ) -> list[dict]:
        """
        Retrieve relevant memories using enhanced query processing

        Args:
            user_id: User ID
            message: Raw user message
            limit: Maximum number of memories to retrieve
            context: Optional context object for context-aware retrieval

        Returns:
            List of relevant memories with enhanced scoring
        """
        try:
            # Process the message to get optimized queries
            query_result = self.query_processor.process_message(message)
            search_strategies = self.query_processor.get_search_strategies(query_result)

            # Log the optimization for debugging
            logger.debug(f"Enhanced query processing for user {user_id}:")
            logger.debug(f"  Original message: '{message}'")
            logger.debug(f"  Extracted entities: {query_result.extracted_entities}")
            logger.debug(f"  Intent: {query_result.intent_classification}")
            logger.debug(f"  Generated {len(search_strategies)} search strategies")

            if self.combine_results:
                return self._retrieve_with_combined_queries(
                    user_id, search_strategies, limit, context, query_result
                )
            else:
                return self._retrieve_with_sequential_queries(
                    user_id, search_strategies, limit, context, query_result
                )

        except Exception as e:
            logger.error(f"Error in enhanced memory retrieval: {e}")
            # Fallback to original method
            logger.info("Falling back to original memory retrieval method")
            return self._fallback_retrieve(user_id, message, limit, context)

    def _retrieve_with_combined_queries(
        self,
        user_id: str,
        search_strategies: list[tuple[str, float]],
        limit: int,
        context: Any | None,
        query_result: QueryResult,
    ) -> list[dict]:
        """
        Retrieve memories using multiple queries and combine results with weighted scoring
        """
        all_memories = {}  # Dict to avoid duplicates, keyed by memory ID
        query_count = 0

        # Use top queries above the weight threshold
        for query, weight in search_strategies:
            if weight < self.min_query_weight or query_count >= self.max_queries_per_search:
                break

            try:
                # Retrieve memories for this specific query
                if hasattr(self.base_memory_manager, "retrieve_context_aware_memories") and context:
                    memories = self.base_memory_manager.retrieve_context_aware_memories(
                        user_id,
                        query,
                        context,
                        limit=limit * 2,  # Get more to allow for combination
                    )
                else:
                    memories = self.base_memory_manager.retrieve_relevant_memories(
                        user_id, query, limit=limit * 2
                    )

                # Process memories with weighted scoring
                for memory in memories:
                    memory_id = memory.get("id", str(hash(memory.get("content", ""))))

                    if memory_id in all_memories:
                        # Memory already found - boost its score
                        existing_score = all_memories[memory_id].get("enhanced_score", 0)
                        boost = weight * 0.5  # Boost for multiple query matches
                        all_memories[memory_id]["enhanced_score"] = existing_score + boost
                        all_memories[memory_id]["query_matches"] += 1
                    else:
                        # New memory - add with weighted score
                        memory_copy = memory.copy()
                        base_score = memory.get("relevance_score", 0.5)
                        memory_copy["enhanced_score"] = base_score * weight
                        memory_copy["query_matches"] = 1
                        memory_copy["matching_query"] = query
                        memory_copy["query_weight"] = weight
                        all_memories[memory_id] = memory_copy

                query_count += 1
                logger.debug(
                    f"Query '{query}' (weight: {weight}) returned {len(memories)} memories"
                )

            except Exception as e:
                logger.warning(f"Error retrieving memories for query '{query}': {e}")
                continue

        # Convert back to list and sort by enhanced score
        combined_memories = list(all_memories.values())
        combined_memories.sort(key=lambda x: x.get("enhanced_score", 0), reverse=True)

        # Apply additional relevance boosting
        self._apply_relevance_boosting(combined_memories, query_result)

        # Re-sort after boosting
        combined_memories.sort(key=lambda x: x.get("enhanced_score", 0), reverse=True)

        # Log results for debugging
        logger.debug(f"Combined search returned {len(combined_memories)} unique memories")
        if combined_memories:
            top_memory = combined_memories[0]
            logger.debug(
                f"Top result: score={top_memory.get('enhanced_score', 0):.3f}, "
                f"matches={top_memory.get('query_matches', 0)}, "
                f"query='{top_memory.get('matching_query', 'unknown')}'"
            )

        return combined_memories[:limit]

    def _retrieve_with_sequential_queries(
        self,
        user_id: str,
        search_strategies: list[tuple[str, float]],
        limit: int,
        context: Any | None,
        query_result: QueryResult,
    ) -> list[dict]:
        """
        Retrieve memories using queries sequentially until limit is reached
        """
        all_memories = []
        seen_ids = set()

        for query, weight in search_strategies:
            if len(all_memories) >= limit or weight < self.min_query_weight:
                break

            try:
                remaining_limit = limit - len(all_memories)

                if hasattr(self.base_memory_manager, "retrieve_context_aware_memories") and context:
                    memories = self.base_memory_manager.retrieve_context_aware_memories(
                        user_id, query, context, limit=remaining_limit
                    )
                else:
                    memories = self.base_memory_manager.retrieve_relevant_memories(
                        user_id, query, limit=remaining_limit
                    )

                # Add new memories (avoid duplicates)
                for memory in memories:
                    memory_id = memory.get("id", str(hash(memory.get("content", ""))))
                    if memory_id not in seen_ids:
                        memory_copy = memory.copy()
                        memory_copy["enhanced_score"] = memory.get("relevance_score", 0.5) * weight
                        memory_copy["matching_query"] = query
                        memory_copy["query_weight"] = weight
                        all_memories.append(memory_copy)
                        seen_ids.add(memory_id)

                logger.debug(
                    f"Query '{query}' added {len([m for m in memories if m.get('id') not in seen_ids])} new memories"
                )

            except Exception as e:
                logger.warning(f"Error retrieving memories for query '{query}': {e}")
                continue

        # Apply relevance boosting
        self._apply_relevance_boosting(all_memories, query_result)

        # Sort by enhanced score
        all_memories.sort(key=lambda x: x.get("enhanced_score", 0), reverse=True)

        return all_memories[:limit]

    def _apply_relevance_boosting(self, memories: list[dict], query_result: QueryResult):
        """
        Apply additional relevance boosting based on query analysis
        """
        for memory in memories:
            metadata = memory.get("metadata", {})

            # Boost memories that match extracted entities
            for entity in query_result.extracted_entities:
                content = memory.get("content", "").lower()
                if entity.lower() in content:
                    memory["enhanced_score"] = memory.get("enhanced_score", 0) + 0.1

            # Boost memories that match intent
            if query_result.intent_classification != "general":
                intent_indicators = {
                    "question": ["question", "ask", "wondering"],
                    "help_request": ["help", "advice", "suggest"],
                    "problem": ["problem", "issue", "trouble"],
                    "sharing": ["went", "did", "happened"],
                    "preference": ["love", "like", "prefer", "think"],
                }

                if query_result.intent_classification in intent_indicators:
                    content = memory.get("content", "").lower()
                    for indicator in intent_indicators[query_result.intent_classification]:
                        if indicator in content:
                            memory["enhanced_score"] = memory.get("enhanced_score", 0) + 0.1
                            break

            # Boost memories with emotional context match
            if query_result.emotional_context:
                content = memory.get("content", "").lower()
                emotion_words = {
                    "positive": ["happy", "great", "awesome", "love", "excited"],
                    "negative": ["sad", "upset", "angry", "stressed", "worried"],
                    "neutral": ["thinking", "wondering", "considering"],
                }

                if query_result.emotional_context in emotion_words:
                    for word in emotion_words[query_result.emotional_context]:
                        if word in content:
                            memory["enhanced_score"] = memory.get("enhanced_score", 0) + 0.15
                            break

            # Boost recent memories slightly
            timestamp = metadata.get("timestamp", "")
            if timestamp:
                try:

                    # Simple recency boost (this could be more sophisticated)
                    memory["enhanced_score"] = memory.get("enhanced_score", 0) + 0.05
                except:
                    pass

    def _fallback_retrieve(
        self, user_id: str, message: str, limit: int, context: Any | None
    ) -> list[dict]:
        """
        Fallback to original memory retrieval method
        """
        try:
            if hasattr(self.base_memory_manager, "retrieve_context_aware_memories") and context:
                return self.base_memory_manager.retrieve_context_aware_memories(
                    user_id, message, context, limit
                )
            else:
                return self.base_memory_manager.retrieve_relevant_memories(user_id, message, limit)
        except Exception as e:
            logger.error(f"Fallback memory retrieval also failed: {e}")
            return []

    # Pass through other methods to base manager
    def store_conversation(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.store_conversation(*args, **kwargs)

    def store_user_fact(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.store_user_fact(*args, **kwargs)

    def store_global_fact(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.store_global_fact(*args, **kwargs)

    def get_emotion_context(self, *args, **kwargs):
        """Pass through to base manager"""
        if hasattr(self.base_memory_manager, "get_emotion_context"):
            return self.base_memory_manager.get_emotion_context(*args, **kwargs)
        return ""

    def classify_discord_context(self, *args, **kwargs):
        """Pass through to base manager"""
        if hasattr(self.base_memory_manager, "classify_discord_context"):
            return self.base_memory_manager.classify_discord_context(*args, **kwargs)
        return None

    def delete_specific_memory(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.delete_specific_memory(*args, **kwargs)

    def delete_user_memories(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.delete_user_memories(*args, **kwargs)

    def delete_global_fact(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.delete_global_fact(*args, **kwargs)

    def get_all_global_facts(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.get_all_global_facts(*args, **kwargs)

    def retrieve_relevant_global_facts(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.retrieve_relevant_global_facts(*args, **kwargs)

    def get_collection_stats(self, *args, **kwargs):
        """Pass through to base manager"""
        return self.base_memory_manager.get_collection_stats(*args, **kwargs)

    @property
    def collection(self):
        """Pass through collection property"""
        return self.base_memory_manager.collection

    def __getattr__(self, name):
        """Pass through any other method calls to base manager"""
        return getattr(self.base_memory_manager, name)

    def retrieve_context_aware_memories(
        self, user_id: str, query: str = None, message: str = None, 
        current_query: str = None, context: Any = None, limit: int = 10, 
        max_memories: int = None, **kwargs
    ) -> list[dict]:
        """
        Enhanced version of context-aware memory retrieval with flexible API compatibility
        
        Supports multiple parameter naming conventions:
        - query: Standard parameter name
        - message: Legacy parameter name  
        - current_query: Hierarchical adapter parameter name
        
        This replaces the original method with our enhanced query processing
        """
        # Handle flexible parameter naming for API compatibility
        actual_query = query or message or current_query
        if not actual_query:
            raise ValueError("Must provide either 'query', 'message', or 'current_query' parameter")
            
        # Use max_memories if provided, otherwise use limit
        actual_limit = max_memories or limit
        
        return self.retrieve_relevant_memories_enhanced(user_id, actual_query, actual_limit, context)

    def retrieve_relevant_memories(self, user_id: str, message: str, limit: int = 10) -> list[dict]:
        """
        Enhanced version of relevant memory retrieval

        This replaces the original method with our enhanced query processing
        """
        return self.retrieve_relevant_memories_enhanced(user_id, message, limit, None)


def create_enhanced_memory_manager(base_memory_manager):
    """
    Factory function to create an enhanced memory manager

    Args:
        base_memory_manager: Existing memory manager instance

    Returns:
        EnhancedMemoryManager instance
    """
    return EnhancedMemoryManager(base_memory_manager)
