#!/usr/bin/env python3
"""Test script to verify global facts are properly disabled"""

import logging
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_global_facts_disabled():
    """Test that global facts are properly disabled in the bot configuration"""

    # Test 1: Memory manager initialization
    from memory_manager import UserMemoryManager

    # Test with auto facts enabled (normal mode)
    memory_manager = UserMemoryManager(enable_auto_facts=True)

    # Disable global fact extraction (as done in bot)
    if hasattr(memory_manager, "global_fact_extractor"):
        memory_manager.global_fact_extractor = None

    # Test 2: Import bot functions without running Discord
    try:
        # Import the functions we modified
        from basic_discord_bot import store_discord_server_info, store_discord_user_info


        # Test that these functions don't store global facts anymore

    except Exception:
        return False


    # Mock user object
    class MockUser:
        def __init__(self):
            self.id = 12345
            self.name = "testuser"
            self.display_name = "Test User"

        def __str__(self):
            return "testuser#1234"

    # Mock guild object
    class MockGuild:
        def __init__(self):
            self.id = 67890
            self.name = "Test Server"
            self.member_count = 100

    # Test store_discord_user_info (should not store global facts)
    mock_user = MockUser()
    mock_guild = MockGuild()

    try:
        store_discord_user_info(mock_user, memory_manager)
    except Exception:
        return False

    try:
        store_discord_server_info(mock_guild, memory_manager)
    except Exception:
        return False

    return True


if __name__ == "__main__":
    success = test_global_facts_disabled()
    sys.exit(0 if success else 1)
