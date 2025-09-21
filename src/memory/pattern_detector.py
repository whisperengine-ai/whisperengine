"""
Cross-Reference Pattern Detection System
=======================================

Advanced pattern detection system that identifies correlations, triggers,
and behavioral patterns across user memory networks for predictive insights.

Phase 3: Multi-Dimensional Memory Networks
"""

import logging
import os
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from itertools import combinations
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _safe_get_emotional_context(data: dict) -> dict:
    """
    Safely extract emotional context from data, handling both dict and string types

    Args:
        data: Dictionary that may contain emotional_context

    Returns:
        Dictionary with emotional context or default empty dict
    """
    emotional_context = data.get("emotional_context", {})

    if isinstance(emotional_context, str):
        # If it's a string, try to parse it as JSON
        try:
            import json

            emotional_context = json.loads(emotional_context)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, create a default dict
            emotional_context = {
                "primary_emotion": emotional_context if emotional_context else "neutral"
            }
    elif not isinstance(emotional_context, dict):
        # If it's neither string nor dict, create default
        emotional_context = {"primary_emotion": "neutral"}

    return emotional_context


class PatternType(Enum):
    TOPIC_CORRELATION = "topic_correlation"
    EMOTIONAL_TRIGGER = "emotional_trigger"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    PREFERENCE_EVOLUTION = "preference_evolution"
    CONVERSATION_CYCLE = "conversation_cycle"
    TEMPORAL_PATTERN = "temporal_pattern"


class PatternStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class DetectedPattern:
    """Represents a detected pattern in user behavior/memories"""

    pattern_id: str
    pattern_type: PatternType
    pattern_strength: PatternStrength
    confidence_score: float
    description: str
    supporting_evidence: list[str]
    frequency: int
    temporal_span: dict[str, str]
    related_memories: list[str]
    prediction_value: float
    pattern_metadata: dict[str, Any]
    detected_at: datetime


@dataclass
class TopicCorrelation:
    """Represents correlation between topics"""

    topic_a: str
    topic_b: str
    correlation_strength: float
    co_occurrence_count: int
    total_occurrences_a: int
    total_occurrences_b: int
    correlation_contexts: list[str]


@dataclass
class EmotionalTrigger:
    """Represents an emotional trigger pattern"""

    trigger_content: str
    triggered_emotion: str
    trigger_strength: float
    occurrence_count: int
    recovery_time_avg: float
    context_factors: list[str]
    trigger_examples: list[str]


@dataclass
class BehavioralPattern:
    """Represents a behavioral pattern"""

    behavior_type: str
    pattern_description: str
    occurrence_frequency: float
    temporal_pattern: str
    trigger_conditions: list[str]
    behavioral_examples: list[str]


class CrossReferencePatternDetector:
    """Advanced cross-reference pattern detection system"""

    def __init__(self):
        """Initialize pattern detector"""
        self.pattern_types = [
            PatternType.TOPIC_CORRELATION,
            PatternType.EMOTIONAL_TRIGGER,
            PatternType.BEHAVIORAL_PATTERN,
            PatternType.PREFERENCE_EVOLUTION,
            PatternType.CONVERSATION_CYCLE,
            PatternType.TEMPORAL_PATTERN,
        ]

        # Detection thresholds
        self.correlation_threshold = 0.3
        self.trigger_threshold = 0.4
        self.pattern_frequency_threshold = 3
        self.confidence_threshold = 0.6

        # Pattern cache
        self.detected_patterns = {}
        self.pattern_history = {}

        logger.info("Cross-Reference Pattern Detector initialized")

    async def detect_memory_patterns(
        self, user_id: str, memories: list[dict], conversation_history: list[dict]
    ) -> dict[str, list[DetectedPattern]]:
        """
        Detect comprehensive patterns across memory networks

        Args:
            user_id: User identifier
            memories: User's memory collection
            conversation_history: Historical conversation data

        Returns:
            Dictionary of detected patterns by type
        """
        logger.info(f"Detecting memory patterns for user {user_id}")

        try:
            patterns = {
                "topic_correlations": await self._find_topic_correlations(user_id, memories),
                "emotional_triggers": await self._identify_emotional_triggers(
                    user_id, memories, conversation_history
                ),
                "behavioral_patterns": await self._detect_behavioral_patterns(
                    user_id, conversation_history
                ),
                "preference_evolution": await self._track_preference_changes(user_id, memories),
                "conversation_cycles": await self._find_conversation_cycles(
                    user_id, conversation_history
                ),
                "temporal_patterns": await self._detect_temporal_patterns(
                    user_id, memories, conversation_history
                ),
            }

            # Cache patterns
            self.detected_patterns[user_id] = patterns

            # Update pattern history
            self._update_pattern_history(user_id, patterns)

            logger.info(f"Pattern detection completed for user {user_id}")
            return patterns

        except Exception as e:
            logger.error(f"Error detecting patterns for user {user_id}: {e}")
            return self._create_empty_pattern_result()

    async def _find_topic_correlations(
        self, user_id: str, memories: list[dict]
    ) -> list[DetectedPattern]:
        """Find topics that frequently appear together"""
        logger.debug("Finding topic correlations")

        if len(memories) < 2:
            return []

        # Extract topics from memories
        topic_memory_map = defaultdict(list)
        for memory in memories:
            topic = memory.get("topic", "").lower().strip()
            if topic:
                topic_memory_map[topic].append(memory)

        topics = list(topic_memory_map.keys())
        if len(topics) < 2:
            return []

        # Find correlations between topic pairs
        correlations = []
        for topic_a, topic_b in combinations(topics, 2):
            correlation = await self._calculate_topic_correlation(
                topic_a, topic_b, topic_memory_map, memories
            )

            if correlation.correlation_strength >= self.correlation_threshold:
                pattern = self._create_correlation_pattern(user_id, correlation, topic_memory_map)
                correlations.append(pattern)

        logger.debug(f"Found {len(correlations)} topic correlations")
        return correlations

    async def _calculate_topic_correlation(
        self, topic_a: str, topic_b: str, topic_memory_map: dict, all_memories: list[dict]
    ) -> TopicCorrelation:
        """Calculate correlation strength between two topics"""

        memories_a = topic_memory_map[topic_a]
        memories_b = topic_memory_map[topic_b]

        # Find co-occurrences (memories that mention both topics or happen close in time)
        co_occurrences = 0
        correlation_contexts = []

        for mem_a in memories_a:
            content_a = mem_a.get("content", "").lower()
            timestamp_a = mem_a.get("timestamp", datetime.now(UTC))

            for mem_b in memories_b:
                content_b = mem_b.get("content", "").lower()
                timestamp_b = mem_b.get("timestamp", datetime.now(UTC))

                # Check for content overlap or temporal proximity
                if (
                    topic_b in content_a
                    or topic_a in content_b
                    or abs((timestamp_a - timestamp_b).days) <= 1
                ):
                    co_occurrences += 1
                    correlation_contexts.append(f"{topic_a} + {topic_b} context")

        # Calculate correlation strength
        total_a = len(memories_a)
        total_b = len(memories_b)

        # Jaccard-like coefficient
        correlation_strength = (
            co_occurrences / (total_a + total_b - co_occurrences)
            if (total_a + total_b - co_occurrences) > 0
            else 0
        )

        return TopicCorrelation(
            topic_a=topic_a,
            topic_b=topic_b,
            correlation_strength=correlation_strength,
            co_occurrence_count=co_occurrences,
            total_occurrences_a=total_a,
            total_occurrences_b=total_b,
            correlation_contexts=correlation_contexts,
        )

    def _create_correlation_pattern(
        self, user_id: str, correlation: TopicCorrelation, topic_memory_map: dict
    ) -> DetectedPattern:
        """Create pattern object for topic correlation"""

        strength = self._determine_pattern_strength(correlation.correlation_strength)

        # Get related memory IDs
        related_memories = []
        for topic in [correlation.topic_a, correlation.topic_b]:
            for memory in topic_memory_map[topic]:
                memory_id = memory.get("id", memory.get("memory_id"))
                if memory_id:
                    related_memories.append(memory_id)

        # Calculate temporal span
        all_timestamps = []
        for topic in [correlation.topic_a, correlation.topic_b]:
            for memory in topic_memory_map[topic]:
                timestamp = memory.get("timestamp", datetime.now(UTC))
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.now(UTC)
                all_timestamps.append(timestamp)

        temporal_span = {
            "start_date": (
                min(all_timestamps).isoformat() if all_timestamps and all(isinstance(ts, datetime) for ts in all_timestamps) else datetime.now(UTC).isoformat()
            ),
            "end_date": (
                max(all_timestamps).isoformat() if all_timestamps and all(isinstance(ts, datetime) for ts in all_timestamps) else datetime.now(UTC).isoformat()
            ),
        }

        pattern_id = f"correlation_{user_id}_{correlation.topic_a}_{correlation.topic_b}"

        return DetectedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.TOPIC_CORRELATION,
            pattern_strength=strength,
            confidence_score=correlation.correlation_strength,
            description=f"Strong correlation between '{correlation.topic_a}' and '{correlation.topic_b}'",
            supporting_evidence=[
                f"Co-occurred {correlation.co_occurrence_count} times",
                f"Correlation strength: {correlation.correlation_strength:.2f}",
            ],
            frequency=correlation.co_occurrence_count,
            temporal_span=temporal_span,
            related_memories=related_memories,
            prediction_value=correlation.correlation_strength * 0.8,
            pattern_metadata={
                "topic_a": correlation.topic_a,
                "topic_b": correlation.topic_b,
                "correlation_data": asdict(correlation),
            },
            detected_at=datetime.now(UTC),
        )

    async def _identify_emotional_triggers(
        self, user_id: str, memories: list[dict], conversation_history: list[dict]
    ) -> list[DetectedPattern]:
        """Identify patterns that trigger specific emotions"""
        logger.debug("Identifying emotional triggers")

        emotional_patterns = []

        # Group interactions by emotional responses
        emotional_sequences = self._extract_emotional_sequences(conversation_history)

        # Analyze each emotional sequence for triggers
        for sequence in emotional_sequences:
            trigger_pattern = await self._analyze_emotional_sequence(user_id, sequence)
            if trigger_pattern and trigger_pattern.confidence_score >= self.trigger_threshold:
                emotional_patterns.append(trigger_pattern)

        logger.debug(f"Identified {len(emotional_patterns)} emotional trigger patterns")
        return emotional_patterns

    def _extract_emotional_sequences(self, conversation_history: list[dict]) -> list[list[dict]]:
        """Extract sequences of interactions with emotional context"""
        sequences = []
        current_sequence = []

        for interaction in conversation_history:
            emotional_context = _safe_get_emotional_context(interaction)

            if (
                emotional_context
                and emotional_context.get("primary_emotion", "neutral") != "neutral"
            ):
                current_sequence.append(interaction)
            else:
                if len(current_sequence) >= 2:  # Minimum sequence length
                    sequences.append(current_sequence)
                current_sequence = []

        if len(current_sequence) >= 2:
            sequences.append(current_sequence)

        return sequences

    async def _analyze_emotional_sequence(
        self, user_id: str, sequence: list[dict]
    ) -> Optional[DetectedPattern]:
        """Analyze emotional sequence for trigger patterns"""

        if len(sequence) < 2:
            return None

        # Look for recurring triggers in the sequence
        trigger_candidates = []

        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_interaction = sequence[i + 1]

            current_emotion = _safe_get_emotional_context(current).get("primary_emotion", "neutral")
            next_emotion = _safe_get_emotional_context(next_interaction).get(
                "primary_emotion", "neutral"
            )

            # Look for emotional transitions
            if current_emotion != next_emotion and next_emotion != "neutral":
                trigger_content = current.get("content", "").lower()

                # Extract potential trigger keywords
                trigger_keywords = self._extract_trigger_keywords(trigger_content)

                if trigger_keywords:
                    trigger_candidates.append(
                        {
                            "trigger_content": trigger_keywords,
                            "triggered_emotion": next_emotion,
                            "context": current.get("topic", ""),
                            "timestamp": current.get("timestamp", datetime.now(UTC)),
                        }
                    )

        # Find most frequent trigger pattern
        if trigger_candidates:
            return self._create_trigger_pattern(user_id, trigger_candidates, sequence)

        return None

    def _extract_trigger_keywords(self, content: str) -> list[str]:
        """Extract potential emotional trigger keywords from content"""
        # Emotional trigger indicators
        trigger_words = [
            "stress",
            "pressure",
            "deadline",
            "problem",
            "issue",
            "worry",
            "concern",
            "failure",
            "mistake",
            "error",
            "difficult",
            "hard",
            "struggle",
            "challenge",
            "overwhelming",
            "frustrated",
            "annoyed",
            "angry",
            "upset",
            "sad",
            "disappointed",
            "anxious",
            "nervous",
            "scared",
            "afraid",
            "worried",
            "panic",
            "overwhelm",
        ]

        found_triggers = []
        content_words = content.lower().split()

        for word in trigger_words:
            if word in content_words:
                found_triggers.append(word)

        return found_triggers

    def _create_trigger_pattern(
        self, user_id: str, trigger_candidates: list[dict], sequence: list[dict]
    ) -> DetectedPattern:
        """Create emotional trigger pattern"""

        # Find most common trigger
        trigger_counter = Counter()
        emotion_counter = Counter()

        for candidate in trigger_candidates:
            for trigger in candidate["trigger_content"]:
                trigger_counter[trigger] += 1
            emotion_counter[candidate["triggered_emotion"]] += 1

        most_common_trigger = (
            trigger_counter.most_common(1)[0] if trigger_counter else ("unknown", 0)
        )
        most_common_emotion = (
            emotion_counter.most_common(1)[0] if emotion_counter else ("unknown", 0)
        )

        # Calculate pattern strength
        trigger_frequency = most_common_trigger[1]
        confidence = trigger_frequency / len(trigger_candidates) if trigger_candidates else 0

        strength = self._determine_pattern_strength(confidence)

        # Extract related memory IDs
        related_memories = []
        for interaction in sequence:
            memory_id = interaction.get("id", interaction.get("memory_id"))
            if memory_id:
                related_memories.append(memory_id)

        # Calculate temporal span
        timestamps = [interaction.get("timestamp", datetime.now(UTC)) for interaction in sequence]

        temporal_span = {
            "start_date": (
                min(timestamps).isoformat() if timestamps else datetime.now(UTC).isoformat()
            ),
            "end_date": (
                max(timestamps).isoformat() if timestamps else datetime.now(UTC).isoformat()
            ),
        }

        pattern_id = f"trigger_{user_id}_{most_common_trigger[0]}_{most_common_emotion[0]}"

        return DetectedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.EMOTIONAL_TRIGGER,
            pattern_strength=strength,
            confidence_score=confidence,
            description=f"'{most_common_trigger[0]}' triggers {most_common_emotion[0]} emotions",
            supporting_evidence=[
                f"Trigger occurred {trigger_frequency} times",
                f"Triggered emotion: {most_common_emotion[0]} ({most_common_emotion[1]} occurrences)",
            ],
            frequency=trigger_frequency,
            temporal_span=temporal_span,
            related_memories=related_memories,
            prediction_value=confidence * 0.9,
            pattern_metadata={
                "trigger_word": most_common_trigger[0],
                "triggered_emotion": most_common_emotion[0],
                "trigger_candidates": trigger_candidates,
            },
            detected_at=datetime.now(UTC),
        )

    async def _detect_behavioral_patterns(
        self, user_id: str, conversation_history: list[dict]
    ) -> list[DetectedPattern]:
        """Detect recurring behavioral patterns"""
        logger.debug("Detecting behavioral patterns")

        behavioral_patterns = []

        # Analyze conversation patterns
        timing_patterns = self._analyze_conversation_timing(conversation_history)
        length_patterns = self._analyze_message_lengths(conversation_history)
        topic_patterns = self._analyze_topic_preferences(conversation_history)

        # Create patterns for significant behavioral traits
        if timing_patterns:
            behavioral_patterns.extend(self._create_timing_patterns(user_id, timing_patterns))

        if length_patterns:
            behavioral_patterns.extend(self._create_length_patterns(user_id, length_patterns))

        if topic_patterns:
            behavioral_patterns.extend(
                self._create_topic_preference_patterns(user_id, topic_patterns)
            )

        logger.debug(f"Detected {len(behavioral_patterns)} behavioral patterns")
        return behavioral_patterns

    def _analyze_conversation_timing(self, conversation_history: list[dict]) -> dict[str, Any]:
        """Analyze timing patterns in conversations"""
        if len(conversation_history) < 3:
            return {}

        # Extract timestamps
        timestamps = []
        for interaction in conversation_history:
            timestamp = interaction.get("timestamp", datetime.now(UTC))
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamps.append(timestamp)

        timestamps.sort()

        # Analyze time-of-day patterns
        hours = [ts.hour for ts in timestamps]
        hour_counter = Counter(hours)

        # Analyze day-of-week patterns
        weekdays = [ts.weekday() for ts in timestamps]
        weekday_counter = Counter(weekdays)

        # Analyze conversation gaps
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600  # hours
            gaps.append(gap)

        return {
            "preferred_hours": hour_counter.most_common(3),
            "preferred_weekdays": weekday_counter.most_common(3),
            "average_gap_hours": statistics.mean(gaps) if gaps else 0,
            "median_gap_hours": statistics.median(gaps) if gaps else 0,
            "total_conversations": len(conversation_history),
        }

    def _analyze_message_lengths(self, conversation_history: list[dict]) -> dict[str, Any]:
        """Analyze message length patterns"""
        lengths = []

        for interaction in conversation_history:
            content = interaction.get("content", "")
            lengths.append(len(content))

        if not lengths:
            return {}

        return {
            "average_length": statistics.mean(lengths),
            "median_length": statistics.median(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "length_variance": statistics.variance(lengths) if len(lengths) > 1 else 0,
        }

    def _analyze_topic_preferences(self, conversation_history: list[dict]) -> dict[str, Any]:
        """Analyze topic preference patterns"""
        topics = []

        for interaction in conversation_history:
            topic = interaction.get("topic", "").lower().strip()
            if topic:
                topics.append(topic)

        if not topics:
            return {}

        topic_counter = Counter(topics)

        return {
            "most_discussed_topics": topic_counter.most_common(5),
            "topic_diversity": len(set(topics)),
            "total_topic_mentions": len(topics),
        }

    def _create_timing_patterns(self, user_id: str, timing_data: dict) -> list[DetectedPattern]:
        """Create behavioral patterns from timing analysis"""
        patterns = []

        if timing_data.get("preferred_hours"):
            preferred_hour = timing_data["preferred_hours"][0]
            hour = preferred_hour[0]
            frequency = preferred_hour[1]

            if frequency >= self.pattern_frequency_threshold:
                confidence = frequency / timing_data.get("total_conversations", 1)

                pattern = DetectedPattern(
                    pattern_id=f"timing_{user_id}_hour_{hour}",
                    pattern_type=PatternType.BEHAVIORAL_PATTERN,
                    pattern_strength=self._determine_pattern_strength(confidence),
                    confidence_score=confidence,
                    description=f"Prefers conversations around {hour}:00",
                    supporting_evidence=[f"Initiated {frequency} conversations at hour {hour}"],
                    frequency=frequency,
                    temporal_span={"start_date": "", "end_date": ""},  # Would need actual span
                    related_memories=[],
                    prediction_value=confidence * 0.6,
                    pattern_metadata={
                        "behavioral_type": "timing_preference",
                        "preferred_hour": hour,
                        "timing_data": timing_data,
                    },
                    detected_at=datetime.now(UTC),
                )
                patterns.append(pattern)

        return patterns

    def _create_length_patterns(self, user_id: str, length_data: dict) -> list[DetectedPattern]:
        """Create behavioral patterns from message length analysis"""
        patterns = []

        avg_length = length_data.get("average_length", 0)

        # Classify communication style based on average message length
        if avg_length > 200:
            style = "detailed_communicator"
            description = "Tends to write detailed, comprehensive messages"
        elif avg_length < 50:
            style = "brief_communicator"
            description = "Prefers brief, concise communication"
        else:
            style = "moderate_communicator"
            description = "Uses moderate-length messages"

        confidence = min(
            abs(avg_length - 100) / 100, 1.0
        )  # Confidence based on deviation from average

        if confidence >= self.confidence_threshold:
            pattern = DetectedPattern(
                pattern_id=f"communication_{user_id}_{style}",
                pattern_type=PatternType.BEHAVIORAL_PATTERN,
                pattern_strength=self._determine_pattern_strength(confidence),
                confidence_score=confidence,
                description=description,
                supporting_evidence=[f"Average message length: {avg_length:.1f} characters"],
                frequency=1,  # Style pattern
                temporal_span={"start_date": "", "end_date": ""},
                related_memories=[],
                prediction_value=confidence * 0.5,
                pattern_metadata={
                    "behavioral_type": "communication_style",
                    "style": style,
                    "length_data": length_data,
                },
                detected_at=datetime.now(UTC),
            )
            patterns.append(pattern)

        return patterns

    def _create_topic_preference_patterns(
        self, user_id: str, topic_data: dict
    ) -> list[DetectedPattern]:
        """Create behavioral patterns from topic preference analysis"""
        patterns = []

        most_discussed = topic_data.get("most_discussed_topics", [])

        for topic, frequency in most_discussed:
            if frequency >= self.pattern_frequency_threshold:
                total_mentions = topic_data.get("total_topic_mentions", 1)
                confidence = frequency / total_mentions

                pattern = DetectedPattern(
                    pattern_id=f"topic_preference_{user_id}_{topic}",
                    pattern_type=PatternType.PREFERENCE_EVOLUTION,
                    pattern_strength=self._determine_pattern_strength(confidence),
                    confidence_score=confidence,
                    description=f"Shows strong preference for discussing '{topic}'",
                    supporting_evidence=[
                        f"Discussed {frequency} times out of {total_mentions} total mentions"
                    ],
                    frequency=frequency,
                    temporal_span={"start_date": "", "end_date": ""},
                    related_memories=[],
                    prediction_value=confidence * 0.7,
                    pattern_metadata={
                        "behavioral_type": "topic_preference",
                        "preferred_topic": topic,
                        "topic_data": topic_data,
                    },
                    detected_at=datetime.now(UTC),
                )
                patterns.append(pattern)

        return patterns

    async def _track_preference_changes(
        self, user_id: str, memories: list[dict]
    ) -> list[DetectedPattern]:
        """Track how user preferences evolve over time"""
        logger.debug("Tracking preference evolution")

        if len(memories) < 5:  # Need sufficient data
            return []

        # Sort memories by timestamp
        sorted_memories = sorted(memories, key=lambda m: m.get("timestamp", datetime.now(UTC)))

        # Split into time periods
        early_memories = sorted_memories[: len(sorted_memories) // 2]
        recent_memories = sorted_memories[len(sorted_memories) // 2 :]

        # Analyze topic preferences in each period
        early_topics = Counter(
            [m.get("topic", "").lower() for m in early_memories if m.get("topic")]
        )
        recent_topics = Counter(
            [m.get("topic", "").lower() for m in recent_memories if m.get("topic")]
        )

        # Find significant changes
        evolution_patterns = []

        for topic in set(list(early_topics.keys()) + list(recent_topics.keys())):
            early_freq = early_topics.get(topic, 0)
            recent_freq = recent_topics.get(topic, 0)

            # Calculate change ratio
            if early_freq > 0 and recent_freq > 0:
                change_ratio = recent_freq / early_freq

                if change_ratio >= 2.0:  # Significant increase
                    pattern = self._create_preference_evolution_pattern(
                        user_id, topic, "increasing_interest", change_ratio, early_freq, recent_freq
                    )
                    evolution_patterns.append(pattern)
                elif change_ratio <= 0.5:  # Significant decrease
                    pattern = self._create_preference_evolution_pattern(
                        user_id, topic, "decreasing_interest", change_ratio, early_freq, recent_freq
                    )
                    evolution_patterns.append(pattern)

        logger.debug(f"Tracked {len(evolution_patterns)} preference evolution patterns")
        return evolution_patterns

    def _create_preference_evolution_pattern(
        self,
        user_id: str,
        topic: str,
        evolution_type: str,
        change_ratio: float,
        early_freq: int,
        recent_freq: int,
    ) -> DetectedPattern:
        """Create preference evolution pattern"""

        confidence = min(abs(change_ratio - 1.0), 1.0)  # Confidence based on magnitude of change
        strength = self._determine_pattern_strength(confidence)

        if evolution_type == "increasing_interest":
            description = f"Growing interest in '{topic}' (increased {change_ratio:.1f}x)"
        else:
            description = f"Declining interest in '{topic}' (decreased to {change_ratio:.1f}x)"

        pattern = DetectedPattern(
            pattern_id=f"evolution_{user_id}_{topic}_{evolution_type}",
            pattern_type=PatternType.PREFERENCE_EVOLUTION,
            pattern_strength=strength,
            confidence_score=confidence,
            description=description,
            supporting_evidence=[
                f"Early period: {early_freq} mentions",
                f"Recent period: {recent_freq} mentions",
                f"Change ratio: {change_ratio:.2f}",
            ],
            frequency=recent_freq,
            temporal_span={"start_date": "", "end_date": ""},
            related_memories=[],
            prediction_value=confidence * 0.8,
            pattern_metadata={
                "topic": topic,
                "evolution_type": evolution_type,
                "change_ratio": change_ratio,
                "early_frequency": early_freq,
                "recent_frequency": recent_freq,
            },
            detected_at=datetime.now(UTC),
        )

        return pattern

    async def _find_conversation_cycles(
        self, user_id: str, conversation_history: list[dict]
    ) -> list[DetectedPattern]:
        """Find cyclical patterns in conversations"""
        logger.debug("Finding conversation cycles")

        # This is a simplified implementation
        # A more sophisticated version would use time series analysis

        if len(conversation_history) < 10:
            return []

        # Analyze topic cycles
        topics = [
            interaction.get("topic", "").lower()
            for interaction in conversation_history
            if interaction.get("topic")
        ]

        # Look for repeating sequences
        cycle_patterns = []

        # Simple cycle detection - look for topics that repeat at regular intervals
        topic_positions = defaultdict(list)
        for i, topic in enumerate(topics):
            topic_positions[topic].append(i)

        for topic, positions in topic_positions.items():
            if len(positions) >= 3:  # Need at least 3 occurrences
                # Calculate intervals between occurrences
                intervals = [positions[i] - positions[i - 1] for i in range(1, len(positions))]

                # Check for consistent intervals (cycle)
                if len(set(intervals)) <= 2:  # Allow some variation
                    avg_interval = statistics.mean(intervals)
                    confidence = (
                        1.0 / (statistics.stdev(intervals) + 1) if len(intervals) > 1 else 1.0
                    )

                    if confidence >= self.confidence_threshold:
                        pattern = DetectedPattern(
                            pattern_id=f"cycle_{user_id}_{topic}",
                            pattern_type=PatternType.CONVERSATION_CYCLE,
                            pattern_strength=self._determine_pattern_strength(confidence),
                            confidence_score=confidence,
                            description=f"Cyclical discussion of '{topic}' every {avg_interval:.1f} conversations",
                            supporting_evidence=[
                                f"Repeats every {avg_interval:.1f} conversations on average"
                            ],
                            frequency=len(positions),
                            temporal_span={"start_date": "", "end_date": ""},
                            related_memories=[],
                            prediction_value=confidence * 0.6,
                            pattern_metadata={
                                "topic": topic,
                                "cycle_interval": avg_interval,
                                "positions": positions,
                            },
                            detected_at=datetime.now(UTC),
                        )
                        cycle_patterns.append(pattern)

        logger.debug(f"Found {len(cycle_patterns)} conversation cycle patterns")
        return cycle_patterns

    async def _detect_temporal_patterns(
        self, user_id: str, memories: list[dict], conversation_history: list[dict]
    ) -> list[DetectedPattern]:
        """Detect temporal patterns in behavior and emotions"""
        logger.debug("Detecting temporal patterns")

        temporal_patterns = []

        # Analyze day-of-week patterns
        daily_patterns = self._analyze_daily_patterns(conversation_history)
        if daily_patterns:
            temporal_patterns.extend(self._create_daily_patterns(user_id, daily_patterns))

        # Analyze seasonal patterns (if enough data spanning multiple months)
        seasonal_patterns = self._analyze_seasonal_patterns(memories)
        if seasonal_patterns:
            temporal_patterns.extend(self._create_seasonal_patterns(user_id, seasonal_patterns))

        logger.debug(f"Detected {len(temporal_patterns)} temporal patterns")
        return temporal_patterns

    def _analyze_daily_patterns(self, conversation_history: list[dict]) -> dict[str, Any]:
        """Analyze patterns by day of week"""
        weekday_data = defaultdict(list)

        for interaction in conversation_history:
            timestamp = interaction.get("timestamp", datetime.now(UTC))
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

            weekday = timestamp.weekday()  # 0 = Monday, 6 = Sunday
            weekday_data[weekday].append(interaction)

        # Analyze each weekday
        patterns = {}
        for weekday, interactions in weekday_data.items():
            if len(interactions) >= 3:  # Minimum for pattern
                # Analyze emotional context for this weekday
                emotions = [
                    _safe_get_emotional_context(interaction).get("primary_emotion", "neutral")
                    for interaction in interactions
                ]
                emotion_counter = Counter(emotions)

                patterns[weekday] = {
                    "interaction_count": len(interactions),
                    "dominant_emotion": (
                        emotion_counter.most_common(1)[0] if emotion_counter else ("neutral", 0)
                    ),
                    "emotion_distribution": dict(emotion_counter),
                }

        return patterns

    def _create_daily_patterns(self, user_id: str, daily_data: dict) -> list[DetectedPattern]:
        """Create daily temporal patterns"""
        patterns = []

        weekday_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for weekday, data in daily_data.items():
            dominant_emotion = data["dominant_emotion"][0]
            emotion_frequency = data["dominant_emotion"][1]
            total_interactions = data["interaction_count"]

            if emotion_frequency >= 2 and dominant_emotion != "neutral":
                confidence = emotion_frequency / total_interactions

                pattern = DetectedPattern(
                    pattern_id=f"daily_{user_id}_{weekday}_{dominant_emotion}",
                    pattern_type=PatternType.TEMPORAL_PATTERN,
                    pattern_strength=self._determine_pattern_strength(confidence),
                    confidence_score=confidence,
                    description=f"Tends to be {dominant_emotion} on {weekday_names[weekday]}s",
                    supporting_evidence=[
                        f"{emotion_frequency} out of {total_interactions} {weekday_names[weekday]} interactions"
                    ],
                    frequency=emotion_frequency,
                    temporal_span={"start_date": "", "end_date": ""},
                    related_memories=[],
                    prediction_value=confidence * 0.7,
                    pattern_metadata={
                        "weekday": weekday,
                        "weekday_name": weekday_names[weekday],
                        "dominant_emotion": dominant_emotion,
                        "daily_data": data,
                    },
                    detected_at=datetime.now(UTC),
                )
                patterns.append(pattern)

        return patterns

    def _analyze_seasonal_patterns(self, memories: list[dict]) -> dict[str, Any]:
        """Analyze seasonal patterns in memories"""
        # This is a placeholder for seasonal analysis
        # Would require longer-term data to be meaningful
        return {}

    def _create_seasonal_patterns(self, user_id: str, seasonal_data: dict) -> list[DetectedPattern]:
        """Create seasonal temporal patterns"""
        # Placeholder for seasonal pattern creation
        return []

    def _determine_pattern_strength(self, confidence: float) -> PatternStrength:
        """Determine pattern strength based on confidence score"""
        if confidence >= 0.8:
            return PatternStrength.VERY_STRONG
        elif confidence >= 0.6:
            return PatternStrength.STRONG
        elif confidence >= 0.4:
            return PatternStrength.MODERATE
        else:
            return PatternStrength.WEAK

    async def predict_pattern_continuation(
        self, user_id: str, current_context: dict, memory_manager=None
    ) -> dict[str, Any]:
        """
        Predict likely pattern continuation based on current context

        Args:
            user_id: User identifier
            current_context: Current conversation/emotional context
            memory_manager: Memory manager for additional data

        Returns:
            Predictions about likely pattern continuations
        """
        logger.debug(f"Predicting pattern continuation for user {user_id}")

        try:
            user_patterns = self.detected_patterns.get(user_id, {})

            predictions = {
                "topic_predictions": self._predict_topic_patterns(current_context, user_patterns),
                "emotional_predictions": self._predict_emotional_patterns(
                    current_context, user_patterns
                ),
                "behavioral_predictions": self._predict_behavioral_patterns(
                    current_context, user_patterns
                ),
                "temporal_predictions": self._predict_temporal_patterns(
                    current_context, user_patterns
                ),
                "confidence_scores": {},
                "prediction_timestamp": datetime.now(UTC),
            }

            # Calculate overall prediction confidence
            all_predictions = []
            for _prediction_type, prediction_list in predictions.items():
                if isinstance(prediction_list, list):
                    all_predictions.extend(prediction_list)

            if all_predictions:
                avg_confidence = statistics.mean([p.get("confidence", 0) for p in all_predictions])
                predictions["overall_confidence"] = avg_confidence
            else:
                predictions["overall_confidence"] = 0.0

            return predictions

        except Exception as e:
            logger.error(f"Error predicting pattern continuation: {e}")
            return {"error": str(e)}

    def _predict_topic_patterns(self, current_context: dict, user_patterns: dict) -> list[dict]:
        """Predict topic-based pattern continuations"""
        current_topic = current_context.get("topic", "").lower()

        if not current_topic:
            return []

        topic_correlations = user_patterns.get("topic_correlations", [])
        predictions = []

        for pattern in topic_correlations:
            metadata = pattern.pattern_metadata
            if metadata.get("topic_a") == current_topic or metadata.get("topic_b") == current_topic:

                # Predict the correlated topic
                predicted_topic = (
                    metadata.get("topic_b")
                    if metadata.get("topic_a") == current_topic
                    else metadata.get("topic_a")
                )

                predictions.append(
                    {
                        "type": "topic_correlation",
                        "predicted_topic": predicted_topic,
                        "confidence": pattern.confidence_score,
                        "reasoning": f"Topic '{current_topic}' often correlates with '{predicted_topic}'",
                    }
                )

        return predictions

    def _predict_emotional_patterns(self, current_context: dict, user_patterns: dict) -> list[dict]:
        """Predict emotional pattern continuations"""
        current_content = current_context.get("content", "").lower()

        emotional_triggers = user_patterns.get("emotional_triggers", [])
        predictions = []

        for pattern in emotional_triggers:
            metadata = pattern.pattern_metadata
            trigger_word = metadata.get("trigger_word", "")

            if trigger_word in current_content:
                predictions.append(
                    {
                        "type": "emotional_trigger",
                        "predicted_emotion": metadata.get("triggered_emotion"),
                        "confidence": pattern.confidence_score,
                        "reasoning": f"Trigger word '{trigger_word}' detected in content",
                    }
                )

        return predictions

    def _predict_behavioral_patterns(
        self, current_context: dict, user_patterns: dict
    ) -> list[dict]:
        """Predict behavioral pattern continuations"""
        # This would analyze current behavioral context and predict likely continuations
        return []

    def _predict_temporal_patterns(self, current_context: dict, user_patterns: dict) -> list[dict]:
        """Predict temporal pattern continuations"""
        current_time = datetime.now(UTC)
        current_weekday = current_time.weekday()

        temporal_patterns = user_patterns.get("temporal_patterns", [])
        predictions = []

        for pattern in temporal_patterns:
            metadata = pattern.pattern_metadata
            if metadata.get("weekday") == current_weekday:
                predictions.append(
                    {
                        "type": "temporal_pattern",
                        "predicted_emotion": metadata.get("dominant_emotion"),
                        "confidence": pattern.confidence_score,
                        "reasoning": "Historical pattern for this day of week",
                    }
                )

        return predictions

    def _create_empty_pattern_result(self) -> dict[str, list]:
        """Create empty pattern result structure"""
        return {
            "topic_correlations": [],
            "emotional_triggers": [],
            "behavioral_patterns": [],
            "preference_evolution": [],
            "conversation_cycles": [],
            "temporal_patterns": [],
        }

    def _update_pattern_history(self, user_id: str, patterns: dict[str, list[DetectedPattern]]):
        """Update pattern history for tracking changes over time"""
        if user_id not in self.pattern_history:
            self.pattern_history[user_id] = []

        self.pattern_history[user_id].append(
            {
                "timestamp": datetime.now(UTC),
                "patterns": patterns,
                "pattern_count": sum(len(pattern_list) for pattern_list in patterns.values()),
            }
        )

        # Keep only last 10 pattern snapshots
        if len(self.pattern_history[user_id]) > 10:
            self.pattern_history[user_id] = self.pattern_history[user_id][-10:]

    def get_pattern_statistics(self, user_id: str) -> dict[str, Any]:
        """Get pattern detection statistics for user"""
        user_patterns = self.detected_patterns.get(user_id, {})

        stats = {
            "total_patterns": sum(len(pattern_list) for pattern_list in user_patterns.values()),
            "patterns_by_type": {
                pattern_type: len(pattern_list)
                for pattern_type, pattern_list in user_patterns.items()
            },
            "pattern_strengths": self._analyze_pattern_strengths(user_patterns),
            "detection_timestamp": datetime.now(UTC),
        }

        return stats

    def _analyze_pattern_strengths(self, user_patterns: dict) -> dict[str, int]:
        """Analyze distribution of pattern strengths"""
        strength_counts = Counter()

        for pattern_list in user_patterns.values():
            for pattern in pattern_list:
                strength_counts[pattern.pattern_strength.value] += 1

        return dict(strength_counts)
