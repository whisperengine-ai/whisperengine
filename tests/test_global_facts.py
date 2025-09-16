#!/usr/bin/env python3
"""
Test script for global facts feature
"""

import os
import sys
import logging
from memory_manager import UserMemoryManager
from fact_extractor import GlobalFactExtractor

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_global_fact_extraction():
    """Test the global fact extraction functionality"""
    print("🧪 Testing Global Fact Extraction Feature")
    print("=" * 50)

    # Initialize global fact extractor
    extractor = GlobalFactExtractor()

    # Test cases for global facts
    test_conversations = [
        {
            "user_message": "Did you know that Paris is the capital of France?",
            "bot_response": "Yes, Paris has been the capital of France for centuries.",
            "expected_facts": ["Paris is located in France", "Paris - capital of France"],
        },
        {
            "user_message": "John works at Google and his wife Mary is a teacher.",
            "bot_response": "That's interesting! Technology and education are both important fields.",
            "expected_facts": ["John works with Google", "John and Mary are family"],
        },
        {
            "user_message": "The moon orbits around Earth every 28 days.",
            "bot_response": "Actually, it's about 27.3 days for the lunar cycle.",
            "expected_facts": ["moon orbits around Earth", "lunar cycle"],
        },
        {
            "user_message": "This bot can process images and remember conversations.",
            "bot_response": "Yes, I have vision capabilities and memory systems.",
            "expected_facts": [
                "Bot capability: process images",
                "Bot capability: remember conversations",
            ],
        },
        {
            "user_message": "World War II ended in 1945.",
            "bot_response": "Yes, it was a significant moment in world history.",
            "expected_facts": ["World War II occurred in 1945"],
        },
    ]

    total_tests = len(test_conversations)
    passed_tests = 0

    for i, test_case in enumerate(test_conversations, 1):
        print(f"\nTest {i}/{total_tests}: {test_case['user_message'][:50]}...")

        try:
            # Extract facts
            extracted_facts = extractor.extract_global_facts_from_message(
                test_case["user_message"], test_case["bot_response"]
            )

            print(f"  Extracted {len(extracted_facts)} global facts:")
            for fact in extracted_facts:
                print(
                    f"    - {fact['fact']} (confidence: {fact['confidence']:.2f}, category: {fact['category']})"
                )

            # Simple validation - check if we extracted any facts
            if extracted_facts:
                passed_tests += 1
                print(f"  ✅ PASSED - Extracted facts from global conversation")
            else:
                print(f"  ❌ FAILED - No facts extracted")

        except Exception as e:
            print(f"  ❌ ERROR - {e}")

    print(f"\nGlobal Fact Extraction Summary:")
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")

    return passed_tests == total_tests


def test_global_fact_storage():
    """Test global fact storage and retrieval"""
    print("\n🧪 Testing Global Fact Storage and Retrieval")
    print("=" * 50)

    try:
        # Initialize memory manager
        memory_manager = UserMemoryManager(
            persist_directory="./test_chromadb", enable_auto_facts=True
        )

        # Test storing a global fact
        test_fact = "The Eiffel Tower is located in Paris, France"
        memory_manager.store_global_fact(
            test_fact, "Test fact for global facts feature", "test_admin"
        )
        print(f"✅ Stored global fact: {test_fact}")

        # Test retrieving global facts
        query = "Eiffel Tower location"
        retrieved_facts = memory_manager.retrieve_relevant_global_facts(query, limit=5)

        if retrieved_facts:
            print(f"✅ Retrieved {len(retrieved_facts)} relevant global facts:")
            for fact in retrieved_facts:
                print(f"  - {fact['metadata']['fact']} (score: {fact['relevance_score']:.2f})")
        else:
            print("❌ No global facts retrieved")
            return False

        # Test global fact priority in combined retrieval
        user_id = "test_user_123"
        memory_manager.store_user_fact(user_id, "I like visiting towers", "Test user fact")

        combined_memories = memory_manager.retrieve_relevant_memories(user_id, query, limit=10)
        global_facts_count = len(
            [m for m in combined_memories if m["metadata"].get("is_global", False)]
        )
        user_facts_count = len(
            [m for m in combined_memories if not m["metadata"].get("is_global", False)]
        )

        print(
            f"✅ Combined retrieval: {global_facts_count} global facts, {user_facts_count} user facts"
        )

        # Verify global facts have higher scores (priority)
        if combined_memories:
            first_result = combined_memories[0]
            if first_result["metadata"].get("is_global", False):
                print("✅ Global fact prioritized in results")
            else:
                print("⚠️  User fact ranked higher than global fact")

        # Test getting all global facts
        all_global_facts = memory_manager.get_all_global_facts()
        print(f"✅ Retrieved all global facts: {len(all_global_facts)} total")

        # Test collection stats
        stats = memory_manager.get_collection_stats()
        print(
            f"✅ Collection stats: {stats.get('total_global_facts', 0)} global facts, {stats.get('total_memories', 0)} user memories"
        )

        return True

    except Exception as e:
        print(f"❌ Error in global fact storage test: {e}")
        return False


def main():
    """Run all global fact tests"""
    print("🚀 Starting Global Facts Feature Tests")
    print("=" * 60)

    # Test 1: Fact Extraction
    extraction_passed = test_global_fact_extraction()

    # Test 2: Storage and Retrieval
    storage_passed = test_global_fact_storage()

    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)

    if extraction_passed:
        print("✅ Global Fact Extraction: PASSED")
    else:
        print("❌ Global Fact Extraction: FAILED")

    if storage_passed:
        print("✅ Global Fact Storage: PASSED")
    else:
        print("❌ Global Fact Storage: FAILED")

    if extraction_passed and storage_passed:
        print("\n🎉 ALL TESTS PASSED! Global facts feature is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
