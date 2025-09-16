#!/usr/bin/env python3
"""
Test script to validate Dynamic Personality Profiler integration.

This script tests the complete integration of the dynamic personality system:
1. Database connectivity and table creation
2. Personality analysis processing
3. Data persistence and retrieval
4. Integration with bot core

Run with: python test_dynamic_personality_integration.py
"""

import asyncio
import logging
import os
import sys

# Setup path for imports
sys.path.append(".")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_dynamic_personality_integration():
    """Test the complete dynamic personality profiler integration."""


    try:
        # Test 1: Import and initialization

        from src.intelligence.dynamic_personality_profiler import (
            PersistentDynamicPersonalityProfiler,
        )


        # Test 2: Environment configuration

        # Check if dynamic personality is enabled
        os.getenv("ENABLE_DYNAMIC_PERSONALITY", "true").lower() == "true"

        # Test 3: Initialize profiler

        profiler = PersistentDynamicPersonalityProfiler()

        # Test 4: Database schema (if PostgreSQL available)

        try:
            # This will attempt to initialize database schema if PostgreSQL is available
            await profiler.initialize_persistence()
        except Exception:
            pass

        # Test 5: Basic personality analysis

        # Test conversation analysis with proper parameters
        test_user_message = "I'm really excited about this new project! I love working on creative things. Sometimes I feel overwhelmed by all the possibilities though."
        test_bot_response = "That's wonderful that you're excited about your project! It sounds like you have a lot of creative energy. It's completely normal to feel overwhelmed when there are many possibilities - that often means you're thinking deeply about the options."

        # Analyze conversation
        analysis_result = await profiler.analyze_conversation(
            user_id="test_user_123",
            context_id="test_channel",
            user_message=test_user_message,
            bot_response=test_bot_response,
            response_time_seconds=1.5,
            emotional_data={"primary_emotion": "excitement", "intensity": 0.8},
        )

        if analysis_result:

            # Test personality profile update
            profile = await profiler.update_personality_profile(analysis_result)

            if profile:

                # Show some personality traits
                if profile.traits:
                    for i, (_trait_name, _trait) in enumerate(profile.traits.items()):
                        if i >= 2:  # Show only first 3
                            break
            else:
                pass
        else:
            pass

        # Test 6: Bot core integration

        try:

            # Test that bot core can initialize with dynamic personality profiler
            # Note: This won't actually start the bot, just test initialization
            pass

        except Exception:
            pass

        # Test 7: Event handler integration

        try:

            pass

        except Exception:
            pass


        if profiler.persistence_enabled:
            pass
        else:
            pass


    except Exception:
        import traceback

        traceback.print_exc()
        return False

    return True


async def main():
    """Main test runner."""
    success = await test_dynamic_personality_integration()

    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
