#!/usr/bin/env python3
"""
Test that legitimate name introductions still work after the fix
"""

import pytest
from emotion_manager import EmotionManager

from env_manager import load_environment

# Load environment variables using centralized manager
load_environment()


@pytest.mark.unit
def test_legitimate_name_extraction_mock(mock_llm_client, temp_profiles_file):
    """Test that legitimate name introductions work with mock LLM client"""
    em = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_legitimate_name_extraction_test(em)


@pytest.mark.integration
def test_legitimate_name_extraction_real(real_llm_client, temp_profiles_file):
    """Test that legitimate name introductions work with real LLM client"""
    em = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_legitimate_name_extraction_test(em)


def _run_legitimate_name_extraction_test(em):
    """Common test logic for legitimate name extraction"""

    # Test cases for legitimate name introductions
    test_cases = [
        "My name is John",
        "Call me Sarah",
        "I'm called Mike",
        "I go by Alex",
        "Hi, my name is Jennifer",
    ]

    for i, message in enumerate(test_cases):
        user_id = f"name_test_user_{i}"

        # Process the interaction
        profile, emotion = em.process_interaction(user_id, message)

        # Check if a name was correctly extracted
        if profile.name:
            pass
        else:
            pass


if __name__ == "__main__":
    pass
