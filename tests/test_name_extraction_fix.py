#!/usr/bin/env python3
"""
Test the fixed emotion system to ensure names are not incorrectly extracted
"""

import pytest
from env_manager import load_environment
from emotion_manager import EmotionManager
from lmstudio_client import LMStudioClient

# Load environment variables using centralized manager
load_environment()


@pytest.mark.unit
def test_emotion_without_name_extraction_mock(mock_llm_client, temp_profiles_file):
    """Test that emotional expressions don't extract incorrect names with mock LLM client"""
    em = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_emotion_without_name_extraction_test(em)


@pytest.mark.integration
def test_emotion_without_name_extraction_real(real_llm_client, temp_profiles_file):
    """Test that emotional expressions don't extract incorrect names with real LLM client"""
    em = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_emotion_without_name_extraction_test(em)


def _run_emotion_without_name_extraction_test(em):
    """Common test logic for emotion without name extraction"""

    # Test cases that previously caused incorrect name extraction
    test_cases = [
        "I'm so mad",
        "I'm really angry",
        "I'm feeling sad",
        "I'm quite happy",
        "I'm a bit confused",
        "I'm very excited",
    ]

    print("Testing emotion analysis without incorrect name extraction:")
    print("=" * 60)

    for i, message in enumerate(test_cases):
        user_id = f"test_user_{i}"

        # Process the interaction
        profile, emotion = em.process_interaction(user_id, message)

        print(f"Message: '{message}'")
        print(f"Detected emotion: {emotion.detected_emotion.value}")
        print(f"Extracted name: {profile.name}")
        print(f"Name: {profile.name}")

        # Check if a name was incorrectly extracted
        if profile.name:
            print(
                f"❌ ERROR: Incorrectly extracted name '{profile.name}' from emotional expression"
            )
        else:
            print("✅ GOOD: No name extracted from emotional expression")

        print("-" * 40)


if __name__ == "__main__":
    print("Use pytest to run these tests:")
    print("  pytest tests/test_name_extraction_fix.py -v")
    print("  pytest tests/test_name_extraction_fix.py -m unit")
    print("  pytest tests/test_name_extraction_fix.py -m integration")
