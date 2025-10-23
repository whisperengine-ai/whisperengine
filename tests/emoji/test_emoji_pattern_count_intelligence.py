"""
Tests for Emoji Pattern Count Intelligence Enhancement

Validates that pattern-based emoji selection uses multi-factor intelligence
for emoji count determination (not just simple intensity thresholds).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.intelligence.database_emoji_selector import DatabaseEmojiSelector


@pytest.fixture
def emoji_selector():
    """Create emoji selector with mocked dependencies"""
    selector = DatabaseEmojiSelector(db_pool=Mock())
    return selector


class TestEmojiPatternCountIntelligence:
    """Test suite for pattern-based emoji count intelligence"""
    
    def test_pattern_selection_with_full_emotion_data(self, emoji_selector):
        """Pattern selection uses multi-factor intelligence with full emotion data"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.90,  # High confidence
            'intensity': 0.65,   # Medium intensity
            'emotional_variance': 0.25  # Stable emotion
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Should get 3 emojis due to confidence boost (0.90 > 0.85)
        # Base: 2 (intensity 0.65 > 0.5) + 1 (confidence boost) = 3
        assert len(result) == 3
        assert result == ['😊', '💙', '✨']
    
    def test_pattern_selection_with_missing_emotion_data(self, emoji_selector):
        """Pattern selection with missing emotion data uses defaults"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.70,
            combination_style='text_plus_emoji',
            bot_emotion_data=None,  # Missing emotion data
            user_emotion_data=None
        )
        
        # Should still work with default emotion data
        # Default confidence=0.5, variance=0.5 -> base count from intensity
        # intensity 0.70 > 0.5 -> base count = 2
        assert len(result) == 2
        assert result == ['😊', '💙']
    
    def test_pattern_selection_high_variance_reduces_count(self, emoji_selector):
        """High emotional variance reduces emoji count"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.60,
            'intensity': 0.70,
            'emotional_variance': 0.80  # High variance -> unstable emotion
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.70,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Base: 2 (intensity 0.70 > 0.5) - 1 (high variance) = 1
        assert len(result) == 1
        assert result == ['😊']
    
    def test_pattern_selection_stable_strong_emotion_boosts_count(self, emoji_selector):
        """Stable + strong emotion boosts emoji count"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.60,
            'intensity': 0.75,
            'emotional_variance': 0.25  # Low variance + high intensity
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.75,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Base: 2 (intensity 0.75 > 0.5) + 1 (stable strong emotion) = 3
        assert len(result) == 3
        assert result == ['😊', '💙', '✨']
    
    def test_pattern_selection_user_distress_reduces_count(self, emoji_selector):
        """User in distress causes conservative emoji count"""
        patterns = [{'emoji_sequence': '💙 🤗 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'caring',
            'confidence': 0.85,
            'intensity': 0.80,
            'emotional_variance': 0.30
        }
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.85  # User in high distress
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.80,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        # Should reduce to 1 emoji due to user distress
        assert len(result) == 1
        assert result == ['💙']
    
    def test_pattern_selection_respects_character_personality_minimal(self, emoji_selector):
        """Minimal symbolic personality always gets 1 emoji"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.95,  # High confidence
            'intensity': 0.90,   # High intensity
            'emotional_variance': 0.20  # Stable
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.90,
            combination_style='minimal_symbolic_emoji',  # Character constraint
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Should be 1 emoji regardless of other factors
        assert len(result) == 1
        assert result == ['😊']
    
    def test_pattern_selection_respects_character_personality_accent(self, emoji_selector):
        """Text with accent personality always gets 1 emoji"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.95,
            'intensity': 0.90,
            'emotional_variance': 0.20
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.90,
            combination_style='text_with_accent_emoji',  # Character constraint
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Should be 1 emoji regardless of other factors
        assert len(result) == 1
        assert result == ['😊']
    
    def test_pattern_selection_emoji_only_capped_at_2(self, emoji_selector):
        """Emoji-only personality capped at 2 emojis"""
        patterns = [{'emoji_sequence': '😊 💙 ✨'}]
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.95,
            'intensity': 0.90,
            'emotional_variance': 0.20
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.90,
            combination_style='emoji_only',  # Character constraint
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Should be capped at 2 emojis
        assert len(result) == 2
        assert result == ['😊', '💙']
    
    def test_pattern_selection_empty_patterns(self, emoji_selector):
        """Empty patterns return empty list"""
        result = emoji_selector._select_from_patterns(
            patterns=[],
            intensity=0.70,
            combination_style='text_plus_emoji',
            bot_emotion_data={'confidence': 0.8, 'intensity': 0.7, 'emotional_variance': 0.3},
            user_emotion_data=None
        )
        
        assert result == []
    
    def test_pattern_selection_insufficient_emojis_in_sequence(self, emoji_selector):
        """Pattern with fewer emojis than calculated count"""
        patterns = [{'emoji_sequence': '😊'}]  # Only 1 emoji
        
        bot_emotion_data = {
            'primary_emotion': 'joy',
            'confidence': 0.95,
            'intensity': 0.90,
            'emotional_variance': 0.20
        }
        
        result = emoji_selector._select_from_patterns(
            patterns=patterns,
            intensity=0.90,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Should get all available emojis (1) even though count might be higher
        assert len(result) == 1
        assert result == ['😊']


class TestMultiFactorEmojiCountLogic:
    """Test the underlying multi-factor emoji count calculation"""
    
    def test_high_confidence_boosts_count(self, emoji_selector):
        """High confidence increases emoji count"""
        bot_emotion_data = {
            'confidence': 0.90,  # > 0.85 threshold
            'intensity': 0.65,   # Medium intensity
            'emotional_variance': 0.50
        }
        
        count = emoji_selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Base: 2 (intensity 0.65 > 0.5) + 1 (confidence boost) = 3
        assert count == 3
    
    def test_stable_strong_emotion_boosts_count(self, emoji_selector):
        """Stable + strong emotion increases count"""
        bot_emotion_data = {
            'confidence': 0.70,
            'intensity': 0.75,   # > 0.7 threshold
            'emotional_variance': 0.25  # < 0.3 threshold
        }
        
        count = emoji_selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.75,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Base: 2 (intensity 0.75 > 0.5) + 1 (stable strong) = 3
        assert count == 3
    
    def test_high_variance_reduces_count(self, emoji_selector):
        """High variance decreases emoji count"""
        bot_emotion_data = {
            'confidence': 0.60,
            'intensity': 0.70,
            'emotional_variance': 0.80  # > 0.7 threshold
        }
        
        count = emoji_selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.70,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=None
        )
        
        # Base: 2 (intensity 0.70 > 0.5) - 1 (high variance) = 1
        assert count == 1
    
    def test_user_distress_forces_conservative(self, emoji_selector):
        """User in distress forces count to 1"""
        bot_emotion_data = {
            'confidence': 0.85,
            'intensity': 0.90,
            'emotional_variance': 0.30
        }
        
        user_emotion_data = {
            'primary_emotion': 'fear',  # Distress emotion
            'intensity': 0.80  # High intensity
        }
        
        count = emoji_selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.90,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        # Should be forced to 1 due to user distress
        assert count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
