"""
Test suite for emotion-aware empathy emoji selection.

Tests the _select_emotion_aware_empathy_emoji() method which replaces hard-coded
"💙" fallbacks with intelligent emotion-specific empathy selection.

Priority 3 Enhancement: Emotion-aware empathy emojis
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.intelligence.vector_emoji_intelligence import VectorEmojiIntelligence


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
# MYSTICAL CHARACTER TESTS
# ============================================================================

def test_mystical_character_uses_prayer_hands(emoji_intelligence):
    """Mystical characters should always use prayer hands for empathy."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.70
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="mystical"
    )
    
    assert result == "🙏"


def test_mystical_character_any_emotion(emoji_intelligence):
    """Mystical characters use prayer hands regardless of emotion type."""
    emotional_state = {
        "current_emotion": "fear",
        "intensity": 0.85
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="mystical"
    )
    
    assert result == "🙏"


# ============================================================================
# SADNESS EMOTION TESTS
# ============================================================================

def test_deep_sadness_crying_face(emoji_intelligence):
    """Deep sadness (>0.7 intensity) should return crying face."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.85
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😢"


def test_moderate_sadness_pensive_face(emoji_intelligence):
    """Moderate sadness (0.5-0.7 intensity) should return pensive face."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.65
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😔"


def test_mild_sadness_blue_heart(emoji_intelligence):
    """Mild sadness (<0.5 intensity) should return blue heart."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.35
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_grief_high_intensity(emoji_intelligence):
    """Grief is treated like sadness - high intensity gets crying face."""
    emotional_state = {
        "current_emotion": "grief",
        "intensity": 0.90
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😢"


def test_melancholy_moderate_intensity(emoji_intelligence):
    """Melancholy is treated like sadness - moderate intensity gets pensive face."""
    emotional_state = {
        "current_emotion": "melancholy",
        "intensity": 0.55
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😔"


# ============================================================================
# FEAR/ANXIETY EMOTION TESTS
# ============================================================================

def test_high_fear_worried_face(emoji_intelligence):
    """High fear (>0.6 intensity) should return worried face."""
    emotional_state = {
        "current_emotion": "fear",
        "intensity": 0.75
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😟"


def test_moderate_fear_blue_heart(emoji_intelligence):
    """Moderate fear (≤0.6 intensity) should return blue heart for reassurance."""
    emotional_state = {
        "current_emotion": "fear",
        "intensity": 0.50
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_high_anxiety_worried_face(emoji_intelligence):
    """High anxiety should return worried face."""
    emotional_state = {
        "current_emotion": "anxiety",
        "intensity": 0.80
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😟"


def test_nervousness_moderate(emoji_intelligence):
    """Nervousness is treated like fear - moderate gets blue heart."""
    emotional_state = {
        "current_emotion": "nervousness",
        "intensity": 0.45
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_worry_high_intensity(emoji_intelligence):
    """High worry should return worried face."""
    emotional_state = {
        "current_emotion": "worry",
        "intensity": 0.70
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😟"


# ============================================================================
# ANGER/FRUSTRATION EMOTION TESTS
# ============================================================================

def test_high_anger_broken_heart(emoji_intelligence):
    """High anger (>0.7 intensity) should return broken heart to acknowledge pain."""
    emotional_state = {
        "current_emotion": "anger",
        "intensity": 0.85
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💔"


def test_moderate_anger_disappointed_face(emoji_intelligence):
    """Moderate anger (≤0.7 intensity) should return disappointed face."""
    emotional_state = {
        "current_emotion": "anger",
        "intensity": 0.60
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😞"


def test_high_frustration_broken_heart(emoji_intelligence):
    """High frustration should return broken heart."""
    emotional_state = {
        "current_emotion": "frustration",
        "intensity": 0.80
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💔"


def test_irritation_moderate(emoji_intelligence):
    """Irritation is treated like anger - moderate gets disappointed face."""
    emotional_state = {
        "current_emotion": "irritation",
        "intensity": 0.55
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😞"


def test_annoyance_low_intensity(emoji_intelligence):
    """Low annoyance should return disappointed face."""
    emotional_state = {
        "current_emotion": "annoyance",
        "intensity": 0.40
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😞"


# ============================================================================
# DISAPPOINTMENT EMOTION TESTS
# ============================================================================

def test_high_disappointment_pleading_face(emoji_intelligence):
    """High disappointment (>0.6 intensity) should return pleading face for vulnerability."""
    emotional_state = {
        "current_emotion": "disappointment",
        "intensity": 0.75
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "🥺"


def test_moderate_disappointment_disappointed_face(emoji_intelligence):
    """Moderate disappointment (≤0.6 intensity) should return disappointed face."""
    emotional_state = {
        "current_emotion": "disappointment",
        "intensity": 0.50
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😞"


def test_high_regret_pleading_face(emoji_intelligence):
    """High regret should return pleading face."""
    emotional_state = {
        "current_emotion": "regret",
        "intensity": 0.80
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "🥺"


def test_shame_high_intensity(emoji_intelligence):
    """High shame should return pleading face for vulnerability."""
    emotional_state = {
        "current_emotion": "shame",
        "intensity": 0.70
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "🥺"


# ============================================================================
# COMPLEX/MIXED EMOTION TESTS
# ============================================================================

def test_confusion_sad_but_relieved(emoji_intelligence):
    """Confusion should return sad but relieved emoji for mixed emotions."""
    emotional_state = {
        "current_emotion": "confusion",
        "intensity": 0.60
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😥"


def test_overwhelm_sad_but_relieved(emoji_intelligence):
    """Overwhelm should return sad but relieved emoji."""
    emotional_state = {
        "current_emotion": "overwhelm",
        "intensity": 0.75
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😥"


def test_conflicted_sad_but_relieved(emoji_intelligence):
    """Conflicted emotions should return sad but relieved emoji."""
    emotional_state = {
        "current_emotion": "conflicted",
        "intensity": 0.55
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😥"


# ============================================================================
# DEFAULT/FALLBACK TESTS
# ============================================================================

def test_neutral_emotion_blue_heart(emoji_intelligence):
    """Neutral emotion should default to blue heart."""
    emotional_state = {
        "current_emotion": "neutral",
        "intensity": 0.50
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_unknown_emotion_blue_heart(emoji_intelligence):
    """Unknown emotion should default to blue heart."""
    emotional_state = {
        "current_emotion": "curiosity",  # Not in any category
        "intensity": 0.60
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_missing_emotion_field_blue_heart(emoji_intelligence):
    """Missing current_emotion field should default to neutral → blue heart."""
    emotional_state = {
        "intensity": 0.70
        # No current_emotion field
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"


def test_missing_intensity_field_uses_default(emoji_intelligence):
    """Missing intensity field should use default (0.5) for emotion selection."""
    emotional_state = {
        "current_emotion": "sadness"
        # No intensity field - defaults to 0.5
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    # Default intensity 0.5 falls in moderate sadness range (>0.5 check fails, goes to else)
    assert result == "💙"  # Falls through to mild sadness


# ============================================================================
# CHARACTER ARCHETYPE TESTS
# ============================================================================

def test_technical_character_uses_emotional_logic(emoji_intelligence):
    """Technical characters should use emotion-based logic (not prayer hands)."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.80
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="technical"
    )
    
    assert result == "😢"  # High sadness


def test_general_character_uses_emotional_logic(emoji_intelligence):
    """General characters should use emotion-based logic."""
    emotional_state = {
        "current_emotion": "fear",
        "intensity": 0.70
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "😟"  # High fear


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_exact_intensity_boundaries(emoji_intelligence):
    """Test exact intensity boundary values."""
    # Sadness at exactly 0.7 (boundary)
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.7
    }
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    assert result == "😔"  # 0.7 is NOT >0.7, so moderate range
    
    # Fear at exactly 0.6 (boundary)
    emotional_state = {
        "current_emotion": "fear",
        "intensity": 0.6
    }
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    assert result == "💙"  # 0.6 is NOT >0.6, so moderate range


def test_very_high_intensity(emoji_intelligence):
    """Test intensity values at upper extreme (1.0)."""
    emotional_state = {
        "current_emotion": "anger",
        "intensity": 1.0
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💔"  # High anger


def test_very_low_intensity(emoji_intelligence):
    """Test intensity values at lower extreme (0.0)."""
    emotional_state = {
        "current_emotion": "sadness",
        "intensity": 0.0
    }
    
    result = emoji_intelligence._select_emotion_aware_empathy_emoji(
        emotional_state=emotional_state,
        bot_character="general"
    )
    
    assert result == "💙"  # Mild sadness


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
