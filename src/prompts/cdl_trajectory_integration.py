"""
CDL Trajectory Integration Module

Purpose:
    Bridge TrajectoryAnalyzer with CDL prompt system to enable trajectory-aware character responses.
    Converts trajectory context into actionable emotional guidance for character personalities.

Architecture:
    1. TrajectoryAnalyzer.retrieve_trajectory_context() → TrajectoryVector metadata
    2. CDLTrajectoryIntegration formats for CDL system prompt injection
    3. Character personality can reference emotional trajectory in responses

Examples:
    User has been getting increasingly frustrated over 15 minutes:
    → "I've noticed you getting more frustrated lately..."

    User's mood is fluctuating unpredictably:
    → "You seem to be riding quite an emotional rollercoaster..."

    User has been stable and calm:
    → "You seem to be in a steady, peaceful place..."

Features:
    • Trajectory-aware emotional guidance generation
    • Context-specific prompt injection for different character archetypes
    • Fallback to basic trajectory if TrajectoryAnalyzer unavailable
    • Metadata enrichment with time-based trajectory descriptions
    • Confidence scoring for trajectory reliability

Module Dependencies:
    - src.intelligence.trajectory_analyzer (TrajectoryAnalyzer)
    - src.memory.vector_memory_system (VectorMemoryManager for fallback)

Created: October 2025
Author: WhisperEngine Development
Status: Phase 2 Task 2
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


class CDLTrajectoryIntegration:
    """
    Integration layer between TrajectoryAnalyzer and CDL prompt system.

    Responsibilities:
    1. Query trajectory context via TrajectoryAnalyzer
    2. Convert trajectory vectors to CDL prompt components
    3. Generate character-aware emotional guidance
    4. Inject into CDL system prompts with proper priority weighting
    5. Handle graceful fallback to basic trajectory
    """

    def __init__(self, trajectory_analyzer=None, memory_manager=None):
        """
        Initialize CDL trajectory integration.

        Args:
            trajectory_analyzer: TrajectoryAnalyzer instance (lazy-loaded if None)
            memory_manager: VectorMemoryManager for fallback trajectory
        """
        self.trajectory_analyzer = trajectory_analyzer
        self.memory_manager = memory_manager
        self._analyzer_imported = False

    async def _ensure_analyzer(self):
        """Lazy-load TrajectoryAnalyzer if not provided."""
        if not self._analyzer_imported:
            try:
                from src.intelligence.trajectory_analyzer import TrajectoryAnalyzer

                if self.trajectory_analyzer is None:
                    self.trajectory_analyzer = TrajectoryAnalyzer(
                        memory_manager=self.memory_manager
                    )
                self._analyzer_imported = True
            except ImportError as e:
                logger.warning(
                    "Failed to import TrajectoryAnalyzer: %s. Falling back to basic trajectory.",
                    str(e),
                )
                self._analyzer_imported = True

    async def get_trajectory_context_for_cdl(
        self, user_id: str, lookback_messages: int = 15, include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve trajectory context optimized for CDL prompt injection.

        Returns dict with:
            {
                'has_trajectory': bool,
                'trajectory_summary': str,  # Natural language summary
                'trend_type': str,          # Classification (e.g., 'RISING_SHARP')
                'emotional_awareness': str, # Character-aware guidance phrase
                'confidence': float,        # 0.0-1.0 reliability score
                'time_context': str,        # "over the last 15 minutes" etc
                'injection_priority': float, # 0.0-1.0 prompt injection weight
                'fallback_trajectory': Dict # Basic trajectory metadata if needed
            }

        Args:
            user_id: Discord user ID or platform-specific identifier
            lookback_messages: Number of recent messages to analyze
            include_summary: Whether to generate natural language summary

        Returns:
            Complete trajectory context dict optimized for CDL injection
        """
        try:
            await self._ensure_analyzer()

            if not self.trajectory_analyzer:
                logger.debug(
                    "TrajectoryAnalyzer unavailable for %s, using basic trajectory",
                    user_id,
                )
                return await self._get_basic_trajectory_context(user_id)

            # Get trajectory from analyzer
            trajectory_context = await self.trajectory_analyzer.retrieve_trajectory_context(
                user_id, lookback_messages=lookback_messages, include_summary=include_summary
            )

            if not trajectory_context.get("has_trajectory"):
                logger.debug("No trajectory data for user %s", user_id)
                return {
                    "has_trajectory": False,
                    "trajectory_summary": "",
                    "trend_type": "UNKNOWN",
                    "emotional_awareness": "",
                    "confidence": 0.0,
                    "time_context": "",
                    "injection_priority": 0.0,
                    "fallback_trajectory": {},
                }

            # Convert TrajectoryVector to CDL-optimized format
            trajectory_vector = trajectory_context.get("trajectory_vector")
            if not trajectory_vector:
                return {
                    "has_trajectory": False,
                    "trajectory_summary": "",
                    "confidence": 0.0,
                    "injection_priority": 0.0,
                }

            # Build CDL-optimized context
            trend_type = trajectory_context.get("trend", "UNKNOWN")
            summary = trajectory_context.get("summary", "")
            direction = trajectory_context.get("direction", 0.0)
            magnitude = trajectory_context.get("magnitude", 0.0)
            variance = trajectory_context.get("variance", 0.0)
            points_count = trajectory_context.get("points_count", 0)

            # Generate character-aware emotional guidance
            emotional_awareness = self._generate_emotional_awareness(
                trend_type, magnitude, variance, direction
            )

            # Calculate time context string
            time_span = trajectory_vector.time_span if trajectory_vector else None
            time_context = self._format_time_context(time_span)

            # Calculate confidence score (based on data quality)
            confidence = self._calculate_trajectory_confidence(points_count, variance, magnitude)

            # Calculate injection priority (higher = more important for prompt)
            injection_priority = self._calculate_injection_priority(magnitude, trend_type, confidence)

            cdl_context = {
                "has_trajectory": True,
                "trajectory_summary": summary,
                "trend_type": trend_type,
                "emotional_awareness": emotional_awareness,
                "confidence": confidence,
                "time_context": time_context,
                "injection_priority": injection_priority,
                "trajectory_metadata": {
                    "direction": direction,
                    "magnitude": magnitude,
                    "variance": variance,
                    "points_count": points_count,
                    "stability": 1.0 - variance,  # Inverse of variance
                },
                "fallback_trajectory": {},  # No fallback needed if successful
            }

            logger.debug(
                "Generated CDL trajectory context for %s: trend=%s, priority=%.2f, confidence=%.2f",
                user_id,
                trend_type,
                injection_priority,
                confidence,
            )

            return cdl_context

        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(
                "Error getting trajectory context for CDL for user %s: %s",
                user_id,
                str(e),
            )
            return {
                "has_trajectory": False,
                "trajectory_summary": "",
                "confidence": 0.0,
                "injection_priority": 0.0,
                "error": str(e),
            }

    async def _get_basic_trajectory_context(self, user_id: str) -> Dict[str, Any]:
        """
        Fallback to basic trajectory system from vector_memory_system.

        Returns basic trajectory metadata with lower confidence/priority.
        """
        try:
            if not self.memory_manager:
                return {
                    "has_trajectory": False,
                    "trajectory_summary": "",
                    "confidence": 0.0,
                    "injection_priority": 0.0,
                }

            # Get basic trajectory from vector memory
            # This would call vector_memory_system.track_emotional_trajectory()
            # For now, return empty since it's not directly accessible
            logger.debug("Basic trajectory fallback not fully implemented for %s", user_id)

            return {
                "has_trajectory": False,
                "trajectory_summary": "",
                "confidence": 0.0,
                "injection_priority": 0.0,
            }

        except (AttributeError, KeyError, TypeError) as e:
            logger.error("Error getting basic trajectory context for %s: %s", user_id, str(e))
            return {
                "has_trajectory": False,
                "trajectory_summary": "",
                "confidence": 0.0,
                "injection_priority": 0.0,
            }

    def _generate_emotional_awareness(
        self, trend_type: str, magnitude: float, variance: float, _direction: float
    ) -> str:
        """
        Generate character-aware emotional guidance phrase.

        Examples:
            RISING_SHARP → "getting increasingly frustrated"
            FALLING_STEADY → "becoming more calm"
            VOLATILE → "experiencing emotional ups and downs"
            STABLE_LOW → "in a consistently subdued mood"

        Args:
            trend_type: TrajectoryTrend classification
            magnitude: Total change (0.0-1.0)
            variance: Emotional stability (lower = more stable)
            _direction: Slope (-1.0 to 1.0) - currently unused

        Returns:
            Natural language phrase for character to reference
        """
        try:
            # Map trend types to character-aware phrases
            trend_phrases = {
                "RISING_SHARP": "getting increasingly intense about things",
                "RISING_STEADY": "gradually becoming more engaged",
                "FALLING_SHARP": "rapidly mellowing out",
                "FALLING_STEADY": "slowly becoming more calm",
                "STABLE_LOW": "in a consistently subdued emotional state",
                "STABLE_NEUTRAL": "maintaining a balanced emotional state",
                "STABLE_HIGH": "staying in an elevated emotional place",
                "VOLATILE": "experiencing significant emotional fluctuations",
                "UNKNOWN": "on an unclear emotional trajectory",
            }

            base_phrase = trend_phrases.get(trend_type, "experiencing emotional changes")

            # Add intensity modifier
            if magnitude > 0.7:
                intensity = "quite dramatically "
            elif magnitude > 0.4:
                intensity = "noticeably "
            else:
                intensity = "somewhat "

            # Add stability context
            if variance > 0.15:
                stability = " - your emotional baseline seems pretty unpredictable"
            elif variance > 0.08:
                stability = " - with some fluctuation"
            else:
                stability = ""

            awareness_phrase = f"{intensity}{base_phrase}{stability}"

            logger.debug(
                "Generated emotional awareness: %s (trend=%s, magnitude=%.2f, variance=%.2f)",
                awareness_phrase,
                trend_type,
                magnitude,
                variance,
            )

            return awareness_phrase

        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Error generating emotional awareness: %s", str(e))
            return "on an emotional journey"

    def _format_time_context(self, time_span: Optional[timedelta]) -> str:
        """
        Format time span into natural language context.

        Examples:
            5 minutes → "over the last few minutes"
            45 minutes → "over the past hour"
            2 hours → "over the last couple of hours"
            1 day → "over the last day"

        Args:
            time_span: Duration of trajectory data

        Returns:
            Formatted time context string
        """
        if not time_span:
            return ""

        try:
            total_seconds = time_span.total_seconds()
            minutes = total_seconds / 60
            hours = minutes / 60
            days = hours / 24

            if minutes < 10:
                return "over the last few minutes"
            elif minutes < 60:
                return f"over the last {int(minutes)} minutes"
            elif hours < 1.5:
                return "over the past hour"
            elif hours < 24:
                hour_count = int(hours)
                return f"over the last {hour_count} hour{'s' if hour_count != 1 else ''}"
            elif days < 2:
                return "over the last day"
            else:
                day_count = int(days)
                return f"over the last {day_count} days"

        except Exception as e:
            logger.warning("Error formatting time context: %s", str(e))
            return ""

    def _calculate_trajectory_confidence(
        self, points_count: int, variance: float, magnitude: float
    ) -> float:
        """
        Calculate confidence score for trajectory analysis.

        Factors:
            • Data quality: More data points = higher confidence
            • Stability: Lower variance = higher confidence
            • Magnitude: Some change is more reliable than extreme values

        Args:
            points_count: Number of emotional data points
            variance: Emotional stability metric (0.0-1.0)
            magnitude: Total change magnitude (0.0-1.0)

        Returns:
            Confidence score 0.0-1.0
        """
        try:
            # Base score from data points (need at least 3 for confidence)
            if points_count < 2:
                return 0.1
            elif points_count < 3:
                return 0.4
            elif points_count < 5:
                return 0.6
            elif points_count < 8:
                return 0.75
            else:
                base_score = 0.9

            # Adjust for variance (extreme volatility reduces confidence)
            if variance > 0.2:
                variance_penalty = 0.1
            elif variance > 0.15:
                variance_penalty = 0.05
            else:
                variance_penalty = 0

            # Adjust for magnitude (moderate changes more reliable than extreme)
            if magnitude > 0.9 or magnitude < 0.05:
                magnitude_penalty = 0.05
            else:
                magnitude_penalty = 0

            confidence = base_score - variance_penalty - magnitude_penalty
            return max(0.0, min(1.0, confidence))  # Clamp to 0.0-1.0

        except (ValueError, TypeError) as e:
            logger.warning("Error calculating trajectory confidence: %s", str(e))
            return 0.5

    def _calculate_injection_priority(
        self, magnitude: float, trend_type: str, confidence: float
    ) -> float:
        """
        Calculate priority for CDL prompt injection.

        Higher values = more important to include in final prompt.

        Factors:
            • Magnitude: Bigger changes = higher priority
            • Trend type: Sharp changes > gradual changes
            • Confidence: More reliable data = higher priority

        Args:
            magnitude: Total change magnitude (0.0-1.0)
            trend_type: Classification (RISING_SHARP, STABLE_LOW, etc.)
            confidence: Confidence score (0.0-1.0)

        Returns:
            Injection priority 0.0-1.0
        """
        try:
            # Base priority from magnitude
            if magnitude < 0.1:
                base_priority = 0.2  # Stable = lower priority
            elif magnitude < 0.3:
                base_priority = 0.4
            elif magnitude < 0.6:
                base_priority = 0.6
            else:
                base_priority = 0.8  # High magnitude = higher priority

            # Boost for sharp trends
            if "SHARP" in trend_type:
                trend_boost = 0.15
            elif "VOLATILE" in trend_type:
                trend_boost = 0.1
            else:
                trend_boost = 0

            # Apply confidence as multiplier
            final_priority = (base_priority + trend_boost) * confidence

            return max(0.0, min(1.0, final_priority))

        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Error calculating injection priority: %s", str(e))
            return 0.5

    def format_for_cdl_prompt(
        self,
        trajectory_context: Dict[str, Any],
        character_archetype: str = "real-world",
        include_time_reference: bool = True,
    ) -> str:
        """
        Format trajectory context for direct CDL prompt injection.

        Generates a natural language block ready for system prompt inclusion.

        Args:
            trajectory_context: Output from get_trajectory_context_for_cdl()
            character_archetype: Character type ('real-world', 'fantasy', 'narrative_ai')
            include_time_reference: Include time context in output

        Returns:
            Formatted string ready for CDL system prompt
        """
        try:
            if not trajectory_context.get("has_trajectory"):
                return ""

            summary = trajectory_context.get("trajectory_summary", "")
            awareness = trajectory_context.get("emotional_awareness", "")
            time_context = (
                trajectory_context.get("time_context", "") if include_time_reference else ""
            )

            if not summary:
                return ""

            # Build prompt block based on character archetype
            if character_archetype == "fantasy":
                # Fantasy characters may reference trajectory more mystically
                prompt_block = f"[Emotional Context: {summary}{' ' + time_context if time_context else ''}]"
            elif character_archetype == "narrative_ai":
                # Narrative AI characters can be more meta about emotional tracking
                prompt_block = f"[Character Context: The user's emotional state {summary}{' ' + time_context if time_context else ''}]"
            else:
                # Real-world characters reference naturally
                prompt_block = f"[Context Note: {awareness}{' ' + time_context if time_context else ''}]"

            logger.debug(
                "Formatted trajectory for CDL prompt (archetype=%s): %s",
                character_archetype,
                prompt_block[:50],
            )

            return prompt_block

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Error formatting trajectory for CDL prompt: %s", str(e))
            return ""

    def should_inject_trajectory_into_prompt(
        self, trajectory_context: Dict[str, Any], prompt_word_count: int
    ) -> bool:
        """
        Determine whether trajectory should be injected into final prompt.

        Decision factors:
            • Injection priority >= 0.4
            • Confidence >= 0.5
            • Available prompt space (word budget)
            • Data quality (minimum points)

        Args:
            trajectory_context: Output from get_trajectory_context_for_cdl()
            prompt_word_count: Current prompt word count

        Returns:
            True if trajectory should be injected, False otherwise
        """
        try:
            if not trajectory_context.get("has_trajectory"):
                return False

            priority = trajectory_context.get("injection_priority", 0.0)
            confidence = trajectory_context.get("confidence", 0.0)
            points_count = (
                trajectory_context.get("trajectory_metadata", {}).get("points_count", 0)
            )

            # Minimum thresholds
            if priority < 0.4 or confidence < 0.5 or points_count < 2:
                logger.debug(
                    "Trajectory filtered: priority=%.2f, confidence=%.2f, points=%d",
                    priority,
                    confidence,
                    points_count,
                )
                return False

            # Check word budget (trajectory block ~20-30 words)
            if prompt_word_count > 2800:  # Leave room for trajectory if close to limit
                if priority < 0.7:
                    logger.debug("Trajectory filtered due to prompt size and low priority")
                    return False

            logger.debug(
                "Trajectory approved for injection: priority=%.2f, confidence=%.2f",
                priority,
                confidence,
            )

            return True

        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Error determining trajectory injection: %s", str(e))
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


async def create_cdl_trajectory_integration(
    vector_memory_manager=None, trajectory_analyzer=None
) -> CDLTrajectoryIntegration:
    """
    Factory function to create CDL trajectory integration instance.

    Args:
        vector_memory_manager: Injected memory manager for fallback
        trajectory_analyzer: Injected trajectory analyzer

    Returns:
        Initialized CDLTrajectoryIntegration instance
    """
    return CDLTrajectoryIntegration(
        trajectory_analyzer=trajectory_analyzer, memory_manager=vector_memory_manager
    )
