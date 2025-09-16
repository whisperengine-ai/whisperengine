"""
Memory Importance Engine
=======================

Advanced system for calculating and managing memory importance scores
based on multiple factors including emotional impact, personal relevance,
recency, access frequency, and uniqueness.

Phase 3: Multi-Dimensional Memory Networks
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import statistics
import math

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

    def to_dict(self) -> Dict[str, float]:
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
    boost_events: List[str]


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

        logger.info("Memory Importance Engine initialized")

    async def calculate_memory_importance(
        self,
        memory_id: str,
        user_id: str,
        memory_data: Dict,
        user_history: List[Dict],
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
                calculation_timestamp=datetime.now(timezone.utc),
                score_explanation=explanation,
                decay_rate=decay_rate,
                boost_events=boost_events,
            )

            # Cache the result
            cache_key = f"{user_id}_{memory_id}"
            self.importance_cache[cache_key] = importance_score

            logger.debug(f"Importance calculated: {overall_score:.3f} for memory {memory_id}")
            return importance_score

        except Exception as e:
            logger.error(f"Error calculating memory importance: {e}")
            # Return default score
            return self._create_default_importance_score(memory_id, user_id)

    async def _assess_emotional_impact(self, memory_data: Dict, user_history: List[Dict]) -> float:
        """Assess emotional significance of memory"""
        logger.debug("Assessing emotional impact")

        # Get emotional context from memory - handle both dict and string types
        emotional_context = memory_data.get("emotional_context", {})
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
        memory_timestamp = memory_data.get("timestamp", datetime.now(timezone.utc))

        # Ensure memory_timestamp is a datetime object
        if isinstance(memory_timestamp, str):
            try:
                memory_timestamp = datetime.fromisoformat(memory_timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                memory_timestamp = datetime.now(timezone.utc)

        # Ensure timezone-aware
        memory_timestamp = self._ensure_timezone_aware(memory_timestamp)

        subsequent_references = 0
        for interaction in user_history:
            interaction_time = interaction.get("timestamp", datetime.now(timezone.utc))
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
        self, memory_data: Dict, user_id: str, user_history: List[Dict]
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
            return dt.replace(tzinfo=timezone.utc)
        return dt

    async def _calculate_recency_score(self, memory_data: Dict) -> float:
        """Calculate recency-based importance score"""
        logger.debug("Calculating recency score")

        memory_timestamp = memory_data.get("timestamp", datetime.now(timezone.utc))
        if isinstance(memory_timestamp, str):
            try:
                memory_timestamp = datetime.fromisoformat(memory_timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                # If parsing fails, use current time (low recency score)
                memory_timestamp = datetime.now(timezone.utc) - timedelta(days=365)

        # Ensure both datetimes are timezone-aware
        memory_timestamp = self._ensure_timezone_aware(memory_timestamp)
        now = datetime.now(timezone.utc)
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
        self, memory_data: Dict, user_id: str, user_history: List[Dict]
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
        self, memory_data: Dict, user_history: List[Dict]
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

    def _calculate_decay_rate(self, factor_scores: ImportanceFactors, memory_data: Dict) -> float:
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

    def _identify_boost_events(self, factor_scores: ImportanceFactors) -> List[str]:
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
        self, memory_id: str, user_id: str, memory_data: Dict, memory_manager
    ):
        """Apply time-based decay to memory importance"""
        cache_key = f"{user_id}_{memory_id}"

        if cache_key in self.importance_cache:
            cached_score = self.importance_cache[cache_key]

            # Calculate time elapsed since last calculation
            now = datetime.now(timezone.utc)
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
        self, user_id: str, user_memories: List[Dict], memory_manager
    ):
        """Boost importance of memories connected to recent conversations"""
        # This would analyze recent conversations and boost related memories
        # Implementation would depend on conversation tracking system
        pass

    async def _adjust_for_emotional_patterns(
        self, user_id: str, user_memories: List[Dict], memory_manager
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
        self, user_id: str, limit: Optional[int] = None, memory_manager=None
    ) -> List[Dict]:
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
            calculation_timestamp=datetime.now(timezone.utc),
            score_explanation="Default score due to calculation error",
            decay_rate=self.base_decay_rate,
            boost_events=[],
        )

    def get_importance_statistics(self, user_id: str) -> Dict[str, Any]:
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
        self, user_scores: List[MemoryImportanceScore]
    ) -> Dict[str, float]:
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

    def clear_cache(self, user_id: Optional[str] = None):
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
