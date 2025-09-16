#!/usr/bin/env python3
"""
Test script to verify that duplicate global facts are prevented
"""

import logging

from memory_manager import UserMemoryManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_duplicate_prevention():
    """Test that duplicate global facts are not stored"""
    try:
        # Initialize memory manager
        memory_manager = UserMemoryManager()

        # Get current count of global facts
        initial_results = memory_manager.global_collection.get(where={"type": "global_fact"})
        initial_count = len(initial_results["documents"])

        # Try to add the same Discord user info that should already exist
        test_fact1 = "Discord user markanthony.art has Discord ID 672814231002939413"
        test_fact2 = (
            "Discord user markanthony.art (ID: 672814231002939413) uses display name 'MarkAnthony'"
        )

        memory_manager.store_global_fact(
            test_fact1,
            "User identification mapping for Discord bot interactions",
            added_by="test_script",
        )

        memory_manager.store_global_fact(
            test_fact2, "Display name information for Discord user", added_by="test_script"
        )

        # Check if count increased (it shouldn't)
        final_results = memory_manager.global_collection.get(where={"type": "global_fact"})
        final_count = len(final_results["documents"])

        if final_count == initial_count:
            return True
        else:
            return False

    except Exception:
        return False


if __name__ == "__main__":
    success = test_duplicate_prevention()
    if not success:
        exit(1)
