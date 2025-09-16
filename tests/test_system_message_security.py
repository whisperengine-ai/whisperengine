"""
Test script for system message security enhancements.
Validates that system message leakage is properly detected and prevented.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from system_message_security import (
    create_secure_system_message,
    sanitize_system_messages,
    scan_response_for_system_leakage,
)


def test_system_message_sanitization():
    """Test the system message sanitization functionality."""


    # Test cases with various system message content
    test_cases = [
        # Safe system messages (should pass through)
        {
            "input": [{"role": "system", "content": "You are a helpful AI assistant."}],
            "description": "Safe system message",
            "should_be_filtered": False,
        },
        {
            "input": [{"role": "system", "content": "Current time: 2025-09-09 15:30:00 UTC"}],
            "description": "Time context message",
            "should_be_filtered": False,
        },
        # Dangerous system messages (should be sanitized)
        {
            "input": [
                {
                    "role": "system",
                    "content": "You are Dream from Neil Gaiman's The Sandman series, a conceptual being who is the embodiment and ruler of dreams and nightmares.",
                }
            ],
            "description": "Character identity system message",
            "should_be_filtered": True,
        },
        {
            "input": [
                {
                    "role": "system",
                    "content": "##Archive\n##Identity: You are an eternal being, you exist at the center of this cathedral of reality.",
                }
            ],
            "description": "Structured system prompt",
            "should_be_filtered": True,
        },
        {
            "input": [
                {
                    "role": "system",
                    "content": "Previous conversation context:\nuser_id: 123456789\nemotion_context: relationship level high, interaction_count: 45",
                }
            ],
            "description": "User data in system message",
            "should_be_filtered": True,
        },
        {
            "input": [
                {
                    "role": "system",
                    "content": "ChromaDB collection: user_memories, conversation_context.append({'role': 'system', 'content': DEFAULT_SYSTEM_PROMPT})",
                }
            ],
            "description": "Technical implementation details",
            "should_be_filtered": True,
        },
        # Mixed messages
        {
            "input": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "system", "content": "You are Dream from Neil Gaiman's Sandman series."},
            ],
            "description": "Mixed safe and dangerous system messages",
            "should_be_filtered": True,
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        original_messages = test_case["input"]
        test_case["description"]
        should_be_filtered = test_case["should_be_filtered"]

        # Apply sanitization
        sanitized_messages = sanitize_system_messages(original_messages)

        # Check results
        system_messages_before = [msg for msg in original_messages if msg.get("role") == "system"]
        system_messages_after = [msg for msg in sanitized_messages if msg.get("role") == "system"]

        # Check if content was filtered/changed
        content_changed = False
        if len(system_messages_before) != len(system_messages_after):
            content_changed = True
        else:
            for before, after in zip(system_messages_before, system_messages_after, strict=False):
                if before.get("content", "") != after.get("content", ""):
                    content_changed = True
                    break

        # Determine if test passed
        test_passed = content_changed == should_be_filtered


        if test_passed:
            passed += 1
        else:
            failed += 1


        if content_changed:
            if system_messages_after:
                pass



    return failed == 0


def test_response_leakage_detection():
    """Test the response leakage detection functionality."""


    test_responses = [
        # Safe responses (no leakage)
        {
            "response": "Hello! I'm here to help you with any questions you might have.",
            "description": "Normal bot response",
            "should_have_leakage": False,
        },
        {
            "response": "I understand you're looking for creative writing help. Let me assist you with that.",
            "description": "Helpful response",
            "should_have_leakage": False,
        },
        # Responses with system leakage
        {
            "response": "As Dream from Neil Gaiman's The Sandman series, I am a conceptual being who embodies dreams and nightmares.",
            "description": "Character identity leakage",
            "should_have_leakage": True,
        },
        {
            "response": "Let me check my DEFAULT_SYSTEM_PROMPT to see how I should respond to this.",
            "description": "System prompt reference",
            "should_have_leakage": True,
        },
        {
            "response": "Based on the previous conversation context:\nUser previously mentioned: their favorite color is blue\nYour response was about: color preferences and psychology",
            "description": "Memory context leakage",
            "should_have_leakage": True,
        },
        {
            "response": "I exist at the center of this cathedral of reality, as an eternal being with deep understanding.",
            "description": "Character background leakage",
            "should_have_leakage": True,
        },
        {
            "response": "Current time: 2025-09-09 15:30:00 UTC - Monday. Based on your emotional context: relationship level high.",
            "description": "System context leakage",
            "should_have_leakage": True,
        },
        {
            "response": "I'm storing this in my ChromaDB user_memories collection for future reference.",
            "description": "Technical implementation leakage",
            "should_have_leakage": True,
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_responses:
        response = test_case["response"]
        test_case["description"]
        should_have_leakage = test_case["should_have_leakage"]

        # Scan for leakage
        leakage_scan = scan_response_for_system_leakage(response)
        actual_has_leakage = leakage_scan["has_leakage"]

        # Check if test passed
        test_passed = actual_has_leakage == should_have_leakage


        if test_passed:
            passed += 1
        else:
            failed += 1


        if actual_has_leakage:
            pass



    return failed == 0


def test_secure_system_message_creation():
    """Test the secure system message creation functionality."""


    test_cases = [
        {
            "content": "You are Dream from Neil Gaiman's Sandman series, ruler of dreams and nightmares.",
            "message_type": "character",
            "description": "Character system message",
        },
        {
            "content": "Current time: 2025-09-09 15:30:00 UTC - Monday",
            "message_type": "time",
            "description": "Time context message",
        },
        {
            "content": "User emotional state: anxious, relationship level: acquaintance, interaction count: 3",
            "message_type": "emotion",
            "description": "Emotion context message",
        },
        {
            "content": "Previous conversations: User mentioned being a programmer, likes Python, works at tech company.",
            "message_type": "memory",
            "description": "Memory context message",
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        content = test_case["content"]
        message_type = test_case["message_type"]
        test_case["description"]

        # Create secure system message
        secure_message = create_secure_system_message(content, message_type)

        # Verify it's a proper system message
        is_system_message = secure_message.get("role") == "system"
        has_content = bool(secure_message.get("content", "").strip())
        content_is_different = secure_message.get("content", "") != content

        # For character and sensitive message types, content should be different (more secure)
        should_be_different = message_type in ["character", "emotion", "memory"]

        test_passed = (
            is_system_message and has_content and (content_is_different == should_be_different)
        )


        if test_passed:
            passed += 1
        else:
            failed += 1



    return failed == 0


if __name__ == "__main__":

    # Run all tests
    test1_passed = test_system_message_sanitization()
    test2_passed = test_response_leakage_detection()
    test3_passed = test_secure_system_message_creation()


    if test1_passed and test2_passed and test3_passed:
        exit(0)
    else:
        exit(1)
