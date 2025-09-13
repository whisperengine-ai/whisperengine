#!/usr/bin/env python3
"""
Test that legitimate name introductions still work after the fix
"""

import pytest
from env_manager import load_environment
from emotion_manager import EmotionManager
from lmstudio_client import LMStudioClient

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
        "Hi, my name is Jennifer"
    ]
    
    print("Testing legitimate name extraction:")
    print("=" * 50)
    
    for i, message in enumerate(test_cases):
        user_id = f"name_test_user_{i}"
        
        # Process the interaction
        profile, emotion = em.process_interaction(user_id, message)
        
        print(f"Message: '{message}'")
        print(f"Extracted name: {profile.name}")
        print(f"Name: {profile.name}")
        
        # Check if a name was correctly extracted
        if profile.name:
            print(f"✅ GOOD: Correctly extracted name '{profile.name}'")
        else:
            print("❌ ERROR: Failed to extract legitimate name")
        
        print("-" * 30)

if __name__ == "__main__":
    print("Use pytest to run these tests:")
    print("  pytest tests/test_legitimate_names.py -v")
    print("  pytest tests/test_legitimate_names.py -m unit")
    print("  pytest tests/test_legitimate_names.py -m integration")
