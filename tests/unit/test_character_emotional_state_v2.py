"""
Unit tests for CharacterEmotionalState (v2) - Full-Spectrum RoBERTa Redesign.

Tests the new 11-emotion tracking system that replaces the old 5-dimension
compression approach.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.intelligence.character_emotional_state_v2 import (
    CharacterEmotionalState,
    CharacterEmotionalStateManager
)


class TestCharacterEmotionalStateBasics:
    """Test basic creation and properties."""
    
    def test_create_default_state(self):
        """Test creating state with default values."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123"
        )
        
        assert state.character_name == "Elena"
        assert state.user_id == "test_user_123"
        assert state.joy == 0.7  # Default
        assert state.anger == 0.1  # Default
        assert state.total_interactions == 0
    
    def test_create_with_custom_baselines(self):
        """Test creating state with custom CDL baselines."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            joy=0.6,
            optimism=0.8,
            fear=0.15,
            baseline_joy=0.6,
            baseline_optimism=0.8,
            baseline_fear=0.15
        )
        
        assert state.joy == 0.6
        assert state.optimism == 0.8
        assert state.baseline_joy == 0.6
        assert state.baseline_optimism == 0.8
    
    def test_get_all_emotions(self):
        """Test retrieving all emotion values."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123"
        )
        
        emotions = state.get_all_emotions()
        
        assert len(emotions) == 11
        assert 'joy' in emotions
        assert 'anger' in emotions
        assert 'anticipation' in emotions
        assert all(0.0 <= v <= 1.0 for v in emotions.values())


class TestComputedProperties:
    """Test computed emotional properties."""
    
    def test_dominant_emotion(self):
        """Test dominant emotion detection."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,  # Highest
            anger=0.2,
            sadness=0.1
        )
        
        assert state.dominant_emotion == "joy"
    
    def test_emotional_intensity_high(self):
        """Test high emotional intensity calculation."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.95,  # Very high
            optimism=0.9,
            love=0.85,
            anticipation=0.8,
            anger=0.0
        )
        
        intensity = state.emotional_intensity
        assert intensity > 0.3  # Should be reasonably high
    
    def test_emotional_intensity_low(self):
        """Test low emotional intensity (neutral state)."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            # All emotions near neutral (0.3)
            joy=0.3,
            anger=0.3,
            sadness=0.3,
            fear=0.3,
            love=0.3,
            trust=0.3,
            optimism=0.3,
            pessimism=0.3,
            anticipation=0.3,
            disgust=0.3,
            surprise=0.3
        )
        
        intensity = state.emotional_intensity
        assert intensity < 0.1  # Should be very low
    
    def test_emotional_valence_positive(self):
        """Test positive emotional valence."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,
            love=0.8,
            optimism=0.85,
            trust=0.75,
            anger=0.1,
            sadness=0.1
        )
        
        valence = state.emotional_valence
        assert valence > 0.5  # Strong positive
    
    def test_emotional_valence_negative(self):
        """Test negative emotional valence."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            anger=0.9,
            fear=0.85,
            sadness=0.9,
            pessimism=0.75,
            disgust=0.7,
            joy=0.05,
            love=0.05,
            optimism=0.05,
            trust=0.1
        )
        
        valence = state.emotional_valence
        assert valence < -0.2  # Clearly negative
    
    def test_emotional_complexity(self):
        """Test emotional complexity (mixed emotions)."""
        # Simple state (one dominant emotion)
        simple_state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,
            # All others low
            anger=0.1,
            sadness=0.1,
            fear=0.1
        )
        
        # Complex state (multiple active emotions)
        complex_state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            joy=0.7,
            anticipation=0.6,
            fear=0.5,
            optimism=0.65,
            trust=0.55
        )
        
        assert simple_state.emotional_complexity < complex_state.emotional_complexity
    
    def test_get_top_emotions(self):
        """Test retrieving top N emotions."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,
            love=0.75,
            optimism=0.65,
            anticipation=0.5,
            trust=0.45,
            anger=0.1
        )
        
        top_3 = state.get_top_emotions(limit=3, threshold=0.3)
        
        assert len(top_3) == 3
        assert top_3[0] == ("joy", 0.9)
        assert top_3[1] == ("love", 0.75)
        assert top_3[2] == ("optimism", 0.65)


class TestEmotionUpdate:
    """Test emotion state updates from RoBERTa data."""
    
    def test_update_from_bot_emotion_direct_application(self):
        """Test direct application of RoBERTa emotions."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.5,  # Starting at 0.5
            sadness=0.2
        )
        
        # Bot expresses strong joy
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.9,
                'love': 0.7,
                'optimism': 0.65,
                'anger': 0.1,
                'sadness': 0.1,
                'fear': 0.1,
                'anticipation': 0.4,
                'trust': 0.7,
                'surprise': 0.2,
                'disgust': 0.05,
                'pessimism': 0.15
            },
            'emotional_intensity': 0.75,
            'roberta_confidence': 0.88
        }
        
        initial_joy = state.joy
        state.update_from_bot_emotion(bot_emotion_data)
        
        # Joy should increase (but smoothly, not jump to 0.9)
        assert state.joy > initial_joy
        assert state.joy < 0.9  # Smoothing prevents full jump
        assert state.total_interactions == 1
    
    def test_update_preserves_all_emotions(self):
        """Test that update applies to all 11 emotions."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123"
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.6,
                'love': 0.5,
                'optimism': 0.7,
                'anger': 0.3,
                'sadness': 0.2,
                'fear': 0.25,
                'anticipation': 0.65,
                'trust': 0.6,
                'surprise': 0.3,
                'disgust': 0.1,
                'pessimism': 0.2
            },
            'emotional_intensity': 0.55,
            'roberta_confidence': 0.82
        }
        
        initial_emotions = state.get_all_emotions()
        state.update_from_bot_emotion(bot_emotion_data)
        updated_emotions = state.get_all_emotions()
        
        # All emotions should have been updated
        # At least some should change - we verify via length check
        assert len(updated_emotions) == 11
        assert updated_emotions != initial_emotions  # Should have changed
    
    def test_empathy_absorption_from_user(self):
        """Test character absorbing user emotions through empathy."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            fear=0.1  # Low initial fear
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.6, 'love': 0.7, 'optimism': 0.6,
                'anger': 0.1, 'sadness': 0.1, 'fear': 0.1,
                'anticipation': 0.4, 'trust': 0.7, 'surprise': 0.2,
                'disgust': 0.05, 'pessimism': 0.15
            },
            'emotional_intensity': 0.5,
            'roberta_confidence': 0.8
        }
        
        # User is very anxious
        user_emotion_data = {
            'all_emotions': {
                'fear': 0.9,  # User very fearful
                'anxiety': 0.85,
                'sadness': 0.6,
                'joy': 0.1,
                'anger': 0.2,
                'love': 0.1,
                'optimism': 0.1,
                'anticipation': 0.2,
                'trust': 0.3,
                'surprise': 0.15,
                'disgust': 0.1,
                'pessimism': 0.7
            },
            'emotional_intensity': 0.85
        }
        
        initial_fear = state.fear
        state.update_from_bot_emotion(bot_emotion_data, user_emotion_data)
        
        # Elena should absorb some of user's fear through empathy
        assert state.fear > initial_fear
    
    def test_interaction_quality_impact_positive(self):
        """Test positive interaction quality boosts positive emotions."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.6,
            trust=0.6,
            optimism=0.6
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.7, 'love': 0.6, 'optimism': 0.65,
                'anger': 0.1, 'sadness': 0.1, 'fear': 0.1,
                'anticipation': 0.5, 'trust': 0.7, 'surprise': 0.2,
                'disgust': 0.05, 'pessimism': 0.15
            },
            'emotional_intensity': 0.6,
            'roberta_confidence': 0.85
        }
        
        initial_joy = state.joy
        initial_trust = state.trust
        
        # Great interaction (quality > 0.8)
        state.update_from_bot_emotion(bot_emotion_data, interaction_quality=0.9)
        
        # Positive emotions should get additional boost
        assert state.joy > initial_joy
        assert state.trust > initial_trust
    
    def test_interaction_quality_impact_negative(self):
        """Test poor interaction quality increases negative emotions."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            sadness=0.2,
            fear=0.15
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.3, 'love': 0.4, 'optimism': 0.3,
                'anger': 0.4, 'sadness': 0.5, 'fear': 0.4,
                'anticipation': 0.3, 'trust': 0.4, 'surprise': 0.2,
                'disgust': 0.25, 'pessimism': 0.5
            },
            'emotional_intensity': 0.5,
            'roberta_confidence': 0.75
        }
        
        initial_sadness = state.sadness
        initial_fear = state.fear
        
        # Poor interaction (quality < 0.4)
        state.update_from_bot_emotion(bot_emotion_data, interaction_quality=0.3)
        
        # Negative emotions should increase
        assert state.sadness > initial_sadness
        assert state.fear > initial_fear
    
    def test_emotion_history_tracking(self):
        """Test that full emotion profiles are stored in history."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123"
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.8, 'love': 0.7, 'optimism': 0.75,
                'anger': 0.1, 'sadness': 0.1, 'fear': 0.1,
                'anticipation': 0.6, 'trust': 0.7, 'surprise': 0.2,
                'disgust': 0.05, 'pessimism': 0.15
            },
            'emotional_intensity': 0.7,
            'roberta_confidence': 0.85
        }
        
        state.update_from_bot_emotion(bot_emotion_data)
        
        assert len(state.recent_emotion_history) == 1
        assert isinstance(state.recent_emotion_history[0], dict)
        assert 'joy' in state.recent_emotion_history[0]
        assert 'anger' in state.recent_emotion_history[0]
    
    def test_emotion_history_limit(self):
        """Test that emotion history is limited to last 5."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123"
        )
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.7, 'love': 0.6, 'optimism': 0.65,
                'anger': 0.1, 'sadness': 0.1, 'fear': 0.1,
                'anticipation': 0.5, 'trust': 0.6, 'surprise': 0.2,
                'disgust': 0.05, 'pessimism': 0.2
            },
            'emotional_intensity': 0.6,
            'roberta_confidence': 0.8
        }
        
        # Add 10 updates
        for _ in range(10):
            state.update_from_bot_emotion(bot_emotion_data)
        
        # Should only keep last 5
        assert len(state.recent_emotion_history) == 5


class TestTimeDecay:
    """Test homeostasis (time decay toward baseline)."""
    
    def test_time_decay_moves_toward_baseline(self):
        """Test that emotions decay toward baseline over time."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,  # High (above baseline 0.7)
            sadness=0.3,  # High (above baseline 0.15)
            baseline_joy=0.7,
            baseline_sadness=0.15
        )
        
        # Simulate 5 hours passing
        state.last_updated = datetime.now(timezone.utc) - timedelta(hours=5)
        
        initial_joy = state.joy
        initial_sadness = state.sadness
        
        state.apply_time_decay()
        
        # Joy should move toward baseline (decrease)
        assert state.joy < initial_joy
        assert state.joy > state.baseline_joy  # Not fully returned yet
        
        # Sadness should move toward baseline (decrease)
        assert state.sadness < initial_sadness
        assert state.sadness > state.baseline_sadness
    
    def test_time_decay_10_hours_full_return(self):
        """Test that 10 hours returns emotions to baseline."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            anger=0.8,  # High (above baseline 0.1)
            baseline_anger=0.1
        )
        
        # Simulate 10 hours (100% decay)
        state.last_updated = datetime.now(timezone.utc) - timedelta(hours=10)
        
        state.apply_time_decay()
        
        # Should be at or very close to baseline
        assert abs(state.anger - state.baseline_anger) < 0.01


class TestPromptGuidance:
    """Test prompt guidance generation."""
    
    def test_guidance_for_joyful_state(self):
        """Test guidance for joyful dominant state."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.9,
            love=0.7,
            optimism=0.65
        )
        
        guidance = state.get_prompt_guidance()
        
        assert guidance is not None
        assert "joy" in guidance.lower() or "JOY" in guidance
        assert "Elena" in guidance
    
    def test_guidance_for_mixed_emotions(self):
        """Test guidance for complex emotional state."""
        state = CharacterEmotionalState(
            character_name="Marcus",
            user_id="test_user_123",
            joy=0.65,
            anticipation=0.6,
            fear=0.55
        )
        
        guidance = state.get_prompt_guidance()
        
        assert guidance is not None
        # Should mention top emotions
        assert "joy" in guidance.lower() or "JOY" in guidance
    
    def test_no_guidance_for_neutral_state(self):
        """Test that neutral state returns minimal guidance."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            # All emotions at low/neutral levels
            joy=0.15,
            anger=0.1,
            sadness=0.1,
            fear=0.1,
            love=0.15,
            optimism=0.15,
            trust=0.15,
            anticipation=0.1,
            surprise=0.1,
            disgust=0.05,
            pessimism=0.1
        )
        
        guidance = state.get_prompt_guidance()
        
        # For very neutral/low state, guidance may be minimal or None
        # Just verify it doesn't crash
        if guidance:
            assert isinstance(guidance, str)
    
    def test_guidance_includes_trajectory(self):
        """Test that guidance includes emotional trajectory."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.8
        )
        
        # Build history showing positive trajectory
        state.recent_emotion_history = [
            {'joy': 0.5, 'anger': 0.2, 'sadness': 0.3, 'fear': 0.2,
             'love': 0.5, 'optimism': 0.4, 'anticipation': 0.3,
             'trust': 0.5, 'surprise': 0.2, 'disgust': 0.1, 'pessimism': 0.3},
            {'joy': 0.8, 'anger': 0.1, 'sadness': 0.15, 'fear': 0.1,
             'love': 0.7, 'optimism': 0.7, 'anticipation': 0.5,
             'trust': 0.7, 'surprise': 0.2, 'disgust': 0.05, 'pessimism': 0.15}
        ]
        
        guidance = state.get_prompt_guidance()
        
        assert guidance is not None
        assert "positive" in guidance.lower() or "stable" in guidance.lower()


class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test serializing state to dictionary."""
        state = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.8,
            anger=0.15
        )
        
        data = state.to_dict()
        
        assert data['character_name'] == "Elena"
        assert data['user_id'] == "test_user_123"
        assert data['joy'] == 0.8
        assert data['anger'] == 0.15
        assert 'dominant_emotion' in data
        assert 'emotional_intensity' in data
        assert 'emotional_valence' in data
    
    def test_from_dict(self):
        """Test deserializing state from dictionary."""
        data = {
            'character_name': "Marcus",
            'user_id': "test_user_456",
            'joy': 0.65,
            'anger': 0.2,
            'sadness': 0.3,
            'fear': 0.25,
            'love': 0.5,
            'optimism': 0.55,
            'pessimism': 0.3,
            'anticipation': 0.45,
            'trust': 0.6,
            'surprise': 0.2,
            'disgust': 0.1,
            'baseline_joy': 0.6,
            'baseline_anger': 0.1,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'total_interactions': 5,
            'recent_emotion_history': []
        }
        
        state = CharacterEmotionalState.from_dict(data)
        
        assert state.character_name == "Marcus"
        assert state.user_id == "test_user_456"
        assert state.joy == 0.65
        assert state.anger == 0.2
        assert state.total_interactions == 5
    
    def test_roundtrip_serialization(self):
        """Test that serialization roundtrip preserves state."""
        original = CharacterEmotionalState(
            character_name="Elena",
            user_id="test_user_123",
            joy=0.85,
            fear=0.25,
            love=0.75
        )
        
        data = original.to_dict()
        restored = CharacterEmotionalState.from_dict(data)
        
        assert restored.character_name == original.character_name
        assert restored.user_id == original.user_id
        assert abs(restored.joy - original.joy) < 0.001
        assert abs(restored.fear - original.fear) < 0.001


class TestCharacterEmotionalStateManager:
    """Test the state manager."""
    
    @pytest.mark.asyncio
    async def test_get_character_state_creates_new(self):
        """Test getting state creates new if not cached."""
        manager = CharacterEmotionalStateManager()
        
        state = await manager.get_character_state("Elena", "user_123")
        
        assert state.character_name == "Elena"
        assert state.user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_get_character_state_returns_cached(self):
        """Test getting state returns cached version."""
        manager = CharacterEmotionalStateManager()
        
        state1 = await manager.get_character_state("Elena", "user_123")
        state1.joy = 0.95  # Modify
        
        state2 = await manager.get_character_state("Elena", "user_123")
        
        # Should be same instance (with minimal time decay difference)
        assert abs(state2.joy - 0.95) < 0.01  # Allow tiny decay from time
    
    @pytest.mark.asyncio
    async def test_update_character_state(self):
        """Test updating character state via manager."""
        manager = CharacterEmotionalStateManager()
        
        bot_emotion_data = {
            'all_emotions': {
                'joy': 0.9, 'love': 0.8, 'optimism': 0.75,
                'anger': 0.1, 'sadness': 0.1, 'fear': 0.1,
                'anticipation': 0.6, 'trust': 0.75, 'surprise': 0.2,
                'disgust': 0.05, 'pessimism': 0.15
            },
            'emotional_intensity': 0.8,
            'roberta_confidence': 0.9
        }
        
        state = await manager.update_character_state(
            "Elena",
            "user_123",
            bot_emotion_data
        )
        
        assert state.total_interactions == 1
        assert state.dominant_emotion == "joy"
    
    @pytest.mark.asyncio
    async def test_time_decay_applied_on_get(self):
        """Test that time decay is applied when getting cached state."""
        manager = CharacterEmotionalStateManager()
        
        # Create state with high joy
        state = await manager.get_character_state("Elena", "user_123")
        state.joy = 0.95
        state.baseline_joy = 0.7
        
        # Simulate time passing
        state.last_updated = datetime.now(timezone.utc) - timedelta(hours=3)
        
        # Get state again (should apply decay)
        state2 = await manager.get_character_state("Elena", "user_123")
        
        # Joy should have decayed toward baseline
        assert state2.joy < 0.95
        assert state2.joy > 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
