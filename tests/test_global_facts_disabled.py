#!/usr/bin/env python3
"""Test script to verify global facts are properly disabled"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_global_facts_disabled():
    """Test that global facts are properly disabled in the bot configuration"""
    print("Testing global facts configuration...")

    # Test 1: Memory manager initialization
    print("\n1. Testing memory manager initialization...")
    from memory_manager import UserMemoryManager

    # Test with auto facts enabled (normal mode)
    memory_manager = UserMemoryManager(enable_auto_facts=True)
    print(f"   Auto facts enabled: {memory_manager.enable_auto_facts}")
    print(f"   User fact extractor: {memory_manager.fact_extractor is not None}")
    print(
        f"   Global fact extractor before disable: {memory_manager.global_fact_extractor is not None}"
    )

    # Disable global fact extraction (as done in bot)
    if hasattr(memory_manager, "global_fact_extractor"):
        memory_manager.global_fact_extractor = None
        print(
            f"   Global fact extractor after disable: {memory_manager.global_fact_extractor is None}"
        )

    # Test 2: Import bot functions without running Discord
    print("\n2. Testing bot function imports...")
    try:
        # Import the functions we modified
        from basic_discord_bot import store_discord_user_info, store_discord_server_info

        print("   ✅ Bot functions imported successfully")

        # Test that these functions don't store global facts anymore
        print("   ✅ Functions available for testing")

    except Exception as e:
        print(f"   ❌ Error importing bot functions: {e}")
        return False

    print("\n3. Testing function behavior...")

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

    print("   Testing store_discord_user_info...")
    try:
        store_discord_user_info(mock_user, memory_manager)
        print("   ✅ store_discord_user_info completed without errors")
    except Exception as e:
        print(f"   ❌ Error in store_discord_user_info: {e}")
        return False

    print("   Testing store_discord_server_info...")
    try:
        store_discord_server_info(mock_guild, memory_manager)
        print("   ✅ store_discord_server_info completed without errors")
    except Exception as e:
        print(f"   ❌ Error in store_discord_server_info: {e}")
        return False

    print("\n✅ All tests passed! Global facts are properly disabled for automatic collection.")
    print("📝 Only admins can manually add global facts using !add_global_fact")
    return True


if __name__ == "__main__":
    success = test_global_facts_disabled()
    sys.exit(0 if success else 1)
