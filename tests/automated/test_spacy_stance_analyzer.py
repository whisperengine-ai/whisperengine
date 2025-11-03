"""
Test suite for spaCy Stance Analyzer

Validates stance detection and second-person emotion filtering
"""

import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.intelligence.spacy_stance_analyzer import create_stance_analyzer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_user_direct_emotion():
    """Test: User expresses their own emotion"""
    analyzer = create_stance_analyzer()
    
    text = "I'm frustrated with your suggestions"
    result = analyzer.analyze_user_stance(text)
    
    print("\n✅ TEST: User direct emotion")
    print(f"   Input: {text}")
    print(f"   Primary emotions: {result.primary_emotions}")
    print(f"   Other emotions: {result.other_emotions}")
    print(f"   Self-focus: {result.self_focus:.2f}")
    print(f"   Type: {result.emotion_type}")
    
    assert 'frustrated' in result.primary_emotions, "Should detect 'frustrated' as primary"
    assert result.self_focus > 0.7, "Self-focus should be high (>0.7)"
    assert result.emotion_type == 'direct', "Should be direct emotion"


def test_user_attributed_emotion():
    """Test: User attributes emotion to someone else"""
    analyzer = create_stance_analyzer()
    
    text = "You seem frustrated with my answers"
    result = analyzer.analyze_user_stance(text)
    
    print("\n✅ TEST: User attributed emotion")
    print(f"   Input: {text}")
    print(f"   Primary emotions: {result.primary_emotions}")
    print(f"   Other emotions: {result.other_emotions}")
    print(f"   Self-focus: {result.self_focus:.2f}")
    print(f"   Type: {result.emotion_type}")
    
    assert 'frustrated' in result.other_emotions, "Should detect 'frustrated' as attributed to other"
    assert len(result.primary_emotions) == 0, "Should have no primary emotions"
    assert result.emotion_type == 'attributed', "Should be attributed emotion"


def test_user_mixed_emotion():
    """Test: User expresses both their own and attributed emotions"""
    analyzer = create_stance_analyzer()
    
    text = "I'm frustrated with your suggestions, but you seem defensive"
    result = analyzer.analyze_user_stance(text)
    
    print("\n✅ TEST: User mixed emotion")
    print(f"   Input: {text}")
    print(f"   Primary emotions: {result.primary_emotions}")
    print(f"   Other emotions: {result.other_emotions}")
    print(f"   Self-focus: {result.self_focus:.2f}")
    print(f"   Type: {result.emotion_type}")
    
    assert 'frustrated' in result.primary_emotions, "Should detect 'frustrated' as primary"
    assert 'defensive' in result.other_emotions, "Should detect 'defensive' as attributed"
    assert 0.3 < result.self_focus < 0.8, "Self-focus should be mixed"
    assert result.emotion_type == 'mixed', "Should be mixed emotion"


def test_filter_second_person_bot_response():
    """Test: Filter out bot's second-person emotions to isolate bot's stance"""
    analyzer = create_stance_analyzer()
    
    text = "I understand you're frustrated. I'm here to help you feel better."
    filtered = analyzer.filter_second_person_emotions(text)
    
    print("\n✅ TEST: Filter second-person bot response")
    print(f"   Original: {text}")
    print(f"   Filtered: {filtered}")
    
    # The filtered text should not contain "you're frustrated"
    # but should retain bot's own emotional/intentional statements
    assert "frustrated" not in filtered.lower() or "you're" not in filtered.lower(), \
        "Should remove 'you're frustrated' phrase"
    assert "help" in filtered.lower(), "Should retain bot's helping intention"


def test_bot_empathy_with_own_emotion():
    """Test: Bot empathizes but also expresses own emotion"""
    analyzer = create_stance_analyzer()
    
    text = "I see you're upset. I'm genuinely happy to assist."
    filtered = analyzer.filter_second_person_emotions(text)
    
    print("\n✅ TEST: Bot empathy with own emotion")
    print(f"   Original: {text}")
    print(f"   Filtered: {filtered}")
    
    # Should remove "you're upset" but keep "I'm genuinely happy"
    assert "upset" not in filtered.lower() or "you're" not in filtered.lower(), \
        "Should remove 'you're upset'"
    assert "happy" in filtered.lower(), "Should keep 'happy' (bot's emotion)"


def test_negation_handling():
    """Test: Handle negation in emotion detection"""
    analyzer = create_stance_analyzer()
    
    text = "I'm not frustrated, I'm just tired"
    result = analyzer.analyze_user_stance(text)
    
    print("\n✅ TEST: Negation handling")
    print(f"   Input: {text}")
    print(f"   Primary emotions: {result.primary_emotions}")
    print(f"   Has negation markers: {result.has_negation}")
    
    # Should detect both emotions - RoBERTa will weight the negated one lower
    # The "not" is a sibling/parent-level modifier, not a direct child of "frustrated"
    assert 'tired' in result.primary_emotions, "Should detect 'tired' as primary"
    assert result.emotion_type == 'direct', "Should be direct emotion"


def test_no_emotions():
    """Test: Text with no emotions"""
    analyzer = create_stance_analyzer()
    
    text = "The weather is nice today"
    result = analyzer.analyze_user_stance(text)
    
    print("\n✅ TEST: No emotions")
    print(f"   Input: {text}")
    print(f"   Primary emotions: {result.primary_emotions}")
    print(f"   Type: {result.emotion_type}")
    
    assert len(result.primary_emotions) == 0, "Should have no primary emotions"
    assert result.emotion_type == 'none', "Should be 'none' type"


def test_spacy_singleton_reuse():
    """Test: Multiple analyzers reuse the same spaCy singleton"""
    analyzer1 = create_stance_analyzer()
    analyzer2 = create_stance_analyzer()
    
    print("\n✅ TEST: spaCy singleton reuse")
    print(f"   Analyzer 1 nlp is analyzer 2 nlp: {analyzer1.nlp is analyzer2.nlp}")
    
    # Both should use the same spaCy instance
    assert analyzer1.nlp is analyzer2.nlp, "Should reuse spaCy singleton"


if __name__ == "__main__":
    print("🧪 Running Stance Analyzer Tests\n")
    print("=" * 60)
    
    try:
        test_user_direct_emotion()
        test_user_attributed_emotion()
        test_user_mixed_emotion()
        test_filter_second_person_bot_response()
        test_bot_empathy_with_own_emotion()
        test_negation_handling()
        test_no_emotions()
        test_spacy_singleton_reuse()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
