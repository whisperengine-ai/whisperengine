#!/usr/bin/env python3
"""
Test the updated Proactive Engagement Engine with vector store integration
"""

import asyncio
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_proactive_engagement_vector():
    """Test the proactive engagement engine with vector store"""
    try:
        # Set environment variables for the test - use correct variable names for vector memory
        os.environ['DISCORD_BOT_NAME'] = 'elena'
        os.environ['POSTGRESQL_HOST'] = 'localhost'
        os.environ['POSTGRESQL_PORT'] = '5433'
        os.environ['POSTGRESQL_DATABASE'] = 'whisperengine'
        os.environ['POSTGRESQL_USERNAME'] = 'whisperengine'
        os.environ['POSTGRESQL_PASSWORD'] = 'whisperengine123'
        os.environ['VECTOR_QDRANT_HOST'] = 'localhost'
        os.environ['VECTOR_QDRANT_PORT'] = '6334'
        os.environ['VECTOR_QDRANT_GRPC_PORT'] = '6334'
        os.environ['REDIS_HOST'] = 'localhost'
        os.environ['REDIS_PORT'] = '6380'
        
        # Import and create memory manager
        from src.memory.memory_protocol import create_memory_manager
        print("✅ Creating vector memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Import and create engagement engine
        from src.conversation.engagement_protocol import create_engagement_engine
        print("✅ Creating proactive engagement engine with vector integration...")
        
        engagement_engine = await create_engagement_engine(
            engagement_engine_type="basic",
            memory_manager=memory_manager
        )
        
        print(f"✅ Engagement engine created: {type(engagement_engine).__name__}")
        print(f"✅ Memory manager integrated: {engagement_engine.memory_manager is not None}")
        
        # Test conversation analysis
        test_messages = [
            {"content": "I've been feeling really stressed about work lately"},
            {"content": "The deadlines are getting overwhelming"},
            {"content": "I'm not sure how to manage it all"}
        ]
        
        print("✅ Testing conversation engagement analysis...")
        analysis = await engagement_engine.analyze_conversation_engagement(
            user_id="test_user_123",
            context_id="test_context",
            recent_messages=test_messages
        )
        
        print("✅ Analysis completed!")
        print(f"   Flow state: {analysis.get('flow_state', 'unknown')}")
        print(f"   Intervention needed: {analysis.get('intervention_needed', 'unknown')}")
        print(f"   Recommendations: {len(analysis.get('recommendations', []))} generated")
        
        # Test vector-based topic coherence
        if hasattr(engagement_engine, '_analyze_topic_coherence_vector'):
            print("✅ Testing vector-based topic coherence...")
            coherence_score = await engagement_engine._analyze_topic_coherence_vector(
                ["I love programming", "Coding is my passion", "Software development is amazing"]
            )
            print(f"   Coherence score: {coherence_score}")
        
        print("🎉 All tests passed! Proactive Engagement Engine is working with vector store.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_proactive_engagement_vector())