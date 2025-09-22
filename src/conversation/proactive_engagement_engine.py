"""
Proactive Conversation Engagement Engine for AI Companions

This module creates intelligent proactive conversation management that transforms AI companions
from reactive responders to engaging conversation partners. The system detects conversation
stagnation, suggests relevant topics, and generates natural conversation prompts to maintain
flowing, engaging discussions.

Key Features:
- Conversation stagnation detection and prevention
- Intelligent topic suggestion based on user interests and personality
- Natural conversation prompt generation with contextual awareness
- Conversation rhythm analysis for optimal engagement timing
- Integration with memory moments and thread management systems

This is Phase 4.3 of the personality-driven AI companion system, building on:
- Phase 3.1: Emotional Context Engine
- Phase 4.1: Memory-Triggered Personality Moments
- Phase 4.2: Multi-Thread Conversation Management

Proactive Engagement Capabilities:
- Real-time conversation flow analysis
- Predictive stagnation detection
- Context-aware topic suggestions
- Natural conversation starters and follow-ups
- Rhythm-based engagement timing
- Personality-driven engagement strategies

Integration Points:
- MemoryTriggeredMoments for conversation connections
- AdvancedConversationThreadManager for multi-thread context
- EmotionalContextEngine for emotional engagement
- DynamicPersonalityProfiler for personalized strategies
"""

import logging
import random
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Union

# Import existing systems for integration
try:
    from src.conversation.advanced_thread_manager import (
        AdvancedConversationThreadManager,
        ConversationThreadAdvanced,
        ConversationThreadState,
    )
except ImportError:
    # Import failed - thread manager components not available
    pass

try:
    from src.personality.memory_moments import ConversationContext, MemoryTriggeredMoments

    MEMORY_MOMENTS_AVAILABLE = True
except ImportError:
    MEMORY_MOMENTS_AVAILABLE = False

try:
    from src.intelligence.emotional_context_engine import EmotionalContext, EmotionalContextEngine
    EMOTIONAL_CONTEXT_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_AVAILABLE = False

try:
    from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = True
except ImportError:
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = False

try:
    from src.intelligence.dynamic_personality_profiler import (
        DynamicPersonalityProfiler,
        PersonalityProfile,
    )

    PERSONALITY_PROFILER_AVAILABLE = True
except ImportError:
    PERSONALITY_PROFILER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConversationFlowState(Enum):
    """States of conversation flow for engagement analysis"""

    HIGHLY_ENGAGING = "highly_engaging"  # Vibrant, active conversation
    ENGAGING = "engaging"  # Good conversation flow
    STEADY = "steady"  # Normal conversation pace
    DECLINING = "declining"  # Conversation losing momentum
    STAGNATING = "stagnating"  # Conversation at risk of ending
    STAGNANT = "stagnant"  # Conversation has stalled


class EngagementStrategy(Enum):
    """Types of proactive engagement strategies"""

    TOPIC_SUGGESTION = "topic_suggestion"  # Suggest new conversation topic
    FOLLOW_UP_QUESTION = "follow_up_question"  # Ask follow-up about current topic
    MEMORY_CONNECTION = "memory_connection"  # Connect to previous conversation
    EMOTIONAL_CHECK_IN = "emotional_check_in"  # Check on user's emotional state
    SHARED_INTEREST = "shared_interest"  # Engage around shared interests
    CURIOSITY_PROMPT = "curiosity_prompt"  # Spark curiosity about something
    CELEBRATION = "celebration"  # Celebrate user achievements
    SUPPORT_OFFER = "support_offer"  # Offer support or encouragement


class TopicRelevanceLevel(Enum):
    """Relevance levels for suggested topics"""

    HIGHLY_RELEVANT = "highly_relevant"  # Perfect match for user interests
    RELEVANT = "relevant"  # Good match for user interests
    SOMEWHAT_RELEVANT = "somewhat_relevant"  # Moderate match
    EXPLORATORY = "exploratory"  # New area to explore
    RANDOM = "random"  # Random topic for variety


@dataclass
class ConversationStagnationSignal:
    """Signal indicating conversation stagnation risk"""

    signal_type: str
    strength: float  # 0.0-1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Context
    recent_messages: list[str] = field(default_factory=list)
    time_since_last_message: float | None = None
    engagement_decline_rate: float = 0.0


@dataclass
class TopicSuggestion:
    """Suggested conversation topic with context"""

    topic_id: str
    topic_title: str
    topic_description: str
    relevance_level: TopicRelevanceLevel

    # Suggestion context
    connection_reason: str
    suggested_opening: str
    follow_up_questions: list[str] = field(default_factory=list)

    # Metadata
    personality_fit_score: float = 0.0
    engagement_potential: float = 0.0
    novelty_score: float = 0.0

    # Source information
    source_memories: list[str] = field(default_factory=list)
    source_threads: list[str] = field(default_factory=list)
    source_interests: list[str] = field(default_factory=list)


@dataclass
class ConversationPrompt:
    """Natural conversation prompt for engagement"""

    prompt_id: str
    strategy: EngagementStrategy
    prompt_text: str

    # Context and timing
    contextual_relevance: float = 0.0
    timing_appropriateness: float = 0.0
    personality_alignment: float = 0.0

    # Expected outcomes
    expected_engagement_boost: float = 0.0
    conversation_direction: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    priority_score: float = 0.0


@dataclass
class ConversationRhythm:
    """Analysis of user's conversation rhythm and patterns"""

    user_id: str

    # Timing patterns
    average_response_time: float = 0.0
    typical_conversation_length: int = 0
    preferred_session_duration: float = 0.0  # minutes

    # Engagement patterns
    peak_engagement_times: list[str] = field(default_factory=list)  # Hour ranges
    engagement_fade_signals: list[str] = field(default_factory=list)
    re_engagement_triggers: list[str] = field(default_factory=list)

    # Communication style
    message_length_preference: str = "medium"  # short, medium, long
    question_asking_frequency: float = 0.0
    topic_switching_frequency: float = 0.0

    # Confidence metrics
    pattern_confidence: float = 0.0
    data_points_analyzed: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class ProactiveConversationEngagementEngine:
    """
    Core engine for proactive conversation engagement that transforms AI companions
    into engaging conversation partners who maintain natural discussion flow.

    This is the Phase 4.3 implementation that builds on the sophisticated foundation
    of memory moments and multi-thread conversation management.
    """

    def __init__(
        self,
        thread_manager: AdvancedConversationThreadManager | None = None,
        memory_moments: MemoryTriggeredMoments | None = None,
        emotional_engine: Union[EmotionalContextEngine, EnhancedVectorEmotionAnalyzer, None] = None,
        personality_profiler: DynamicPersonalityProfiler | None = None,
        stagnation_threshold_minutes: int | None = None,
        engagement_check_interval_minutes: int | None = None,
        max_proactive_suggestions_per_hour: int | None = None,
    ):
        """
        Initialize the proactive conversation engagement engine.

        Args:
            thread_manager: Advanced conversation thread manager
            memory_moments: Memory-triggered moments system
            emotional_engine: Emotional context engine or Enhanced Vector Emotion Analyzer
            personality_profiler: Dynamic personality profiler
            stagnation_threshold_minutes: Minutes before considering conversation stagnant
            engagement_check_interval_minutes: How often to check engagement levels
            max_proactive_suggestions_per_hour: Limit proactive interventions
        """
        import os
        
        self.thread_manager = thread_manager
        self.memory_moments = memory_moments
        self.emotional_engine = emotional_engine
        self.personality_profiler = personality_profiler

        # Use environment variables with fallbacks
        stagnation_threshold_minutes = stagnation_threshold_minutes or int(
            os.getenv("PHASE4_ENGAGEMENT_STAGNATION_THRESHOLD_MINUTES", "5")
        )
        engagement_check_interval_minutes = engagement_check_interval_minutes or int(
            os.getenv("PHASE4_ENGAGEMENT_CHECK_INTERVAL_MINUTES", "3")
        )
        max_proactive_suggestions_per_hour = max_proactive_suggestions_per_hour or int(
            os.getenv("PHASE4_ENGAGEMENT_MAX_SUGGESTIONS_PER_HOUR", "8")
        )

        self.stagnation_threshold = timedelta(minutes=stagnation_threshold_minutes)
        self.engagement_check_interval = timedelta(minutes=engagement_check_interval_minutes)
        self.max_suggestions_per_hour = max_proactive_suggestions_per_hour

        # Conversation flow tracking
        self.conversation_flows: dict[str, list[ConversationFlowState]] = defaultdict(list)
        self.stagnation_signals: dict[str, list[ConversationStagnationSignal]] = defaultdict(list)
        self.conversation_rhythms: dict[str, ConversationRhythm] = {}

        # Proactive engagement tracking
        self.topic_suggestions: dict[str, list[TopicSuggestion]] = defaultdict(list)
        self.generated_prompts: dict[str, list[ConversationPrompt]] = defaultdict(list)
        self.engagement_interventions: dict[str, list[datetime]] = defaultdict(list)

        # Topic suggestion engines
        self.topic_generator = IntelligentTopicGenerator()
        self.prompt_generator = NaturalPromptGenerator()
        self.rhythm_analyzer = ConversationRhythmAnalyzer()

        # Performance tracking
        self.engagement_success_rates: dict[str, float] = {}
        self.intervention_effectiveness: dict[EngagementStrategy, float] = defaultdict(float)

        logger.info(
            "ProactiveConversationEngagementEngine initialized with %d minute stagnation threshold",
            stagnation_threshold_minutes,
        )

    async def analyze_conversation_engagement(
        self,
        user_id: str,
        context_id: str,
        recent_messages: list[dict[str, Any]],
        current_thread_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze current conversation engagement and provide proactive recommendations.

        Args:
            user_id: User identifier
            context_id: Context identifier (channel/DM)
            recent_messages: Recent conversation messages
            current_thread_info: Current thread information from thread manager

        Returns:
            Comprehensive engagement analysis with proactive recommendations
        """
        logger.info(f"🎯 ENGAGEMENT: Analyzing conversation for user {user_id} with {len(recent_messages)} recent messages")
        
        # Analyze conversation flow state
        flow_analysis = await self._analyze_conversation_flow(user_id, recent_messages)
        logger.info(f"🎯 ENGAGEMENT: Flow state: {flow_analysis['current_state'].value}, engagement score: {flow_analysis.get('engagement_score', 'N/A')}")

        # Detect stagnation signals
        stagnation_analysis = await self._detect_stagnation_signals(user_id, recent_messages)
        logger.info(f"🎯 ENGAGEMENT: Stagnation risk: {stagnation_analysis['risk_level']}")

        # Check if proactive intervention is needed
        intervention_needed = await self._assess_intervention_need(
            user_id, flow_analysis, stagnation_analysis
        )
        logger.info(f"🎯 ENGAGEMENT: Intervention needed: {intervention_needed}")

        # Generate proactive recommendations if needed
        recommendations = []
        if intervention_needed:
            recommendations = await self._generate_proactive_recommendations(
                user_id, context_id, recent_messages, current_thread_info
            )
            logger.info(f"🎯 ENGAGEMENT: Generated {len(recommendations)} proactive recommendations")

        # Update conversation rhythm analysis
        await self._update_conversation_rhythm(user_id, recent_messages)

        # Compile comprehensive analysis
        engagement_analysis = {
            "user_id": user_id,
            "context_id": context_id,
            "timestamp": datetime.now().isoformat(),
            # Current state analysis
            "flow_state": flow_analysis["current_state"].value,
            "flow_trend": flow_analysis["trend"],
            "engagement_score": flow_analysis["engagement_score"],
            "stagnation_risk": stagnation_analysis["risk_level"],
            # Proactive recommendations
            "intervention_needed": intervention_needed,
            "recommendations": recommendations,
            "suggested_strategy": recommendations[0]["strategy"].value if recommendations else None,
            # Context information
            "conversation_rhythm": await self._get_conversation_rhythm_summary(user_id),
            "recent_interventions": await self._get_recent_interventions(user_id),
            "success_rate": self.engagement_success_rates.get(user_id, 0.0),
        }

        return engagement_analysis

    async def _analyze_conversation_flow(
        self, user_id: str, recent_messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze the current flow state of the conversation"""

        if not recent_messages:
            return {
                "current_state": ConversationFlowState.STAGNANT,
                "trend": "declining",
                "engagement_score": 0.0,
                "flow_indicators": [],
            }

        # Calculate engagement indicators
        engagement_indicators = []

        # Message frequency analysis
        message_times = [msg.get("timestamp", datetime.now()) for msg in recent_messages]
        if len(message_times) >= 2:
            time_gaps = []
            for i in range(1, len(message_times)):
                if isinstance(message_times[i], str):
                    current_time = datetime.fromisoformat(message_times[i].replace("Z", "+00:00"))
                else:
                    current_time = message_times[i]

                if isinstance(message_times[i - 1], str):
                    prev_time = datetime.fromisoformat(message_times[i - 1].replace("Z", "+00:00"))
                else:
                    prev_time = message_times[i - 1]

                gap = (current_time - prev_time).total_seconds()
                time_gaps.append(gap)

            avg_gap = statistics.mean(time_gaps) if time_gaps else 300
            if avg_gap < 30:  # Very quick responses
                engagement_indicators.append(("quick_responses", 0.8))
            elif avg_gap < 120:  # Normal pace
                engagement_indicators.append(("normal_pace", 0.6))
            elif avg_gap > 300:  # Slow responses
                engagement_indicators.append(("slow_responses", 0.2))

        # Message content analysis
        recent_content = [msg.get("content", "") for msg in recent_messages[-5:]]

        # Enthusiasm indicators
        enthusiasm_score = 0.0
        for content in recent_content:
            content_lower = content.lower()

            # Positive indicators
            if any(
                indicator in content_lower
                for indicator in ["!", "amazing", "great", "love", "excited", "awesome"]
            ):
                enthusiasm_score += 0.2

            # Question indicators (engagement)
            if "?" in content:
                enthusiasm_score += 0.1

            # Length indicator (engagement)
            if len(content.split()) > 10:
                enthusiasm_score += 0.1

        enthusiasm_score = min(1.0, enthusiasm_score)
        engagement_indicators.append(("enthusiasm", enthusiasm_score))

        # Topic coherence analysis
        coherence_score = await self._analyze_topic_coherence(recent_content)
        engagement_indicators.append(("topic_coherence", coherence_score))

        # Calculate overall engagement score
        if engagement_indicators:
            engagement_score = statistics.mean([score for _, score in engagement_indicators])
        else:
            engagement_score = 0.5

        # Determine flow state
        if engagement_score >= 0.8:
            flow_state = ConversationFlowState.HIGHLY_ENGAGING
        elif engagement_score >= 0.6:
            flow_state = ConversationFlowState.ENGAGING
        elif engagement_score >= 0.4:
            flow_state = ConversationFlowState.STEADY
        elif engagement_score >= 0.3:
            flow_state = ConversationFlowState.DECLINING
        elif engagement_score >= 0.2:
            flow_state = ConversationFlowState.STAGNATING
        else:
            flow_state = ConversationFlowState.STAGNANT

        # Determine trend
        recent_scores = [score for _, score in engagement_indicators]
        if len(recent_scores) >= 2:
            trend = "improving" if recent_scores[-1] > recent_scores[0] else "declining"
        else:
            trend = "stable"

        # Store flow state
        self.conversation_flows[user_id].append(flow_state)
        if len(self.conversation_flows[user_id]) > 20:  # Keep last 20 states
            self.conversation_flows[user_id].pop(0)

        return {
            "current_state": flow_state,
            "trend": trend,
            "engagement_score": engagement_score,
            "flow_indicators": engagement_indicators,
        }

    async def _detect_stagnation_signals(
        self, user_id: str, recent_messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Detect signals indicating conversation stagnation"""

        stagnation_signals = []

        # Time-based stagnation
        if recent_messages:
            last_message_time = recent_messages[-1].get("timestamp", datetime.now())
            if isinstance(last_message_time, str):
                last_message_time = datetime.fromisoformat(last_message_time.replace("Z", "+00:00"))

            time_since_last = (datetime.now() - last_message_time).total_seconds() / 60

            if time_since_last > self.stagnation_threshold.total_seconds() / 60:
                signal = ConversationStagnationSignal(
                    signal_type="time_gap",
                    strength=min(1.0, time_since_last / 10),  # Normalize to 10 minutes
                    description=f"No messages for {time_since_last:.1f} minutes",
                    time_since_last_message=time_since_last,
                )
                stagnation_signals.append(signal)

        # Content-based stagnation signals
        if len(recent_messages) >= 3:
            recent_content = [msg.get("content", "").lower() for msg in recent_messages[-3:]]

            # Short responses pattern
            short_responses = sum(1 for content in recent_content if len(content.split()) <= 3)
            if short_responses >= 2:
                signal = ConversationStagnationSignal(
                    signal_type="short_responses",
                    strength=short_responses / 3,
                    description="Multiple short responses detected",
                    recent_messages=recent_content,
                )
                stagnation_signals.append(signal)

            # Repetitive content
            if len(set(recent_content)) < len(recent_content) / 2:
                signal = ConversationStagnationSignal(
                    signal_type="repetitive_content",
                    strength=0.7,
                    description="Repetitive or similar messages",
                    recent_messages=recent_content,
                )
                stagnation_signals.append(signal)

            # Declining engagement words
            engagement_words = ["interesting", "tell me more", "really?", "wow", "amazing", "!"]
            engagement_decline = 0
            for i, content in enumerate(recent_content):
                engagement_count = sum(1 for word in engagement_words if word in content)
                if i > 0 and engagement_count < len(engagement_words) / 3:
                    engagement_decline += 1

            if engagement_decline >= 2:
                signal = ConversationStagnationSignal(
                    signal_type="engagement_decline",
                    strength=engagement_decline / 3,
                    description="Declining engagement indicators",
                    engagement_decline_rate=engagement_decline / len(recent_content),
                )
                stagnation_signals.append(signal)

        # Calculate overall risk level
        if stagnation_signals:
            risk_level = min(
                1.0, statistics.mean([signal.strength for signal in stagnation_signals])
            )
        else:
            risk_level = 0.0

        # Store signals
        self.stagnation_signals[user_id].extend(stagnation_signals)
        if len(self.stagnation_signals[user_id]) > 10:  # Keep last 10 signals
            self.stagnation_signals[user_id] = self.stagnation_signals[user_id][-10:]

        return {
            "risk_level": risk_level,
            "signals": stagnation_signals,
            "signal_count": len(stagnation_signals),
            "primary_signal": stagnation_signals[0].signal_type if stagnation_signals else None,
        }

    async def _assess_intervention_need(
        self, user_id: str, flow_analysis: dict[str, Any], stagnation_analysis: dict[str, Any]
    ) -> bool:
        """Assess whether proactive intervention is needed"""

        # Check recent intervention frequency
        recent_interventions = self.engagement_interventions[user_id]
        now = datetime.now()

        # Remove old interventions (older than 1 hour)
        self.engagement_interventions[user_id] = [
            intervention
            for intervention in recent_interventions
            if (now - intervention).total_seconds() < 3600
        ]

        # Check if we've exceeded max interventions per hour
        if len(self.engagement_interventions[user_id]) >= self.max_suggestions_per_hour:
            return False

        # Check flow state
        flow_state = flow_analysis["current_state"]
        if flow_state in [
            ConversationFlowState.DECLINING,
            ConversationFlowState.STAGNATING,
            ConversationFlowState.STAGNANT,
        ]:
            return True

        # Check stagnation risk
        if stagnation_analysis["risk_level"] > 0.6:
            return True

        # Check engagement trend
        if flow_analysis["trend"] == "declining" and flow_analysis["engagement_score"] < 0.5:
            return True

        return False

    async def _generate_proactive_recommendations(
        self,
        user_id: str,
        context_id: str,
        recent_messages: list[dict[str, Any]],
        current_thread_info: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Generate proactive engagement recommendations"""

        recommendations = []

        # Get user personality profile for personalized recommendations
        personality_context = None
        if self.personality_profiler:
            try:
                personality_profile = await self.personality_profiler.get_personality_profile(
                    user_id
                )
                if personality_profile:
                    personality_context = {
                        "relationship_depth": personality_profile.relationship_depth,
                        "trust_level": personality_profile.trust_level,
                        "topics_of_interest": personality_profile.topics_of_high_engagement[:5],
                    }
            except Exception as e:
                logger.warning("Failed to get personality context for recommendations: %s", e)

        # Generate topic suggestions
        topic_suggestions = await self._generate_topic_suggestions(
            user_id, recent_messages, personality_context
        )

        for suggestion in topic_suggestions[:2]:  # Top 2 topic suggestions
            recommendations.append(
                {
                    "type": "topic_suggestion",
                    "strategy": EngagementStrategy.TOPIC_SUGGESTION,
                    "content": suggestion.suggested_opening,
                    "topic_title": suggestion.topic_title,
                    "relevance": suggestion.relevance_level.value,
                    "engagement_potential": suggestion.engagement_potential,
                    "follow_ups": suggestion.follow_up_questions[:2],
                }
            )

        # Generate conversation prompts
        conversation_prompts = await self._generate_conversation_prompts(
            user_id, recent_messages, current_thread_info, personality_context
        )

        for prompt in conversation_prompts[:2]:  # Top 2 prompts
            recommendations.append(
                {
                    "type": "conversation_prompt",
                    "strategy": prompt.strategy,
                    "content": prompt.prompt_text,
                    "engagement_boost": prompt.expected_engagement_boost,
                    "timing_score": prompt.timing_appropriateness,
                    "personality_fit": prompt.personality_alignment,
                }
            )

        # Generate memory-based connections if available
        if self.memory_moments:
            try:
                memory_connections = await self._generate_memory_connections(
                    user_id, recent_messages
                )

                for connection in memory_connections[:1]:  # Top 1 memory connection
                    recommendations.append(
                        {
                            "type": "memory_connection",
                            "strategy": EngagementStrategy.MEMORY_CONNECTION,
                            "content": connection["prompt"],
                            "connection_strength": connection["relevance_score"],
                            "memory_context": connection["memory_context"],
                        }
                    )
            except Exception as e:
                logger.warning("Failed to generate memory connections: %s", e)

        # Sort recommendations by engagement potential
        recommendations.sort(
            key=lambda r: r.get("engagement_potential", r.get("engagement_boost", 0.5)),
            reverse=True,
        )

        # Record intervention
        self.engagement_interventions[user_id].append(datetime.now())

        return recommendations[:3]  # Return top 3 recommendations

    async def _analyze_topic_coherence(self, recent_content: list[str]) -> float:
        """Analyze topic coherence in recent messages"""
        if len(recent_content) < 2:
            return 0.5

        # Simple keyword overlap analysis
        all_keywords = []
        for content in recent_content:
            keywords = self._extract_simple_keywords(content)
            all_keywords.extend(keywords)

        if not all_keywords:
            return 0.3

        # Calculate keyword overlap between messages
        overlaps = []
        for i in range(1, len(recent_content)):
            keywords1 = set(self._extract_simple_keywords(recent_content[i - 1]))
            keywords2 = set(self._extract_simple_keywords(recent_content[i]))

            if keywords1 and keywords2:
                overlap = len(keywords1 & keywords2) / len(keywords1 | keywords2)
                overlaps.append(overlap)

        return statistics.mean(overlaps) if overlaps else 0.3

    def _extract_simple_keywords(self, text: str) -> list[str]:
        """Extract simple keywords from text"""
        words = re.findall(r"\b\w+\b", text.lower())
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        return [word for word in words if len(word) > 2 and word not in stop_words]

    # Additional methods for topic generation, prompt creation, etc. will be added...

    async def _generate_topic_suggestions(
        self,
        user_id: str,
        recent_messages: list[dict[str, Any]],
        personality_context: dict[str, Any] | None,
    ) -> list[TopicSuggestion]:
        """Generate intelligent topic suggestions"""

        suggestions = []

        # Extract current conversation themes
        current_themes = []
        for msg in recent_messages[-3:]:
            content = msg.get("content", "")
            themes = self._identify_message_themes(content)
            current_themes.extend(themes)

        # Generate suggestions based on personality interests
        if personality_context and personality_context.get("topics_of_interest"):
            for topic in personality_context["topics_of_interest"][:3]:
                suggestion = TopicSuggestion(
                    topic_id=f"personality_{topic}_{user_id}",
                    topic_title=topic.title(),
                    topic_description=f"Continue exploring {topic} based on your interests",
                    relevance_level=TopicRelevanceLevel.HIGHLY_RELEVANT,
                    connection_reason=f"This aligns with your interest in {topic}",
                    suggested_opening=f"I've been thinking about {topic} - {self._generate_topic_opener(topic)}",
                    personality_fit_score=0.9,
                    engagement_potential=0.8,
                    source_interests=[topic],
                )
                suggestions.append(suggestion)

        # Generate exploratory suggestions
        exploratory_topics = [
            "recent technological innovations",
            "personal growth and learning",
            "creative projects and hobbies",
            "travel and cultural experiences",
            "books, movies, or entertainment",
            "health and wellness practices",
        ]

        for topic in random.sample(exploratory_topics, 2):
            suggestion = TopicSuggestion(
                topic_id=f"exploratory_{topic.replace(' ', '_')}_{user_id}",
                topic_title=topic.title(),
                topic_description=f"Explore {topic} together",
                relevance_level=TopicRelevanceLevel.EXPLORATORY,
                connection_reason="Expanding our conversation into new areas",
                suggested_opening=f"I'm curious about {topic} - {self._generate_topic_opener(topic)}",
                personality_fit_score=0.5,
                engagement_potential=0.6,
                novelty_score=0.8,
            )
            suggestions.append(suggestion)

        return suggestions

    def _identify_message_themes(self, content: str) -> list[str]:
        """
        Identify themes in a message using Phase 4 topic analysis with pattern fallback
        
        This method integrates sophisticated Phase 4 topic analysis while maintaining
        simple pattern matching as a reliable fallback for immediate theme detection.
        """
        themes = []
        
        # Try Phase 4 topic analysis first for more sophisticated theme detection
        if self.personality_profiler and PERSONALITY_PROFILER_AVAILABLE:
            try:
                import asyncio
                # Run Phase 4 analysis for better topic detection
                async def get_phase4_topics():
                    analysis = await self.personality_profiler.analyze_conversation(
                        "proactive_analysis", 
                        "topic_extraction",
                        content,
                        ""  # No bot response for topic extraction
                    )
                    return analysis.topics_discussed
                
                # Get Phase 4 topics
                phase4_topics = asyncio.run(get_phase4_topics())
                if phase4_topics:
                    themes.extend(phase4_topics)
                    logger.debug(f"Phase 4 detected themes: {phase4_topics}")
                    
            except Exception as e:
                logger.debug(f"Phase 4 topic analysis unavailable: {e}")
        
        # Fallback to pattern-based detection (always runs for completeness)
        content_lower = content.lower()
        
        # Enhanced theme patterns (improved from simple keywords)
        theme_patterns = {
            "work": ["work", "job", "career", "office", "meeting", "project", "colleagues", "boss", "workplace"],
            "technology": ["tech", "computer", "software", "ai", "programming", "coding", "development", "digital"],
            "health": ["health", "exercise", "fitness", "wellness", "medical", "nutrition", "workout", "mental health"],
            "learning": ["learn", "study", "education", "course", "skill", "training", "knowledge", "research"],
            "entertainment": ["movie", "music", "game", "book", "show", "series", "streaming", "reading"],
            "relationships": ["friend", "family", "partner", "social", "dating", "marriage", "children", "parents"],
            "hobbies": ["hobby", "art", "craft", "sport", "photography", "cooking", "gardening", "collecting"],
            "travel": ["travel", "trip", "vacation", "visit", "explore", "journey", "adventure", "destination"],
        }

        for theme, keywords in theme_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                if theme not in themes:  # Avoid duplicates from Phase 4
                    themes.append(theme)

        return themes

    def _generate_topic_opener(self, topic: str) -> str:
        """Generate an opening line for a topic"""
        openers = {
            "technology": "what's the most exciting tech development you've heard about lately?",
            "learning": "what's something new you've been wanting to learn?",
            "travel": "is there a place you've always wanted to visit?",
            "hobbies": "what's a hobby you've always wanted to try?",
            "health": "how do you like to stay active and healthy?",
            "entertainment": "have you discovered any great books or shows recently?",
            "work": "what's the most interesting part of your work lately?",
            "relationships": "how do you like to connect with the people you care about?",
        }

        # Generic opener if specific topic not found
        return openers.get(topic, f"what are your thoughts on {topic}?")

    async def _generate_conversation_prompts(
        self,
        user_id: str,
        recent_messages: list[dict[str, Any]],
        current_thread_info: dict[str, Any] | None,
        personality_context: dict[str, Any] | None,
    ) -> list[ConversationPrompt]:
        """Generate natural conversation prompts"""

        prompts = []

        # Follow-up question based on recent content
        if recent_messages:
            last_message = recent_messages[-1].get("content", "")
            if len(last_message.split()) > 5:  # Substantial message
                prompt = ConversationPrompt(
                    prompt_id=f"followup_{user_id}_{datetime.now().timestamp()}",
                    strategy=EngagementStrategy.FOLLOW_UP_QUESTION,
                    prompt_text=f"That's interesting! Could you tell me more about {self._extract_followup_focus(last_message)}?",
                    contextual_relevance=0.9,
                    timing_appropriateness=0.8,
                    expected_engagement_boost=0.7,
                )
                prompts.append(prompt)

        # Emotional check-in if appropriate
        emotional_checkup_prompt = ConversationPrompt(
            prompt_id=f"emotional_checkin_{user_id}_{datetime.now().timestamp()}",
            strategy=EngagementStrategy.EMOTIONAL_CHECK_IN,
            prompt_text="How are you feeling about everything we've been discussing?",
            timing_appropriateness=0.7,
            expected_engagement_boost=0.6,
            conversation_direction="emotional_support",
        )
        prompts.append(emotional_checkup_prompt)

        # Curiosity prompt
        curiosity_prompt = ConversationPrompt(
            prompt_id=f"curiosity_{user_id}_{datetime.now().timestamp()}",
            strategy=EngagementStrategy.CURIOSITY_PROMPT,
            prompt_text="I'm curious - what's something that's been on your mind lately?",
            timing_appropriateness=0.6,
            expected_engagement_boost=0.7,
            conversation_direction="open_exploration",
        )
        prompts.append(curiosity_prompt)

        return prompts

    def _extract_followup_focus(self, message: str) -> str:
        """Extract the main focus for a follow-up question"""
        # Simple extraction - could be enhanced with NLP
        words = message.split()

        # Look for interesting nouns or concepts
        interesting_words = []
        for word in words:
            word_clean = re.sub(r"[^\w]", "", word.lower())
            if len(word_clean) > 4 and word_clean not in ["that", "this", "have", "been", "with"]:
                interesting_words.append(word_clean)

        if interesting_words:
            return interesting_words[0]
        else:
            return "what you mentioned"

    async def _generate_memory_connections(
        self, user_id: str, recent_messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate memory-based conversation connections using memory moments"""

        connections = []

        if not self.memory_moments:
            return connections

        try:
            # Extract recent conversation context
            recent_content = " ".join([msg.get("content", "") for msg in recent_messages[-3:]])

            if not recent_content.strip():
                return connections

            # Enhanced: Use memory moments for authentic memory connections
            if MEMORY_MOMENTS_AVAILABLE:
                try:
                    # Analyze recent conversation for memory connections
                    memory_connections = (
                        await self.memory_moments.analyze_conversation_for_memories(
                            user_id=user_id,
                            context_id=f"proactive_engagement_{user_id}",
                            message=recent_content,
                        )
                    )

                    # Convert memory connections to engagement prompts
                    for connection in memory_connections[:2]:  # Top 2 connections
                        # Get a natural callback if available
                        if hasattr(connection, "source_memory") and hasattr(
                            connection, "connection_type"
                        ):
                            connection_type = getattr(connection, "connection_type", "general")

                            if connection_type == "similar_topic":
                                prompt = "This conversation reminds me of something we discussed before. Would you like to explore that connection further?"
                            elif connection_type == "emotional_echo":
                                prompt = "I sense a familiar emotional resonance here - it echoes something meaningful from our past conversations."
                            elif connection_type == "personal_growth":
                                prompt = "This seems to connect to your personal journey that we've touched on before. How has your perspective evolved?"
                            else:
                                prompt = "This brings back memories of our previous conversations. There might be a deeper connection here worth exploring."

                            connections.append(
                                {
                                    "prompt": prompt,
                                    "relevance_score": getattr(
                                        connection, "connection_strength", 0.7
                                    ),
                                    "memory_context": connection_type,
                                    "memory_connection": connection,
                                }
                            )

                except Exception as memory_error:
                    logger.debug(
                        f"Memory moments connection failed, using simple fallback: {memory_error}"
                    )
                    # Fallback to simple connection
                    connection = {
                        "prompt": "This reminds me of something we talked about before - how do you feel about revisiting that topic?",
                        "relevance_score": 0.6,
                        "memory_context": "previous_conversation",
                    }
                    connections.append(connection)
            else:
                # Fallback: Simple memory connection
                connection = {
                    "prompt": "This reminds me of something we talked about before - how do you feel about revisiting that topic?",
                    "relevance_score": 0.5,
                    "memory_context": "previous_conversation",
                }
                connections.append(connection)

        except (AttributeError, TypeError, KeyError) as e:
            logger.warning("Failed to generate memory connections: %s", e)

        return connections

    async def _update_conversation_rhythm(
        self, user_id: str, recent_messages: list[dict[str, Any]]
    ):
        """Update conversation rhythm analysis for user"""

        if user_id not in self.conversation_rhythms:
            self.conversation_rhythms[user_id] = ConversationRhythm(user_id=user_id)

        rhythm = self.conversation_rhythms[user_id]

        # Analyze response times
        if len(recent_messages) >= 2:
            response_times = []
            for _i in range(1, len(recent_messages)):
                # This would calculate actual response times
                # For now, use a placeholder
                response_times.append(60.0)  # 1 minute average

            if response_times:
                rhythm.average_response_time = statistics.mean(response_times)

        # Update pattern confidence
        rhythm.data_points_analyzed += len(recent_messages)
        rhythm.pattern_confidence = min(1.0, rhythm.data_points_analyzed / 100)
        rhythm.last_updated = datetime.now()

    async def _get_conversation_rhythm_summary(self, user_id: str) -> dict[str, Any]:
        """Get conversation rhythm summary for user"""

        if user_id not in self.conversation_rhythms:
            return {"rhythm_available": False}

        rhythm = self.conversation_rhythms[user_id]

        return {
            "rhythm_available": True,
            "average_response_time": rhythm.average_response_time,
            "pattern_confidence": rhythm.pattern_confidence,
            "preferred_session_duration": rhythm.preferred_session_duration,
            "data_points": rhythm.data_points_analyzed,
        }

    async def _get_recent_interventions(self, user_id: str) -> list[str]:
        """Get recent intervention timestamps"""
        interventions = self.engagement_interventions[user_id]
        return [intervention.isoformat() for intervention in interventions[-5:]]


# Supporting classes for proactive engagement


class IntelligentTopicGenerator:
    """Generates intelligent topic suggestions based on user context"""

    def __init__(self):
        self.topic_templates = self._load_topic_templates()

    def _load_topic_templates(self) -> dict[str, list[str]]:
        """Load topic generation templates"""
        return {
            "personal_growth": [
                "What's a skill you've been wanting to develop?",
                "What's something new you learned recently?",
                "What goal are you most excited about right now?",
            ],
            "technology": [
                "What's your take on the latest AI developments?",
                "Have you tried any interesting apps or tools lately?",
                "What technology do you think will change the world next?",
            ],
            "creativity": [
                "What's a creative project you'd love to start?",
                "What inspires your creativity the most?",
                "Have you discovered any new artists or creators recently?",
            ],
        }


class NaturalPromptGenerator:
    """Generates natural conversation prompts"""

    def __init__(self):
        self.prompt_templates = self._load_prompt_templates()

    def _load_prompt_templates(self) -> dict[EngagementStrategy, list[str]]:
        """Load conversation prompt templates"""
        return {
            EngagementStrategy.FOLLOW_UP_QUESTION: [
                "That's fascinating! Could you elaborate on {topic}?",
                "I'm really interested in {topic} - what's your experience with it?",
                "Tell me more about {topic} - what draws you to it?",
            ],
            EngagementStrategy.EMOTIONAL_CHECK_IN: [
                "How are you feeling about all of this?",
                "What's your emotional takeaway from {topic}?",
                "How has this conversation been for you so far?",
            ],
            EngagementStrategy.CURIOSITY_PROMPT: [
                "I'm curious - what's been on your mind lately?",
                "What's something you've been wondering about?",
                "Is there anything you've been wanting to explore or discuss?",
            ],
        }


class ConversationRhythmAnalyzer:
    """Analyzes conversation rhythms and patterns"""

    def __init__(self):
        self.rhythm_patterns = {}

    async def analyze_rhythm(
        self, user_id: str, message_history: list[dict[str, Any]]
    ) -> ConversationRhythm:
        """Analyze conversation rhythm for a user"""

        rhythm = ConversationRhythm(user_id=user_id)

        # Analyze timing patterns
        if len(message_history) >= 5:
            # This would perform sophisticated rhythm analysis
            rhythm.average_response_time = 120.0  # 2 minutes
            rhythm.pattern_confidence = 0.7
            rhythm.typical_conversation_length = len(message_history)

        return rhythm


# Convenience function for easy integration
async def create_proactive_engagement_engine(
    thread_manager=None, memory_moments=None, emotional_engine=None, personality_profiler=None
) -> ProactiveConversationEngagementEngine:
    """
    Create and initialize a proactive conversation engagement engine.

    Returns:
        ProactiveConversationEngagementEngine ready for use
    """
    # Check if thread manager components are available
    try:
        from src.conversation.thread_management.conversation_thread_manager import ConversationThreadManager
        logger.info("Thread manager components available for full integration")
    except ImportError:
        logger.warning(
            "AdvancedConversationThreadManager not available - limited thread integration"
        )

    if not MEMORY_MOMENTS_AVAILABLE:
        logger.warning("MemoryTriggeredMoments not available - limited memory integration")

    if not EMOTIONAL_CONTEXT_AVAILABLE:
        logger.warning("EmotionalContextEngine not available - limited emotional integration")

    if not PERSONALITY_PROFILER_AVAILABLE:
        logger.warning("DynamicPersonalityProfiler not available - limited personality integration")

    engine = ProactiveConversationEngagementEngine(
        thread_manager=thread_manager,
        memory_moments=memory_moments,
        emotional_engine=emotional_engine,
        personality_profiler=personality_profiler,
    )

    logger.info("ProactiveConversationEngagementEngine created successfully")
    return engine
