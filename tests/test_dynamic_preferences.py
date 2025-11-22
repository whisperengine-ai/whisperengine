import asyncio
import os
import sys
import emoji

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src_v2.agents.engine import AgentEngine
from src_v2.core.character import character_manager
from src_v2.evolution.trust import trust_manager
from src_v2.core.database import db_manager

async def test_dynamic_preferences(char_name: str = "elena"):
    print(f"=== Testing Dynamic Preferences for: {char_name} ===")
    
    # Initialize DB
    await db_manager.connect_postgres()
    
    character = character_manager.load_character(char_name)
    if not character:
        print(f"Error: Could not load character {char_name}")
        return

    engine = AgentEngine()
    user_id = "test_user_prefs_001"
    
    # Test 1: Conciseness
    print("\n--- Test 1: Conciseness Constraint ---")
    await trust_manager.update_preference(user_id, char_name, "verbosity", "extremely concise, max 10 words")
    
    response = await engine.generate_response(
        character=character,
        user_message="Tell me about the ocean.",
        user_id=user_id,
        chat_history=[]
    )
    
    print(f"Bot: {response}")
    word_count = len(response.split())
    print(f"Word Count: {word_count}")
    
    if word_count <= 15: # Allow a small buffer
        print("RESULT: PASS ✅")
    else:
        print("RESULT: FAIL ❌ (Too verbose)")

    # Test 2: No Emojis
    print("\n--- Test 2: No Emojis Constraint ---")
    await trust_manager.update_preference(user_id, char_name, "emoji_usage", "none, strictly forbidden")
    # Reset verbosity to normal for this test
    await trust_manager.update_preference(user_id, char_name, "verbosity", "normal")
    
    response = await engine.generate_response(
        character=character,
        user_message="I'm feeling happy today!",
        user_id=user_id,
        chat_history=[]
    )
    
    print(f"Bot: {response}")
    emoji_count = emoji.emoji_count(response)
    print(f"Emoji Count: {emoji_count}")
    
    if emoji_count == 0:
        print("RESULT: PASS ✅")
    else:
        print("RESULT: FAIL ❌ (Emojis detected)")

if __name__ == "__main__":
    char_name = os.getenv("DISCORD_BOT_NAME", "elena")
    asyncio.run(test_dynamic_preferences(char_name))
