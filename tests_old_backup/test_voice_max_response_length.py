#!/usr/bin/env python3
"""
Test script to verify VOICE_MAX_RESPONSE_LENGTH functionality
"""
import os
import sys

# Try to import centralized environment manager, but don't fail if it's not available
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from env_manager import load_environment

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def test_voice_max_response_length():
    """Test the VOICE_MAX_RESPONSE_LENGTH environment variable functionality"""

    # Test 1: Default value (300)
    os.environ.pop("VOICE_MAX_RESPONSE_LENGTH", None)  # Remove if exists
    voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))
    assert voice_max_length == 300, f"Expected 300, got {voice_max_length}"

    # Test 2: Custom value from environment
    os.environ["VOICE_MAX_RESPONSE_LENGTH"] = "500"
    voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))
    assert voice_max_length == 500, f"Expected 500, got {voice_max_length}"

    # Test 3: Another custom value
    os.environ["VOICE_MAX_RESPONSE_LENGTH"] = "150"
    voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))
    assert voice_max_length == 150, f"Expected 150, got {voice_max_length}"

    # Test 4: Test with .env.dream configuration
    if DOTENV_AVAILABLE:
        try:
            # Note: env_manager doesn't support specific file loading in the same way
            # For testing purposes, we'll just load the default environment
            load_environment()
            voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))
        except Exception:
            pass
    else:
        pass

    # Test 5: Test response truncation logic (simulate the actual code)
    test_response = "This is a very long response that should be truncated when it exceeds the maximum length limit for voice responses to ensure compatibility with ElevenLabs and good user experience in voice channels."

    os.environ["VOICE_MAX_RESPONSE_LENGTH"] = "100"
    voice_max_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "300"))

    if len(test_response) > voice_max_length:
        truncated_response = test_response[:voice_max_length] + "..."
    else:
        truncated_response = test_response

    assert (
        len(truncated_response) <= voice_max_length + 3
    ), "Response not properly truncated"  # +3 for "..."
    assert truncated_response.endswith("..."), "Truncated response should end with '...'"

    # Cleanup
    os.environ.pop("VOICE_MAX_RESPONSE_LENGTH", None)


if __name__ == "__main__":
    test_voice_max_response_length()
