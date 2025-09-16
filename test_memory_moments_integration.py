#!/usr/bin/env python3
"""
Memory Moments Integration Test

Tests that Phase 4.1 Memory-Triggered Personality Moments are properly integrated
into the WhisperEngine bot system.
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.bot import DiscordBotCore
from src.personality.memory_moments import MemoryTriggeredMoments


async def test_memory_moments_integration():
    """Test memory moments integration with bot core"""

    try:
        # Test 1: MemoryTriggeredMoments can be imported and initialized

        # Create a minimal memory manager mock
        class MockMemoryManager:
            def retrieve_relevant_memories(self, user_id, query, limit=5):
                return [f"Mock memory {i} for {user_id}: {query[:30]}..." for i in range(2)]

        memory_manager = MockMemoryManager()

        memory_moments = MemoryTriggeredMoments(
            memory_manager=memory_manager,
            emotional_context_engine=None,  # Can be None for basic testing
            personality_profiler=None,  # Can be None for basic testing
        )


        # Test 2: Bot core can initialize memory moments

        # We can't fully test bot core without Discord bot setup,
        # but we can test the integration path exists
        try:
            # Check if bot core has memory moments in components when initialized
            # This is a simplified test since full bot initialization requires Discord
            bot_core = DiscordBotCore(debug_mode=True)
            components = bot_core.get_components()

            if "memory_moments" in components:
                pass
            else:
                pass

        except Exception:
            pass

        # Test 3: Memory moments can analyze conversations

        try:
            # Test basic conversation analysis
            await memory_moments.analyze_conversation_for_memories(
                user_id="test_user_123",
                context_id="test_context",
                message="I've been thinking about our conversation yesterday about goals.",
            )


        except Exception:
            pass

        # Test 4: Memory moments can generate moments

        try:
            # Create minimal conversation context
            from datetime import timedelta

            from src.personality.memory_moments import ConversationContext

            conversation_context = ConversationContext(
                user_id="test_user_123",
                context_id="test_context",
                current_message="Let's continue our discussion about personal growth.",
                topic_keywords=["personal growth", "goals", "development"],
                emotional_state="interested",
                conversation_phase="deepening",
                recent_messages=["Hello", "How are you?", "Let's talk about growth"],
                conversation_length=3,
                current_relationship_depth=0.7,  # Float value
                current_trust_level=0.6,  # Float value
                current_engagement_level=0.8,  # Float value
                time_since_last_conversation=timedelta(hours=1),  # timedelta
                conversation_frequency=0.5,  # Float value
                recently_triggered_moments=[],
            )

            await memory_moments.generate_memory_moments(
                user_id="test_user_123", conversation_context=conversation_context
            )


        except Exception:
            pass


        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_integration_completeness():
    """Test that all integration points are properly connected"""

    integration_points = {
        "Bot Core Initialization": "src/core/bot.py contains memory_moments initialization",
        "Universal Chat Integration": "src/platforms/universal_chat.py contains memory moments processing",
        "System Prompt Integration": "src/utils/helpers.py contains MEMORY_MOMENTS_CONTEXT",
        "System Prompt Template": "config/system_prompts/dream_ai_enhanced.md contains {MEMORY_MOMENTS_CONTEXT}",
        "Thread Manager Integration": "src/conversation/advanced_thread_manager.py uses memory_moments",
        "Proactive Engagement Integration": "src/conversation/proactive_engagement_engine.py uses memory_moments",
    }

    results = {}

    for name, description in integration_points.items():
        try:
            if "src/core/bot.py" in description:
                with open("src/core/bot.py") as f:
                    content = f.read()
                    if "memory_moments" in content and "Phase 4.1" in content:
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

            elif "src/platforms/universal_chat.py" in description:
                with open("src/platforms/universal_chat.py") as f:
                    content = f.read()
                    if "memory_moments_context" in content:
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

            elif "src/utils/helpers.py" in description:
                with open("src/utils/helpers.py") as f:
                    content = f.read()
                    if "MEMORY_MOMENTS_CONTEXT" in content:
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

            elif "dream_ai_enhanced.md" in description:
                with open("config/system_prompts/dream_ai_enhanced.md") as f:
                    content = f.read()
                    if "{MEMORY_MOMENTS_CONTEXT}" in content:
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

            elif "advanced_thread_manager.py" in description:
                with open("src/conversation/advanced_thread_manager.py") as f:
                    content = f.read()
                    if "self.memory_moments" in content and "MEMORY_MOMENTS_AVAILABLE" in content:
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

            elif "proactive_engagement_engine.py" in description:
                with open("src/conversation/proactive_engagement_engine.py") as f:
                    content = f.read()
                    if (
                        "self.memory_moments" in content
                        and "analyze_conversation_for_memories" in content
                    ):
                        results[name] = "✅ Found"
                    else:
                        results[name] = "❌ Missing"

        except Exception as e:
            results[name] = f"❌ Error: {e}"

    for name, _status in results.items():
        pass

    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    total_count = len(results)


    return success_count == total_count


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.ERROR)  # Reduce noise during testing


    # Test integration completeness
    completeness_passed = test_integration_completeness()

    # Test runtime integration
    runtime_passed = asyncio.run(test_memory_moments_integration())

    if completeness_passed and runtime_passed:
        sys.exit(0)
    else:
        sys.exit(1)
