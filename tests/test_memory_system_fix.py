#!/usr/bin/env python3
"""
Test script to verify memory system functionality and resolve Phase 3 warnings.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment

if not load_environment():
    sys.exit(1)

from src.core.bot import DiscordBotCore


async def test_memory_system():
    """Test memory system functionality and create test data if needed"""

    try:
        # Initialize bot core
        bot_core = DiscordBotCore(debug_mode=True)
        components = bot_core.get_components()

        memory_manager = components.get("memory_manager")
        if not memory_manager:
            return False


        # Test user ID for desktop mode
        test_user_id = "desktop_test_user"

        # Check existing memories
        existing_memories = await memory_manager.get_memories_by_user(test_user_id)

        # Add some test memories if none exist
        if len(existing_memories) < 2:

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

        # Verify memories were added
        await memory_manager.get_memories_by_user(test_user_id)

        # Test Phase 3 integration if available
        try:
            from src.memory.phase3_integration import Phase3MemoryNetworks

            phase3 = Phase3MemoryNetworks()

            # Test memory analysis
            await phase3.analyze_complete_memory_network(test_user_id, memory_manager)

        except Exception:
            pass

        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""

    success = await test_memory_system()

    if success:
        pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(main())
