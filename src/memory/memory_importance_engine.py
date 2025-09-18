"""
Memory Importance Engine
=======================

Advanced system for calculating and managing memory importance scores
based on multiple factors including emotional impact, personal relevance,
recency, access frequency, and uniqueness.

Phase 3: Multi-Dimensional Memory Networks
"""

import json
import logging
import os
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

# Database imports for persistence
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImportanceFactor(Enum):
    EMOTIONAL_INTENSITY = "emotional_intensity"
    PERSONAL_RELEVANCE = "personal_relevance"
    RECENCY = "recency"
    ACCESS_FREQUENCY = "access_frequency"
    UNIQUENESS = "uniqueness"
    RELATIONSHIP_MILESTONE = "relationship_milestone"


@dataclass
class ImportanceFactors:
    """Individual importance factor scores"""

    emotional_intensity: float
    personal_relevance: float
    recency: float
    access_frequency: float
    uniqueness: float
    relationship_milestone: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class MemoryImportanceScore:
    """Complete importance assessment for a memory"""

    memory_id: str
    user_id: str
    overall_score: float
    factor_scores: ImportanceFactors
    calculation_timestamp: datetime
    score_explanation: str
    decay_rate: float
    boost_events: list[str]


class MemoryImportanceEngine:
    """Advanced memory importance calculation system"""

    def __init__(self):
        """Initialize memory importance engine"""
        # Importance factor weights (should sum to 1.0)
        self.importance_weights = {
            ImportanceFactor.EMOTIONAL_INTENSITY: 0.30,
            ImportanceFactor.PERSONAL_RELEVANCE: 0.25,
            ImportanceFactor.RECENCY: 0.15,
            ImportanceFactor.ACCESS_FREQUENCY: 0.15,
            ImportanceFactor.UNIQUENESS: 0.10,
            ImportanceFactor.RELATIONSHIP_MILESTONE: 0.05,
        }

        # Decay parameters
        self.base_decay_rate = 0.01  # Base decay per day
        self.access_boost_multiplier = 1.5
        self.emotional_preservation_threshold = 0.8

        # Core memory thresholds
        self.core_memory_threshold = 0.85
        self.max_core_memories = 20

        # Caching
        self.importance_cache = {}
        self.user_statistics = {}
        
        # Database persistence
        self._persistence_initialized = False

        logger.info("Memory Importance Engine initialized")

    async def ensure_persistence_initialized(self):
        """Ensure database persistence is initialized (lazy initialization)"""
        if not self._persistence_initialized:
            await self.initialize_persistence()
            self._persistence_initialized = True

    async def calculate_memory_importance_with_patterns(
        self,
        memory_id: str,
        user_id: str,
        memory_data: dict,
        user_history: list[dict],
        memory_manager=None,
    ) -> MemoryImportanceScore:
        """
        Calculate memory importance using learned user patterns
        
        This enhanced version uses persisted user patterns to personalize
        importance calculations based on what the user has shown to value.
        """
        # Ensure persistence is initialized
        await self.ensure_persistence_initialized()
        
        # Load user-specific patterns if available
        user_patterns = await self.load_user_importance_patterns(user_id)
        learned_weights = await self._get_user_learned_weights(user_id)
        
        # Use learned weights if available, otherwise use defaults
        if learned_weights:
            original_weights = self.importance_weights.copy()
            self.importance_weights = learned_weights
        
        try:
            # Calculate base importance using existing method
            base_score = await self.calculate_memory_importance(
                memory_id, user_id, memory_data, user_history, memory_manager
            )
            
            # Apply user-specific pattern boosts
            pattern_boost = await self._apply_pattern_boosts(memory_data, user_patterns)
            
            # Adjust overall score with pattern learning
            enhanced_factor_scores = ImportanceFactors(
                emotional_intensity=base_score.factor_scores.emotional_intensity * pattern_boost.get("emotional_multiplier", 1.0),
                personal_relevance=base_score.factor_scores.personal_relevance * pattern_boost.get("personal_multiplier", 1.0),
                recency=base_score.factor_scores.recency,
                access_frequency=base_score.factor_scores.access_frequency,
                uniqueness=base_score.factor_scores.uniqueness,
                relationship_milestone=base_score.factor_scores.relationship_milestone,
            )
            
            # Recalculate overall score with enhanced factors
            enhanced_overall_score = sum(
                getattr(enhanced_factor_scores, factor.value) * weight
                for factor, weight in self.importance_weights.items()
            )
            
            # Update pattern learning based on this calculation
            await self._update_pattern_learning(user_id, memory_data, enhanced_overall_score)
            
            return MemoryImportanceScore(
                memory_id=memory_id,
                user_id=user_id,
                overall_score=min(1.0, enhanced_overall_score),
                factor_scores=enhanced_factor_scores,
                calculation_timestamp=datetime.now(UTC),
                score_explanation=f"Enhanced with learned patterns (boost: {pattern_boost})",
                decay_rate=base_score.decay_rate,
                boost_events=base_score.boost_events + ["pattern_learning_applied"],
            )
            
        finally:
            # Restore original weights
            if learned_weights:
                self.importance_weights = original_weights

    async def _get_user_learned_weights(self, user_id: str) -> dict | None:
        """Get user-specific learned importance weights"""
        user_stats = await self.load_user_memory_statistics(user_id)
        if not user_stats:
            return None
            
        return {
            ImportanceFactor.EMOTIONAL_INTENSITY: user_stats.get("emotional_intensity_weight", 0.30),
            ImportanceFactor.PERSONAL_RELEVANCE: user_stats.get("personal_relevance_weight", 0.25),
            ImportanceFactor.RECENCY: user_stats.get("recency_weight", 0.15),
            ImportanceFactor.ACCESS_FREQUENCY: user_stats.get("access_frequency_weight", 0.15),
            ImportanceFactor.UNIQUENESS: user_stats.get("uniqueness_weight", 0.10),
            ImportanceFactor.RELATIONSHIP_MILESTONE: user_stats.get("relationship_milestone_weight", 0.05),
        }

    async def _apply_pattern_boosts(self, memory_data: dict, user_patterns: list[dict]) -> dict:
        """Apply learned pattern boosts to memory importance"""
        boosts = {
            "emotional_multiplier": 1.0,
            "personal_multiplier": 1.0,
            "total_boost": 0.0,
        }
        
        if not user_patterns:
            return boosts
            
        memory_content = str(memory_data.get("content", "")).lower()
        
        for pattern in user_patterns:
            if pattern["confidence_score"] < 0.3:  # Skip low-confidence patterns
                continue
                
            # Check if pattern keywords match memory content
            pattern_keywords = pattern.get("pattern_keywords", [])
            keyword_matches = sum(1 for keyword in pattern_keywords if keyword in memory_content)
            
            if keyword_matches > 0:
                # Calculate boost based on pattern strength and matches
                match_ratio = keyword_matches / max(len(pattern_keywords), 1)
                boost_strength = pattern["importance_multiplier"] * pattern["confidence_score"] * match_ratio
                
                # Apply boosts based on pattern type
                if pattern["pattern_type"] == "emotional_trigger":
                    boosts["emotional_multiplier"] *= (1.0 + boost_strength * 0.5)
                elif pattern["pattern_type"] == "personal_anchor":
                    boosts["personal_multiplier"] *= (1.0 + boost_strength * 0.6)
                elif pattern["pattern_type"] == "topic_interest":
                    boosts["personal_multiplier"] *= (1.0 + boost_strength * 0.4)
                    
                boosts["total_boost"] += boost_strength
        
        return boosts

    async def _update_pattern_learning(self, user_id: str, memory_data: dict, importance_score: float):
        """Update pattern learning based on calculated importance"""
        # Extract patterns from this memory for learning
        content = str(memory_data.get("content", "")).lower()
        metadata = memory_data.get("metadata", {})
        
        # Learn emotional patterns
        emotional_context = metadata.get("emotional_context")
        if emotional_context and importance_score > 0.7:  # High importance memory
            await self._learn_emotional_pattern(user_id, content, emotional_context, importance_score)
        
        # Learn topic patterns  
        topics = self._extract_topics_from_content(content)
        for topic in topics:
            if importance_score > 0.6:  # Above average importance
                await self._learn_topic_pattern(user_id, topic, importance_score)

    async def _learn_emotional_pattern(self, user_id: str, content: str, emotional_context: dict, importance_score: float):
        """Learn emotional trigger patterns"""
        emotion = emotional_context.get("primary_emotion", "unknown")
        intensity = emotional_context.get("emotion_intensity", 0.5)
        
        if intensity > 0.6:  # Strong emotional content
            pattern_data = {
                "pattern_name": f"emotional_trigger_{emotion}",
                "importance_multiplier": min(2.0, 1.0 + intensity),
                "confidence_score": min(1.0, importance_score),
                "frequency_count": 1,
                "pattern_keywords": self._extract_emotional_keywords(content),
                "emotional_associations": [emotion],
                "context_requirements": {"min_intensity": intensity * 0.8},
            }
            await self.save_importance_pattern(user_id, "emotional_trigger", pattern_data)

    async def _learn_topic_pattern(self, user_id: str, topic: str, importance_score: float):
        """Learn topic interest patterns"""
        pattern_data = {
            "pattern_name": f"topic_interest_{topic}",
            "importance_multiplier": min(1.8, 1.0 + (importance_score - 0.5)),
            "confidence_score": importance_score,
            "frequency_count": 1,
            "pattern_keywords": [topic],
            "emotional_associations": [],
            "context_requirements": {},
        }
        await self.save_importance_pattern(user_id, "topic_interest", pattern_data)

    def _extract_topics_from_content(self, content: str) -> list[str]:
        """Extract topics from memory content for pattern learning"""
        # Simple topic extraction - could be enhanced with NLP
        topics = []
        topic_keywords = {
            "work": ["work", "job", "career", "office", "boss", "colleague"],
            "family": ["family", "mom", "dad", "sister", "brother", "parent"],
            "technology": ["programming", "code", "computer", "software", "tech"],
            "health": ["health", "medical", "doctor", "exercise", "fitness"],
            "hobbies": ["hobby", "music", "art", "game", "sport", "reading"],
            "travel": ["travel", "vacation", "trip", "journey", "visit"],
            "education": ["school", "learn", "study", "education", "class"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # Limit to top 3 topics

    def _extract_emotional_keywords(self, content: str) -> list[str]:
        """Extract emotional keywords from content"""
        emotional_words = []
        emotion_keywords = [
            "excited", "happy", "sad", "angry", "frustrated", "worried", "anxious",
            "proud", "disappointed", "grateful", "surprised", "confused", "scared"
        ]
        
        words = content.split()
        for word in words:
            if word in emotion_keywords:
                emotional_words.append(word)
        
        return emotional_words[:5]  # Limit to top 5 emotional words

    async def calculate_memory_importance(
        self,
        memory_id: str,
        user_id: str,
        memory_data: dict,
        user_history: list[dict],
        memory_manager=None,
    ) -> MemoryImportanceScore:
        """
        Calculate comprehensive importance score for a memory

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            memory_data: Memory content and metadata
            user_history: User's interaction history
            memory_manager: Memory manager for additional data

        Returns:
            Complete importance assessment
        """
        # Check cache first to avoid redundant calculations
        cache_key = f"{user_id}:{memory_id}"
        if cache_key in self.importance_cache:
            logger.debug(f"Retrieved cached importance for memory {memory_id}")
            return self.importance_cache[cache_key]

        logger.debug(f"Calculating importance for memory {memory_id}")

        try:
            # Calculate individual factor scores
            emotional_intensity = await self._assess_emotional_impact(memory_data, user_history)
            personal_relevance = await self._assess_personal_relevance(
                memory_data, user_id, user_history
            )
            recency = await self._calculate_recency_score(memory_data)
            access_frequency = await self._get_access_frequency(memory_id, user_id, memory_manager)
            uniqueness = await self._assess_uniqueness(memory_data, user_id, user_history)
            milestone = await self._check_milestone_significance(memory_data, user_history)

            # Create factor scores object
            factor_scores = ImportanceFactors(
                emotional_intensity=emotional_intensity,
                personal_relevance=personal_relevance,
                recency=recency,
                access_frequency=access_frequency,
                uniqueness=uniqueness,
                relationship_milestone=milestone,
            )

            # Calculate weighted overall score
            overall_score = self._calculate_weighted_score(factor_scores)

            # Calculate decay rate
            decay_rate = self._calculate_decay_rate(factor_scores, memory_data)

            # Generate explanation
            explanation = self._generate_score_explanation(factor_scores, overall_score)

            # Identify boost events
            boost_events = self._identify_boost_events(factor_scores)

            importance_score = MemoryImportanceScore(
                memory_id=memory_id,
                user_id=user_id,
                overall_score=overall_score,
                factor_scores=factor_scores,
                calculation_timestamp=datetime.now(UTC),
                score_explanation=explanation,
                decay_rate=decay_rate,
                boost_events=boost_events,
            )

            # Cache the result for future use
            self.importance_cache[cache_key] = importance_score

            logger.debug(f"Importance calculated: {overall_score:.3f} for memory {memory_id}")
            return importance_score

        except Exception as e:
            logger.error(f"Error calculating memory importance: {e}")
            # Return default score
            return self._create_default_importance_score(memory_id, user_id)

    async def _assess_emotional_impact(self, memory_data: dict, user_history: list[dict]) -> float:
        """Assess emotional significance of memory"""
        logger.debug("Assessing emotional impact")

        # Get emotional context from memory - handle both dict and string types
        emotional_context = memory_data.get("emotional_context", {})
        if isinstance(emotional_context, str):
            # If it's a string, try to parse it as JSON
            try:
                emotional_context = json.loads(emotional_context)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, create a default dict
                emotional_context = {
                    "primary_emotion": emotional_context if emotional_context else "neutral"
                }
        elif not isinstance(emotional_context, dict):
            # If it's neither string nor dict, create default
            emotional_context = {"primary_emotion": "neutral"}

        # Base emotional intensity
        emotional_intensity = emotional_context.get("intensity", 0.5)
        # Ensure emotional_intensity is a float
        if isinstance(emotional_intensity, str):
            try:
                emotional_intensity = float(emotional_intensity)
            except (ValueError, TypeError):
                emotional_intensity = 0.5
        elif not isinstance(emotional_intensity, (int, float)):
            emotional_intensity = 0.5

        primary_emotion = emotional_context.get("primary_emotion", "neutral")

        # Boost for strong emotions
        strong_emotions = {"joy", "sadness", "anger", "fear", "surprise", "love", "grief"}
        if primary_emotion in strong_emotions:
            emotional_intensity *= 1.3

        # Check if emotion was triggered or resolved
        if emotional_context.get("trigger_detected", False):
            emotional_intensity *= 1.2

        if emotional_context.get("resolution_achieved", False):
            emotional_intensity *= 1.4  # Resolution is very important

        # Check for subsequent emotional references
        content = memory_data.get("content", "").lower()
        memory_timestamp = memory_data.get("timestamp", datetime.now(UTC))

        # Ensure memory_timestamp is a datetime object
        if isinstance(memory_timestamp, str):
            try:
                memory_timestamp = datetime.fromisoformat(memory_timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                memory_timestamp = datetime.now(UTC)

        # Ensure timezone-aware
        memory_timestamp = self._ensure_timezone_aware(memory_timestamp)

        subsequent_references = 0
        for interaction in user_history:
            interaction_time = interaction.get("timestamp", datetime.now(UTC))
            if isinstance(interaction_time, str):
                try:
                    interaction_time = datetime.fromisoformat(
                        interaction_time.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    continue  # Skip invalid timestamps

            # Ensure timezone-aware
            interaction_time = self._ensure_timezone_aware(interaction_time)

            # Only look at interactions after this memory
            if interaction_time > memory_timestamp:
                interaction_content = interaction.get("content", "").lower()
                # Simple keyword matching for emotional references
                if any(word in interaction_content for word in content.split()[:5]):
                    subsequent_references += 1

        # Boost for memories that are referenced later
        if subsequent_references > 0:
            emotional_intensity *= 1 + min(subsequent_references * 0.1, 0.5)

        return min(emotional_intensity, 1.0)

    async def _assess_personal_relevance(
        self, memory_data: dict, user_id: str, user_history: list[dict]
    ) -> float:
        """Assess how personally relevant the memory is to the user"""
        logger.debug("Assessing personal relevance")

        relevance_score = 0.5  # Base relevance

        content = memory_data.get("content", "").lower()
        topic = memory_data.get("topic", "").lower()

        # Personal indicators in content
        personal_indicators = [
            "my",
            "mine",
            "myself",
            "i am",
            "i was",
            "i have",
            "i had",
            "i feel",
            "i think",
            "i believe",
            "i want",
            "i need",
            "my family",
            "my job",
            "my life",
            "my experience",
            "my problem",
            "my goal",
            "personal",
        ]

        personal_matches = sum(1 for indicator in personal_indicators if indicator in content)
        relevance_score += min(personal_matches * 0.05, 0.3)

        # Topic frequency in user's conversation history
        topic_frequency = sum(
            1
            for interaction in user_history
            if topic and topic in interaction.get("topic", "").lower()
        )

        if len(user_history) > 0:
            topic_ratio = topic_frequency / len(user_history)
            relevance_score += min(topic_ratio * 0.5, 0.4)

        # Self-disclosure level
        disclosure_keywords = [
            "secret",
            "private",
            "personal",
            "confess",
            "admit",
            "share",
            "tell you",
            "between us",
            "don't tell",
            "trust you",
            "opening up",
        ]

        disclosure_matches = sum(1 for keyword in disclosure_keywords if keyword in content)
        if disclosure_matches > 0:
            relevance_score += 0.2

        # Goals and aspirations
        goal_keywords = [
            "goal",
            "dream",
            "hope",
            "plan",
            "future",
            "want to",
            "aspire",
            "vision",
            "ambition",
            "achieve",
            "succeed",
        ]

        goal_matches = sum(1 for keyword in goal_keywords if keyword in content)
        relevance_score += min(goal_matches * 0.03, 0.15)

        return min(relevance_score, 1.0)

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime object is timezone-aware (UTC if naive)"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    async def _calculate_recency_score(self, memory_data: dict) -> float:
        """Calculate recency-based importance score"""
        logger.debug("Calculating recency score")

        memory_timestamp = memory_data.get("timestamp", datetime.now(UTC))
        if isinstance(memory_timestamp, str):
            try:
                memory_timestamp = datetime.fromisoformat(memory_timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                # If parsing fails, use current time (low recency score)
                memory_timestamp = datetime.now(UTC) - timedelta(days=365)

        # Ensure both datetimes are timezone-aware
        memory_timestamp = self._ensure_timezone_aware(memory_timestamp)
        now = datetime.now(UTC)
        days_old = (now - memory_timestamp).days

        # Ensure days_old is not negative
        days_old = max(0, days_old)

        # Exponential decay with configurable half-life
        half_life_days = 30  # Memory loses half importance after 30 days
        decay_factor = 0.5 ** (days_old / half_life_days)

        # Recent memories (< 7 days) get a boost
        if days_old < 7:
            recent_boost = 1.0 + (7 - days_old) * 0.05
            decay_factor *= recent_boost

        return min(decay_factor, 1.0)

    async def _get_access_frequency(
        self, memory_id: str, user_id: str, memory_manager=None
    ) -> float:
        """Calculate access frequency score"""
        logger.debug("Calculating access frequency")

        # This would ideally track actual access patterns
        # For now, we'll use a placeholder based on memory age and importance

        # Simulate access frequency based on memory characteristics
        # In a real implementation, this would track actual database queries
        base_frequency = 0.1  # Base access rate

        # More recent memories are accessed more
        # More important memories are accessed more
        # This is a simplified model

        return min(base_frequency + np.random.uniform(0, 0.4), 1.0)

    async def _assess_uniqueness(
        self, memory_data: dict, user_id: str, user_history: list[dict]
    ) -> float:
        """Assess how unique this memory is compared to others"""
        logger.debug("Assessing memory uniqueness")

        content = memory_data.get("content", "").lower()
        topic = memory_data.get("topic", "").lower()

        # Count similar topics in history
        similar_topics = sum(
            1
            for interaction in user_history
            if topic and topic in interaction.get("topic", "").lower()
        )

        # Calculate uniqueness based on topic rarity
        if len(user_history) == 0:
            topic_uniqueness = 1.0
        else:
            topic_frequency = similar_topics / len(user_history)
            topic_uniqueness = 1.0 - min(topic_frequency * 2, 0.8)  # Rare topics are more unique

        # Content uniqueness (simplified)
        content_words = set(content.split())
        all_history_words = set()

        for interaction in user_history:
            interaction_content = interaction.get("content", "").lower()
            all_history_words.update(interaction_content.split())

        if len(all_history_words) == 0:
            content_uniqueness = 1.0
        else:
            unique_words = content_words - all_history_words
            content_uniqueness = len(unique_words) / max(len(content_words), 1)

        # Combine topic and content uniqueness
        overall_uniqueness = (topic_uniqueness * 0.6) + (content_uniqueness * 0.4)

        return min(overall_uniqueness, 1.0)

    async def _check_milestone_significance(
        self, memory_data: dict, user_history: list[dict]
    ) -> float:
        """Check if memory represents a relationship or personal milestone"""
        logger.debug("Checking milestone significance")

        content = memory_data.get("content", "").lower()

        # Relationship milestones
        relationship_milestones = [
            "first time",
            "anniversary",
            "birthday",
            "graduation",
            "promotion",
            "wedding",
            "engagement",
            "birth",
            "death",
            "funeral",
            "celebration",
            "achievement",
            "award",
            "success",
            "failure",
            "breakthrough",
            "milestone",
            "turning point",
            "life-changing",
            "important moment",
        ]

        milestone_matches = sum(1 for milestone in relationship_milestones if milestone in content)

        if milestone_matches > 0:
            return min(milestone_matches * 0.3, 1.0)

        # Check for "first" or "last" occurrences
        first_last_indicators = ["first", "last", "final", "initial", "beginning", "start", "end"]
        first_last_matches = sum(1 for indicator in first_last_indicators if indicator in content)

        if first_last_matches > 0:
            return min(first_last_matches * 0.2, 0.6)

        return 0.0

    def _calculate_weighted_score(self, factor_scores: ImportanceFactors) -> float:
        """Calculate weighted overall importance score"""
        total_score = 0.0

        for factor, weight in self.importance_weights.items():
            factor_value = getattr(factor_scores, factor.value)
            total_score += factor_value * weight

        return min(total_score, 1.0)

    def _calculate_decay_rate(self, factor_scores: ImportanceFactors, memory_data: dict) -> float:
        """Calculate how quickly this memory should decay in importance"""
        base_decay = self.base_decay_rate

        # Emotional memories decay slower
        if factor_scores.emotional_intensity > self.emotional_preservation_threshold:
            base_decay *= 0.5

        # Frequently accessed memories decay slower
        if factor_scores.access_frequency > 0.7:
            base_decay *= 0.3

        # Milestone memories decay very slowly
        if factor_scores.relationship_milestone > 0.5:
            base_decay *= 0.2

        # Recent memories decay slower
        if factor_scores.recency > 0.8:
            base_decay *= 0.7

        return base_decay

    def _generate_score_explanation(
        self, factor_scores: ImportanceFactors, overall_score: float
    ) -> str:
        """Generate human-readable explanation of importance score"""
        explanations = []

        if factor_scores.emotional_intensity > 0.7:
            explanations.append("high emotional significance")

        if factor_scores.personal_relevance > 0.7:
            explanations.append("very personally relevant")

        if factor_scores.uniqueness > 0.7:
            explanations.append("unique content")

        if factor_scores.relationship_milestone > 0.5:
            explanations.append("milestone event")

        if factor_scores.access_frequency > 0.7:
            explanations.append("frequently referenced")

        if factor_scores.recency > 0.8:
            explanations.append("recent memory")

        if not explanations:
            explanations.append("moderate importance across factors")

        explanation = f"Score: {overall_score:.2f} - " + ", ".join(explanations)
        return explanation

    def _identify_boost_events(self, factor_scores: ImportanceFactors) -> list[str]:
        """Identify events that boosted the importance score"""
        boost_events = []

        if factor_scores.emotional_intensity > 0.8:
            boost_events.append("high_emotional_intensity")

        if factor_scores.personal_relevance > 0.8:
            boost_events.append("high_personal_relevance")

        if factor_scores.relationship_milestone > 0.5:
            boost_events.append("milestone_detected")

        if factor_scores.uniqueness > 0.8:
            boost_events.append("unique_content")

        if factor_scores.access_frequency > 0.7:
            boost_events.append("frequent_access")

        return boost_events

    async def auto_adjust_importance(self, user_id: str, memory_manager=None):
        """Automatically adjust importance scores based on patterns and time decay"""
        logger.info(f"Auto-adjusting importance scores for user {user_id}")

        try:
            if memory_manager is None:
                logger.error("Memory manager required for auto-adjustment")
                return

            # Get all user memories
            user_memories = await memory_manager.get_memories_by_user(user_id)

            # Apply time decay
            for memory in user_memories:
                memory_id = memory.get("id")
                if memory_id:
                    await self._apply_time_decay(memory_id, user_id, memory, memory_manager)

            # Boost memories connected to recent conversations
            await self._boost_recently_connected_memories(user_id, user_memories, memory_manager)

            # Adjust based on emotional pattern changes
            await self._adjust_for_emotional_patterns(user_id, user_memories, memory_manager)

            logger.info(f"Importance auto-adjustment completed for user {user_id}")

        except Exception as e:
            logger.error(f"Error in auto-adjustment: {e}")

    async def _apply_time_decay(
        self, memory_id: str, user_id: str, memory_data: dict, memory_manager
    ):
        """Apply time-based decay to memory importance"""
        cache_key = f"{user_id}_{memory_id}"

        if cache_key in self.importance_cache:
            cached_score = self.importance_cache[cache_key]

            # Calculate time elapsed since last calculation
            now = datetime.now(UTC)
            time_elapsed = now - cached_score.calculation_timestamp
            days_elapsed = time_elapsed.days

            if days_elapsed > 0:
                # Apply decay
                decay_amount = cached_score.decay_rate * days_elapsed
                new_score = max(cached_score.overall_score - decay_amount, 0.1)  # Minimum score

                # Update cached score
                cached_score.overall_score = new_score
                cached_score.calculation_timestamp = now

                # Update in memory manager if needed
                await self._update_memory_importance(memory_id, new_score, memory_manager)

    async def _boost_recently_connected_memories(
        self, user_id: str, user_memories: list[dict], memory_manager
    ):
        """Boost importance of memories connected to recent conversations"""
        # This would analyze recent conversations and boost related memories
        # Implementation would depend on conversation tracking system
        pass

    async def _adjust_for_emotional_patterns(
        self, user_id: str, user_memories: list[dict], memory_manager
    ):
        """Adjust importance based on emotional pattern changes"""
        # This would analyze emotional patterns and adjust memory importance accordingly
        # Implementation would depend on emotional intelligence system integration
        pass

    async def _update_memory_importance(self, memory_id: str, new_score: float, memory_manager):
        """Update memory importance in the storage system"""
        try:
            await memory_manager.update_memory_importance(memory_id, new_score)
        except Exception as e:
            logger.error(f"Failed to update memory importance: {e}")

    async def identify_core_memories(
        self, user_id: str, limit: int | None = None, memory_manager=None
    ) -> list[dict]:
        """
        Identify most important memories for user

        Args:
            user_id: User identifier
            limit: Maximum number of core memories (default: self.max_core_memories)
            memory_manager: Memory manager instance

        Returns:
            List of core memory dictionaries with importance scores
        """
        logger.info(f"Identifying core memories for user {user_id}")

        if limit is None:
            limit = self.max_core_memories

        try:
            if memory_manager is None:
                logger.error("Memory manager required")
                return []

            # Get all user memories
            user_memories = await memory_manager.get_memories_by_user(user_id)
            user_history = user_memories  # Simplified for this example

            # Calculate importance for each memory
            memory_scores = []
            for memory in user_memories:
                memory_id = memory.get("id")
                if memory_id:
                    importance_score = await self.calculate_memory_importance(
                        memory_id, user_id, memory, user_history, memory_manager
                    )

                    if importance_score.overall_score >= self.core_memory_threshold:
                        memory_scores.append(
                            {
                                "memory": memory,
                                "importance_score": importance_score,
                                "score_value": importance_score.overall_score,
                            }
                        )

            # Sort by importance and return top memories
            memory_scores.sort(key=lambda x: x["score_value"], reverse=True)
            core_memories = memory_scores[:limit]

            logger.info(f"Identified {len(core_memories)} core memories for user {user_id}")
            return core_memories

        except Exception as e:
            logger.error(f"Error identifying core memories: {e}")
            return []

    def _create_default_importance_score(
        self, memory_id: str, user_id: str
    ) -> MemoryImportanceScore:
        """Create default importance score for error cases"""
        factor_scores = ImportanceFactors(
            emotional_intensity=0.5,
            personal_relevance=0.5,
            recency=0.5,
            access_frequency=0.1,
            uniqueness=0.5,
            relationship_milestone=0.0,
        )

        return MemoryImportanceScore(
            memory_id=memory_id,
            user_id=user_id,
            overall_score=0.5,
            factor_scores=factor_scores,
            calculation_timestamp=datetime.now(UTC),
            score_explanation="Default score due to calculation error",
            decay_rate=self.base_decay_rate,
            boost_events=[],
        )

    def get_importance_statistics(self, user_id: str) -> dict[str, Any]:
        """Get importance calculation statistics for user"""
        user_scores = [
            score for key, score in self.importance_cache.items() if key.startswith(f"{user_id}_")
        ]

        if not user_scores:
            return {}

        scores = [score.overall_score for score in user_scores]

        return {
            "total_memories_scored": len(user_scores),
            "average_importance": statistics.mean(scores),
            "median_importance": statistics.median(scores),
            "max_importance": max(scores),
            "min_importance": min(scores),
            "core_memory_candidates": len([s for s in scores if s >= self.core_memory_threshold]),
            "factor_averages": self._calculate_factor_averages(user_scores),
        }

    def _calculate_factor_averages(
        self, user_scores: list[MemoryImportanceScore]
    ) -> dict[str, float]:
        """Calculate average scores for each importance factor"""
        factors = {
            "emotional_intensity": [],
            "personal_relevance": [],
            "recency": [],
            "access_frequency": [],
            "uniqueness": [],
            "relationship_milestone": [],
        }

        for score in user_scores:
            for factor in factors:
                factors[factor].append(getattr(score.factor_scores, factor))

        return {
            factor: statistics.mean(values) if values else 0.0 for factor, values in factors.items()
        }

    def clear_cache(self, user_id: str | None = None):
        """Clear importance cache for user or all users"""
        if user_id:
            # Clear cache for specific user
            keys_to_remove = [
                key for key in self.importance_cache.keys() if key.startswith(f"{user_id}_")
            ]
            for key in keys_to_remove:
                del self.importance_cache[key]
            logger.info(f"Cleared importance cache for user {user_id}")
        else:
            # Clear all cache
            self.importance_cache.clear()
            logger.info("Cleared all importance cache")

    # ===== DATABASE PERSISTENCE METHODS =====

    async def initialize_persistence(self):
        """Initialize database persistence for memory importance patterns"""
        if self._get_db_connection():
            self._ensure_memory_importance_tables()
            logger.info("Memory importance persistence initialized")
            
            # Load existing patterns for optimization
            logger.info("Memory importance persistence ready")
        else:
            logger.warning(
                "Database not available - memory importance patterns will not persist across restarts"
            )

    def _get_db_connection(self):
        """Get database connection for memory importance persistence"""
        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL not available - memory importance data will not persist")
            return None

        try:
            connection = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "whisper_engine"),
                user=os.getenv("POSTGRES_USER", "bot_user"),
                password=os.getenv("POSTGRES_PASSWORD", "securepassword123"),
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL for memory importance persistence: {e}")
            return None

    def _ensure_memory_importance_tables(self):
        """Ensure memory importance tables exist in the database"""
        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                # Read and execute schema
                import pathlib
                schema_path = pathlib.Path(__file__).parent.parent.parent / "docs" / "database" / "memory_importance_schema.sql"
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                cursor.execute(schema_sql)
                connection.commit()
                logger.info("Memory importance database tables ensured")
                return True
        except Exception as e:
            logger.error(f"Failed to create memory importance tables: {e}")
            return False
        finally:
            connection.close()

    async def save_user_memory_statistics(self, user_id: str, statistics_data: dict) -> bool:
        """Save user memory statistics to database"""
        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_memory_statistics (
                        user_id, total_memories_scored, average_importance_score,
                        median_importance_score, max_importance_score, min_importance_score,
                        core_memory_count, emotional_intensity_weight, personal_relevance_weight,
                        recency_weight, access_frequency_weight, uniqueness_weight,
                        relationship_milestone_weight, pattern_learning_confidence,
                        total_pattern_adjustments, factor_averages, memory_type_preferences,
                        temporal_patterns, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_memories_scored = EXCLUDED.total_memories_scored,
                        average_importance_score = EXCLUDED.average_importance_score,
                        median_importance_score = EXCLUDED.median_importance_score,
                        max_importance_score = EXCLUDED.max_importance_score,
                        min_importance_score = EXCLUDED.min_importance_score,
                        core_memory_count = EXCLUDED.core_memory_count,
                        emotional_intensity_weight = EXCLUDED.emotional_intensity_weight,
                        personal_relevance_weight = EXCLUDED.personal_relevance_weight,
                        recency_weight = EXCLUDED.recency_weight,
                        access_frequency_weight = EXCLUDED.access_frequency_weight,
                        uniqueness_weight = EXCLUDED.uniqueness_weight,
                        relationship_milestone_weight = EXCLUDED.relationship_milestone_weight,
                        pattern_learning_confidence = EXCLUDED.pattern_learning_confidence,
                        total_pattern_adjustments = EXCLUDED.total_pattern_adjustments,
                        factor_averages = EXCLUDED.factor_averages,
                        memory_type_preferences = EXCLUDED.memory_type_preferences,
                        temporal_patterns = EXCLUDED.temporal_patterns,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        user_id,
                        statistics_data.get("total_memories_scored", 0),
                        statistics_data.get("average_importance", 0.5),
                        statistics_data.get("median_importance", 0.5),
                        statistics_data.get("max_importance", 0.0),
                        statistics_data.get("min_importance", 1.0),
                        statistics_data.get("core_memory_candidates", 0),
                        self.importance_weights.get(ImportanceFactor.EMOTIONAL_INTENSITY, 0.30),
                        self.importance_weights.get(ImportanceFactor.PERSONAL_RELEVANCE, 0.25),
                        self.importance_weights.get(ImportanceFactor.RECENCY, 0.15),
                        self.importance_weights.get(ImportanceFactor.ACCESS_FREQUENCY, 0.15),
                        self.importance_weights.get(ImportanceFactor.UNIQUENESS, 0.10),
                        self.importance_weights.get(ImportanceFactor.RELATIONSHIP_MILESTONE, 0.05),
                        0.0,  # pattern_learning_confidence - will be calculated
                        0,    # total_pattern_adjustments
                        json.dumps(statistics_data.get("factor_averages", {})),
                        json.dumps({}),  # memory_type_preferences - to be implemented
                        json.dumps({}),  # temporal_patterns - to be implemented
                        datetime.now(UTC),
                    ),
                )
                connection.commit()
                logger.debug("Saved memory statistics for user %s", user_id)
                return True
        except Exception as e:
            logger.error("Failed to save memory statistics for user %s: %s", user_id, e)
            return False
        finally:
            connection.close()

    async def load_user_memory_statistics(self, user_id: str) -> dict | None:
        """Load user memory statistics from database"""
        connection = self._get_db_connection()
        if not connection:
            return None

        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM user_memory_statistics
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
                if result:
                    # Convert to regular dict and parse JSON fields
                    stats = dict(result)
                    stats["factor_averages"] = self._safe_json_loads(stats.get("factor_averages", "{}"), {})
                    stats["memory_type_preferences"] = self._safe_json_loads(stats.get("memory_type_preferences", "{}"), {})
                    stats["temporal_patterns"] = self._safe_json_loads(stats.get("temporal_patterns", "{}"), {})
                    logger.debug("Loaded memory statistics for user %s", user_id)
                    return stats
                return None
        except Exception as e:
            logger.error("Failed to load memory statistics for user %s: %s", user_id, e)
            return None
        finally:
            connection.close()

    async def save_importance_pattern(self, user_id: str, pattern_type: str, pattern_data: dict) -> bool:
        """Save a memory importance pattern for a user"""
        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_memory_importance_patterns (
                        user_id, pattern_type, pattern_name, importance_multiplier,
                        confidence_score, frequency_count, success_rate,
                        pattern_keywords, emotional_associations, context_requirements,
                        user_feedback_score, memory_recall_frequency, pattern_metadata,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (user_id, pattern_type, pattern_name) DO UPDATE SET
                        importance_multiplier = EXCLUDED.importance_multiplier,
                        confidence_score = EXCLUDED.confidence_score,
                        frequency_count = EXCLUDED.frequency_count,
                        success_rate = EXCLUDED.success_rate,
                        pattern_keywords = EXCLUDED.pattern_keywords,
                        emotional_associations = EXCLUDED.emotional_associations,
                        context_requirements = EXCLUDED.context_requirements,
                        user_feedback_score = EXCLUDED.user_feedback_score,
                        memory_recall_frequency = EXCLUDED.memory_recall_frequency,
                        pattern_metadata = EXCLUDED.pattern_metadata,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        user_id,
                        pattern_type,
                        pattern_data.get("pattern_name", ""),
                        pattern_data.get("importance_multiplier", 1.0),
                        pattern_data.get("confidence_score", 0.0),
                        pattern_data.get("frequency_count", 1),
                        pattern_data.get("success_rate", 0.0),
                        json.dumps(pattern_data.get("pattern_keywords", [])),
                        json.dumps(pattern_data.get("emotional_associations", [])),
                        json.dumps(pattern_data.get("context_requirements", {})),
                        pattern_data.get("user_feedback_score", 0.0),
                        pattern_data.get("memory_recall_frequency", 0.0),
                        json.dumps(pattern_data.get("pattern_metadata", {})),
                        datetime.now(UTC),
                    ),
                )
                connection.commit()
                logger.debug("Saved importance pattern for user %s: %s", user_id, pattern_type)
                return True
        except Exception as e:
            logger.error("Failed to save importance pattern for user %s: %s", user_id, e)
            return False
        finally:
            connection.close()

    async def load_user_importance_patterns(self, user_id: str, pattern_type: str | None = None) -> list[dict]:
        """Load importance patterns for a user"""
        connection = self._get_db_connection()
        if not connection:
            return []

        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if pattern_type:
                    cursor.execute(
                        """
                        SELECT * FROM user_memory_importance_patterns
                        WHERE user_id = %s AND pattern_type = %s
                        ORDER BY confidence_score DESC, frequency_count DESC
                        """,
                        (user_id, pattern_type),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM user_memory_importance_patterns
                        WHERE user_id = %s
                        ORDER BY pattern_type, confidence_score DESC
                        """,
                        (user_id,),
                    )
                
                results = cursor.fetchall()
                patterns = []
                for result in results:
                    pattern = dict(result)
                    # Parse JSON fields
                    pattern["pattern_keywords"] = self._safe_json_loads(pattern.get("pattern_keywords", "[]"), [])
                    pattern["emotional_associations"] = self._safe_json_loads(pattern.get("emotional_associations", "[]"), [])
                    pattern["context_requirements"] = self._safe_json_loads(pattern.get("context_requirements", "{}"), {})
                    pattern["pattern_metadata"] = self._safe_json_loads(pattern.get("pattern_metadata", "{}"), {})
                    patterns.append(pattern)
                
                logger.debug("Loaded %d importance patterns for user %s", len(patterns), user_id)
                return patterns
        except Exception as e:
            logger.error("Failed to load importance patterns for user %s: %s", user_id, e)
            return []
        finally:
            connection.close()

    def _safe_json_loads(self, value, default=None):
        """Safely parse JSON value with fallback"""
        if value is None:
            return default if default is not None else {}
        
        if isinstance(value, (dict, list)):
            return value
            
        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to parse JSON: %s... Error: %s", str(value)[:50], e)
            return default if default is not None else {}

    async def update_user_importance_weights(self, user_id: str, learned_weights: dict) -> bool:
        """Update user-specific importance factor weights based on learning"""
        # Update internal weights
        for factor, weight in learned_weights.items():
            if factor in self.importance_weights:
                self.importance_weights[factor] = weight
        
        # Save to database as part of user statistics
        current_stats = await self.load_user_memory_statistics(user_id) or {}
        current_stats.update({
            "emotional_intensity_weight": learned_weights.get(ImportanceFactor.EMOTIONAL_INTENSITY, 0.30),
            "personal_relevance_weight": learned_weights.get(ImportanceFactor.PERSONAL_RELEVANCE, 0.25),
            "recency_weight": learned_weights.get(ImportanceFactor.RECENCY, 0.15),
            "access_frequency_weight": learned_weights.get(ImportanceFactor.ACCESS_FREQUENCY, 0.15),
            "uniqueness_weight": learned_weights.get(ImportanceFactor.UNIQUENESS, 0.10),
            "relationship_milestone_weight": learned_weights.get(ImportanceFactor.RELATIONSHIP_MILESTONE, 0.05),
            "pattern_learning_confidence": min(1.0, current_stats.get("pattern_learning_confidence", 0.0) + 0.1),
            "total_pattern_adjustments": current_stats.get("total_pattern_adjustments", 0) + 1,
        })
        
        return await self.save_user_memory_statistics(user_id, current_stats)
