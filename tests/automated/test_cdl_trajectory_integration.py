"""
Tests for CDL Trajectory Integration Module

Purpose:
    Validate CDLTrajectoryIntegration functionality for CDL prompt injection.
    Tests cover trajectory context retrieval, formatting, injection decisions, and fallback behavior.

Coverage:
    • Context retrieval and optimization
    • Emotional awareness phrase generation
    • Time context formatting
    • Confidence and priority calculations
    • CDL prompt formatting for different archetypes
    • Injection decision logic
    • End-to-end workflows with different trajectory scenarios

Created: October 2025
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.prompts.cdl_trajectory_integration import (
    CDLTrajectoryIntegration,
    create_cdl_trajectory_integration,
)


class TestTrajectoryContextRetrieval:
    """Test CDL trajectory context retrieval."""

    @pytest.mark.asyncio
    async def test_get_context_no_trajectory_data(self):
        """Return empty context when no trajectory available."""
        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.return_value = {"has_trajectory": False}

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)
        context = await integration.get_trajectory_context_for_cdl("user_123")

        assert context["has_trajectory"] is False
        assert context["confidence"] == 0.0
        assert context["injection_priority"] == 0.0

    @pytest.mark.asyncio
    async def test_get_context_with_trajectory(self):
        """Successfully retrieve and convert trajectory context."""
        mock_vector = MagicMock()
        mock_vector.time_span = timedelta(minutes=15)

        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.return_value = {
            "has_trajectory": True,
            "trajectory_vector": mock_vector,
            "trend": "RISING_SHARP",
            "summary": "rapidly escalating emotional state over 15 minutes",
            "direction": 0.75,
            "magnitude": 0.6,
            "variance": 0.02,
            "points_count": 8,
        }

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)
        context = await integration.get_trajectory_context_for_cdl("user_123")

        assert context["has_trajectory"] is True
        assert context["trend_type"] == "RISING_SHARP"
        assert "escalating" in context["trajectory_summary"]
        assert context["confidence"] > 0.5
        assert context["injection_priority"] > 0.4

    @pytest.mark.asyncio
    async def test_get_context_lazy_loads_analyzer(self):
        """Lazy-load TrajectoryAnalyzer if not provided."""
        integration = CDLTrajectoryIntegration()

        with patch("src.intelligence.trajectory_analyzer.TrajectoryAnalyzer") as MockAnalyzer:
            mock_instance = AsyncMock()
            mock_instance.retrieve_trajectory_context.return_value = {"has_trajectory": False}
            MockAnalyzer.return_value = mock_instance

            context = await integration.get_trajectory_context_for_cdl("user_123")

            assert context["has_trajectory"] is False

    @pytest.mark.asyncio
    async def test_get_context_error_handling(self):
        """Gracefully handle errors during context retrieval."""
        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.side_effect = RuntimeError("Qdrant error")

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)
        
        # Should handle error gracefully without raising
        try:
            context = await integration.get_trajectory_context_for_cdl("user_123")
            assert context["has_trajectory"] is False
            assert "error" in context
        except RuntimeError:
            pytest.fail("Error handling failed - should not raise RuntimeError")


class TestEmotionalAwarenessGeneration:
    """Test character-aware emotional guidance phrase generation."""

    def test_awareness_rising_sharp(self):
        """Generate appropriate phrase for sharp rise."""
        integration = CDLTrajectoryIntegration()

        awareness = integration._generate_emotional_awareness(
            trend_type="RISING_SHARP", magnitude=0.7, variance=0.05, _direction=0.8
        )

        assert "intense" in awareness or "dramatically" in awareness
        assert "rising" in awareness.lower() or "increasing" in awareness.lower()

    def test_awareness_falling_steady(self):
        """Generate appropriate phrase for steady fall."""
        integration = CDLTrajectoryIntegration()

        awareness = integration._generate_emotional_awareness(
            trend_type="FALLING_STEADY", magnitude=0.5, variance=0.03, _direction=-0.5
        )

        assert "calm" in awareness.lower() or "mellow" in awareness.lower()
        assert "gradually" in awareness.lower() or "slowly" in awareness.lower()

    def test_awareness_volatile(self):
        """Generate appropriate phrase for volatile emotions."""
        integration = CDLTrajectoryIntegration()

        awareness = integration._generate_emotional_awareness(
            trend_type="VOLATILE", magnitude=0.4, variance=0.25, _direction=0.1
        )

        assert "fluctuat" in awareness.lower() or "rollercoaster" in awareness.lower()
        assert "unpredictable" in awareness.lower()

    def test_awareness_stable_low(self):
        """Generate appropriate phrase for stable low mood."""
        integration = CDLTrajectoryIntegration()

        awareness = integration._generate_emotional_awareness(
            trend_type="STABLE_LOW", magnitude=0.05, variance=0.02, _direction=0.0
        )

        assert "subdued" in awareness.lower() or "low" in awareness.lower()
        assert "consistently" in awareness.lower()

    def test_awareness_intensity_modifier(self):
        """Intensity modifier changes with magnitude."""
        integration = CDLTrajectoryIntegration()

        high_mag = integration._generate_emotional_awareness(
            trend_type="RISING_SHARP", magnitude=0.8, variance=0.05, _direction=0.8
        )
        assert "dramatically" in high_mag.lower() or "quite" in high_mag.lower()

        low_mag = integration._generate_emotional_awareness(
            trend_type="RISING_SHARP", magnitude=0.15, variance=0.05, _direction=0.3
        )
        assert "somewhat" in low_mag.lower()


class TestTimeContextFormatting:
    """Test time span to natural language conversion."""

    def test_format_few_minutes(self):
        """Format short time spans (< 10 min)."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(minutes=5))

        assert "few minutes" in time_context.lower()

    def test_format_minutes(self):
        """Format minutes (10-60)."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(minutes=35))

        assert "35 minutes" in time_context

    def test_format_hour(self):
        """Format single hour."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(hours=1))

        assert "hour" in time_context.lower()
        assert "past" in time_context.lower() or "last" in time_context.lower()

    def test_format_hours(self):
        """Format multiple hours."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(hours=3))

        assert "3 hours" in time_context

    def test_format_day(self):
        """Format single day."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(hours=24))

        assert "day" in time_context.lower()

    def test_format_days(self):
        """Format multiple days."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(timedelta(days=5))

        assert "5 days" in time_context

    def test_format_none_time_span(self):
        """Return empty string for None time span."""
        integration = CDLTrajectoryIntegration()

        time_context = integration._format_time_context(None)

        assert time_context == ""


class TestConfidenceCalculation:
    """Test trajectory confidence score calculation."""

    def test_confidence_insufficient_data(self):
        """Low confidence with < 2 data points."""
        integration = CDLTrajectoryIntegration()

        confidence = integration._calculate_trajectory_confidence(
            points_count=1, variance=0.1, magnitude=0.3
        )

        assert confidence < 0.2

    def test_confidence_limited_data(self):
        """Moderate confidence with 2-3 points."""
        integration = CDLTrajectoryIntegration()

        confidence = integration._calculate_trajectory_confidence(
            points_count=2, variance=0.1, magnitude=0.3
        )

        assert 0.3 < confidence < 0.5

    def test_confidence_good_data(self):
        """High confidence with 8+ stable points."""
        integration = CDLTrajectoryIntegration()

        confidence = integration._calculate_trajectory_confidence(
            points_count=10, variance=0.05, magnitude=0.4
        )

        assert confidence > 0.8

    def test_confidence_high_variance_penalty(self):
        """High variance reduces confidence."""
        integration = CDLTrajectoryIntegration()

        volatile = integration._calculate_trajectory_confidence(
            points_count=8, variance=0.25, magnitude=0.4
        )
        stable = integration._calculate_trajectory_confidence(
            points_count=8, variance=0.05, magnitude=0.4
        )

        assert volatile < stable

    def test_confidence_extreme_magnitude_penalty(self):
        """Extreme magnitudes reduce confidence."""
        integration = CDLTrajectoryIntegration()

        moderate = integration._calculate_trajectory_confidence(
            points_count=8, variance=0.05, magnitude=0.5
        )
        extreme = integration._calculate_trajectory_confidence(
            points_count=8, variance=0.05, magnitude=0.95
        )

        assert extreme < moderate


class TestInjectionPriorityCalculation:
    """Test CDL prompt injection priority calculation."""

    def test_priority_stable_low(self):
        """Stable patterns have low priority."""
        integration = CDLTrajectoryIntegration()

        priority = integration._calculate_injection_priority(
            magnitude=0.05, trend_type="STABLE_NEUTRAL", confidence=0.8
        )

        assert priority < 0.3

    def test_priority_rising_sharp(self):
        """Sharp rises have high priority."""
        integration = CDLTrajectoryIntegration()

        priority = integration._calculate_injection_priority(
            magnitude=0.7, trend_type="RISING_SHARP", confidence=0.8
        )

        assert priority > 0.6

    def test_priority_volatile(self):
        """Volatile patterns have moderate-high priority."""
        integration = CDLTrajectoryIntegration()

        priority = integration._calculate_injection_priority(
            magnitude=0.6, trend_type="VOLATILE", confidence=0.7
        )

        assert priority > 0.5

    def test_priority_confidence_multiplier(self):
        """Low confidence reduces priority."""
        integration = CDLTrajectoryIntegration()

        high_conf = integration._calculate_injection_priority(
            magnitude=0.7, trend_type="RISING_SHARP", confidence=0.8
        )
        low_conf = integration._calculate_injection_priority(
            magnitude=0.7, trend_type="RISING_SHARP", confidence=0.3
        )

        assert low_conf < high_conf


class TestCDLPromptFormatting:
    """Test trajectory formatting for CDL prompt injection."""

    def test_format_no_trajectory(self):
        """Return empty string when no trajectory."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {"has_trajectory": False}
        prompt_block = integration.format_for_cdl_prompt(trajectory_context)

        assert prompt_block == ""

    def test_format_real_world_archetype(self):
        """Format for real-world character archetype."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "trajectory_summary": "rapidly escalating over 15 minutes",
            "emotional_awareness": "getting increasingly intense",
            "time_context": "over the last 15 minutes",
        }
        prompt_block = integration.format_for_cdl_prompt(
            trajectory_context, character_archetype="real-world"
        )

        assert "[Context Note:" in prompt_block
        assert "increasingly intense" in prompt_block

    def test_format_fantasy_archetype(self):
        """Format for fantasy character archetype."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "trajectory_summary": "mystical emotional undulation",
            "emotional_awareness": "on a mystical journey",
            "time_context": "over the past hour",
        }
        prompt_block = integration.format_for_cdl_prompt(
            trajectory_context, character_archetype="fantasy"
        )

        assert "[Emotional Context:" in prompt_block
        assert "mystical" in prompt_block

    def test_format_narrative_ai_archetype(self):
        """Format for narrative AI character archetype."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "trajectory_summary": "emotional state trending upward",
            "emotional_awareness": "experiencing escalation",
            "time_context": "over 2 hours",
        }
        prompt_block = integration.format_for_cdl_prompt(
            trajectory_context, character_archetype="narrative_ai"
        )

        assert "[Character Context:" in prompt_block
        assert "emotional state" in prompt_block

    def test_format_without_time_reference(self):
        """Exclude time context when requested."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "trajectory_summary": "rapidly escalating",
            "emotional_awareness": "intense",
            "time_context": "over 15 minutes",
        }
        prompt_block = integration.format_for_cdl_prompt(
            trajectory_context, include_time_reference=False
        )

        assert "15 minutes" not in prompt_block


class TestInjectionDecision:
    """Test CDL prompt injection decision logic."""

    def test_should_inject_high_priority(self):
        """Inject when priority and confidence are high."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.75,
            "confidence": 0.8,
            "trajectory_metadata": {"points_count": 8},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 1500)

        assert should_inject is True

    def test_should_not_inject_low_priority(self):
        """Skip injection when priority below threshold."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.2,
            "confidence": 0.8,
            "trajectory_metadata": {"points_count": 8},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 1500)

        assert should_inject is False

    def test_should_not_inject_low_confidence(self):
        """Skip injection when confidence below threshold."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.75,
            "confidence": 0.3,
            "trajectory_metadata": {"points_count": 8},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 1500)

        assert should_inject is False

    def test_should_not_inject_insufficient_data(self):
        """Skip injection when data points too low."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.75,
            "confidence": 0.8,
            "trajectory_metadata": {"points_count": 1},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 1500)

        assert should_inject is False

    def test_should_not_inject_prompt_size_exceeded(self):
        """Skip injection when prompt nearly full and priority not critical."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.5,  # Medium priority
            "confidence": 0.8,
            "trajectory_metadata": {"points_count": 8},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 2850)

        assert should_inject is False

    def test_should_inject_critical_priority_despite_size(self):
        """Inject even when prompt full if priority is critical."""
        integration = CDLTrajectoryIntegration()

        trajectory_context = {
            "has_trajectory": True,
            "injection_priority": 0.8,  # Critical priority
            "confidence": 0.8,
            "trajectory_metadata": {"points_count": 8},
        }
        should_inject = integration.should_inject_trajectory_into_prompt(trajectory_context, 2850)

        assert should_inject is True


class TestEndToEndWorkflows:
    """Test complete CDL trajectory integration workflows."""

    @pytest.mark.asyncio
    async def test_workflow_frustrated_user(self):
        """Complete workflow for frustrated user becoming more frustrated."""
        mock_vector = MagicMock()
        mock_vector.time_span = timedelta(minutes=20)

        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.return_value = {
            "has_trajectory": True,
            "trajectory_vector": mock_vector,
            "trend": "RISING_SHARP",
            "summary": "emotional intensity escalating rapidly",
            "direction": 0.85,
            "magnitude": 0.75,
            "variance": 0.08,
            "points_count": 10,
        }

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)

        # Get context
        context = await integration.get_trajectory_context_for_cdl("frustrated_user")

        assert context["has_trajectory"] is True
        assert context["injection_priority"] > 0.7
        assert context["confidence"] > 0.7

        # Format for prompt
        prompt_block = integration.format_for_cdl_prompt(context)

        assert "[Context Note:" in prompt_block
        assert len(prompt_block) > 0

        # Decide on injection
        should_inject = integration.should_inject_trajectory_into_prompt(context, 1800)

        assert should_inject is True

    @pytest.mark.asyncio
    async def test_workflow_calming_user(self):
        """Complete workflow for user becoming calm."""
        mock_vector = MagicMock()
        mock_vector.time_span = timedelta(hours=1)

        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.return_value = {
            "has_trajectory": True,
            "trajectory_vector": mock_vector,
            "trend": "FALLING_STEADY",
            "summary": "emotional state gradually decreasing",
            "direction": -0.45,
            "magnitude": 0.55,
            "variance": 0.06,
            "points_count": 12,
        }

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)

        context = await integration.get_trajectory_context_for_cdl("calm_user")

        assert context["trend_type"] == "FALLING_STEADY"
        assert "calm" in context["emotional_awareness"].lower()
        assert "hour" in context["time_context"].lower()

    @pytest.mark.asyncio
    async def test_workflow_volatile_user_low_confidence(self):
        """Complete workflow for volatile user with limited data."""
        mock_vector = MagicMock()
        mock_vector.time_span = timedelta(minutes=8)

        mock_analyzer = AsyncMock()
        mock_analyzer.retrieve_trajectory_context.return_value = {
            "has_trajectory": True,
            "trajectory_vector": mock_vector,
            "trend": "VOLATILE",
            "summary": "emotional fluctuations detected",
            "direction": 0.1,
            "magnitude": 0.3,
            "variance": 0.22,
            "points_count": 2,
        }

        integration = CDLTrajectoryIntegration(trajectory_analyzer=mock_analyzer)

        context = await integration.get_trajectory_context_for_cdl("volatile_user")

        assert context["trend_type"] == "VOLATILE"
        assert context["confidence"] < 0.5  # Low data quality
        assert context["injection_priority"] < 0.4

        # Should not inject due to low confidence and data
        should_inject = integration.should_inject_trajectory_into_prompt(context, 2000)

        assert should_inject is False


class TestFactoryFunction:
    """Test factory function for creating integration instances."""

    @pytest.mark.asyncio
    async def test_factory_creates_instance(self):
        """Factory function creates CDLTrajectoryIntegration."""
        integration = await create_cdl_trajectory_integration()

        assert isinstance(integration, CDLTrajectoryIntegration)

    @pytest.mark.asyncio
    async def test_factory_injects_dependencies(self):
        """Factory accepts and injects memory manager."""
        mock_memory = MagicMock()
        mock_analyzer = MagicMock()

        integration = await create_cdl_trajectory_integration(
            vector_memory_manager=mock_memory, trajectory_analyzer=mock_analyzer
        )

        assert integration.memory_manager is mock_memory
        assert integration.trajectory_analyzer is mock_analyzer
