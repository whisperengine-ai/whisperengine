"""
Feedback Analysis System

Analyzes user reactions (emoji) to bot messages and adjusts memory importance
scores and personality traits accordingly.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from influxdb_client.client.write.point import Point
from influxdb_client.client.flux_table import FluxTable
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src_v2.core.database import db_manager
from src_v2.config.settings import settings


class FeedbackAnalyzer:
    """
    Analyzes user feedback (reactions) to adjust memory importance and personality traits.
    """
    
    # Reaction sentiment mapping
    POSITIVE_REACTIONS = ['👍', '❤️', '😊', '🎉', '✨', '💯', '🔥', '💖']
    NEGATIVE_REACTIONS = ['👎', '😢', '😠', '💔', '😕', '🤔']
    
    def __init__(self):
        self.influx_client = db_manager.influxdb_client
        self.qdrant_client = db_manager.qdrant_client
        logger.info("FeedbackAnalyzer initialized")

    async def get_feedback_score(self, message_id: str, user_id: str) -> Optional[Dict]:
        """
        Queries InfluxDB for reactions to a specific message and calculates a feedback score.
        
        Args:
            message_id: Discord message ID
            user_id: User who sent the original message (for filtering)
            
        Returns:
            Dict with {score: float, positive_count: int, negative_count: int, reactions: List[str]}
            Score ranges from -1.0 (all negative) to +1.0 (all positive)
        """
        if not self.influx_client:
            logger.warning("InfluxDB not available, cannot get feedback score")
            return None
            
        try:
            query_api = self.influx_client.query_api()
            
            # Query for reaction events on this message
            flux_query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: -30d)
                |> filter(fn: (r) => r["_measurement"] == "reaction_event")
                |> filter(fn: (r) => r["message_id"] == "{message_id}")
                |> filter(fn: (r) => r["user_id"] == "{user_id}")
            '''
            
            tables = query_api.query(flux_query)
            
            reactions = []
            for table in tables:
                for record in table.records:
                    reaction = record.values.get("reaction")
                    if reaction:
                        reactions.append(reaction)
            
            if not reactions:
                return {
                    "score": 0.0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "reactions": []
                }
            
            # Calculate sentiment
            positive_count = sum(1 for r in reactions if r in self.POSITIVE_REACTIONS)
            negative_count = sum(1 for r in reactions if r in self.NEGATIVE_REACTIONS)
            total_count = positive_count + negative_count
            
            # Score: -1.0 to +1.0
            if total_count == 0:
                score = 0.0
            else:
                score = (positive_count - negative_count) / total_count
            
            logger.debug(f"Feedback score for message {message_id}: {score} (👍{positive_count} 👎{negative_count})")
            
            return {
                "score": score,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "reactions": reactions
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback score: {e}")
            return None

    async def adjust_memory_score(self, memory_id: str, collection_name: str, score_delta: float):
        """
        Updates the 'importance' score in a Qdrant memory point based on feedback.
        
        Args:
            memory_id: UUID of the memory point in Qdrant
            collection_name: Qdrant collection name
            score_delta: Amount to adjust the importance score by (-1.0 to +1.0)
        """
        if not self.qdrant_client:
            logger.warning("Qdrant not available, cannot adjust memory score")
            return
            
        try:
            # Retrieve the current point
            points = await self.qdrant_client.retrieve(
                collection_name=collection_name,
                ids=[memory_id]
            )
            
            if not points:
                logger.warning(f"Memory {memory_id} not found in {collection_name}")
                return
            
            point = points[0]
            payload = point.payload or {}
            current_importance = payload.get("importance", 0.5)
            
            # Adjust importance (clamp between 0 and 1)
            new_importance = max(0.0, min(1.0, current_importance + score_delta))
            
            # Update the point payload
            await self.qdrant_client.set_payload(
                collection_name=collection_name,
                payload={"importance": new_importance},
                points=[memory_id]
            )
            
            logger.info(f"Adjusted memory {memory_id} importance: {current_importance:.2f} -> {new_importance:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to adjust memory score: {e}")

    async def adjust_memory_score_by_message_id(self, message_id: str, collection_name: str, score_delta: float):
        """
        Finds a memory point by message_id and adjusts its importance score.
        """
        if not self.qdrant_client:
            return

        try:
            # Search for point with message_id in payload
            scroll_result = await self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="message_id",
                            match=MatchValue(value=message_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            points = scroll_result[0]
            if not points:
                logger.warning(f"No memory found for message_id {message_id}")
                return
                
            point_id = str(points[0].id)
            await self.adjust_memory_score(point_id, collection_name, score_delta)
            
        except Exception as e:
            logger.error(f"Failed to adjust memory by message_id: {e}")

    async def analyze_user_feedback_patterns(self, user_id: str, days: int = 30) -> Dict:
        """
        Analyzes a user's feedback patterns over time to detect preferences.
        
        Returns insights like:
        - "User dislikes long messages" (if consistently reacts 👎 to responses >500 chars)
        - "User loves empathetic responses" (if reacts ❤️ to emotion-heavy messages)
        
        Args:
            user_id: User to analyze
            days: Number of days to look back
            
        Returns:
            Dict with insights and metrics
        """
        if not self.influx_client:
            return {"error": "InfluxDB not available"}
            
        try:
            query_api = self.influx_client.query_api()
            
            # Query reaction events
            flux_query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: -{days}d)
                |> filter(fn: (r) => r["_measurement"] == "reaction_event")
                |> filter(fn: (r) => r["user_id"] == "{user_id}")
            '''
            
            tables = query_api.query(flux_query)
            
            reactions_by_message = {}
            for table in tables:
                for record in table.records:
                    msg_id = record.values.get("message_id")
                    reaction = record.values.get("reaction")
                    msg_length = record.values.get("message_length", 0)
                    
                    if msg_id not in reactions_by_message:
                        reactions_by_message[msg_id] = {
                            "reactions": [],
                            "length": msg_length
                        }
                    reactions_by_message[msg_id]["reactions"].append(reaction)
            
            # Analyze patterns
            insights = {
                "total_reactions": sum(len(m["reactions"]) for m in reactions_by_message.values()),
                "positive_ratio": 0.0,
                "verbosity_preference": "unknown",
                "recommendations": []
            }
            
            if not reactions_by_message:
                return insights
            
            # Calculate positive ratio
            all_reactions = []
            for msg_data in reactions_by_message.values():
                all_reactions.extend(msg_data["reactions"])
            
            positive_count = sum(1 for r in all_reactions if r in self.POSITIVE_REACTIONS)
            negative_count = sum(1 for r in all_reactions if r in self.NEGATIVE_REACTIONS)
            total = positive_count + negative_count
            
            if total > 0:
                insights["positive_ratio"] = positive_count / total
            
            # Analyze verbosity preference
            long_messages = [m for m in reactions_by_message.values() if m["length"] > 500]
            short_messages = [m for m in reactions_by_message.values() if m["length"] <= 500]
            
            if long_messages:
                long_negative = sum(
                    1 for m in long_messages 
                    if any(r in self.NEGATIVE_REACTIONS for r in m["reactions"])
                )
                if long_negative / len(long_messages) > 0.6:
                    insights["verbosity_preference"] = "concise"
                    insights["recommendations"].append("User prefers shorter responses")
            
            if short_messages:
                short_positive = sum(
                    1 for m in short_messages 
                    if any(r in self.POSITIVE_REACTIONS for r in m["reactions"])
                )
                if short_positive / len(short_messages) > 0.6:
                    insights["verbosity_preference"] = "concise"
                    insights["recommendations"].append("User appreciates concise communication")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze feedback patterns: {e}")
            return {"error": str(e)}

    async def log_reaction_to_influx(
        self, 
        user_id: str, 
        message_id: str, 
        reaction: str, 
        bot_name: str,
        message_length: int = 0
    ):
        """
        Logs a reaction event to InfluxDB for later analysis.
        
        This should be called from the bot's on_reaction_add event handler.
        """
        if not db_manager.influxdb_write_api:
            return
            
        try:
            point = Point("reaction_event") \
                .tag("user_id", user_id) \
                .tag("bot_name", bot_name) \
                .tag("message_id", message_id) \
                .field("reaction", reaction) \
                .field("message_length", message_length) \
                .time(datetime.utcnow())
            
            db_manager.influxdb_write_api.write(
                bucket=settings.INFLUXDB_BUCKET, 
                record=point
            )
            
            logger.debug(f"Logged reaction {reaction} to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to log reaction to InfluxDB: {e}")


# Global singleton
feedback_analyzer = FeedbackAnalyzer()
