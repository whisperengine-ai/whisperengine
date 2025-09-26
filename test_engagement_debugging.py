#!/usr/bin/env python3
"""
Test script for Proactive Engagement Engine debugging features

This script demonstrates how to test the comprehensive debugging system
added to the engagement engine to see when features get triggered.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

# Configure logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_engagement_debugging():
    """Test the engagement engine with debugging enabled"""
    
    try:
        from src.conversation.engagement_protocol import create_engagement_engine
        from src.memory.memory_protocol import create_memory_manager
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you're running from the project root and have the environment set up")
        return
    
    print("🤖 Testing Proactive Engagement Engine Debugging")
    print("=" * 60)
    
    # Create memory manager for vector integration
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Create engagement engine with vector integration
    engagement_engine = await create_engagement_engine(
        engagement_engine_type="full",
        memory_manager=memory_manager
    )
    
    # Test user and conversation data
    test_user_id = "test_user_123"
    test_context_id = "debug_test_conversation"
    
    # Simulate recent messages that would trigger different engagement strategies
    test_messages = [
        {
            "content": "Hey, how are you doing?",
            "timestamp": datetime.now().isoformat(),
            "user_id": test_user_id
        },
        {
            "content": "I'm feeling a bit stressed about work lately.",
            "timestamp": datetime.now().isoformat(),
            "user_id": test_user_id
        },
        {
            "content": "Yeah, just dealing with some difficult projects.",
            "timestamp": datetime.now().isoformat(),
            "user_id": test_user_id
        },
        {
            "content": "It's been pretty challenging.",
            "timestamp": datetime.now().isoformat(),
            "user_id": test_user_id
        }
    ]
    
    print("📝 Test Messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"  {i}. \"{msg['content']}\"")
    
    print("\n🔍 Running Engagement Analysis...")
    print("=" * 40)
    
    # Run engagement analysis - this will trigger all the debugging output
    result = await engagement_engine.analyze_conversation_engagement(
        user_id=test_user_id,
        context_id=test_context_id,
        recent_messages=test_messages,
        current_thread_info=None
    )
    
    print("\n📊 Analysis Results:")
    print("=" * 30)
    print(f"Flow State: {result.get('flow_state', 'N/A')}")
    print(f"Engagement Score: {result.get('engagement_score', 'N/A')}")
    print(f"Stagnation Risk: {result.get('stagnation_risk_level', 'N/A')}")
    print(f"Intervention Needed: {result.get('intervention_needed', 'N/A')}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    
    if result.get('recommendations'):
        print("\n💡 Generated Recommendations:")
        for i, rec in enumerate(result.get('recommendations', []), 1):
            rec_type = rec.get('type', 'unknown')
            strategy = rec.get('strategy', 'unknown')
            content = rec.get('content', '')[:100] + "..." if len(rec.get('content', '')) > 100 else rec.get('content', '')
            print(f"  {i}. [{rec_type}] {strategy}: {content}")
    
    print("\n✅ Engagement debugging test complete!")
    print("\n🤖 Check the logs above for detailed debugging output showing:")
    print("  • 🎯 When engagement analysis triggers")
    print("  • 📊 Conversation flow analysis")
    print("  • 🔍 Vector coherence analysis")
    print("  • 🧠 Memory system triggers")
    print("  • 💡 Topic suggestion triggers")
    print("  • 💬 Conversation prompt triggers")


async def test_vector_coherence_debugging():
    """Test specific vector coherence analysis with debugging"""
    
    print("\n🔍 Testing Vector Coherence Analysis Debugging")
    print("=" * 50)
    
    try:
        from src.conversation.engagement_protocol import create_engagement_engine
        from src.memory.memory_protocol import create_memory_manager
        
        # Create components
        memory_manager = create_memory_manager(memory_type="vector")
        engagement_engine = await create_engagement_engine(
            engagement_engine_type="full", 
            memory_manager=memory_manager
        )
        
        # Test different coherence scenarios
        coherent_messages = [
            "I love marine biology and studying ocean ecosystems.",
            "The coral reefs are fascinating underwater communities.",
            "Marine biodiversity is so important for ocean health."
        ]
        
        incoherent_messages = [
            "I love marine biology and studying ocean ecosystems.",
            "My favorite pizza topping is pepperoni.",
            "The weather has been really nice lately."
        ]
        
        print("📝 Testing coherent messages:")
        for msg in coherent_messages:
            print(f"  • {msg}")
        
        # This will trigger vector coherence analysis debugging
        if hasattr(engagement_engine, '_analyze_topic_coherence_vector'):
            coherent_score = await engagement_engine._analyze_topic_coherence_vector(coherent_messages)
            print(f"  → Coherence Score: {coherent_score:.3f}")
        
        print("\n📝 Testing incoherent messages:")
        for msg in incoherent_messages:
            print(f"  • {msg}")
        
        if hasattr(engagement_engine, '_analyze_topic_coherence_vector'):
            incoherent_score = await engagement_engine._analyze_topic_coherence_vector(incoherent_messages)
            print(f"  → Coherence Score: {incoherent_score:.3f}")
        
        print("\n✅ Vector coherence debugging test complete!")
        
    except Exception as e:
        print(f"❌ Vector coherence test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Engagement Engine Debugging Tests")
    print("=" * 60)
    
    try:
        # Run main engagement debugging test
        asyncio.run(test_engagement_debugging())
        
        # Run vector coherence specific test
        asyncio.run(test_vector_coherence_debugging())
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()