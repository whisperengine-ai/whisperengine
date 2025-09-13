#!/usr/bin/env python3
"""
Test script to verify that duplicate global facts are prevented
"""

import logging
from memory_manager import UserMemoryManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_duplicate_prevention():
    """Test that duplicate global facts are not stored"""
    try:
        # Initialize memory manager
        memory_manager = UserMemoryManager()
        
        # Get current count of global facts
        initial_results = memory_manager.global_collection.get(
            where={"type": "global_fact"}
        )
        initial_count = len(initial_results['documents'])
        print(f"Initial global facts count: {initial_count}")
        
        # Try to add the same Discord user info that should already exist
        test_fact1 = "Discord user markanthony.art has Discord ID 672814231002939413"
        test_fact2 = "Discord user markanthony.art (ID: 672814231002939413) uses display name 'MarkAnthony'"
        
        print(f"Attempting to store duplicate fact 1: {test_fact1}")
        memory_manager.store_global_fact(
            test_fact1,
            "User identification mapping for Discord bot interactions",
            added_by="test_script"
        )
        
        print(f"Attempting to store duplicate fact 2: {test_fact2}")
        memory_manager.store_global_fact(
            test_fact2,
            "Display name information for Discord user",
            added_by="test_script"
        )
        
        # Check if count increased (it shouldn't)
        final_results = memory_manager.global_collection.get(
            where={"type": "global_fact"}
        )
        final_count = len(final_results['documents'])
        print(f"Final global facts count: {final_count}")
        
        if final_count == initial_count:
            print("✅ SUCCESS: Duplicate facts were correctly prevented from being stored")
            return True
        else:
            print(f"❌ FAILURE: Expected {initial_count} facts, but found {final_count}")
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing duplicate prevention...")
    success = test_duplicate_prevention()
    if not success:
        exit(1)
