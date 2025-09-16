"""
Real-time Mood and Stress Detection System
==========================================

Advanced mood detection system that monitors emotional states in real-time,
providing early warning systems for stress and emotional support needs.

Phase 2: Predictive Emotional Intelligence
"""

import logging
import re
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import spacy

logger = logging.getLogger(__name__)


class MoodCategory(Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class StressLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    STRESS_ESCALATION = "stress_escalation"
    MOOD_DECLINE = "mood_decline"
    EMOTIONAL_VOLATILITY = "emotional_volatility"
    ISOLATION_PATTERN = "isolation_pattern"
    OVERWHELM_INDICATORS = "overwhelm_indicators"


@dataclass
class MoodAssessment:
    """Real-time mood assessment"""

    mood_category: MoodCategory
    mood_score: float  # -1.0 to 1.0
    confidence: float
    contributing_factors: list[str]
    linguistic_indicators: list[str]
    temporal_context: str
    assessment_timestamp: datetime


@dataclass
class StressAssessment:
    """Real-time stress level assessment"""

    stress_level: StressLevel
    stress_score: float  # 0.0 to 1.0
    immediate_stressors: list[str]
    physiological_indicators: list[str]
    cognitive_load_indicators: list[str]
    coping_indicators: list[str]
    assessment_timestamp: datetime


@dataclass
class EmotionalAlert:
    """Alert for concerning emotional patterns"""

    alert_type: AlertType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    evidence: list[str]
    recommended_intervention: str
    urgency_level: int  # 1-5
    alert_timestamp: datetime


class MoodDetector:
    """Real-time mood and stress detection system"""

    def __init__(self):
        """Initialize the mood detector"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model not found. Please install: python -m spacy download en_core_web_sm"
            )
            raise

        # Sliding window for real-time analysis
        self.mood_history_window = 10  # Last 10 interactions
        self.stress_threshold = 0.7
        self.mood_volatility_threshold = 0.6

        # Advanced mood indicators
        self._mood_indicators = {
            "very_positive": {
                "keywords": [
                    "amazing",
                    "fantastic",
                    "incredible",
                    "wonderful",
                    "excellent",
                    "outstanding",
                    "brilliant",
                    "perfect",
                    "awesome",
                    "thrilled",
                    "ecstatic",
                    "overjoyed",
                ],
                "patterns": [
                    r"\b(so|really|very|extremely)\s+(happy|excited|good|great)\b",
                    r"\b(love|adore|absolutely)\b.*\b(this|it|that)\b",
                ],
                "punctuation": [r"[!]{2,}", r"[!].*[!]", r":\)", r"😄|😊|🎉|❤️"],
                "intensity_multipliers": ["really", "so", "very", "extremely", "incredibly"],
            },
            "positive": {
                "keywords": [
                    "good",
                    "great",
                    "nice",
                    "happy",
                    "glad",
                    "pleased",
                    "satisfied",
                    "content",
                    "optimistic",
                    "hopeful",
                    "confident",
                    "relaxed",
                ],
                "patterns": [
                    r"\b(feel|feeling)\s+(good|great|better|fine)\b",
                    r"\b(going|things)\s+(well|good|great)\b",
                ],
                "punctuation": [r":\)", r"😊|🙂|👍"],
                "sentiment_boosters": ["thanks", "appreciate", "grateful", "pleased"],
            },
            "neutral": {
                "keywords": ["okay", "fine", "alright", "normal", "usual", "same", "regular"],
                "patterns": [
                    r"\b(it\'s|that\'s)\s+(okay|fine|alright)\b",
                    r"\b(just|simply|only)\b",
                ],
                "indicators": ["matter-of-fact", "informational", "procedural"],
            },
            "negative": {
                "keywords": [
                    "bad",
                    "difficult",
                    "hard",
                    "tough",
                    "challenging",
                    "problematic",
                    "concerned",
                    "worried",
                    "disappointed",
                    "frustrated",
                    "annoyed",
                ],
                "patterns": [
                    r"\b(not|don\'t)\s+(like|want|think)\b",
                    r"\b(having)\s+(trouble|issues|problems)\b",
                ],
                "punctuation": [r":\(", r"😞|😔|😟"],
                "negation_intensifiers": ["really", "very", "extremely", "quite"],
            },
            "very_negative": {
                "keywords": [
                    "terrible",
                    "awful",
                    "horrible",
                    "devastating",
                    "overwhelming",
                    "impossible",
                    "hopeless",
                    "desperate",
                    "miserable",
                    "unbearable",
                ],
                "patterns": [
                    r"\b(can\'t|cannot)\s+(take|handle|deal)\b",
                    r"\b(want|need)\s+to\s+(give up|quit|stop)\b",
                ],
                "punctuation": [r"[.]{3,}", r"😭|😰|😱"],
                "crisis_indicators": ["give up", "no point", "why bother", "waste of time"],
            },
        }

        # Stress detection patterns
        self._stress_indicators = {
            "time_pressure": {
                "keywords": [
                    "deadline",
                    "urgent",
                    "asap",
                    "quickly",
                    "immediately",
                    "rushing",
                    "late",
                ],
                "patterns": [
                    r"\b(running out of|short on)\s+time\b",
                    r"\b(due|deadline)\s+(today|tomorrow|soon)\b",
                ],
                "intensity": 0.8,
            },
            "workload_overwhelm": {
                "keywords": ["overwhelmed", "too much", "overloaded", "swamped", "buried"],
                "patterns": [
                    r"\b(too many|so many)\s+(things|tasks|projects)\b",
                    r"\b(can\'t keep up|falling behind)\b",
                ],
                "intensity": 0.9,
            },
            "cognitive_overload": {
                "keywords": ["confused", "complicated", "complex", "difficult to understand"],
                "patterns": [
                    r"\b(don\'t understand|makes no sense)\b",
                    r"\b(too complicated|too complex)\b",
                ],
                "intensity": 0.6,
            },
            "emotional_exhaustion": {
                "keywords": ["exhausted", "drained", "burnt out", "tired", "worn out"],
                "patterns": [
                    r"\b(so tired|really tired|completely exhausted)\b",
                    r"\b(can\'t anymore|had enough)\b",
                ],
                "intensity": 0.7,
            },
            "interpersonal_stress": {
                "keywords": ["conflict", "argument", "disagreement", "tension", "friction"],
                "patterns": [
                    r"\b(having issues with|problems with)\s+\w+\b",
                    r"\b(don\'t get along|not working)\b",
                ],
                "intensity": 0.6,
            },
        }

        # Physiological stress indicators (text-based)
        self._physiological_indicators = {
            "sleep_disruption": ["tired", "exhausted", "sleepy", "insomnia", "can't sleep"],
            "appetite_changes": ["not hungry", "no appetite", "stress eating", "overeating"],
            "energy_levels": ["low energy", "drained", "no motivation", "lethargic"],
            "concentration": ["can't focus", "distracted", "scattered", "unfocused"],
            "physical_symptoms": ["headache", "tense", "aches", "stomach", "nauseous"],
        }

        # Coping mechanism indicators
        self._coping_indicators = {
            "positive_coping": {
                "keywords": ["exercise", "meditation", "break", "walk", "breathe", "relax"],
                "patterns": [
                    r"\b(taking a|going for a)\s+(break|walk)\b",
                    r"\b(trying to|going to)\s+(relax|calm down)\b",
                ],
                "effectiveness": 0.8,
            },
            "social_support": {
                "keywords": ["talking to", "help from", "support", "friend", "family"],
                "patterns": [
                    r"\b(reached out|talked to)\s+\w+\b",
                    r"\b(getting help|asking for help)\b",
                ],
                "effectiveness": 0.9,
            },
            "problem_solving": {
                "keywords": ["planning", "organizing", "prioritizing", "strategy", "solution"],
                "patterns": [
                    r"\b(working on|figuring out)\s+\w+\b",
                    r"\b(making a plan|getting organized)\b",
                ],
                "effectiveness": 0.7,
            },
            "negative_coping": {
                "keywords": ["avoiding", "ignoring", "procrastinating", "giving up"],
                "patterns": [
                    r"\b(putting off|avoiding)\s+\w+\b",
                    r"\b(just ignoring|not dealing with)\b",
                ],
                "effectiveness": 0.2,
            },
        }

    async def assess_current_mood(self, message: str, context: dict[str, Any]) -> MoodAssessment:
        """
        Assess current mood from message content and context

        Args:
            message: User's current message
            context: Conversation context including recent history

        Returns:
            Comprehensive mood assessment
        """
        logger.debug(f"Assessing mood from message: {message[:50]}...")

        message_lower = message.lower()
        self.nlp(message)

        mood_scores = {}
        contributing_factors = []
        linguistic_indicators = []

        # Analyze each mood category
        for mood_cat, indicators in self._mood_indicators.items():
            score = 0.0
            factors = []

            # Check keywords
            for keyword in indicators.get("keywords", []):
                if keyword in message_lower:
                    weight = 1.0
                    # Check for intensity multipliers
                    if "intensity_multipliers" in indicators:
                        for multiplier in indicators["intensity_multipliers"]:
                            if multiplier in message_lower and keyword in message_lower:
                                weight = 1.5
                                break
                    score += weight
                    factors.append(f"keyword: {keyword}")
                    linguistic_indicators.append(keyword)

            # Check patterns
            for pattern in indicators.get("patterns", []):
                matches = re.findall(pattern, message_lower)
                if matches:
                    score += len(matches) * 1.2
                    factors.append(f"pattern: {pattern}")
                    linguistic_indicators.extend(matches)

            # Check punctuation patterns
            for punct_pattern in indicators.get("punctuation", []):
                if re.search(punct_pattern, message):
                    score += 0.8
                    factors.append("punctuation: emotional expression")

            # Special handling for crisis indicators in very_negative
            if mood_cat == "very_negative":
                crisis_indicators = indicators.get("crisis_indicators", [])
                for crisis_phrase in crisis_indicators:
                    if crisis_phrase in message_lower:
                        score += 2.0  # High weight for crisis language
                        factors.append(f"crisis indicator: {crisis_phrase}")

            mood_scores[mood_cat] = {"score": score, "factors": factors}
            contributing_factors.extend(factors)

        # Determine dominant mood
        max_score = 0
        dominant_mood = MoodCategory.NEUTRAL

        for mood_cat, result in mood_scores.items():
            if result["score"] > max_score:
                max_score = result["score"]
                dominant_mood = MoodCategory(mood_cat)

        # Convert to mood score (-1.0 to 1.0)
        mood_score_mapping = {
            MoodCategory.VERY_POSITIVE: 1.0,
            MoodCategory.POSITIVE: 0.5,
            MoodCategory.NEUTRAL: 0.0,
            MoodCategory.NEGATIVE: -0.5,
            MoodCategory.VERY_NEGATIVE: -1.0,
        }

        mood_score = mood_score_mapping[dominant_mood]

        # Adjust score based on intensity
        if max_score > 2:
            mood_score *= min(1.5, max_score / 2)  # Amplify for strong indicators

        # Calculate confidence based on evidence strength
        confidence = min(1.0, max_score / 3.0) if max_score > 0 else 0.3

        # Consider temporal context
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 9:
            temporal_context = "morning"
        elif 9 <= current_hour <= 17:
            temporal_context = "daytime"
        elif 17 <= current_hour <= 22:
            temporal_context = "evening"
        else:
            temporal_context = "late_night"

        # Adjust confidence based on context
        if "recent_mood_history" in context:
            recent_moods = context["recent_mood_history"]
            if len(recent_moods) >= 2:
                # If consistent with recent pattern, increase confidence
                recent_mood_avg = sum(m.get("mood_score", 0) for m in recent_moods) / len(
                    recent_moods
                )
                if abs(mood_score - recent_mood_avg) < 0.3:
                    confidence *= 1.2
                    contributing_factors.append("consistent with recent mood pattern")

        assessment = MoodAssessment(
            mood_category=dominant_mood,
            mood_score=max(-1.0, min(1.0, mood_score)),
            confidence=min(1.0, confidence),
            contributing_factors=contributing_factors,
            linguistic_indicators=list(set(linguistic_indicators)),
            temporal_context=temporal_context,
            assessment_timestamp=datetime.now(UTC),
        )

        logger.debug(
            f"Mood assessment: {dominant_mood.value} (score: {mood_score:.2f}, confidence: {confidence:.2f})"
        )
        return assessment

    async def assess_stress_level(self, message: str, context: dict[str, Any]) -> StressAssessment:
        """
        Assess current stress level from message and context

        Args:
            message: User's current message
            context: Conversation context

        Returns:
            Comprehensive stress assessment
        """
        logger.debug(f"Assessing stress level from message: {message[:50]}...")

        message_lower = message.lower()
        self.nlp(message)

        stress_score = 0.0
        immediate_stressors = []
        physiological_indicators = []
        cognitive_load_indicators = []
        coping_indicators = []

        # Analyze stress indicators
        for category, indicators in self._stress_indicators.items():
            category_score = 0.0

            # Check keywords
            for keyword in indicators.get("keywords", []):
                if keyword in message_lower:
                    weight = indicators.get("intensity", 0.5)
                    category_score += weight
                    immediate_stressors.append(f"{category}: {keyword}")

            # Check patterns
            for pattern in indicators.get("patterns", []):
                if re.search(pattern, message_lower):
                    weight = indicators.get("intensity", 0.5)
                    category_score += weight * 1.2
                    immediate_stressors.append(f"{category}: pattern match")

            stress_score += category_score

        # Check physiological indicators
        for category, indicators in self._physiological_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    stress_score += 0.3
                    physiological_indicators.append(f"{category}: {indicator}")

        # Check cognitive load indicators
        cognitive_patterns = [
            r"\b(too much|so much|overwhelming)\b",
            r"\b(can\'t think|mind is blank|confused)\b",
            r"\b(too fast|too quick|slow down)\b",
        ]

        for pattern in cognitive_patterns:
            if re.search(pattern, message_lower):
                stress_score += 0.4
                cognitive_load_indicators.append(f"cognitive overload: {pattern}")

        # Check for coping mechanisms
        for coping_type, coping_data in self._coping_indicators.items():
            for keyword in coping_data.get("keywords", []):
                if keyword in message_lower:
                    effectiveness = coping_data.get("effectiveness", 0.5)
                    if coping_type == "negative_coping":
                        stress_score += 0.2  # Negative coping adds stress
                    else:
                        stress_score -= 0.3 * effectiveness  # Positive coping reduces stress
                    coping_indicators.append(f"{coping_type}: {keyword}")

            for pattern in coping_data.get("patterns", []):
                if re.search(pattern, message_lower):
                    effectiveness = coping_data.get("effectiveness", 0.5)
                    if coping_type == "negative_coping":
                        stress_score += 0.2
                    else:
                        stress_score -= 0.3 * effectiveness
                    coping_indicators.append(f"{coping_type}: coping strategy")

        # Consider message length and complexity as stress indicators
        if len(message.split()) > 50:  # Long messages might indicate stress
            stress_score += 0.1
            cognitive_load_indicators.append("verbose communication")

        if len(re.findall(r"[.!?]", message)) > 5:  # Multiple sentences/exclamations
            stress_score += 0.1
            cognitive_load_indicators.append("fragmented communication")

        # Normalize stress score (0.0 to 1.0)
        stress_score = max(0.0, min(1.0, stress_score))

        # Determine stress level
        if stress_score >= 0.8:
            stress_level = StressLevel.CRITICAL
        elif stress_score >= 0.6:
            stress_level = StressLevel.HIGH
        elif stress_score >= 0.4:
            stress_level = StressLevel.MODERATE
        elif stress_score >= 0.2:
            stress_level = StressLevel.LOW
        else:
            stress_level = StressLevel.MINIMAL

        # Consider context factors
        if "recent_stress_history" in context:
            recent_stress = context["recent_stress_history"]
            if len(recent_stress) >= 2:
                # Check for stress escalation
                recent_scores = [s.get("stress_score", 0) for s in recent_stress]
                if len(recent_scores) >= 2:
                    trend = recent_scores[-1] - recent_scores[0]
                    if trend > 0.2:  # Increasing stress
                        stress_score = min(1.0, stress_score + 0.1)
                        immediate_stressors.append("escalating stress pattern")

        assessment = StressAssessment(
            stress_level=stress_level,
            stress_score=stress_score,
            immediate_stressors=immediate_stressors,
            physiological_indicators=physiological_indicators,
            cognitive_load_indicators=cognitive_load_indicators,
            coping_indicators=coping_indicators,
            assessment_timestamp=datetime.now(UTC),
        )

        logger.debug(f"Stress assessment: {stress_level.value} (score: {stress_score:.2f})")
        return assessment

    async def detect_emotional_alerts(
        self,
        mood_history: list[MoodAssessment],
        stress_history: list[StressAssessment],
        conversation_context: dict[str, Any],
    ) -> list[EmotionalAlert]:
        """
        Detect concerning emotional patterns requiring intervention

        Args:
            mood_history: Recent mood assessments
            stress_history: Recent stress assessments
            conversation_context: Additional context

        Returns:
            List of emotional alerts
        """
        logger.debug(
            f"Detecting emotional alerts from {len(mood_history)} mood and {len(stress_history)} stress assessments"
        )

        alerts = []

        if len(mood_history) >= 3:
            # Check for mood decline
            recent_moods = mood_history[-3:]
            mood_scores = [m.mood_score for m in recent_moods]

            if all(score < -0.3 for score in mood_scores):
                alerts.append(
                    EmotionalAlert(
                        alert_type=AlertType.MOOD_DECLINE,
                        severity="high",
                        description="Sustained negative mood detected over recent interactions",
                        evidence=[f"Mood scores: {mood_scores}"],
                        recommended_intervention="Proactive emotional support and check-in",
                        urgency_level=4,
                        alert_timestamp=datetime.now(UTC),
                    )
                )

            # Check for emotional volatility
            if len(mood_scores) >= 3:
                volatility = statistics.stdev(mood_scores)
                if volatility > self.mood_volatility_threshold:
                    alerts.append(
                        EmotionalAlert(
                            alert_type=AlertType.EMOTIONAL_VOLATILITY,
                            severity="medium",
                            description=f"High emotional volatility detected (σ={volatility:.2f})",
                            evidence=[f"Mood score variation: {mood_scores}"],
                            recommended_intervention="Offer stability and grounding techniques",
                            urgency_level=3,
                            alert_timestamp=datetime.now(UTC),
                        )
                    )

        if len(stress_history) >= 2:
            # Check for stress escalation
            recent_stress = stress_history[-2:]
            stress_scores = [s.stress_score for s in recent_stress]

            if stress_scores[-1] > self.stress_threshold:
                severity = "critical" if stress_scores[-1] > 0.85 else "high"
                urgency = 5 if severity == "critical" else 4

                alerts.append(
                    EmotionalAlert(
                        alert_type=AlertType.STRESS_ESCALATION,
                        severity=severity,
                        description=f"High stress level detected: {stress_scores[-1]:.2f}",
                        evidence=[f"Stress indicators: {recent_stress[-1].immediate_stressors}"],
                        recommended_intervention="Immediate stress management support",
                        urgency_level=urgency,
                        alert_timestamp=datetime.now(UTC),
                    )
                )

            # Check for escalating stress pattern
            if len(stress_scores) >= 2 and stress_scores[-1] > stress_scores[0] + 0.2:
                alerts.append(
                    EmotionalAlert(
                        alert_type=AlertType.STRESS_ESCALATION,
                        severity="medium",
                        description="Escalating stress pattern detected",
                        evidence=[f"Stress trend: {stress_scores}"],
                        recommended_intervention="Stress intervention and coping strategies",
                        urgency_level=3,
                        alert_timestamp=datetime.now(UTC),
                    )
                )

        # Check for overwhelm indicators
        if stress_history:
            latest_stress = stress_history[-1]
            overwhelm_indicators = [
                indicator
                for indicator in latest_stress.immediate_stressors
                if "overwhelm" in indicator or "too much" in indicator
            ]

            if overwhelm_indicators:
                alerts.append(
                    EmotionalAlert(
                        alert_type=AlertType.OVERWHELM_INDICATORS,
                        severity="medium",
                        description="Overwhelm indicators detected in communication",
                        evidence=overwhelm_indicators,
                        recommended_intervention="Break down tasks and offer structured support",
                        urgency_level=3,
                        alert_timestamp=datetime.now(UTC),
                    )
                )

        # Check for isolation patterns (based on conversation timing)
        if "last_interaction_time" in conversation_context:
            try:
                last_interaction = datetime.fromisoformat(
                    conversation_context["last_interaction_time"]
                )
                time_since_last = datetime.now(UTC) - last_interaction

                if time_since_last.days >= 3:
                    alerts.append(
                        EmotionalAlert(
                            alert_type=AlertType.ISOLATION_PATTERN,
                            severity="low",
                            description=f"Extended absence detected: {time_since_last.days} days",
                            evidence=[f"Last interaction: {last_interaction.strftime('%Y-%m-%d')}"],
                            recommended_intervention="Gentle check-in and re-engagement",
                            urgency_level=2,
                            alert_timestamp=datetime.now(UTC),
                        )
                    )
            except (ValueError, TypeError):
                pass

        # Sort alerts by urgency level (highest first)
        alerts.sort(key=lambda x: x.urgency_level, reverse=True)

        logger.debug(f"Generated {len(alerts)} emotional alerts")
        return alerts

    async def generate_intervention_recommendations(
        self, mood: MoodAssessment, stress: StressAssessment, alerts: list[EmotionalAlert]
    ) -> dict[str, Any]:
        """
        Generate specific intervention recommendations based on assessments

        Args:
            mood: Current mood assessment
            stress: Current stress assessment
            alerts: Active emotional alerts

        Returns:
            Detailed intervention recommendations
        """
        recommendations = {
            "immediate_actions": [],
            "communication_adjustments": [],
            "support_strategies": [],
            "monitoring_priorities": [],
            "escalation_triggers": [],
        }

        # High-priority alert responses
        critical_alerts = [alert for alert in alerts if alert.severity == "critical"]
        if critical_alerts:
            recommendations["immediate_actions"].extend(
                [
                    "Prioritize immediate emotional support",
                    "Use empathetic, non-judgmental language",
                    "Offer specific, actionable assistance",
                    "Monitor for crisis indicators",
                ]
            )
            recommendations["escalation_triggers"].append("Continue monitoring for crisis language")

        # Mood-based recommendations
        if mood.mood_category in [MoodCategory.NEGATIVE, MoodCategory.VERY_NEGATIVE]:
            recommendations["communication_adjustments"].extend(
                [
                    "Use warm, supportive tone",
                    "Validate their feelings explicitly",
                    "Avoid overwhelming with information",
                    "Focus on small, achievable steps",
                ]
            )

            if mood.mood_category == MoodCategory.VERY_NEGATIVE:
                recommendations["support_strategies"].extend(
                    [
                        "Offer emotional validation",
                        "Suggest breaking problems into smaller parts",
                        "Provide hope and perspective when appropriate",
                        "Monitor for improvement signs",
                    ]
                )

        elif mood.mood_category in [MoodCategory.POSITIVE, MoodCategory.VERY_POSITIVE]:
            recommendations["communication_adjustments"].extend(
                [
                    "Match their positive energy",
                    "Encourage their enthusiasm",
                    "Build on their positive momentum",
                    "Celebrate their achievements",
                ]
            )

        # Stress-based recommendations
        if stress.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]:
            recommendations["immediate_actions"].extend(
                [
                    "Acknowledge their stress explicitly",
                    "Offer concrete problem-solving assistance",
                    "Suggest stress management techniques",
                    "Help prioritize immediate concerns",
                ]
            )

            if stress.cognitive_load_indicators:
                recommendations["communication_adjustments"].extend(
                    [
                        "Use clear, simple language",
                        "Break information into digestible chunks",
                        "Provide step-by-step guidance",
                        "Avoid complex explanations",
                    ]
                )

            if stress.physiological_indicators:
                recommendations["support_strategies"].extend(
                    [
                        "Acknowledge physical stress symptoms",
                        "Suggest self-care strategies",
                        "Encourage breaks and rest",
                        "Validate the mind-body connection",
                    ]
                )

        # Alert-specific recommendations
        for alert in alerts:
            if alert.alert_type == AlertType.EMOTIONAL_VOLATILITY:
                recommendations["support_strategies"].extend(
                    [
                        "Provide consistent, stable responses",
                        "Use grounding techniques",
                        "Avoid topics that might trigger volatility",
                        "Offer predictable interaction patterns",
                    ]
                )

            elif alert.alert_type == AlertType.OVERWHELM_INDICATORS:
                recommendations["immediate_actions"].extend(
                    [
                        "Help break down overwhelming situations",
                        "Prioritize most critical tasks",
                        "Offer to tackle one thing at a time",
                        "Provide structured support",
                    ]
                )

        # Monitoring priorities
        recommendations["monitoring_priorities"].extend(
            [
                f"Track mood trend: currently {mood.mood_category.value}",
                f"Monitor stress level: currently {stress.stress_level.value}",
                "Watch for language indicating crisis or overwhelm",
                "Note effectiveness of coping strategies mentioned",
            ]
        )

        # Remove duplicates
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))

        return recommendations

    def get_assessment_summary(
        self, mood: MoodAssessment, stress: StressAssessment, alerts: list[EmotionalAlert]
    ) -> dict[str, Any]:
        """Generate human-readable assessment summary"""
        return {
            "mood": {
                "category": mood.mood_category.value,
                "score": f"{mood.mood_score:.2f}",
                "confidence": f"{mood.confidence:.1%}",
                "main_indicators": mood.linguistic_indicators[:3],
                "temporal_context": mood.temporal_context,
            },
            "stress": {
                "level": stress.stress_level.value,
                "score": f"{stress.stress_score:.2f}",
                "main_stressors": stress.immediate_stressors[:3],
                "coping_present": len(stress.coping_indicators) > 0,
            },
            "alerts": {
                "count": len(alerts),
                "highest_severity": max([alert.severity for alert in alerts], default="none"),
                "urgent_alerts": [
                    alert.description for alert in alerts if alert.urgency_level >= 4
                ],
            },
            "summary": f"Mood: {mood.mood_category.value}, Stress: {stress.stress_level.value}, {len(alerts)} alerts",
        }
