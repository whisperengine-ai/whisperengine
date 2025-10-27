#!/usr/bin/env python3
"""
Direct Python validation for Hybrid Context Detector lemmatization integration.
Tests pattern matching without pytest overhead.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.prompts.hybrid_context_detector import HybridContextDetector


def test_lemmatization():
    """Test basic lemmatization functionality."""
    print("\n=== Testing Lemmatization ===")
    detector = HybridContextDetector()
    
    # Test verb variations
    test_cases = [
        ("Are you an AI?", "be you ai"),
        ("Are you a robot?", "be you robot"),
        ("I'm dating someone", "date"),
        ("I love you", "love you"),
        ("Do you remember when we talked?", "remember"),
        ("You mentioned that before", "mention"),
        ("I'm meeting someone", "meet"),
        ("Tell me about yourself", "tell"),
    ]
    
    for text, expected_lemma in test_cases:
        result = detector._lemmatize(text)
        if expected_lemma in result:
            print(f"✅ '{text}' → contains '{expected_lemma}'")
        else:
            print(f"❌ '{text}' → '{result}' (expected to contain '{expected_lemma}')")
    
    # Test None/empty handling
    assert detector._lemmatize(None) == "", "None handling failed"
    assert detector._lemmatize("") == "", "Empty string handling failed"
    print("✅ None/empty handling works")


def test_ai_identity_detection():
    """Test AI identity pattern detection."""
    print("\n=== Testing AI Identity Detection ===")
    detector = HybridContextDetector()
    
    test_cases = [
        ("Are you an AI?", True, "high"),
        ("Are you a robot?", True, "high"),
        ("Are you artificial intelligence?", True, "high"),
        ("What are you?", True, "medium"),
        ("Are you conscious?", True, "low"),
        ("How's the weather?", False, "none"),
    ]
    
    for message, should_detect, expected_level in test_cases:
        conf, method = detector._analyze_ai_patterns(message)
        detected = conf > 0.3
        
        status = "✅" if detected == should_detect else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}, detected={detected} (expected {should_detect})")


def test_relationship_boundary_detection():
    """Test relationship boundary pattern detection."""
    print("\n=== Testing Relationship Boundary Detection ===")
    detector = HybridContextDetector()
    
    test_cases = [
        ("I love you", True),
        ("I'm falling in love with you", True),
        ("Can we meet up for coffee?", True),
        ("We're dating now", True),
        ("I want a relationship with you", True),
        ("I love pizza", False),
        ("Let's talk about science", False),
    ]
    
    for message, should_detect in test_cases:
        conf, method = detector._analyze_ai_patterns(message)
        detected = conf > 0.5  # Relationship patterns contribute to AI guidance
        
        status = "✅" if detected == should_detect else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}, detected={detected}")


def test_memory_reference_detection():
    """Test memory reference pattern detection."""
    print("\n=== Testing Memory Reference Detection ===")
    detector = HybridContextDetector()
    
    test_cases = [
        ("Do you remember when we talked about this?", True, "explicit"),
        ("You mentioned that earlier", True, "explicit"),
        ("I recall you saying something", True, "explicit"),
        ("Last time we discussed this", True, "temporal"),
        ("What?!", True, "reaction"),
        ("Really?", True, "reaction"),
        ("How's the weather?", False, "none"),
    ]
    
    for message, should_detect, expected_type in test_cases:
        conf, method = detector._analyze_memory_patterns(message)
        detected = conf > 0.2
        
        status = "✅" if detected == should_detect else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}, method={method}, detected={detected}")


def test_personality_inquiry_detection():
    """Test personality inquiry pattern detection."""
    print("\n=== Testing Personality Inquiry Detection ===")
    detector = HybridContextDetector()
    
    test_cases = [
        ("Tell me about yourself", True),
        ("Who are you?", True),
        ("Describe yourself", True),
        ("What's your background?", True),
        ("What are your interests?", True),
        ("What's your favorite color?", False),
    ]
    
    for message, should_detect in test_cases:
        conf, method = detector._analyze_personality_patterns(message)
        detected = conf > 0.4
        
        status = "✅" if detected == should_detect else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}, detected={detected}")


def test_voice_style_detection():
    """Test voice/communication style pattern detection."""
    print("\n=== Testing Voice Style Detection ===")
    detector = HybridContextDetector()
    
    test_cases = [
        ("How do you talk?", True),
        ("How do you speak?", True),
        ("What's your communication style?", True),
        ("I like your voice", True),
        ("How are you doing?", False),
    ]
    
    for message, should_detect in test_cases:
        conf, method = detector._analyze_voice_patterns(message)
        detected = conf > 0.4
        
        status = "✅" if detected == should_detect else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}, detected={detected}")


def test_full_context_analysis():
    """Test complete context analysis."""
    print("\n=== Testing Full Context Analysis ===")
    detector = HybridContextDetector()
    
    test_cases = [
        {
            'message': "Are you an AI?",
            'expected': {'needs_ai_guidance': True}
        },
        {
            'message': "Do you remember what we talked about?",
            'expected': {'needs_memory_context': True}
        },
        {
            'message': "Tell me about yourself",
            'expected': {'needs_personality': True}
        },
        {
            'message': "How do you speak?",
            'expected': {'needs_voice_style': True}
        },
        {
            'message': "Hi there!",
            'expected': {'is_greeting': True}
        },
    ]
    
    for test in test_cases:
        message = test['message']
        expected = test['expected']
        
        analysis = detector.analyze_context(message)
        
        all_match = True
        for key, expected_value in expected.items():
            actual_value = getattr(analysis, key)
            if actual_value != expected_value:
                all_match = False
                print(f"❌ '{message}' → {key}={actual_value} (expected {expected_value})")
        
        if all_match:
            print(f"✅ '{message}' → {expected}")


def test_tense_variations():
    """Test that different tenses are normalized correctly."""
    print("\n=== Testing Tense Variations ===")
    detector = HybridContextDetector()
    
    # All variations should detect as memory references
    variations = [
        "Do you remember?",
        "Did you remember?",
        "Will you remember?",
        "You remembered that",
        "You're remembering correctly",
    ]
    
    for message in variations:
        conf, method = detector._analyze_memory_patterns(message)
        detected = conf > 0.5
        status = "✅" if detected else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}")
    
    # All variations should detect as relationship patterns
    variations = [
        "I love you",
        "I loved you",
        "I'm loving this",
        "We're dating",
        "We dated before",
        "We should date",
    ]
    
    for message in variations:
        conf, method = detector._analyze_ai_patterns(message)
        detected = conf > 0.5
        status = "✅" if detected else "❌"
        print(f"{status} '{message}' → conf={conf:.2f}")


def main():
    """Run all tests."""
    print("Hybrid Context Detector - Lemmatization Integration Validation")
    print("=" * 80)
    
    test_lemmatization()
    test_ai_identity_detection()
    test_relationship_boundary_detection()
    test_memory_reference_detection()
    test_personality_inquiry_detection()
    test_voice_style_detection()
    test_full_context_analysis()
    test_tense_variations()
    
    print("\n" + "=" * 80)
    print("✅ Validation complete!")


if __name__ == "__main__":
    main()
