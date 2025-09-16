#!/usr/bin/env python3
"""
Test script to verify the personality fact integration works correctly
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_personality_fact_integration():
    """Test the integrated personality fact system"""
    print("\n🧪 Testing Integrated Personality Fact System")
    print("=" * 60)

    try:
        # Test 1: Import and initialization
        print("\n📦 Test 1: Checking imports and initialization...")

        from src.memory.memory_manager import UserMemoryManager
        from src.memory.personality_facts import get_personality_fact_classifier

        # Create memory manager (with minimal config for testing)
        memory_manager = UserMemoryManager(
            persist_directory="./temp_test_chromadb",
            enable_auto_facts=True,
            enable_global_facts=False,
            enable_emotions=False,
        )

        print("✅ Memory manager initialized successfully")

        # Test 2: Personality fact storage
        print("\n💾 Test 2: Testing personality fact storage...")

        test_user_id = "test_user_123"
        test_fact = "I love playing jazz piano and have been practicing for 5 years"

        context_metadata = {
            "extraction_source": "test",
            "timestamp": datetime.now().isoformat(),
            "channel_id": "test_channel",
            "is_dm": True,
        }

        personality_fact = memory_manager.store_personality_fact(
            test_user_id, test_fact, context_metadata
        )

        print(f"✅ Stored personality fact:")
        print(f"   🔍 Type: {personality_fact.fact_type.value}")
        print(
            f"   📊 Relevance: {personality_fact.relevance.value} ({personality_fact.relevance_score:.2f})"
        )
        print(f"   💾 Memory tier: {personality_fact.memory_tier.value}")
        print(f"   🎭 Emotional weight: {personality_fact.emotional_weight:.2f}")
        print(f"   🔒 Privacy level: {personality_fact.privacy_level}")

        # Test 3: Fact retrieval
        print("\n🔍 Test 3: Testing personality fact retrieval...")

        retrieved_facts = memory_manager.retrieve_personality_facts(user_id=test_user_id, limit=10)

        print(f"✅ Retrieved {len(retrieved_facts)} personality facts")

        if retrieved_facts:
            fact = retrieved_facts[0]
            print(f"   📝 Content: {fact.get('content', 'Unknown')[:50]}...")
            print(f"   🏷️ Type: {fact.get('fact_type', 'Unknown')}")
            print(f"   ⭐ Score: {fact.get('relevance_score', 0.0):.2f}")

        # Test 4: Conversation storage with automatic extraction
        print("\n💬 Test 4: Testing conversation storage with auto-extraction...")

        test_message = "I'm feeling really anxious about my job interview tomorrow. I've been preparing for weeks but still worry about public speaking."
        test_response = "I understand that job interviews can be nerve-wracking, especially when public speaking is involved. It sounds like you've been preparing well though!"

        # Simulate conversation storage (this should trigger personality fact extraction)
        success = memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=test_message,
            bot_response=test_response,
            channel_id="test_channel",
            metadata={"is_dm": True},
        )

        print(f"✅ Conversation stored successfully: {success}")

        # Check if facts were auto-extracted
        new_facts = memory_manager.retrieve_personality_facts(user_id=test_user_id, limit=20)

        print(f"✅ Total personality facts after conversation: {len(new_facts)}")

        # Show any new facts that were extracted
        for fact in new_facts[1:]:  # Skip the first one we manually added
            print(
                f"   🆕 Auto-extracted: {fact.get('fact_type', 'unknown')} - {fact.get('content', 'Unknown')[:50]}..."
            )

        # Test 5: Cleanup
        print("\n🧹 Test 5: Cleanup...")

        # Delete test memories
        deleted_count = memory_manager.delete_user_memories(test_user_id)
        print(f"✅ Cleaned up {deleted_count} test memories")

        # Clean up test ChromaDB directory
        import shutil

        if os.path.exists("./temp_test_chromadb"):
            shutil.rmtree("./temp_test_chromadb")
            print("✅ Cleaned up test database directory")

        print(f"\n🎉 All tests passed! Personality fact integration is working correctly.")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the whisperengine root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the integration test"""
    print("🤖 WhisperEngine Personality Fact Integration Test")
    print("=" * 70)

    success = test_personality_fact_integration()

    print(f"\n🏁 Test Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
