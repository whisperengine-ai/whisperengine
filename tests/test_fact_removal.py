#!/usr/bin/env python3
"""
Test script for the new fact removal functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import UserMemoryManager
import tempfile
import shutil


def test_fact_removal():
    """Test the fact removal functionality"""
    print("🧪 Testing Fact Removal Functionality")
    print("=" * 50)

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

        print("📝 Adding test facts...")
        for fact in test_facts:
            memory_manager.store_user_fact(test_user_id, fact)
            print(f"   ✅ Added: {fact}")

        # Test retrieving facts
        print("\n🔍 Testing fact retrieval...")
        memories = memory_manager.retrieve_relevant_memories(test_user_id, "cat", limit=10)
        cat_facts = [
            m
            for m in memories
            if m["metadata"].get("type") == "user_fact"
            and "cat" in m["metadata"].get("fact", "").lower()
        ]

        if cat_facts:
            print(f"   ✅ Found {len(cat_facts)} cat-related facts")
            cat_fact = cat_facts[0]
            print(f"   📄 Cat fact: {cat_fact['metadata'].get('fact')}")
            print(f"   🆔 Memory ID: {cat_fact.get('id')}")

            # Test removing the specific fact
            print("\n🗑️  Testing fact removal...")
            if memory_manager.delete_specific_memory(cat_fact["id"]):
                print("   ✅ Successfully deleted the cat fact")

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
                    print("   ✅ Fact was successfully removed from database")
                else:
                    print("   ❌ Fact removal may not have worked correctly")
            else:
                print("   ❌ Failed to delete the cat fact")
        else:
            print("   ❌ No cat facts found")

        # Test retrieving all remaining facts
        print("\n📊 Remaining facts:")
        all_memories = memory_manager.retrieve_relevant_memories(test_user_id, "user", limit=20)
        remaining_facts = [m for m in all_memories if m["metadata"].get("type") == "user_fact"]

        for i, fact in enumerate(remaining_facts, 1):
            print(f"   {i}. {fact['metadata'].get('fact')}")

        print(
            f"\n✅ Test completed! {len(remaining_facts)} facts remaining out of {len(test_facts)} original facts."
        )

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🧹 Cleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    test_fact_removal()
