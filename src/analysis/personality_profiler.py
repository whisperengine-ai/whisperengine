"""
Advanced Personality Profiler
============================

Analyzes user communication patterns to build comprehensive personality profiles.
Works with graph database to enhance relationship understanding.

Features:
- Communication style analysis (formal/casual, direct/indirect)
- Emotional expression patterns
- Decision-making style detection
- Learning preference identification
- Social interaction analysis
- Personality trait scoring (Big Five model)
"""

import logging
import re
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import spacy

logger = logging.getLogger(__name__)


class CommunicationStyle(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    MIXED = "mixed"


class DirectnessStyle(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    DIPLOMATIC = "diplomatic"


class DecisionStyle(Enum):
    QUICK = "quick"
    DELIBERATE = "deliberate"
    IMPULSIVE = "impulsive"
    ANALYTICAL = "analytical"


@dataclass
class PersonalityMetrics:
    """Comprehensive personality analysis metrics"""

    # Big Five personality traits (0-1 scale)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Communication patterns
    communication_style: CommunicationStyle = CommunicationStyle.MIXED
    directness_style: DirectnessStyle = DirectnessStyle.DIPLOMATIC
    decision_style: DecisionStyle = DecisionStyle.DELIBERATE

    # Behavioral indicators
    avg_message_length: float = 0.0
    complexity_score: float = 0.5
    emotional_expressiveness: float = 0.5
    question_asking_frequency: float = 0.0
    uncertainty_indicators: float = 0.0
    confidence_level: float = 0.5

    # Learning and interaction preferences
    detail_orientation: float = 0.5
    abstract_thinking: float = 0.5
    social_engagement: float = 0.5
    humor_usage: float = 0.0

    # Metadata
    total_messages_analyzed: int = 0
    last_updated: datetime | None = None
    confidence_interval: float = 0.0


class PersonalityProfiler:
    """Advanced personality analysis system"""

    def __init__(self):
        """Initialize the personality profiler"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("PersonalityProfiler initialized with spaCy model")
        except OSError:
            logger.error(
                "spaCy model not found. Please install: python -m spacy download en_core_web_sm"
            )
            raise

        # Personality indicators
        self._formal_indicators = {
            "words": [
                "furthermore",
                "therefore",
                "consequently",
                "nevertheless",
                "moreover",
                "request",
                "assistance",
                "proceed",
                "recommend",
                "professional",
                "formal",
                "consider",
                "propose",
                "beneficial",
                "appropriate",
            ],
            "patterns": [r"\b(I would|I shall|one might|it appears that|I believe we should)\b"],
            "contractions": False,  # Formal speech avoids contractions
        }

        self._casual_indicators = {
            "words": [
                "yeah",
                "nah",
                "gonna",
                "wanna",
                "kinda",
                "sorta",
                "btw",
                "lol",
                "omg",
                "hey",
                "what's up",
                "ngl",
                "awesome",
                "thing",
            ],
            "patterns": [r"\b(you know|like|so|anyway|just go for it)\b"],
            "contractions": True,  # Casual speech uses contractions
        }

        self._confidence_indicators = {
            "high": [
                "definitely",
                "certainly",
                "absolutely",
                "obviously",
                "clearly",
                "know this is",
                "will work",
                "best solution",
                "most effective",
                "perfect",
            ],
            "low": [
                "maybe",
                "perhaps",
                "possibly",
                "might",
                "could be",
                "not sure",
                "i think",
                "i guess",
                "worried",
                "not certain",
            ],
        }

        self._emotion_indicators = {
            "excitement": ["!", "wow", "amazing", "awesome", "fantastic", "incredible"],
            "concern": ["worried", "concerned", "anxious", "nervous", "stressed"],
            "happiness": ["happy", "glad", "joy", "excited", "pleased", "delighted"],
            "analytical": ["analyze", "consider", "evaluate", "examine", "review"],
        }

        self._decision_indicators = {
            "quick": ["immediately", "right away", "now", "asap", "quickly", "just go for it"],
            "deliberate": ["think about", "consider", "evaluate", "analyze", "review", "careful"],
            "impulsive": ["just do it", "why not", "let's go", "sounds good", "go for it"],
            "analytical": [
                "pros and cons",
                "research",
                "data",
                "evidence",
                "study",
                "analyze",
                "evaluate",
                "thoroughly",
                "potential risks",
                "benefits",
            ],
        }

    def analyze_personality(self, messages: list[str], user_id: str) -> PersonalityMetrics:
        """
        Analyze personality from a collection of messages

        Args:
            messages: List of user messages to analyze
            user_id: User identifier for context

        Returns:
            PersonalityMetrics with comprehensive personality analysis
        """
        if not messages:
            logger.warning(f"No messages provided for personality analysis of user {user_id}")
            return PersonalityMetrics()

        logger.info(f"Analyzing personality for user {user_id} with {len(messages)} messages")

        # Initialize analysis containers
        metrics = PersonalityMetrics()
        metrics.total_messages_analyzed = len(messages)
        metrics.last_updated = datetime.now(UTC)

        # Analyze each message
        message_stats = []
        for message in messages:
            stats = self._analyze_single_message(message)
            message_stats.append(stats)

        # Aggregate results
        metrics = self._aggregate_personality_metrics(message_stats, metrics)

        # Calculate confidence based on sample size
        metrics.confidence_interval = min(0.95, len(messages) / 100.0)

        logger.info(f"Personality analysis complete for user {user_id}")
        logger.debug(f"Personality metrics: {asdict(metrics)}")

        return metrics

    def _analyze_single_message(self, message: str) -> dict[str, Any]:
        """Analyze a single message for personality indicators"""
        doc = self.nlp(message.lower())

        stats = {
            "length": len(message),
            "word_count": len([token for token in doc if not token.is_space]),
            "sentence_count": len(list(doc.sents)),
            "complexity_score": 0.0,
            "formality_score": 0.0,
            "confidence_score": 0.0,
            "emotional_intensity": 0.0,
            "question_count": message.count("?"),
            "exclamation_count": message.count("!"),
            "decision_indicators": {"quick": 0, "deliberate": 0, "impulsive": 0, "analytical": 0},
            "big_five_indicators": {
                "openness": 0.0,
                "conscientiousness": 0.0,
                "extraversion": 0.0,
                "agreeableness": 0.0,
                "neuroticism": 0.0,
            },
        }

        # Calculate complexity (sentence length, vocabulary diversity)
        if stats["sentence_count"] > 0:
            avg_sentence_length = stats["word_count"] / stats["sentence_count"]
            stats["complexity_score"] = min(1.0, avg_sentence_length / 20.0)  # Normalize to 0-1

        # Analyze formality
        stats["formality_score"] = self._calculate_formality(message, doc)

        # Analyze confidence indicators
        stats["confidence_score"] = self._calculate_confidence(message)

        # Analyze emotional expression
        stats["emotional_intensity"] = self._calculate_emotional_intensity(message)

        # Analyze decision-making style indicators
        stats["decision_indicators"] = self._analyze_decision_style(message)

        # Analyze Big Five personality indicators
        stats["big_five_indicators"] = self._analyze_big_five_indicators(message, doc)

        return stats

    def _calculate_formality(self, message: str, doc) -> float:
        """Calculate formality score (0=casual, 1=formal)"""
        formal_score = 0
        casual_score = 0

        message_lower = message.lower()

        # Check formal indicators
        for word in self._formal_indicators["words"]:
            if word in message_lower:
                formal_score += 1

        for pattern in self._formal_indicators["patterns"]:
            formal_score += len(re.findall(pattern, message_lower))

        # Check casual indicators
        for word in self._casual_indicators["words"]:
            if word in message_lower:
                casual_score += 1

        for pattern in self._casual_indicators["patterns"]:
            casual_score += len(re.findall(pattern, message_lower))

        # Check contractions (casual indicator)
        contractions = len(re.findall(r"\w+'\w+", message))
        if contractions > 0:
            casual_score += contractions

        # Normalize to 0-1 scale
        total_indicators = formal_score + casual_score
        if total_indicators == 0:
            return 0.5  # Neutral

        return formal_score / total_indicators

    def _calculate_confidence(self, message: str) -> float:
        """Calculate confidence level (0=low confidence, 1=high confidence)"""
        message_lower = message.lower()

        high_confidence = 0
        low_confidence = 0

        for indicator in self._confidence_indicators["high"]:
            if indicator in message_lower:
                high_confidence += 1

        for indicator in self._confidence_indicators["low"]:
            if indicator in message_lower:
                low_confidence += 1

        # Check for uncertainty patterns
        uncertainty_patterns = [r"\bi think\b", r"\bi guess\b", r"\bmaybe\b", r"\bperhaps\b"]
        for pattern in uncertainty_patterns:
            low_confidence += len(re.findall(pattern, message_lower))

        total_indicators = high_confidence + low_confidence
        if total_indicators == 0:
            return 0.5  # Neutral

        return high_confidence / total_indicators

    def _calculate_emotional_intensity(self, message: str) -> float:
        """Calculate emotional expressiveness (0=neutral, 1=highly emotional)"""
        message_lower = message.lower()

        emotional_indicators = 0

        # Count emotional words
        for _emotion_type, words in self._emotion_indicators.items():
            for word in words:
                if word in message_lower:
                    emotional_indicators += 1

        # Count emotional punctuation
        emotional_indicators += message.count("!")
        emotional_indicators += message.count("?") * 0.5  # Questions are somewhat emotional

        # Count caps (excitement/emphasis)
        caps_words = len(re.findall(r"\b[A-Z]{2,}\b", message))
        emotional_indicators += caps_words

        # Normalize based on message length
        word_count = len(message.split())
        if word_count == 0:
            return 0.0

        return min(1.0, emotional_indicators / word_count * 5)  # Scale factor

    def _analyze_decision_style(self, message: str) -> dict[str, int]:
        """Analyze decision-making style indicators"""
        message_lower = message.lower()
        indicators = {"quick": 0, "deliberate": 0, "impulsive": 0, "analytical": 0}

        for style, words in self._decision_indicators.items():
            for word in words:
                if word in message_lower:
                    indicators[style] += 1

        return indicators

    def _analyze_big_five_indicators(self, message: str, doc) -> dict[str, float]:
        """Analyze Big Five personality trait indicators"""
        message_lower = message.lower()
        indicators = {
            "openness": 0.0,
            "conscientiousness": 0.0,
            "extraversion": 0.0,
            "agreeableness": 0.0,
            "neuroticism": 0.0,
        }

        # Openness indicators
        openness_words = [
            "creative",
            "imagination",
            "new",
            "different",
            "unique",
            "innovative",
            "explore",
        ]
        for word in openness_words:
            if word in message_lower:
                indicators["openness"] += 0.1

        # Conscientiousness indicators
        conscientiousness_words = [
            "plan",
            "organize",
            "careful",
            "detail",
            "complete",
            "finish",
            "responsible",
            "analyze",
            "evaluate",
            "consider",
            "review",
            "thorough",
            "research",
        ]
        for word in conscientiousness_words:
            if word in message_lower:
                indicators["conscientiousness"] += 0.15

        # Extraversion indicators
        extraversion_words = ["meet", "people", "social", "party", "group", "together", "share"]
        for word in extraversion_words:
            if word in message_lower:
                indicators["extraversion"] += 0.1

        # Count first-person pronouns (extraversion indicator)
        first_person = len(re.findall(r"\bi\b|\bme\b|\bmy\b|\bmyself\b", message_lower))
        indicators["extraversion"] += min(0.5, first_person * 0.05)

        # Agreeableness indicators
        agreeableness_words = ["help", "support", "agree", "understand", "please", "thank", "sorry"]
        for word in agreeableness_words:
            if word in message_lower:
                indicators["agreeableness"] += 0.1

        # Neuroticism indicators
        neuroticism_words = [
            "worry",
            "stress",
            "anxious",
            "nervous",
            "problem",
            "difficult",
            "hard",
            "worried",
            "not sure",
            "not certain",
            "might",
            "maybe",
        ]
        for word in neuroticism_words:
            if word in message_lower:
                indicators["neuroticism"] += 0.15

        # Normalize to 0-1 scale
        for trait in indicators:
            indicators[trait] = min(1.0, indicators[trait])

        return indicators

    def _aggregate_personality_metrics(
        self, message_stats: list[dict], metrics: PersonalityMetrics
    ) -> PersonalityMetrics:
        """Aggregate individual message statistics into overall personality metrics"""
        if not message_stats:
            return metrics

        # Calculate averages
        metrics.avg_message_length = statistics.mean([s["length"] for s in message_stats])
        metrics.complexity_score = statistics.mean([s["complexity_score"] for s in message_stats])
        metrics.emotional_expressiveness = statistics.mean(
            [s["emotional_intensity"] for s in message_stats]
        )
        metrics.confidence_level = statistics.mean([s["confidence_score"] for s in message_stats])

        # Calculate communication style
        formality_scores = [s["formality_score"] for s in message_stats]
        avg_formality = statistics.mean(formality_scores)

        if avg_formality > 0.6:
            metrics.communication_style = CommunicationStyle.FORMAL
        elif avg_formality < 0.4:
            metrics.communication_style = CommunicationStyle.CASUAL
        else:
            metrics.communication_style = CommunicationStyle.MIXED

        # Calculate directness style based on confidence and question patterns
        if metrics.confidence_level > 0.6:
            metrics.directness_style = DirectnessStyle.DIRECT
        elif metrics.confidence_level < 0.4:
            metrics.directness_style = DirectnessStyle.INDIRECT
        else:
            metrics.directness_style = DirectnessStyle.DIPLOMATIC

        # Aggregate Big Five traits
        all_openness = [s["big_five_indicators"]["openness"] for s in message_stats]
        all_conscientiousness = [
            s["big_five_indicators"]["conscientiousness"] for s in message_stats
        ]
        all_extraversion = [s["big_five_indicators"]["extraversion"] for s in message_stats]
        all_agreeableness = [s["big_five_indicators"]["agreeableness"] for s in message_stats]
        all_neuroticism = [s["big_five_indicators"]["neuroticism"] for s in message_stats]

        metrics.openness = statistics.mean(all_openness) if all_openness else 0.5
        metrics.conscientiousness = (
            statistics.mean(all_conscientiousness) if all_conscientiousness else 0.5
        )
        metrics.extraversion = statistics.mean(all_extraversion) if all_extraversion else 0.5
        metrics.agreeableness = statistics.mean(all_agreeableness) if all_agreeableness else 0.5
        metrics.neuroticism = statistics.mean(all_neuroticism) if all_neuroticism else 0.5

        # Calculate decision style
        decision_totals = {"quick": 0, "deliberate": 0, "impulsive": 0, "analytical": 0}
        for stats in message_stats:
            for style, count in stats["decision_indicators"].items():
                decision_totals[style] += count

        if sum(decision_totals.values()) > 0:
            max_style = max(decision_totals.keys(), key=lambda k: decision_totals[k])
            metrics.decision_style = DecisionStyle(max_style)

        # Calculate behavioral indicators
        total_questions = sum([s["question_count"] for s in message_stats])
        metrics.question_asking_frequency = total_questions / len(message_stats)

        # Calculate derived metrics
        metrics.detail_orientation = (
            metrics.conscientiousness * 0.7 + metrics.complexity_score * 0.3
        )
        metrics.abstract_thinking = metrics.openness * 0.8 + metrics.complexity_score * 0.2
        metrics.social_engagement = (
            metrics.extraversion * 0.6 + metrics.emotional_expressiveness * 0.4
        )
        metrics.uncertainty_indicators = 1.0 - metrics.confidence_level

        return metrics

    def get_personality_summary(self, metrics: PersonalityMetrics) -> dict[str, Any]:
        """Generate a human-readable personality summary"""
        summary = {
            "communication_style": {
                "primary": metrics.communication_style.value,
                "directness": metrics.directness_style.value,
                "confidence_level": self._score_to_label(metrics.confidence_level, "confidence"),
            },
            "personality_traits": {
                "openness": self._score_to_label(metrics.openness, "openness"),
                "conscientiousness": self._score_to_label(
                    metrics.conscientiousness, "conscientiousness"
                ),
                "extraversion": self._score_to_label(metrics.extraversion, "extraversion"),
                "agreeableness": self._score_to_label(metrics.agreeableness, "agreeableness"),
                "neuroticism": self._score_to_label(metrics.neuroticism, "neuroticism"),
            },
            "behavioral_patterns": {
                "decision_style": metrics.decision_style.value,
                "emotional_expressiveness": self._score_to_label(
                    metrics.emotional_expressiveness, "emotion"
                ),
                "detail_orientation": self._score_to_label(metrics.detail_orientation, "detail"),
                "social_engagement": self._score_to_label(metrics.social_engagement, "social"),
            },
            "communication_metrics": {
                "avg_message_length": round(metrics.avg_message_length, 1),
                "complexity_score": round(metrics.complexity_score, 2),
                "question_frequency": round(metrics.question_asking_frequency, 2),
            },
            "analysis_meta": {
                "messages_analyzed": metrics.total_messages_analyzed,
                "confidence": round(metrics.confidence_interval, 2),
                "last_updated": metrics.last_updated.isoformat() if metrics.last_updated else None,
            },
        }

        return summary

    def _score_to_label(self, score: float, trait_type: str) -> str:
        """Convert numerical scores to descriptive labels"""
        labels = {
            "confidence": ["Low", "Moderate", "High", "Very High"],
            "openness": ["Traditional", "Conventional", "Open", "Very Creative"],
            "conscientiousness": ["Flexible", "Moderate", "Organized", "Very Disciplined"],
            "extraversion": ["Introverted", "Reserved", "Social", "Very Outgoing"],
            "agreeableness": ["Competitive", "Neutral", "Cooperative", "Very Agreeable"],
            "neuroticism": ["Calm", "Stable", "Sensitive", "Very Anxious"],
            "emotion": ["Reserved", "Moderate", "Expressive", "Very Emotional"],
            "detail": ["Big Picture", "Balanced", "Detail-Focused", "Very Precise"],
            "social": ["Private", "Selective", "Social", "Very Engaging"],
        }

        if trait_type not in labels:
            return f"{score:.2f}"

        # Map score to label index
        if score < 0.25:
            return labels[trait_type][0]
        elif score < 0.5:
            return labels[trait_type][1]
        elif score < 0.75:
            return labels[trait_type][2]
        else:
            return labels[trait_type][3]
