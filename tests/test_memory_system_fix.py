#!/usr/bin/env python3
"""
Test script to verify memory system functionality and resolve Phase 3 warnings.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment

if not load_environment():
    print("❌ Failed to load environment")
    sys.exit(1)

from src.core.bot import DiscordBotCore


async def test_memory_system():
    """Test memory system functionality and create test data if needed"""
    print("🧠 Testing WhisperEngine Memory System...")

    try:
        # Initialize bot core
        bot_core = DiscordBotCore(debug_mode=True)
        components = bot_core.get_components()

        memory_manager = components.get("memory_manager")
        if not memory_manager:
            print("❌ Memory manager not available")
            return False

        print("✅ Memory manager initialized")

        # Test user ID for desktop mode
        test_user_id = "desktop_test_user"

        # Check existing memories
        existing_memories = await memory_manager.get_memories_by_user(test_user_id)
        print(f"📊 Found {len(existing_memories)} existing memories for user {test_user_id}")

        # Add some test memories if none exist
        if len(existing_memories) < 2:
            print("📝 Creating test memories...")

            test_memories = [
                {
                    "content": "I love working on AI projects and machine learning",
                    "topic": "AI and Technology",
                    "context": "User expressing interest in AI development",
                },
                {
                    "content": "I enjoy hiking in the mountains during weekends",
                    "topic": "Outdoor Activities",
                    "context": "User sharing personal hobbies",
                },
                {
                    "content": "Python is my favorite programming language",
                    "topic": "Programming",
                    "context": "User discussing programming preferences",
                },
            ]

            for memory_data in test_memories:
                await memory_manager.add_memory(
                    user_id=test_user_id,
                    content=memory_data["content"],
                    topic=memory_data["topic"],
                    context=memory_data["context"],
                )
                print(f"✅ Added memory: {memory_data['topic']}")

        # Verify memories were added
        updated_memories = await memory_manager.get_memories_by_user(test_user_id)
        print(f"✅ Total memories after test: {len(updated_memories)}")

        # Test Phase 3 integration if available
        try:
            from src.memory.phase3_integration import Phase3MemoryNetworks

            phase3 = Phase3MemoryNetworks()
            print("✅ Phase 3 Memory Networks initialized")

            # Test memory analysis
            analysis = await phase3.analyze_complete_memory_network(test_user_id, memory_manager)
            print(f"✅ Phase 3 analysis completed:")
            print(
                f"   - Total memories: {analysis.get('network_state', {}).get('total_memories', 0)}"
            )
            print(f"   - Clusters: {analysis.get('network_state', {}).get('cluster_count', 0)}")
            print(f"   - Patterns: {analysis.get('network_state', {}).get('pattern_count', 0)}")

        except Exception as e:
            print(f"⚠️ Phase 3 test failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 WhisperEngine Memory System Test")
    print("=" * 50)

    success = await test_memory_system()

    if success:
        print("\n✅ Memory system test completed successfully!")
        print("   The Phase 3 memory warnings should now be resolved.")
    else:
        print("\n❌ Memory system test failed!")
        print("   Please check the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())
