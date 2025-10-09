#!/usr/bin/env python3
"""
Test Synthetic Conversation Generation with LM Studio

This script tests the synthetic conversation generator with LM Studio integration
to ensure it properly works with the chat completions API endpoint.
"""

import os
import asyncio
import random
from setup_lm_studio_synthetic import setup_lm_studio_environment
from synthetic_conversation_generator import (
    SyntheticConversationGenerator,
    SyntheticUser,
    UserPersona,
    ConversationType
)

async def test_synthetic_generation():
    """Test synthetic conversation generation with LM Studio"""
    
    print("\n🤖 Testing Synthetic Conversation Generator with LM Studio")
    print("========================================================")
    
    # Set up the environment for LM Studio
    setup_lm_studio_environment()
    print("✅ Environment configured for LM Studio")
    
    # Create a synthetic conversation generator with LM Studio
    generator = SyntheticConversationGenerator({}, use_llm=True)
    
    if generator.use_llm and generator.llm_client:
        print("✅ LLM client initialized successfully for synthetic generation")
    else:
        print("❌ Failed to initialize LLM client")
        return False
    
    # Create a test user
    test_user = SyntheticUser(
        user_id='test_user',
        name='Alex Tester',
        persona=UserPersona.CREATIVE_EXPLORER,
        interests=['AI', 'creative writing', 'technology'],
        emotional_baseline={'curiosity': 0.8, 'happiness': 0.7},
        conversation_style='enthusiastic and curious',
        memory_details={},
        relationship_goals=['explore_technology', 'have_fun_conversations']
    )
    
    # Test conversation types
    conversation_types = [
        ConversationType.CASUAL_CHAT,
        ConversationType.CREATIVE_MODE_TEST,
        ConversationType.EMOTIONAL_SUPPORT
    ]
    
    # Test each conversation type
    for conv_type in conversation_types:
        print(f"\n📝 Testing conversation type: {conv_type.value}")
        
        # Generate an opener
        opener = await generator._llm_generate_opener(
            test_user,
            'elena',
            conv_type,
            ['AI', 'creative projects', 'marine biology']
        )
        
        print(f"✅ Generated opener: {opener}")
        
        # Generate a bot response (simulated)
        bot_response = f"Hello {test_user.name}! I'd be happy to chat about {conv_type.value}. What aspects interest you most?"
        
        # Generate a follow-up message
        follow_up = await generator._llm_generate_follow_up(
            test_user,
            bot_response,
            ['AI', 'creative projects', 'marine biology'],
            ['curious', 'interested'],
            [{'user_message': opener, 'bot_response': bot_response}]
        )
        
        print(f"✅ Generated follow-up: {follow_up}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_synthetic_generation())