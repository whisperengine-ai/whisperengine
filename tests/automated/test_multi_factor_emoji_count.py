"""
Test Multi-Factor Emoji Count Selection

Tests the enhanced emoji count logic that considers:
- Emotional intensity
- RoBERTa confidence
- Emotional variance (stability)
- User emotion context
- Character personality constraints
"""

import pytest
from unittest.mock import MagicMock
from src.intelligence.database_emoji_selector import DatabaseEmojiSelector


class TestMultiFactorEmojiCount:
    """Test suite for emotionally intelligent emoji count selection"""
    
    @pytest.fixture
    def selector(self):
        """Create DatabaseEmojiSelector instance with mock db_pool"""
        mock_db_pool = MagicMock()
        return DatabaseEmojiSelector(db_pool=mock_db_pool)
    
    # ==================== BASE INTENSITY TESTS ====================
    
    def test_high_intensity_base_count(self, selector):
        """High intensity (>0.8) should start with 3 emojis"""
        bot_emotion_data = {
            'intensity': 0.85,
            'confidence': 0.5,  # Average confidence
            'emotional_variance': 0.5  # Average variance
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 3, "High intensity should yield 3 emojis"
    
    def test_medium_intensity_base_count(self, selector):
        """Medium intensity (0.5-0.8) should start with 2 emojis"""
        bot_emotion_data = {
            'intensity': 0.65,
            'confidence': 0.5,
            'emotional_variance': 0.5
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 2, "Medium intensity should yield 2 emojis"
    
    def test_low_intensity_base_count(self, selector):
        """Low intensity (<0.5) should start with 1 emoji"""
        bot_emotion_data = {
            'intensity': 0.4,
            'confidence': 0.5,
            'emotional_variance': 0.5
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.4,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 1, "Low intensity should yield 1 emoji"
    
    # ==================== CONFIDENCE BOOST TESTS ====================
    
    def test_high_confidence_boosts_count(self, selector):
        """High confidence (>0.85) should boost emoji count"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium intensity (base 2)
            'confidence': 0.90,  # High confidence
            'emotional_variance': 0.5
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 3, "High confidence should boost medium intensity from 2 to 3"
    
    def test_low_confidence_no_boost(self, selector):
        """Low confidence should not boost emoji count"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium intensity
            'confidence': 0.50,  # Low confidence
            'emotional_variance': 0.5
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 2, "Low confidence should not boost count"
    
    def test_confidence_respects_cap(self, selector):
        """Confidence boost should not exceed 3 emoji cap"""
        bot_emotion_data = {
            'intensity': 0.85,  # High intensity (base 3)
            'confidence': 0.95,  # Very high confidence
            'emotional_variance': 0.5
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 3, "Should cap at 3 even with high confidence boost"
    
    # ==================== EMOTIONAL VARIANCE TESTS ====================
    
    def test_low_variance_stable_emotion_boosts_count(self, selector):
        """Low variance + high intensity = stable strong emotion = boost"""
        bot_emotion_data = {
            'intensity': 0.75,  # High intensity
            'confidence': 0.60,
            'emotional_variance': 0.25  # Very stable
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.75,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 3, "Stable strong emotion should boost from 2 to 3"
    
    def test_high_variance_reduces_count(self, selector):
        """High variance = unstable emotion = reduce expressiveness"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium intensity (base 2)
            'confidence': 0.60,
            'emotional_variance': 0.75  # Very unstable
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 1, "High variance should reduce count from 2 to 1"
    
    def test_low_variance_with_low_intensity_no_boost(self, selector):
        """Low variance without high intensity (>0.7) should not boost"""
        bot_emotion_data = {
            'intensity': 0.55,  # Below 0.7 threshold
            'confidence': 0.60,
            'emotional_variance': 0.25  # Stable but intensity too low
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.55,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 2, "Stable emotion with low intensity should not boost"
    
    # ==================== USER DISTRESS TESTS ====================
    
    def test_user_distress_reduces_count(self, selector):
        """High user distress should reduce emoji count to 1"""
        bot_emotion_data = {
            'intensity': 0.85,  # High intensity (normally 3)
            'confidence': 0.70,
            'emotional_variance': 0.40
        }
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.75  # High distress
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 1, "User distress should reduce count to 1"
    
    def test_user_fear_high_intensity_reduces_count(self, selector):
        """User fear with high intensity should reduce count"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium (normally 2)
            'confidence': 0.70,
            'emotional_variance': 0.40
        }
        
        user_emotion_data = {
            'primary_emotion': 'fear',
            'intensity': 0.80  # High fear
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 1, "User fear should reduce count"
    
    def test_user_anger_high_intensity_reduces_count(self, selector):
        """User anger with high intensity should reduce count"""
        bot_emotion_data = {
            'intensity': 0.70,
            'confidence': 0.70,
            'emotional_variance': 0.40
        }
        
        user_emotion_data = {
            'primary_emotion': 'anger',
            'intensity': 0.75
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.70,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 1, "User anger should reduce count"
    
    def test_user_low_intensity_distress_no_reduction(self, selector):
        """Low intensity user distress (<0.7) should not reduce count"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium (base 2)
            'confidence': 0.70,
            'emotional_variance': 0.40
        }
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.50  # Low intensity
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 2, "Low intensity distress should not reduce count"
    
    def test_user_positive_emotion_no_reduction(self, selector):
        """User positive emotions should not reduce count"""
        bot_emotion_data = {
            'intensity': 0.85,  # High (base 3)
            'confidence': 0.70,
            'emotional_variance': 0.40
        }
        
        user_emotion_data = {
            'primary_emotion': 'joy',
            'intensity': 0.80
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 3, "User joy should not reduce count"
    
    # ==================== CHARACTER PERSONALITY CONSTRAINTS ====================
    
    def test_minimal_symbolic_always_one(self, selector):
        """Minimal symbolic characters always use 1 emoji"""
        bot_emotion_data = {
            'intensity': 0.95,  # Very high
            'confidence': 0.95,  # Very high
            'emotional_variance': 0.20  # Very stable
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.95,
            combination_style='minimal_symbolic_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 1, "Minimal symbolic should always return 1"
    
    def test_text_with_accent_always_one(self, selector):
        """Text with accent characters always use 1 emoji"""
        bot_emotion_data = {
            'intensity': 0.90,
            'confidence': 0.90,
            'emotional_variance': 0.25
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.90,
            combination_style='text_with_accent_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 1, "Text with accent should always return 1"
    
    def test_emoji_only_caps_at_two(self, selector):
        """Emoji-only style caps at 2 emojis"""
        bot_emotion_data = {
            'intensity': 0.95,  # Would normally be 3
            'confidence': 0.90,
            'emotional_variance': 0.25
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.95,
            combination_style='emoji_only',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 2, "Emoji-only should cap at 2"
    
    # ==================== COMBINED FACTOR TESTS ====================
    
    def test_all_factors_boost_maximum(self, selector):
        """High intensity + high confidence + low variance = maximum 3"""
        bot_emotion_data = {
            'intensity': 0.85,  # High (base 3)
            'confidence': 0.92,  # Very high
            'emotional_variance': 0.20  # Very stable
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        assert count == 3, "All positive factors should yield maximum"
    
    def test_mixed_factors_balanced_result(self, selector):
        """High confidence offset by high variance = balanced"""
        bot_emotion_data = {
            'intensity': 0.65,  # Medium (base 2)
            'confidence': 0.90,  # High (would boost to 3)
            'emotional_variance': 0.75  # High (would reduce to 2)
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.65,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data
        )
        
        # Confidence boosts 2→3, variance reduces 3→2, result should be 2
        assert count == 2, "Mixed factors should balance out"
    
    def test_all_factors_reduce_minimum(self, selector):
        """Low intensity + high variance + user distress = minimum 1"""
        bot_emotion_data = {
            'intensity': 0.40,  # Low (base 1)
            'confidence': 0.50,  # Medium
            'emotional_variance': 0.80  # Very high
        }
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.85
        }
        
        count = selector._calculate_emotionally_intelligent_emoji_count(
            intensity=0.40,
            combination_style='text_plus_emoji',
            bot_emotion_data=bot_emotion_data,
            user_emotion_data=user_emotion_data
        )
        
        assert count == 1, "All negative factors should yield minimum"
    
    def test_fallback_without_emotion_data(self, selector):
        """Should gracefully fall back if emotion data missing"""
        # This tests the fallback path in _select_from_patterns
        patterns = [{'emoji_sequence': '😊 🎉 ✨'}]
        
        emojis = selector._select_from_patterns(
            patterns=patterns,
            intensity=0.85,
            combination_style='text_plus_emoji',
            bot_emotion_data=None  # No emotion data
        )
        
        # Should use original intensity-only logic
        assert len(emojis) == 3, "Should fall back to intensity-only logic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
