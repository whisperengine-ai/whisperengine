import sys

sys.path.append(".")
import asyncio
import os

from env_manager import load_environment

load_environment()
os.environ["ENV_MODE"] = "production"

from src.core.bot import DiscordBotCore


async def test_all_functionality():
    bot_core = DiscordBotCore(debug_mode=True)
    bot_core.initialize_all()

    components = bot_core.get_components()

    # Test 1: Memory System
    memory_manager = components.get("memory_manager")
    test_user = "123456789012345678"  # Discord-style user ID
    test_message = "I am passionate about machine learning and AI research"

    memory_manager.store_conversation(
        user_id=test_user,
        user_message=test_message,
        bot_response="That is fascinating! What specific areas of AI research interest you most?",
        channel_id="test_channel",
    )

    memory_manager.retrieve_relevant_memories(
        user_id=test_user, message="artificial intelligence research", limit=3
    )

    # Test 2: Phase 2 - Emotional Intelligence
    phase2 = components.get("phase2_integration")
    if phase2:
        try:
            phase2.process_message_with_emotional_intelligence(
                user_id=test_user,
                message="I'm feeling overwhelmed with my workload lately",
                context={"channel_id": "test"},
            )
        except Exception:
            pass

    # Test 3: Phase 3 - Memory Networks
    phase3 = components.get("phase3_memory_networks")
    if phase3:
        try:
            phase3.get_network_state(user_id=test_user)
        except Exception:
            pass

    # Test 4: External Emotion AI
    emotion_ai = components.get("external_emotion_ai")
    if emotion_ai:
        try:
            emotion_ai.analyze_emotion_cloud(
                "I'm really excited about my new project!"
            )
        except Exception:
            pass

    # Test 5: Phase 4 - Human-Like Intelligence (async)
    if hasattr(memory_manager, "process_with_phase4_intelligence"):
        try:
            await memory_manager.process_with_phase4_intelligence(
                user_id=test_user,
                message="I'm looking for advice on career development",
                conversation_context=[],
                discord_context={"channel_id": "test", "guild_id": "test"},
            )
        except Exception:
            pass

    # Test 6: Production Optimization
    production_adapter = components.get("production_adapter")
    if production_adapter:
        pass

    # Test 7: Conversation Cache (Redis)
    conversation_cache = components.get("conversation_cache")
    if conversation_cache:
        pass

    sum(1 for comp in components.values() if comp is not None)
    len(components)

    critical_systems = [
        "memory_manager",
        "llm_client",
        "phase2_integration",
        "phase3_memory_networks",
    ]
    critical_working = sum(1 for sys in critical_systems if components.get(sys) is not None)

    if critical_working == len(critical_systems):
        pass
    else:
        pass


# Run the comprehensive test
try:
    asyncio.run(test_all_functionality())
except Exception:
    import traceback

    traceback.print_exc()
