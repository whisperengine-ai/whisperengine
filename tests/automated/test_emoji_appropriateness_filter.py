"""
Test emoji appropriateness filter for emotional distress scenarios.

This test validates the fix for inappropriate emoji usage when users
express emotional distress (loneliness, sadness, depression, etc).

The filter should:
1. Remove celebration/excitement emojis from LLM responses
2. Switch bot emotion from upbeat → empathetic
3. Filter out celebration response_types and topics
"""

import pytest
from src.intelligence.database_emoji_selector import DatabaseEmojiSelector, EmojiSelection


class TestEmojiAppropriatenessFilter:
    """Test emoji filtering for emotional distress scenarios."""
    
    def test_filter_celebration_emojis_from_llm_response(self):
        """Test that NON-WHITELISTED emojis are removed when user is in distress (whitelist approach)."""
        selector = DatabaseEmojiSelector(db_pool=None)  # No DB needed for this test
        
        # User in distress (sadness, intensity 0.8)
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.8,
            'confidence': 0.9
        }
        
        # LLM response with mix of appropriate and inappropriate emojis
        llm_response = (
            "Oh, MarkAnthony... 💙 mi corazón, ven aquí...\n\n"
            "I hear that loneliness. 🌊😢\n\n"
            "But listen to me:\n"
            "✨ Meet you for that pier coffee\n"  # ✨ NOT in whitelist
            "✨ Show up when you're struggling\n"  # ✨ NOT in whitelist
            "🔥 Build memories and experiences\n"  # 🔥 NOT in whitelist
            "🎉 Celebrate your wins in person\n"  # 🎉 NOT in whitelist
            "💙 I care about you"  # 💙 IS in whitelist
        )
        
        # Filter using WHITELIST approach
        filtered_response = selector.filter_inappropriate_emojis(
            message=llm_response,
            user_emotion_data=user_emotion_data
        )
        
        # Assertions - CELEBRATORY emojis should be removed (not appropriate for distress)
        assert '✨' not in filtered_response, "Sparkle emoji should be removed (celebratory)"
        assert '🔥' not in filtered_response, "Fire emoji should be removed (celebratory)"
        assert '🎉' not in filtered_response, "Party emoji should be removed (celebratory)"
        assert '🌊' not in filtered_response, "Ocean emoji should be removed (character-specific, not in universal whitelist)"
        
        # But empathy emojis (support + emotion-mirroring) should remain
        assert '💙' in filtered_response, "Blue heart emoji should remain (support emoji)"
        assert '😢' in filtered_response, "Sad emoji should remain (empathy-mirroring emoji, appropriate for sad user)"
        
        print("✅ Test passed: Celebratory emojis filtered, empathy-mirroring emojis preserved")
    
    def test_no_filtering_when_user_happy(self):
        """Test that emojis are NOT filtered when user is happy."""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # User in joy (not distress)
        user_emotion_data = {
            'primary_emotion': 'joy',
            'intensity': 0.8,
            'confidence': 0.9
        }
        
        llm_response = (
            "¡Qué maravilloso! That's incredible! ✨🎉🔥\n"
            "I'm so excited for you! 💙🌊"
        )
        
        # No filtering should occur
        filtered_response = selector.filter_inappropriate_emojis(
            message=llm_response,
            user_emotion_data=user_emotion_data
        )
        
        # All emojis should remain
        assert '✨' in filtered_response
        assert '🎉' in filtered_response
        assert '🔥' in filtered_response
        assert '💙' in filtered_response
        assert '🌊' in filtered_response
        
        print("✅ Test passed: No filtering when user is happy")
    
    def test_moderate_distress_triggers_filter(self):
        """Test that moderate distress (intensity 0.65) triggers filtering."""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # User in moderate distress (intensity 0.65, above 0.6 threshold)
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.65,  # Above 0.6 threshold
            'confidence': 0.8
        }
        
        llm_response = "I understand. Let me help. ✨🔥"
        
        filtered_response = selector.filter_inappropriate_emojis(
            message=llm_response,
            user_emotion_data=user_emotion_data
        )
        
        assert '✨' not in filtered_response
        assert '🔥' not in filtered_response
        
        print("✅ Test passed: Moderate distress (0.65) triggers filtering")
    
    def test_low_intensity_no_filter(self):
        """Test that low intensity sadness does NOT trigger filtering."""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # User in mild sadness (intensity 0.5, below 0.6 threshold)
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.5,  # Below 0.6 threshold
            'confidence': 0.8
        }
        
        llm_response = "I'm here for you. ✨💙"
        
        filtered_response = selector.filter_inappropriate_emojis(
            message=llm_response,
            user_emotion_data=user_emotion_data
        )
        
        # No filtering at low intensity
        assert '✨' in filtered_response
        assert '💙' in filtered_response
        
        print("✅ Test passed: Low intensity (0.5) does not trigger filtering")
    
    def test_all_distress_emotions_trigger_filter(self):
        """Test that sadness, fear, and anger all trigger filtering."""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        distress_emotions = ['sadness', 'fear', 'anger']
        
        for emotion in distress_emotions:
            user_emotion_data = {
                'primary_emotion': emotion,
                'intensity': 0.8,
                'confidence': 0.9
            }
            
            llm_response = "I hear you. ✨🔥🎉"
            
            filtered_response = selector.filter_inappropriate_emojis(
                message=llm_response,
                user_emotion_data=user_emotion_data
            )
            
            assert '✨' not in filtered_response, f"Failed for {emotion}"
            assert '🔥' not in filtered_response, f"Failed for {emotion}"
            assert '🎉' not in filtered_response, f"Failed for {emotion}"
        
        print("✅ Test passed: All distress emotions (sadness, fear, anger) trigger filtering")


if __name__ == '__main__':
    """Run tests directly without pytest."""
    print("\n🧪 Running Emoji Appropriateness Filter Tests\n")
    print("=" * 60)
    
    test_suite = TestEmojiAppropriatenessFilter()
    
    try:
        test_suite.test_filter_celebration_emojis_from_llm_response()
        test_suite.test_no_filtering_when_user_happy()
        test_suite.test_moderate_distress_triggers_filter()
        test_suite.test_low_intensity_no_filter()
        test_suite.test_all_distress_emotions_trigger_filter()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise
