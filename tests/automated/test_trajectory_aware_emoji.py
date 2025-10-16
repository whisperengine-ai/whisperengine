"""
Test suite for trajectory-aware emoji selection.

Tests the _select_trajectory_aware_emoji() method which replaces hard-coded
keyword matching with intelligent trajectory analysis.

Priority 2 Enhancement: Trajectory-aware context selection
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.intelligence.vector_emoji_intelligence import VectorEmojiIntelligence, EmojiResponseContext


@pytest.fixture
def emoji_intelligence():
    """Create VectorEmojiIntelligence instance with mocked dependencies."""
    # Mock memory manager (required for VectorEmojiIntelligence)
    mock_memory_manager = MagicMock()
    mock_memory_manager.retrieve_relevant_memories = AsyncMock(return_value=[])
    
    intelligence = VectorEmojiIntelligence(
        memory_manager=mock_memory_manager
    )
    return intelligence


# ============================================================================
# TRAJECTORY 1: Rising Positive Emotions → Enthusiastic Response
# ============================================================================

def test_rising_joy_high_intensity_enthusiastic(emoji_intelligence):
    """Rising joy with high intensity should return enthusiastic wonder emoji."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.85,
        "confidence": 0.90
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",  # Use "general" character set
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert emoji in ["😍", "🤩", "�", "✨", "�"]  # General's wonder emojis
    assert context == EmojiResponseContext.EMOTIONAL_OVERWHELM


def test_rising_excitement_high_intensity_enthusiastic(emoji_intelligence):
    """Rising excitement should return enthusiastic response."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "excitement",
        "intensity": 0.75,
        "confidence": 0.85
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert context == EmojiResponseContext.EMOTIONAL_OVERWHELM


def test_rising_joy_low_intensity_no_match(emoji_intelligence):
    """Rising joy with low intensity (<0.6) should not match trajectory 1."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.45,  # Below 0.6 threshold
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should fall through (no enthusiastic response for low intensity)
    assert result is None


# ============================================================================
# TRAJECTORY 2: Stable Positive Emotions → Warm Acknowledgment
# ============================================================================

def test_stable_joy_warm_acknowledgment(emoji_intelligence):
    """Stable joy with medium intensity should return warm positive emoji."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "joy",
        "intensity": 0.65,
        "confidence": 0.75
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",  # Use "general" character set
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert emoji in ["😊", "❤️", "👍", "🎉", "😄"]  # General's positive emojis
    assert context == EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT


def test_stable_gratitude_warm_acknowledgment(emoji_intelligence):
    """Stable gratitude should return warm acknowledgment."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "gratitude",
        "intensity": 0.70,
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert context == EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT


def test_stable_joy_low_intensity_no_match(emoji_intelligence):
    """Stable joy with low intensity (<0.5) should not match trajectory 2."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "joy",
        "intensity": 0.35,  # Below 0.5 threshold
        "confidence": 0.75
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


# ============================================================================
# TRAJECTORY 3: Rising Negative Emotions → Avoid Celebratory
# ============================================================================

def test_rising_sadness_falls_through(emoji_intelligence):
    """Rising sadness should fall through (no celebratory response)."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "sadness",
        "intensity": 0.70,
        "confidence": 0.85
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should explicitly return None (avoid celebratory)
    assert result is None


def test_rising_anger_falls_through(emoji_intelligence):
    """Rising anger should fall through (no celebratory response)."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "anger",
        "intensity": 0.65,
        "confidence": 0.75
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


def test_rising_fear_falls_through(emoji_intelligence):
    """Rising fear should fall through (no celebratory response)."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "fear",
        "intensity": 0.80,
        "confidence": 0.90
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


# ============================================================================
# TRAJECTORY 4: Falling Negative Emotions → Supportive Encouragement
# ============================================================================

def test_falling_sadness_supportive(emoji_intelligence):
    """Falling sadness (improving mood) should return supportive emoji."""
    emotional_state = {
        "emotional_trajectory": "falling",
        "current_emotion": "sadness",
        "intensity": 0.50,  # Below 0.7 threshold (improving)
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert emoji == "💙"  # Supportive blue heart
    assert context == EmojiResponseContext.EMOTIONAL_OVERWHELM


def test_falling_fear_supportive(emoji_intelligence):
    """Falling fear (calming down) should return supportive emoji."""
    emotional_state = {
        "emotional_trajectory": "falling",
        "current_emotion": "fear",
        "intensity": 0.45,
        "confidence": 0.75
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert emoji == "💙"
    assert context == EmojiResponseContext.EMOTIONAL_OVERWHELM


def test_falling_sadness_high_intensity_no_match(emoji_intelligence):
    """Falling sadness with high intensity (>0.7) should not match trajectory 4."""
    emotional_state = {
        "emotional_trajectory": "falling",
        "current_emotion": "sadness",
        "intensity": 0.85,  # Above 0.7 threshold (still quite sad)
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should fall through (sadness still too high)
    assert result is None


# ============================================================================
# TRAJECTORY 5: High Excitement/Surprise → Playful Response
# ============================================================================

def test_high_excitement_playful(emoji_intelligence):
    """High excitement with high confidence should return playful emoji."""
    emotional_state = {
        "emotional_trajectory": "stable",  # Trajectory doesn't matter here
        "current_emotion": "excitement",
        "intensity": 0.85,
        "confidence": 0.90
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert emoji in ["😄", "😉", "�", "😆"]  # General's playful emojis
    assert context == EmojiResponseContext.PLAYFUL_INTERACTION


def test_high_surprise_playful(emoji_intelligence):
    """High surprise with high confidence should return playful emoji."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "surprise",
        "intensity": 0.90,
        "confidence": 0.85
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is not None
    emoji, context = result
    assert context == EmojiResponseContext.PLAYFUL_INTERACTION


def test_excitement_low_intensity_no_playful(emoji_intelligence):
    """Excitement with low intensity (<0.7) should not return playful emoji."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "excitement",
        "intensity": 0.55,  # Below 0.7 threshold
        "confidence": 0.85
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should fall through (not excited enough)
    assert result is None


def test_excitement_low_confidence_no_playful(emoji_intelligence):
    """Excitement with low confidence (<0.7) should not return playful emoji."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "excitement",
        "intensity": 0.85,
        "confidence": 0.55  # Below 0.7 threshold
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


# ============================================================================
# CONFIDENCE THRESHOLD TESTS
# ============================================================================

def test_low_confidence_always_falls_through(emoji_intelligence):
    """Low confidence (<0.65) should always fall through regardless of trajectory."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.90,
        "confidence": 0.50  # Below 0.65 threshold
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should fall through due to low confidence
    assert result is None


def test_borderline_confidence_uses_trajectory(emoji_intelligence):
    """Confidence at 0.65 threshold should use trajectory logic."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.80,
        "confidence": 0.65  # Exactly at threshold
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should match trajectory 1 (rising joy)
    assert result is not None
    emoji, context = result
    assert context == EmojiResponseContext.EMOTIONAL_OVERWHELM


# ============================================================================
# USER DISTRESS PROTECTION TESTS
# ============================================================================

def test_user_distress_blocks_all_trajectory_responses(emoji_intelligence):
    """User distress should block all trajectory-based responses."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.90,
        "confidence": 0.95
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=True  # User in distress
    )
    
    # Should skip all trajectory logic due to distress
    assert result is None


def test_user_distress_blocks_playful_responses(emoji_intelligence):
    """User distress should block playful excitement responses."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "excitement",
        "intensity": 0.95,
        "confidence": 0.95
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=True
    )
    
    assert result is None


# ============================================================================
# FALLTHROUGH BEHAVIOR TESTS
# ============================================================================

def test_neutral_emotion_falls_through(emoji_intelligence):
    """Neutral emotion should fall through (no trajectory match)."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "neutral",
        "intensity": 0.50,
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


def test_confusion_emotion_falls_through(emoji_intelligence):
    """Confusion emotion should fall through (not in any trajectory category)."""
    emotional_state = {
        "emotional_trajectory": "stable",
        "current_emotion": "confusion",
        "intensity": 0.70,
        "confidence": 0.75
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    assert result is None


def test_missing_trajectory_falls_through(emoji_intelligence):
    """Missing trajectory field should default to 'stable' and process normally."""
    emotional_state = {
        # No emotional_trajectory field
        "current_emotion": "joy",
        "intensity": 0.70,
        "confidence": 0.80
    }
    
    result = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Should match stable joy trajectory (trajectory 2)
    assert result is not None
    emoji, context = result
    assert context == EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT


# ============================================================================
# CHARACTER-SPECIFIC EMOJI TESTS
# ============================================================================

def test_different_characters_use_different_emoji_sets(emoji_intelligence):
    """Different characters should return different emojis from their sets."""
    emotional_state = {
        "emotional_trajectory": "rising",
        "current_emotion": "joy",
        "intensity": 0.85,
        "confidence": 0.90
    }
    
    # Test Elena
    result_elena = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="general",
        user_in_distress=False
    )
    
    # Test Marcus
    result_marcus = emoji_intelligence._select_trajectory_aware_emoji(
        emotional_state=emotional_state,
        bot_character="marcus",
        user_in_distress=False
    )
    
    assert result_elena is not None
    assert result_marcus is not None
    
    # Both should return wonder context, but possibly different emojis
    _, context_elena = result_elena
    _, context_marcus = result_marcus
    
    assert context_elena == EmojiResponseContext.EMOTIONAL_OVERWHELM
    assert context_marcus == EmojiResponseContext.EMOTIONAL_OVERWHELM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
