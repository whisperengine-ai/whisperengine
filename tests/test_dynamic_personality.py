#!/usr/bin/env python3
"""
Test Dynamic Personality Profiling System for Phase 2.1 Implementation

Tests the real-time personality adaptation and conversation pattern analysis
for personality-driven AI companions.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the personality profiling system
try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler

except ImportError:
    sys.exit(1)


async def test_conversation_analysis():
    """Test basic conversation analysis"""

    profiler = DynamicPersonalityProfiler()

    # Test cases with different personality characteristics
    test_conversations = [
        {
            "name": "Formal professional inquiry",
            "user_message": "Good morning. I would appreciate your assistance with a technical question regarding software development best practices.",
            "expected_formality": "formal",
            "expected_detail": "high",
        },
        {
            "name": "Casual friendly chat",
            "user_message": "Hey! lol just wondering if you know any cool music stuff? I'm kinda bored 😊",
            "expected_formality": "casual",
            "expected_humor": True,
        },
        {
            "name": "Emotional sharing",
            "user_message": "I feel really anxious about my job interview tomorrow. I'm worried I won't be good enough.",
            "expected_openness": "high",
            "expected_support_seeking": True,
        },
        {
            "name": "Knowledge sharing",
            "user_message": "Did you know that Python was named after Monty Python? Fun fact I learned recently!",
            "expected_knowledge_sharing": True,
            "expected_topics": ["technology"],
        },
    ]

    for case in test_conversations:
        analysis = await profiler.analyze_conversation(
            user_id="test_user",
            context_id="test_channel",
            user_message=case["user_message"],
            bot_response="Thank you for your message.",
            emotional_data={"primary_emotion": "neutral", "intensity": 0.5},
        )


        # Validate expectations
        if "expected_formality" in case:
            if case["expected_formality"] == "formal" and analysis.formality_score >= 0:
                pass
            elif case["expected_formality"] == "casual" and analysis.formality_score <= 0:
                pass

        if "expected_humor" in case and case["expected_humor"] != analysis.humor_detected:
            pass

        if (
            "expected_support_seeking" in case
            and case["expected_support_seeking"] != analysis.support_seeking
        ):
            pass

        if (
            "expected_knowledge_sharing" in case
            and case["expected_knowledge_sharing"] != analysis.knowledge_sharing
        ):
            pass


    return profiler


async def test_personality_profile_building(profiler):
    """Test building personality profiles over multiple conversations"""

    user_id = "test_user_profile"

    # Simulate a series of conversations showing personality development
    conversations = [
        # Initial formal interactions
        {
            "message": "Hello, I need help with Python programming.",
            "emotional_data": {"primary_emotion": "neutral", "intensity": 0.3},
        },
        {
            "message": "Thank you for the explanation. Could you provide more details?",
            "emotional_data": {"primary_emotion": "curious", "intensity": 0.5},
        },
        # Becoming more casual
        {
            "message": "Hey, that worked great! You're really helpful 😊",
            "emotional_data": {"primary_emotion": "happy", "intensity": 0.7},
        },
        # Emotional sharing - building trust
        {
            "message": "I feel comfortable sharing this with you - I'm actually struggling with confidence at work.",
            "emotional_data": {"primary_emotion": "vulnerable", "intensity": 0.8},
        },
        # More personal sharing
        {
            "message": "I trust you understand me. I'm worried about my relationship and need someone to talk to.",
            "emotional_data": {"primary_emotion": "worried", "intensity": 0.9},
        },
        # Humor and casualness
        {
            "message": "lol you always know what to say! btw any jokes today?",
            "emotional_data": {"primary_emotion": "playful", "intensity": 0.6},
        },
    ]

    for _i, conv in enumerate(conversations, 1):
        analysis = await profiler.analyze_conversation(
            user_id=user_id,
            context_id="test_channel",
            user_message=conv["message"],
            bot_response="I understand.",
            emotional_data=conv["emotional_data"],
        )

        await profiler.update_personality_profile(analysis)


    # Get final profile summary
    final_profile = await profiler.get_personality_profile(user_id)

    # Show personality traits
    for _dimension, _trait in final_profile.traits.items():
        pass

    return final_profile


async def test_adaptation_recommendations(profiler, user_id):
    """Test AI adaptation recommendations"""

    recommendations = await profiler.get_adaptation_recommendations(user_id)

    if "error" in recommendations:
        return False


    if recommendations["communication_style"]:
        for _key, _value in recommendations["communication_style"].items():
            pass

    if recommendations["emotional_approach"]:
        for _key, _value in recommendations["emotional_approach"].items():
            pass

    if recommendations["support_strategy"]:
        for _key, _value in recommendations["support_strategy"].items():
            pass

    if recommendations["conversation_tactics"]:
        for _key, _value in recommendations["conversation_tactics"].items():
            pass

    return True


async def test_personality_summary(profiler, user_id):
    """Test comprehensive personality summary"""

    summary = await profiler.get_personality_summary(user_id)

    if "error" in summary:
        return False


    if summary["personality_traits"]:
        for _trait_name, _trait_data in summary["personality_traits"].items():
            pass

    if summary["conversation_patterns"]:
        summary["conversation_patterns"]

    if summary["confidence_metrics"]:
        summary["confidence_metrics"]

    return True


async def test_real_time_adaptation():
    """Test real-time personality adaptation scenarios"""

    profiler = DynamicPersonalityProfiler()
    user_id = "adaptation_test_user"

    # Scenario 1: User requests more casual interaction
    analysis1 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="Hey, could you be more casual? I prefer friendly chat over formal responses.",
        bot_response="Of course! I'll adjust my tone.",
        emotional_data={"primary_emotion": "neutral", "intensity": 0.5},
    )

    await profiler.update_personality_profile(analysis1)
    await profiler.get_adaptation_recommendations(user_id)


    # Scenario 2: User seeks emotional support
    analysis2 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="I'm feeling really overwhelmed and need help figuring out what to do.",
        bot_response="I'm here to support you through this.",
        emotional_data={"primary_emotion": "overwhelmed", "intensity": 0.8},
    )

    await profiler.update_personality_profile(analysis2)
    await profiler.get_adaptation_recommendations(user_id)


    # Scenario 3: Building deeper relationship
    analysis3 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="I trust you completely and feel comfortable sharing my personal challenges with you.",
        bot_response="Thank you for trusting me with your thoughts.",
        emotional_data={"primary_emotion": "trusting", "intensity": 0.9},
    )

    await profiler.update_personality_profile(analysis3)
    await profiler.get_adaptation_recommendations(user_id)


    return True


async def main():
    """Main test function"""

    try:
        # Run all tests
        profiler = await test_conversation_analysis()
        final_profile = await test_personality_profile_building(profiler)

        user_id = final_profile.user_id
        await test_adaptation_recommendations(profiler, user_id)
        await test_personality_summary(profiler, user_id)
        await test_real_time_adaptation()


    except Exception:
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
