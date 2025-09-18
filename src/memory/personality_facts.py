"""
Personality-Focused Fact Classification System

This module replaces the global/user fact distinction with a personality-driven
classification system that maximizes AI companion engagement and relationship building.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.security.pii_detector import PIIDetector

logger = logging.getLogger(__name__)


class PersonalityFactType(Enum):
    """Types of facts that enhance AI companion personality and relationships"""

    # Core personality building facts
    EMOTIONAL_INSIGHT = "emotional_insight"  # User's emotional patterns, triggers, responses
    COMMUNICATION_PREFERENCE = "communication_pref"  # How user likes to interact
    RELATIONSHIP_BUILDING = "relationship_building"  # Moments that strengthen connection
    INTEREST_DISCOVERY = "interest_discovery"  # User's passions, hobbies, curiosities
    SUPPORT_OPPORTUNITY = "support_opportunity"  # When user needs encouragement/help

    # Behavioral and preference facts
    HUMOR_STYLE = "humor_style"  # What makes user laugh
    LEARNING_STYLE = "learning_style"  # How user processes information
    PERSONALITY_TRAIT = "personality_trait"  # User's character traits
    VALUE_SYSTEM = "value_system"  # What user finds important
    LIFE_CONTEXT = "life_context"  # Current life situation/phase

    # Interaction enhancement facts
    CONVERSATION_CATALYST = "conversation_catalyst"  # Topics that engage user
    SHARED_MEMORY = "shared_memory"  # Memorable moments between AI and user
    GROWTH_MOMENT = "growth_moment"  # User's personal development
    TRUST_INDICATOR = "trust_indicator"  # Signs of growing trust/comfort
    BOUNDARY_PREFERENCE = "boundary_preference"  # User's comfort zones and limits

    # Knowledge and capability facts
    EXPERTISE_AREA = "expertise_area"  # What user knows well
    KNOWLEDGE_GAP = "knowledge_gap"  # What user wants to learn
    SKILL_DEVELOPMENT = "skill_development"  # User's learning journey
    ACHIEVEMENT = "achievement"  # User's accomplishments
    ASPIRATION = "aspiration"  # User's goals and dreams


class PersonalityRelevance(Enum):
    """How much a fact contributes to personality and relationship building"""

    CRITICAL = "critical"  # Essential for understanding user (score: 0.9-1.0)
    HIGH = "high"  # Very important for personality (score: 0.7-0.89)
    MODERATE = "moderate"  # Useful for relationship (score: 0.5-0.69)
    LOW = "low"  # Minor personality insight (score: 0.3-0.49)
    MINIMAL = "minimal"  # Little personality value (score: 0.0-0.29)


@dataclass
class PersonalityFact:
    """A fact that enhances AI companion personality and relationships"""

    content: str
    fact_type: PersonalityFactType
    relevance: PersonalityRelevance
    relevance_score: float
    emotional_weight: float
    privacy_level: str
    context_metadata: dict
    extraction_confidence: float
    last_accessed: datetime
    access_frequency: int
    user_id: str

    def to_storage_dict(self) -> dict:
        """Convert to dictionary for database storage with flattened metadata"""
        storage_dict = {
            "content": self.content,
            "fact_type": self.fact_type.value,
            "relevance": self.relevance.value,
            "relevance_score": self.relevance_score,
            "emotional_weight": self.emotional_weight,
            "privacy_level": self.privacy_level,
            "extraction_confidence": self.extraction_confidence,
            "last_accessed": self.last_accessed.isoformat(),
            "access_frequency": self.access_frequency,
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "version": "personality_v1",
            "type": "personality_fact",  # Mark as personality fact for retrieval
        }

        # Flatten context metadata to avoid nested dictionaries (ChromaDB limitation)
        if self.context_metadata:
            for key, value in self.context_metadata.items():
                # Prefix context keys to avoid conflicts
                flattened_key = f"context_{key}"
                # Convert value to proper ChromaDB-compatible types
                if value is None:
                    # Skip None values entirely as ChromaDB doesn't handle them well
                    continue
                elif isinstance(value, (str, int, float, bool)):
                    storage_dict[flattened_key] = value
                else:
                    # Convert all other types to string
                    storage_dict[flattened_key] = str(value)

        return storage_dict


class PersonalityFactClassifier:
    """
    Classifies facts based on their potential for personality development and
    relationship building rather than global vs user categorization
    """

    def __init__(self, pii_detector: PIIDetector | None = None):
        self.pii_detector = pii_detector or PIIDetector()
        self.setup_classification_patterns()
        self.setup_relevance_scoring()

    def setup_classification_patterns(self):
        """Setup patterns for classifying personality fact types"""

        self.fact_type_patterns = {
            PersonalityFactType.EMOTIONAL_INSIGHT: {
                "keywords": [
                    "feel",
                    "feeling",
                    "emotion",
                    "emotional",
                    "mood",
                    "anxiety",
                    "depression",
                    "happy",
                    "sad",
                    "excited",
                    "nervous",
                    "stressed",
                    "calm",
                    "overwhelmed",
                    "triggered by",
                    "makes me",
                    "i get",
                    "when i",
                    "i become",
                ],
                "patterns": [
                    r"i feel \w+ when",
                    r"makes? me (feel|get) \w+",
                    r"i (get|become) \w+ (when|if)",
                    r"i\'m (usually|often|always) \w+ (when|about)",
                ],
            },
            PersonalityFactType.COMMUNICATION_PREFERENCE: {
                "keywords": [
                    "prefer",
                    "like when",
                    "appreciate",
                    "communication",
                    "explain",
                    "detail",
                    "direct",
                    "gentle",
                    "humor",
                    "funny",
                    "serious",
                    "formal",
                    "casual",
                    "speak to me",
                    "talk to me",
                    "respond",
                    "answer",
                ],
                "patterns": [
                    r"i prefer (when|if) you",
                    r"i like it when",
                    r"please (be|talk|speak)",
                    r"i appreciate (when|if)",
                    r"(don\'t|please don\'t) be too",
                ],
            },
            PersonalityFactType.INTEREST_DISCOVERY: {
                "keywords": [
                    "love",
                    "enjoy",
                    "passionate",
                    "hobby",
                    "interest",
                    "fascinated",
                    "favorite",
                    "obsessed",
                    "into",
                    "fan of",
                    "collecting",
                    "studying",
                    "playing",
                    "watching",
                    "reading",
                    "listening to",
                ],
                "patterns": [
                    r"i (love|enjoy|like) \w+",
                    r"my (favorite|passion|hobby) is",
                    r"i\'m (into|interested in|passionate about)",
                    r"i spend time \w+ing",
                ],
            },
            PersonalityFactType.SUPPORT_OPPORTUNITY: {
                "keywords": [
                    "struggling",
                    "difficult",
                    "hard time",
                    "challenge",
                    "problem",
                    "worried",
                    "concerned",
                    "help",
                    "support",
                    "advice",
                    "guidance",
                    "don't know",
                    "confused",
                    "stuck",
                    "overwhelmed",
                ],
                "patterns": [
                    r"i\'m (struggling|having trouble) with",
                    r"i need (help|advice|support) with",
                    r"i don\'t know (how to|what to)",
                    r"this is (difficult|hard|challenging)",
                ],
            },
            PersonalityFactType.ACHIEVEMENT: {
                "keywords": [
                    "accomplished",
                    "achieved",
                    "succeeded",
                    "completed",
                    "finished",
                    "graduated",
                    "promoted",
                    "learned",
                    "mastered",
                    "overcome",
                    "proud",
                    "excited",
                    "milestone",
                ],
                "patterns": [
                    r"i (just|recently|finally) \w+",
                    r"i\'m proud (of|that)",
                    r"i accomplished",
                    r"i (completed|finished|achieved)",
                ],
            },
            PersonalityFactType.RELATIONSHIP_BUILDING: {
                "keywords": [
                    "trust",
                    "comfortable",
                    "safe",
                    "understand",
                    "connection",
                    "appreciate you",
                    "thank you",
                    "helpful",
                    "caring",
                    "support",
                    "remember when",
                    "like talking",
                    "enjoy our",
                ],
                "patterns": [
                    r"i trust (you|that you)",
                    r"i feel (comfortable|safe) (with|telling)",
                    r"you (understand|get) me",
                    r"i (appreciate|like) (that you|how you)",
                ],
            },
        }

    def setup_relevance_scoring(self):
        """Setup scoring weights for personality relevance"""

        # Base scores by fact type
        self.base_relevance_scores = {
            PersonalityFactType.EMOTIONAL_INSIGHT: 0.85,
            PersonalityFactType.COMMUNICATION_PREFERENCE: 0.80,
            PersonalityFactType.RELATIONSHIP_BUILDING: 0.90,
            PersonalityFactType.INTEREST_DISCOVERY: 0.75,
            PersonalityFactType.SUPPORT_OPPORTUNITY: 0.88,
            PersonalityFactType.HUMOR_STYLE: 0.70,
            PersonalityFactType.LEARNING_STYLE: 0.65,
            PersonalityFactType.PERSONALITY_TRAIT: 0.82,
            PersonalityFactType.VALUE_SYSTEM: 0.78,
            PersonalityFactType.LIFE_CONTEXT: 0.73,
            PersonalityFactType.CONVERSATION_CATALYST: 0.68,
            PersonalityFactType.SHARED_MEMORY: 0.85,
            PersonalityFactType.GROWTH_MOMENT: 0.80,
            PersonalityFactType.TRUST_INDICATOR: 0.92,
            PersonalityFactType.BOUNDARY_PREFERENCE: 0.87,
            PersonalityFactType.EXPERTISE_AREA: 0.60,
            PersonalityFactType.KNOWLEDGE_GAP: 0.58,
            PersonalityFactType.SKILL_DEVELOPMENT: 0.63,
            PersonalityFactType.ACHIEVEMENT: 0.72,
            PersonalityFactType.ASPIRATION: 0.76,
        }

        # Modifiers based on emotional weight and specificity
        self.scoring_modifiers = {
            "high_emotional_weight": 0.15,  # Very emotional content
            "specific_detail": 0.10,  # Specific vs general statements
            "repeated_mention": 0.08,  # User mentions multiple times
            "vulnerability_shared": 0.12,  # User sharing something personal
            "direct_feedback": 0.10,  # Direct feedback about AI interaction
            "growth_indicator": 0.08,  # Shows personal development
            "relationship_milestone": 0.15,  # Significant relationship moment
        }

    def classify_fact(
        self, fact_content: str, context_metadata: dict, user_id: str
    ) -> PersonalityFact:
        """
        Classify a fact for personality enhancement potential

        Args:
            fact_content: The fact text to classify
            context_metadata: Context information about where fact was extracted
            user_id: User ID for privacy context

        Returns:
            PersonalityFact with classification and scoring
        """
        try:
            # Step 1: Analyze for PII and privacy
            pii_analysis = self.pii_detector.analyze_fact_for_pii(fact_content)

            # Step 2: Classify personality fact type
            fact_type = self._determine_fact_type(fact_content)

            # Step 3: Calculate personality relevance score
            relevance_score, emotional_weight = self._calculate_relevance_score(
                fact_content, fact_type, context_metadata
            )

            # Step 4: Determine relevance category
            relevance = self._score_to_relevance_category(relevance_score)

            # Step 5: Set privacy level from PII analysis
            privacy_level = pii_analysis.recommended_security_level

            personality_fact = PersonalityFact(
                content=fact_content,
                fact_type=fact_type,
                relevance=relevance,
                relevance_score=relevance_score,
                emotional_weight=emotional_weight,
                privacy_level=privacy_level,
                context_metadata=context_metadata,
                extraction_confidence=0.8,  # Default, could be enhanced
                last_accessed=datetime.now(),
                access_frequency=0,
                user_id=user_id,
            )

            logger.debug(
                "Classified personality fact: %s (relevance: %.2f)",
                fact_type.value,
                relevance_score,
            )

            return personality_fact

        except Exception as e:
            logger.error(f"Error classifying personality fact: {e}")
            # Return conservative classification for safety
            return self._create_safe_fallback_fact(fact_content, context_metadata, user_id)

    def _determine_fact_type(self, fact_content: str) -> PersonalityFactType:
        """Determine the personality fact type based on content analysis"""
        fact_lower = fact_content.lower()
        scores = {}

        for fact_type, patterns in self.fact_type_patterns.items():
            score = 0

            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in fact_lower:
                    score += 1

            # Check regex patterns
            for pattern in patterns["patterns"]:
                if re.search(pattern, fact_lower):
                    score += 2  # Patterns are more specific, weight them higher

            scores[fact_type] = score

        # Return the fact type with highest score, or default to interest discovery
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type

        # Default classification for unmatched content
        return PersonalityFactType.INTEREST_DISCOVERY

    def _calculate_relevance_score(
        self, fact_content: str, fact_type: PersonalityFactType, context_metadata: dict
    ) -> tuple[float, float]:
        """Calculate personality relevance score and emotional weight"""

        base_score = self.base_relevance_scores.get(fact_type, 0.5)
        emotional_weight = self._calculate_emotional_weight(fact_content)

        # Apply modifiers based on content analysis
        modifiers = 0
        fact_lower = fact_content.lower()

        # High emotional weight modifier
        if emotional_weight > 0.7:
            modifiers += self.scoring_modifiers["high_emotional_weight"]

        # Specificity modifier (longer, more detailed facts)
        if len(fact_content.split()) > 10:
            modifiers += self.scoring_modifiers["specific_detail"]

        # Vulnerability sharing modifier
        vulnerability_indicators = ["i feel", "i'm scared", "i worry", "i struggle", "i'm afraid"]
        if any(indicator in fact_lower for indicator in vulnerability_indicators):
            modifiers += self.scoring_modifiers["vulnerability_shared"]

        # Direct feedback modifier
        feedback_indicators = ["you", "your", "this ai", "appreciate", "helpful"]
        if any(indicator in fact_lower for indicator in feedback_indicators):
            modifiers += self.scoring_modifiers["direct_feedback"]

        # Growth indicator modifier
        growth_indicators = ["learned", "improved", "overcome", "better at", "progress"]
        if any(indicator in fact_lower for indicator in growth_indicators):
            modifiers += self.scoring_modifiers["growth_indicator"]

        final_score = min(1.0, base_score + modifiers)

        return final_score, emotional_weight

    def _calculate_emotional_weight(self, fact_content: str) -> float:
        """Calculate how emotionally significant a fact is"""
        fact_lower = fact_content.lower()
        emotional_weight = 0.0

        # Strong emotional indicators
        strong_emotions = ["love", "hate", "terrified", "devastated", "overjoyed", "heartbroken"]
        for emotion in strong_emotions:
            if emotion in fact_lower:
                emotional_weight += 0.3

        # Moderate emotional indicators
        moderate_emotions = ["happy", "sad", "angry", "excited", "worried", "anxious"]
        for emotion in moderate_emotions:
            if emotion in fact_lower:
                emotional_weight += 0.2

        # Emotional context indicators
        emotional_contexts = ["i feel", "makes me", "i get", "i become", "emotional"]
        for context in emotional_contexts:
            if context in fact_lower:
                emotional_weight += 0.15

        return min(1.0, emotional_weight)

    def _score_to_relevance_category(self, score: float) -> PersonalityRelevance:
        """Convert numeric score to relevance category"""
        if score >= 0.9:
            return PersonalityRelevance.CRITICAL
        elif score >= 0.7:
            return PersonalityRelevance.HIGH
        elif score >= 0.5:
            return PersonalityRelevance.MODERATE
        elif score >= 0.3:
            return PersonalityRelevance.LOW
        else:
            return PersonalityRelevance.MINIMAL

    def _create_safe_fallback_fact(
        self, fact_content: str, context_metadata: dict, user_id: str
    ) -> PersonalityFact:
        """Create a safe fallback fact when classification fails"""
        return PersonalityFact(
            content=fact_content,
            fact_type=PersonalityFactType.INTEREST_DISCOVERY,
            relevance=PersonalityRelevance.LOW,
            relevance_score=0.3,
            emotional_weight=0.1,
            privacy_level="private_dm",  # Conservative privacy
            context_metadata=context_metadata,
            extraction_confidence=0.5,
            last_accessed=datetime.now(),
            access_frequency=0,
            user_id=user_id,
        )


def get_personality_fact_classifier() -> PersonalityFactClassifier:
    """Get a personality fact classifier instance (singleton pattern)"""
    if not hasattr(get_personality_fact_classifier, "_instance"):
        from src.security.pii_detector import get_pii_detector

        get_personality_fact_classifier._instance = PersonalityFactClassifier(get_pii_detector())
    return get_personality_fact_classifier._instance
