#!/usr/bin/env python3
"""
Test Character Learning Moment Detector with spaCy Lemmatization Integration

Validates that pattern-based detection using lemmatization works correctly for:
- Growth insights (growth_triggers)
- User observations (observation_triggers)
- Memory surprises (memory_triggers)
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from src.characters.learning.character_learning_moment_detector import (
    CharacterLearningMomentDetector,
    LearningMomentContext,
    LearningMomentType
)


@pytest.fixture
def detector():
    """Create a CharacterLearningMomentDetector instance."""
    return CharacterLearningMomentDetector()


@pytest.fixture
def base_context():
    """Base context for testing."""
    return {
        'user_id': 'test_user_123',
        'character_name': 'elena',
        'conversation_history': [],
        'temporal_data': None,
        'emotional_context': None,
        'episodic_memories': []
    }


class TestLemmatizationPatternMatching:
    """Test lemmatization-based pattern matching."""
    
    def test_lemmatize_method(self, detector):
        """Test basic lemmatization functionality."""
        # Test verb variations
        assert "grow" in detector._lemmatize("I'm growing so much")
        assert "grow" in detector._lemmatize("I've grown a lot")
        assert "grow" in detector._lemmatize("growth is important")
        
        # Test noun/verb variations
        assert "change" in detector._lemmatize("I'm changing")
        assert "change" in detector._lemmatize("That changed me")
        assert "change" in detector._lemmatize("What a change!")
        
        # Test relationship patterns
        assert "fall in love" in detector._lemmatize("I'm falling in love")
        assert "fall in love" in detector._lemmatize("I fell in love")
        assert "fall in love" in detector._lemmatize("I've fallen in love")
    
    def test_matches_trigger_pattern_basic(self, detector):
        """Test basic pattern matching with lemmatization."""
        # Growth triggers
        assert detector._matches_trigger_pattern(
            "I'm growing as a person",
            detector.growth_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "I've grown so much from this",
            detector.growth_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "This experience changed me",
            detector.growth_triggers
        )
    
    def test_matches_trigger_pattern_observations(self, detector):
        """Test observation trigger patterns."""
        # Observation triggers
        assert detector._matches_trigger_pattern(
            "I've noticed that I always do this",
            detector.observation_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "I'm realizing something about myself",
            detector.observation_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "I tend to react this way",
            detector.observation_triggers
        )
    
    def test_matches_trigger_pattern_memory(self, detector):
        """Test memory trigger patterns."""
        # Memory triggers
        assert detector._matches_trigger_pattern(
            "Do you remember when we talked about this?",
            detector.memory_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "I recall you mentioning something",
            detector.memory_triggers
        )
        
        assert detector._matches_trigger_pattern(
            "That reminds me of our conversation",
            detector.memory_triggers
        )
    
    def test_matches_trigger_pattern_no_match(self, detector):
        """Test that non-matching patterns return False."""
        # Should not match growth triggers
        assert not detector._matches_trigger_pattern(
            "The weather is nice today",
            detector.growth_triggers
        )
        
        # Should not match observation triggers
        assert not detector._matches_trigger_pattern(
            "I like pizza",
            detector.observation_triggers
        )
        
        # Should not match memory triggers
        assert not detector._matches_trigger_pattern(
            "What's the capital of France?",
            detector.memory_triggers
        )


class TestGrowthInsightsLemmatization:
    """Test growth insights detection with lemmatization."""
    
    @pytest.mark.asyncio
    async def test_growth_pattern_detection_growing(self, detector, base_context):
        """Test detection when user says 'growing'."""
        context = LearningMomentContext(
            current_message="I'm growing as a person through these conversations",
            **base_context
        )
        
        moments = await detector._detect_growth_insights(context)
        
        # Should detect at least one growth moment via pattern matching
        assert len(moments) > 0
        assert any(m.moment_type == LearningMomentType.GROWTH_INSIGHT for m in moments)
        
        # Check that pattern match was triggered
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_growth_pattern_detection_grown(self, detector, base_context):
        """Test detection when user says 'grown' (past tense)."""
        context = LearningMomentContext(
            current_message="I've really grown from our talks",
            **base_context
        )
        
        moments = await detector._detect_growth_insights(context)
        
        # Lemmatization should normalize "grown" → "grow"
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_growth_pattern_detection_changed(self, detector, base_context):
        """Test detection when user says 'changed'."""
        context = LearningMomentContext(
            current_message="This experience changed me forever",
            **base_context
        )
        
        moments = await detector._detect_growth_insights(context)
        
        # Should detect change pattern
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0


class TestUserObservationsLemmatization:
    """Test user observations detection with lemmatization."""
    
    @pytest.mark.asyncio
    async def test_observation_pattern_noticing(self, detector, base_context):
        """Test detection when user says 'noticing'."""
        context = LearningMomentContext(
            current_message="I'm noticing a pattern in my behavior",
            **base_context
        )
        
        moments = await detector._detect_user_observations(context)
        
        # Should detect observation moment
        assert len(moments) > 0
        assert any(m.moment_type == LearningMomentType.USER_OBSERVATION for m in moments)
        
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_observation_pattern_realized(self, detector, base_context):
        """Test detection when user says 'realized' (past tense)."""
        context = LearningMomentContext(
            current_message="I just realized something about myself",
            **base_context
        )
        
        moments = await detector._detect_user_observations(context)
        
        # Lemmatization should normalize "realized" → "realize"
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_observation_pattern_tend(self, detector, base_context):
        """Test detection when user says 'tend to'."""
        context = LearningMomentContext(
            current_message="I tend to react emotionally in these situations",
            **base_context
        )
        
        moments = await detector._detect_user_observations(context)
        
        # Should detect tendency pattern
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0


class TestMemorySurprisesLemmatization:
    """Test memory surprises detection with lemmatization."""
    
    @pytest.mark.asyncio
    async def test_memory_pattern_remember(self, detector, base_context):
        """Test detection when user asks 'do you remember'."""
        context = LearningMomentContext(
            current_message="Do you remember when we talked about marine biology?",
            **base_context
        )
        
        moments = await detector._detect_memory_surprises(context)
        
        # Should detect memory moment
        assert len(moments) > 0
        assert any(m.moment_type == LearningMomentType.MEMORY_SURPRISE for m in moments)
        
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_memory_pattern_recall(self, detector, base_context):
        """Test detection when user says 'recall'."""
        context = LearningMomentContext(
            current_message="I recall you mentioning something interesting",
            **base_context
        )
        
        moments = await detector._detect_memory_surprises(context)
        
        # Should detect recall pattern
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0
    
    @pytest.mark.asyncio
    async def test_memory_pattern_reminds(self, detector, base_context):
        """Test detection when user says 'reminds me'."""
        context = LearningMomentContext(
            current_message="This reminds me of what we discussed last week",
            **base_context
        )
        
        moments = await detector._detect_memory_surprises(context)
        
        # Should detect reminder pattern
        assert len(moments) > 0
        pattern_moments = [m for m in moments if m.supporting_data.get('trigger') == 'pattern_match']
        assert len(pattern_moments) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_lemmatize_empty_string(self, detector):
        """Test lemmatization with empty string."""
        result = detector._lemmatize("")
        assert result == ""
    
    def test_lemmatize_none(self, detector):
        """Test lemmatization with None input."""
        result = detector._lemmatize(None)
        assert result == ""
    
    def test_matches_trigger_pattern_empty_text(self, detector):
        """Test pattern matching with empty text."""
        result = detector._matches_trigger_pattern("", detector.growth_triggers)
        assert result is False
    
    def test_matches_trigger_pattern_none_text(self, detector):
        """Test pattern matching with None text."""
        result = detector._matches_trigger_pattern(None, detector.growth_triggers)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_no_current_message(self, detector, base_context):
        """Test detection when current_message is None."""
        context = LearningMomentContext(
            current_message=None,
            **base_context
        )
        
        # Should not crash, should return empty list
        growth_moments = await detector._detect_growth_insights(context)
        observation_moments = await detector._detect_user_observations(context)
        memory_moments = await detector._detect_memory_surprises(context)
        
        # Pattern-based detection should be skipped, but other detection may run
        assert isinstance(growth_moments, list)
        assert isinstance(observation_moments, list)
        assert isinstance(memory_moments, list)


if __name__ == "__main__":
    # Run with: python -m pytest tests/automated/test_character_learning_lemmatization.py -v
    pytest.main([__file__, "-v", "--tb=short"])
