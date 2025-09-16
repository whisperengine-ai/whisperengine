"""
Graph Database Personality Integration
====================================

Integrates personality profiling with Neo4j graph database for enhanced
relationship tracking and personality evolution over time.
"""

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from neo4j import AsyncGraphDatabase

from .personality_profiler import PersonalityMetrics, PersonalityProfiler

logger = logging.getLogger(__name__)


class GraphPersonalityManager:
    """Manages personality data in the graph database"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize graph database connection"""
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.profiler = PersonalityProfiler()
        logger.info("GraphPersonalityManager initialized")

    async def close(self):
        """Close database connection"""
        await self.driver.close()

    async def store_personality_profile(
        self, user_id: str, metrics: PersonalityMetrics, conversation_context: dict | None = None
    ) -> bool:
        """
        Store or update personality profile in graph database

        Args:
            user_id: User identifier
            metrics: Personality analysis results
            conversation_context: Optional context about when this was analyzed

        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.driver.session() as session:
                # Convert metrics to dictionary for storage
                personality_data = asdict(metrics)

                # Convert enums to strings
                if hasattr(personality_data.get("communication_style"), "value"):
                    personality_data["communication_style"] = personality_data[
                        "communication_style"
                    ].value
                if hasattr(personality_data.get("directness_style"), "value"):
                    personality_data["directness_style"] = personality_data[
                        "directness_style"
                    ].value
                if hasattr(personality_data.get("decision_style"), "value"):
                    personality_data["decision_style"] = personality_data["decision_style"].value

                # Convert datetime to ISO string
                if personality_data.get("last_updated"):
                    personality_data["last_updated"] = personality_data["last_updated"].isoformat()

                # Store/update personality profile
                await session.execute_write(
                    self._create_personality_profile,
                    user_id,
                    personality_data,
                    conversation_context,
                )

                logger.info(f"Stored personality profile for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error storing personality profile for user {user_id}: {e}")
            return False

    @staticmethod
    async def _create_personality_profile(
        tx, user_id: str, personality_data: dict, conversation_context: dict | None
    ):
        """Create or update personality profile node"""

        # Create or update user node with personality data
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.personality_openness = $openness,
            u.personality_conscientiousness = $conscientiousness,
            u.personality_extraversion = $extraversion,
            u.personality_agreeableness = $agreeableness,
            u.personality_neuroticism = $neuroticism,
            u.communication_style = $communication_style,
            u.directness_style = $directness_style,
            u.decision_style = $decision_style,
            u.avg_message_length = $avg_message_length,
            u.complexity_score = $complexity_score,
            u.emotional_expressiveness = $emotional_expressiveness,
            u.confidence_level = $confidence_level,
            u.detail_orientation = $detail_orientation,
            u.abstract_thinking = $abstract_thinking,
            u.social_engagement = $social_engagement,
            u.personality_last_updated = $last_updated,
            u.personality_confidence = $confidence_interval,
            u.total_messages_analyzed = $total_messages_analyzed
        RETURN u
        """

        await tx.run(
            query,
            user_id=user_id,
            openness=personality_data.get("openness", 0.5),
            conscientiousness=personality_data.get("conscientiousness", 0.5),
            extraversion=personality_data.get("extraversion", 0.5),
            agreeableness=personality_data.get("agreeableness", 0.5),
            neuroticism=personality_data.get("neuroticism", 0.5),
            communication_style=personality_data.get("communication_style", "mixed"),
            directness_style=personality_data.get("directness_style", "diplomatic"),
            decision_style=personality_data.get("decision_style", "deliberate"),
            avg_message_length=personality_data.get("avg_message_length", 0.0),
            complexity_score=personality_data.get("complexity_score", 0.5),
            emotional_expressiveness=personality_data.get("emotional_expressiveness", 0.5),
            confidence_level=personality_data.get("confidence_level", 0.5),
            detail_orientation=personality_data.get("detail_orientation", 0.5),
            abstract_thinking=personality_data.get("abstract_thinking", 0.5),
            social_engagement=personality_data.get("social_engagement", 0.5),
            last_updated=personality_data.get("last_updated"),
            confidence_interval=personality_data.get("confidence_interval", 0.0),
            total_messages_analyzed=personality_data.get("total_messages_analyzed", 0),
        )

    async def get_personality_profile(self, user_id: str) -> dict | None:
        """
        Retrieve personality profile from graph database

        Args:
            user_id: User identifier

        Returns:
            Dictionary with personality data or None if not found
        """
        try:
            async with self.driver.session() as session:
                result = await session.execute_read(self._get_personality_data, user_id)
                return result

        except Exception as e:
            logger.error(f"Error retrieving personality profile for user {user_id}: {e}")
            return None

    @staticmethod
    async def _get_personality_data(tx, user_id: str) -> dict | None:
        """Retrieve personality data for user"""
        query = """
        MATCH (u:User {user_id: $user_id})
        WHERE u.personality_last_updated IS NOT NULL
        RETURN u.personality_openness as openness,
               u.personality_conscientiousness as conscientiousness,
               u.personality_extraversion as extraversion,
               u.personality_agreeableness as agreeableness,
               u.personality_neuroticism as neuroticism,
               u.communication_style as communication_style,
               u.directness_style as directness_style,
               u.decision_style as decision_style,
               u.avg_message_length as avg_message_length,
               u.complexity_score as complexity_score,
               u.emotional_expressiveness as emotional_expressiveness,
               u.confidence_level as confidence_level,
               u.detail_orientation as detail_orientation,
               u.abstract_thinking as abstract_thinking,
               u.social_engagement as social_engagement,
               u.personality_last_updated as last_updated,
               u.personality_confidence as confidence_interval,
               u.total_messages_analyzed as total_messages_analyzed
        """

        result = await tx.run(query, user_id=user_id)
        record = await result.single()

        if record:
            return dict(record)
        return None

    async def analyze_and_store_personality(
        self, user_id: str, messages: list[str], conversation_context: dict | None = None
    ) -> dict | None:
        """
        Analyze personality from messages and store in graph database

        Args:
            user_id: User identifier
            messages: List of user messages to analyze
            conversation_context: Optional context about the conversation

        Returns:
            Personality summary or None if failed
        """
        try:
            # Analyze personality
            metrics = self.profiler.analyze_personality(messages, user_id)

            # Store in graph database
            success = await self.store_personality_profile(user_id, metrics, conversation_context)

            if success:
                # Return summary
                summary = self.profiler.get_personality_summary(metrics)
                return summary
            else:
                return None

        except Exception as e:
            logger.error(f"Error analyzing and storing personality for user {user_id}: {e}")
            return None

    async def get_personality_insights(self, user_id: str) -> dict[str, Any]:
        """
        Get comprehensive personality insights including graph relationships

        Args:
            user_id: User identifier

        Returns:
            Dictionary with personality insights and relationship patterns
        """
        try:
            async with self.driver.session() as session:
                # Get personality profile
                personality = await self.get_personality_profile(user_id)

                if not personality:
                    return {"error": "No personality profile found"}

                # Get conversation patterns from graph
                conversation_patterns = await session.execute_read(
                    self._get_conversation_patterns, user_id
                )

                # Get relationship insights
                relationship_insights = await session.execute_read(
                    self._get_relationship_insights, user_id
                )

                return {
                    "personality_profile": personality,
                    "conversation_patterns": conversation_patterns,
                    "relationship_insights": relationship_insights,
                    "recommendations": self._generate_recommendations(personality),
                }

        except Exception as e:
            logger.error(f"Error getting personality insights for user {user_id}: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _get_conversation_patterns(tx, user_id: str) -> dict:
        """Get conversation patterns from graph"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:PARTICIPATED_IN]->(c:Conversation)
        WITH u, c, COUNT {(c)-[:CONTAINS]->(:Message)} as message_count
        RETURN count(c) as total_conversations,
               avg(message_count) as avg_messages_per_conversation,
               collect(DISTINCT c.topic)[0..5] as common_topics
        """

        result = await tx.run(query, user_id=user_id)
        record = await result.single()

        if record:
            return {
                "total_conversations": record["total_conversations"],
                "avg_messages_per_conversation": record["avg_messages_per_conversation"],
                "common_topics": record["common_topics"],
            }
        return {}

    @staticmethod
    async def _get_relationship_insights(tx, user_id: str) -> dict:
        """Get relationship insights from graph"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:COMMUNICATED_WITH]->(other:User)
        WITH u, other, r.message_count as interactions
        ORDER BY interactions DESC
        RETURN collect({
            user_id: other.user_id,
            interaction_count: interactions,
            relationship_strength: r.strength
        })[0..5] as top_relationships
        """

        result = await tx.run(query, user_id=user_id)
        record = await result.single()

        if record:
            return {"top_relationships": record["top_relationships"]}
        return {"top_relationships": []}

    def _generate_recommendations(self, personality: dict) -> list[str]:
        """Generate personalized recommendations based on personality"""
        recommendations = []

        # Communication style recommendations
        if personality.get("communication_style") == "formal":
            recommendations.append("Prefers structured, professional communication")
        elif personality.get("communication_style") == "casual":
            recommendations.append("Responds well to informal, friendly conversation")

        # Decision style recommendations
        decision_style = personality.get("decision_style")
        if decision_style == "analytical":
            recommendations.append("Provide detailed information and data to support decisions")
        elif decision_style == "quick":
            recommendations.append("Present clear, concise options for quick decision-making")

        # Emotional expressiveness recommendations
        emotional_expr = personality.get("emotional_expressiveness", 0.5)
        if emotional_expr > 0.7:
            recommendations.append(
                "Comfortable with emotional discussions and empathetic responses"
            )
        elif emotional_expr < 0.3:
            recommendations.append("Prefers fact-based, less emotional conversation approach")

        # Confidence level recommendations
        confidence = personality.get("confidence_level", 0.5)
        if confidence > 0.7:
            recommendations.append("Appreciates direct feedback and challenging discussions")
        elif confidence < 0.3:
            recommendations.append("Benefits from reassurance and supportive communication")

        return recommendations

    async def update_personality_from_conversation(
        self, user_id: str, new_messages: list[str]
    ) -> bool:
        """
        Update personality profile with new conversation data

        Args:
            user_id: User identifier
            new_messages: New messages to incorporate into personality analysis

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing personality data
            existing_profile = await self.get_personality_profile(user_id)

            # Analyze new messages
            new_metrics = self.profiler.analyze_personality(new_messages, user_id)

            if existing_profile:
                # Merge with existing data (weighted average)
                merged_metrics = self._merge_personality_metrics(existing_profile, new_metrics)
            else:
                merged_metrics = new_metrics

            # Store updated profile
            return await self.store_personality_profile(user_id, merged_metrics)

        except Exception as e:
            logger.error(f"Error updating personality from conversation for user {user_id}: {e}")
            return False

    def _merge_personality_metrics(
        self, existing: dict, new: PersonalityMetrics
    ) -> PersonalityMetrics:
        """Merge existing personality data with new analysis"""
        # Weight factor for new vs existing data
        existing_weight = min(0.8, existing.get("total_messages_analyzed", 0) / 100.0)
        new_weight = 1.0 - existing_weight

        # Create merged metrics
        merged = PersonalityMetrics()

        # Merge Big Five traits
        merged.openness = (
            existing.get("openness", 0.5) * existing_weight + new.openness * new_weight
        )
        merged.conscientiousness = (
            existing.get("conscientiousness", 0.5) * existing_weight
            + new.conscientiousness * new_weight
        )
        merged.extraversion = (
            existing.get("extraversion", 0.5) * existing_weight + new.extraversion * new_weight
        )
        merged.agreeableness = (
            existing.get("agreeableness", 0.5) * existing_weight + new.agreeableness * new_weight
        )
        merged.neuroticism = (
            existing.get("neuroticism", 0.5) * existing_weight + new.neuroticism * new_weight
        )

        # Merge behavioral metrics
        merged.avg_message_length = (
            existing.get("avg_message_length", 0.0) * existing_weight
            + new.avg_message_length * new_weight
        )
        merged.complexity_score = (
            existing.get("complexity_score", 0.5) * existing_weight
            + new.complexity_score * new_weight
        )
        merged.emotional_expressiveness = (
            existing.get("emotional_expressiveness", 0.5) * existing_weight
            + new.emotional_expressiveness * new_weight
        )
        merged.confidence_level = (
            existing.get("confidence_level", 0.5) * existing_weight
            + new.confidence_level * new_weight
        )
        merged.detail_orientation = (
            existing.get("detail_orientation", 0.5) * existing_weight
            + new.detail_orientation * new_weight
        )
        merged.abstract_thinking = (
            existing.get("abstract_thinking", 0.5) * existing_weight
            + new.abstract_thinking * new_weight
        )
        merged.social_engagement = (
            existing.get("social_engagement", 0.5) * existing_weight
            + new.social_engagement * new_weight
        )

        # Use the most recent categorical assessments (they don't average well)
        merged.communication_style = new.communication_style
        merged.directness_style = new.directness_style
        merged.decision_style = new.decision_style

        # Update metadata
        merged.total_messages_analyzed = (
            existing.get("total_messages_analyzed", 0) + new.total_messages_analyzed
        )
        merged.last_updated = datetime.now(UTC)
        merged.confidence_interval = min(0.95, merged.total_messages_analyzed / 100.0)

        return merged
