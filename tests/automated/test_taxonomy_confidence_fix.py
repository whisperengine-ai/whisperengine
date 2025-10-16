"""
Test suite for taxonomy confidence fix.

Tests the _fallback_to_taxonomy() method which now uses actual RoBERTa confidence
instead of intensity, with variance-based adjustment.

Priority 4 Enhancement: Taxonomy confidence fix
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.intelligence.database_emoji_selector import DatabaseEmojiSelector


@pytest.fixture
def emoji_selector():
    """Create DatabaseEmojiSelector instance with mocked dependencies."""
    mock_db_pool = MagicMock()
    mock_db_pool.fetchrow = AsyncMock(return_value=None)
    mock_db_pool.fetch = AsyncMock(return_value=[])
    
    # Mock taxonomy
    mock_taxonomy = MagicMock()
    mock_taxonomy.standardize_emotion_label = MagicMock(side_effect=lambda x: x)
    mock_taxonomy.roberta_to_emoji_choice = MagicMock(return_value="😊")
    
    selector = DatabaseEmojiSelector(db_pool=mock_db_pool)
    selector.taxonomy = mock_taxonomy
    
    return selector


# ============================================================================
# BASIC CONFIDENCE USAGE TESTS
# ============================================================================

def test_uses_roberta_confidence_not_intensity(emoji_selector):
    """Should use roberta_confidence field, not intensity field."""
    bot_emotion_data = {
        "intensity": 0.9,  # High intensity
        "roberta_confidence": 0.4,  # Low confidence
        "emotional_variance": 0.5  # Normal variance
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    # Should call taxonomy with confidence=0.4, NOT 0.9
    emoji_selector.taxonomy.roberta_to_emoji_choice.assert_called_once()
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    
    assert call_args[1]['confidence'] == 0.4  # Uses confidence, not intensity
    assert call_args[1]['roberta_emotion'] == "joy"
    assert call_args[1]['character'] == "elena"


def test_default_confidence_when_missing(emoji_selector):
    """Should default to 0.5 confidence when field is missing."""
    bot_emotion_data = {
        "intensity": 0.8,
        # No roberta_confidence field
        "emotional_variance": 0.5
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    assert call_args[1]['confidence'] == 0.5  # Default value


# ============================================================================
# VARIANCE-BASED CONFIDENCE ADJUSTMENT TESTS
# ============================================================================

def test_low_variance_boosts_confidence(emoji_selector):
    """Low variance (<0.3) should boost confidence by 10%."""
    bot_emotion_data = {
        "roberta_confidence": 0.7,
        "emotional_variance": 0.2,  # Low variance (stable emotion)
        "intensity": 0.8
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.7 * 1.1 = 0.77
    assert call_args[1]['confidence'] == pytest.approx(0.77, abs=0.01)


def test_low_variance_caps_at_one(emoji_selector):
    """Low variance boost should not exceed 1.0."""
    bot_emotion_data = {
        "roberta_confidence": 0.95,  # Very high confidence
        "emotional_variance": 0.1,  # Very low variance
        "intensity": 0.9
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.95 * 1.1 = 1.045, but capped at 1.0
    assert call_args[1]['confidence'] == 1.0


def test_high_variance_reduces_confidence(emoji_selector):
    """High variance (>0.7) should reduce confidence by 10%."""
    bot_emotion_data = {
        "roberta_confidence": 0.8,
        "emotional_variance": 0.85,  # High variance (unstable emotion)
        "intensity": 0.7
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="sadness",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.8 * 0.9 = 0.72
    assert call_args[1]['confidence'] == pytest.approx(0.72, abs=0.01)


def test_normal_variance_unchanged(emoji_selector):
    """Normal variance (0.3-0.7) should not adjust confidence."""
    bot_emotion_data = {
        "roberta_confidence": 0.65,
        "emotional_variance": 0.5,  # Normal variance
        "intensity": 0.75
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="contentment",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    assert call_args[1]['confidence'] == 0.65  # Unchanged


def test_variance_boundary_low(emoji_selector):
    """Variance at 0.3 boundary should NOT boost (must be < 0.3)."""
    bot_emotion_data = {
        "roberta_confidence": 0.7,
        "emotional_variance": 0.3,  # Exactly at boundary
        "intensity": 0.8
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    assert call_args[1]['confidence'] == 0.7  # Not boosted


def test_variance_boundary_high(emoji_selector):
    """Variance at 0.7 boundary should NOT reduce (must be > 0.7)."""
    bot_emotion_data = {
        "roberta_confidence": 0.8,
        "emotional_variance": 0.7,  # Exactly at boundary
        "intensity": 0.75
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="excitement",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    assert call_args[1]['confidence'] == 0.8  # Not reduced


def test_default_variance_when_missing(emoji_selector):
    """Should default to 0.5 variance when field is missing (no adjustment)."""
    bot_emotion_data = {
        "roberta_confidence": 0.75,
        # No emotional_variance field
        "intensity": 0.8
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    assert call_args[1]['confidence'] == 0.75  # No adjustment (default 0.5 variance)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_stable_high_confidence_emotion(emoji_selector):
    """Stable emotion with high confidence should get boosted."""
    bot_emotion_data = {
        "roberta_confidence": 0.85,
        "emotional_variance": 0.15,  # Very stable
        "intensity": 0.9
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="joy",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.85 * 1.1 = 0.935
    assert call_args[1]['confidence'] == pytest.approx(0.935, abs=0.01)


def test_unstable_low_confidence_emotion(emoji_selector):
    """Unstable emotion with low confidence should get reduced further."""
    bot_emotion_data = {
        "roberta_confidence": 0.45,
        "emotional_variance": 0.8,  # Very unstable
        "intensity": 0.6
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="confusion",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.45 * 0.9 = 0.405
    assert call_args[1]['confidence'] == pytest.approx(0.405, abs=0.01)


def test_returns_emoji_when_taxonomy_succeeds(emoji_selector):
    """Should return emoji list when taxonomy returns an emoji."""
    emoji_selector.taxonomy.roberta_to_emoji_choice.return_value = "🎉"
    
    bot_emotion_data = {
        "roberta_confidence": 0.7,
        "emotional_variance": 0.4,
        "intensity": 0.8
    }
    
    result = emoji_selector._fallback_to_taxonomy(
        emotion="excitement",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    assert result == ["🎉"]


def test_returns_empty_when_taxonomy_fails(emoji_selector):
    """Should return empty list when taxonomy returns None."""
    emoji_selector.taxonomy.roberta_to_emoji_choice.return_value = None
    
    bot_emotion_data = {
        "roberta_confidence": 0.6,
        "emotional_variance": 0.5,
        "intensity": 0.7
    }
    
    result = emoji_selector._fallback_to_taxonomy(
        emotion="unknown_emotion",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    assert result == []


def test_emotion_standardization_called(emoji_selector):
    """Should call standardize_emotion_label on the emotion."""
    bot_emotion_data = {
        "roberta_confidence": 0.7,
        "emotional_variance": 0.5,
        "intensity": 0.8
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="HAPPINESS",  # Non-standard label
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    emoji_selector.taxonomy.standardize_emotion_label.assert_called_once_with("HAPPINESS")


# ============================================================================
# EXTREME VALUE TESTS
# ============================================================================

def test_zero_confidence_zero_variance(emoji_selector):
    """Should handle zero confidence with zero variance."""
    bot_emotion_data = {
        "roberta_confidence": 0.0,
        "emotional_variance": 0.0,  # Extremely stable
        "intensity": 0.5
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="neutral",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 0.0 * 1.1 = 0.0
    assert call_args[1]['confidence'] == 0.0


def test_max_confidence_max_variance(emoji_selector):
    """Should handle max confidence with max variance."""
    bot_emotion_data = {
        "roberta_confidence": 1.0,
        "emotional_variance": 1.0,  # Extremely unstable
        "intensity": 0.9
    }
    
    _ = emoji_selector._fallback_to_taxonomy(
        emotion="chaos",
        character_name="elena",
        bot_emotion_data=bot_emotion_data
    )
    
    call_args = emoji_selector.taxonomy.roberta_to_emoji_choice.call_args
    # 1.0 * 0.9 = 0.9
    assert call_args[1]['confidence'] == pytest.approx(0.9, abs=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
