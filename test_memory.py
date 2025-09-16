import sys

sys.path.append(".")
import os

from env_manager import load_environment

load_environment()
os.environ["ENV_MODE"] = "production"

from src.core.bot import DiscordBotCore

bot_core = DiscordBotCore(debug_mode=True)
bot_core.initialize_all()

memory_manager = bot_core.get_components()["memory_manager"]

# Test storing a conversation with correct parameters
test_user = "test_user_correct_api"
test_message = "I love playing guitar and learning jazz music"
bot_response = "That sounds amazing! Jazz guitar is really complex and beautiful."


try:
    result = memory_manager.store_conversation(
        user_id=test_user,
        user_message=test_message,
        bot_response=bot_response,
        channel_id="test_channel_123",
    )
except Exception:
    pass

# Test retrieving memories with correct parameters
try:
    memories = memory_manager.retrieve_relevant_memories(
        user_id=test_user, message="guitar jazz music", limit=5
    )

    for _i, memory in enumerate(memories):
        for key, value in memory.items():
            if key not in ["embedding"]:  # Skip embedding data
                if len(str(value)) > 100:
                    pass
                else:
                    pass

    # Check if our test message was found
    found_our_message = any(
        "guitar" in str(m.get("message", "") or m.get("user_message", "")).lower() for m in memories
    )

    if found_our_message:
        pass
    else:
        pass

except Exception:
    import traceback

    traceback.print_exc()
