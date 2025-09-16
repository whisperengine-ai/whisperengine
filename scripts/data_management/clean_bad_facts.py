#!/usr/bin/env python3
"""
Clean up inappropriate facts from the memory system
"""
import logging
import re
from typing import List
from memory_manager import UserMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_bad_fact(fact_text: str) -> bool:
    """Check if a fact should be removed because it's temporary/inappropriate"""
    if not fact_text:
        return True

    fact_lower = fact_text.lower()

    # Patterns for bad facts to remove
    bad_patterns = [
        # Temporary emotional states
        r"\b(is|am|was|were)\s+(feeling|feel)\s+",
        r"\b(is|am|was|were)\s+(happy|sad|angry|calm|excited|tired|stressed|worried|anxious|frustrated|upset|nervous|annoyed)\b",
        # Conversational context
        r"\b(is|am|was|were)\s+(asking|wondering|saying|telling|responding|replying)\b",
        r"\buser\s+(is|was)\s+(asking|wondering|saying)\b",
        # Immediate intentions/plans
        r"\b(is|am|was|were)\s+going\s+to\b",
        r"\b(will|planning\s+to|about\s+to)\b",
        # Temporal qualifiers
        r"\b(currently|right\s+now|at\s+the\s+moment|today|this\s+morning|this\s+afternoon|tonight|just|recently|yesterday)\b",
        # Question artifacts
        r"\bfor\s+their\s+name\b",
        r"\babout\s+their\s+name\b",
    ]

    # Check if any bad pattern matches
    for pattern in bad_patterns:
        if re.search(pattern, fact_lower):
            return True

    # Additional specific bad fact patterns
    specific_bad_facts = [
        "the user is feeling",
        "i am feeling",
        "i am calm",
        "i am happy",
        "i am sad",
        "the user is asking",
        "i am going to listen",
        "i am going to",
        "the user is going to",
        "user is asking for their name",
        "asking for their name",
    ]

    for bad_fact in specific_bad_facts:
        if bad_fact in fact_lower:
            return True

    return False


def clean_user_facts(memory_manager: UserMemoryManager, user_id: str) -> int:
    """Clean bad facts for a specific user"""
    try:
        # Get all entries for this user
        results = memory_manager.collection.get(where={"user_id": user_id})

        if not results["documents"]:
            logger.info(f"No entries found for user {user_id}")
            return 0

        # Find user facts that are bad
        bad_fact_ids = []
        bad_facts = []

        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]
            doc_id = results["ids"][i]

            # Only process user facts
            if metadata.get("type") == "user_fact":
                fact_text = metadata.get("fact", doc)
                if is_bad_fact(fact_text):
                    bad_fact_ids.append(doc_id)
                    bad_facts.append(fact_text)

        if not bad_facts:
            logger.info(f"No bad facts found for user {user_id}")
            return 0

        logger.info(f"Found {len(bad_facts)} bad facts to remove for user {user_id}:")
        for fact in bad_facts:
            logger.info(f"  - {fact}")

        # Remove bad facts from ChromaDB
        if bad_fact_ids:
            memory_manager.collection.delete(ids=bad_fact_ids)
            logger.info(f"Removed {len(bad_fact_ids)} bad facts for user {user_id}")

        return len(bad_fact_ids)

    except Exception as e:
        logger.error(f"Error cleaning facts for user {user_id}: {e}")
        return 0


def clean_all_users(memory_manager: UserMemoryManager) -> int:
    """Clean bad facts for all users"""
    total_removed = 0

    try:
        # Get all entries from the collection
        results = memory_manager.collection.get()

        if not results["documents"]:
            logger.info("No entries found in memory system")
            return 0

        # Get unique user IDs
        user_ids = set()
        for metadata in results["metadatas"]:
            if "user_id" in metadata:
                user_ids.add(metadata["user_id"])

        if not user_ids:
            logger.info("No user IDs found in memory system")
            return 0

        logger.info(f"Cleaning facts for {len(user_ids)} users...")

        for user_id in user_ids:
            removed = clean_user_facts(memory_manager, user_id)
            total_removed += removed

        logger.info(f"Total facts removed across all users: {total_removed}")

    except Exception as e:
        logger.error(f"Error cleaning all users: {e}")

    return total_removed


def main():
    """Main function to clean up bad facts"""
    print("🧹 Cleaning up inappropriate facts from memory system...")

    try:
        # Initialize memory manager
        memory_manager = UserMemoryManager(
            persist_directory="./chromadb_data", enable_auto_facts=True, enable_emotions=True
        )

        # Option to clean specific user or all users
        user_input = input("Enter user ID to clean (or 'all' for all users): ").strip()

        if user_input.lower() == "all":
            total_removed = clean_all_users(memory_manager)
            print(f"\n✅ Cleanup complete! Removed {total_removed} inappropriate facts.")
        else:
            removed = clean_user_facts(memory_manager, user_input)
            print(
                f"\n✅ Cleanup complete! Removed {removed} inappropriate facts for user {user_input}."
            )

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
