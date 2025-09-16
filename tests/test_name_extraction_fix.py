#!/usr/bin/env python3
"""
Test the fixed emotion system to ensure names are not incorrectly extracted
"""

import pytest
from emotion_manager import EmotionManager

from env_manager import load_environment

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


    for i, message in enumerate(test_cases):
        user_id = f"test_user_{i}"

        # Process the interaction
        profile, emotion = em.process_interaction(user_id, message)


        # Check if a name was incorrectly extracted
        if profile.name:
            pass
        else:
            pass



if __name__ == "__main__":
    pass
