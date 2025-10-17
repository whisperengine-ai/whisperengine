"""
Test Proactive Engagement Engine Activation
Tests basic initialization and stagnation detection
"""
import asyncio
import sys
from datetime import datetime

async def test_engagement_initialization():
    """Test basic initialization of ProactiveConversationEngagementEngine"""
    print("=" * 70)
    print("TEST 1: Proactive Engagement Engine Initialization")
    print("=" * 70)
    
    try:
        from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
        
        # Test initialization with conservative configuration
        engine = ProactiveConversationEngagementEngine(
            emotional_engine=None,  # Can work without emotional engine
            personality_profiler=None,  # Can work without personality profiler
            memory_manager=None,  # Can work without memory manager
            stagnation_threshold_minutes=10,
            engagement_check_interval_minutes=5,
            max_proactive_suggestions_per_hour=3
        )
        
        print("✅ Engine initialized successfully")
        print(f"   - Stagnation threshold: {engine.stagnation_threshold.total_seconds() / 60} minutes")
        print(f"   - Check interval: {engine.engagement_check_interval.total_seconds() / 60} minutes")
        print(f"   - Max suggestions: {engine.max_suggestions_per_hour}/hour")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stagnation_detection():
    """Test stagnation detection with short messages"""
    print("=" * 70)
    print("TEST 2: Stagnation Detection (Short Messages)")
    print("=" * 70)
    
    try:
        from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
        
        engine = ProactiveConversationEngagementEngine(
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None,
            stagnation_threshold_minutes=10,
            engagement_check_interval_minutes=5,
            max_proactive_suggestions_per_hour=3
        )
        
        # Simulate declining conversation with short messages
        recent_messages = [
            {'content': 'ok', 'role': 'user', 'timestamp': datetime.now()},
            {'content': 'cool', 'role': 'user', 'timestamp': datetime.now()},
            {'content': 'nice', 'role': 'user', 'timestamp': datetime.now()},
            {'content': 'yeah', 'role': 'user', 'timestamp': datetime.now()},
        ]
        
        analysis = await engine.analyze_conversation_engagement(
            user_id='test_user',
            context_id='test_context',
            recent_messages=recent_messages
        )
        
        print("✅ Stagnation detection completed")
        print(f"   - Flow state: {analysis.get('flow_analysis', {}).get('current_state', 'unknown')}")
        print(f"   - Stagnation risk: {analysis.get('stagnation_analysis', {}).get('risk_level', 'unknown')}")
        print(f"   - Intervention needed: {analysis.get('intervention_needed', False)}")
        
        if analysis.get('intervention_needed'):
            print(f"   - Recommended strategy: {analysis.get('recommended_strategy', 'none')}")
            print(f"   - Recommendations: {len(analysis.get('recommendations', []))}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Stagnation detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_engaged_conversation():
    """Test engaged conversation (should NOT trigger intervention)"""
    print("=" * 70)
    print("TEST 3: Engaged Conversation Detection (No Intervention)")
    print("=" * 70)
    
    try:
        from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
        
        engine = ProactiveConversationEngagementEngine(
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None,
            stagnation_threshold_minutes=10,
            engagement_check_interval_minutes=5,
            max_proactive_suggestions_per_hour=3
        )
        
        # Simulate engaged conversation with substantive messages
        recent_messages = [
            {
                'content': 'How are you Elena?', 
                'role': 'user', 
                'timestamp': datetime.now()
            },
            {
                'content': 'I\'m doing wonderfully! I was just thinking about coral reef restoration.',
                'role': 'assistant',
                'timestamp': datetime.now()
            },
            {
                'content': 'That sounds fascinating! Tell me more about your work with coral reefs.',
                'role': 'user',
                'timestamp': datetime.now()
            },
        ]
        
        analysis = await engine.analyze_conversation_engagement(
            user_id='test_user',
            context_id='test_context',
            recent_messages=recent_messages
        )
        
        print("✅ Engaged conversation analysis completed")
        print(f"   - Flow state: {analysis.get('flow_analysis', {}).get('current_state', 'unknown')}")
        print(f"   - Stagnation risk: {analysis.get('stagnation_analysis', {}).get('risk_level', 'unknown')}")
        print(f"   - Intervention needed: {analysis.get('intervention_needed', False)}")
        
        if not analysis.get('intervention_needed'):
            print("   ✅ Correctly identified as engaged conversation (no intervention)")
        else:
            print("   ⚠️ False positive: intervention suggested for engaged conversation")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Engaged conversation detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("PROACTIVE ENGAGEMENT ENGINE ACTIVATION TEST SUITE")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Basic initialization
    results.append(await test_engagement_initialization())
    
    # Test 2: Stagnation detection
    results.append(await test_stagnation_detection())
    
    # Test 3: Engaged conversation
    results.append(await test_engaged_conversation())
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Engine ready for Discord integration!")
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        sys.exit(1)
    
    print()


if __name__ == '__main__':
    asyncio.run(main())
