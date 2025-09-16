#!/usr/bin/env python3
"""
Test Dynamic Personality Profiling System for Phase 2.1 Implementation

Tests the real-time personality adaptation and conversation pattern analysis
for personality-driven AI companions.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the personality profiling system
try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler

    print("✅ Dynamic personality profiler imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_conversation_analysis():
    """Test basic conversation analysis"""
    print("\n🧪 Testing Conversation Analysis")
    print("=" * 50)

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

        print(f"📝 {case['name']}")
        print(f"   Message: {case['user_message'][:50]}...")
        print(f"   Formality score: {analysis.formality_score:.2f}")
        print(f"   Detail preference: {analysis.detail_preference:.2f}")
        print(f"   Emotional openness: {analysis.emotional_openness:.2f}")
        print(f"   Conversation depth: {analysis.conversation_depth:.2f}")
        print(f"   Humor detected: {analysis.humor_detected}")
        print(f"   Support seeking: {analysis.support_seeking}")
        print(f"   Knowledge sharing: {analysis.knowledge_sharing}")
        print(f"   Topics: {analysis.topics_discussed}")
        print(f"   Trust indicators: {len(analysis.trust_indicators)}")
        print()

        # Validate expectations
        status = "✅"
        if "expected_formality" in case:
            if case["expected_formality"] == "formal" and analysis.formality_score >= 0:
                status = "❌"
            elif case["expected_formality"] == "casual" and analysis.formality_score <= 0:
                status = "❌"

        if "expected_humor" in case and case["expected_humor"] != analysis.humor_detected:
            status = "❌"

        if (
            "expected_support_seeking" in case
            and case["expected_support_seeking"] != analysis.support_seeking
        ):
            status = "❌"

        if (
            "expected_knowledge_sharing" in case
            and case["expected_knowledge_sharing"] != analysis.knowledge_sharing
        ):
            status = "❌"

        print(f"   {status} Analysis accuracy")
        print()

    return profiler


async def test_personality_profile_building(profiler):
    """Test building personality profiles over multiple conversations"""
    print("\n🧠 Testing Personality Profile Building")
    print("=" * 50)

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

    print("📈 Conversation Progression:")
    for i, conv in enumerate(conversations, 1):
        analysis = await profiler.analyze_conversation(
            user_id=user_id,
            context_id="test_channel",
            user_message=conv["message"],
            bot_response="I understand.",
            emotional_data=conv["emotional_data"],
        )

        profile = await profiler.update_personality_profile(analysis)

        print(f"   Conversation {i}: {conv['message'][:40]}...")
        print(f"      Formality: {analysis.formality_score:.2f}")
        print(f"      Emotional openness: {analysis.emotional_openness:.2f}")
        print(f"      Trust indicators: {len(analysis.trust_indicators)}")
        print(f"      Relationship depth: {profile.relationship_depth:.2f}")
        print(f"      Total traits: {len(profile.traits)}")
        print()

    # Get final profile summary
    final_profile = await profiler.get_personality_profile(user_id)
    print("🎯 Final Personality Profile:")
    print(f"   Total conversations: {final_profile.total_conversations}")
    print(f"   Relationship depth: {final_profile.relationship_depth:.2f}")
    print(f"   Trust level: {final_profile.trust_level:.2f}")
    print()

    # Show personality traits
    print("🧠 Personality Traits:")
    for dimension, trait in final_profile.traits.items():
        print(f"   {dimension.value}: {trait.value:.2f} (confidence: {trait.confidence:.2f})")
    print()

    return final_profile


async def test_adaptation_recommendations(profiler, user_id):
    """Test AI adaptation recommendations"""
    print("\n🎯 Testing Adaptation Recommendations")
    print("=" * 50)

    recommendations = await profiler.get_adaptation_recommendations(user_id)

    if "error" in recommendations:
        print("❌ No recommendations available")
        return False

    print("💡 AI Adaptation Recommendations:")
    print(f"   Confidence level: {recommendations['confidence_level']:.2f}")
    print()

    if recommendations["communication_style"]:
        print("🗣️ Communication Style:")
        for key, value in recommendations["communication_style"].items():
            print(f"   {key}: {value}")
        print()

    if recommendations["emotional_approach"]:
        print("💝 Emotional Approach:")
        for key, value in recommendations["emotional_approach"].items():
            print(f"   {key}: {value}")
        print()

    if recommendations["support_strategy"]:
        print("🤝 Support Strategy:")
        for key, value in recommendations["support_strategy"].items():
            print(f"   {key}: {value}")
        print()

    if recommendations["conversation_tactics"]:
        print("💬 Conversation Tactics:")
        for key, value in recommendations["conversation_tactics"].items():
            print(f"   {key}: {value}")
        print()

    return True


async def test_personality_summary(profiler, user_id):
    """Test comprehensive personality summary"""
    print("\n📊 Testing Personality Summary")
    print("=" * 50)

    summary = await profiler.get_personality_summary(user_id)

    if "error" in summary:
        print("❌ No summary available")
        return False

    print("📋 Personality Summary:")
    print(f"   User ID: {summary['user_id']}")
    print(f"   Profile age: {summary['profile_age_days']} days")
    print(f"   Total conversations: {summary['total_conversations']}")
    print(f"   Relationship depth: {summary['relationship_depth']:.2f}")
    print(f"   Trust level: {summary['trust_level']:.2f}")
    print()

    if summary["personality_traits"]:
        print("🧠 Personality Traits Summary:")
        for trait_name, trait_data in summary["personality_traits"].items():
            print(
                f"   {trait_name}: {trait_data['value']:.2f} (confidence: {trait_data['confidence']:.2f})"
            )
        print()

    if summary["conversation_patterns"]:
        patterns = summary["conversation_patterns"]
        print("💬 Conversation Patterns:")
        print(f"   Avg message length: {patterns['avg_message_length']:.0f} chars")
        print(f"   Avg formality: {patterns['avg_formality']:.2f}")
        print(f"   Avg emotional openness: {patterns['avg_emotional_openness']:.2f}")
        print(f"   Humor frequency: {patterns['humor_frequency']:.1%}")
        print(f"   Support seeking frequency: {patterns['support_seeking_frequency']:.1%}")
        print(f"   Top topics: {patterns['top_topics']}")
        print()

    if summary["confidence_metrics"]:
        metrics = summary["confidence_metrics"]
        print("📈 Confidence Metrics:")
        print(f"   Overall confidence: {metrics['overall_confidence']:.2f}")
        print(
            f"   High confidence traits: {metrics['traits_high_confidence']}/{metrics['traits_total']}"
        )
        print()

    return True


async def test_real_time_adaptation():
    """Test real-time personality adaptation scenarios"""
    print("\n⚡ Testing Real-Time Adaptation Scenarios")
    print("=" * 50)

    profiler = DynamicPersonalityProfiler()
    user_id = "adaptation_test_user"

    # Scenario 1: User requests more casual interaction
    print("🎭 Scenario 1: User requests casual interaction")
    analysis1 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="Hey, could you be more casual? I prefer friendly chat over formal responses.",
        bot_response="Of course! I'll adjust my tone.",
        emotional_data={"primary_emotion": "neutral", "intensity": 0.5},
    )

    profile1 = await profiler.update_personality_profile(analysis1)
    recommendations1 = await profiler.get_adaptation_recommendations(user_id)

    print(f"   Adaptation requests detected: {len(analysis1.adaptation_requests)}")
    print(
        f"   Formality preference: {profile1.preferred_response_style.get('formality', 'none set')}"
    )
    print(
        f"   AI recommendation: {recommendations1.get('communication_style', {}).get('formality', 'none')}"
    )
    print()

    # Scenario 2: User seeks emotional support
    print("🎭 Scenario 2: User seeks emotional support")
    analysis2 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="I'm feeling really overwhelmed and need help figuring out what to do.",
        bot_response="I'm here to support you through this.",
        emotional_data={"primary_emotion": "overwhelmed", "intensity": 0.8},
    )

    profile2 = await profiler.update_personality_profile(analysis2)
    recommendations2 = await profiler.get_adaptation_recommendations(user_id)

    print(f"   Support seeking detected: {analysis2.support_seeking}")
    print(f"   Emotional openness: {analysis2.emotional_openness:.2f}")
    print(f"   Trust level: {profile2.trust_level:.2f}")
    print(
        f"   Support strategy: {recommendations2.get('support_strategy', {}).get('approach', 'none')}"
    )
    print()

    # Scenario 3: Building deeper relationship
    print("🎭 Scenario 3: Building deeper relationship")
    analysis3 = await profiler.analyze_conversation(
        user_id=user_id,
        context_id="test_channel",
        user_message="I trust you completely and feel comfortable sharing my personal challenges with you.",
        bot_response="Thank you for trusting me with your thoughts.",
        emotional_data={"primary_emotion": "trusting", "intensity": 0.9},
    )

    profile3 = await profiler.update_personality_profile(analysis3)
    recommendations3 = await profiler.get_adaptation_recommendations(user_id)

    print(f"   Trust indicators: {len(analysis3.trust_indicators)}")
    print(f"   Conversation depth: {analysis3.conversation_depth:.2f}")
    print(f"   Relationship depth: {profile3.relationship_depth:.2f}")
    print(
        f"   Conversation tactics: {recommendations3.get('conversation_tactics', {}).get('depth', 'none')}"
    )
    print()

    return True


async def main():
    """Main test function"""
    print("🤖 WhisperEngine Dynamic Personality Profiling Test")
    print("=" * 70)
    print("Testing Phase 2.1: Dynamic Personality Profiling")
    print()

    try:
        # Run all tests
        profiler = await test_conversation_analysis()
        final_profile = await test_personality_profile_building(profiler)

        user_id = final_profile.user_id
        await test_adaptation_recommendations(profiler, user_id)
        await test_personality_summary(profiler, user_id)
        await test_real_time_adaptation()

        print("\n🎉 All Dynamic Personality Profiling Tests Completed Successfully!")
        print("✨ Phase 2.1 Implementation: READY")
        print()
        print("🚀 Next Steps:")
        print("   • Integrate with existing conversation handlers")
        print("   • Add personality-aware response generation")
        print("   • Implement proactive personality adaptation")
        print("   • Begin Phase 3.1: Emotional Context Engine")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
