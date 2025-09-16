#!/usr/bin/env python3
"""
Test script for the new fact removal functionality
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import shutil
import tempfile

from memory_manager import UserMemoryManager


def test_fact_removal():
    """Test the fact removal functionality"""

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize memory manager with temporary directory
        memory_manager = UserMemoryManager(persist_directory=temp_dir, enable_auto_facts=False)

        test_user_id = "123456789012345678"  # Discord-style numeric user ID

        # Add some test facts
        test_facts = [
            "loves pizza",
            "has a cat named Whiskers",
            "works as a software engineer",
            "lives in San Francisco",
            "plays guitar",
        ]

        for fact in test_facts:
            memory_manager.store_user_fact(test_user_id, fact)

        # Test retrieving facts
        memories = memory_manager.retrieve_relevant_memories(test_user_id, "cat", limit=10)
        cat_facts = [
            m
            for m in memories
            if m["metadata"].get("type") == "user_fact"
            and "cat" in m["metadata"].get("fact", "").lower()
        ]

        if cat_facts:
            cat_fact = cat_facts[0]

            # Test removing the specific fact
            if memory_manager.delete_specific_memory(cat_fact["id"]):

                # Verify it's gone
                memories_after = memory_manager.retrieve_relevant_memories(
                    test_user_id, "cat", limit=10
                )
                cat_facts_after = [
                    m
                    for m in memories_after
                    if m["metadata"].get("type") == "user_fact"
                    and "cat" in m["metadata"].get("fact", "").lower()
                ]

                if len(cat_facts_after) < len(cat_facts):
                    pass
                else:
                    pass
            else:
                pass
        else:
            pass

        # Test retrieving all remaining facts
        all_memories = memory_manager.retrieve_relevant_memories(test_user_id, "user", limit=20)
        remaining_facts = [m for m in all_memories if m["metadata"].get("type") == "user_fact"]

        for _i, fact in enumerate(remaining_facts, 1):
            pass


    except Exception:
        import traceback

        traceback.print_exc()

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_fact_removal()
