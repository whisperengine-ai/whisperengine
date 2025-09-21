"""
Emotional Context Engine for AI Companions

This module creates sophisticated emotional intelligence that understands user emotional states
and adapts AI companion responses accordingly. It integrates the existing emotional AI system
with the personality profiling system to create deeply empathetic and contextually appropriate
responses.

Key Features:
- Integration of emotional analysis with personality profiling
- Emotional memory clustering for pattern recognition
- Context-aware emotional adaptation based on relationship depth
- Emotional trigger detection and support opportunity identification
- Real-time emotional state tracking with personality-based responses

Integration Points:
- ExternalAPIEmotionAI (src/emotion/external_api_emotion_ai.py) for emotion detection
- DynamicPersonalityProfiler (src/intelligence/dynamic_personality_profiler.py) for personality context
- Memory clustering for emotional pattern storage

Key Integration Points:
- ExternalAPIEmotionAI: Primary emotion analysis from user messages
- DynamicPersonalityProfiler: Personality-aware emotional adaptations
- PersonalityFactClassifier: Classification of personality-relevant emotional data
- Privacy-aware emotional data handling
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Import existing systems for integration
# LocalEmotionEngine has been removed - using fallback systems
LOCAL_EMOTION_ENGINE_AVAILABLE = False

try:
    from src.intelligence.dynamic_personality_profiler import (
        DynamicPersonalityProfiler,
        PersonalityDimension,
    )

    PERSONALITY_PROFILER_AVAILABLE = True
except ImportError:
    PERSONALITY_PROFILER_AVAILABLE = False

try:
    from src.memory.personality_facts import PersonalityFactClassifier

    PERSONALITY_FACTS_AVAILABLE = True
except ImportError:
    PERSONALITY_FACTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Core emotional states for context tracking"""

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    ANTICIPATION = "anticipation"
    TRUST = "trust"


class EmotionalPattern(Enum):
    """Types of emotional patterns for memory clustering"""

    RECURRING_JOY = "recurring_joy"
    STRESS_RESPONSE = "stress_response"
    SUPPORT_SEEKING = "support_seeking"
    CELEBRATION_MOMENTS = "celebration_moments"
    VULNERABILITY_SHARING = "vulnerability_sharing"
    RESILIENCE_BUILDING = "resilience_building"
    EMOTIONAL_VALIDATION = "emotional_validation"
    COMFORT_SEEKING = "comfort_seeking"
    EXCITEMENT_SHARING = "excitement_sharing"
    FRUSTRATION_VENTING = "frustration_venting"


class EmotionalTrigger(Enum):
    """Types of emotional triggers to detect and handle appropriately"""

    STRESS_INDICATORS = "stress_indicators"
    SADNESS_ONSET = "sadness_onset"
    OVERWHELMING_EMOTIONS = "overwhelming_emotions"
    SUPPORT_OPPORTUNITIES = "support_opportunities"
    CELEBRATION_MOMENTS = "celebration_moments"
    ANXIETY_PATTERNS = "anxiety_patterns"
    EMOTIONAL_BREAKTHROUGHS = "emotional_breakthroughs"
    RELATIONSHIP_CONCERNS = "relationship_concerns"


@dataclass
class EmotionalContext:
    """Complete emotional context for a user interaction"""

    user_id: str
    context_id: str
    timestamp: datetime

    # Current emotional state
    primary_emotion: EmotionalState
    emotion_confidence: float
    emotion_intensity: float

    # Emotional analysis data
    all_emotions: dict[str, float]
    sentiment_score: float
    emotional_triggers: list[EmotionalTrigger]

    # Personality context
    personality_alignment: float  # How well emotion aligns with known personality
    relationship_depth: float  # Current relationship depth
    trust_level: float  # Current trust level

    # Contextual factors
    conversation_length: int
    response_time_context: float | None
    topic_emotional_weight: float

    # Adaptation recommendations
    response_tone_adjustment: str
    empathy_level_needed: float
    support_opportunity: bool
    celebration_opportunity: bool


@dataclass
class EmotionalMemoryCluster:
    """A cluster of emotionally similar memories"""

    cluster_id: str
    emotional_pattern: EmotionalPattern
    user_id: str

    # Cluster characteristics
    dominant_emotion: EmotionalState
    emotion_intensity_range: tuple[float, float]
    frequency: int  # How often this pattern occurs

    # Memory content
    representative_memories: list[str]  # Key examples
    common_triggers: list[str]
    effective_responses: list[str]  # AI responses that worked well

    # Temporal patterns
    created_at: datetime
    last_occurrence: datetime
    typical_timing: str | None  # e.g., "evening", "weekends", "stressful periods"

    # User feedback
    positive_outcomes: int
    adaptation_success_rate: float


@dataclass
class EmotionalAdaptationStrategy:
    """Strategy for adapting AI responses based on emotional context"""

    strategy_id: str
    user_id: str
    emotional_context: EmotionalContext

    # Adaptation parameters
    tone_adjustments: dict[str, float]  # warmth, formality, enthusiasm, etc.
    response_length_modifier: float  # longer/shorter responses
    empathy_emphasis: float  # how much to emphasize understanding

    # Personality-based adaptations
    personality_based_adjustments: dict[PersonalityDimension, float]
    communication_style_override: str | None

    # Response strategies
    acknowledge_emotion: bool
    offer_support: bool
    provide_validation: bool
    suggest_solutions: bool
    share_empathy: bool

    # Success metrics
    expected_effectiveness: float
    confidence_score: float


class EmotionalContextEngine:
    """
    Core emotional intelligence system that creates context-aware emotional responses
    for AI companions by integrating emotional analysis with personality profiling.
    """

    def __init__(
        self,
        emotional_ai: Any | None = None,  # Legacy parameter - LocalEmotionEngine removed
        personality_profiler: DynamicPersonalityProfiler | None = None,
        personality_fact_classifier: PersonalityFactClassifier | None = None,
        emotional_memory_retention_days: int = 90,
        pattern_detection_threshold: int = 3,
    ):
        """
        Initialize the emotional context engine.

        Args:
            emotional_ai: Legacy parameter - LocalEmotionEngine component removed
            personality_profiler: Dynamic personality profiling system
            personality_fact_classifier: Personality fact classification system
            emotional_memory_retention_days: Days to retain emotional memory clusters
            pattern_detection_threshold: Minimum occurrences to recognize a pattern
        """
        self.emotional_ai = emotional_ai
        self.personality_profiler = personality_profiler
        self.personality_fact_classifier = personality_fact_classifier

        self.retention_period = timedelta(days=emotional_memory_retention_days)
        self.pattern_threshold = pattern_detection_threshold

        # Emotional context storage
        self.emotional_contexts: dict[str, list[EmotionalContext]] = defaultdict(list)
        self.emotional_clusters: dict[str, list[EmotionalMemoryCluster]] = defaultdict(list)
        self.adaptation_strategies: dict[str, list[EmotionalAdaptationStrategy]] = defaultdict(list)

        # Pattern recognition
        self.emotional_patterns: dict[str, dict[EmotionalPattern, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.trigger_history: dict[str, list[tuple[datetime, EmotionalTrigger]]] = defaultdict(list)

        # Performance tracking
        self.adaptation_success_rates: dict[str, float] = {}
        self.emotional_accuracy_scores: dict[str, list[float]] = defaultdict(list)

        logger.info(
            "EmotionalContextEngine initialized with %d day retention",
            emotional_memory_retention_days,
        )

    async def analyze_emotional_context(
        self,
        user_id: str,
        context_id: str,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> EmotionalContext:
        """
        Analyze the complete emotional context of a user interaction.

        Args:
            user_id: User identifier
            context_id: Context identifier (channel/DM)
            user_message: User's message content
            conversation_history: Recent conversation history

        Returns:
            EmotionalContext with comprehensive emotional analysis
        """
        timestamp = datetime.now()

        # Get emotional analysis from existing system
        emotional_data = None
        if self.emotional_ai and LOCAL_EMOTION_ENGINE_AVAILABLE:
            try:
                # Use local emotion engine with simple text analysis
                result = await self.emotional_ai.analyze_emotion(user_message, method="auto")
                emotional_data = {
                    "primary_emotion": result.primary_emotion,
                    "confidence": result.confidence,
                    "sentiment_score": result.sentiment_score,
                    "all_emotions": result.emotions,
                    "analysis_method": result.method,
                    "analysis_time_ms": result.analysis_time_ms
                }
            except (AttributeError, TypeError, ConnectionError) as e:
                logger.warning("Emotional AI analysis failed: %s", str(e))

        # Fallback emotional analysis if needed
        if not emotional_data:
            emotional_data = self._fallback_emotional_analysis(user_message)

        # Get personality context
        personality_context = {}
        if self.personality_profiler and PERSONALITY_PROFILER_AVAILABLE:
            try:
                profile = await self.personality_profiler.get_personality_profile(user_id)
                if profile:
                    personality_context = {
                        "relationship_depth": profile.relationship_depth,
                        "trust_level": profile.trust_level,
                        "personality_traits": profile.traits,
                    }
            except (AttributeError, TypeError) as e:
                logger.warning("Personality profiling failed: %s", str(e))

        # Default personality context
        if not personality_context:
            personality_context = {
                "relationship_depth": 0.3,
                "trust_level": 0.3,
                "personality_traits": {},
            }

        # Extract emotional state
        primary_emotion = EmotionalState(emotional_data.get("primary_emotion", "neutral"))
        emotion_confidence = emotional_data.get("confidence", 0.5)
        emotion_intensity = emotional_data.get("intensity", 0.5)

        # Detect emotional triggers
        emotional_triggers = self._detect_emotional_triggers(
            user_message, emotional_data, personality_context
        )

        # Calculate personality alignment
        personality_alignment = self._calculate_personality_alignment(
            primary_emotion, personality_context.get("personality_traits", {})
        )

        # Create emotional context
        emotional_context = EmotionalContext(
            user_id=user_id,
            context_id=context_id,
            timestamp=timestamp,
            primary_emotion=primary_emotion,
            emotion_confidence=emotion_confidence,
            emotion_intensity=emotion_intensity,
            all_emotions=emotional_data.get("all_emotions", {}),
            sentiment_score=emotional_data.get("sentiment", {}).get("score", 0.5),
            emotional_triggers=emotional_triggers,
            personality_alignment=personality_alignment,
            relationship_depth=personality_context["relationship_depth"],
            trust_level=personality_context["trust_level"],
            conversation_length=len(conversation_history or []),
            response_time_context=None,  # Could be filled from conversation history
            topic_emotional_weight=self._calculate_topic_emotional_weight(user_message),
            response_tone_adjustment=self._determine_tone_adjustment(
                primary_emotion, personality_context
            ),
            empathy_level_needed=self._calculate_empathy_level(
                emotional_triggers, emotion_intensity
            ),
            support_opportunity=EmotionalTrigger.SUPPORT_OPPORTUNITIES in emotional_triggers,
            celebration_opportunity=EmotionalTrigger.CELEBRATION_MOMENTS in emotional_triggers,
        )

        # Store emotional context
        self.emotional_contexts[user_id].append(emotional_context)

        # Update emotional patterns
        await self._update_emotional_patterns(user_id, emotional_context)

        return emotional_context

    async def create_adaptation_strategy(
        self, emotional_context: EmotionalContext
    ) -> EmotionalAdaptationStrategy:
        """
        Create an adaptation strategy based on emotional context and personality.

        Args:
            emotional_context: Complete emotional context for the interaction

        Returns:
            EmotionalAdaptationStrategy with specific adaptation recommendations
        """
        user_id = emotional_context.user_id

        # Analyze historical emotional patterns
        historical_patterns = self._analyze_historical_patterns(
            user_id, emotional_context.primary_emotion
        )

        # Get personality-based adaptations
        personality_adaptations = self._get_personality_based_adaptations(emotional_context)

        # Determine tone adjustments
        tone_adjustments = self._calculate_tone_adjustments(emotional_context, historical_patterns)

        # Determine response strategies
        response_strategies = self._determine_response_strategies(emotional_context)

        # Calculate effectiveness prediction
        expected_effectiveness = self._predict_strategy_effectiveness(
            emotional_context, historical_patterns
        )

        strategy = EmotionalAdaptationStrategy(
            strategy_id=f"{user_id}_{emotional_context.timestamp.isoformat()}",
            user_id=user_id,
            emotional_context=emotional_context,
            tone_adjustments=tone_adjustments,
            response_length_modifier=self._calculate_length_modifier(emotional_context),
            empathy_emphasis=emotional_context.empathy_level_needed,
            personality_based_adjustments=personality_adaptations,
            communication_style_override=self._get_communication_style_override(emotional_context),
            acknowledge_emotion=response_strategies["acknowledge_emotion"],
            offer_support=response_strategies["offer_support"],
            provide_validation=response_strategies["provide_validation"],
            suggest_solutions=response_strategies["suggest_solutions"],
            share_empathy=response_strategies["share_empathy"],
            expected_effectiveness=expected_effectiveness,
            confidence_score=self._calculate_strategy_confidence(
                emotional_context, historical_patterns
            ),
        )

        # Store strategy
        self.adaptation_strategies[user_id].append(strategy)

        return strategy

    async def cluster_emotional_memories(self, user_id: str) -> list[EmotionalMemoryCluster]:
        """
        Group user's emotional memories into meaningful clusters for pattern recognition.

        Args:
            user_id: User identifier

        Returns:
            List of emotional memory clusters
        """
        user_contexts = self.emotional_contexts.get(user_id, [])

        if len(user_contexts) < self.pattern_threshold:
            return []

        # Group contexts by emotional patterns
        pattern_groups = defaultdict(list)

        for context in user_contexts:
            # Determine which pattern this context belongs to
            pattern = self._classify_emotional_pattern(context)
            pattern_groups[pattern].append(context)

        clusters = []

        for pattern, contexts in pattern_groups.items():
            if len(contexts) >= self.pattern_threshold:
                cluster = self._create_emotional_cluster(user_id, pattern, contexts)
                clusters.append(cluster)

        # Update stored clusters
        self.emotional_clusters[user_id] = clusters

        return clusters

    def get_emotional_adaptation_prompt(self, strategy: EmotionalAdaptationStrategy) -> str:
        """
        Generate a prompt for the AI companion that incorporates emotional adaptation.

        Args:
            strategy: Emotional adaptation strategy

        Returns:
            Prompt text for the AI companion
        """
        context = strategy.emotional_context
        adaptations = []

        # Emotional acknowledgment
        if strategy.acknowledge_emotion:
            emotion_name = context.primary_emotion.value
            adaptations.append(f"Acknowledge the user's {emotion_name} emotion with empathy")

        # Tone adjustments
        if strategy.tone_adjustments:
            tone_desc = []
            for tone, level in strategy.tone_adjustments.items():
                if level > 0.5:
                    tone_desc.append(f"more {tone}")
                elif level < 0.5:
                    tone_desc.append(f"less {tone}")
            if tone_desc:
                adaptations.append(f"Adjust tone to be {', '.join(tone_desc)}")

        # Support and validation
        if strategy.offer_support:
            adaptations.append("Offer appropriate support and assistance")

        if strategy.provide_validation:
            adaptations.append("Validate the user's feelings and perspective")

        # Response style
        if strategy.response_length_modifier > 1.2:
            adaptations.append("Provide a more detailed, thoughtful response")
        elif strategy.response_length_modifier < 0.8:
            adaptations.append("Keep response concise and focused")

        # Empathy emphasis
        if strategy.empathy_emphasis > 0.7:
            adaptations.append("Emphasize understanding and emotional connection")

        # Create natural, internal guidance instead of visible coaching prompts
        if adaptations:
            # Convert adaptations to natural behavioral guidelines
            internal_guidance = []
            for adaptation in adaptations:
                # Convert coaching language to natural behavioral guidance
                if "Acknowledge" in adaptation:
                    internal_guidance.append("be understanding and empathetic")
                elif "Adjust tone" in adaptation:
                    if "more supportive" in adaptation:
                        internal_guidance.append("use a warm, supportive tone")
                    elif "more encouraging" in adaptation:
                        internal_guidance.append("be encouraging and uplifting")
                    elif "less formal" in adaptation:
                        internal_guidance.append("be casual and friendly")
                elif "Offer appropriate support" in adaptation:
                    internal_guidance.append("be helpful and supportive")
                elif "Validate" in adaptation:
                    internal_guidance.append("validate their feelings")
                elif "detailed" in adaptation:
                    internal_guidance.append("provide thoughtful responses")
                elif "concise" in adaptation:
                    internal_guidance.append("be direct and clear")
                elif "understanding and emotional connection" in adaptation:
                    internal_guidance.append("show genuine understanding")
            
            # Create natural system guidance
            if internal_guidance:
                guidance_text = ", ".join(internal_guidance[:2])  # Limit to top 2 guidelines
                prompt = f"For this conversation, {guidance_text} while staying true to your character."
            else:
                prompt = f"Respond naturally while being mindful of the user's {context.primary_emotion.value} emotional state."
        else:
            prompt = f"Respond naturally while being mindful of the user's {context.primary_emotion.value} emotional state."

        return prompt

    async def get_conversation_emotional_context(
        self, user_id: str, current_message: str | None = None
    ) -> dict[str, Any]:
        """
        Get comprehensive emotional context for conversation enhancement.

        Args:
            user_id: User identifier
            current_message: Current user message

        Returns:
            Dictionary with emotional context data for conversation
        """
        context_data = {
            "adaptation_strategy": None,
            "emotional_patterns": [],
            "recent_emotions": [],
            "cluster_insights": [],
            "adaptation_prompt": "",
        }

        try:
            # TODO: Use current_message for real-time emotional analysis if provided
            # For now, using most recent stored emotional context

            # Get recent emotional patterns
            user_contexts = self.emotional_contexts.get(user_id, [])
            if user_contexts:
                # Get recent emotions (last 5)
                recent_contexts = user_contexts[-5:]
                context_data["recent_emotions"] = [
                    {
                        "emotion": ctx.primary_emotion.value,
                        "intensity": ctx.emotion_intensity,
                        "timestamp": ctx.timestamp.isoformat() if ctx.timestamp else None,
                    }
                    for ctx in recent_contexts
                ]

                # Get emotional clusters
                clusters = await self.cluster_emotional_memories(user_id)
                if clusters:
                    context_data["cluster_insights"] = [
                        {
                            "pattern": cluster.emotional_pattern.value,
                            "frequency": cluster.frequency,
                            "intensity": (
                                cluster.emotion_intensity_range[1]
                                if cluster.emotion_intensity_range
                                else 0
                            ),
                            "triggers": cluster.common_triggers[:3],  # Top 3 triggers
                        }
                        for cluster in clusters[:3]  # Top 3 clusters
                    ]

                # Create adaptation strategy for current message
                latest_context = recent_contexts[-1]
                strategy = await self.create_adaptation_strategy(emotional_context=latest_context)

                if strategy:
                    context_data["adaptation_strategy"] = {
                        "acknowledge_emotion": strategy.acknowledge_emotion,
                        "tone_adjustments": strategy.tone_adjustments,
                        "offer_support": strategy.offer_support,
                        "provide_validation": strategy.provide_validation,
                        "empathy_emphasis": strategy.empathy_emphasis,
                    }

                    # Generate adaptation prompt
                    context_data["adaptation_prompt"] = self.get_emotional_adaptation_prompt(
                        strategy
                    )

            return context_data

        except (AttributeError, TypeError, KeyError) as e:
            logger.warning("Failed to get conversation emotional context: %s", str(e))
            return context_data

    def _fallback_emotional_analysis(self, text: str) -> dict[str, Any]:
        """Provide basic emotional analysis when external AI is unavailable"""
        # Simple keyword-based emotion detection
        text_lower = text.lower()

        emotions = {
            "joy": ["happy", "excited", "great", "wonderful", "amazing", "love", "fantastic"],
            "sadness": ["sad", "depressed", "down", "unhappy", "disappointed", "upset"],
            "anger": ["angry", "mad", "frustrated", "annoyed", "furious", "irritated"],
            "fear": ["scared", "afraid", "worried", "anxious", "nervous", "concerned"],
            "surprise": ["surprised", "shocked", "unexpected", "wow", "amazing"],
            "neutral": [],
        }

        emotion_scores = {}
        for emotion, keywords in emotions.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = min(score / 3, 1.0)

        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            confidence = emotion_scores[primary_emotion]
        else:
            primary_emotion = "neutral"
            confidence = 0.5
            emotion_scores = {"neutral": 0.5}

        return {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "intensity": confidence * 0.8,
            "all_emotions": emotion_scores,
            "sentiment": {"score": 0.5},
        }

    def _detect_emotional_triggers(
        self, message: str, emotional_data: dict, personality_context: dict
    ) -> list[EmotionalTrigger]:
        """Detect emotional triggers in the user message"""
        triggers = []
        message_lower = message.lower()
        emotion = emotional_data.get("primary_emotion", "neutral")
        intensity = emotional_data.get("intensity", 0.5)

        # Use personality context for more nuanced trigger detection
        trust_level = personality_context.get("trust_level", 0.3)

        # Stress indicators
        stress_keywords = ["stressed", "overwhelmed", "pressure", "deadline", "anxiety", "panic"]
        if any(keyword in message_lower for keyword in stress_keywords) or intensity > 0.7:
            triggers.append(EmotionalTrigger.STRESS_INDICATORS)

        # Support opportunities
        support_keywords = ["help", "confused", "don't know", "stuck", "problem", "advice"]
        if any(keyword in message_lower for keyword in support_keywords):
            triggers.append(EmotionalTrigger.SUPPORT_OPPORTUNITIES)

        # Celebration moments
        celebration_keywords = [
            "achieved",
            "success",
            "won",
            "accomplished",
            "excited",
            "breakthrough",
        ]
        if any(keyword in message_lower for keyword in celebration_keywords) and emotion == "joy":
            triggers.append(EmotionalTrigger.CELEBRATION_MOMENTS)

        # Sadness onset
        if emotion == "sadness" and intensity > 0.6:
            triggers.append(EmotionalTrigger.SADNESS_ONSET)

        # Overwhelming emotions
        if intensity > 0.8:
            triggers.append(EmotionalTrigger.OVERWHELMING_EMOTIONS)

        # Vulnerability sharing (only detected with sufficient trust)
        if trust_level > 0.6 and emotion in ["sadness", "fear"] and intensity > 0.5:
            vulnerability_keywords = ["feel", "share", "personal", "difficult", "struggle"]
            if any(keyword in message_lower for keyword in vulnerability_keywords):
                triggers.append(EmotionalTrigger.RELATIONSHIP_CONCERNS)

        return triggers

    def _calculate_personality_alignment(
        self, emotion: EmotionalState, personality_traits: dict
    ) -> float:
        """Calculate how well the emotion aligns with known personality"""
        # Analyze if emotion is consistent with user's typical emotional patterns
        base_alignment = 0.7

        # If we have personality traits, check emotional expression patterns
        if personality_traits:
            # This would analyze historical emotional patterns vs current emotion
            # For now, return moderate alignment with some variation based on emotion type
            if emotion in [EmotionalState.JOY, EmotionalState.NEUTRAL]:
                return min(1.0, base_alignment + 0.1)
            elif emotion in [EmotionalState.SADNESS, EmotionalState.FEAR]:
                return max(0.3, base_alignment - 0.1)

        return base_alignment

    def _calculate_topic_emotional_weight(self, message: str) -> float:
        """Calculate the emotional weight of the topic being discussed"""
        heavy_topics = ["death", "loss", "breakup", "diagnosis", "failure", "trauma"]
        light_topics = ["weather", "food", "movies", "games", "casual"]

        message_lower = message.lower()

        heavy_score = sum(1 for topic in heavy_topics if topic in message_lower)
        light_score = sum(1 for topic in light_topics if topic in message_lower)

        if heavy_score > 0:
            return 0.8 + (heavy_score * 0.1)
        elif light_score > 0:
            return 0.2 + (light_score * 0.1)
        else:
            return 0.5

    def _determine_tone_adjustment(self, emotion: EmotionalState, personality_context: dict) -> str:
        """Determine how to adjust response tone based on emotion and personality"""
        # Base tone adjustment on emotion
        if emotion == EmotionalState.SADNESS:
            tone = "gentle_supportive"
        elif emotion == EmotionalState.JOY:
            tone = "enthusiastic_sharing"
        elif emotion == EmotionalState.ANGER:
            tone = "calm_understanding"
        elif emotion == EmotionalState.FEAR:
            tone = "reassuring_stable"
        elif emotion == EmotionalState.SURPRISE:
            tone = "engaged_curious"
        else:
            tone = "balanced_natural"

        # Adjust based on relationship depth and trust level
        relationship_depth = personality_context.get("relationship_depth", 0.3)
        trust_level = personality_context.get("trust_level", 0.3)

        # For deeper relationships, allow more emotional tones
        if relationship_depth > 0.7:
            if emotion == EmotionalState.JOY:
                tone = "warmly_celebratory"
            elif emotion == EmotionalState.SADNESS:
                tone = "deeply_empathetic"

        # For lower trust, use more neutral tones
        if trust_level < 0.4:
            if emotion in [EmotionalState.SADNESS, EmotionalState.FEAR]:
                tone = "professionally_supportive"

        return tone

    def _calculate_empathy_level(self, triggers: list[EmotionalTrigger], intensity: float) -> float:
        """Calculate the level of empathy needed in the response"""
        base_empathy = 0.5

        # Increase empathy for certain triggers
        if EmotionalTrigger.STRESS_INDICATORS in triggers:
            base_empathy += 0.2
        if EmotionalTrigger.SADNESS_ONSET in triggers:
            base_empathy += 0.3
        if EmotionalTrigger.OVERWHELMING_EMOTIONS in triggers:
            base_empathy += 0.2
        if EmotionalTrigger.SUPPORT_OPPORTUNITIES in triggers:
            base_empathy += 0.1

        # Adjust for intensity
        empathy_level = base_empathy + (intensity * 0.2)

        return min(empathy_level, 1.0)

    async def _update_emotional_patterns(self, user_id: str, context: EmotionalContext):
        """Update emotional pattern tracking for the user"""
        pattern = self._classify_emotional_pattern(context)
        self.emotional_patterns[user_id][pattern] += 1

        # Update trigger history
        for trigger in context.emotional_triggers:
            self.trigger_history[user_id].append((context.timestamp, trigger))

    def _classify_emotional_pattern(self, context: EmotionalContext) -> EmotionalPattern:
        """Classify an emotional context into a pattern type"""
        if context.primary_emotion == EmotionalState.JOY and context.emotion_intensity > 0.6:
            if EmotionalTrigger.CELEBRATION_MOMENTS in context.emotional_triggers:
                return EmotionalPattern.CELEBRATION_MOMENTS
            else:
                return EmotionalPattern.RECURRING_JOY
        elif EmotionalTrigger.STRESS_INDICATORS in context.emotional_triggers:
            return EmotionalPattern.STRESS_RESPONSE
        elif EmotionalTrigger.SUPPORT_OPPORTUNITIES in context.emotional_triggers:
            return EmotionalPattern.SUPPORT_SEEKING
        elif context.primary_emotion == EmotionalState.SADNESS:
            if context.trust_level > 0.7:
                return EmotionalPattern.VULNERABILITY_SHARING
            else:
                return EmotionalPattern.COMFORT_SEEKING
        else:
            return EmotionalPattern.EMOTIONAL_VALIDATION

    def _analyze_historical_patterns(
        self, user_id: str, current_emotion: EmotionalState
    ) -> dict[str, Any]:
        """Analyze historical emotional patterns for the user"""
        user_contexts = self.emotional_contexts.get(user_id, [])

        if not user_contexts:
            return {"pattern_count": 0, "avg_intensity": 0.5, "common_triggers": []}

        # Filter for similar emotions
        similar_contexts = [ctx for ctx in user_contexts if ctx.primary_emotion == current_emotion]

        if not similar_contexts:
            return {"pattern_count": 0, "avg_intensity": 0.5, "common_triggers": []}

        avg_intensity = statistics.mean(ctx.emotion_intensity for ctx in similar_contexts)

        # Find common triggers
        all_triggers = []
        for ctx in similar_contexts:
            all_triggers.extend(ctx.emotional_triggers)

        trigger_counts = defaultdict(int)
        for trigger in all_triggers:
            trigger_counts[trigger] += 1

        common_triggers = [
            trigger
            for trigger, count in trigger_counts.items()
            if count >= len(similar_contexts) * 0.3
        ]

        return {
            "pattern_count": len(similar_contexts),
            "avg_intensity": avg_intensity,
            "common_triggers": common_triggers,
        }

    def _get_personality_based_adaptations(
        self, context: EmotionalContext
    ) -> dict[PersonalityDimension, float]:
        """Get personality-based adaptation adjustments"""
        adaptations = {}

        # This would integrate with the personality profiler to get specific adaptations
        # For now, provide basic adaptations based on emotional state
        if context.primary_emotion == EmotionalState.SADNESS:
            adaptations[PersonalityDimension.EMOTIONAL_EXPRESSION] = 0.8  # More expressive
            adaptations[PersonalityDimension.SUPPORT_PREFERENCES] = 0.9  # High support
        elif context.primary_emotion == EmotionalState.JOY:
            adaptations[PersonalityDimension.EMOTIONAL_EXPRESSION] = 0.7  # Moderately expressive
            adaptations[PersonalityDimension.HUMOR_STYLE] = 0.6  # Some humor

        return adaptations

    def _calculate_tone_adjustments(
        self, context: EmotionalContext, historical_patterns: dict
    ) -> dict[str, float]:
        """Calculate specific tone adjustments based on context and history"""
        adjustments = {"warmth": 0.5, "formality": 0.5, "enthusiasm": 0.5, "gentleness": 0.5}

        # Adjust based on emotion
        if context.primary_emotion == EmotionalState.SADNESS:
            adjustments["warmth"] = 0.8
            adjustments["gentleness"] = 0.9
            adjustments["enthusiasm"] = 0.3
        elif context.primary_emotion == EmotionalState.JOY:
            adjustments["warmth"] = 0.7
            adjustments["enthusiasm"] = 0.8
        elif context.primary_emotion == EmotionalState.ANGER:
            adjustments["gentleness"] = 0.8
            adjustments["formality"] = 0.6

        # Adjust based on relationship depth
        if context.relationship_depth > 0.7:
            adjustments["warmth"] += 0.1
            adjustments["formality"] -= 0.1

        # Adjust based on historical patterns
        if historical_patterns.get("pattern_count", 0) > 3:
            avg_intensity = historical_patterns.get("avg_intensity", 0.5)
            if avg_intensity > 0.7:
                # User tends to experience intense emotions - be more gentle
                adjustments["gentleness"] += 0.1
            elif avg_intensity < 0.3:
                # User tends to be more reserved - match their energy level
                adjustments["enthusiasm"] -= 0.1

        # Normalize values
        for key in adjustments:
            adjustments[key] = max(0.0, min(1.0, adjustments[key]))

        return adjustments

    def _determine_response_strategies(self, context: EmotionalContext) -> dict[str, bool]:
        """Determine which response strategies to use"""
        strategies = {
            "acknowledge_emotion": False,
            "offer_support": False,
            "provide_validation": False,
            "suggest_solutions": False,
            "share_empathy": False,
        }

        # Acknowledge emotion for high intensity or specific triggers
        if context.emotion_intensity > 0.6 or context.emotional_triggers:
            strategies["acknowledge_emotion"] = True

        # Offer support for support opportunities
        if EmotionalTrigger.SUPPORT_OPPORTUNITIES in context.emotional_triggers:
            strategies["offer_support"] = True

        # Provide validation for negative emotions
        if context.primary_emotion in [
            EmotionalState.SADNESS,
            EmotionalState.ANGER,
            EmotionalState.FEAR,
        ]:
            strategies["provide_validation"] = True

        # Share empathy for vulnerable moments
        if context.trust_level > 0.6 and context.emotion_intensity > 0.5:
            strategies["share_empathy"] = True

        # Suggest solutions for stress/problem indicators
        if EmotionalTrigger.STRESS_INDICATORS in context.emotional_triggers:
            strategies["suggest_solutions"] = True

        return strategies

    def _calculate_length_modifier(self, context: EmotionalContext) -> float:
        """Calculate how to modify response length"""
        base_modifier = 1.0

        # Longer responses for high emotion intensity
        if context.emotion_intensity > 0.7:
            base_modifier *= 1.3

        # Longer responses for support situations
        if EmotionalTrigger.SUPPORT_OPPORTUNITIES in context.emotional_triggers:
            base_modifier *= 1.2

        # Shorter responses for low trust
        if context.trust_level < 0.4:
            base_modifier *= 0.8

        return base_modifier

    def _get_communication_style_override(self, context: EmotionalContext) -> str | None:
        """Get communication style override for specific situations"""
        if EmotionalTrigger.OVERWHELMING_EMOTIONS in context.emotional_triggers:
            return "calm_grounding"
        elif EmotionalTrigger.CELEBRATION_MOMENTS in context.emotional_triggers:
            return "enthusiastic_celebratory"
        elif context.primary_emotion == EmotionalState.FEAR:
            return "reassuring_stable"
        else:
            return None

    def _predict_strategy_effectiveness(
        self, context: EmotionalContext, historical_patterns: dict
    ) -> float:
        """Predict how effective the adaptation strategy will be"""
        base_effectiveness = 0.7

        # Higher effectiveness for established patterns
        if historical_patterns["pattern_count"] > 3:
            base_effectiveness += 0.1

        # Higher effectiveness for high trust relationships
        if context.trust_level > 0.7:
            base_effectiveness += 0.1

        # Lower effectiveness for very high intensity emotions
        if context.emotion_intensity > 0.9:
            base_effectiveness -= 0.1

        return max(0.3, min(1.0, base_effectiveness))

    def _calculate_strategy_confidence(
        self, context: EmotionalContext, historical_patterns: dict
    ) -> float:
        """Calculate confidence in the adaptation strategy"""
        confidence = 0.6

        # Higher confidence with more historical data
        confidence += min(0.2, historical_patterns["pattern_count"] * 0.05)

        # Higher confidence with higher emotion confidence
        confidence += context.emotion_confidence * 0.2

        # Higher confidence for established relationships
        confidence += context.relationship_depth * 0.1

        return max(0.3, min(1.0, confidence))

    def _create_emotional_cluster(
        self, user_id: str, pattern: EmotionalPattern, contexts: list[EmotionalContext]
    ) -> EmotionalMemoryCluster:
        """Create an emotional memory cluster from similar contexts"""
        # Analyze cluster characteristics
        emotions = [ctx.primary_emotion for ctx in contexts]
        intensities = [ctx.emotion_intensity for ctx in contexts]

        dominant_emotion = max(set(emotions), key=emotions.count)
        intensity_range = (min(intensities), max(intensities))

        # Get representative memories (simplified)
        representative_memories = [
            f"User experienced {ctx.primary_emotion.value} (intensity: {ctx.emotion_intensity:.2f})"
            for ctx in contexts[:3]  # Take first 3 as examples
        ]

        # Find common triggers
        all_triggers = []
        for ctx in contexts:
            all_triggers.extend([trigger.value for trigger in ctx.emotional_triggers])

        trigger_counts = defaultdict(int)
        for trigger in all_triggers:
            trigger_counts[trigger] += 1

        common_triggers = [
            trigger for trigger, count in trigger_counts.items() if count >= len(contexts) * 0.3
        ]

        return EmotionalMemoryCluster(
            cluster_id=f"{user_id}_{pattern.value}_{datetime.now().isoformat()}",
            emotional_pattern=pattern,
            user_id=user_id,
            dominant_emotion=dominant_emotion,
            emotion_intensity_range=intensity_range,
            frequency=len(contexts),
            representative_memories=representative_memories,
            common_triggers=common_triggers,
            effective_responses=[],  # Would be populated from feedback
            created_at=datetime.now(),
            last_occurrence=max(ctx.timestamp for ctx in contexts),
            typical_timing=None,  # Could be analyzed from timestamps
            positive_outcomes=0,  # Would be tracked from user feedback
            adaptation_success_rate=0.7,  # Initial estimate
        )

    async def get_user_emotional_summary(self, user_id: str) -> dict[str, Any]:
        """Get a summary of the user's emotional patterns and context"""
        contexts = self.emotional_contexts.get(user_id, [])
        clusters = self.emotional_clusters.get(user_id, [])

        if not contexts:
            return {
                "total_interactions": 0,
                "dominant_emotions": {},
                "emotional_patterns": {},
                "relationship_progression": [],
                "adaptation_effectiveness": 0.0,
            }

        # Analyze dominant emotions
        emotions = [ctx.primary_emotion.value for ctx in contexts]
        emotion_counts = defaultdict(int)
        for emotion in emotions:
            emotion_counts[emotion] += 1

        dominant_emotions = dict(sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True))

        # Analyze emotional patterns
        pattern_analysis = {}
        for cluster in clusters:
            pattern_analysis[cluster.emotional_pattern.value] = {
                "frequency": cluster.frequency,
                "dominant_emotion": cluster.dominant_emotion.value,
                "intensity_range": cluster.emotion_intensity_range,
                "common_triggers": cluster.common_triggers,
            }

        # Track relationship progression
        relationship_progression = [
            {
                "timestamp": ctx.timestamp.isoformat(),
                "relationship_depth": ctx.relationship_depth,
                "trust_level": ctx.trust_level,
            }
            for ctx in contexts[-10:]  # Last 10 interactions
        ]

        # Calculate adaptation effectiveness
        strategies = self.adaptation_strategies.get(user_id, [])
        if strategies:
            avg_effectiveness = statistics.mean(s.expected_effectiveness for s in strategies)
        else:
            avg_effectiveness = 0.0

        return {
            "total_interactions": len(contexts),
            "dominant_emotions": dominant_emotions,
            "emotional_patterns": pattern_analysis,
            "relationship_progression": relationship_progression,
            "adaptation_effectiveness": avg_effectiveness,
            "current_relationship_depth": contexts[-1].relationship_depth if contexts else 0.0,
            "current_trust_level": contexts[-1].trust_level if contexts else 0.0,
        }


# Convenience function for easy integration
async def create_emotional_context_engine(
    emotional_ai=None, personality_profiler=None, personality_fact_classifier=None
) -> EmotionalContextEngine:
    """
    Create and initialize an emotional context engine with available components.

    Returns:
        EmotionalContextEngine ready for use
    """
    if not LOCAL_EMOTION_ENGINE_AVAILABLE:
        logger.warning("ExternalAPIEmotionAI not available - using fallback emotional analysis")

    if not PERSONALITY_PROFILER_AVAILABLE:
        logger.warning("DynamicPersonalityProfiler not available - limited personality integration")

    engine = EmotionalContextEngine(
        emotional_ai=emotional_ai,
        personality_profiler=personality_profiler,
        personality_fact_classifier=personality_fact_classifier,
    )

    logger.info("EmotionalContextEngine created successfully")
    return engine
