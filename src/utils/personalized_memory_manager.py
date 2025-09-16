"""
Enhanced Memory Manager with Graph Database Integration

This module extends the existing UserMemoryManager to include graph-based
relationship modeling for more natural and personable AI interactions.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# Import existing components
from src.memory.memory_manager import UserMemoryManager
from .graph_memory_manager import GraphMemoryManager, GraphMemoryConfig
from .emotion_manager import EmotionalState, RelationshipLevel

logger = logging.getLogger(__name__)


class PersonalizedMemoryManager(UserMemoryManager):
    """Enhanced memory manager with graph-based personalization"""

    def __init__(
        self,
        *args,
        enable_graph_memory: bool = True,
        graph_config: Optional[GraphMemoryConfig] = None,
        **kwargs,
    ):
        """Initialize with graph database capabilities"""
        super().__init__(*args, **kwargs)

        self.enable_graph_memory = enable_graph_memory
        self.graph_manager = None

        if enable_graph_memory:
            config = graph_config or GraphMemoryConfig()
            self.graph_manager = GraphMemoryManager(config, memory_manager=self)

            # Initialize graph database asynchronously
            asyncio.create_task(self._initialize_graph_async())

    async def _initialize_graph_async(self):
        """Initialize graph database connection"""
        try:
            if self.graph_manager:
                await self.graph_manager.initialize()
                logger.info("Graph memory manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize graph memory manager: {e}")
            self.enable_graph_memory = False

    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        channel_id: Optional[str] = None,
        pre_analyzed_emotion_data: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ):
        """Enhanced conversation storage with graph relationship building"""

        # Store in ChromaDB using parent method
        super().store_conversation(
            user_id, user_message, bot_response, channel_id, pre_analyzed_emotion_data, metadata
        )

        # Enhance with graph relationships if enabled
        if self.enable_graph_memory and self.graph_manager:
            asyncio.create_task(
                self._store_graph_relationships(
                    user_id, user_message, bot_response, pre_analyzed_emotion_data
                )
            )

    async def _store_graph_relationships(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        emotion_data: Optional[dict] = None,
    ):
        """Store relationships in graph database"""
        try:
            # Extract topics from the conversation
            topics = await self._extract_topics_from_message(user_message)

            # Create a summary for the memory node
            summary = f"User: {user_message[:100]}... Bot: {bot_response[:100]}..."

            # Generate a chromadb_id (this would typically come from the ChromaDB insertion)
            chromadb_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"

            # Store in graph with relationships
            await self.graph_manager.create_memory_with_relationships(
                user_id=user_id,
                chromadb_id=chromadb_id,
                summary=summary,
                topics=topics,
                emotion_data=emotion_data,
                importance=self._calculate_memory_importance(user_message, emotion_data),
            )

            # Update user profile in graph
            user_profile = self.get_user_emotion_profile(user_id)
            if user_profile:
                await self.graph_manager.create_or_update_user(
                    user_id=user_id,
                    discord_id=user_id,  # Assuming user_id is discord_id
                    name=user_profile.name,
                    personality_traits=await self._infer_personality_traits(user_id),
                    communication_style=await self._infer_communication_style(user_id),
                )

        except Exception as e:
            logger.error(f"Error storing graph relationships: {e}")

    async def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from user message using simple keyword extraction"""
        # This is a simplified version - you could enhance with NLP
        common_topics = {
            "work": ["work", "job", "career", "office", "boss", "colleague"],
            "family": ["family", "parent", "child", "sibling", "mom", "dad"],
            "hobbies": ["hobby", "play", "game", "music", "art", "sport"],
            "feelings": ["feel", "emotion", "happy", "sad", "angry", "excited"],
            "technology": ["computer", "software", "app", "internet", "tech"],
            "health": ["health", "doctor", "medicine", "exercise", "sick"],
            "education": ["school", "university", "study", "learn", "course"],
            "travel": ["travel", "trip", "vacation", "visit", "country"],
            "food": ["food", "eat", "cook", "restaurant", "recipe"],
            "relationships": ["friend", "relationship", "dating", "partner"],
        }

        message_lower = message.lower()
        detected_topics = []

        for topic, keywords in common_topics.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_topics.append(topic)

        # Add specific entities (this could be enhanced with NER)
        # For now, just return detected topics
        return detected_topics[:5]  # Limit to top 5 topics

    def _calculate_memory_importance(
        self, message: str, emotion_data: Optional[dict] = None
    ) -> float:
        """Calculate importance score for memory storage"""
        importance = 0.5  # Base importance

        # Increase importance based on message length (more detailed = more important)
        if len(message) > 100:
            importance += 0.1
        if len(message) > 200:
            importance += 0.1

        # Increase importance based on emotional intensity
        if emotion_data:
            emotion_intensity = emotion_data.get("intensity", 0)
            confidence = emotion_data.get("confidence", 0)
            importance += (emotion_intensity * confidence) * 0.3

        # Increase importance for personal information sharing
        personal_indicators = ["my name is", "i work", "i live", "my family", "i feel"]
        if any(indicator in message.lower() for indicator in personal_indicators):
            importance += 0.2

        return min(importance, 1.0)  # Cap at 1.0

    async def _infer_personality_traits(self, user_id: str) -> List[str]:
        """Infer personality traits from interaction history"""
        try:
            # Get recent conversations
            memories = self.retrieve_relevant_memories(
                user_id, "personality communication style", limit=20
            )

            traits = []
            message_texts = []

            for memory in memories:
                metadata = memory.get("metadata", {})
                if "user_message" in metadata:
                    message_texts.append(metadata["user_message"].lower())

            all_text = " ".join(message_texts)

            # Simple pattern matching for personality traits
            if any(word in all_text for word in ["please", "thank", "sorry"]):
                traits.append("polite")
            if any(word in all_text for word in ["!", "amazing", "awesome", "great"]):
                traits.append("enthusiastic")
            if len([msg for msg in message_texts if len(msg) > 100]) > len(message_texts) * 0.5:
                traits.append("detailed")
            if any(word in all_text for word in ["think", "analyze", "consider", "reason"]):
                traits.append("analytical")
            if any(word in all_text for word in ["feel", "emotion", "heart", "love"]):
                traits.append("emotional")

            return traits[:3]  # Return top 3 traits

        except Exception as e:
            logger.error(f"Error inferring personality traits: {e}")
            return []

    async def _infer_communication_style(self, user_id: str) -> str:
        """Infer communication style from message patterns"""
        try:
            memories = self.retrieve_relevant_memories(user_id, "communication", limit=10)

            message_lengths = []
            formality_score = 0
            casual_indicators = 0

            for memory in memories:
                metadata = memory.get("metadata", {})
                if "user_message" in metadata:
                    msg = metadata["user_message"]
                    message_lengths.append(len(msg))

                    # Check formality indicators
                    if any(word in msg.lower() for word in ["please", "would you", "could you"]):
                        formality_score += 1
                    if any(word in msg.lower() for word in ["hey", "yeah", "cool", "lol"]):
                        casual_indicators += 1

            avg_length = sum(message_lengths) / len(message_lengths) if message_lengths else 50

            if formality_score > casual_indicators:
                return "formal"
            elif casual_indicators > formality_score:
                return "casual"
            elif avg_length > 100:
                return "detailed"
            else:
                return "concise"

        except Exception as e:
            logger.error(f"Error inferring communication style: {e}")
            return "neutral"

    async def get_personalized_context(self, user_id: str, query: str, limit: int = 5) -> str:
        """Get context enhanced with graph-based relationship insights"""

        # Get regular context from parent class
        base_context = self.get_emotion_aware_context(user_id, query, limit)

        if not self.enable_graph_memory or not self.graph_manager:
            return base_context

        try:
            # Get graph-based relationship context
            relationship_context = await self.graph_manager.get_relationship_context(user_id)
            emotional_patterns = await self.graph_manager.get_emotional_patterns(user_id)

            # Extract topics from current query
            topics = await self._extract_topics_from_message(query)
            related_memories = await self.graph_manager.find_related_memories(
                user_id, topics, limit
            )

            # Build enhanced context
            context_parts = [base_context]

            if relationship_context:
                intimacy = relationship_context.get("intimacy_level", 0)
                if intimacy > 0.7:
                    context_parts.append(
                        f"\n[Deep Relationship Context: You have built strong trust with this user over {relationship_context.get('memory_count', 0)} interactions]"
                    )
                elif intimacy > 0.4:
                    context_parts.append(
                        f"\n[Growing Relationship: Developing friendship with this user]"
                    )

                if relationship_context.get("interests"):
                    interests = ", ".join(relationship_context["interests"][:3])
                    context_parts.append(f"\n[Known Interests: {interests}]")

            if emotional_patterns and emotional_patterns.get("dominant_emotions"):
                dominant = emotional_patterns["dominant_emotions"][0]
                context_parts.append(
                    f"\n[Emotional Profile: Often experiences {dominant['emotion']} (frequency: {dominant['frequency']})]"
                )

            if related_memories:
                memory_summaries = []
                for mem in related_memories[:3]:
                    if mem.get("emotion"):
                        memory_summaries.append(f"• {mem['summary']} (felt {mem['emotion']})")
                    else:
                        memory_summaries.append(f"• {mem['summary']}")

                if memory_summaries:
                    context_parts.append(
                        f"\n[Related Experiences:\n{chr(10).join(memory_summaries)}]"
                    )

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting personalized context: {e}")
            return base_context

    def generate_personality_aware_prompt(self, user_id: str, current_message: str) -> str:
        """Generate system prompt based on relationship analysis"""
        if not self.enable_graph_memory:
            return self.get_emotion_context(user_id)

        try:
            # This would be called asynchronously in practice
            relationship_future = asyncio.ensure_future(
                self.graph_manager.get_relationship_context(user_id)
            )

            # For now, return the emotion context as fallback
            base_context = self.get_emotion_context(user_id)

            # In a real implementation, you'd await the relationship context
            # and build a more sophisticated prompt
            return f"{base_context}\n[Graph-enhanced personality awareness enabled]"

        except Exception as e:
            logger.error(f"Error generating personality-aware prompt: {e}")
            return self.get_emotion_context(user_id)

    async def track_relationship_milestone(
        self, user_id: str, milestone_type: str, context: Optional[str] = None
    ):
        """Track significant relationship progression events"""
        if self.enable_graph_memory and self.graph_manager:
            await self.graph_manager.update_relationship_milestone(user_id, milestone_type, context)

    async def close(self):
        """Clean up resources"""
        if self.graph_manager:
            await self.graph_manager.close()
