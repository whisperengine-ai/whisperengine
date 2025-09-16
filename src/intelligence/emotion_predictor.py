"""
Emotion Pattern Recognition Engine
=================================

Advanced emotional intelligence system that learns from historical emotional patterns
to predict future emotional states and provide proactive support.

Phase 2: Predictive Emotional Intelligence
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import re
import spacy
from collections import defaultdict, Counter
import numpy as np

logger = logging.getLogger(__name__)


class EmotionalTriggerType(Enum):
    TOPIC_BASED = "topic_based"
    TIME_BASED = "time_based"
    SOCIAL_CONTEXT = "social_context"
    WORKLOAD_STRESS = "workload_stress"
    COMMUNICATION_STYLE = "communication_style"
    EXTERNAL_EVENTS = "external_events"


class EmotionalPattern(Enum):
    DAILY_CYCLE = "daily_cycle"
    WEEKLY_CYCLE = "weekly_cycle"
    STRESS_BUILDUP = "stress_buildup"
    RECOVERY_PATTERN = "recovery_pattern"
    TRIGGER_RESPONSE = "trigger_response"


@dataclass
class EmotionalPrediction:
    """Prediction of future emotional state"""

    predicted_emotion: str
    confidence: float
    time_horizon: str  # "immediate", "short_term", "medium_term"
    triggering_factors: List[str]
    recommended_actions: List[str]
    risk_level: str  # "low", "medium", "high"


@dataclass
class EmotionalCycle:
    """Detected emotional cycle pattern"""

    pattern_type: EmotionalPattern
    cycle_length: str  # "hourly", "daily", "weekly"
    peak_times: List[str]
    low_times: List[str]
    confidence: float
    sample_size: int


@dataclass
class EmotionalTrigger:
    """Identified emotional trigger"""

    trigger_type: EmotionalTriggerType
    trigger_description: str
    triggered_emotion: str
    response_intensity: float
    recovery_time: str
    frequency: int
    confidence: float


class EmotionPredictor:
    """Advanced emotion prediction and pattern recognition"""

    def __init__(self):
        """Initialize the emotion predictor"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model not found. Please install: python -m spacy download en_core_web_sm"
            )
            raise

        self.prediction_confidence_threshold = 0.7
        self.pattern_detection_min_samples = 3  # Changed from 5 to 3 - we need fewer turns since these are conversation turns, not separate conversations

        # Emotional vocabulary mapping
        self._emotion_keywords = {
            "stress": [
                "stressed",
                "overwhelmed",
                "pressure",
                "deadline",
                "busy",
                "exhausted",
                "tired",
            ],
            "anxiety": [
                "worried",
                "anxious",
                "nervous",
                "concerned",
                "scared",
                "afraid",
                "uncertain",
            ],
            "frustration": [
                "frustrated",
                "annoyed",
                "irritated",
                "angry",
                "mad",
                "upset",
                "bothered",
            ],
            "sadness": ["sad", "down", "depressed", "disappointed", "low", "blue", "unhappy"],
            "excitement": [
                "excited",
                "thrilled",
                "amazing",
                "awesome",
                "fantastic",
                "incredible",
                "wonderful",
            ],
            "joy": ["happy", "glad", "joyful", "pleased", "delighted", "cheerful", "content"],
            "confidence": [
                "confident",
                "sure",
                "certain",
                "ready",
                "prepared",
                "capable",
                "strong",
            ],
            "confusion": [
                "confused",
                "lost",
                "unclear",
                "puzzled",
                "unsure",
                "don't understand",
                "mixed up",
            ],
        }

        # Stress indicator patterns
        self._stress_indicators = {
            "linguistic": [
                r"\b(help|urgent|asap|quickly|immediately)\b",
                r"\b(can\'t|cannot|won\'t|impossible)\b",
                r"\b(too much|overload|overwhelm)\b",
                r"[.]{3,}|[!]{2,}",  # Multiple punctuation
            ],
            "temporal": ["deadline", "due", "running out", "late", "behind schedule"],
            "emotional_escalation": [
                "really really",
                "so so",
                "very very",
                "extremely",
                "incredibly",
            ],
        }

        # Recovery pattern indicators
        self._recovery_indicators = {
            "positive_shift": ["better", "improving", "getting there", "making progress"],
            "resolution": ["solved", "figured out", "resolved", "fixed", "working now"],
            "support_acknowledgment": ["thanks", "helpful", "appreciate", "grateful"],
            "energy_return": ["ready", "let's go", "excited again", "back on track"],
        }

    async def analyze_emotional_patterns(
        self, user_id: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze historical emotional patterns for prediction

        Args:
            user_id: User identifier
            conversation_history: List of conversation records with timestamps and emotions

        Returns:
            Comprehensive emotional pattern analysis
        """
        logger.info(
            f"Analyzing emotional patterns for user {user_id} with {len(conversation_history)} conversation turns"
        )

        if len(conversation_history) < self.pattern_detection_min_samples:
            logger.debug(
                f"Insufficient conversation turns for pattern analysis: {len(conversation_history)} turns (need {self.pattern_detection_min_samples})"
            )
            return {
                "error": "insufficient_data",
                "required_minimum": self.pattern_detection_min_samples,
            }

        analysis = {
            "emotional_cycles": await self._detect_emotional_cycles(conversation_history),
            "trigger_patterns": await self._analyze_trigger_patterns(conversation_history),
            "recovery_patterns": await self._analyze_recovery_patterns(conversation_history),
            "stress_indicators": await self._detect_stress_patterns(conversation_history),
            "emotional_trajectory": await self._predict_emotional_trajectory(conversation_history),
            "conversation_timing_patterns": await self._analyze_conversation_timing(
                conversation_history
            ),
            "emotional_volatility": await self._calculate_emotional_volatility(
                conversation_history
            ),
        }

        logger.debug(
            f"Emotional pattern analysis complete for {user_id}: {len(analysis)} pattern types detected"
        )
        return analysis

    async def _detect_emotional_cycles(self, history: List[Dict]) -> List[EmotionalCycle]:
        """Detect daily/weekly emotional patterns"""
        cycles = []

        # Group conversations by time patterns
        hourly_emotions = defaultdict(list)
        daily_emotions = defaultdict(list)

        for conv in history:
            if "timestamp" in conv and "emotion" in conv:
                try:
                    timestamp = datetime.fromisoformat(conv["timestamp"].replace("Z", "+00:00"))
                    hour = timestamp.hour
                    day = timestamp.strftime("%A")

                    hourly_emotions[hour].append(conv["emotion"])
                    daily_emotions[day].append(conv["emotion"])
                except (ValueError, AttributeError):
                    continue

        # Detect daily emotional cycles (by hour)
        if len(hourly_emotions) >= 3:
            emotion_by_hour = {}
            for hour, emotions in hourly_emotions.items():
                if len(emotions) >= 2:  # Need multiple samples
                    # Calculate dominant emotion for this hour
                    emotion_counts = Counter(emotions)
                    dominant_emotion = emotion_counts.most_common(1)[0][0]
                    emotion_by_hour[hour] = dominant_emotion

            if len(emotion_by_hour) >= 3:
                # Find peak emotional times
                positive_emotions = ["joy", "excitement", "confidence"]
                negative_emotions = ["stress", "anxiety", "frustration", "sadness"]

                peak_times = [
                    str(hour)
                    for hour, emotion in emotion_by_hour.items()
                    if emotion in positive_emotions
                ]
                low_times = [
                    str(hour)
                    for hour, emotion in emotion_by_hour.items()
                    if emotion in negative_emotions
                ]

                cycles.append(
                    EmotionalCycle(
                        pattern_type=EmotionalPattern.DAILY_CYCLE,
                        cycle_length="daily",
                        peak_times=peak_times,
                        low_times=low_times,
                        confidence=min(0.9, len(emotion_by_hour) / 24.0),
                        sample_size=len(emotion_by_hour),
                    )
                )

        # Detect weekly patterns
        if len(daily_emotions) >= 3:
            emotion_by_day = {}
            for day, emotions in daily_emotions.items():
                if len(emotions) >= 2:
                    emotion_counts = Counter(emotions)
                    dominant_emotion = emotion_counts.most_common(1)[0][0]
                    emotion_by_day[day] = dominant_emotion

            if len(emotion_by_day) >= 3:
                positive_emotions = ["joy", "excitement", "confidence"]
                negative_emotions = ["stress", "anxiety", "frustration"]

                peak_days = [
                    day for day, emotion in emotion_by_day.items() if emotion in positive_emotions
                ]
                low_days = [
                    day for day, emotion in emotion_by_day.items() if emotion in negative_emotions
                ]

                cycles.append(
                    EmotionalCycle(
                        pattern_type=EmotionalPattern.WEEKLY_CYCLE,
                        cycle_length="weekly",
                        peak_times=peak_days,
                        low_times=low_days,
                        confidence=min(0.8, len(emotion_by_day) / 7.0),
                        sample_size=len(emotion_by_day),
                    )
                )

        return cycles

    async def _analyze_trigger_patterns(self, history: List[Dict]) -> List[EmotionalTrigger]:
        """Identify what triggers specific emotions"""
        triggers = []

        # Analyze topic-emotion correlations
        topic_emotion_pairs = []
        for conv in history:
            if "topic" in conv and "emotion" in conv and "user_message" in conv:
                topic = conv["topic"]
                emotion = conv["emotion"]
                message = conv["user_message"]

                topic_emotion_pairs.append(
                    {
                        "topic": topic,
                        "emotion": emotion,
                        "message": message,
                        "timestamp": conv.get("timestamp"),
                    }
                )

        # Find topic-emotion correlations
        topic_emotions = defaultdict(list)
        for pair in topic_emotion_pairs:
            topic_emotions[pair["topic"]].append(pair["emotion"])

        for topic, emotions in topic_emotions.items():
            if len(emotions) >= 2:  # Need multiple occurrences
                emotion_counts = Counter(emotions)
                most_common_emotion, frequency = emotion_counts.most_common(1)[0]

                if frequency / len(emotions) >= 0.6:  # 60% correlation threshold
                    triggers.append(
                        EmotionalTrigger(
                            trigger_type=EmotionalTriggerType.TOPIC_BASED,
                            trigger_description=f"Topic: {topic}",
                            triggered_emotion=most_common_emotion,
                            response_intensity=frequency / len(emotions),
                            recovery_time="unknown",  # Would need temporal analysis
                            frequency=frequency,
                            confidence=frequency / len(emotions),
                        )
                    )

        # Analyze communication style triggers
        formal_emotions = []
        casual_emotions = []

        for conv in history:
            if "communication_style" in conv and "emotion" in conv:
                style = conv["communication_style"]
                emotion = conv["emotion"]

                if style == "formal":
                    formal_emotions.append(emotion)
                elif style == "casual":
                    casual_emotions.append(emotion)

        # Check if communication style correlates with emotions
        if len(formal_emotions) >= 2:
            formal_emotion_counts = Counter(formal_emotions)
            dominant_formal, freq = formal_emotion_counts.most_common(1)[0]

            if freq / len(formal_emotions) >= 0.6:
                triggers.append(
                    EmotionalTrigger(
                        trigger_type=EmotionalTriggerType.COMMUNICATION_STYLE,
                        trigger_description="Formal communication context",
                        triggered_emotion=dominant_formal,
                        response_intensity=freq / len(formal_emotions),
                        recovery_time="immediate",
                        frequency=freq,
                        confidence=freq / len(formal_emotions),
                    )
                )

        return triggers

    async def _analyze_recovery_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """Analyze how users recover from negative emotions"""
        recovery_patterns = {
            "average_recovery_time": None,
            "recovery_strategies": [],
            "recovery_success_rate": 0.0,
            "recovery_triggers": [],
        }

        # Find sequences where negative emotion transitions to positive
        recovery_sequences = []
        negative_emotions = ["stress", "anxiety", "frustration", "sadness", "confusion"]
        positive_emotions = ["joy", "excitement", "confidence"]
        neutral_emotions = ["neutral", "calm"]

        for i in range(len(history) - 1):
            current_conv = history[i]
            next_conv = history[i + 1]

            if (
                "emotion" in current_conv
                and "emotion" in next_conv
                and "timestamp" in current_conv
                and "timestamp" in next_conv
            ):

                current_emotion = current_conv["emotion"]
                next_emotion = next_conv["emotion"]

                if current_emotion in negative_emotions and (
                    next_emotion in positive_emotions or next_emotion in neutral_emotions
                ):

                    try:
                        current_time = datetime.fromisoformat(
                            current_conv["timestamp"].replace("Z", "+00:00")
                        )
                        next_time = datetime.fromisoformat(
                            next_conv["timestamp"].replace("Z", "+00:00")
                        )
                        recovery_time = next_time - current_time

                        recovery_sequences.append(
                            {
                                "from_emotion": current_emotion,
                                "to_emotion": next_emotion,
                                "recovery_time": recovery_time.total_seconds() / 3600,  # hours
                                "recovery_message": next_conv.get("user_message", ""),
                                "bot_response": current_conv.get("bot_response", ""),
                            }
                        )
                    except (ValueError, AttributeError):
                        continue

        if recovery_sequences:
            # Calculate average recovery time
            recovery_times = [seq["recovery_time"] for seq in recovery_sequences]
            recovery_patterns["average_recovery_time"] = (
                f"{statistics.mean(recovery_times):.1f} hours"
            )

            # Analyze recovery messages for patterns
            recovery_messages = [
                seq["recovery_message"] for seq in recovery_sequences if seq["recovery_message"]
            ]
            recovery_strategies = []

            for message in recovery_messages:
                message_lower = message.lower()
                for category, indicators in self._recovery_indicators.items():
                    for indicator in indicators:
                        if indicator in message_lower:
                            recovery_strategies.append(category)
                            break

            if recovery_strategies:
                strategy_counts = Counter(recovery_strategies)
                recovery_patterns["recovery_strategies"] = [
                    f"{strategy}: {count} times"
                    for strategy, count in strategy_counts.most_common()
                ]

            recovery_patterns["recovery_success_rate"] = len(recovery_sequences) / max(
                1, len([conv for conv in history if conv.get("emotion") in negative_emotions])
            )

        return recovery_patterns

    async def _detect_stress_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect patterns that indicate stress buildup"""
        stress_patterns = {
            "stress_indicators_found": [],
            "stress_escalation_detected": False,
            "stress_frequency": 0,
            "common_stress_contexts": [],
            "stress_linguistic_markers": [],
        }

        stress_conversations = []

        for conv in history:
            if conv.get("emotion") == "stress" or conv.get("emotion") == "anxiety":
                stress_conversations.append(conv)

        if len(stress_conversations) >= 2:
            stress_patterns["stress_frequency"] = len(stress_conversations) / len(history)

            # Analyze stress contexts
            stress_topics = [conv.get("topic", "unknown") for conv in stress_conversations]
            topic_counts = Counter(stress_topics)
            stress_patterns["common_stress_contexts"] = [
                f"{topic}: {count} times" for topic, count in topic_counts.most_common(3)
            ]

            # Analyze linguistic stress markers
            stress_messages = [conv.get("user_message", "") for conv in stress_conversations]
            linguistic_markers = []

            for message in stress_messages:
                if message:
                    message_lower = message.lower()
                    for category, patterns in self._stress_indicators.items():
                        for pattern in patterns:
                            if isinstance(pattern, str):
                                if pattern in message_lower:
                                    linguistic_markers.append(f"{category}: {pattern}")
                            else:  # regex pattern
                                if re.search(pattern, message_lower):
                                    linguistic_markers.append(f"{category}: {pattern.pattern}")

            stress_patterns["stress_linguistic_markers"] = list(set(linguistic_markers))

            # Check for stress escalation (increasing frequency over time)
            if len(stress_conversations) >= 3:
                recent_stress = sum(
                    1 for conv in stress_conversations[-3:] if conv.get("timestamp")
                )
                if recent_stress >= 2:
                    stress_patterns["stress_escalation_detected"] = True

        return stress_patterns

    async def _predict_emotional_trajectory(self, history: List[Dict]) -> Dict[str, Any]:
        """Predict likely emotional trajectory based on recent patterns"""
        if len(history) < 3:
            return {"prediction": "insufficient_data"}

        # Analyze recent emotional trend (last 5 conversations)
        recent_conversations = history[-5:]
        emotions = [conv.get("emotion") for conv in recent_conversations if conv.get("emotion")]

        if len(emotions) < 2:
            return {"prediction": "insufficient_emotion_data"}

        # Map emotions to numerical values for trend analysis
        emotion_values = {
            "joy": 4,
            "excitement": 4,
            "confidence": 3,
            "neutral": 0,
            "calm": 1,
            "confusion": -1,
            "frustration": -2,
            "anxiety": -3,
            "stress": -3,
            "sadness": -4,
        }

        emotion_scores = [emotion_values.get(emotion, 0) for emotion in emotions if emotion]

        # Calculate trend
        if len(emotion_scores) >= 2:
            trend = emotion_scores[-1] - emotion_scores[0]

            trajectory = {
                "recent_emotions": emotions,
                "trend_direction": (
                    "improving" if trend > 0 else "declining" if trend < 0 else "stable"
                ),
                "trend_magnitude": abs(trend),
                "current_emotional_score": emotion_scores[-1],
                "volatility": statistics.stdev(emotion_scores) if len(emotion_scores) > 1 else 0,
            }

            # Generate prediction
            if trend > 1:
                trajectory["short_term_prediction"] = "continued_improvement"
            elif trend < -1:
                trajectory["short_term_prediction"] = "potential_support_needed"
            else:
                trajectory["short_term_prediction"] = "stable_emotional_state"

            return trajectory

        return {"prediction": "insufficient_trend_data"}

    async def _analyze_conversation_timing(self, history: List[Dict]) -> Dict[str, Any]:
        """Analyze when emotional conversations typically occur"""
        timing_patterns = {
            "peak_conversation_hours": [],
            "emotional_conversation_timing": {},
            "response_time_patterns": {},
        }

        conversation_hours = []
        emotion_timing = defaultdict(list)

        for conv in history:
            if "timestamp" in conv:
                try:
                    timestamp = datetime.fromisoformat(conv["timestamp"].replace("Z", "+00:00"))
                    hour = timestamp.hour
                    conversation_hours.append(hour)

                    if "emotion" in conv:
                        emotion_timing[conv["emotion"]].append(hour)
                except (ValueError, AttributeError):
                    continue

        if conversation_hours:
            # Find peak conversation hours
            hour_counts = Counter(conversation_hours)
            peak_hours = [str(hour) for hour, count in hour_counts.most_common(3)]
            timing_patterns["peak_conversation_hours"] = peak_hours

            # Analyze emotion-specific timing
            for emotion, hours in emotion_timing.items():
                if len(hours) >= 2:
                    hour_counts = Counter(hours)
                    most_common_hour = hour_counts.most_common(1)[0][0]
                    timing_patterns["emotional_conversation_timing"][
                        emotion
                    ] = f"{most_common_hour:02d}:00"

        return timing_patterns

    async def _calculate_emotional_volatility(self, history: List[Dict]) -> float:
        """Calculate how much user's emotions fluctuate"""
        emotions = [conv.get("emotion") for conv in history if conv.get("emotion")]

        if len(emotions) < 3:
            return 0.0

        # Map emotions to numerical values
        emotion_values = {
            "joy": 4,
            "excitement": 4,
            "confidence": 3,
            "neutral": 0,
            "calm": 1,
            "confusion": -1,
            "frustration": -2,
            "anxiety": -3,
            "stress": -3,
            "sadness": -4,
        }

        emotion_scores = [emotion_values.get(emotion, 0) for emotion in emotions if emotion]

        # Calculate volatility as standard deviation
        if len(emotion_scores) > 1:
            return statistics.stdev(emotion_scores)
        return 0.0

    async def predict_emotional_state(
        self, user_id: str, context: Dict, historical_patterns: Dict
    ) -> EmotionalPrediction:
        """
        Predict likely emotional response to given context

        Args:
            user_id: User identifier
            context: Current conversation context
            historical_patterns: Result from analyze_emotional_patterns

        Returns:
            Emotional prediction with confidence and recommendations
        """
        logger.debug(
            f"Predicting emotional state for user {user_id} with context: {list(context.keys())}"
        )

        # Extract relevant context
        current_topic = context.get("topic", "general")
        current_time_hour = datetime.now().hour
        recent_messages = context.get("recent_messages", [])
        conversation_style = context.get("communication_style", "neutral")

        predicted_emotion = "neutral"
        confidence = 0.5
        triggering_factors = []
        recommended_actions = []
        risk_level = "low"

        # Check for topic-based triggers
        trigger_patterns = historical_patterns.get("trigger_patterns", [])
        for trigger in trigger_patterns:
            if (
                trigger.trigger_type == EmotionalTriggerType.TOPIC_BASED
                and current_topic in trigger.trigger_description
            ):
                predicted_emotion = trigger.triggered_emotion
                confidence = max(confidence, trigger.confidence)
                triggering_factors.append(f"Topic trigger: {current_topic}")

                if trigger.triggered_emotion in ["stress", "anxiety", "frustration"]:
                    risk_level = "medium"
                    recommended_actions.append("Monitor for stress indicators")
                    recommended_actions.append("Offer supportive responses")

        # Check for time-based patterns
        emotional_cycles = historical_patterns.get("emotional_cycles", [])
        for cycle in emotional_cycles:
            if cycle.pattern_type == EmotionalPattern.DAILY_CYCLE:
                current_hour_str = str(current_time_hour)
                if current_hour_str in cycle.low_times:
                    if predicted_emotion == "neutral":  # Don't override stronger predictions
                        predicted_emotion = "low_energy"
                        confidence = max(confidence, cycle.confidence * 0.7)
                        triggering_factors.append(
                            f"Time-based pattern: typically low energy at {current_time_hour}:00"
                        )
                elif current_hour_str in cycle.peak_times:
                    if predicted_emotion in ["neutral", "low_energy"]:
                        predicted_emotion = "positive"
                        confidence = max(confidence, cycle.confidence * 0.7)
                        triggering_factors.append(
                            f"Time-based pattern: typically positive at {current_time_hour}:00"
                        )

        # Check recent emotional trajectory
        trajectory = historical_patterns.get("emotional_trajectory", {})
        if trajectory.get("trend_direction") == "declining":
            risk_level = "medium" if risk_level == "low" else "high"
            recommended_actions.append("Proactive emotional support recommended")
            triggering_factors.append("Recent declining emotional trend")

        # Check stress patterns
        stress_patterns = historical_patterns.get("stress_indicators", {})
        if stress_patterns.get("stress_escalation_detected"):
            risk_level = "high"
            recommended_actions.append("High stress detected - prioritize supportive interaction")
            triggering_factors.append("Stress escalation pattern detected")

        # Analyze current message content for immediate emotional indicators
        if recent_messages:
            latest_message = recent_messages[-1] if recent_messages else ""

            # Check for stress indicators in current message
            message_lower = latest_message.lower()
            for category, patterns in self._stress_indicators.items():
                for pattern in patterns:
                    if isinstance(pattern, str):
                        if pattern in message_lower:
                            if predicted_emotion == "neutral":
                                predicted_emotion = "stress"
                            confidence = max(confidence, 0.8)
                            triggering_factors.append(
                                f"Current message stress indicator: {pattern}"
                            )
                            risk_level = "medium"
                    else:  # regex
                        if re.search(pattern, message_lower):
                            if predicted_emotion == "neutral":
                                predicted_emotion = "stress"
                            confidence = max(confidence, 0.8)
                            triggering_factors.append(f"Current message pattern: {category}")
                            risk_level = "medium"

            # Check for emotional keywords
            for emotion, keywords in self._emotion_keywords.items():
                for keyword in keywords:
                    if keyword in message_lower:
                        if predicted_emotion == "neutral":
                            predicted_emotion = emotion
                        confidence = max(confidence, 0.9)
                        triggering_factors.append(f"Emotional keyword detected: {keyword}")

                        if emotion in ["stress", "anxiety", "frustration", "sadness"]:
                            risk_level = "medium" if risk_level == "low" else risk_level

        # Generate appropriate recommendations based on prediction
        if predicted_emotion in ["stress", "anxiety"]:
            recommended_actions.extend(
                [
                    "Use calming, supportive language",
                    "Offer specific assistance or problem-solving",
                    "Avoid overwhelming with too much information",
                    "Acknowledge their stress explicitly",
                ]
            )
        elif predicted_emotion in ["frustration", "anger"]:
            recommended_actions.extend(
                [
                    "Validate their feelings",
                    "Offer solutions or alternatives",
                    "Use patient, understanding tone",
                    "Avoid defensive responses",
                ]
            )
        elif predicted_emotion in ["sadness", "disappointment"]:
            recommended_actions.extend(
                [
                    "Provide empathetic responses",
                    "Offer encouragement when appropriate",
                    "Listen actively to their concerns",
                    "Suggest positive future-focused topics",
                ]
            )
        elif predicted_emotion in ["excitement", "joy"]:
            recommended_actions.extend(
                [
                    "Match their positive energy",
                    "Encourage their enthusiasm",
                    "Ask follow-up questions about their excitement",
                    "Share in their positive experience",
                ]
            )

        # Determine time horizon
        if triggering_factors:
            time_horizon = "immediate"
        elif any("pattern" in factor for factor in triggering_factors):
            time_horizon = "short_term"
        else:
            time_horizon = "medium_term"

        prediction = EmotionalPrediction(
            predicted_emotion=predicted_emotion,
            confidence=min(1.0, confidence),
            time_horizon=time_horizon,
            triggering_factors=triggering_factors,
            recommended_actions=recommended_actions,
            risk_level=risk_level,
        )

        logger.debug(
            f"Emotional prediction for {user_id}: {predicted_emotion} (confidence: {confidence:.2f})"
        )
        return prediction

    def get_prediction_summary(self, prediction: EmotionalPrediction) -> Dict[str, Any]:
        """Generate human-readable prediction summary"""
        return {
            "prediction": {
                "emotion": prediction.predicted_emotion,
                "confidence": f"{prediction.confidence:.1%}",
                "risk_level": prediction.risk_level,
                "time_horizon": prediction.time_horizon,
            },
            "analysis": {
                "triggering_factors": prediction.triggering_factors,
                "recommended_actions": prediction.recommended_actions,
            },
            "summary": f"Predicted emotion: {prediction.predicted_emotion} with {prediction.confidence:.1%} confidence",
        }
