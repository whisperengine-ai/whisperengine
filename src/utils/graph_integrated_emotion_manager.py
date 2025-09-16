"""
Integrated Emotion Manager with Graph Database Enhancement

This module extends the existing emotion manager to optionally sync with
a graph database while preserving all existing functionality.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from src.utils.emotion_manager import EmotionManager, UserProfile, EmotionProfile, RelationshipLevel
from src.graph_database.neo4j_connector import get_neo4j_connector, Neo4jConnector

logger = logging.getLogger(__name__)


class GraphIntegratedEmotionManager(EmotionManager):
    """Enhanced emotion manager with optional graph database integration"""

    def __init__(self, *args, **kwargs):
        """Initialize with optional graph database support"""
        super().__init__(*args, **kwargs)

        # Graph database configuration
        self.enable_graph_sync = os.getenv("ENABLE_GRAPH_DATABASE", "false").lower() == "true"
        self.graph_sync_mode = os.getenv(
            "GRAPH_SYNC_MODE", "async"
        ).lower()  # async, sync, disabled
        self.fallback_to_existing = os.getenv("FALLBACK_TO_EXISTING", "true").lower() == "true"
        self.sync_interval = int(os.getenv("EMOTION_GRAPH_SYNC_INTERVAL", "10"))

        # Graph connection (lazy loaded)
        self._graph_connector: Optional[Neo4jConnector] = None
        self._graph_available = None  # Cache availability check
        self._last_relationship_levels: Dict[str, RelationshipLevel] = {}

        logger.info(
            f"Graph integration: enabled={self.enable_graph_sync}, mode={self.graph_sync_mode}"
        )

    async def _get_graph_connector(self) -> Optional[Neo4jConnector]:
        """Get graph connector with lazy loading and caching"""
        if not self.enable_graph_sync:
            return None

        # Use cached availability check
        if self._graph_available is False:
            return None

        try:
            if self._graph_connector is None:
                self._graph_connector = await get_neo4j_connector()
                self._graph_available = True
                logger.info("Graph database connection established")

            return self._graph_connector

        except Exception as e:
            self._graph_available = False
            if self.fallback_to_existing:
                logger.warning(f"Graph database unavailable, using existing system: {e}")
                return None
            else:
                raise

    def process_interaction_enhanced(
        self, user_id: str, message: str, display_name: Optional[str] = None
    ) -> Tuple[UserProfile, EmotionProfile]:
        """Enhanced process_interaction with optional graph sync"""

        # Use existing emotion analysis system (preserve all functionality)
        profile, emotion_profile = self.process_interaction(user_id, message, display_name)

        # Sync to graph database if enabled and available
        if self.enable_graph_sync and self.graph_sync_mode != "disabled":
            if self.graph_sync_mode == "async":
                # Non-blocking sync
                asyncio.create_task(self._sync_to_graph_database(profile, emotion_profile, message))
            elif self.graph_sync_mode == "sync":
                # Blocking sync
                try:
                    asyncio.run(self._sync_to_graph_database(profile, emotion_profile, message))
                except Exception as e:
                    logger.warning(f"Synchronous graph sync failed: {e}")

        return profile, emotion_profile

    async def _sync_to_graph_database(
        self, profile: UserProfile, emotion_profile: EmotionProfile, message: str
    ):
        """Sync current emotion/relationship state to graph database"""

        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return

        try:
            # Create/update user node with current state
            await graph_connector.create_or_update_user(
                user_id=profile.user_id,
                discord_id=profile.user_id,
                name=profile.name or f"User_{profile.user_id[-4:]}",
                relationship_level=profile.relationship_level.value,
                interaction_count=profile.interaction_count,
                current_emotion=profile.current_emotion.value,
                escalation_count=profile.escalation_count,
                trust_indicators=profile.trust_indicators or [],
            )

            # Create emotion context node for this interaction
            emotion_id = f"{profile.user_id}_emotion_{int(datetime.now().timestamp())}"
            await graph_connector.execute_write_query(
                """
                CREATE (ec:EmotionContext {
                    id: $emotion_id,
                    emotion: $emotion,
                    intensity: $intensity,
                    confidence: $confidence,
                    triggers: $triggers,
                    timestamp: datetime(),
                    resolved: false
                })
                
                WITH ec
                MATCH (u:User {id: $user_id})
                CREATE (u)-[:EXPERIENCED {
                    context: "conversation",
                    intensity: $intensity,
                    timestamp: datetime(),
                    message_preview: $message_preview
                }]->(ec)
                """,
                {
                    "emotion_id": emotion_id,
                    "emotion": emotion_profile.detected_emotion.value,
                    "intensity": emotion_profile.intensity,
                    "confidence": emotion_profile.confidence,
                    "triggers": emotion_profile.triggers,
                    "user_id": profile.user_id,
                    "message_preview": message[:100],  # Store preview for context
                },
            )

            # Track relationship progression
            await self._track_relationship_progression(profile)

            # Extract and link topics from message
            topics = await self._extract_topics_from_message(message)
            if topics:
                await self._link_message_to_topics(
                    profile.user_id, emotion_id, topics, emotion_profile
                )

            logger.debug(f"Synced emotion data to graph for user {profile.user_id}")

        except Exception as e:
            logger.warning(f"Graph sync failed for user {profile.user_id}: {e}")
            if not self.fallback_to_existing:
                raise

    async def _track_relationship_progression(self, profile: UserProfile):
        """Track relationship level changes in graph database"""

        user_id = profile.user_id
        current_level = profile.relationship_level

        # Check if relationship level changed
        previous_level = self._last_relationship_levels.get(user_id)
        if previous_level != current_level:

            graph_connector = await self._get_graph_connector()
            if graph_connector:
                # Create relationship milestone
                await graph_connector.execute_write_query(
                    """
                    MATCH (u:User {id: $user_id})
                    MERGE (bot:User {id: 'bot'})
                    
                    CREATE (u)-[:RELATIONSHIP_MILESTONE {
                        level: $level,
                        achieved_at: datetime(),
                        previous_level: $previous_level,
                        interaction_count: $interaction_count,
                        context: $context
                    }]->(bot)
                    """,
                    {
                        "user_id": user_id,
                        "level": current_level.value,
                        "previous_level": previous_level.value if previous_level else "none",
                        "interaction_count": profile.interaction_count,
                        "context": f"Progressed from {previous_level.value if previous_level else 'new user'} to {current_level.value}",
                    },
                )

                logger.info(
                    f"Tracked relationship progression for {user_id}: {previous_level} → {current_level}"
                )

        # Update cache
        self._last_relationship_levels[user_id] = current_level

    async def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from message using enhanced detection"""

        topics = []
        message_lower = message.lower()

        # Enhanced topic detection with emotional context
        enhanced_topic_keywords = {
            "work_stress": [
                "work stress",
                "job pressure",
                "deadline",
                "boss",
                "overtime",
                "project stress",
            ],
            "work_success": [
                "promotion",
                "raise",
                "work achievement",
                "project success",
                "work proud",
            ],
            "family_positive": [
                "family time",
                "family gathering",
                "parents proud",
                "family support",
            ],
            "family_conflict": [
                "family argument",
                "family problem",
                "parents upset",
                "family stress",
            ],
            "health_concern": ["doctor", "medical", "health issue", "pain", "sick", "hospital"],
            "relationship_positive": [
                "relationship good",
                "partner",
                "love",
                "dating",
                "anniversary",
            ],
            "relationship_problems": [
                "breakup",
                "relationship issue",
                "fight with",
                "relationship stress",
            ],
            "hobby_excitement": ["hobby", "game", "sport", "music", "art", "creative"],
            "financial_stress": ["money", "financial", "bills", "debt", "expensive", "afford"],
            "achievement": ["proud", "accomplished", "succeeded", "achieved", "milestone"],
            "personal_growth": ["learning", "improving", "growing", "developing", "progress"],
            "social": ["friends", "social", "party", "gathering", "meetup", "social event"],
            "technology": ["computer", "phone", "app", "software", "tech", "programming"],
            "education": ["study", "school", "course", "learning", "education", "exam"],
        }

        for topic, keywords in enhanced_topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)

        # Fallback to general categories if no specific topics found
        if not topics:
            general_keywords = {
                "personal": ["i feel", "i think", "my", "personal"],
                "question": ["how", "what", "why", "when", "where", "?"],
                "help": ["help", "assist", "support", "advice", "suggest"],
                "casual": ["hi", "hello", "thanks", "bye", "chat"],
            }

            for topic, keywords in general_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    topics.append(topic)

        return topics if topics else ["general"]

    async def _link_message_to_topics(
        self, user_id: str, emotion_id: str, topics: List[str], emotion_profile: EmotionProfile
    ):
        """Link message topics to emotions in graph database"""

        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return

        for topic in topics:
            try:
                # Create or update topic node and link to emotion
                await graph_connector.execute_write_query(
                    """
                    MERGE (t:Topic {name: $topic})
                    ON CREATE SET t.id = randomUUID(),
                                 t.category = $category,
                                 t.created_at = datetime(),
                                 t.first_mentioned = datetime(),
                                 t.importance_score = 0.5
                    ON MATCH SET t.last_mentioned = datetime()
                    
                    WITH t
                    MATCH (ec:EmotionContext {id: $emotion_id})
                    CREATE (t)-[:TRIGGERS {
                        emotion: $emotion,
                        intensity: $intensity,
                        timestamp: datetime(),
                        user_id: $user_id
                    }]->(ec)
                    """,
                    {
                        "topic": topic,
                        "category": self._categorize_topic(topic),
                        "emotion_id": emotion_id,
                        "emotion": emotion_profile.detected_emotion.value,
                        "intensity": emotion_profile.intensity,
                        "user_id": user_id,
                    },
                )

            except Exception as e:
                logger.warning(f"Failed to link topic {topic} to emotion: {e}")

    def _categorize_topic(self, topic: str) -> str:
        """Categorize topics for better organization"""

        category_mapping = {
            "work": ["work_stress", "work_success"],
            "family": ["family_positive", "family_conflict"],
            "health": ["health_concern"],
            "relationships": ["relationship_positive", "relationship_problems"],
            "hobbies": ["hobby_excitement"],
            "finance": ["financial_stress"],
            "personal": ["achievement", "personal_growth"],
            "social": ["social"],
            "technology": ["technology"],
            "education": ["education"],
            "general": ["personal", "question", "help", "casual", "general"],
        }

        for category, topic_list in category_mapping.items():
            if topic in topic_list:
                return category

        return "general"

    async def get_enhanced_emotion_context(self, user_id: str, current_message: str = "") -> str:
        """Get emotion context enhanced with graph database insights"""

        # Get existing emotion context (preserve original functionality)
        base_context = self.get_emotion_context(user_id)

        # Enhance with graph data if available
        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return base_context

        try:
            # Get relationship context from graph
            relationship_context = await graph_connector.get_user_relationship_context(user_id)
            emotional_patterns = await graph_connector.get_emotional_patterns(user_id)

            enhancements = []

            # Add topic associations
            if relationship_context.get("topics"):
                topic_names = [t["name"] for t in relationship_context["topics"][:3]]
                enhancements.append(f"Recent topics: {', '.join(topic_names)}")

            # Add emotional trigger patterns
            if emotional_patterns.get("triggers"):
                # Find topics that frequently trigger negative emotions
                negative_triggers = [
                    t
                    for t in emotional_patterns["triggers"]
                    if t.get("emotion") in ["frustrated", "angry", "sad", "worried"]
                    and t.get("avg_intensity", 0) > 0.6
                ][:2]

                if negative_triggers:
                    trigger_topics = [t["topic"] for t in negative_triggers]
                    enhancements.append(f"Sensitive topics: {', '.join(trigger_topics)}")

                # Find topics that trigger positive emotions
                positive_triggers = [
                    t
                    for t in emotional_patterns["triggers"]
                    if t.get("emotion") in ["happy", "excited", "grateful"]
                    and t.get("avg_intensity", 0) > 0.6
                ][:2]

                if positive_triggers:
                    positive_topics = [t["topic"] for t in positive_triggers]
                    enhancements.append(f"Positive topics: {', '.join(positive_topics)}")

            # Add relationship progression insights
            intimacy_level = relationship_context.get("intimacy_level", 0.3)
            memory_count = relationship_context.get("memory_count", 0)

            if intimacy_level >= 0.7:
                enhancements.append(f"Close relationship with {memory_count} shared conversations")
            elif intimacy_level >= 0.5:
                enhancements.append(f"Developing relationship with {memory_count} conversations")

            # Combine enhancements with base context
            if enhancements:
                enhanced_context = base_context + "\nGraph insights: " + "; ".join(enhancements)
                return enhanced_context

        except Exception as e:
            logger.warning(f"Failed to enhance context with graph data: {e}")

        return base_context

    async def get_contextual_memories_for_prompt(
        self, user_id: str, message: str, limit: int = 5
    ) -> str:
        """Get relevant memories based on current message context"""

        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return ""

        try:
            # Extract topics from current message
            topics = await self._extract_topics_from_message(message)

            # Get relevant memories from graph
            memories = []
            for topic in topics[:2]:  # Limit to 2 most relevant topics
                topic_memories = await graph_connector.get_contextual_memories(
                    user_id, topic, limit=3
                )
                memories.extend(topic_memories)

            if memories:
                # Format memories for context
                memory_summaries = []
                for memory in memories[:limit]:
                    summary = memory.get("summary", "")
                    emotion = memory.get("emotion", "")
                    if summary:
                        emotion_context = (
                            f" ({emotion})" if emotion and emotion != "neutral" else ""
                        )
                        memory_summaries.append(f"- {summary}{emotion_context}")

                if memory_summaries:
                    return "Relevant memories:\n" + "\n".join(memory_summaries)

        except Exception as e:
            logger.warning(f"Failed to get contextual memories: {e}")

        return ""

    async def health_check(self) -> Dict[str, Any]:
        """Check health of emotion manager and graph integration"""

        health_status = {
            "emotion_manager": {"status": "healthy"},
            "graph_integration": {
                "enabled": self.enable_graph_sync,
                "mode": self.graph_sync_mode,
                "status": "disabled" if not self.enable_graph_sync else "unknown",
            },
            "user_profiles": len(self.user_profiles),
            "fallback_enabled": self.fallback_to_existing,
        }

        # Check graph database health if enabled
        if self.enable_graph_sync:
            try:
                graph_connector = await self._get_graph_connector()
                if graph_connector:
                    graph_health = await graph_connector.health_check()
                    health_status["graph_integration"]["status"] = graph_health.get(
                        "status", "unknown"
                    )
                    health_status["graph_integration"]["details"] = graph_health
                else:
                    health_status["graph_integration"]["status"] = "unavailable"
            except Exception as e:
                health_status["graph_integration"]["status"] = "error"
                health_status["graph_integration"]["error"] = str(e)

        return health_status

    # Preserve all existing methods by inheritance
    # This ensures backward compatibility with existing code
