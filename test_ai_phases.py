import sys

sys.path.append(".")
import os

from env_manager import load_environment

load_environment()
os.environ["ENV_MODE"] = "production"

from src.core.bot import DiscordBotCore

bot_core = DiscordBotCore(debug_mode=True)
bot_core.initialize_all()

components = bot_core.get_components()

# Test Phase 2 - Emotional Intelligence
phase2 = components.get("phase2_integration")
if phase2:
    pass
else:
    pass

# Test Phase 3 - Memory Networks
phase3 = components.get("phase3_memory_networks")
if phase3:
    pass
else:
    pass

# Test External Emotion AI
emotion_ai = components.get("external_emotion_ai")
if emotion_ai:

    # Test emotion analysis
    try:
        test_message = "I'm feeling really excited about my new job!"
        emotion_result = emotion_ai.analyze_emotion(test_message)
    except Exception:
        pass
else:
    pass

# Test Phase 4 Integration
memory_manager = components.get("memory_manager")
if memory_manager and hasattr(memory_manager, "get_phase4_status"):
    try:
        phase4_status = memory_manager.get_phase4_status()
    except Exception:
        pass

    # Test Phase 4 processing
    if hasattr(memory_manager, "process_with_phase4_intelligence"):
        try:
            test_user = "phase4_test_user"
            test_message = "I'm struggling with motivation lately"

            phase4_result = memory_manager.process_with_phase4_intelligence(
                user_id=test_user,
                message=test_message,
                conversation_context=[],
                discord_context={"channel_id": "test", "guild_id": "test"},
            )
        except Exception:
            import traceback

            traceback.print_exc()
else:
    pass
