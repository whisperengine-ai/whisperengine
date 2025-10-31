"""
Context Switch Engine - Strategic Intelligence Engine 4/7

Analyzes conversation topic transitions and context changes:
- Detects when users switch topics/contexts in conversation history
- Identifies common transition patterns
- Measures topic duration and switch frequency
- Predicts context switch likelihood

This replaces the removed hot path context switch detection (message_processor.py line 4617).
Strategic analysis informs adaptive conversation strategies.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ContextSwitchEngine:
    """
    Analyzes conversation context switches and topic transitions.
    
    Detects and analyzes:
    - Topic changes in conversation flow
    - Context switch frequency patterns
    - Average topic duration
    - Common transition types (gradual vs abrupt)
    - Switch likelihood prediction
    """
    
    def __init__(self, qdrant_client):
        """
        Initialize the Context Switch Engine.
        
        Args:
            qdrant_client: QdrantClient for querying conversations directly
        """
        self.qdrant_client = qdrant_client
    
    async def analyze_context_switches(
        self,
        bot_name: str,
        user_id: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze context switch patterns in conversation history.
        
        Args:
            bot_name: Name of the bot/character
            user_id: User ID to analyze
            lookback_days: Days to look back for conversation data
            
        Returns:
            Dict containing context switch analysis and patterns
        """
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get conversation history
            conversations = await self._get_conversation_history(
                bot_name, user_id, start_time, end_time
            )
            
            if not conversations or len(conversations) < 3:
                logger.info(f"Insufficient conversation history for context analysis: {bot_name}/{user_id}")
                return self._empty_context_result(bot_name, user_id)
            
            # Detect context switches in conversation flow
            switches = await self._detect_context_switches(conversations)
            
            # Analyze switch patterns
            switch_patterns = self._analyze_switch_patterns(switches, conversations)
            
            # Calculate topic durations
            topic_durations = self._calculate_topic_durations(switches, conversations)
            
            # Identify common transitions
            transition_types = self._classify_transition_types(switches, conversations)
            
            # Predict switch likelihood
            switch_prediction = self._predict_switch_likelihood(switch_patterns, topic_durations)
            
            return {
                "bot_name": bot_name,
                "user_id": user_id,
                "lookback_days": lookback_days,
                "analyzed_at": end_time.isoformat(),
                "conversation_count": len(conversations),
                "switch_count": len(switches),
                "switches": switches,
                "switch_patterns": switch_patterns,
                "topic_durations": topic_durations,
                "transition_types": transition_types,
                "switch_prediction": switch_prediction,
                "analysis_confidence": self._calculate_confidence(len(conversations), len(switches))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing context switches for {bot_name}/{user_id}: {e}")
            return self._empty_context_result(bot_name, user_id)
    
    async def _get_conversation_history(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get chronologically ordered conversation history."""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            collection_name = f"whisperengine_memory_{bot_name}"
            
            logger.debug(f"Querying conversation history for context analysis: {bot_name}/{user_id}")
            
            # Query Qdrant for user's conversation history via qdrant_client
            search_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation"))
                    ]
                ),
                limit=500,
                with_payload=True,
                with_vectors=False
            )
            
            # Extract payloads and filter by timestamp
            conversations = []
            for point in search_result[0]:
                payload = point.payload
                if payload:
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
            
            # Sort chronologically for context analysis
            conversations.sort(key=lambda x: x.get('timestamp', ''))
            
            logger.debug(f"Retrieved {len(conversations)} conversations for context analysis")
            return conversations
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def _detect_context_switches(
        self,
        conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect context switches in conversation flow.
        
        A context switch is detected when:
        - Topic changes significantly between messages
        - User introduces new subject matter
        - Conversation mode shifts (analytical → emotional, etc.)
        
        Returns:
            List of detected switches with metadata
        """
        try:
            switches = []
            
            # Analyze user messages only (user initiates context switches)
            user_messages = [msg for msg in conversations if msg.get("role") == "user"]
            
            if len(user_messages) < 2:
                return switches
            
            # Analyze consecutive message pairs for topic shifts
            for i in range(1, len(user_messages)):
                prev_msg = user_messages[i - 1]
                curr_msg = user_messages[i]
                
                # Detect switch using multiple signals
                switch_detected, confidence, switch_type = self._detect_switch_between_messages(
                    prev_msg, curr_msg
                )
                
                if switch_detected:
                    switches.append({
                        "switch_index": i,
                        "timestamp": curr_msg.get("timestamp"),
                        "prev_content": prev_msg.get("content", "")[:100],  # First 100 chars
                        "new_content": curr_msg.get("content", "")[:100],
                        "confidence": confidence,
                        "switch_type": switch_type,
                        "prev_emotion": prev_msg.get("metadata", {}).get("emotion"),
                        "new_emotion": curr_msg.get("metadata", {}).get("emotion")
                    })
            
            return switches
            
        except Exception as e:
            logger.error(f"Error detecting context switches: {e}")
            return []
    
    def _detect_switch_between_messages(
        self,
        prev_msg: Dict[str, Any],
        curr_msg: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect if a context switch occurred between two messages.
        
        Returns:
            Tuple of (switch_detected, confidence, switch_type)
        """
        try:
            prev_content = prev_msg.get("content", "").lower()
            curr_content = curr_msg.get("content", "").lower()
            
            # Signal 1: Explicit transition phrases
            transition_phrases = [
                "by the way", "btw", "anyway", "speaking of", "also",
                "changing topic", "different topic", "quick question",
                "off topic", "unrelated", "moving on"
            ]
            
            has_transition_phrase = any(phrase in curr_content for phrase in transition_phrases)
            
            # Signal 2: Question after statement or vice versa
            prev_is_question = "?" in prev_content
            curr_is_question = "?" in curr_content
            question_type_change = prev_is_question != curr_is_question
            
            # Signal 3: Emotional shift
            prev_emotion = prev_msg.get("metadata", {}).get("emotion", "neutral")
            curr_emotion = curr_msg.get("metadata", {}).get("emotion", "neutral")
            
            # Define emotional distance (simplified)
            emotion_categories = {
                "analytical": ["curiosity", "interest"],
                "positive": ["joy", "love", "optimism", "trust"],
                "negative": ["anger", "fear", "sadness", "disgust"],
                "neutral": ["surprise", "anticipation", "neutral"]
            }
            
            prev_category = self._get_emotion_category(prev_emotion, emotion_categories)
            curr_category = self._get_emotion_category(curr_emotion, emotion_categories)
            
            emotional_shift = prev_category != curr_category
            
            # Signal 4: Word overlap (low overlap suggests topic change)
            prev_words = set(prev_content.split())
            curr_words = set(curr_content.split())
            
            # Remove common words
            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            prev_words -= common_words
            curr_words -= common_words
            
            if prev_words and curr_words:
                overlap = len(prev_words & curr_words) / min(len(prev_words), len(curr_words))
            else:
                overlap = 0.0
            
            low_word_overlap = overlap < 0.3
            
            # Determine switch detection
            switch_signals = [
                has_transition_phrase,
                emotional_shift and not question_type_change,  # Emotion shift without Q/A pattern
                low_word_overlap and len(curr_content) > 20  # Topic change with substantial content
            ]
            
            signal_count = sum(switch_signals)
            
            # Detect switch if multiple signals present
            switch_detected = signal_count >= 2
            
            # Calculate confidence
            confidence = signal_count / 3.0
            
            # Classify switch type
            if has_transition_phrase:
                switch_type = "explicit"  # User explicitly signals topic change
            elif emotional_shift and low_word_overlap:
                switch_type = "abrupt"  # Sudden shift without transition
            elif low_word_overlap:
                switch_type = "gradual"  # Smooth transition to new topic
            else:
                switch_type = "none"
            
            return switch_detected, confidence, switch_type
            
        except Exception as e:
            logger.error(f"Error detecting switch between messages: {e}")
            return False, 0.0, "none"
    
    def _get_emotion_category(
        self,
        emotion: str,
        categories: Dict[str, List[str]]
    ) -> str:
        """Get broad category for an emotion."""
        for category, emotions in categories.items():
            if emotion in emotions:
                return category
        return "neutral"
    
    def _analyze_switch_patterns(
        self,
        switches: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in context switches.
        
        Returns:
            Dict with switch frequency, patterns, and insights
        """
        try:
            if not switches:
                return {
                    "switch_frequency": 0.0,
                    "avg_messages_between_switches": 0,
                    "most_common_switch_type": "none",
                    "pattern": "no_switches"
                }
            
            user_message_count = len([m for m in conversations if m.get("role") == "user"])
            
            # Calculate switch frequency (switches per 10 messages)
            switch_frequency = (len(switches) / user_message_count) * 10 if user_message_count > 0 else 0.0
            
            # Average messages between switches
            avg_messages_between = user_message_count / (len(switches) + 1) if switches else 0
            
            # Most common switch type
            switch_types = [s.get("switch_type", "none") for s in switches]
            if switch_types:
                most_common = max(set(switch_types), key=switch_types.count)
            else:
                most_common = "none"
            
            # Classify pattern
            if switch_frequency > 5:
                pattern = "highly_dynamic"  # Frequent topic changes
            elif switch_frequency > 2:
                pattern = "moderately_dynamic"
            elif switch_frequency > 0.5:
                pattern = "focused_with_transitions"
            else:
                pattern = "highly_focused"
            
            return {
                "switch_frequency": round(switch_frequency, 2),
                "avg_messages_between_switches": round(avg_messages_between, 1),
                "most_common_switch_type": most_common,
                "pattern": pattern,
                "switch_type_distribution": {
                    "explicit": switch_types.count("explicit"),
                    "abrupt": switch_types.count("abrupt"),
                    "gradual": switch_types.count("gradual")
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing switch patterns: {e}")
            return {
                "switch_frequency": 0.0,
                "avg_messages_between_switches": 0,
                "most_common_switch_type": "none",
                "pattern": "unknown"
            }
    
    def _calculate_topic_durations(
        self,
        switches: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate average topic duration between switches.
        
        Returns:
            Dict with duration metrics
        """
        try:
            if not switches or len(switches) < 2:
                return {
                    "avg_topic_duration_messages": 0,
                    "min_duration": 0,
                    "max_duration": 0
                }
            
            # Calculate messages between each switch
            durations = []
            prev_index = 0
            
            for switch in switches:
                switch_index = switch.get("switch_index", 0)
                duration = switch_index - prev_index
                durations.append(duration)
                prev_index = switch_index
            
            # Add final segment duration
            user_messages = [m for m in conversations if m.get("role") == "user"]
            final_duration = len(user_messages) - prev_index
            durations.append(final_duration)
            
            if durations:
                return {
                    "avg_topic_duration_messages": round(sum(durations) / len(durations), 1),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "duration_distribution": durations
                }
            else:
                return {
                    "avg_topic_duration_messages": 0,
                    "min_duration": 0,
                    "max_duration": 0
                }
            
        except Exception as e:
            logger.error(f"Error calculating topic durations: {e}")
            return {
                "avg_topic_duration_messages": 0,
                "min_duration": 0,
                "max_duration": 0
            }
    
    def _classify_transition_types(
        self,
        switches: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify types of transitions in conversation.
        
        Returns:
            Dict with transition type analysis
        """
        try:
            if not switches:
                return {
                    "dominant_type": "none",
                    "transition_style": "no_transitions",
                    "explicit_ratio": 0.0
                }
            
            # Count transition types
            explicit_count = sum(1 for s in switches if s.get("switch_type") == "explicit")
            abrupt_count = sum(1 for s in switches if s.get("switch_type") == "abrupt")
            gradual_count = sum(1 for s in switches if s.get("switch_type") == "gradual")
            
            total_switches = len(switches)
            
            # Determine dominant type
            type_counts = {
                "explicit": explicit_count,
                "abrupt": abrupt_count,
                "gradual": gradual_count
            }
            dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
            
            # Classify transition style
            explicit_ratio = explicit_count / total_switches if total_switches > 0 else 0.0
            
            if explicit_ratio > 0.6:
                transition_style = "explicit_communicator"
            elif abrupt_count > gradual_count * 2:
                transition_style = "rapid_switcher"
            elif gradual_count > abrupt_count * 2:
                transition_style = "smooth_transitioner"
            else:
                transition_style = "mixed"
            
            return {
                "dominant_type": dominant_type,
                "transition_style": transition_style,
                "explicit_ratio": round(explicit_ratio, 3),
                "type_counts": type_counts
            }
            
        except Exception as e:
            logger.error(f"Error classifying transition types: {e}")
            return {
                "dominant_type": "none",
                "transition_style": "unknown",
                "explicit_ratio": 0.0
            }
    
    def _predict_switch_likelihood(
        self,
        switch_patterns: Dict[str, Any],
        topic_durations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict likelihood of context switch in future interactions.
        
        Returns:
            Dict with prediction metrics
        """
        try:
            switch_frequency = switch_patterns.get("switch_frequency", 0.0)
            avg_duration = topic_durations.get("avg_topic_duration_messages", 0)
            
            # Calculate switch likelihood (0.0 to 1.0)
            if switch_frequency == 0:
                likelihood = 0.1  # Low but non-zero
                pattern_desc = "User maintains focus on single topics"
            elif switch_frequency > 5:
                likelihood = 0.8  # High
                pattern_desc = "User frequently changes topics"
            elif switch_frequency > 2:
                likelihood = 0.6  # Moderate-high
                pattern_desc = "User switches topics regularly"
            else:
                likelihood = 0.3  # Moderate-low
                pattern_desc = "User occasionally switches topics"
            
            # Adjustment based on average duration
            if avg_duration > 0 and avg_duration < 3:
                likelihood += 0.1  # Short durations suggest higher switch likelihood
            
            # Cap at 1.0
            likelihood = min(likelihood, 1.0)
            
            return {
                "switch_likelihood": round(likelihood, 3),
                "prediction_confidence": 0.7 if switch_frequency > 1 else 0.4,
                "pattern_description": pattern_desc,
                "recommendation": self._generate_switch_recommendation(likelihood, switch_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error predicting switch likelihood: {e}")
            return {
                "switch_likelihood": 0.5,
                "prediction_confidence": 0.0,
                "pattern_description": "Unknown",
                "recommendation": "Insufficient data for prediction"
            }
    
    def _generate_switch_recommendation(
        self,
        likelihood: float,
        switch_patterns: Dict[str, Any]
    ) -> str:
        """Generate recommendation based on switch patterns."""
        pattern = switch_patterns.get("pattern", "unknown")
        
        if likelihood > 0.7:
            return "Be prepared for frequent topic changes; maintain contextual flexibility"
        elif likelihood > 0.5:
            return "User switches topics moderately; balance focus with adaptability"
        elif pattern == "highly_focused":
            return "User maintains topic focus; provide depth and continuity"
        else:
            return "Monitor for topic transitions; maintain conversational coherence"
    
    def _calculate_confidence(
        self,
        conversation_count: int,
        switch_count: int
    ) -> float:
        """
        Calculate confidence in context switch analysis.
        
        Args:
            conversation_count: Number of conversations analyzed
            switch_count: Number of switches detected
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Confidence increases with more data
        data_confidence = min(conversation_count / 20, 1.0)
        
        # Higher switch count provides better pattern analysis
        pattern_confidence = min(switch_count / 5, 1.0) if switch_count > 0 else 0.3
        
        # Weighted average
        return round((data_confidence * 0.6 + pattern_confidence * 0.4), 3)
    
    def _empty_context_result(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Return empty context analysis structure."""
        return {
            "bot_name": bot_name,
            "user_id": user_id,
            "lookback_days": 0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "conversation_count": 0,
            "switch_count": 0,
            "switches": [],
            "switch_patterns": {
                "switch_frequency": 0.0,
                "avg_messages_between_switches": 0,
                "most_common_switch_type": "none",
                "pattern": "insufficient_data"
            },
            "topic_durations": {
                "avg_topic_duration_messages": 0,
                "min_duration": 0,
                "max_duration": 0
            },
            "transition_types": {
                "dominant_type": "none",
                "transition_style": "insufficient_data",
                "explicit_ratio": 0.0
            },
            "switch_prediction": {
                "switch_likelihood": 0.5,
                "prediction_confidence": 0.0,
                "pattern_description": "Insufficient data",
                "recommendation": "Need more conversation history for analysis"
            },
            "analysis_confidence": 0.0
        }
