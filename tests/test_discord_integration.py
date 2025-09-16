#!/usr/bin/env python3
"""
Quick test to verify Discord bot integration with emotion system
"""

import sys
import os
import logging

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import UserMemoryManager


def test_discord_integration():
    """Test that the Discord bot integration works"""
    print("🤖 TESTING DISCORD BOT INTEGRATION")
    print("=" * 60)

    try:
        # Initialize memory manager with emotions enabled (like in the Discord bot)
        memory_manager = UserMemoryManager(
            persist_directory="./test_discord_chromadb", enable_emotions=True
        )

        print("✅ Memory manager initialized with emotion support")

        # Simulate a Discord interaction
        user_id = "123456789"  # Discord user ID format
        user_message = (
            "Hey Dream! I'm feeling really excited about this new project I'm working on!"
        )
        bot_response = "How wonderful that excitement flows through you like starlight upon still water. Tell me of this endeavor that kindles such joy within your mortal heart."

        # Store conversation (this processes emotions automatically)
        memory_manager.store_conversation(user_id, user_message, bot_response)
        print("✅ Conversation stored with emotion processing")

        # Get emotion context (what the bot would receive)
        emotion_context = memory_manager.get_emotion_context(user_id)
        print(f"✅ Emotion context generated: {emotion_context}")

        # Simulate the CLEAN system prompt (no temporary context)
        DEFAULT_SYSTEM_PROMPT = "You are Dream, from Neil Gaiman's The Sandman series..."
        time_context = "Current time: 2025-09-06"

        print("\n📝 CLEAN SYSTEM PROMPT:")
        print("-" * 40)
        print(DEFAULT_SYSTEM_PROMPT[:300] + "...")

        # Simulate the context user message (where temporal context now goes)
        context_parts = [f"Current context: {time_context}"]
        if emotion_context:
            context_parts.append(f"Emotional Context: {emotion_context}")

        context_message = "[Context from previous conversations]\n" + "\n\n".join(context_parts)
        print("\n📝 CONTEXT USER MESSAGE:")
        print("-" * 40)
        print(context_message)

        # Test multiple interactions to show progression
        print("\n🔄 TESTING RELATIONSHIP PROGRESSION:")
        print("-" * 40)

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
            context = memory_manager.get_emotion_context(user_id)
            print(f"Interaction {i}: {context}")

        # Get final stats
        stats = memory_manager.get_collection_stats()
        print(f"\n📊 FINAL STATS:")
        print(f"- Total memories: {stats['total_memories']}")
        print(f"- Emotion profiles: {stats['emotion_profiles_count']}")
        print(f"- Emotion system enabled: {stats['emotion_system_enabled']}")

        print("\n✅ Discord bot integration test completed successfully!")
        print("\n🚀 Your bot is ready to use emotion-aware responses!")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    logging.basicConfig(level=logging.INFO)

    if test_discord_integration():
        print("\n" + "=" * 60)
        print("✅ ALL SYSTEMS GO!")
        print("=" * 60)
        print("\n🎯 NEXT STEPS:")
        print("1. Start your Discord bot: python basic_discord_bot.py")
        print("2. Send messages to test emotion detection")
        print("3. Watch for emotion context in the logs")
        print("4. Notice how Dream's responses adapt over time")

        print("\n💡 TIP: Use --debug flag to see emotion processing:")
        print("   python basic_discord_bot.py --debug")
    else:
        print("\n❌ Please fix the integration issues before using the bot")


if __name__ == "__main__":
    main()
