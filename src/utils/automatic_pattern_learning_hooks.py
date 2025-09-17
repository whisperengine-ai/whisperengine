"""
Sprint 3 Task 3.3: Automatic Pattern Learning Hooks

Creates seamless background learning that automatically improves 
memory importance and emotional patterns as users interact with 
the memory system. Implements hooks for memory storage, access, 
and retrieval operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone as tz
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LearningEvent:
    """Represents a learning event for pattern improvement"""
    
    event_type: str  # "memory_stored", "memory_accessed", "memory_retrieved"
    user_id: str
    memory_id: str
    memory_content: str
    context_data: Dict[str, Any]
    importance_score: float
    emotional_context: Optional[Dict[str, Any]]
    timestamp: datetime
    learning_confidence: float


class AutomaticPatternLearningHooks:
    """
    Automatic pattern learning hooks for memory operations
    
    Provides seamless background learning that improves memory
    importance patterns and emotional triggers based on user
    interactions with the memory system.
    """
    
    def __init__(self, memory_importance_engine, emotional_memory_bridge=None):
        """
        Initialize automatic learning hooks
        
        Args:
            memory_importance_engine: Memory importance engine for pattern learning
            emotional_memory_bridge: Optional emotional-memory bridge for emotional learning
        """
        self.memory_importance_engine = memory_importance_engine
        self.emotional_memory_bridge = emotional_memory_bridge
        
        # Learning configuration
        self.learning_config = {
            "min_importance_threshold": 0.6,  # Only learn from important memories
            "access_frequency_weight": 0.3,   # Weight for memory access frequency
            "recency_weight": 0.2,            # Weight for recent interactions
            "emotional_significance_weight": 0.4,  # Weight for emotional context
            "pattern_update_threshold": 0.1,  # Minimum change to update patterns
            "max_learning_events_per_session": 50,  # Prevent excessive learning
        }
        
        # Track learning events for analysis
        self.learning_events = []
        self.session_learning_count = 0
        
        logger.info("Automatic Pattern Learning Hooks initialized for Sprint 3 Task 3.3")

    async def on_memory_stored(
        self,
        user_id: str,
        memory_id: str,
        memory_data: Dict[str, Any],
        storage_context: Dict[str, Any]
    ):
        """
        Hook called when a memory is stored
        
        Learns from new memory patterns and updates importance patterns
        based on content, context, and emotional significance.
        """
        try:
            if self.session_learning_count >= self.learning_config["max_learning_events_per_session"]:
                return
                
            # Extract learning signals from storage event
            importance_score = memory_data.get("importance_score", 0.5)
            content = memory_data.get("content", "")
            
            # Only learn from significant memories
            if importance_score < self.learning_config["min_importance_threshold"]:
                return
                
            # Create learning event
            learning_event = LearningEvent(
                event_type="memory_stored",
                user_id=user_id,
                memory_id=memory_id,
                memory_content=content,
                context_data=storage_context,
                importance_score=importance_score,
                emotional_context=memory_data.get("emotional_enhancement"),
                timestamp=datetime.now(tz.utc),
                learning_confidence=self._calculate_learning_confidence(memory_data, storage_context)
            )
            
            # Apply learning from storage event
            await self._learn_from_storage_event(learning_event)
            
            # Track event
            self.learning_events.append(learning_event)
            self.session_learning_count += 1
            
            logger.debug("Learned from memory storage: user=%s, importance=%.3f", 
                        user_id, importance_score)
            
        except (ValueError, KeyError) as e:
            logger.warning("Error in memory storage learning hook: %s", e)

    async def on_memory_accessed(
        self,
        user_id: str,
        memory_id: str,
        memory_data: Dict[str, Any],
        access_context: Dict[str, Any]
    ):
        """
        Hook called when a memory is accessed/retrieved
        
        Learns from memory access patterns to understand which
        memories are most valuable and relevant to users.
        """
        try:
            if self.session_learning_count >= self.learning_config["max_learning_events_per_session"]:
                return
                
            # Extract access signals
            access_frequency = access_context.get("access_count", 1)
            query_relevance = access_context.get("relevance_score", 0.5)
            importance_score = memory_data.get("importance_score", 0.5)
            
            # Calculate access-based importance boost
            access_boost = self._calculate_access_importance_boost(
                access_frequency, query_relevance, importance_score
            )
            
            # Create learning event
            learning_event = LearningEvent(
                event_type="memory_accessed",
                user_id=user_id,
                memory_id=memory_id,
                memory_content=memory_data.get("content", ""),
                context_data=access_context,
                importance_score=importance_score + access_boost,
                emotional_context=memory_data.get("emotional_enhancement"),
                timestamp=datetime.now(tz.utc),
                learning_confidence=self._calculate_access_confidence(access_context)
            )
            
            # Apply learning from access event
            await self._learn_from_access_event(learning_event)
            
            # Track event
            self.learning_events.append(learning_event)
            self.session_learning_count += 1
            
            logger.debug("Learned from memory access: user=%s, access_count=%d, boost=%.3f", 
                        user_id, access_frequency, access_boost)
            
        except (ValueError, KeyError) as e:
            logger.warning("Error in memory access learning hook: %s", e)

    async def on_memory_retrieval_session(
        self,
        user_id: str,
        query: str,
        retrieved_memories: List[Dict[str, Any]],
        retrieval_context: Dict[str, Any]
    ):
        """
        Hook called after a memory retrieval session
        
        Learns from retrieval patterns to understand user preferences,
        query patterns, and memory relevance relationships.
        """
        try:
            if self.session_learning_count >= self.learning_config["max_learning_events_per_session"]:
                return
                
            # Analyze retrieval session for learning opportunities
            session_insights = self._analyze_retrieval_session(
                query, retrieved_memories, retrieval_context
            )
            
            # Learn from high-relevance memories
            for memory in retrieved_memories:
                relevance_score = memory.get("relevance_score", 0.0)
                
                if relevance_score > 0.7:  # High relevance threshold
                    learning_event = LearningEvent(
                        event_type="memory_retrieved",
                        user_id=user_id,
                        memory_id=memory.get("id", "unknown"),
                        memory_content=memory.get("content", ""),
                        context_data={
                            "query": query,
                            "relevance_score": relevance_score,
                            "session_insights": session_insights,
                            **retrieval_context
                        },
                        importance_score=memory.get("importance_score", 0.5),
                        emotional_context=memory.get("emotional_enhancement"),
                        timestamp=datetime.now(tz.utc),
                        learning_confidence=relevance_score
                    )
                    
                    # Apply learning from retrieval event
                    await self._learn_from_retrieval_event(learning_event)
                    
                    # Track event
                    self.learning_events.append(learning_event)
                    self.session_learning_count += 1
            
            logger.debug("Learned from retrieval session: user=%s, query='%s', memories=%d", 
                        user_id, query[:50], len(retrieved_memories))
            
        except (ValueError, KeyError) as e:
            logger.warning("Error in memory retrieval learning hook: %s", e)

    async def _learn_from_storage_event(self, event: LearningEvent):
        """Learn patterns from memory storage event"""
        try:
            # Extract keywords and topics from new content
            content_keywords = await self._extract_content_keywords(event.memory_content)
            
            # Learn topic importance patterns
            if content_keywords and event.importance_score > 0.6:
                await self._update_topic_importance_patterns(
                    event.user_id, content_keywords, event.importance_score, event.learning_confidence
                )
            
            # Learn emotional patterns if available
            if event.emotional_context and self.emotional_memory_bridge:
                await self._update_emotional_storage_patterns(event)
                
        except (ValueError, AttributeError) as e:
            logger.warning("Error learning from storage event: %s", e)

    async def _learn_from_access_event(self, event: LearningEvent):
        """Learn patterns from memory access event"""
        try:
            # Learn access frequency patterns
            access_count = event.context_data.get("access_count", 1)
            
            if access_count > 3:  # Frequently accessed memories are important
                content_keywords = await self._extract_content_keywords(event.memory_content)
                
                if content_keywords:
                    # Boost importance patterns for frequently accessed content
                    await self._update_access_frequency_patterns(
                        event.user_id, content_keywords, access_count, event.learning_confidence
                    )
            
            # Learn query-content relationship patterns if available in context
            query_context = event.context_data.get("query_context")
            if query_context:
                # Simple query context learning (can be enhanced)
                logger.debug("Query context available for learning: user=%s", event.user_id)
                
        except (ValueError, AttributeError) as e:
            logger.warning("Error learning from access event: %s", e)

    async def _learn_from_retrieval_event(self, event: LearningEvent):
        """Learn patterns from memory retrieval event"""
        try:
            query = event.context_data.get("query", "")
            relevance_score = event.context_data.get("relevance_score", 0.0)
            
            if query and relevance_score > 0.7:
                # Extract query keywords
                query_keywords = await self._extract_content_keywords(query)
                content_keywords = await self._extract_content_keywords(event.memory_content)
                
                if query_keywords and content_keywords:
                    # Learn query-content associations
                    await self._update_query_content_associations(
                        event.user_id, query_keywords, content_keywords, 
                        relevance_score, event.learning_confidence
                    )
            
            # Learn from emotional retrieval patterns
            if event.emotional_context and self.emotional_memory_bridge:
                await self._update_emotional_retrieval_patterns(event)
                
        except (ValueError, AttributeError) as e:
            logger.warning("Error learning from retrieval event: %s", e)

    async def _update_topic_importance_patterns(
        self, 
        user_id: str, 
        keywords: List[str], 
        importance_score: float, 
        confidence: float
    ):
        """Update topic-based importance patterns"""
        try:
            # Load existing patterns
            existing_patterns = await self.memory_importance_engine.load_user_importance_patterns(user_id)
            
            # Find or create topic pattern
            topic_pattern = None
            for pattern in existing_patterns:
                if pattern.get("pattern_type") == "topic_importance":
                    pattern_keywords = set(pattern.get("pattern_keywords", []))
                    keyword_overlap = len(set(keywords) & pattern_keywords)
                    
                    if keyword_overlap > 0:  # Found related pattern
                        topic_pattern = pattern
                        break
            
            if topic_pattern:
                # Update existing pattern
                current_multiplier = topic_pattern.get("importance_multiplier", 1.0)
                current_confidence = topic_pattern.get("confidence_score", 0.5)
                
                # Weighted update based on new evidence
                weight = confidence * 0.3  # Conservative learning rate
                new_multiplier = current_multiplier + (importance_score - 0.5) * weight
                new_confidence = (current_confidence + confidence) / 2
                
                topic_pattern.update({
                    "importance_multiplier": max(0.5, min(2.0, new_multiplier)),
                    "confidence_score": min(1.0, new_confidence),
                    "frequency_count": topic_pattern.get("frequency_count", 1) + 1,
                    "last_updated": datetime.now(tz.utc).isoformat(),
                })
                
                # Save updated pattern
                await self.memory_importance_engine.save_importance_pattern(
                    user_id, "topic_importance", topic_pattern
                )
                
            else:
                # Create new topic pattern
                new_pattern = {
                    "pattern_name": f"topic_importance_{len(keywords)}_{user_id}",
                    "importance_multiplier": 1.0 + (importance_score - 0.5) * 0.5,
                    "confidence_score": confidence,
                    "frequency_count": 1,
                    "pattern_keywords": keywords[:10],  # Limit keywords
                    "creation_method": "automatic_learning",
                    "last_updated": datetime.now(tz.utc).isoformat(),
                }
                
                await self.memory_importance_engine.save_importance_pattern(
                    user_id, "topic_importance", new_pattern
                )
                
        except (ValueError, AttributeError) as e:
            logger.warning("Error updating topic importance patterns: %s", e)

    async def _update_access_frequency_patterns(
        self, 
        user_id: str, 
        keywords: List[str], 
        access_count: int, 
        confidence: float
    ):
        """Update patterns based on memory access frequency"""
        try:
            # Create access frequency pattern
            access_boost = min(0.5, (access_count - 1) * 0.1)  # Max 0.5 boost
            
            pattern_data = {
                "pattern_name": f"access_frequency_{user_id}_{datetime.now(tz.utc).timestamp()}",
                "importance_multiplier": 1.0 + access_boost,
                "confidence_score": confidence,
                "frequency_count": access_count,
                "pattern_keywords": keywords[:8],
                "access_based_learning": True,
                "creation_method": "access_frequency_learning",
                "last_updated": datetime.now(tz.utc).isoformat(),
            }
            
            await self.memory_importance_engine.save_importance_pattern(
                user_id, "access_frequency", pattern_data
            )
            
        except (ValueError, AttributeError) as e:
            logger.warning("Error updating access frequency patterns: %s", e)

    async def _update_query_content_associations(
        self, 
        user_id: str, 
        query_keywords: List[str], 
        content_keywords: List[str], 
        relevance_score: float, 
        confidence: float
    ):
        """Update query-content association patterns"""
        try:
            # Create query-content association pattern
            association_strength = relevance_score * confidence
            
            pattern_data = {
                "pattern_name": f"query_content_association_{user_id}_{datetime.now(tz.utc).timestamp()}",
                "importance_multiplier": 1.0 + (association_strength - 0.5) * 0.3,
                "confidence_score": confidence,
                "frequency_count": 1,
                "query_keywords": query_keywords[:5],
                "content_keywords": content_keywords[:5],
                "association_strength": association_strength,
                "creation_method": "query_content_learning",
                "last_updated": datetime.now(tz.utc).isoformat(),
            }
            
            await self.memory_importance_engine.save_importance_pattern(
                user_id, "query_association", pattern_data
            )
            
        except (ValueError, AttributeError) as e:
            logger.warning("Error updating query-content associations: %s", e)

    async def _update_emotional_storage_patterns(self, event: LearningEvent):
        """Update emotional patterns from storage events"""
        try:
            if not self.emotional_memory_bridge:
                return
                
            emotional_context = event.emotional_context
            if not emotional_context:
                return
                
            # Extract emotional learning signals
            mood = emotional_context.get("mood_category", "neutral")
            stress_level = emotional_context.get("stress_level", "low")
            trigger_match = emotional_context.get("trigger_match", False)
            
            # Learn from emotional storage patterns
            if trigger_match and event.importance_score > 0.7:
                content_keywords = await self._extract_content_keywords(event.memory_content)
                
                if content_keywords:
                    emotional_pattern = {
                        "pattern_name": f"emotional_storage_{mood}_{event.user_id}",
                        "importance_multiplier": 1.0 + (event.importance_score - 0.5) * 0.4,
                        "confidence_score": event.learning_confidence,
                        "frequency_count": 1,
                        "pattern_keywords": content_keywords[:6],
                        "emotional_associations": [mood],
                        "stress_context": stress_level,
                        "creation_method": "emotional_storage_learning",
                        "last_updated": datetime.now(tz.utc).isoformat(),
                    }
                    
                    await self.memory_importance_engine.save_importance_pattern(
                        event.user_id, "emotional_storage", emotional_pattern
                    )
                    
        except (ValueError, AttributeError) as e:
            logger.warning("Error updating emotional storage patterns: %s", e)

    async def _update_emotional_retrieval_patterns(self, event: LearningEvent):
        """Update emotional patterns from retrieval events"""
        try:
            if not self.emotional_memory_bridge:
                return
                
            emotional_context = event.emotional_context
            query = event.context_data.get("query", "")
            relevance_score = event.context_data.get("relevance_score", 0.0)
            
            if emotional_context and query and relevance_score > 0.7:
                mood = emotional_context.get("mood_category", "neutral")
                
                # Learn emotional retrieval preferences
                query_keywords = await self._extract_content_keywords(query)
                
                if query_keywords:
                    retrieval_pattern = {
                        "pattern_name": f"emotional_retrieval_{mood}_{event.user_id}",
                        "importance_multiplier": 1.0 + relevance_score * 0.3,
                        "confidence_score": event.learning_confidence,
                        "frequency_count": 1,
                        "query_keywords": query_keywords[:5],
                        "emotional_associations": [mood],
                        "retrieval_preference": True,
                        "creation_method": "emotional_retrieval_learning",
                        "last_updated": datetime.now(tz.utc).isoformat(),
                    }
                    
                    await self.memory_importance_engine.save_importance_pattern(
                        event.user_id, "emotional_retrieval", retrieval_pattern
                    )
                    
        except (ValueError, AttributeError) as e:
            logger.warning("Error updating emotional retrieval patterns: %s", e)

    def _calculate_learning_confidence(
        self, 
        memory_data: Dict[str, Any], 
        _context: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for learning events"""
        try:
            base_confidence = 0.5
            
            # Boost confidence based on importance score
            importance = memory_data.get("importance_score", 0.5)
            importance_boost = (importance - 0.5) * 0.4
            
            # Boost confidence based on content length
            content = memory_data.get("content", "")
            length_boost = min(0.2, len(content.split()) / 50)  # Longer content = higher confidence
            
            # Boost confidence based on emotional enhancement
            emotional_context = memory_data.get("emotional_enhancement")
            emotional_boost = 0.2 if emotional_context and emotional_context.get("enhancement_applied") else 0.0
            
            # Boost confidence based on context richness
            context_boost = min(0.2, len(_context) / 10)
            
            final_confidence = base_confidence + importance_boost + length_boost + emotional_boost + context_boost
            return min(1.0, max(0.1, final_confidence))
            
        except (ValueError, AttributeError):
            return 0.5

    def _calculate_access_confidence(self, access_context: Dict[str, Any]) -> float:
        """Calculate confidence for access-based learning"""
        try:
            base_confidence = 0.4
            
            # Higher access count = higher confidence
            access_count = access_context.get("access_count", 1)
            access_boost = min(0.3, access_count * 0.05)
            
            # Relevance score boosts confidence
            relevance = access_context.get("relevance_score", 0.5)
            relevance_boost = (relevance - 0.5) * 0.4
            
            final_confidence = base_confidence + access_boost + relevance_boost
            return min(1.0, max(0.1, final_confidence))
            
        except (ValueError, AttributeError):
            return 0.4

    def _calculate_access_importance_boost(
        self, 
        access_frequency: int, 
        query_relevance: float, 
        current_importance: float
    ) -> float:
        """Calculate importance boost based on access patterns"""
        try:
            # Frequent access indicates high importance
            frequency_boost = min(0.3, (access_frequency - 1) * 0.05)
            
            # High relevance indicates importance
            relevance_boost = max(0.0, (query_relevance - 0.5) * 0.2)
            
            # Consider current importance to avoid over-boosting
            importance_factor = 1.0 - current_importance  # Less boost for already important memories
            
            total_boost = (frequency_boost + relevance_boost) * importance_factor
            return min(0.4, total_boost)  # Cap boost at 0.4
            
        except (ValueError, AttributeError):
            return 0.0

    def _analyze_retrieval_session(
        self, 
        query: str, 
        memories: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze retrieval session for learning insights"""
        try:
            insights = {
                "query_length": len(query.split()),
                "memory_count": len(memories),
                "avg_relevance": 0.0,
                "high_relevance_count": 0,
                "topic_diversity": 0,
                "emotional_context_present": False,
            }
            
            if memories:
                relevance_scores = [m.get("relevance_score", 0.0) for m in memories]
                insights["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)
                insights["high_relevance_count"] = sum(1 for r in relevance_scores if r > 0.7)
                
                # Check for emotional context
                emotional_memories = [m for m in memories if m.get("emotional_enhancement")]
                insights["emotional_context_present"] = len(emotional_memories) > 0
                
                # Estimate topic diversity (simplified)
                unique_topics = set()
                for memory in memories:
                    content = memory.get("content", "")
                    words = content.lower().split()
                    unique_topics.update(words[:5])  # First 5 words as topic indicators
                
                insights["topic_diversity"] = min(1.0, len(unique_topics) / 20)
            
            return insights
            
        except (ValueError, AttributeError):
            return {"error": "analysis_failed"}

    async def _extract_content_keywords(self, content: str) -> List[str]:
        """Extract keywords from content for pattern learning"""
        try:
            if not content:
                return []
                
            # Simple keyword extraction (can be enhanced with NLP)
            words = content.lower().split()
            
            # Filter out common stop words
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
                "of", "with", "by", "from", "up", "about", "into", "through", "during",
                "before", "after", "above", "below", "is", "are", "was", "were", "be",
                "been", "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "must", "can", "this",
                "that", "these", "those", "i", "you", "he", "she", "it", "we", "they"
            }
            
            # Extract significant words
            keywords = []
            for word in words:
                # Clean word
                word = ''.join(c for c in word if c.isalnum())
                
                # Keep words that are 3+ characters and not stop words
                if len(word) >= 3 and word not in stop_words:
                    keywords.append(word)
            
            # Return top keywords by frequency
            word_freq = {}
            for word in keywords:
                word_freq[word] = word_freq.get(word, 0) + 1
                
            sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_keywords[:10]]  # Top 10 keywords
            
        except (ValueError, AttributeError):
            return []

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about automatic learning activity"""
        try:
            stats = {
                "total_learning_events": len(self.learning_events),
                "session_learning_count": self.session_learning_count,
                "event_types": {},
                "avg_learning_confidence": 0.0,
                "learning_active": self.session_learning_count > 0,
            }
            
            if self.learning_events:
                # Count event types
                for event in self.learning_events:
                    event_type = event.event_type
                    stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
                
                # Calculate average confidence
                confidences = [event.learning_confidence for event in self.learning_events]
                stats["avg_learning_confidence"] = sum(confidences) / len(confidences)
                
                # Recent learning activity
                recent_events = [
                    event for event in self.learning_events 
                    if (datetime.now(tz.utc) - event.timestamp).seconds < 3600  # Last hour
                ]
                stats["recent_learning_events"] = len(recent_events)
            
            return stats
            
        except (ValueError, AttributeError):
            return {"error": "statistics_unavailable"}

    def reset_session_learning(self):
        """Reset session learning counters"""
        self.session_learning_count = 0
        logger.debug("Session learning counters reset")