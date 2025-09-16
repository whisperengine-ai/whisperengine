import sys

sys.path.append(".")
from env_manager import load_environment
import os

load_environment()
os.environ["ENV_MODE"] = "production"

from src.core.bot import DiscordBotCore

print("=== TESTING AI PHASES FUNCTIONALITY ===")
bot_core = DiscordBotCore(debug_mode=True)
bot_core.initialize_all()

components = bot_core.get_components()

# Test Phase 2 - Emotional Intelligence
print("\n--- Testing Phase 2: Emotional Intelligence ---")
phase2 = components.get("phase2_integration")
if phase2:
    print(f"Phase 2 type: {type(phase2).__name__}")
    print(
        f'Phase 2 methods: {[m for m in dir(phase2) if not m.startswith("_") and callable(getattr(phase2, m))]}'
    )
else:
    print("❌ Phase 2 not available")

# Test Phase 3 - Memory Networks
print("\n--- Testing Phase 3: Memory Networks ---")
phase3 = components.get("phase3_memory_networks")
if phase3:
    print(f"Phase 3 type: {type(phase3).__name__}")
    print(
        f'Phase 3 methods: {[m for m in dir(phase3) if not m.startswith("_") and callable(getattr(phase3, m))]}'
    )
else:
    print("❌ Phase 3 not available")

# Test External Emotion AI
print("\n--- Testing External Emotion AI ---")
emotion_ai = components.get("external_emotion_ai")
if emotion_ai:
    print(f"Emotion AI type: {type(emotion_ai).__name__}")

    # Test emotion analysis
    try:
        test_message = "I'm feeling really excited about my new job!"
        emotion_result = emotion_ai.analyze_emotion(test_message)
        print(f"✅ Emotion analysis result: {emotion_result}")
    except Exception as e:
        print(f"❌ Emotion analysis failed: {e}")
else:
    print("❌ External Emotion AI not available")

# Test Phase 4 Integration
print("\n--- Testing Phase 4: Human-Like Intelligence ---")
memory_manager = components.get("memory_manager")
if memory_manager and hasattr(memory_manager, "get_phase4_status"):
    try:
        phase4_status = memory_manager.get_phase4_status()
        print(f"✅ Phase 4 status: {phase4_status}")
    except Exception as e:
        print(f"❌ Phase 4 status failed: {e}")

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
            print(f"✅ Phase 4 processing result keys: {list(phase4_result.keys())}")
            print(f'   Interaction type: {phase4_result.get("interaction_type", "N/A")}')
            print(f'   Conversation mode: {phase4_result.get("conversation_mode", "N/A")}')
        except Exception as e:
            print(f"❌ Phase 4 processing failed: {e}")
            import traceback

            traceback.print_exc()
else:
    print("❌ Phase 4 not available")

print("\n=== AI PHASES TEST COMPLETE ===")
