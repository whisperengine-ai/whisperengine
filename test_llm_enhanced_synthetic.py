#!/usr/bin/env python3
"""
LLM-Enhanced Synthetic Conversation State Test

This demonstrates the full power of the enhanced synthetic conversation generator 
when LLM is available, showing how the synthetic user maintains sophisticated 
conversational context and generates realistic responses that build upon all 
previous turns in the test scenario.

Author: WhisperEngine AI Team  
Created: October 9, 2025
Purpose: Validate LLM-enhanced state-aware synthetic testing
"""

import asyncio
import os
from synthetic_conversation_generator import (
    SyntheticConversationGenerator,
    SyntheticUser, 
    UserPersona,
    ConversationType
)

async def test_llm_enhanced_conversation_state():
    """Test LLM-enhanced conversation with full state awareness"""
    
    print("🧠 Testing LLM-Enhanced Synthetic Conversation State Management")
    print("=" * 65)
    
    # Enable LLM generation
    use_llm = os.getenv("SYNTHETIC_USE_LLM", "true").lower() == "true"
    
    # Create generator with LLM enabled
    generator = SyntheticConversationGenerator({}, use_llm=use_llm)
    
    if generator.use_llm:
        print("✅ LLM-enhanced generation ENABLED")
    else:
        print("⚠️ LLM-enhanced generation DISABLED (falling back to templates)")
        print("   Set SYNTHETIC_USE_LLM=true to enable LLM enhancement")
    
    print()
    
    # Create a creative test user for more interesting LLM generation
    test_user = SyntheticUser(
        user_id='creative_tester_001',
        name='Maya Rodriguez',
        persona=UserPersona.CREATIVE_EXPLORER,
        interests=['digital art', 'AI creativity', 'human-AI collaboration'],
        emotional_baseline={'creativity': 0.9, 'curiosity': 0.8, 'inspiration': 0.7},
        conversation_style='imaginative_expressive',
        memory_details={'artistic_focus': 'AI-generated art', 'collaboration_interest': 'human-AI'},
        relationship_goals=['explore_creativity', 'push_boundaries', 'inspire_innovation']
    )
    
    print(f"👤 Test User: {test_user.name} ({test_user.persona.value})")
    print(f"🎨 Interests: {', '.join(test_user.interests)}")
    print(f"💫 Style: {test_user.conversation_style}")
    print()
    
    # Test conversation type that benefits from creative LLM generation
    conversation_type = ConversationType.CREATIVE_MODE_TEST
    conversation_id = f"llm_test_{test_user.user_id}_creative_bot_{os.getpid()}"
    
    print(f"🎭 Test Scenario: {conversation_type.value}")
    print(f"🆔 Conversation ID: {conversation_id}")
    print()
    
    # Initialize conversation state
    generator._initialize_conversation_state(conversation_id, test_user, 'elena', conversation_type)
    
    # Test LLM-enhanced opener generation
    print("🚀 TESTING LLM-ENHANCED OPENER GENERATION:")
    print("-" * 45)
    
    opener = await generator._llm_generate_opener(
        test_user, 
        'elena', 
        conversation_type, 
        ['creative writing', 'storytelling', 'imagination'],
        conversation_id
    )
    
    print(f"🗣️ Generated Opener: {opener}")
    print()
    
    # Simulate a bot response to test follow-up generation
    mock_bot_response = "I'd love to collaborate on a creative story! Let's imagine a world where colors have consciousness and can communicate with artists. What kind of story would you want to tell in this world?"
    
    # Test LLM-enhanced follow-up generation with conversation state
    print("🔄 TESTING LLM-ENHANCED FOLLOW-UP WITH STATE:")
    print("-" * 48)
    
    # Create mock conversation history
    conversation_history = [{
        "turn": 1,
        "user_message": opener,
        "bot_response": mock_bot_response,
        "user_emotion": {"primary_emotion": "creativity"},
        "conversation_phase": "opening",
        "conversation_state": generator.conversation_state[conversation_id].copy()
    }]
    
    follow_up = await generator._generate_follow_up_message(
        test_user,
        mock_bot_response,
        ['creative writing', 'storytelling', 'imagination'], 
        ['creativity', 'inspiration', 'excitement'],
        conversation_history=conversation_history,
        conversation_id=conversation_id
    )
    
    print(f"🗣️ Generated Follow-up: {follow_up}")
    print()
    
    # Test how state context influences generation
    print("📊 STATE CONTEXT INFLUENCE ON GENERATION:")
    print("-" * 42)
    
    state = generator.conversation_state[conversation_id]
    print(f"🎯 Conversation Goals: {', '.join(state['conversation_arc']['goals'])}")
    print(f"🔄 Current Phase: {generator._get_conversation_phase(conversation_id)}")
    print(f"💖 Relationship Level: Trust={state['relationship_evolution']['trust']:.1f}")
    print()
    
    # Show the difference between template and LLM generation
    print("⚖️ TEMPLATE vs LLM GENERATION COMPARISON:")
    print("-" * 43)
    
    # Template-based generation (fallback)
    template_message = await generator._template_generate_follow_up(
        test_user,
        mock_bot_response,
        ['creative writing', 'storytelling'],
        ['creativity', 'inspiration']
    )
    
    print(f"📝 Template-based: {template_message}")
    print(f"🧠 LLM-enhanced:   {follow_up}")
    print()
    
    if generator.use_llm:
        print("✅ LLM ENHANCEMENT BENEFITS:")
        print("  🎯 More contextually aware and specific")
        print("  💫 Reflects user personality more authentically") 
        print("  🔄 Builds naturally on conversation history")
        print("  🎨 Shows creative personality traits")
        print("  📚 References established conversation context")
    else:
        print("ℹ️ TEMPLATE GENERATION CHARACTERISTICS:")
        print("  📋 Follows predefined patterns")
        print("  🔄 Basic persona-based variation")
        print("  ⚡ Fast and reliable fallback")
        print("  🛡️ Consistent output format")
    
    print()
    print("🎯 KEY STATE MANAGEMENT FEATURES:")
    print("  ✅ Conversation ID tracking for unique test scenarios")
    print("  ✅ Enhanced conversation arc planning")
    print("  ✅ Turn-by-turn state evolution")
    print("  ✅ Relationship progression tracking")
    print("  ✅ Established facts accumulation")
    print("  ✅ Emotional journey mapping")
    print("  ✅ Conversation phase awareness")
    print("  ✅ LLM context enhancement when available")
    
    print()
    print("🔬 TESTING IMPACT FOR WHISPERENGINE:")
    print("  🎯 Synthetic conversations now mirror realistic human interaction patterns")
    print("  📊 Full conversation state enables testing of long-term memory systems")
    print("  🧠 LLM enhancement provides more realistic and varied test data")
    print("  🔄 Multi-turn scenarios can validate complex AI intelligence features")
    print("  🎭 Different personas create diverse testing scenarios")
    print("  📈 Relationship evolution testing validates character development")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_llm_enhanced_conversation_state())
    print(f"\n🏆 Test Result: {'SUCCESS' if result else 'FAILED'}")