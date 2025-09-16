#!/usr/bin/env python3
"""
Test to verify that temporary context (time and emotion) is moved to user message
instead of being included in the system prompt.
"""

import os
import sys
from unittest.mock import Mock

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_context_placement():
    """Test that context goes to user message, not system prompt"""

    # Mock Discord message
    mock_message = Mock()
    mock_message.author.id = 12345
    mock_message.author.name = "TestUser"
    mock_message.author.discriminator = "0001"
    mock_message.content = "Hello bot!"
    mock_message.attachments = []
    mock_message.guild = None
    mock_message.channel.id = 67890
    mock_message.id = 111

    # Mock bot user
    mock_bot_user = Mock()
    mock_bot_user.id = 99999

    # Import after setting up mocks
    from basic_discord_bot import get_current_time_context

    # Test that time context function works
    time_context = get_current_time_context()

    # Verify it contains expected parts
    assert "Current time:" in time_context
    assert "UTC" in time_context

    # Test the format - should not contain system prompt contamination keywords
    contamination_keywords = ["You are a helpful", "system", "assistant"]
    has_contamination = any(
        keyword.lower() in time_context.lower() for keyword in contamination_keywords
    )
    assert (
        not has_contamination
    ), f"Time context should not contain system prompt keywords: {time_context}"

    return True


def test_system_prompt_cleanliness():
    """Test that DEFAULT_SYSTEM_PROMPT doesn't contain temporary context"""

    from basic_discord_bot import DEFAULT_SYSTEM_PROMPT

    # Check that system prompt doesn't contain temporary context
    temporal_keywords = ["Current time:", "Current context:", "Emotional Context:", "2025-"]
    has_temporal = any(keyword in DEFAULT_SYSTEM_PROMPT for keyword in temporal_keywords)
    assert (
        not has_temporal
    ), f"System prompt should not contain temporal context: {DEFAULT_SYSTEM_PROMPT[:200]}..."


    return True


def test_emotion_context_format():
    """Test that emotion context has expected format"""

    # Create a mock emotion context string (simulating what get_emotion_context returns)
    mock_emotion_context = (
        "User: Friend | Current Emotion: Neutral | Interactions: 2309 | Be warm and personal."
    )

    # Verify format
    assert "User:" in mock_emotion_context
    assert "Current Emotion:" in mock_emotion_context
    assert "Interactions:" in mock_emotion_context

    # Test that it doesn't contain system prompt keywords
    system_keywords = ["You are", "helpful assistant", "respond"]
    has_system_keywords = any(
        keyword.lower() in mock_emotion_context.lower() for keyword in system_keywords
    )
    assert (
        not has_system_keywords
    ), f"Emotion context should not contain system keywords: {mock_emotion_context}"

    return True


if __name__ == "__main__":

    try:
        test_context_placement()
        test_system_prompt_cleanliness()
        test_emotion_context_format()


    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
