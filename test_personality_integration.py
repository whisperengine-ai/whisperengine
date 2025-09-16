#!/usr/bin/env python3
"""
Test script to verify the personality fact integration works correctly
"""

import logging
import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_personality_fact_integration():
    """Test the integrated personality fact system"""

    try:
        # Test 1: Import and initialization

        from src.memory.memory_manager import UserMemoryManager
        from src.memory.personality_facts import get_personality_fact_classifier

        # Create memory manager (with minimal config for testing)
        memory_manager = UserMemoryManager(
            persist_directory="./temp_test_chromadb",
            enable_auto_facts=True,
            enable_global_facts=False,
            enable_emotions=False,
        )


        # Test 2: Personality fact storage

        test_user_id = "test_user_123"
        test_fact = "I love playing jazz piano and have been practicing for 5 years"

        context_metadata = {
            "extraction_source": "test",
            "timestamp": datetime.now().isoformat(),
            "channel_id": "test_channel",
            "is_dm": True,
        }

        memory_manager.store_personality_fact(
            test_user_id, test_fact, context_metadata
        )


        # Test 3: Fact retrieval

        retrieved_facts = memory_manager.retrieve_personality_facts(user_id=test_user_id, limit=10)


        if retrieved_facts:
            retrieved_facts[0]

        # Test 4: Conversation storage with automatic extraction

        test_message = "I'm feeling really anxious about my job interview tomorrow. I've been preparing for weeks but still worry about public speaking."
        test_response = "I understand that job interviews can be nerve-wracking, especially when public speaking is involved. It sounds like you've been preparing well though!"

        # Simulate conversation storage (this should trigger personality fact extraction)
        memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=test_message,
            bot_response=test_response,
            channel_id="test_channel",
            metadata={"is_dm": True},
        )


        # Check if facts were auto-extracted
        new_facts = memory_manager.retrieve_personality_facts(user_id=test_user_id, limit=20)


        # Show any new facts that were extracted
        for _fact in new_facts[1:]:  # Skip the first one we manually added
            pass

        # Test 5: Cleanup

        # Delete test memories
        memory_manager.delete_user_memories(test_user_id)

        # Clean up test ChromaDB directory
        import shutil

        if os.path.exists("./temp_test_chromadb"):
            shutil.rmtree("./temp_test_chromadb")

        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the integration test"""

    success = test_personality_fact_integration()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
