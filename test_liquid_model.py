#!/usr/bin/env python3
"""
Test Liquid LFM2-1.2B Model for Synthetic Conversations

Quick test to validate the tiny Liquid model is working correctly
for enhanced synthetic conversation generation.

Model: liquid/lfm2-1.2b (1.2B parameters - fast & efficient)
"""

import asyncio
import os
from synthetic_conversation_generator import (
    SyntheticConversationGenerator,
    SyntheticUser,
    UserPersona,
    ConversationType
)

async def test_liquid_model():
    """Test the tiny Liquid model for synthetic conversation generation"""
    
    print("🧪 Testing Liquid LFM2-1.2B Model for Synthetic Conversations")
    print("=" * 60)
    
    # Verify environment
    print("📋 Configuration:")
    print(f"   Model: {os.getenv('LLM_CHAT_MODEL', 'Not set')}")
    print(f"   URL: {os.getenv('LLM_CHAT_API_URL', 'Not set')}")
    print(f"   Max Tokens: {os.getenv('LLM_MAX_TOKENS_CHAT', 'Not set')}")
    print()
    
    # Create generator
    generator = SyntheticConversationGenerator({}, use_llm=True)
    
    if not generator.use_llm:
        print("❌ LLM not available - check LM Studio is running")
        return False
    
    print("✅ Synthetic generator initialized with Liquid model")
    print()
    
    # Create a simple test user
    test_user = SyntheticUser(
        user_id='liquid_test_001',
        name='Emma Chen',
        persona=UserPersona.CURIOUS_STUDENT,
        interests=['AI technology', 'learning'],
        emotional_baseline={'curiosity': 0.8, 'enthusiasm': 0.7},
        conversation_style='eager_learner',
        memory_details={},
        relationship_goals=['learn_new_things']
    )
    
    print(f"👤 Test User: {test_user.name} ({test_user.persona.value})")
    print()
    
    # Test scenarios optimized for tiny model
    test_scenarios = [
        {
            "type": ConversationType.CASUAL_CHAT,
            "topics": ["daily life", "interests"],
            "description": "Simple conversation"
        },
        {
            "type": ConversationType.LEARNING_SESSION,
            "topics": ["AI basics", "technology"],
            "description": "Learning discussion"
        }
    ]
    
    success_count = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🔬 Test {i}: {scenario['description']}")
        
        try:
            # Test opener generation
            opener = await generator._llm_generate_opener(
                test_user,
                'elena',
                scenario['type'],
                scenario['topics']
            )
            
            print(f"   🗣️ Generated opener: {opener}")
            
            # Test follow-up with simple context
            mock_response = "That's interesting! I'd like to help you with that."
            
            follow_up = await generator._llm_generate_follow_up(
                test_user,
                mock_response,
                scenario['topics'],
                ['curiosity', 'enthusiasm'],
                conversation_history=[]
            )
            
            print(f"   🔄 Generated follow-up: {follow_up}")
            success_count += 1
            print(f"   ✅ Test {i} successful")
            
        except Exception as e:
            print(f"   ❌ Test {i} failed: {e}")
        
        print()
    
    # Summary
    print("📊 TEST RESULTS:")
    print(f"   Successful tests: {success_count}/{len(test_scenarios)}")
    
    if success_count == len(test_scenarios):
        print("🎉 ALL TESTS PASSED!")
        print()
        print("🚀 LIQUID MODEL BENEFITS:")
        print("   ✅ Ultra-fast generation (1.2B parameters)")
        print("   ✅ Low memory usage")
        print("   ✅ Good instruction following")
        print("   ✅ Perfect for synthetic testing")
        print("   ✅ No API costs or rate limits")
        print()
        print("📋 READY FOR SYNTHETIC TESTING:")
        print("   Your synthetic conversation generator is now configured")
        print("   with the tiny but capable Liquid LFM2-1.2B model!")
        print()
        print("🎯 Next Steps:")
        print("   1. Run: python synthetic_conversation_generator.py")
        print("   2. Enjoy fast, realistic synthetic conversations")
        print("   3. Test your bot intelligence features efficiently")
        
        return True
    else:
        print("⚠️ Some tests failed - check LM Studio configuration")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_liquid_model())
    print(f"\n🏆 Overall Result: {'SUCCESS' if result else 'FAILED'}")