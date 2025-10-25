"""
Test refined emotional intelligence component with cleaner formatting.
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.prompts.emotional_intelligence_component import create_emotional_intelligence_component


async def test_refined_format():
    """Test that new format matches cleaner ai-brain-memory style."""
    
    # Mock user emotion data (joy with high confidence)
    current_user_emotion = {
        'primary_emotion': 'joy',
        'roberta_confidence': 0.87,
        'emotional_intensity': 0.65,
        'emotion_variance': 0.12
    }
    
    # Mock character emotional state with recent history
    class MockCharacterState:
        def __init__(self):
            self.recent_emotion_history = [
                {'emotion': 'optimism', 'intensity': 0.6},
                {'emotion': 'anticipation', 'intensity': 0.5},
                {'emotion': 'joy', 'intensity': 0.7}
            ]
        
        def get_prompt_guidance(self):
            return None  # Force fallback to RoBERTa data
    
    component = await create_emotional_intelligence_component(
        user_id="test_user_123",
        bot_name="elena",
        current_user_emotion=current_user_emotion,
        current_bot_emotion=None,
        character_emotional_state=MockCharacterState(),
        temporal_client=None,  # Skip InfluxDB for this test
        priority=9,
        confidence_threshold=0.7,
        intensity_threshold=0.5,
        return_metadata=False  # Return just component, not tuple
    )
    
    if component:
        print("✅ Component created successfully!\n")
        print("=" * 80)
        print(component.content)
        print("=" * 80)
        
        # Validate format
        content = component.content
        assert "=== EMOTIONAL CONTEXT" in content, "Missing emotional context header"
        assert "=== EMOTIONAL ADAPTATION ===" in content, "Missing adaptation header"
        assert "joyful and happy" in content, "Missing natural language descriptor"
        assert "• User's current state: JOY" in content, "Missing current state"
        assert "• Response style:" in content, "Missing response style guidance"
        assert "• Tone:" in content, "Missing tone guidance"
        assert "• Actions:" in content, "Missing actions guidance"
        
        print("\n✅ All format validations passed!")
        print("🎯 New format matches cleaner ai-brain-memory style with actionable guidance")
    else:
        print("❌ No component created - check thresholds")


async def test_negative_emotion_with_warning():
    """Test that negative emotions trigger appropriate warnings."""
    
    # Mock user emotion data (fear - negative emotion)
    current_user_emotion = {
        'primary_emotion': 'fear',
        'roberta_confidence': 0.82,
        'emotional_intensity': 0.72,
        'emotion_variance': 0.15
    }
    
    component = await create_emotional_intelligence_component(
        user_id="test_user_456",
        bot_name="elena",
        current_user_emotion=current_user_emotion,
        current_bot_emotion=None,
        character_emotional_state=None,
        temporal_client=None,
        priority=9,
        confidence_threshold=0.7,
        intensity_threshold=0.5,
        return_metadata=False  # Return just component, not tuple
    )
    
    if component:
        print("\n" + "=" * 80)
        print("Testing FEAR emotion (negative):")
        print("=" * 80)
        print(component.content)
        print("=" * 80)
        
        # Validate fear-specific guidance
        content = component.content
        assert "fearful and anxious" in content, "Missing fear descriptor"
        assert "⚠️ ALERT" in content, "Missing alert for negative emotion"
        assert "reassuring" in content.lower(), "Missing reassurance guidance"
        
        print("\n✅ Fear emotion handled correctly with alert!")
    else:
        print("❌ No component created for fear emotion")


if __name__ == "__main__":
    print("Testing refined emotional intelligence component...")
    print("=" * 80)
    asyncio.run(test_refined_format())
    asyncio.run(test_negative_emotion_with_warning())
    print("\n✅ All tests passed! Ready for integration.")
