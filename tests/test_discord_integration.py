#!/usr/bin/env python3
"""
Quick test to verify Discord bot integration with emotion system
"""

import logging
import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import UserMemoryManager


def test_discord_integration():
    """Test that the Discord bot integration works"""

    try:
        # Initialize memory manager with emotions enabled (like in the Discord bot)
        memory_manager = UserMemoryManager(
            persist_directory="./test_discord_chromadb", enable_emotions=True
        )


        # Simulate a Discord interaction
        user_id = "123456789"  # Discord user ID format
        user_message = (
            "Hey Dream! I'm feeling really excited about this new project I'm working on!"
        )
        bot_response = "How wonderful that excitement flows through you like starlight upon still water. Tell me of this endeavor that kindles such joy within your mortal heart."

        # Store conversation (this processes emotions automatically)
        memory_manager.store_conversation(user_id, user_message, bot_response)

        # Get emotion context (what the bot would receive)
        emotion_context = memory_manager.get_emotion_context(user_id)

        # Simulate the CLEAN system prompt (no temporary context)
        time_context = "Current time: 2025-09-06"


        # Simulate the context user message (where temporal context now goes)
        context_parts = [f"Current context: {time_context}"]
        if emotion_context:
            context_parts.append(f"Emotional Context: {emotion_context}")

        "[Context from previous conversations]\n" + "\n\n".join(context_parts)

        # Test multiple interactions to show progression

        interactions = [
            "Thanks Dream, you're really helpful!",
            "My name is Alex, by the way",
            "I work as a software engineer at a startup",
            "I'm feeling a bit overwhelmed with work lately",
            "Thank you for understanding, you really get me",
        ]

        for i, message in enumerate(interactions, 2):
            bot_response = f"Response {i}"
            memory_manager.store_conversation(user_id, message, bot_response)
            memory_manager.get_emotion_context(user_id)

        # Get final stats
        memory_manager.get_collection_stats()


        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


def main():
    logging.basicConfig(level=logging.INFO)

    if test_discord_integration():

        pass
    else:
        pass


if __name__ == "__main__":
    main()
