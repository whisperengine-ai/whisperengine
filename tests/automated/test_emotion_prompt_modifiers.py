"""
Direct Python validation test for emotion-driven prompt modifiers.

Tests WhisperEngine's "biochemical modeling" - using RoBERTa emotion data
to dynamically influence AI response style.

Run with:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    python tests/automated/test_emotion_prompt_modifiers.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.intelligence.emotion_prompt_modifier import (
    EmotionPromptModifier,
    EmotionCategory,
    create_emotion_prompt_modifier
)


def test_joy_emotion_modifier():
    """Test prompt modification for joyful user state."""
    print("\n" + "="*80)
    print("TEST 1: JOY EMOTION MODIFIER")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    # Simulate RoBERTa joy emotion data
    emotion_data = {
        'primary_emotion': 'joy',
        'roberta_confidence': 0.85,
        'emotional_intensity': 0.75,
        'secondary_emotions': ['excitement', 'happiness'],
        'emotion_variance': 0.2,
        'emotional_trajectory': ['neutral', 'happy', 'joy']
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data, character_archetype="real_world")
    
    assert guidance is not None, "Should generate guidance for high-confidence joy"
    assert guidance.primary_emotion == 'joy'
    assert 'warm' in guidance.tone_modifiers or 'encouraging' in guidance.tone_modifiers
    assert 'dopamine' in guidance.biochemical_analogy.lower()
    
    print(f"✅ Primary Emotion: {guidance.primary_emotion}")
    print(f"✅ Confidence: {guidance.confidence:.2f}")
    print(f"✅ Intensity: {guidance.intensity:.2f}")
    print(f"✅ Tone Modifiers: {', '.join(guidance.tone_modifiers)}")
    print(f"✅ Biochemical: {guidance.biochemical_analogy}")
    print(f"\n📝 Response Style Guidance:\n{guidance.response_style_guidance}")
    
    # Test system prompt addition
    system_addition = modifier.create_system_prompt_addition(emotion_data, "real_world")
    assert system_addition is not None
    assert "EMOTIONAL CONTEXT GUIDANCE" in system_addition
    print(f"\n📋 System Prompt Addition:\n{system_addition}")
    
    print("\n✅ TEST 1 PASSED: Joy emotion modifier working correctly")


def test_anxiety_emotion_modifier():
    """Test prompt modification for anxious user state."""
    print("\n" + "="*80)
    print("TEST 2: ANXIETY EMOTION MODIFIER")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    # Simulate RoBERTa anxiety emotion data
    emotion_data = {
        'primary_emotion': 'anxiety',
        'roberta_confidence': 0.92,
        'emotional_intensity': 0.68,
        'secondary_emotions': ['worry', 'fear'],
        'emotion_variance': 0.35,
        'emotional_trajectory': ['neutral', 'worried', 'anxiety']
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data, character_archetype="fantasy")
    
    assert guidance is not None
    assert guidance.primary_emotion == 'anxiety'
    assert 'reassuring' in guidance.tone_modifiers or 'supportive' in guidance.tone_modifiers
    assert 'cortisol' in guidance.biochemical_analogy.lower()
    
    print(f"✅ Primary Emotion: {guidance.primary_emotion}")
    print(f"✅ Confidence: {guidance.confidence:.2f}")
    print(f"✅ Intensity: {guidance.intensity:.2f}")
    print(f"✅ Tone Modifiers: {', '.join(guidance.tone_modifiers)}")
    print(f"✅ Biochemical: {guidance.biochemical_analogy}")
    print(f"\n📝 Response Style Guidance:\n{guidance.response_style_guidance}")
    
    # Verify approach suggestions
    assert any('calm' in approach.lower() for approach in guidance.approach_suggestions)
    
    print("\n✅ TEST 2 PASSED: Anxiety emotion modifier working correctly")


def test_anger_emotion_modifier():
    """Test prompt modification for angry user state."""
    print("\n" + "="*80)
    print("TEST 3: ANGER EMOTION MODIFIER")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    emotion_data = {
        'primary_emotion': 'anger',
        'roberta_confidence': 0.88,
        'emotional_intensity': 0.82,
        'secondary_emotions': ['frustration', 'irritation']
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    assert guidance is not None
    assert guidance.primary_emotion == 'anger'
    assert 'calm' in guidance.tone_modifiers or 'validating' in guidance.tone_modifiers
    assert 'serotonin' in guidance.biochemical_analogy.lower()
    
    print(f"✅ Primary Emotion: {guidance.primary_emotion}")
    print(f"✅ Biochemical: {guidance.biochemical_analogy}")
    print(f"✅ Avoid Patterns: {guidance.avoid_patterns[0]}")
    
    # Verify avoidance patterns
    assert any('defensive' in avoid.lower() or 'escalat' in avoid.lower() 
               for avoid in guidance.avoid_patterns)
    
    print("\n✅ TEST 3 PASSED: Anger emotion modifier working correctly")


def test_sadness_emotion_modifier():
    """Test prompt modification for sad user state."""
    print("\n" + "="*80)
    print("TEST 4: SADNESS EMOTION MODIFIER")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    emotion_data = {
        'primary_emotion': 'sadness',
        'roberta_confidence': 0.79,
        'emotional_intensity': 0.71,
        'secondary_emotions': ['melancholy', 'grief']
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data, character_archetype="narrative_ai")
    
    assert guidance is not None
    assert guidance.primary_emotion == 'sadness'
    assert 'empathetic' in guidance.tone_modifiers or 'gentle' in guidance.tone_modifiers
    assert 'oxytocin' in guidance.biochemical_analogy.lower()
    
    print(f"✅ Primary Emotion: {guidance.primary_emotion}")
    print(f"✅ Biochemical: {guidance.biochemical_analogy}")
    print(f"✅ Approach: {guidance.approach_suggestions[0]}")
    
    # Verify avoidance of toxic positivity
    assert any('toxic' in avoid.lower() or 'dismiss' in avoid.lower() 
               for avoid in guidance.avoid_patterns)
    
    print("\n✅ TEST 4 PASSED: Sadness emotion modifier working correctly")


def test_neutral_emotion_no_modification():
    """Test that neutral emotions don't force unnatural modifications."""
    print("\n" + "="*80)
    print("TEST 5: NEUTRAL EMOTION (NATURAL STATE)")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    emotion_data = {
        'primary_emotion': 'neutral',
        'roberta_confidence': 0.65,
        'emotional_intensity': 0.3  # Low intensity
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    # Low intensity should result in no guidance (below threshold)
    assert guidance is None, "Low intensity neutral should not generate guidance"
    
    print("✅ Correctly skipped guidance for low-intensity neutral emotion")
    
    # Test high-intensity neutral (rare but possible)
    emotion_data['emotional_intensity'] = 0.8
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    if guidance:
        print(f"✅ High-intensity neutral generated: {guidance.primary_emotion}")
        assert guidance.primary_emotion == 'neutral'
        assert 'natural' in guidance.tone_modifiers or 'authentic' in guidance.tone_modifiers
    
    print("\n✅ TEST 5 PASSED: Neutral emotion handling correct")


def test_low_confidence_threshold():
    """Test that low-confidence emotions are ignored."""
    print("\n" + "="*80)
    print("TEST 6: LOW CONFIDENCE THRESHOLD")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier(confidence_threshold=0.7)
    
    # Emotion with confidence below threshold
    emotion_data = {
        'primary_emotion': 'joy',
        'roberta_confidence': 0.55,  # Below 0.7 threshold
        'emotional_intensity': 0.85
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    assert guidance is None, "Should skip low-confidence emotions"
    print("✅ Correctly ignored low-confidence emotion (0.55 < 0.7 threshold)")
    
    # Increase confidence above threshold
    emotion_data['roberta_confidence'] = 0.75
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    assert guidance is not None, "Should process high-confidence emotions"
    print(f"✅ Correctly processed high-confidence emotion (0.75 > 0.7 threshold)")
    
    print("\n✅ TEST 6 PASSED: Confidence threshold working correctly")


def test_intensity_threshold():
    """Test that low-intensity emotions are ignored."""
    print("\n" + "="*80)
    print("TEST 7: INTENSITY THRESHOLD")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier(intensity_threshold=0.5)
    
    # Emotion with intensity below threshold
    emotion_data = {
        'primary_emotion': 'excitement',
        'roberta_confidence': 0.85,
        'emotional_intensity': 0.35  # Below 0.5 threshold
    }
    
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    assert guidance is None, "Should skip low-intensity emotions"
    print("✅ Correctly ignored low-intensity emotion (0.35 < 0.5 threshold)")
    
    # Increase intensity above threshold
    emotion_data['emotional_intensity'] = 0.65
    guidance = modifier.generate_prompt_guidance(emotion_data)
    
    assert guidance is not None, "Should process high-intensity emotions"
    print(f"✅ Correctly processed high-intensity emotion (0.65 > 0.5 threshold)")
    
    print("\n✅ TEST 7 PASSED: Intensity threshold working correctly")


def test_emotion_mapping():
    """Test that various emotion strings map correctly to categories."""
    print("\n" + "="*80)
    print("TEST 8: EMOTION STRING MAPPING")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    # Test various emotion string formats
    test_cases = [
        ('happiness', EmotionCategory.JOY),
        ('happy', EmotionCategory.JOY),
        ('sad', EmotionCategory.SADNESS),
        ('angry', EmotionCategory.ANGER),
        ('scared', EmotionCategory.FEAR),
        ('anxious', EmotionCategory.ANXIETY),
        ('frustrated', EmotionCategory.FRUSTRATION),
        ('confused', EmotionCategory.CONFUSION),
    ]
    
    for emotion_str, expected_category in test_cases:
        mapped = modifier._map_emotion_to_category(emotion_str)
        assert mapped == expected_category, f"Failed to map '{emotion_str}' to {expected_category}"
        print(f"✅ Correctly mapped '{emotion_str}' → {expected_category.value}")
    
    print("\n✅ TEST 8 PASSED: Emotion string mapping working correctly")


def test_character_archetype_modifiers():
    """Test that character archetypes affect guidance appropriately."""
    print("\n" + "="*80)
    print("TEST 9: CHARACTER ARCHETYPE MODIFIERS")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    emotion_data = {
        'primary_emotion': 'joy',
        'roberta_confidence': 0.85,
        'emotional_intensity': 0.75
    }
    
    # Test real_world archetype
    real_world_addition = modifier.create_system_prompt_addition(
        emotion_data, 
        character_archetype="real_world"
    )
    assert "authentic AI nature" in real_world_addition
    print("✅ Real-world archetype includes AI nature guidance")
    
    # Test fantasy archetype
    fantasy_addition = modifier.create_system_prompt_addition(
        emotion_data,
        character_archetype="fantasy"
    )
    assert "fully immersed" in fantasy_addition
    print("✅ Fantasy archetype includes immersion guidance")
    
    # Test no archetype (generic)
    generic_addition = modifier.create_system_prompt_addition(emotion_data)
    assert generic_addition is not None
    assert "EMOTIONAL CONTEXT GUIDANCE" in generic_addition
    print("✅ Generic guidance works without archetype")
    
    print("\n✅ TEST 9 PASSED: Character archetype modifiers working correctly")


def test_comprehensive_emotion_coverage():
    """Test all supported emotion categories."""
    print("\n" + "="*80)
    print("TEST 10: COMPREHENSIVE EMOTION COVERAGE")
    print("="*80)
    
    modifier = create_emotion_prompt_modifier()
    
    all_emotions = [
        'joy', 'sadness', 'anger', 'fear', 'anxiety', 
        'excitement', 'frustration', 'confusion', 'neutral'
    ]
    
    for emotion in all_emotions:
        emotion_data = {
            'primary_emotion': emotion,
            'roberta_confidence': 0.85,
            'emotional_intensity': 0.75
        }
        
        guidance = modifier.generate_prompt_guidance(emotion_data)
        assert guidance is not None, f"Failed to generate guidance for {emotion}"
        assert guidance.biochemical_analogy, f"No biochemical analogy for {emotion}"
        
        print(f"✅ {emotion.upper():15} → {guidance.biochemical_analogy[:50]}...")
    
    print("\n✅ TEST 10 PASSED: All emotion categories supported")


def run_all_tests():
    """Run all emotion prompt modifier tests."""
    print("\n" + "🎭" * 40)
    print("WHIPERENGINE EMOTION PROMPT MODIFIER TEST SUITE")
    print("Testing 'Biochemical Modeling' - Emotion-Driven Response Guidance")
    print("🎭" * 40)
    
    tests = [
        test_joy_emotion_modifier,
        test_anxiety_emotion_modifier,
        test_anger_emotion_modifier,
        test_sadness_emotion_modifier,
        test_neutral_emotion_no_modification,
        test_low_confidence_threshold,
        test_intensity_threshold,
        test_emotion_mapping,
        test_character_archetype_modifiers,
        test_comprehensive_emotion_coverage
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test.__name__}")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Emotion prompt modifiers working correctly.")
        print("\nNext steps:")
        print("1. Test with live Discord bot (Elena character recommended)")
        print("2. Send messages with different emotional tones")
        print("3. Observe response style adaptations")
        print("\nWhisperEngine's 'biochemical modeling' is operational! 🧠✨")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review errors above")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
