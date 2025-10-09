"""
Modified version of the message processor with MemoryBoost disabled
"""

async def _retrieve_relevant_memories(self, message_context: MessageContext) -> List[Dict[str, Any]]:
    """Retrieve relevant memories with context-aware filtering."""
    if not self.memory_manager:
        logger.warning("Memory manager not available; skipping memory retrieval.")
        return []

    try:
        # Start timing memory retrieval
        memory_start_time = datetime.now()
        
        # Create platform-agnostic message context classification
        classified_context = self._classify_message_context(message_context)
        logger.debug("Message context classified: %s", classified_context.context_type.value)

        # 🚫 MEMORYBOOST: Completely disabled due to compatibility issues
        logger.info("🚫 MemoryBoost disabled - using standard memory retrieval only")

        # Try optimized memory retrieval as primary path
        if hasattr(self.memory_manager, 'retrieve_relevant_memories_optimized'):
            try:
                query_type = self._classify_query_type(message_context.content)
                user_preferences = self._build_user_preferences(message_context.user_id, classified_context)
                filters = self._build_memory_filters(classified_context)
                
                # Add recency boost and meta-conversation filtering
                filters["prefer_recent_conversation"] = True
                filters["recency_hours"] = 2
                filters["exclude_content_patterns"] = [
                    "your prompt", "your system prompt", "how you're programmed",
                    "your character file", "cdl_ai_integration.py", "fix the bot's",
                    "bot is announcing wrong time", "bot should speak like",
                    "testing bot response", "bot container",
                    "bot's speaking style", "bot's detection"
                ]
                
                relevant_memories = await self.memory_manager.retrieve_relevant_memories_optimized(
                    user_id=message_context.user_id,
                    query=message_context.content,
                    query_type=query_type,
                    user_history=user_preferences,
                    filters=filters,
                    limit=20
                )
                
                # Calculate actual retrieval timing
                memory_end_time = datetime.now()
                retrieval_time_ms = int((memory_end_time - memory_start_time).total_seconds() * 1000)
                
                logger.info("🚀 MEMORY: Optimized retrieval returned %d memories in %dms", len(relevant_memories), retrieval_time_ms)
                
                # Record memory quality metrics to InfluxDB with ACTUAL timing
                if self.fidelity_metrics and relevant_memories:
                    # Calculate average relevance score (if available)
                    relevance_scores = [mem.get('relevance_score', 0.7) for mem in relevant_memories]
                    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.7
                    
                    # Calculate average vector similarity (if available)
                    vector_similarities = [mem.get('vector_similarity', 0.8) for mem in relevant_memories]
                    avg_similarity = sum(vector_similarities) / len(vector_similarities) if vector_similarities else 0.8
                    
                    self.fidelity_metrics.record_memory_quality(
                        user_id=message_context.user_id,
                        operation="optimized_retrieval",
                        relevance_score=avg_relevance,
                        retrieval_time_ms=retrieval_time_ms,  # ACTUAL timing
                        memory_count=len(relevant_memories),
                        vector_similarity=avg_similarity
                    )
                
                return relevant_memories
                
            except (AttributeError, ValueError, TypeError) as e:
                logger.warning("Optimized memory retrieval failed, using fallback: %s", str(e))
        
        # Fallback to context-aware retrieval
        relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
            user_id=message_context.user_id,
            query=message_context.content,
            max_memories=20,
            context=classified_context,
            emotional_context="general conversation"
        )
        
        logger.info("🔍 MEMORY: Retrieved %d memories via context-aware fallback", len(relevant_memories))
        
        # REMOVED: Fake estimated memory metrics for fallback - not useful
        # Fallback doesn't provide real relevance/similarity scores
        
        return relevant_memories
        
    except (AttributeError, ValueError, TypeError) as e:
        logger.error("Memory retrieval failed: %s", str(e))
        return []