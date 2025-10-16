"""
Test Emotion Mirroring Functionality
====================================

Tests that both emoji systems (Discord reactions and LLM response decoration)
correctly mirror user emotions when detected with high confidence and intensity.
"""

import pytest
from src.intelligence.database_emoji_selector import DatabaseEmojiSelector
from src.intelligence.vector_emoji_intelligence import VectorEmojiIntelligence


class TestEmotionMirroring:
    """Test emotion mirroring functionality in emoji systems"""
    
    def test_sadness_mirroring_high_intensity(self):
        """Test that high-intensity sadness triggers crying emoji"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # High intensity sadness (0.9)
        mirroring_emoji = selector._get_emotion_mirroring_emoji('sadness', 0.9)
        
        assert mirroring_emoji == '😢', "High-intensity sadness should mirror with crying face"
    
    def test_sadness_mirroring_medium_intensity(self):
        """Test that medium-intensity sadness triggers pensive emoji"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # Medium intensity sadness (0.7)
        mirroring_emoji = selector._get_emotion_mirroring_emoji('sadness', 0.7)
        
        assert mirroring_emoji == '😔', "Medium-intensity sadness should mirror with pensive face"
    
    def test_joy_mirroring_high_intensity(self):
        """Test that high-intensity joy triggers beaming smile"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # High intensity joy (0.85)
        mirroring_emoji = selector._get_emotion_mirroring_emoji('joy', 0.85)
        
        assert mirroring_emoji == '😄', "High-intensity joy should mirror with beaming smile"
    
    def test_fear_mirroring(self):
        """Test that fear triggers worried/anxious emojis"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # High intensity fear
        high_fear = selector._get_emotion_mirroring_emoji('fear', 0.9)
        assert high_fear == '😰', "High-intensity fear should mirror with anxious face"
        
        # Medium intensity fear
        med_fear = selector._get_emotion_mirroring_emoji('fear', 0.7)
        assert med_fear == '😟', "Medium-intensity fear should mirror with worried face"
    
    def test_anger_mirroring(self):
        """Test that anger triggers appropriate anger emojis"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # High intensity anger
        high_anger = selector._get_emotion_mirroring_emoji('anger', 0.85)
        assert high_anger == '😤', "High-intensity anger should mirror with steam face"
        
        # Medium intensity anger
        med_anger = selector._get_emotion_mirroring_emoji('anger', 0.65)
        assert med_anger == '😠', "Medium-intensity anger should mirror with angry face"
    
    def test_neutral_no_mirroring(self):
        """Test that neutral emotions don't trigger mirroring"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # Neutral should return None
        mirroring_emoji = selector._get_emotion_mirroring_emoji('neutral', 0.7)
        
        assert mirroring_emoji is None, "Neutral emotions should not trigger mirroring"
    
    def test_should_mirror_high_confidence_intensity(self):
        """Test that mirroring triggers with high confidence AND intensity"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.8,
            'confidence': 0.9
        }
        
        bot_emotion_data = {
            'primary_emotion': 'concern',  # Empathetic response
            'intensity': 0.6,
            'confidence': 0.8
        }
        
        should_mirror = selector._should_mirror_user_emotion(user_emotion_data, bot_emotion_data)
        
        assert should_mirror is True, "Should mirror when confidence>0.7, intensity>0.6, and emotions align"
    
    def test_should_not_mirror_low_confidence(self):
        """Test that mirroring doesn't trigger with low confidence"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.8,
            'confidence': 0.5  # Low confidence
        }
        
        bot_emotion_data = {
            'primary_emotion': 'concern',
            'intensity': 0.6,
            'confidence': 0.8
        }
        
        should_mirror = selector._should_mirror_user_emotion(user_emotion_data, bot_emotion_data)
        
        assert should_mirror is False, "Should NOT mirror when confidence <= 0.7"
    
    def test_should_not_mirror_low_intensity(self):
        """Test that mirroring doesn't trigger with low intensity"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        user_emotion_data = {
            'primary_emotion': 'sadness',
            'intensity': 0.4,  # Low intensity
            'confidence': 0.9
        }
        
        bot_emotion_data = {
            'primary_emotion': 'concern',
            'intensity': 0.6,
            'confidence': 0.8
        }
        
        should_mirror = selector._should_mirror_user_emotion(user_emotion_data, bot_emotion_data)
        
        assert should_mirror is False, "Should NOT mirror when intensity <= 0.6"
    
    def test_empathetic_emotion_pairs(self):
        """Test that empathetic emotion pairs trigger mirroring"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # Sadness → Concern (bot being empathetic)
        user_data = {'primary_emotion': 'sadness', 'intensity': 0.8, 'confidence': 0.9}
        bot_data = {'primary_emotion': 'concern', 'intensity': 0.6, 'confidence': 0.8}
        assert selector._should_mirror_user_emotion(user_data, bot_data) is True
        
        # Fear → Concern
        user_data = {'primary_emotion': 'fear', 'intensity': 0.8, 'confidence': 0.9}
        bot_data = {'primary_emotion': 'concern', 'intensity': 0.6, 'confidence': 0.8}
        assert selector._should_mirror_user_emotion(user_data, bot_data) is True
        
        # Joy → Joy (bot shares user's joy)
        user_data = {'primary_emotion': 'joy', 'intensity': 0.8, 'confidence': 0.9}
        bot_data = {'primary_emotion': 'joy', 'intensity': 0.7, 'confidence': 0.8}
        assert selector._should_mirror_user_emotion(user_data, bot_data) is True
    
    def test_intensity_levels(self):
        """Test that different intensity levels map to different emojis"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        # Sadness: high, medium, low
        assert selector._get_emotion_mirroring_emoji('sadness', 0.9) == '😢'  # high
        assert selector._get_emotion_mirroring_emoji('sadness', 0.7) == '😔'  # medium
        assert selector._get_emotion_mirroring_emoji('sadness', 0.5) == '🙁'  # low (below threshold but testing mapping)
        
        # Joy: high, medium, low
        assert selector._get_emotion_mirroring_emoji('joy', 0.9) == '😄'  # high
        assert selector._get_emotion_mirroring_emoji('joy', 0.7) == '😊'  # medium
        assert selector._get_emotion_mirroring_emoji('joy', 0.5) == '🙂'  # low
    
    def test_vector_emoji_intelligence_mirroring(self):
        """Test that VectorEmojiIntelligence has emotion mirroring capability"""
        # Create mock memory manager
        class MockMemoryManager:
            async def search_similar_conversations(self, *args, **kwargs):
                return []
        
        intelligence = VectorEmojiIntelligence(MockMemoryManager())
        
        # Test that method exists and works (0.85 is high intensity >0.8)
        mirroring_emoji = intelligence._get_emotion_mirroring_emoji('sadness', 0.85)
        
        assert mirroring_emoji == '😢', "VectorEmojiIntelligence should support emotion mirroring"
    
    def test_mirroring_coverage_all_emotions(self):
        """Test that all major emotions have mirroring mappings"""
        selector = DatabaseEmojiSelector(db_pool=None)
        
        emotions_to_test = ['sadness', 'joy', 'fear', 'anger', 'surprise', 'disgust', 'excitement']
        
        for emotion in emotions_to_test:
            mirroring_emoji = selector._get_emotion_mirroring_emoji(emotion, 0.8)
            assert mirroring_emoji is not None, f"Emotion '{emotion}' should have a mirroring emoji"
            assert isinstance(mirroring_emoji, str), f"Mirroring emoji for '{emotion}' should be a string"
            assert len(mirroring_emoji) > 0, f"Mirroring emoji for '{emotion}' should not be empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
