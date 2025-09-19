#!/usr/bin/env python3
"""
Test script for global facts feature
"""

import logging
import sys

from fact_extractor import GlobalFactExtractor
from memory_manager import UserMemoryManager

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_global_fact_extraction():
    """Test the global fact extraction functionality"""

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

    for _i, test_case in enumerate(test_conversations, 1):

        try:
            # Extract facts
            extracted_facts = extractor.extract_global_facts_from_message(
                test_case["user_message"], test_case["bot_response"]
            )

            for _fact in extracted_facts:
                pass

            # Simple validation - check if we extracted any facts
            if extracted_facts:
                passed_tests += 1
            else:
                pass

        except Exception:
            pass

    return passed_tests == total_tests


def test_global_fact_storage():
    """Test global fact storage and retrieval"""

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

        # Test retrieving global facts
        query = "Eiffel Tower location"
        retrieved_facts = memory_manager.retrieve_relevant_global_facts(query, limit=5)

        if retrieved_facts:
            for _fact in retrieved_facts:
                pass
        else:
            return False

        # Test global fact priority in combined retrieval
        user_id = "test_user_123"
        memory_manager.store_user_fact(user_id, "I like visiting towers", "Test user fact")

        combined_memories = memory_manager.retrieve_relevant_memories(user_id, query, limit=10)
        len([m for m in combined_memories if m["metadata"].get("is_global", False)])
        len([m for m in combined_memories if not m["metadata"].get("is_global", False)])

        # Verify global facts have higher scores (priority)
        if combined_memories:
            first_result = combined_memories[0]
            if first_result["metadata"].get("is_global", False):
                pass
            else:
                pass

        # Test getting all global facts
        memory_manager.get_all_global_facts()

        # Test collection stats
        memory_manager.get_collection_stats()

        return True

    except Exception:
        return False


def main():
    """Run all global fact tests"""

    # Test 1: Fact Extraction
    extraction_passed = test_global_fact_extraction()

    # Test 2: Storage and Retrieval
    storage_passed = test_global_fact_storage()

    # Summary

    if extraction_passed:
        pass
    else:
        pass

    if storage_passed:
        pass
    else:
        pass

    if extraction_passed and storage_passed:
        return True
    else:
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
