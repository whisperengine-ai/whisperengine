"""
Empathy Calibration System
=========================

Advanced system that learns and adapts to individual user emotional 
acknowledgment preferences using vector memory analysis for personalized 
empathetic responses.

Phase 3: Advanced Intelligence
"""

import logging
import os
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EmpathyStyle(Enum):
    """Different styles of empathetic response"""
    DIRECT_ACKNOWLEDGMENT = "direct_acknowledgment"  # "I understand you're frustrated"
    REFLECTIVE_LISTENING = "reflective_listening"    # "It sounds like you're feeling..."
    SOLUTION_FOCUSED = "solution_focused"            # "Let's work through this together"
    VALIDATION_FIRST = "validation_first"            # "Your feelings are completely valid"
    GENTLE_INQUIRY = "gentle_inquiry"                # "Would you like to tell me more?"
    SUPPORTIVE_PRESENCE = "supportive_presence"      # "I'm here for you"


class EmotionalResponseType(Enum):
    """Types of emotional responses to calibrate"""
    FRUSTRATION = "frustration"
    SADNESS = "sadness"
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    CONFUSION = "confusion"
    ANGER = "anger"
    JOY = "joy"
    STRESS = "stress"
    OVERWHELM = "overwhelm"
    CONTENTMENT = "contentment"


@dataclass
class EmpathyPreference:
    """User's preference for empathetic response style"""
    
    user_id: str
    emotion_type: EmotionalResponseType
    preferred_style: EmpathyStyle
    confidence_score: float  # 0.0 to 1.0
    response_effectiveness: float  # 0.0 to 1.0 based on user feedback
    last_positive_response: datetime
    interaction_count: int
    learned_from_interactions: List[str]
    metadata: Dict[str, Any]


@dataclass
class EmpathyCalibration:
    """Result of empathy calibration for a specific interaction"""
    
    calibration_id: str
    user_id: str
    detected_emotion: EmotionalResponseType
    recommended_style: EmpathyStyle
    confidence_score: float
    reasoning: str
    alternative_styles: List[EmpathyStyle]
    personalization_factors: Dict[str, Any]
    calibrated_at: datetime


class EmpathyCalibrator:
    """
    Advanced empathy calibration system that learns individual user 
    preferences for emotional acknowledgment and adapts responses accordingly.
    """
    
    def __init__(self, vector_memory_store=None):
        """Initialize the empathy calibrator"""
        self.vector_store = vector_memory_store
        
        # User preference tracking
        self.user_preferences = {}  # user_id -> Dict[EmotionalResponseType, EmpathyPreference]
        
        # Style effectiveness baselines
        self.baseline_effectiveness = {
            EmotionalResponseType.FRUSTRATION: {
                EmpathyStyle.VALIDATION_FIRST: 0.8,
                EmpathyStyle.DIRECT_ACKNOWLEDGMENT: 0.7,
                EmpathyStyle.SOLUTION_FOCUSED: 0.6
            },
            EmotionalResponseType.SADNESS: {
                EmpathyStyle.SUPPORTIVE_PRESENCE: 0.8,
                EmpathyStyle.REFLECTIVE_LISTENING: 0.7,
                EmpathyStyle.VALIDATION_FIRST: 0.6
            },
            EmotionalResponseType.ANXIETY: {
                EmpathyStyle.GENTLE_INQUIRY: 0.7,
                EmpathyStyle.SUPPORTIVE_PRESENCE: 0.8,
                EmpathyStyle.SOLUTION_FOCUSED: 0.6
            },
            EmotionalResponseType.EXCITEMENT: {
                EmpathyStyle.DIRECT_ACKNOWLEDGMENT: 0.8,
                EmpathyStyle.REFLECTIVE_LISTENING: 0.7,
                EmpathyStyle.VALIDATION_FIRST: 0.6
            }
        }
        
        # Learning parameters (configurable via environment)
        self.min_interactions_for_confidence = int(os.getenv("PHASE3_EMPATHY_MIN_INTERACTIONS", "3"))
        self.effectiveness_threshold = float(os.getenv("PHASE3_EMPATHY_EFFECTIVENESS_THRESHOLD", "0.6"))
        self.learning_rate = float(os.getenv("PHASE3_EMPATHY_LEARNING_RATE", "0.1"))
        self.confidence_threshold = float(os.getenv("PHASE3_EMPATHY_CONFIDENCE_THRESHOLD", "0.7"))
        
        logger.info(
            "Empathy Calibrator initialized with parameters: "
            "min_interactions=%s, effectiveness_threshold=%s, learning_rate=%s, confidence_threshold=%s",
            self.min_interactions_for_confidence, self.effectiveness_threshold,
            self.learning_rate, self.confidence_threshold
        )
    
    async def calibrate_empathy(
        self, 
        user_id: str, 
        detected_emotion: EmotionalResponseType,
        message_content: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> EmpathyCalibration:
        """
        Calibrate empathetic response style for user and detected emotion.
        
        Args:
            user_id: User identifier
            detected_emotion: Type of emotion detected
            message_content: User's message content
            conversation_context: Additional conversation context
            
        Returns:
            EmpathyCalibration with recommended style and reasoning
        """
        logger.debug("Calibrating empathy for user %s, emotion %s", user_id, detected_emotion.value)
        
        try:
            # Get or initialize user preferences
            await self._ensure_user_preferences(user_id)
            
            # Get user's preference for this emotion type
            user_preference = self.user_preferences[user_id].get(detected_emotion)
            
            # Analyze recent interaction patterns
            interaction_analysis = await self._analyze_recent_interactions(
                user_id, message_content
            )
            
            # Determine recommended style
            recommended_style, confidence, reasoning = await self._determine_optimal_style(
                detected_emotion, user_preference, interaction_analysis, conversation_context
            )
            
            # Get alternative styles
            alternatives = await self._get_alternative_styles(
                detected_emotion, recommended_style, user_preference
            )
            
            # Create calibration result
            calibration = EmpathyCalibration(
                calibration_id=f"empathy_{user_id}_{int(datetime.now(UTC).timestamp())}",
                user_id=user_id,
                detected_emotion=detected_emotion,
                recommended_style=recommended_style,
                confidence_score=confidence,
                reasoning=reasoning,
                alternative_styles=alternatives,
                personalization_factors=interaction_analysis,
                calibrated_at=datetime.now(UTC)
            )
            
            logger.debug("Empathy calibrated: %s style with %.2f confidence", 
                        recommended_style.value, confidence)
            
            return calibration
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error calibrating empathy: %s", e)
            # Return default calibration
            return self._create_default_calibration(user_id, detected_emotion)
    
    async def learn_from_response(
        self, 
        user_id: str, 
        emotion_type: EmotionalResponseType,
        used_style: EmpathyStyle,
        user_feedback_indicators: Dict[str, Any]
    ):
        """
        Learn from user response to empathetic style and update preferences.
        
        Args:
            user_id: User identifier
            emotion_type: Type of emotion that was addressed
            used_style: Empathy style that was used
            user_feedback_indicators: Indicators of response effectiveness
        """
        logger.debug("Learning from empathy response for user %s", user_id)
        
        try:
            # Ensure user preferences exist
            await self._ensure_user_preferences(user_id)
            
            # Calculate effectiveness score from feedback indicators
            effectiveness = self._calculate_response_effectiveness(user_feedback_indicators)
            
            # Update or create preference
            if emotion_type in self.user_preferences[user_id]:
                # Update existing preference
                preference = self.user_preferences[user_id][emotion_type]
                
                # Update effectiveness using moving average
                old_effectiveness = preference.response_effectiveness
                new_effectiveness = (
                    old_effectiveness * (1 - self.learning_rate) + 
                    effectiveness * self.learning_rate
                )
                
                preference.response_effectiveness = new_effectiveness
                preference.interaction_count += 1
                
                # Update preferred style if this one is more effective
                if (effectiveness > preference.response_effectiveness and 
                    preference.interaction_count >= self.min_interactions_for_confidence):
                    preference.preferred_style = used_style
                    preference.confidence_score = min(1.0, preference.confidence_score + 0.1)
                
                if effectiveness > self.effectiveness_threshold:
                    preference.last_positive_response = datetime.now(UTC)
                    preference.learned_from_interactions.append(
                        f"{used_style.value}: {effectiveness:.2f}"
                    )
                
            else:
                # Create new preference
                self.user_preferences[user_id][emotion_type] = EmpathyPreference(
                    user_id=user_id,
                    emotion_type=emotion_type,
                    preferred_style=used_style,
                    confidence_score=0.3,  # Start with low confidence
                    response_effectiveness=effectiveness,
                    last_positive_response=datetime.now(UTC) if effectiveness > self.effectiveness_threshold else datetime.min.replace(tzinfo=UTC),
                    interaction_count=1,
                    learned_from_interactions=[f"{used_style.value}: {effectiveness:.2f}"],
                    metadata={"learning_session": datetime.now(UTC).isoformat()}
                )
            
            # Store learning in vector memory for future analysis
            if self.vector_store:
                await self._store_empathy_learning(
                    user_id, emotion_type, used_style, effectiveness, user_feedback_indicators
                )
            
            logger.debug("Updated empathy preference for %s: %s style with %.2f effectiveness", 
                        emotion_type.value, used_style.value, effectiveness)
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error learning from empathy response: %s", e)
    
    async def get_user_empathy_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive empathy profile for user"""
        
        await self._ensure_user_preferences(user_id)
        
        profile = {
            "user_id": user_id,
            "preferences": {},
            "learning_stats": {
                "total_interactions": 0,
                "confident_preferences": 0,
                "last_learning_session": None
            },
            "style_effectiveness": {},
            "personality_indicators": {}
        }
        
        total_interactions = 0
        confident_count = 0
        latest_session = datetime.min.replace(tzinfo=UTC)
        
        for emotion_type, preference in self.user_preferences[user_id].items():
            profile["preferences"][emotion_type.value] = {
                "preferred_style": preference.preferred_style.value,
                "confidence": preference.confidence_score,
                "effectiveness": preference.response_effectiveness,
                "interaction_count": preference.interaction_count,
                "last_positive": preference.last_positive_response.isoformat()
            }
            
            total_interactions += preference.interaction_count
            if preference.confidence_score > 0.7:
                confident_count += 1
            
            if preference.last_positive_response > latest_session:
                latest_session = preference.last_positive_response
        
        profile["learning_stats"]["total_interactions"] = total_interactions
        profile["learning_stats"]["confident_preferences"] = confident_count
        profile["learning_stats"]["last_learning_session"] = latest_session.isoformat()
        
        # Analyze personality indicators from preferences
        profile["personality_indicators"] = await self._analyze_personality_indicators(user_id)
        
        return profile
    
    async def _ensure_user_preferences(self, user_id: str):
        """Ensure user preferences dictionary exists"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
    
    async def _analyze_recent_interactions(
        self, 
        user_id: str, 
        message_content: str
    ) -> Dict[str, Any]:
        """Analyze recent interactions to inform empathy calibration"""
        
        analysis = {
            "message_intensity": 0.5,
            "context_complexity": 0.5,
            "user_state_indicators": [],
            "recent_emotion_pattern": "stable",
            "interaction_frequency": "normal"
        }
        
        try:
            if self.vector_store:
                # Get recent emotional interactions
                recent_memories = await self.vector_store.get_conversation_history(
                    user_id=user_id,
                    limit=10
                )
                
                # Analyze message intensity
                analysis["message_intensity"] = self._calculate_message_intensity(message_content)
                
                # Analyze emotional pattern
                if recent_memories:
                    emotions = []
                    for memory in recent_memories:
                        metadata = memory.get('metadata', {})
                        if metadata.get('role') == 'user':
                            emotional_context = metadata.get('emotional_context', '')
                            if emotional_context:
                                emotions.append(emotional_context)
                    
                    if len(emotions) >= 3:
                        analysis["recent_emotion_pattern"] = self._analyze_emotion_pattern(emotions)
                
                # Analyze interaction frequency
                if len(recent_memories) > 0:
                    latest_time = recent_memories[0].get('timestamp', datetime.now(UTC).isoformat())
                    
                    # Handle string timestamps
                    if isinstance(latest_time, str):
                        try:
                            # Parse ISO format string and make timezone-aware
                            if 'T' in latest_time:
                                if '+' in latest_time or 'Z' in latest_time:
                                    # Already has timezone info
                                    latest_time = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                                else:
                                    # No timezone, assume UTC
                                    latest_time = datetime.fromisoformat(latest_time).replace(tzinfo=UTC)
                            else:
                                # Simple format, assume UTC
                                latest_time = datetime.fromisoformat(latest_time).replace(tzinfo=UTC)
                        except ValueError:
                            # Fallback to current time if parsing fails
                            latest_time = datetime.now(UTC)
                    elif isinstance(latest_time, datetime):
                        # Datetime object
                        if latest_time.tzinfo is None:
                            # If naive datetime, assume UTC
                            latest_time = latest_time.replace(tzinfo=UTC)
                    else:
                        # Fallback
                        latest_time = datetime.now(UTC)
                    
                    time_since_last = datetime.now(UTC) - latest_time
                    if time_since_last < timedelta(hours=1):
                        analysis["interaction_frequency"] = "high"
                    elif time_since_last > timedelta(days=1):
                        analysis["interaction_frequency"] = "low"
            
            return analysis
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error analyzing recent interactions: %s", e)
            return analysis
    
    async def _determine_optimal_style(
        self,
        emotion_type: EmotionalResponseType,
        user_preference: Optional[EmpathyPreference],
        interaction_analysis: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> tuple[EmpathyStyle, float, str]:
        """Determine optimal empathy style for current situation"""
        
        # Start with baseline or user preference
        if user_preference and user_preference.confidence_score > 0.5:
            recommended_style = user_preference.preferred_style
            confidence = user_preference.confidence_score
            reasoning = f"Based on learned preference from {user_preference.interaction_count} interactions"
        else:
            # Use baseline effectiveness
            baseline_styles = self.baseline_effectiveness.get(emotion_type, {})
            if baseline_styles:
                recommended_style = max(baseline_styles.items(), key=lambda x: x[1])[0]
                confidence = 0.6
                reasoning = "Using baseline effectiveness for emotion type"
            else:
                recommended_style = EmpathyStyle.SUPPORTIVE_PRESENCE
                confidence = 0.4
                reasoning = "Using default supportive presence style"
        
        # Adjust based on interaction analysis
        message_intensity = interaction_analysis.get("message_intensity", 0.5)
        emotion_pattern = interaction_analysis.get("recent_emotion_pattern", "stable")
        
        # High intensity messages may need different approach
        if message_intensity > 0.8:
            if recommended_style == EmpathyStyle.GENTLE_INQUIRY:
                recommended_style = EmpathyStyle.DIRECT_ACKNOWLEDGMENT
                reasoning += " (adjusted for high intensity)"
                confidence *= 0.9
        
        # Frequent emotional volatility may need validation-first approach
        if emotion_pattern == "volatile":
            if recommended_style not in [EmpathyStyle.VALIDATION_FIRST, EmpathyStyle.SUPPORTIVE_PRESENCE]:
                recommended_style = EmpathyStyle.VALIDATION_FIRST
                reasoning += " (adjusted for emotional volatility)"
                confidence *= 0.8
        
        # Context-specific adjustments
        if conversation_context:
            conversation_mode = conversation_context.get("conversation_mode", "casual")
            if conversation_mode == "problem_solving" and recommended_style != EmpathyStyle.SOLUTION_FOCUSED:
                recommended_style = EmpathyStyle.SOLUTION_FOCUSED
                reasoning += " (adjusted for problem-solving context)"
        
        return recommended_style, min(1.0, confidence), reasoning
    
    async def _get_alternative_styles(
        self,
        emotion_type: EmotionalResponseType,
        primary_style: EmpathyStyle,
        user_preference: Optional[EmpathyPreference]
    ) -> List[EmpathyStyle]:
        """Get alternative empathy styles for the emotion type"""
        
        # Get baseline alternatives
        baseline_styles = self.baseline_effectiveness.get(emotion_type, {})
        alternatives = [style for style in baseline_styles.keys() if style != primary_style]
        
        # Sort by effectiveness
        alternatives.sort(key=lambda s: baseline_styles.get(s, 0.0), reverse=True)
        
        # Add user's historical preferences if different
        if (user_preference and 
            user_preference.preferred_style != primary_style and 
            user_preference.preferred_style not in alternatives):
            alternatives.insert(0, user_preference.preferred_style)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def _calculate_response_effectiveness(self, feedback_indicators: Dict[str, Any]) -> float:
        """Calculate effectiveness score from user feedback indicators"""
        
        effectiveness = 0.5  # baseline
        
        # Positive indicators
        if feedback_indicators.get("continued_conversation", False):
            effectiveness += 0.2
        
        if feedback_indicators.get("emotional_de_escalation", False):
            effectiveness += 0.3
        
        if feedback_indicators.get("expressed_gratitude", False):
            effectiveness += 0.2
        
        if feedback_indicators.get("shared_more_details", False):
            effectiveness += 0.1
        
        if feedback_indicators.get("positive_sentiment_shift", False):
            effectiveness += 0.3
        
        # Negative indicators
        if feedback_indicators.get("conversation_ended_abruptly", False):
            effectiveness -= 0.4
        
        if feedback_indicators.get("repeated_frustration", False):
            effectiveness -= 0.3
        
        if feedback_indicators.get("requested_different_response", False):
            effectiveness -= 0.2
        
        if feedback_indicators.get("emotional_escalation", False):
            effectiveness -= 0.4
        
        return max(0.0, min(1.0, effectiveness))
    
    def _calculate_message_intensity(self, message: str) -> float:
        """Calculate emotional intensity of message"""
        
        intensity = 0.3  # baseline
        message_lower = message.lower()
        
        # Intensity indicators
        high_intensity_words = [
            "extremely", "completely", "totally", "absolutely", "devastated",
            "furious", "overwhelmed", "exhausted", "terrified", "ecstatic"
        ]
        
        medium_intensity_words = [
            "really", "very", "quite", "pretty", "frustrated", "worried",
            "excited", "upset", "happy", "concerned"
        ]
        
        # Check for intensity words
        for word in high_intensity_words:
            if word in message_lower:
                intensity += 0.3
        
        for word in medium_intensity_words:
            if word in message_lower:
                intensity += 0.1
        
        # Punctuation indicators
        if "!" in message:
            intensity += 0.1 * message.count("!")
        
        if message.isupper():
            intensity += 0.4
        
        # Length and repetition
        if len(message) > 200:
            intensity += 0.1
        
        # Word repetition
        words = message_lower.split()
        if len(words) > len(set(words)) * 1.5:  # Significant repetition
            intensity += 0.2
        
        return min(1.0, intensity)
    
    def _analyze_emotion_pattern(self, emotions: List[str]) -> str:
        """Analyze pattern in recent emotions"""
        
        if len(emotions) < 3:
            return "stable"
        
        # Simple pattern analysis
        emotion_values = []
        emotion_map = {
            "very_positive": 2, "positive": 1, "neutral": 0,
            "negative": -1, "very_negative": -2,
            "anxious": -1, "contemplative": 0
        }
        
        for emotion in emotions[:5]:  # Last 5 emotions
            emotion_values.append(emotion_map.get(emotion, 0))
        
        if len(emotion_values) >= 3:
            # Calculate variance
            variance = statistics.variance(emotion_values) if len(emotion_values) > 1 else 0
            
            if variance > 2.0:
                return "volatile"
            elif variance < 0.5:
                return "stable"
            else:
                return "variable"
        
        return "stable"
    
    async def _store_empathy_learning(
        self,
        user_id: str,
        emotion_type: EmotionalResponseType,
        used_style: EmpathyStyle,
        effectiveness: float,
        feedback_indicators: Dict[str, Any]
    ):
        """Store empathy learning data in vector memory"""
        
        try:
            learning_data = {
                "user_id": user_id,
                "emotion_type": emotion_type.value,
                "empathy_style": used_style.value,
                "effectiveness": effectiveness,
                "feedback_indicators": feedback_indicators,
                "timestamp": datetime.now(UTC).isoformat(),
                "learning_type": "empathy_calibration"
            }
            
            if self.vector_store:
                await self.vector_store.store_conversation(
                    user_id=user_id,
                    user_message=f"Empathy learning: {emotion_type.value} -> {used_style.value}",
                    bot_response=f"Effectiveness: {effectiveness:.2f}",
                    metadata=learning_data
                )
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error storing empathy learning: %s", e)
    
    async def _analyze_personality_indicators(self, user_id: str) -> Dict[str, Any]:
        """Analyze personality indicators from empathy preferences"""
        
        indicators = {
            "response_preference": "balanced",
            "emotional_processing_style": "moderate",
            "support_seeking_pattern": "normal",
            "communication_style": "adaptive"
        }
        
        if user_id not in self.user_preferences:
            return indicators
        
        preferences = self.user_preferences[user_id]
        
        # Analyze preferred styles across emotions
        style_counts = {}
        for preference in preferences.values():
            style = preference.preferred_style
            style_counts[style] = style_counts.get(style, 0) + 1
        
        if style_counts:
            most_common_style = max(style_counts.items(), key=lambda x: x[1])[0]
            
            # Map styles to personality indicators
            if most_common_style == EmpathyStyle.DIRECT_ACKNOWLEDGMENT:
                indicators["response_preference"] = "direct"
                indicators["communication_style"] = "straightforward"
            elif most_common_style == EmpathyStyle.VALIDATION_FIRST:
                indicators["emotional_processing_style"] = "validation_seeking"
                indicators["support_seeking_pattern"] = "high"
            elif most_common_style == EmpathyStyle.SOLUTION_FOCUSED:
                indicators["response_preference"] = "action_oriented"
                indicators["communication_style"] = "pragmatic"
            elif most_common_style == EmpathyStyle.REFLECTIVE_LISTENING:
                indicators["emotional_processing_style"] = "introspective"
                indicators["communication_style"] = "thoughtful"
        
        return indicators
    
    def _create_default_calibration(
        self, 
        user_id: str, 
        emotion_type: EmotionalResponseType
    ) -> EmpathyCalibration:
        """Create default calibration when analysis fails"""
        
        return EmpathyCalibration(
            calibration_id=f"default_{user_id}_{int(datetime.now(UTC).timestamp())}",
            user_id=user_id,
            detected_emotion=emotion_type,
            recommended_style=EmpathyStyle.SUPPORTIVE_PRESENCE,
            confidence_score=0.3,
            reasoning="Default supportive style due to analysis error",
            alternative_styles=[EmpathyStyle.VALIDATION_FIRST, EmpathyStyle.GENTLE_INQUIRY],
            personalization_factors={},
            calibrated_at=datetime.now(UTC)
        )