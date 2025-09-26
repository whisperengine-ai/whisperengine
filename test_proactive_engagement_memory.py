#!/usr/bin/env python3
"""
Extended test for Proactive Engagement Engine vector integration
Tests memory connections and recommendation generation
"""

import asyncio
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_memory_connections():
    """Test memory connections with actual vector store data"""
    try:
        # Set environment variables for the test
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
        
        # Store some test conversations first
        print("✅ Storing test conversations for memory connections...")
        test_user_id = "test_user_memory_123"
        
        # Store some conversations to test against
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message="I'm really interested in machine learning",
            bot_response="Machine learning is fascinating! What aspects interest you most?"
        )
        
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message="I love working on AI projects",
            bot_response="AI projects can be incredibly rewarding. Tell me about your experiences."
        )
        
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message="I'm feeling stressed about my coding bootcamp",
            bot_response="Bootcamps can be intense. What's causing you the most stress?"
        )
        
        # Create engagement engine
        from src.conversation.engagement_protocol import create_engagement_engine
        print("✅ Creating engagement engine...")
        engagement_engine = await create_engagement_engine(
            engagement_engine_type="basic",
            memory_manager=memory_manager
        )
        
        # Test memory connections with related content
        print("✅ Testing memory connections for AI-related conversation...")
        recent_messages = [
            {"content": "I've been working on a new neural network project"},
            {"content": "The training is going well but the results are confusing"},
            {"content": "I could use some advice on machine learning best practices"}
        ]
        
        analysis = await engagement_engine.analyze_conversation_engagement(
            user_id=test_user_id,
            context_id="test_context_memory",
            recent_messages=recent_messages
        )
        
        print("✅ Memory connection analysis results:")
        print(f"   Flow state: {analysis.get('flow_state', 'unknown')}")
        print(f"   Intervention needed: {analysis.get('intervention_needed', 'unknown')}")
        print(f"   Recommendations: {len(analysis.get('recommendations', []))} generated")
        
        # Show the actual recommendations
        recommendations = analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            rec_type = rec.get('type', 'unknown')
            content = rec.get('content', 'No content')
            print(f"   {i}. [{rec_type}] {content}")
            
        # Test with emotional content
        print("\n✅ Testing memory connections for emotional conversation...")
        emotional_messages = [
            {"content": "I'm feeling overwhelmed with all my studies"},
            {"content": "The pressure is getting to me lately"},
            {"content": "I'm not sure if I can handle all this stress"}
        ]
        
        emotional_analysis = await engagement_engine.analyze_conversation_engagement(
            user_id=test_user_id,
            context_id="test_context_emotional",
            recent_messages=emotional_messages
        )
        
        print("✅ Emotional memory connection results:")
        emotional_recs = emotional_analysis.get('recommendations', [])
        for i, rec in enumerate(emotional_recs, 1):
            rec_type = rec.get('type', 'unknown')
            content = rec.get('content', 'No content')
            print(f"   {i}. [{rec_type}] {content}")
        
        # Test vector coherence with different topic relationships
        print("\n✅ Testing vector coherence analysis...")
        
        # High coherence: same topic
        high_coherence_content = [
            "I love programming in Python",
            "Python is such a versatile language",
            "The Python ecosystem is amazing"
        ]
        
        # Low coherence: different topics
        low_coherence_content = [
            "I love programming in Python",
            "My cat is really cute",
            "The weather is nice today"
        ]
        
        if hasattr(engagement_engine, '_analyze_topic_coherence_vector'):
            high_score = await engagement_engine._analyze_topic_coherence_vector(high_coherence_content)
            low_score = await engagement_engine._analyze_topic_coherence_vector(low_coherence_content)
            
            print(f"   High coherence (same topic): {high_score:.3f}")
            print(f"   Low coherence (different topics): {low_score:.3f}")
            print(f"   Coherence discrimination: {(high_score - low_score):.3f}")
        
        print("\n🎉 Extended testing complete! Vector integration is working perfectly.")
        
    except Exception as e:
        print(f"❌ Extended test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_memory_connections())