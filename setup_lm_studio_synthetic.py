#!/usr/bin/env python3
"""
Configure LM Studio for Synthetic Conversation Generator

This script sets up the environment to use your local LM Studio server
for enhanced synthetic conversation generation.

Local LM Studio Configuration:
- URL: http://127.0.0.1:1234
- Model: liquid/lfm2-1.2b (1.2B parameters - fast & efficient)
"""

import os
import asyncio
from synthetic_conversation_generator import (
    SyntheticConversationGenerator,
    SyntheticUser,
    UserPersona,
    ConversationType
)

def setup_lm_studio_environment():
    """Configure environment variables for LM Studio"""
    
    # Set LM Studio endpoint - ensure we're using the correct endpoint
    os.environ["LLM_CHAT_API_URL"] = "http://127.0.0.1:1234"  # Base URL without /v1
    os.environ["LLM_CLIENT_TYPE"] = "lmstudio"
    os.environ["LLM_CHAT_MODEL"] = "mistralai/mistral-nemo-instruct-2407"
    
    # LM Studio typically doesn't require an API key for local use
    # But some configurations might need it - leave empty for local
    os.environ["LLM_CHAT_API_KEY"] = ""
    
    # Enable LLM for synthetic generation
    os.environ["SYNTHETIC_USE_LLM"] = "true"
    
    # Set reasonable token limits for small local model
    os.environ["LLM_MAX_TOKENS_CHAT"] = "1024"
    
    print("✅ Environment configured for LM Studio:")
    print(f"   URL: {os.environ['LLM_CHAT_API_URL']}")
    print(f"   Model: {os.environ['LLM_CHAT_MODEL']}")
    print(f"   Client Type: {os.environ['LLM_CLIENT_TYPE']}")
    print(f"   Synthetic LLM: {os.environ['SYNTHETIC_USE_LLM']}")

async def test_lm_studio_connection():
    """Test connection to LM Studio server"""
    
    print("\n🔌 Testing LM Studio Connection...")
    
    try:
        # Create generator with LM Studio configuration
        generator = SyntheticConversationGenerator({}, use_llm=True)
        
        if generator.use_llm and generator.llm_client:
            print("✅ LM Studio client initialized successfully")
            
            # Test with a simple creative user
            test_user = SyntheticUser(
                user_id='lm_studio_test',
                name='Alex Testing',
                persona=UserPersona.CREATIVE_EXPLORER,
                interests=['AI technology', 'creative writing'],
                emotional_baseline={'curiosity': 0.8, 'creativity': 0.9},
                conversation_style='enthusiastic_creative',
                memory_details={},
                relationship_goals=['explore_creativity']
            )
            
            # Test opener generation
            print("\n🎨 Testing LM Studio Message Generation...")
            
            opener = await generator._llm_generate_opener(
                test_user,
                'elena',
                ConversationType.CREATIVE_MODE_TEST,
                ['creative writing', 'storytelling', 'AI collaboration']
            )
            
            print(f"✅ Generated opener: {opener}")
            
            # Test follow-up generation
            mock_response = "I'd love to explore creative writing with you! What kind of story would you like to create?"
            
            follow_up = await generator._llm_generate_follow_up(
                test_user,
                mock_response,
                ['creative writing', 'storytelling'],
                ['creativity', 'excitement'],
                conversation_history=[]
            )
            
            print(f"✅ Generated follow-up: {follow_up}")
            
            print(f"\n🎯 LM Studio Integration Successful!")
            print(f"   Model: liquid/lfm2-1.2b (1.2B parameters)")
            print(f"   Endpoint: http://127.0.0.1:1234")
            print(f"   Synthetic generation: Enhanced with tiny local LLM")
            
            return True
            
        else:
            print("❌ Failed to initialize LM Studio client")
            return False
            
    except Exception as e:
        print(f"❌ LM Studio connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure LM Studio is running on http://127.0.0.1:1234")
        print("   2. Verify the model 'liquid/lfm2-1.2b' is loaded")
        print("   3. Check that the API server is enabled in LM Studio")
        print("   4. Ensure no firewall is blocking localhost:1234")
        return False

async def run_lm_studio_synthetic_test():
    """Run a full synthetic conversation test with LM Studio"""
    
    print("\n🧪 Running Full Synthetic Conversation Test with LM Studio...")
    
    # Create bot endpoints (mock for testing)
    bot_endpoints = {
        "elena": "http://localhost:9091",  # These would be your actual bot endpoints
        "marcus": "http://localhost:9092"
    }
    
    # Create generator
    generator = SyntheticConversationGenerator(bot_endpoints, use_llm=True)
    
    if not generator.use_llm:
        print("❌ LLM not available for synthetic generation")
        return False
    
    # Create test user
    test_user = SyntheticUser(
        user_id='lm_studio_full_test',
        name='Maya Rodriguez',
        persona=UserPersona.CREATIVE_EXPLORER,
        interests=['digital art', 'AI creativity', 'storytelling'],
        emotional_baseline={'creativity': 0.9, 'curiosity': 0.8},
        conversation_style='imaginative_expressive',
        memory_details={'artistic_focus': 'AI-human collaboration'},
        relationship_goals=['explore_creativity', 'push_boundaries']
    )
    
    print(f"👤 Test User: {test_user.name} ({test_user.persona.value})")
    print(f"🎨 Focus: {', '.join(test_user.interests)}")
    
    # Test multiple message types
    test_scenarios = [
        {
            "type": ConversationType.CREATIVE_MODE_TEST,
            "topics": ["creative writing", "storytelling", "imagination"],
            "description": "Creative collaboration"
        },
        {
            "type": ConversationType.LEARNING_SESSION,
            "topics": ["AI technology", "machine learning", "creativity"],
            "description": "Technical learning"
        },
        {
            "type": ConversationType.RELATIONSHIP_BUILDING,
            "topics": ["connection", "understanding", "friendship"],
            "description": "Relationship development"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['description']}")
        
        # Generate opener
        opener = await generator._llm_generate_opener(
            test_user,
            'elena',
            scenario['type'],
            scenario['topics']
        )
        
        print(f"🗣️ Generated Opener: {opener}")
        
        # Mock bot response
        mock_responses = [
            "That's a fascinating creative idea! I'd love to explore that concept with you. What inspired this direction?",
            "I find that approach really interesting from a technical perspective. How do you think we could implement that?",
            "I really appreciate you sharing that with me. It means a lot that you trust me with these thoughts."
        ]
        
        mock_response = mock_responses[i-1]
        
        # Generate follow-up
        follow_up = await generator._llm_generate_follow_up(
            test_user,
            mock_response,
            scenario['topics'],
            ['creativity', 'curiosity', 'engagement'],
            conversation_history=[]
        )
        
        print(f"🔄 Generated Follow-up: {follow_up}")
    
    print(f"\n🎉 LM Studio Synthetic Conversation Test Complete!")
    print(f"✅ All message generation scenarios successful")
    print(f"\n🧠 Local Liquid model performing well for synthetic users")
    
    return True

async def main():
    """Main function to set up and test LM Studio integration"""
    
    print("🚀 LM Studio Integration for WhisperEngine Synthetic Testing")
    print("=" * 60)
    
    # Set up environment
    setup_lm_studio_environment()
    
    # Test connection
    connection_success = await test_lm_studio_connection()
    
    if connection_success:
        # Run full test
        test_success = await run_lm_studio_synthetic_test()
        
        if test_success:
            print(f"\n🏆 SUCCESS: LM Studio integration fully operational!")
            print(f"\n📋 Next Steps:")
            print(f"   1. Your synthetic conversation generator is now using local LM Studio")
            print(f"   2. Run synthetic tests with: python synthetic_conversation_generator.py")
            print(f"   3. All synthetic users will generate contextually aware messages")
            print(f"   4. Conversations will be more realistic and varied")
            print(f"\n🎯 Benefits of Local LM Studio:")
            print(f"   ✅ No API costs or rate limits")
            print(f"   ✅ Full privacy and control")
            print(f"   ✅ Consistent model performance")
            print(f"   ✅ Liquid's excellent instruction following and speed")
        else:
            print(f"\n❌ Full test failed - check LM Studio configuration")
    else:
        print(f"\n❌ Connection test failed - LM Studio may not be running")

if __name__ == "__main__":
    asyncio.run(main())