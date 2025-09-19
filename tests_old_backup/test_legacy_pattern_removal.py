#!/usr/bin/env python3
"""
Test to verify that the legacy context-in-user-message pattern has been removed
and that we now only use clean system messages for context.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re


def test_no_legacy_context_patterns():
    """Test that we no longer create user messages with embedded context"""

    # Read the bot file to check for problematic patterns
    with open("basic_discord_bot.py") as f:
        bot_code = f.read()

    # Check for problematic patterns that indicate context being embedded in user messages
    problematic_patterns = [
        r"role.*user.*Context from previous conversations",
        r"conversation_context.*append.*user.*\[Context",
        r"role.*user.*content.*Context:",
    ]

    issues_found = []

    for pattern in problematic_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        if matches:
            issues_found.extend(matches)

    if issues_found:
        return False
    else:
        pass

    # Check that we have clean system message patterns
    good_patterns = [
        r"role.*system.*content.*f.*User relationship and emotional context",
        r"role.*system.*content.*f.*Recent conversation summary",
        r"role.*system.*content.*memory_context",
        r"role.*system.*content.*DEFAULT_SYSTEM_PROMPT",
    ]

    system_patterns_found = 0
    for pattern in good_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        if matches:
            system_patterns_found += len(matches)

    if system_patterns_found >= 4:  # Should find multiple system message patterns
        return True
    else:
        return False


def test_conversation_context_structure():
    """Test that conversation context only contains proper system and user/assistant messages"""

    # This test would require mocking the entire message processing,
    # but we can check the structure by looking at the code patterns

    with open("basic_discord_bot.py") as f:
        bot_code = f.read()

    # Look for the system message creation patterns
    system_message_patterns = [
        'conversation_context.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})',
        'conversation_context.append({"role": "system", "content": f"Current time: {time_context}"})',
        'conversation_context.append({"role": "system", "content": f"User relationship and emotional context: {emotion_context}"})',
        'conversation_context.append({"role": "system", "content": memory_context})',
        'conversation_context.append({"role": "system", "content": f"Recent conversation summary: {conversation_summary}"})',
    ]

    found_patterns = 0
    for pattern in system_message_patterns:
        if pattern in bot_code:
            found_patterns += 1

    if found_patterns >= 4:  # Should find at least 4 of the 5 patterns
        return True
    else:
        return False


def test_no_context_message_updates():
    """Test that we no longer try to update context messages in user messages"""

    with open("basic_discord_bot.py") as f:
        bot_code = f.read()

    # Look for the old problematic update patterns
    update_patterns = [
        r"startswith\(.*Context from previous conversations",
        r"Update the context user message",
        r"Find the context message and update it",
        r"conversation_context\[i\].*=.*user.*content.*context_content",
    ]

    found_updates = 0
    for pattern in update_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        found_updates += len(matches)

    if found_updates == 0:
        return True
    else:
        return False


def test_memory_storage_safety():
    """Test that memory storage comments indicate proper filtering"""

    with open("basic_discord_bot.py") as f:
        bot_code = f.read()

    # Look for safety comments about preventing synthetic context storage
    safety_patterns = [
        "This prevents synthetic.*Context from previous conversations.*messages from polluting memory",
        "Only store the original user message content, not any synthetic context",
    ]

    found_safety = 0
    for pattern in safety_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        found_safety += len(matches)

    if found_safety >= 1:
        return True
    else:
        return False


if __name__ == "__main__":

    try:
        # Test that legacy patterns are removed
        test1_passed = test_no_legacy_context_patterns()

        # Test that we have proper system message structure
        test2_passed = test_conversation_context_structure()

        # Test that context update logic is removed
        test3_passed = test_no_context_message_updates()

        # Test memory storage safety
        test4_passed = test_memory_storage_safety()

        if test1_passed and test2_passed and test3_passed:

            pass

        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
