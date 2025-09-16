#!/usr/bin/env python3
"""
Show remaining facts for a user after cleanup
"""
import logging

from memory_manager import UserMemoryManager

logging.basicConfig(level=logging.INFO)


def show_user_facts(user_id: str):
    """Show all facts for a specific user"""
    try:
        memory_manager = UserMemoryManager()

        # Get all entries for this user
        results = memory_manager.collection.get(where={"user_id": user_id})

        if not results["documents"]:
            return


        fact_count = 0
        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]

            # Only show user facts
            if metadata.get("type") == "user_fact":
                metadata.get("fact", doc)
                metadata.get("confidence", "unknown")
                metadata.get("timestamp", "unknown")
                fact_count += 1

        if fact_count == 0:
            pass
        else:
            pass

    except Exception:
        pass


if __name__ == "__main__":
    user_id = input("Enter user ID: ").strip()
    show_user_facts(user_id)
