"""
Personality Profile Engine - Strategic Intelligence Engine 3/7

Analyzes user-bot interaction patterns to build personality profiles:
- Conversation style preferences (formal/casual, brief/detailed)
- Topic interests and preferences
- Communication patterns (question frequency, emotional expression)
- Interaction timing and frequency

This engine creates rich personality profiles that inform personalized bot responses.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class PersonalityProfileEngine:
    """
    Analyzes user personality and interaction patterns.
    
    Provides insights into:
    - Communication style (formal/casual, verbose/concise)
    - Topic preferences and interests
    - Emotional expression patterns
    - Interaction frequency and timing
    """
    
    def __init__(self, qdrant_client, temporal_client=None):
        """
        Initialize the Personality Profile Engine.
        
        Args:
            qdrant_client: QdrantClient for querying conversations
            temporal_client: Optional TemporalIntelligenceClient for InfluxDB queries
        """
        self.qdrant_client = qdrant_client
        self.temporal_client = temporal_client
    
    async def analyze_personality(
        self,
        bot_name: str,
        user_id: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze user personality profile based on conversation history.
        
        Args:
            bot_name: Name of the bot/character
            user_id: User ID to analyze
            lookback_days: Days to look back for conversation data
            
        Returns:
            Dict containing personality profile and insights
        """
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get conversation history from vector memory
            conversations = await self._get_conversation_history(
                bot_name, user_id, start_time, end_time
            )
            
            if not conversations:
                logger.info(f"No conversation history found for {bot_name}/{user_id}")
                return self._empty_profile_result(bot_name, user_id)
            
            # Analyze different personality dimensions in parallel
            analyses = await asyncio.gather(
                self._analyze_communication_style(conversations),
                self._analyze_topic_preferences(conversations),
                self._analyze_emotional_patterns(conversations),
                self._analyze_interaction_frequency(conversations, start_time, end_time),
                return_exceptions=True
            )
            
            # Unpack results with proper type handling
            communication_style = analyses[0] if isinstance(analyses[0], dict) else {}
            topic_preferences = analyses[1] if isinstance(analyses[1], dict) else {}
            emotional_patterns = analyses[2] if isinstance(analyses[2], dict) else {}
            interaction_freq = analyses[3] if isinstance(analyses[3], dict) else {}
            
            # Build comprehensive personality profile
            personality_profile = self._build_personality_profile(
                communication_style,
                topic_preferences,
                emotional_patterns,
                interaction_freq,
                len(conversations)
            )
            
            return {
                "bot_name": bot_name,
                "user_id": user_id,
                "lookback_days": lookback_days,
                "analyzed_at": end_time.isoformat(),
                "conversation_count": len(conversations),
                "communication_style": communication_style,
                "topic_preferences": topic_preferences,
                "emotional_patterns": emotional_patterns,
                "interaction_frequency": interaction_freq,
                "personality_profile": personality_profile,
                "profile_confidence": self._calculate_profile_confidence(len(conversations))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing personality for {bot_name}/{user_id}: {e}")
            return self._empty_profile_result(bot_name, user_id)
    
    async def _get_conversation_history(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get conversation history from vector memory."""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            collection_name = f"whisperengine_memory_{bot_name}"
            
            logger.debug(f"Querying conversation history for {bot_name}/{user_id} from {collection_name}")
            
            # Query Qdrant for user's conversation history via qdrant_client
            search_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation"))
                    ]
                ),
                limit=500,  # Fetch up to 500 conversations
                with_payload=True,
                with_vectors=False
            )
            
            # Extract payloads and filter by timestamp
            conversations = []
            for point in search_result[0]:
                payload = point.payload
                if payload:
                    # Parse timestamp and filter
                    timestamp_str = payload.get('timestamp', '')
                    if timestamp_str:
                        try:
                            msg_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            # Ensure timezone-aware comparison
                            if msg_time.tzinfo is None:
                                msg_time = msg_time.replace(tzinfo=timezone.utc)
                            if start_time <= msg_time <= end_time:
                                conversations.append(payload)
                        except (ValueError, AttributeError):
                            continue
            
            logger.debug(f"Retrieved {len(conversations)} conversations for {bot_name}/{user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def _analyze_communication_style(
        self,
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user's communication style from conversations.
        
        Returns:
            Dict with style metrics (formality, verbosity, question_frequency)
        """
        try:
            user_messages = [c for c in conversations if c.get("role") == "user"]
            
            if not user_messages:
                return {"formality": "unknown", "verbosity": "unknown", "style_confidence": 0.0}
            
            # Analyze message lengths
            message_lengths = [len(m.get("content", "")) for m in user_messages]
            avg_length = sum(message_lengths) / len(message_lengths)
            
            # Determine verbosity
            if avg_length < 50:
                verbosity = "concise"
            elif avg_length < 150:
                verbosity = "moderate"
            else:
                verbosity = "verbose"
            
            # Count questions
            question_count = sum(1 for m in user_messages if "?" in m.get("content", ""))
            question_freq = question_count / len(user_messages) if user_messages else 0.0
            
            # Analyze formality (simplified - could use NLP for better analysis)
            casual_indicators = ["lol", "haha", "yeah", "cool", "hey", "btw", "tbh"]
            formal_indicators = ["please", "thank you", "could you", "would you", "kindly"]
            
            casual_count = sum(
                1 for m in user_messages 
                for indicator in casual_indicators 
                if indicator in m.get("content", "").lower()
            )
            formal_count = sum(
                1 for m in user_messages 
                for indicator in formal_indicators 
                if indicator in m.get("content", "").lower()
            )
            
            if formal_count > casual_count * 2:
                formality = "formal"
            elif casual_count > formal_count * 2:
                formality = "casual"
            else:
                formality = "neutral"
            
            return {
                "formality": formality,
                "verbosity": verbosity,
                "avg_message_length": round(avg_length, 1),
                "question_frequency": round(question_freq, 3),
                "questions_per_10_messages": round(question_freq * 10, 1),
                "style_confidence": min(len(user_messages) / 10, 1.0)  # Higher confidence with more messages
            }
            
        except Exception as e:
            logger.error(f"Error analyzing communication style: {e}")
            return {"formality": "unknown", "verbosity": "unknown", "style_confidence": 0.0}
    
    async def _analyze_topic_preferences(
        self,
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user's topic preferences from conversation content.
        
        Returns:
            Dict with topic categories and preference scores
        """
        try:
            user_messages = [c for c in conversations if c.get("role") == "user"]
            
            if not user_messages:
                return {"primary_topics": [], "topic_diversity": 0.0, "confidence": 0.0}
            
            # Extract content
            all_content = " ".join(m.get("content", "") for m in user_messages).lower()
            
            # Define topic keywords (simplified - could use NLP topic modeling)
            topic_keywords = {
                "technology": ["computer", "software", "code", "program", "app", "tech", "digital"],
                "science": ["research", "study", "experiment", "theory", "scientific", "data"],
                "personal": ["feel", "think", "life", "experience", "personal", "my", "me"],
                "creative": ["art", "music", "create", "design", "creative", "imagine"],
                "learning": ["learn", "understand", "explain", "teach", "how", "why", "question"],
                "problem_solving": ["help", "problem", "solve", "fix", "issue", "solution"],
                "casual": ["chat", "talk", "conversation", "discuss", "share", "story"]
            }
            
            # Count topic mentions
            topic_scores = {}
            for topic, keywords in topic_keywords.items():
                score = sum(1 for keyword in keywords if keyword in all_content)
                if score > 0:
                    topic_scores[topic] = score
            
            # Rank topics by frequency
            sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
            primary_topics = [topic for topic, _ in sorted_topics[:3]]
            
            # Calculate topic diversity (how many different topics discussed)
            topic_diversity = len(topic_scores) / len(topic_keywords) if topic_keywords else 0.0
            
            return {
                "primary_topics": primary_topics,
                "topic_scores": dict(sorted_topics),
                "topic_diversity": round(topic_diversity, 3),
                "confidence": min(len(user_messages) / 20, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic preferences: {e}")
            return {"primary_topics": [], "topic_diversity": 0.0, "confidence": 0.0}
    
    async def _analyze_emotional_patterns(
        self,
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user's emotional expression patterns.
        
        Returns:
            Dict with emotional tendencies and patterns
        """
        try:
            user_messages = [c for c in conversations if c.get("role") == "user"]
            
            if not user_messages:
                return {"emotional_range": "unknown", "expressiveness": "low", "confidence": 0.0}
            
            # Extract emotions from metadata
            emotions = []
            for msg in user_messages:
                metadata = msg.get("metadata", {})
                if isinstance(metadata, dict):
                    emotion = metadata.get("emotion") or metadata.get("primary_emotion")
                    if emotion:
                        emotions.append(emotion)
            
            if not emotions:
                return {"emotional_range": "unknown", "expressiveness": "low", "confidence": 0.0}
            
            # Count emotion frequencies
            emotion_counts = Counter(emotions)
            most_common = emotion_counts.most_common(3)
            
            # Calculate emotional diversity
            unique_emotions = len(set(emotions))
            emotional_range = "narrow" if unique_emotions < 3 else "moderate" if unique_emotions < 6 else "wide"
            
            # Determine expressiveness based on emotion intensity presence
            expressiveness_indicators = ["!", "!!", "😊", "😢", "😡", "❤️", "🎉"]
            expressive_count = sum(
                1 for m in user_messages 
                for indicator in expressiveness_indicators 
                if indicator in m.get("content", "")
            )
            
            if expressive_count > len(user_messages) * 0.5:
                expressiveness = "high"
            elif expressive_count > len(user_messages) * 0.2:
                expressiveness = "moderate"
            else:
                expressiveness = "low"
            
            return {
                "emotional_range": emotional_range,
                "expressiveness": expressiveness,
                "primary_emotions": [emotion for emotion, _ in most_common],
                "emotion_distribution": dict(emotion_counts),
                "unique_emotion_count": unique_emotions,
                "confidence": min(len(emotions) / 15, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotional patterns: {e}")
            return {"emotional_range": "unknown", "expressiveness": "low", "confidence": 0.0}
    
    async def _analyze_interaction_frequency(
        self,
        conversations: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Analyze user's interaction frequency and timing patterns.
        
        Returns:
            Dict with frequency metrics and patterns
        """
        try:
            user_messages = [c for c in conversations if c.get("role") == "user"]
            
            if not user_messages:
                return {"frequency": "unknown", "pattern": "irregular", "confidence": 0.0}
            
            # Calculate time span
            time_span_days = (end_time - start_time).days
            if time_span_days == 0:
                time_span_days = 1
            
            # Calculate messages per day
            messages_per_day = len(user_messages) / time_span_days
            
            # Classify frequency
            if messages_per_day >= 5:
                frequency = "very_active"
            elif messages_per_day >= 2:
                frequency = "active"
            elif messages_per_day >= 0.5:
                frequency = "moderate"
            elif messages_per_day >= 0.1:
                frequency = "occasional"
            else:
                frequency = "rare"
            
            # Analyze timing pattern (simplified - could extract timestamps for detailed analysis)
            # For now, use message count distribution
            if len(user_messages) >= 7:
                # Check if messages are spread evenly or bursty
                # This is simplified - real implementation would analyze actual timestamps
                pattern = "regular" if messages_per_day > 0.5 else "irregular"
            else:
                pattern = "insufficient_data"
            
            return {
                "frequency": frequency,
                "pattern": pattern,
                "messages_per_day": round(messages_per_day, 2),
                "total_messages": len(user_messages),
                "time_span_days": time_span_days,
                "confidence": min(time_span_days / 30, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing interaction frequency: {e}")
            return {"frequency": "unknown", "pattern": "irregular", "confidence": 0.0}
    
    def _build_personality_profile(
        self,
        communication_style: Dict[str, Any],
        topic_preferences: Dict[str, Any],
        emotional_patterns: Dict[str, Any],
        interaction_freq: Dict[str, Any],
        conversation_count: int
    ) -> Dict[str, Any]:
        """
        Build comprehensive personality profile from component analyses.
        
        Returns:
            Dict with integrated personality insights
        """
        try:
            # Generate personality summary
            formality = communication_style.get("formality", "unknown")
            verbosity = communication_style.get("verbosity", "unknown")
            primary_topics = topic_preferences.get("primary_topics", [])
            emotional_range = emotional_patterns.get("emotional_range", "unknown")
            frequency = interaction_freq.get("frequency", "unknown")
            
            # Create personality description
            description_parts = []
            
            if formality != "unknown":
                description_parts.append(f"{formality} communicator")
            
            if verbosity != "unknown":
                description_parts.append(f"{verbosity} style")
            
            if primary_topics:
                topics_str = ", ".join(primary_topics[:2])
                description_parts.append(f"interested in {topics_str}")
            
            if emotional_range != "unknown":
                description_parts.append(f"{emotional_range} emotional expression")
            
            description = "; ".join(description_parts) if description_parts else "Profile being developed"
            
            # Identify behavioral traits
            traits = []
            
            if communication_style.get("question_frequency", 0) > 0.5:
                traits.append("inquisitive")
            
            if emotional_patterns.get("expressiveness") == "high":
                traits.append("expressive")
            
            if topic_preferences.get("topic_diversity", 0) > 0.5:
                traits.append("diverse_interests")
            
            if frequency in ["very_active", "active"]:
                traits.append("engaged")
            
            # Generate adaptation recommendations
            recommendations = []
            
            if formality == "formal":
                recommendations.append("Maintain professional tone and structure")
            elif formality == "casual":
                recommendations.append("Use conversational, friendly language")
            
            if verbosity == "concise":
                recommendations.append("Keep responses brief and focused")
            elif verbosity == "verbose":
                recommendations.append("Provide detailed explanations and examples")
            
            if emotional_patterns.get("expressiveness") == "high":
                recommendations.append("Match emotional engagement level")
            
            if primary_topics:
                recommendations.append(f"Reference {primary_topics[0]} topics when relevant")
            
            return {
                "description": description,
                "behavioral_traits": traits,
                "adaptation_recommendations": recommendations,
                "profile_maturity": self._calculate_profile_maturity(conversation_count),
                "key_insights": {
                    "communication": f"{formality}, {verbosity}",
                    "interests": ", ".join(primary_topics[:3]) if primary_topics else "developing",
                    "emotional_style": f"{emotional_range} range, {emotional_patterns.get('expressiveness', 'unknown')} expressiveness",
                    "engagement": frequency
                }
            }
            
        except Exception as e:
            logger.error(f"Error building personality profile: {e}")
            return {
                "description": "Profile analysis in progress",
                "behavioral_traits": [],
                "adaptation_recommendations": [],
                "profile_maturity": "developing",
                "key_insights": {}
            }
    
    def _calculate_profile_confidence(self, conversation_count: int) -> float:
        """
        Calculate overall confidence in personality profile.
        
        Args:
            conversation_count: Number of conversations analyzed
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Confidence increases with more conversations, plateaus at 50
        return min(conversation_count / 50, 1.0)
    
    def _calculate_profile_maturity(self, conversation_count: int) -> str:
        """
        Calculate profile maturity level.
        
        Args:
            conversation_count: Number of conversations analyzed
            
        Returns:
            Maturity level: "developing", "emerging", "established", "mature"
        """
        if conversation_count < 5:
            return "developing"
        elif conversation_count < 15:
            return "emerging"
        elif conversation_count < 30:
            return "established"
        else:
            return "mature"
    
    def _empty_profile_result(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Return empty personality profile structure."""
        return {
            "bot_name": bot_name,
            "user_id": user_id,
            "lookback_days": 0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "conversation_count": 0,
            "communication_style": {},
            "topic_preferences": {},
            "emotional_patterns": {},
            "interaction_frequency": {},
            "personality_profile": {
                "description": "Insufficient data for personality analysis",
                "behavioral_traits": [],
                "adaptation_recommendations": [],
                "profile_maturity": "insufficient_data",
                "key_insights": {}
            },
            "profile_confidence": 0.0
        }
