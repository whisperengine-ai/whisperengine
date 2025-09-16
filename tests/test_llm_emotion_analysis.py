#!/usr/bin/env python3
"""
Test script for LLM-based emotion analysis

This script tests the new LLM-based sentiment analysis system compared to the old pattern-based system.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient
from emotion_manager import SentimentAnalyzer, EmotionalState

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_emotion_analysis():
    """Test LLM-based emotion analysis with various messages"""

    # Initialize LLM client
    try:
        llm_client = LMStudioClient()
        print("✅ LLM Client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        print("Make sure LM Studio is running on localhost:1234")
        return False

    # Test messages with expected emotions
    test_messages = [
        ("I'm so excited about this new feature!", "excited"),
        ("This is really frustrating, nothing seems to work", "frustrated"),
        ("Thank you so much for your help, I really appreciate it", "grateful"),
        ("I'm worried about what might happen next", "worried"),
        ("That's absolutely amazing! I love it!", "happy"),
        ("I hate when things don't work as expected", "angry"),
        ("I'm feeling pretty sad about the situation", "sad"),
        ("I was hoping for something better than this", "disappointed"),
        ("How does this system actually work?", "curious"),
        ("The weather is nice today", "neutral"),
        ("Well, that's just fucking brilliant, isn't it?", "angry"),  # Sarcasm test
        (
            "I'm not angry, just disappointed in how this turned out",
            "disappointed",
        ),  # Complex emotion
    ]

    # Initialize LLM analyzer
    llm_analyzer = SentimentAnalyzer(llm_client=llm_client)

    print("\n" + "=" * 80)
    print("LLM EMOTION ANALYSIS TEST")
    print("=" * 80)

    for message, expected in test_messages:
        print(f'\n📝 Message: "{message}"')
        print(f"🎯 Expected: {expected}")

        # Test LLM-based analysis
        try:
            llm_result = llm_analyzer.analyze_emotion(message)
            print(f"🤖 LLM Analysis:")
            print(f"   Emotion: {llm_result.detected_emotion.value}")
            print(f"   Confidence: {llm_result.confidence:.2f}")
            print(f"   Intensity: {llm_result.intensity:.2f}")
            print(f"   Triggers: {llm_result.triggers[:2]}")  # Show first 2 triggers
        except Exception as e:
            print(f"❌ LLM Analysis failed: {e}")

        print("-" * 60)

    print("\n✅ Emotion analysis test completed!")
    return True


def test_direct_llm_emotion():
    """Test the LLM emotion analysis directly"""

    try:
        llm_client = LMStudioClient()

        test_message = "I'm absolutely thrilled about this new project, but also a bit nervous about the deadlines"

        print(f"\n🧪 Direct LLM Emotion Test:")
        print(f'Message: "{test_message}"')

        result = llm_client.analyze_emotion(test_message)

        print(f"\nResult: {result}")
        print(f"Primary Emotion: {result['primary_emotion']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Intensity: {result['intensity']}")
        print(f"Secondary Emotions: {result['secondary_emotions']}")
        print(f"Reasoning: {result['reasoning']}")

        return True

    except Exception as e:
        print(f"❌ Direct LLM test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting LLM-based Emotion Analysis Test")

    # Test direct LLM emotion analysis
    print("\n" + "=" * 50)
    print("DIRECT LLM EMOTION ANALYSIS TEST")
    print("=" * 50)
    test_direct_llm_emotion()

    # Test full emotion analysis system
    test_emotion_analysis()

    print("\n🎉 All tests completed!")
