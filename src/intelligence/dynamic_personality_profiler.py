"""
Dynamic Personality Profiling System for AI Companions

This module implements real-time personality adaptation based on conversation patterns,
emotional intelligence analysis, and relationship development over time.

Key Features:
- Real-time personality trait tracking and evolution
- Conversation pattern analysis for personality insights
- Emotional response adaptation based on user preferences
- Contextual personality state management
- Relationship depth measurement and adaptation
- PostgreSQL persistence for long-term personality learning

Personality Dimensions Tracked:
- Communication Style: formal/casual, brief/detailed, direct/indirect
- Emotional Expression: reserved/expressive, analytical/intuitive
- Social Engagement: introverted/extroverted, group/individual preference
- Learning Style: visual/auditory/kinesthetic, structured/exploratory
- Decision Making: logical/emotional, quick/deliberate, independent/collaborative
- Humor Style: witty/playful/dry/serious, frequency and timing preferences
- Support Preferences: advice/listening/encouragement, autonomy/guidance
"""

import asyncio
import json
import logging
import os
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Database imports
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class PersonalityDimension(Enum):
    """Core personality dimensions for AI companion adaptation"""

    COMMUNICATION_STYLE = "communication_style"
    EMOTIONAL_EXPRESSION = "emotional_expression"
    SOCIAL_ENGAGEMENT = "social_engagement"
    LEARNING_STYLE = "learning_style"
    DECISION_MAKING = "decision_making"
    HUMOR_STYLE = "humor_style"
    SUPPORT_PREFERENCES = "support_preferences"
    TRUST_LEVEL = "trust_level"
    CONVERSATION_DEPTH = "conversation_depth"
    RESPONSE_TIMING = "response_timing"


class ConversationPattern(Enum):
    """Types of conversation patterns that reveal personality"""

    GREETING_STYLE = "greeting_style"
    QUESTION_FREQUENCY = "question_frequency"
    TOPIC_TRANSITIONS = "topic_transitions"
    EMOTIONAL_SHARING = "emotional_sharing"
    HUMOR_USAGE = "humor_usage"
    HELP_SEEKING = "help_seeking"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    RESPONSE_LENGTH = "response_length"
    CONVERSATION_INITIATION = "conversation_initiation"
    CONFLICT_HANDLING = "conflict_handling"


@dataclass
class PersonalityTrait:
    """A single personality trait measurement"""

    dimension: PersonalityDimension
    value: float  # -1.0 to 1.0 scale (e.g., -1.0=formal, 1.0=casual)
    confidence: float  # 0.0 to 1.0 confidence in this measurement
    last_updated: datetime
    evidence_count: int  # Number of conversation instances supporting this
    evidence_sources: list[str] = field(default_factory=list)


@dataclass
class ConversationAnalysis:
    """Analysis results from a single conversation"""

    user_id: str
    context_id: str
    timestamp: datetime

    # Message characteristics
    message_length: int
    response_time_seconds: float | None
    emotional_tone: str  # from emotional AI
    topics_discussed: list[str]

    # Personality indicators
    formality_score: float  # -1.0=very formal, 1.0=very casual
    detail_preference: float  # -1.0=brief, 1.0=detailed
    emotional_openness: float  # 0.0=reserved, 1.0=very open
    question_ratio: float  # ratio of questions to statements
    humor_detected: bool
    support_seeking: bool
    knowledge_sharing: bool

    # Conversation context
    conversation_depth: float  # 0.0=surface, 1.0=deep personal
    trust_indicators: list[str]  # phrases indicating trust/comfort
    adaptation_requests: list[str]  # explicit requests for AI behavior changes


@dataclass
class PersonalityProfile:
    """Complete personality profile for a user"""

    user_id: str
    created_at: datetime
    last_updated: datetime

    # Core personality traits
    traits: dict[PersonalityDimension, PersonalityTrait]

    # Conversation history analysis
    total_conversations: int
    conversation_analyses: deque  # Recent conversation analyses

    # Relationship metrics
    relationship_depth: float  # 0.0=stranger, 1.0=close companion
    trust_level: float  # 0.0=minimal, 1.0=high trust
    adaptation_success_rate: float  # How often user responds positively to personality adaptations

    # AI companion optimization
    preferred_response_style: dict[str, Any]
    effective_conversation_patterns: list[str]
    topics_of_high_engagement: list[str]

    def __post_init__(self):
        """Initialize conversation analyses deque with max length"""
        if not isinstance(self.conversation_analyses, deque):
            self.conversation_analyses = deque(self.conversation_analyses or [], maxlen=50)


class DynamicPersonalityProfiler:
    """
    Real-time personality profiling system for AI companions.

    Analyzes conversation patterns to build dynamic personality profiles
    that enable human-like adaptation and relationship building.
    """

    def __init__(
        self,
        analysis_window_days: int = 30,
        min_conversations_for_confidence: int = 5,
        trait_update_threshold: float = 0.1,
    ):
        """
        Initialize the personality profiler.

        Args:
            analysis_window_days: Days of conversation history to consider
            min_conversations_for_confidence: Minimum conversations needed for confident trait assessment
            trait_update_threshold: Minimum change required to update a trait
        """
        self.analysis_window = timedelta(days=analysis_window_days)
        self.min_conversations = min_conversations_for_confidence
        self.update_threshold = trait_update_threshold

        # User profiles storage
        self.profiles: dict[str, PersonalityProfile] = {}

        # Pattern analysis
        self.conversation_patterns = defaultdict(list)

        logger.info(
            "DynamicPersonalityProfiler initialized with %d day analysis window",
            analysis_window_days,
        )

    async def analyze_conversation(
        self,
        user_id: str,
        context_id: str,
        user_message: str,
        bot_response: str,
        response_time_seconds: float | None = None,
        emotional_data: dict | None = None,
    ) -> ConversationAnalysis:
        """
        Analyze a single conversation for personality insights.

        Args:
            user_id: User identifier
            context_id: Context identifier (channel/DM)
            user_message: User's message content
            bot_response: Bot's response content
            response_time_seconds: Time between bot response and user message
            emotional_data: Pre-analyzed emotional data

        Returns:
            ConversationAnalysis with personality insights
        """
        analysis = ConversationAnalysis(
            user_id=user_id,
            context_id=context_id,
            timestamp=datetime.now(),
            message_length=len(user_message),
            response_time_seconds=response_time_seconds,
            emotional_tone=(
                emotional_data.get("primary_emotion", "neutral") if emotional_data else "neutral"
            ),
            topics_discussed=self._extract_topics(user_message),
            formality_score=self._analyze_formality(user_message),
            detail_preference=self._analyze_detail_preference(user_message),
            emotional_openness=self._analyze_emotional_openness(user_message, emotional_data),
            question_ratio=self._calculate_question_ratio(user_message),
            humor_detected=self._detect_humor(user_message),
            support_seeking=self._detect_support_seeking(user_message),
            knowledge_sharing=self._detect_knowledge_sharing(user_message),
            conversation_depth=self._analyze_conversation_depth(user_message),
            trust_indicators=self._extract_trust_indicators(user_message),
            adaptation_requests=self._extract_adaptation_requests(user_message, bot_response),
        )

        logger.debug(
            "Analyzed conversation for %s: depth=%.2f, formality=%.2f, trust_indicators=%d",
            user_id,
            analysis.conversation_depth,
            analysis.formality_score,
            len(analysis.trust_indicators),
        )

        return analysis

    async def update_personality_profile(
        self, analysis: ConversationAnalysis
    ) -> PersonalityProfile:
        """
        Update user's personality profile based on conversation analysis.

        Args:
            analysis: Conversation analysis results

        Returns:
            Updated personality profile
        """
        user_id = analysis.user_id

        # Get or create profile
        if user_id not in self.profiles:
            self.profiles[user_id] = PersonalityProfile(
                user_id=user_id,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                traits={},
                total_conversations=0,
                conversation_analyses=deque(maxlen=50),
                relationship_depth=0.0,
                trust_level=0.0,
                adaptation_success_rate=0.5,
                preferred_response_style={},
                effective_conversation_patterns=[],
                topics_of_high_engagement=[],
            )

        profile = self.profiles[user_id]

        # Add conversation analysis
        profile.conversation_analyses.append(analysis)
        profile.total_conversations += 1
        profile.last_updated = datetime.now()

        # Update personality traits
        await self._update_communication_style(profile, analysis)
        await self._update_emotional_expression(profile, analysis)
        await self._update_social_engagement(profile, analysis)
        await self._update_learning_style(profile, analysis)
        await self._update_support_preferences(profile, analysis)
        await self._update_trust_level(profile, analysis)

        # Update relationship metrics
        await self._update_relationship_depth(profile, analysis)

        # Update AI companion optimization data
        await self._update_response_preferences(profile, analysis)

        logger.debug(
            "Updated personality profile for %s: %d traits, relationship_depth=%.2f",
            user_id,
            len(profile.traits),
            profile.relationship_depth,
        )

        return profile

    def _extract_topics(self, message: str) -> list[str]:
        """Extract topics from a message"""
        # Simple topic extraction - could be enhanced with NLP
        topics = []

        # Common topic keywords
        topic_keywords = {
            "work": ["work", "job", "career", "office", "boss", "colleague"],
            "family": ["family", "parent", "child", "sibling", "relative"],
            "hobbies": ["hobby", "music", "art", "sports", "game", "reading"],
            "technology": ["computer", "software", "code", "programming", "tech"],
            "health": ["health", "doctor", "medicine", "exercise", "diet"],
            "education": ["school", "university", "study", "learn", "course"],
            "relationships": ["friend", "relationship", "dating", "love", "romance"],
            "emotions": ["feel", "emotion", "happy", "sad", "angry", "excited"],
        }

        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _analyze_formality(self, message: str) -> float:
        """Analyze formality level of a message (-1.0=formal, 1.0=casual)"""
        formal_indicators = [
            "please",
            "thank you",
            "would you",
            "could you",
            "may I",
            "I would appreciate",
            "sincerely",
            "regards",
        ]

        casual_indicators = [
            "hey",
            "hi",
            "yeah",
            "ok",
            "cool",
            "awesome",
            "lol",
            "btw",
            "ur",
            "u",
            "gonna",
            "wanna",
            "dunno",
            "kinda",
        ]

        message_lower = message.lower()

        formal_count = sum(1 for indicator in formal_indicators if indicator in message_lower)
        casual_count = sum(1 for indicator in casual_indicators if indicator in message_lower)

        # Normalize by message length
        message_words = len(message.split())
        if message_words == 0:
            return 0.0

        formal_score = formal_count / message_words
        casual_score = casual_count / message_words

        # Return difference, scaled to -1.0 to 1.0
        return min(1.0, max(-1.0, (casual_score - formal_score) * 10))

    def _analyze_detail_preference(self, message: str) -> float:
        """Analyze preference for detailed vs brief communication"""
        # Longer messages with explanations = detail preference
        # Shorter, direct messages = brief preference

        message_length = len(message)
        len(message.split())

        # Detail indicators
        detail_indicators = [
            "because",
            "since",
            "therefore",
            "however",
            "moreover",
            "furthermore",
            "for example",
            "specifically",
            "in particular",
            "detailed",
            "explain",
        ]

        brief_indicators = ["yes", "no", "ok", "sure", "nope", "yep", "quick", "brief", "short"]

        message_lower = message.lower()
        detail_count = sum(1 for indicator in detail_indicators if indicator in message_lower)
        brief_count = sum(1 for indicator in brief_indicators if indicator in message_lower)

        # Base score on message length (normalized)
        length_score = min(1.0, message_length / 500.0)  # 500 chars = detailed

        # Adjust based on indicators
        indicator_score = (detail_count - brief_count) * 0.2

        return min(1.0, max(-1.0, length_score + indicator_score))

    def _analyze_emotional_openness(self, message: str, emotional_data: dict | None) -> float:
        """Analyze how emotionally open/expressive the user is"""
        emotional_words = [
            "feel",
            "emotion",
            "happy",
            "sad",
            "angry",
            "excited",
            "worried",
            "anxious",
            "love",
            "hate",
            "fear",
            "joy",
            "frustrated",
            "grateful",
            "disappointed",
            "hopeful",
            "proud",
            "embarrassed",
            "confident",
        ]

        personal_sharing = [
            "I feel",
            "I'm feeling",
            "I think",
            "I believe",
            "I'm worried",
            "I'm excited",
            "I'm sad",
            "I'm happy",
            "personally",
            "honestly",
        ]

        message_lower = message.lower()
        emotional_count = sum(1 for word in emotional_words if word in message_lower)
        personal_count = sum(1 for phrase in personal_sharing if phrase in message_lower)

        # Factor in emotional AI data if available
        emotional_intensity = 0.5
        if emotional_data and "intensity" in emotional_data:
            emotional_intensity = emotional_data["intensity"]

        # Combine indicators
        message_words = len(message.split())
        if message_words == 0:
            return 0.0

        openness_score = (emotional_count + personal_count * 2) / message_words
        openness_score = openness_score * emotional_intensity

        return min(1.0, openness_score * 5)  # Scale up to 0-1 range

    def _calculate_question_ratio(self, message: str) -> float:
        """Calculate ratio of questions to total sentences"""
        sentences = message.split(".")
        questions = message.count("?")

        if len(sentences) == 0:
            return 0.0

        return min(1.0, questions / len(sentences))

    def _detect_humor(self, message: str) -> bool:
        """Detect if humor is present in the message"""
        humor_indicators = [
            "lol",
            "haha",
            "hehe",
            "😂",
            "😄",
            "😆",
            "funny",
            "joke",
            "kidding",
            "joking",
            "😊",
            "😁",
            "witty",
            "hilarious",
        ]

        return any(indicator in message.lower() for indicator in humor_indicators)

    def _detect_support_seeking(self, message: str) -> bool:
        """Detect if user is seeking support or help"""
        support_phrases = [
            "help me",
            "I need",
            "struggling with",
            "having trouble",
            "don't know how",
            "any advice",
            "what should I",
            "I'm stuck",
            "feeling lost",
            "need guidance",
            "can you help",
        ]

        return any(phrase in message.lower() for phrase in support_phrases)

    def _detect_knowledge_sharing(self, message: str) -> bool:
        """Detect if user is sharing knowledge or teaching"""
        knowledge_phrases = [
            "did you know",
            "let me explain",
            "the way it works",
            "I learned",
            "actually",
            "in fact",
            "for your information",
            "fun fact",
            "interestingly",
            "it turns out",
        ]

        return any(phrase in message.lower() for phrase in knowledge_phrases)

    def _analyze_conversation_depth(self, message: str) -> float:
        """Analyze how deep/personal the conversation is"""
        surface_indicators = [
            "weather",
            "how are you",
            "good morning",
            "good night",
            "hello",
            "hi",
            "bye",
            "goodbye",
            "thanks",
            "ok",
        ]

        deep_indicators = [
            "personal",
            "relationship",
            "family",
            "fear",
            "dream",
            "goal",
            "struggle",
            "challenge",
            "growth",
            "experience",
            "memory",
            "belief",
            "value",
            "philosophy",
            "meaningful",
            "important",
        ]

        message_lower = message.lower()
        surface_count = sum(1 for indicator in surface_indicators if indicator in message_lower)
        deep_count = sum(1 for indicator in deep_indicators if indicator in message_lower)

        # Longer messages tend to be deeper
        length_factor = min(1.0, len(message) / 200.0)

        # Calculate depth score
        if surface_count + deep_count == 0:
            depth_score = length_factor * 0.5
        else:
            depth_score = deep_count / (surface_count + deep_count)
            depth_score = depth_score * 0.7 + length_factor * 0.3

        return min(1.0, depth_score)

    def _extract_trust_indicators(self, message: str) -> list[str]:
        """Extract indicators of trust/comfort with the AI"""
        trust_phrases = [
            "I trust you",
            "I feel comfortable",
            "you understand me",
            "I can tell you",
            "between us",
            "privately",
            "confidentially",
            "I'm sharing this",
            "you're helpful",
            "I appreciate",
            "you get it",
            "you understand",
            "I feel safe",
        ]

        found_indicators = []
        message_lower = message.lower()

        for phrase in trust_phrases:
            if phrase in message_lower:
                found_indicators.append(phrase)

        return found_indicators

    def _extract_adaptation_requests(self, user_message: str, _bot_response: str) -> list[str]:
        """Extract explicit requests for AI behavior changes"""
        adaptation_phrases = [
            "be more",
            "less",
            "could you",
            "please don't",
            "I prefer",
            "I'd like you to",
            "it would be better if",
            "instead of",
            "rather than",
            "tone down",
            "more formal",
            "more casual",
            "shorter responses",
            "longer responses",
            "more detail",
            "less detail",
        ]

        requests = []
        user_lower = user_message.lower()

        for phrase in adaptation_phrases:
            if phrase in user_lower:
                # Extract the full sentence containing the request
                sentences = user_message.split(".")
                for sentence in sentences:
                    if phrase in sentence.lower():
                        requests.append(sentence.strip())

        return requests

    async def _update_communication_style(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update communication style traits"""
        # Update formality preference
        await self._update_trait(
            profile,
            PersonalityDimension.COMMUNICATION_STYLE,
            analysis.formality_score,
            f"conversation_{analysis.timestamp.isoformat()}",
        )

        # Update detail preference
        await self._update_trait(
            profile,
            PersonalityDimension.CONVERSATION_DEPTH,
            analysis.detail_preference,
            f"detail_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_emotional_expression(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update emotional expression traits"""
        await self._update_trait(
            profile,
            PersonalityDimension.EMOTIONAL_EXPRESSION,
            analysis.emotional_openness,
            f"emotional_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_social_engagement(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update social engagement traits based on conversation patterns"""
        # Use question ratio as indicator of social engagement
        engagement_score = (
            analysis.question_ratio * 0.7 + (1.0 if analysis.humor_detected else 0.0) * 0.3
        )

        await self._update_trait(
            profile,
            PersonalityDimension.SOCIAL_ENGAGEMENT,
            engagement_score,
            f"social_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_learning_style(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update learning style preferences"""
        # Knowledge sharing indicates structured learning preference
        learning_score = 1.0 if analysis.knowledge_sharing else 0.0

        await self._update_trait(
            profile,
            PersonalityDimension.LEARNING_STYLE,
            learning_score,
            f"learning_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_support_preferences(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update support and help-seeking preferences"""
        support_score = 1.0 if analysis.support_seeking else 0.0

        await self._update_trait(
            profile,
            PersonalityDimension.SUPPORT_PREFERENCES,
            support_score,
            f"support_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_trust_level(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update trust level based on conversation openness and trust indicators"""
        trust_score = len(analysis.trust_indicators) * 0.3 + analysis.conversation_depth * 0.7

        await self._update_trait(
            profile,
            PersonalityDimension.TRUST_LEVEL,
            min(1.0, trust_score),
            f"trust_analysis_{analysis.timestamp.isoformat()}",
        )

    async def _update_trait(
        self,
        profile: PersonalityProfile,
        dimension: PersonalityDimension,
        new_value: float,
        evidence_source: str,
    ):
        """Update a personality trait with new evidence"""

        if dimension not in profile.traits:
            # Create new trait
            profile.traits[dimension] = PersonalityTrait(
                dimension=dimension,
                value=new_value,
                confidence=0.1,  # Low initial confidence
                last_updated=datetime.now(),
                evidence_count=1,
                evidence_sources=[evidence_source],
            )
        else:
            trait = profile.traits[dimension]

            # Calculate weighted average with existing value
            weight_existing = min(0.9, trait.evidence_count / (trait.evidence_count + 1))
            weight_new = 1.0 - weight_existing

            new_trait_value = trait.value * weight_existing + new_value * weight_new

            # Only update if change is significant
            if abs(new_trait_value - trait.value) >= self.update_threshold:
                trait.value = new_trait_value
                trait.evidence_count += 1
                trait.last_updated = datetime.now()
                trait.evidence_sources.append(evidence_source)

                # Keep only recent evidence sources
                if len(trait.evidence_sources) > 10:
                    trait.evidence_sources = trait.evidence_sources[-10:]

                # Update confidence based on evidence count
                trait.confidence = min(1.0, trait.evidence_count / self.min_conversations)

    async def _update_relationship_depth(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update relationship depth based on conversation patterns"""
        # Factors that increase relationship depth
        depth_increase = 0.0

        # Deep conversations increase relationship depth
        depth_increase += analysis.conversation_depth * 0.1

        # Trust indicators increase relationship depth
        depth_increase += len(analysis.trust_indicators) * 0.05

        # Emotional openness increases relationship depth
        depth_increase += analysis.emotional_openness * 0.05

        # Update with exponential smoothing
        profile.relationship_depth = min(1.0, profile.relationship_depth * 0.95 + depth_increase)

    async def _update_response_preferences(
        self, profile: PersonalityProfile, analysis: ConversationAnalysis
    ):
        """Update AI response preferences based on user adaptation requests"""

        for request in analysis.adaptation_requests:
            # Parse adaptation requests to update preferences
            request_lower = request.lower()

            if "more formal" in request_lower:
                profile.preferred_response_style["formality"] = "formal"
            elif "more casual" in request_lower or "less formal" in request_lower:
                profile.preferred_response_style["formality"] = "casual"

            if "shorter" in request_lower or "brief" in request_lower:
                profile.preferred_response_style["length"] = "brief"
            elif "longer" in request_lower or "more detail" in request_lower:
                profile.preferred_response_style["length"] = "detailed"

            if "more help" in request_lower or "more guidance" in request_lower:
                profile.preferred_response_style["support_level"] = "high"
            elif "less help" in request_lower or "more independent" in request_lower:
                profile.preferred_response_style["support_level"] = "low"

    async def get_personality_profile(self, user_id: str) -> PersonalityProfile | None:
        """Get current personality profile for a user"""
        return self.profiles.get(user_id)

    async def get_adaptation_recommendations(self, user_id: str) -> dict[str, Any]:
        """Get AI behavior adaptation recommendations for a user"""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No personality profile found"}

        recommendations = {
            "communication_style": {},
            "emotional_approach": {},
            "support_strategy": {},
            "conversation_tactics": {},
            "confidence_level": 0.0,
        }

        # Calculate overall confidence
        if profile.traits:
            avg_confidence = statistics.mean(trait.confidence for trait in profile.traits.values())
            recommendations["confidence_level"] = avg_confidence

        # Communication style recommendations
        if PersonalityDimension.COMMUNICATION_STYLE in profile.traits:
            comm_trait = profile.traits[PersonalityDimension.COMMUNICATION_STYLE]
            if comm_trait.value > 0.3:
                recommendations["communication_style"]["formality"] = "casual"
                recommendations["communication_style"]["tone"] = "friendly and relaxed"
            elif comm_trait.value < -0.3:
                recommendations["communication_style"]["formality"] = "formal"
                recommendations["communication_style"]["tone"] = "professional and respectful"
            else:
                recommendations["communication_style"]["formality"] = "balanced"
                recommendations["communication_style"]["tone"] = "adaptable"

        # Emotional approach recommendations
        if PersonalityDimension.EMOTIONAL_EXPRESSION in profile.traits:
            emotion_trait = profile.traits[PersonalityDimension.EMOTIONAL_EXPRESSION]
            if emotion_trait.value > 0.5:
                recommendations["emotional_approach"]["expressiveness"] = "high"
                recommendations["emotional_approach"][
                    "empathy_level"
                ] = "strong emotional validation"
            else:
                recommendations["emotional_approach"]["expressiveness"] = "moderate"
                recommendations["emotional_approach"]["empathy_level"] = "thoughtful but reserved"

        # Support strategy recommendations
        if PersonalityDimension.SUPPORT_PREFERENCES in profile.traits:
            support_trait = profile.traits[PersonalityDimension.SUPPORT_PREFERENCES]
            if support_trait.value > 0.5:
                recommendations["support_strategy"]["approach"] = "proactive guidance"
                recommendations["support_strategy"]["detail_level"] = "comprehensive explanations"
            else:
                recommendations["support_strategy"]["approach"] = "wait for explicit requests"
                recommendations["support_strategy"]["detail_level"] = "concise responses"

        # Trust-based recommendations
        if PersonalityDimension.TRUST_LEVEL in profile.traits:
            trust_trait = profile.traits[PersonalityDimension.TRUST_LEVEL]
            if trust_trait.value > 0.7:
                recommendations["conversation_tactics"]["depth"] = "can discuss personal topics"
                recommendations["conversation_tactics"][
                    "initiative"
                ] = "can ask follow-up questions"
            else:
                recommendations["conversation_tactics"]["depth"] = "stick to surface-level topics"
                recommendations["conversation_tactics"][
                    "initiative"
                ] = "respond rather than initiate"

        # Add user preferences from explicit requests
        if profile.preferred_response_style:
            recommendations["explicit_preferences"] = profile.preferred_response_style

        return recommendations

    async def get_personality_summary(self, user_id: str) -> dict[str, Any]:
        """Get a comprehensive personality summary for a user"""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No personality profile found"}

        summary = {
            "user_id": user_id,
            "profile_age_days": (datetime.now() - profile.created_at).days,
            "total_conversations": profile.total_conversations,
            "relationship_depth": profile.relationship_depth,
            "trust_level": profile.trust_level,
            "personality_traits": {},
            "conversation_patterns": {},
            "adaptation_history": profile.preferred_response_style,
            "confidence_metrics": {},
        }

        # Personality traits summary
        for dimension, trait in profile.traits.items():
            summary["personality_traits"][dimension.value] = {
                "value": trait.value,
                "confidence": trait.confidence,
                "evidence_count": trait.evidence_count,
                "last_updated": trait.last_updated.isoformat(),
            }

        # Recent conversation patterns
        if profile.conversation_analyses:
            recent_analyses = list(profile.conversation_analyses)[-10:]  # Last 10 conversations

            summary["conversation_patterns"] = {
                "avg_message_length": statistics.mean(a.message_length for a in recent_analyses),
                "avg_formality": statistics.mean(a.formality_score for a in recent_analyses),
                "avg_emotional_openness": statistics.mean(
                    a.emotional_openness for a in recent_analyses
                ),
                "humor_frequency": sum(1 for a in recent_analyses if a.humor_detected)
                / len(recent_analyses),
                "support_seeking_frequency": sum(1 for a in recent_analyses if a.support_seeking)
                / len(recent_analyses),
                "top_topics": self._get_top_topics(recent_analyses),
            }

        # Confidence metrics
        if profile.traits:
            confidences = [trait.confidence for trait in profile.traits.values()]
            summary["confidence_metrics"] = {
                "overall_confidence": statistics.mean(confidences),
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "traits_high_confidence": sum(1 for c in confidences if c >= 0.7),
                "traits_total": len(confidences),
            }

        return summary

    def _get_top_topics(self, analyses: list[ConversationAnalysis]) -> list[str]:
        """Get most frequently discussed topics from recent conversations"""
        topic_counts = defaultdict(int)

        for analysis in analyses:
            for topic in analysis.topics_discussed:
                topic_counts[topic] += 1

        # Return top 5 topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]

    # Database Persistence Methods

    def _get_db_connection(self):
        """Get database connection for personality data persistence"""
        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL not available - personality data will not persist")
            return None

        try:
            connection = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "whisper_engine"),
                user=os.getenv("POSTGRES_USER", "bot_user"),
                password=os.getenv("POSTGRES_PASSWORD", "bot_password_change_me"),
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL for personality persistence: {e}")
            return None

    def _ensure_personality_tables(self):
        """Ensure personality tables exist in the database"""
        if not POSTGRES_AVAILABLE:
            return False

        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                # Dynamic personality profiles table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dynamic_personality_profiles (
                        user_id VARCHAR(255) PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_conversations INTEGER DEFAULT 0,
                        relationship_depth FLOAT DEFAULT 0.0,
                        trust_level FLOAT DEFAULT 0.0,
                        preferred_response_style JSONB DEFAULT '{}'::jsonb
                    )
                """
                )

                # Personality traits table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dynamic_personality_traits (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255),
                        dimension VARCHAR(100),
                        value FLOAT,
                        confidence FLOAT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        evidence_count INTEGER DEFAULT 0,
                        evidence_sources JSONB DEFAULT '[]'::jsonb,
                        CONSTRAINT fk_user_profile
                            FOREIGN KEY (user_id)
                            REFERENCES dynamic_personality_profiles(user_id)
                            ON DELETE CASCADE
                    )
                """
                )

                # Conversation analyses table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dynamic_conversation_analyses (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255),
                        context_id VARCHAR(255),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_length INTEGER,
                        formality_score FLOAT,
                        emotional_openness FLOAT,
                        conversation_depth FLOAT,
                        topics_discussed JSONB DEFAULT '[]'::jsonb,
                        emotional_tone VARCHAR(50),
                        humor_detected BOOLEAN DEFAULT FALSE,
                        support_seeking BOOLEAN DEFAULT FALSE,
                        CONSTRAINT fk_user_profile_analysis
                            FOREIGN KEY (user_id)
                            REFERENCES dynamic_personality_profiles(user_id)
                            ON DELETE CASCADE
                    )
                """
                )

                # Indexes for performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_dynamic_personality_traits_user_id
                    ON dynamic_personality_traits(user_id)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_dynamic_conversation_analyses_user_id
                    ON dynamic_conversation_analyses(user_id)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_dynamic_conversation_analyses_timestamp
                    ON dynamic_conversation_analyses(timestamp)
                """
                )

                connection.commit()
                logger.info("Dynamic personality database tables ensured")
                return True

        except Exception as e:
            logger.error(f"Failed to create personality tables: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()

    async def save_profile_to_db(self, user_id: str, profile: PersonalityProfile):
        """Save personality profile to PostgreSQL database"""
        if not POSTGRES_AVAILABLE:
            return False

        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                # Insert or update profile
                cursor.execute(
                    """
                    INSERT INTO dynamic_personality_profiles
                    (user_id, updated_at, total_conversations, relationship_depth, trust_level, preferred_response_style)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        updated_at = EXCLUDED.updated_at,
                        total_conversations = EXCLUDED.total_conversations,
                        relationship_depth = EXCLUDED.relationship_depth,
                        trust_level = EXCLUDED.trust_level,
                        preferred_response_style = EXCLUDED.preferred_response_style
                """,
                    (
                        user_id,
                        datetime.now(),
                        profile.total_conversations,
                        profile.relationship_depth,
                        profile.trust_level,
                        json.dumps(profile.preferred_response_style),
                    ),
                )

                # Delete old traits and insert new ones
                cursor.execute(
                    "DELETE FROM dynamic_personality_traits WHERE user_id = %s", (user_id,)
                )

                for dimension, trait in profile.traits.items():
                    cursor.execute(
                        """
                        INSERT INTO dynamic_personality_traits
                        (user_id, dimension, value, confidence, last_updated, evidence_count, evidence_sources)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            user_id,
                            dimension.value,
                            trait.value,
                            trait.confidence,
                            trait.last_updated,
                            trait.evidence_count,
                            json.dumps(trait.evidence_sources),
                        ),
                    )

                connection.commit()
                logger.debug(f"Saved personality profile for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save personality profile for user {user_id}: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()

    def _safe_json_loads(self, value, default=None) -> list:
        """Safely load JSON data, handling various input types and ensuring list output"""
        if value is None:
            return default if default is not None else []

        # If it's already a list, return it
        if isinstance(value, list):
            return value

        # If it's a dict, convert to list if possible, otherwise return default
        if isinstance(value, dict):
            logger.warning(f"Expected list but got dict: {value}")
            return default if default is not None else []

        # If it's a string, try to parse it as JSON
        if isinstance(value, str):
            if not value.strip():
                return default if default is not None else []
            try:
                result = json.loads(value)
                # Ensure result is a list
                if isinstance(result, list):
                    return result
                else:
                    logger.warning(f"JSON parsed to non-list type: {type(result)}")
                    return default if default is not None else []
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON: {value[:50]}... Error: {e}")
                return default if default is not None else []

        # For any other type, return default
        logger.warning(f"Unexpected value type for JSON parsing: {type(value)} - {value}")
        return default if default is not None else []

    async def load_profile_from_db(self, user_id: str) -> PersonalityProfile | None:
        """Load personality profile from PostgreSQL database"""
        if not POSTGRES_AVAILABLE:
            return None

        connection = self._get_db_connection()
        if not connection:
            return None

        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Load profile
                cursor.execute(
                    """
                    SELECT * FROM dynamic_personality_profiles WHERE user_id = %s
                """,
                    (user_id,),
                )
                profile_row = cursor.fetchone()

                if not profile_row:
                    return None

                # Load traits
                cursor.execute(
                    """
                    SELECT * FROM dynamic_personality_traits WHERE user_id = %s
                """,
                    (user_id,),
                )
                trait_rows = cursor.fetchall()

                # Load recent conversation analyses
                cursor.execute(
                    """
                    SELECT * FROM dynamic_conversation_analyses
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 50
                """,
                    (user_id,),
                )
                analysis_rows = cursor.fetchall()

                # Reconstruct profile
                traits = {}
                for trait_row in trait_rows:
                    dimension = PersonalityDimension(trait_row["dimension"])
                    traits[dimension] = PersonalityTrait(
                        dimension=dimension,
                        value=trait_row["value"],
                        confidence=trait_row["confidence"],
                        last_updated=trait_row["last_updated"],
                        evidence_count=trait_row["evidence_count"],
                        evidence_sources=self._safe_json_loads(trait_row["evidence_sources"], []),
                    )

                conversation_analyses = deque(maxlen=50)
                for analysis_row in analysis_rows:
                    analysis = ConversationAnalysis(
                        user_id=analysis_row["user_id"],
                        context_id=analysis_row["context_id"],
                        timestamp=analysis_row["timestamp"],
                        message_length=analysis_row["message_length"],
                        response_time_seconds=None,  # Not stored in DB
                        emotional_tone=analysis_row["emotional_tone"] or "neutral",
                        topics_discussed=self._safe_json_loads(
                            analysis_row["topics_discussed"], []
                        ),
                        formality_score=analysis_row["formality_score"] or 0.0,
                        detail_preference=0.0,  # Can be derived if needed
                        emotional_openness=analysis_row["emotional_openness"] or 0.0,
                        question_ratio=0.0,  # Can be derived if needed
                        humor_detected=analysis_row["humor_detected"] or False,
                        support_seeking=analysis_row["support_seeking"] or False,
                        knowledge_sharing=False,  # Can be derived if needed
                        conversation_depth=analysis_row["conversation_depth"] or 0.0,
                        trust_indicators=[],  # Can be derived if needed
                        adaptation_requests=[],  # Can be derived if needed
                    )
                    conversation_analyses.append(analysis)

                profile = PersonalityProfile(
                    user_id=user_id,
                    created_at=profile_row["created_at"],
                    last_updated=profile_row["updated_at"],
                    traits=traits,
                    conversation_analyses=conversation_analyses,
                    total_conversations=profile_row["total_conversations"],
                    relationship_depth=profile_row["relationship_depth"],
                    trust_level=profile_row["trust_level"],
                    adaptation_success_rate=0.5,  # Default value - can be enhanced later
                    preferred_response_style=json.loads(
                        profile_row["preferred_response_style"] or "{}"
                    ),
                    effective_conversation_patterns=[],  # Can be derived from analysis data
                    topics_of_high_engagement=[],  # Can be derived from analysis data
                )

                logger.debug(f"Loaded personality profile for user {user_id}")
                return profile

        except Exception as e:
            logger.error(f"Failed to load personality profile for user {user_id}: {e}")
            return None
        finally:
            connection.close()

    async def save_conversation_analysis(self, analysis: ConversationAnalysis):
        """Save conversation analysis to database"""
        if not POSTGRES_AVAILABLE:
            return False

        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dynamic_conversation_analyses
                    (user_id, context_id, timestamp, message_length, formality_score,
                     emotional_openness, conversation_depth, topics_discussed,
                     emotional_tone, humor_detected, support_seeking)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        analysis.user_id,
                        analysis.context_id,
                        analysis.timestamp,
                        analysis.message_length,
                        analysis.formality_score,
                        analysis.emotional_openness,
                        analysis.conversation_depth,
                        json.dumps(analysis.topics_discussed),
                        analysis.emotional_tone,
                        analysis.humor_detected,
                        analysis.support_seeking,
                    ),
                )

                connection.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to save conversation analysis: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()

    async def initialize_persistence(self):
        """Initialize database persistence for personality profiles"""
        if POSTGRES_AVAILABLE:
            self._ensure_personality_tables()
            logger.info("Dynamic personality persistence initialized")
        else:
            logger.warning(
                "PostgreSQL not available - personality profiles will not persist across restarts"
            )


# Enhanced DynamicPersonalityProfiler with database persistence
class PersistentDynamicPersonalityProfiler(DynamicPersonalityProfiler):
    """
    Enhanced Dynamic Personality Profiler with automatic database persistence.

    This class extends the base DynamicPersonalityProfiler to automatically
    save and load personality profiles from PostgreSQL database.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistence_enabled = POSTGRES_AVAILABLE

        # Initialize database schema and load existing profiles
        if self.persistence_enabled:
            asyncio.create_task(self.initialize_persistence())

    async def update_personality_profile(
        self, analysis: ConversationAnalysis
    ) -> PersonalityProfile:
        """Update personality profile with automatic database persistence"""
        # Load existing profile from database if not in memory
        if analysis.user_id not in self.profiles and self.persistence_enabled:
            db_profile = await self.load_profile_from_db(analysis.user_id)
            if db_profile:
                self.profiles[analysis.user_id] = db_profile

        # Update profile using parent method
        profile = await super().update_personality_profile(analysis)

        # Save to database
        if self.persistence_enabled:
            await self.save_profile_to_db(analysis.user_id, profile)
            await self.save_conversation_analysis(analysis)

        return profile


# Global instance for use across the application - now with persistence!
dynamic_personality_profiler = PersistentDynamicPersonalityProfiler()
