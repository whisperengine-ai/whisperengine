#!/usr/bin/env python3
"""
Direct Python validation for Character Learning Moment Detector lemmatization integration.
Tests pattern matching without pytest overhead.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.characters.learning.character_learning_moment_detector import (
    CharacterLearningMomentDetector,
    LearningMomentContext
)


def test_lemmatization():
    """Test basic lemmatization functionality."""
    print("\n=== Testing Lemmatization ===")
    detector = CharacterLearningMomentDetector()
    
    # Test verb variations
    test_cases = [
        ("I'm growing so much", "grow"),
        ("I've grown a lot", "grow"),
        ("growth is important", "grow"),
        ("I'm changing", "change"),
        ("That changed me", "change"),
        ("I'm noticing patterns", "notice"),
        ("I noticed something", "notice"),
        ("Do you remember when", "remember"),
        ("I recall that", "recall"),
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


def test_pattern_matching():
    """Test pattern matching with trigger lists."""
    print("\n=== Testing Pattern Matching ===")
    detector = CharacterLearningMomentDetector()
    
    growth_tests = [
        ("I'm growing as a person", True),
        ("I've grown so much from this", True),
        ("This experience changed me", True),
        ("The weather is nice", False),
    ]
    
    observation_tests = [
        ("I've noticed that I always do this", True),
        ("I'm realizing something about myself", True),
        ("I tend to react this way", True),
        ("I like pizza", False),
    ]
    
    memory_tests = [
        ("Do you remember when we talked?", True),
        ("I recall you mentioning something", True),
        ("This reminds me of our conversation", True),
        ("What's the capital of France?", False),
    ]
    
    print("\nGrowth triggers:")
    for text, should_match in growth_tests:
        matches = detector._matches_trigger_pattern(text, detector.growth_triggers)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} '{text}' → {matches} (expected {should_match})")
    
    print("\nObservation triggers:")
    for text, should_match in observation_tests:
        matches = detector._matches_trigger_pattern(text, detector.observation_triggers)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} '{text}' → {matches} (expected {should_match})")
    
    print("\nMemory triggers:")
    for text, should_match in memory_tests:
        matches = detector._matches_trigger_pattern(text, detector.memory_triggers)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} '{text}' → {matches} (expected {should_match})")


async def test_detection_methods():
    """Test actual detection methods."""
    print("\n=== Testing Detection Methods ===")
    detector = CharacterLearningMomentDetector()
    
    base_context = {
        'user_id': 'test_user_123',
        'character_name': 'elena',
        'conversation_history': [],
        'temporal_data': None,
        'emotional_context': None,
        'episodic_memories': []
    }
    
    # Test growth insights
    context = LearningMomentContext(
        current_message="I'm growing as a person through these conversations",
        **base_context
    )
    moments = await detector._detect_growth_insights(context)
    print(f"Growth insight detection: {len(moments)} moments found")
    if moments:
        print(f"  → Trigger: {moments[0].supporting_data.get('trigger')}")
    
    # Test user observations
    context = LearningMomentContext(
        current_message="I've noticed that I always react this way",
        **base_context
    )
    moments = await detector._detect_user_observations(context)
    print(f"User observation detection: {len(moments)} moments found")
    if moments:
        print(f"  → Trigger: {moments[0].supporting_data.get('trigger')}")
    
    # Test memory surprises
    context = LearningMomentContext(
        current_message="Do you remember when we talked about marine biology?",
        **base_context
    )
    moments = await detector._detect_memory_surprises(context)
    print(f"Memory surprise detection: {len(moments)} moments found")
    if moments:
        print(f"  → Trigger: {moments[0].supporting_data.get('trigger')}")


async def main():
    """Run all tests."""
    print("Character Learning Moment Detector - Lemmatization Integration Validation")
    print("=" * 80)
    
    test_lemmatization()
    test_pattern_matching()
    await test_detection_methods()
    
    print("\n" + "=" * 80)
    print("✅ Validation complete!")


if __name__ == "__main__":
    asyncio.run(main())
