"""
Tests for TrajectoryAnalyzer - emotional trajectory context building.

Tests cover:
- extract_trajectory() - Memory retrieval and ordering
- compute_trajectory_vector() - Vector quantification and classification
- generate_trajectory_summary() - Natural language generation
- retrieve_trajectory_context() - End-to-end integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List
from unittest.mock import Mock, AsyncMock, MagicMock

from src.intelligence.trajectory_analyzer import (
    TrajectoryAnalyzer,
    TrajectoryPoint,
    TrajectoryVector,
    TrajectoryTrend,
)


class TestTrajectoryExtraction:
    """Tests for extract_trajectory() method."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TrajectoryAnalyzer(memory_manager=Mock())
    
    @pytest.mark.asyncio
    async def test_extract_trajectory_empty_memory(self):
        """No emotional memories returns empty list."""
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=[]
        )
        
        trajectory = await self.analyzer.extract_trajectory("user_123")
        
        assert trajectory == []
        assert len(trajectory) == 0
    
    @pytest.mark.asyncio
    async def test_extract_trajectory_single_point(self):
        """Single emotional state extracted correctly."""
        now = datetime.now()
        memories = [{
            'payload': {
                'timestamp': now.isoformat(),
                'emotional_intensity_ema': 0.7,
                'emotional_intensity_raw': 0.75,
                'emotion_type': 'joy'
            }
        }]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        trajectory = await self.analyzer.extract_trajectory("user_123")
        
        assert len(trajectory) == 1
        assert trajectory[0].ema_value == 0.7
        assert trajectory[0].raw_value == 0.75
        assert trajectory[0].emotion_type == 'joy'
    
    @pytest.mark.asyncio
    async def test_extract_trajectory_multiple_points_ordered(self):
        """Multiple points extracted and sorted by timestamp."""
        t1 = datetime(2025, 1, 1, 10, 0)
        t2 = datetime(2025, 1, 1, 10, 5)
        t3 = datetime(2025, 1, 1, 10, 10)
        
        # Return in reverse order to test sorting
        memories = [
            {'payload': {'timestamp': t3.isoformat(), 'emotional_intensity_ema': 0.8}},
            {'payload': {'timestamp': t1.isoformat(), 'emotional_intensity_ema': 0.5}},
            {'payload': {'timestamp': t2.isoformat(), 'emotional_intensity_ema': 0.6}},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        trajectory = await self.analyzer.extract_trajectory("user_123")
        
        assert len(trajectory) == 3
        assert trajectory[0].ema_value == 0.5  # t1 first
        assert trajectory[1].ema_value == 0.6  # t2 middle
        assert trajectory[2].ema_value == 0.8  # t3 last
    
    @pytest.mark.asyncio
    async def test_extract_trajectory_fallback_to_raw_intensity(self):
        """Falls back to raw intensity if EMA not available."""
        now = datetime.now()
        memories = [{
            'payload': {
                'timestamp': now.isoformat(),
                'emotional_intensity_ema': None,
                'emotional_intensity': 0.65
            }
        }]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        trajectory = await self.analyzer.extract_trajectory("user_123")
        
        assert len(trajectory) == 1
        assert trajectory[0].ema_value == 0.65
    
    @pytest.mark.asyncio
    async def test_extract_trajectory_skip_missing_data(self):
        """Skips entries with missing timestamps or values."""
        now = datetime.now()
        memories = [
            {'payload': {'timestamp': now.isoformat(), 'emotional_intensity_ema': 0.7}},
            {'payload': {'emotional_intensity_ema': 0.6}},  # No timestamp - skip
            {'payload': {'timestamp': now.isoformat()}},    # No intensity - skip
            {'payload': {'timestamp': now.isoformat(), 'emotional_intensity_ema': 0.8}},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        trajectory = await self.analyzer.extract_trajectory("user_123")
        
        assert len(trajectory) == 2
        assert trajectory[0].ema_value == 0.7
        assert trajectory[1].ema_value == 0.8


class TestTrajectoryVectorComputation:
    """Tests for compute_trajectory_vector() method."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TrajectoryAnalyzer(memory_manager=Mock())
    
    def test_trajectory_vector_empty_input(self):
        """Empty trajectory returns unknown trend."""
        vector = self.analyzer.compute_trajectory_vector([])
        
        assert vector.trend == TrajectoryTrend.UNKNOWN
        assert vector.direction == 0.0
        assert vector.magnitude == 0.0
        assert vector.points_count == 0
    
    def test_trajectory_vector_single_point(self):
        """Single point has zero direction/magnitude."""
        now = datetime.now()
        points = [TrajectoryPoint(timestamp=now, ema_value=0.5)]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert vector.direction == 0.0
        assert vector.magnitude == 0.0
        assert vector.mean_intensity == 0.5
        assert vector.points_count == 1
    
    def test_trajectory_vector_stable_trend(self):
        """Consistent values classified as stable."""
        now = datetime.now()
        points = [
            TrajectoryPoint(timestamp=now, ema_value=0.5),
            TrajectoryPoint(timestamp=now + timedelta(minutes=1), ema_value=0.5),
            TrajectoryPoint(timestamp=now + timedelta(minutes=2), ema_value=0.5),
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert abs(vector.direction) < 0.1  # Nearly zero slope
        assert abs(vector.magnitude) < 0.01  # No change
        assert vector.variance < 0.01  # Low variance
        assert vector.trend == TrajectoryTrend.STABLE_NEUTRAL
    
    def test_trajectory_vector_rising_steady(self):
        """Gradual increase classified as rising steady."""
        now = datetime.now()
        points = [
            TrajectoryPoint(timestamp=now, ema_value=0.0),
            TrajectoryPoint(timestamp=now + timedelta(minutes=1), ema_value=0.2),
            TrajectoryPoint(timestamp=now + timedelta(minutes=2), ema_value=0.4),
            TrajectoryPoint(timestamp=now + timedelta(minutes=3), ema_value=0.6),
            TrajectoryPoint(timestamp=now + timedelta(minutes=4), ema_value=0.8),
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert vector.direction > 0.2  # Positive slope
        assert vector.magnitude > 0.7  # Large change
        # This is classified as RISING_SHARP because magnitude > 0.5
        assert vector.trend in [TrajectoryTrend.RISING_STEADY, TrajectoryTrend.RISING_SHARP]
    
    def test_trajectory_vector_falling_steady(self):
        """Gradual decrease classified as falling steady."""
        now = datetime.now()
        points = [
            TrajectoryPoint(timestamp=now, ema_value=0.8),
            TrajectoryPoint(timestamp=now + timedelta(minutes=1), ema_value=0.6),
            TrajectoryPoint(timestamp=now + timedelta(minutes=2), ema_value=0.4),
            TrajectoryPoint(timestamp=now + timedelta(minutes=3), ema_value=0.2),
            TrajectoryPoint(timestamp=now + timedelta(minutes=4), ema_value=0.0),
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert vector.direction < -0.2  # Negative slope
        assert vector.magnitude > 0.7  # Large change
        # This is classified as FALLING_SHARP because magnitude > 0.5
        assert vector.trend in [TrajectoryTrend.FALLING_STEADY, TrajectoryTrend.FALLING_SHARP]
    
    def test_trajectory_vector_rising_sharp(self):
        """Rapid increase classified as rising sharp."""
        now = datetime.now()
        points = [
            TrajectoryPoint(timestamp=now, ema_value=0.2),
            TrajectoryPoint(timestamp=now + timedelta(seconds=30), ema_value=0.9),
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert vector.direction > 0.3  # Strong positive slope
        assert vector.magnitude > 0.6  # Large change
        assert vector.trend == TrajectoryTrend.RISING_SHARP
    
    def test_trajectory_vector_volatile_trend(self):
        """High variance classified as volatile."""
        now = datetime.now()
        points = [
            TrajectoryPoint(timestamp=now, ema_value=0.1),
            TrajectoryPoint(timestamp=now + timedelta(minutes=1), ema_value=0.9),
            TrajectoryPoint(timestamp=now + timedelta(minutes=2), ema_value=0.05),
            TrajectoryPoint(timestamp=now + timedelta(minutes=3), ema_value=0.95),
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert vector.variance > 0.18  # High variance
        assert vector.trend == TrajectoryTrend.VOLATILE
    
    def test_trajectory_vector_statistics(self):
        """Vector statistics calculated correctly."""
        now = datetime.now()
        values = [0.2, 0.4, 0.6, 0.8]
        points = [
            TrajectoryPoint(timestamp=now + timedelta(minutes=i), ema_value=v)
            for i, v in enumerate(values)
        ]
        
        vector = self.analyzer.compute_trajectory_vector(points)
        
        assert abs(vector.mean_intensity - 0.5) < 0.01  # Mean of [0.2, 0.4, 0.6, 0.8]
        assert vector.variance > 0.04  # Variance > 0
        assert vector.points_count == 4
        assert (vector.time_span.total_seconds() / 60) == 3  # 3 minutes span


class TestTrajectorySummaryGeneration:
    """Tests for generate_trajectory_summary() method."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TrajectoryAnalyzer(memory_manager=Mock())
    
    def test_summary_insufficient_data(self):
        """Empty summary for insufficient data."""
        vector = TrajectoryVector(
            trend=TrajectoryTrend.UNKNOWN,
            direction=0.0,
            magnitude=0.0,
            acceleration=0.0,
            mean_intensity=0.5,
            variance=0.01,
            points_count=1,
            time_span=timedelta(minutes=1)
        )
        
        summary = self.analyzer.generate_trajectory_summary(vector)
        
        assert summary == ""
    
    def test_summary_rising_sharp(self):
        """Summary for rapidly rising emotional state."""
        vector = TrajectoryVector(
            trend=TrajectoryTrend.RISING_SHARP,
            direction=0.8,
            magnitude=0.6,
            acceleration=0.1,
            mean_intensity=0.75,
            variance=0.01,
            points_count=5,
            time_span=timedelta(minutes=10)
        )
        
        summary = self.analyzer.generate_trajectory_summary(vector)
        
        assert "rapidly escalating" in summary
        assert "emotional state" in summary
        assert "10 minutes" in summary
    
    def test_summary_falling_steady(self):
        """Summary for gradually falling mood."""
        vector = TrajectoryVector(
            trend=TrajectoryTrend.FALLING_STEADY,
            direction=-0.4,
            magnitude=0.2,
            acceleration=0.05,
            mean_intensity=0.45,
            variance=0.01,
            points_count=5,
            time_span=timedelta(hours=2)
        )
        
        summary = self.analyzer.generate_trajectory_summary(vector)
        
        assert "gradually decreasing" in summary
        assert "mood" in summary
        assert "2 hours" in summary or "2 hour" in summary
    
    def test_summary_stable_low(self):
        """Summary for consistently low emotional state."""
        vector = TrajectoryVector(
            trend=TrajectoryTrend.STABLE_LOW,
            direction=0.0,
            magnitude=0.01,
            acceleration=0.0,
            mean_intensity=0.2,
            variance=0.001,
            points_count=5,
            time_span=timedelta(hours=1)
        )
        
        summary = self.analyzer.generate_trajectory_summary(vector)
        
        assert "consistently low" in summary
        assert "disposition" in summary
    
    def test_summary_volatile(self):
        """Summary for fluctuating emotional state."""
        vector = TrajectoryVector(
            trend=TrajectoryTrend.VOLATILE,
            direction=0.1,
            magnitude=0.3,
            acceleration=0.05,
            mean_intensity=0.5,
            variance=0.25,
            points_count=8,  # More points to avoid "limited data"
            time_span=timedelta(minutes=30)
        )
        
        summary = self.analyzer.generate_trajectory_summary(vector)
        
        assert "fluctuating" in summary
        assert "limited data" not in summary  # 8 points doesn't get limited data note
    
    def test_summary_time_descriptions(self):
        """Time descriptions vary by duration."""
        vector_short = TrajectoryVector(
            trend=TrajectoryTrend.RISING_STEADY,
            direction=0.5,
            magnitude=0.2,
            acceleration=0.02,
            mean_intensity=0.5,
            variance=0.02,
            points_count=3,
            time_span=timedelta(minutes=5)
        )
        
        vector_long = TrajectoryVector(
            trend=TrajectoryTrend.RISING_STEADY,
            direction=0.5,
            magnitude=0.2,
            acceleration=0.02,
            mean_intensity=0.5,
            variance=0.02,
            points_count=10,
            time_span=timedelta(days=2)
        )
        
        summary_short = self.analyzer.generate_trajectory_summary(vector_short)
        summary_long = self.analyzer.generate_trajectory_summary(vector_long)
        
        assert "few minutes" in summary_short
        assert "2 days" in summary_long


class TestTrajectoryContextRetrieval:
    """Tests for retrieve_trajectory_context() end-to-end method."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TrajectoryAnalyzer(memory_manager=Mock())
    
    @pytest.mark.asyncio
    async def test_retrieve_context_no_trajectory(self):
        """Returns empty context when no trajectory found."""
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=[]
        )
        
        context = await self.analyzer.retrieve_trajectory_context("user_123")
        
        assert context['has_trajectory'] is False
        assert context['summary'] == ''
        assert context['points_count'] == 0
        assert context['trend'] is None
    
    @pytest.mark.asyncio
    async def test_retrieve_context_with_trajectory(self):
        """Returns complete context with trajectory data."""
        now = datetime.now()
        memories = [
            {'payload': {'timestamp': now.isoformat(), 'emotional_intensity_ema': 0.2}},
            {'payload': {'timestamp': (now + timedelta(minutes=5)).isoformat(), 'emotional_intensity_ema': 0.8}},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        context = await self.analyzer.retrieve_trajectory_context("user_123")
        
        assert context['has_trajectory'] is True
        assert context['points_count'] == 2
        assert context['direction'] > 0  # Rising
        assert context['magnitude'] > 0.5  # Significant change
        assert 'escalat' in context['summary'].lower() or 'rising' in context['summary'].lower()
    
    @pytest.mark.asyncio
    async def test_retrieve_context_without_summary(self):
        """Can exclude summary generation."""
        now = datetime.now()
        memories = [
            {'payload': {'timestamp': now.isoformat(), 'emotional_intensity_ema': 0.5}},
            {'payload': {'timestamp': (now + timedelta(minutes=1)).isoformat(), 'emotional_intensity_ema': 0.5}},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        context = await self.analyzer.retrieve_trajectory_context(
            "user_123",
            include_summary=False
        )
        
        assert context['has_trajectory'] is True
        assert context['summary'] == ''  # No summary generated
        assert context['trend'] is not None  # But trend is still computed
    
    @pytest.mark.asyncio
    async def test_retrieve_context_error_handling(self):
        """Gracefully handles errors."""
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            side_effect=Exception("Memory error")
        )
        
        context = await self.analyzer.retrieve_trajectory_context("user_123")
        
        assert context['has_trajectory'] is False
        assert context['summary'] == ''
        assert context['points_count'] == 0


class TestTrajectoryIntegration:
    """Integration tests for complete trajectory analysis workflow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TrajectoryAnalyzer(memory_manager=Mock())
    
    @pytest.mark.asyncio
    async def test_full_workflow_rising_frustrated_user(self):
        """Complete workflow: user becoming increasingly frustrated."""
        now = datetime.now()
        
        # Simulate user becoming frustrated: 0.2 → 0.4 → 0.6 → 0.8
        memories = [
            {'payload': {
                'timestamp': now.isoformat(),
                'emotional_intensity_ema': 0.2,
                'emotion_type': 'calm'
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=5)).isoformat(),
                'emotional_intensity_ema': 0.4,
                'emotion_type': 'concerned'
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=10)).isoformat(),
                'emotional_intensity_ema': 0.6,
                'emotion_type': 'frustrated'
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=15)).isoformat(),
                'emotional_intensity_ema': 0.8,
                'emotion_type': 'angry'
            }},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        context = await self.analyzer.retrieve_trajectory_context("user_123")
        
        # Verify trajectory detected rising trend
        assert context['has_trajectory'] is True
        assert context['points_count'] == 4
        assert context['direction'] > 0.3  # Strong positive slope
        assert context['magnitude'] > 0.5  # Significant change
        
        # Verify summary mentions rising trend
        assert 'rising' in context['summary'].lower() or 'escalat' in context['summary'].lower()
        
        # This context would be injected into the prompt to make the bot aware:
        # "Bot is aware: User has been rapidly escalating emotional state over the last 15 minutes"
    
    @pytest.mark.asyncio
    async def test_full_workflow_calming_user(self):
        """Complete workflow: user becoming progressively calmer."""
        now = datetime.now()
        
        # User calming down: 0.9 → 0.6 → 0.3 → 0.05
        memories = [
            {'payload': {
                'timestamp': now.isoformat(),
                'emotional_intensity_ema': 0.9
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=10)).isoformat(),
                'emotional_intensity_ema': 0.6
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=20)).isoformat(),
                'emotional_intensity_ema': 0.3
            }},
            {'payload': {
                'timestamp': (now + timedelta(minutes=30)).isoformat(),
                'emotional_intensity_ema': 0.05
            }},
        ]
        
        self.analyzer.memory_manager.retrieve_relevant_memories = AsyncMock(
            return_value=memories
        )
        
        context = await self.analyzer.retrieve_trajectory_context("user_123")
        
        assert context['direction'] < -0.3  # Negative slope
        assert 'escalat' in context['summary'].lower() or 'decreasing' in context['summary'].lower() or 'falling' in context['summary'].lower() or 'de-escalat' in context['summary'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
