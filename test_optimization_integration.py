#!/usr/bin/env python3
"""
Test script for Qdrant optimization integration.
Tests the new optimization features integrated into VectorMemoryManager.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_optimization_integration():
    """Test the optimization features integrated into VectorMemoryManager."""
    
    try:
        # Import the vector memory system
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Test configuration
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'collection_name': 'test_optimization'
            },
            'embeddings': {
                'model_name': 'snowflake/snowflake-arctic-embed-xs',
                'device': 'cpu'
            }
        }
        
        # Initialize memory manager
        logger.info("🚀 Initializing VectorMemoryManager with optimization...")
        memory_manager = VectorMemoryManager(config)
        
        # Test user
        user_id = "test_user_optimization"
        
        # Store some test conversations
        logger.info("📝 Storing test conversations...")
        
        conversations = [
            ("What's my cat's name?", "Your cat's name is Luna, and she's a beautiful tabby."),
            ("Tell me about Luna's favorite activities", "Luna loves to play with feather toys and nap in sunny windows."),
            ("How can I train my cat?", "Cats can be trained using positive reinforcement with treats and patience."),
            ("My favorite color is blue", "I'll remember that your favorite color is blue."),
            ("I work as a software engineer", "Got it, you're a software engineer. That's a great field!")
        ]
        
        for user_msg, bot_response in conversations:
            await memory_manager.store_conversation(
                user_id=user_id,
                user_message=user_msg,
                bot_response=bot_response,
                channel_id="test_channel"
            )
        
        # Test 1: Basic optimized search
        logger.info("\n🔍 Test 1: Basic optimized memory retrieval")
        results = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="what's my pet's name?",
            query_type="conversation_recall"
        )
        
        logger.info(f"Found {len(results)} optimized results")
        for i, result in enumerate(results[:3]):
            logger.info(f"  {i+1}. Score: {result.get('score', 0):.3f} | {result.get('content', '')[:80]}...")
            if 'reranked_score' in result:
                logger.info(f"      Reranked: {result['reranked_score']:.3f}")
        
        # Test 2: Optimized search with user preferences
        logger.info("\n🎯 Test 2: Optimized search with user preferences")
        user_preferences = {
            'conversational_user': True,
            'prefers_recent': True,
            'favorite_topics': ['pets', 'cats']
        }
        
        results_with_prefs = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="tell me about my cat",
            query_type="conversation_recall",
            user_history=user_preferences
        )
        
        logger.info(f"Found {len(results_with_prefs)} results with preferences")
        for i, result in enumerate(results_with_prefs[:3]):
            logger.info(f"  {i+1}. Score: {result.get('score', 0):.3f} | {result.get('content', '')[:80]}...")
            if 'scoring_breakdown' in result:
                breakdown = result['scoring_breakdown']
                logger.info(f"      Scoring: base={breakdown.get('base_score', 0):.3f}, "
                          f"recency={breakdown.get('recency_boost', 0):.3f}, "
                          f"preference={breakdown.get('preference_boost', 0):.3f}")
        
        # Test 3: Optimized conversation context
        logger.info("\n💬 Test 3: Optimized conversation context")
        context = await memory_manager.get_conversation_context_optimized(
            user_id=user_id,
            current_message="How do I take care of Luna?",
            user_preferences=user_preferences
        )
        
        logger.info(f"Retrieved {len(context)} context memories")
        for i, memory in enumerate(context[:3]):
            logger.info(f"  {i+1}. {memory.get('content', '')[:80]}...")
        
        # Test 4: Search with filters
        logger.info("\n🔧 Test 4: Optimized search with filters")
        filters = {
            'time_range': {
                'start': datetime.utcnow() - timedelta(days=1),
                'end': datetime.utcnow()
            },
            'topics': ['cats', 'pets']
        }
        
        filtered_results = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="pet care",
            query_type="fact_lookup",
            filters=filters
        )
        
        logger.info(f"Found {len(filtered_results)} filtered results")
        
        # Test 5: Compare basic vs optimized search
        logger.info("\n⚖️  Test 5: Basic vs Optimized comparison")
        
        basic_results = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="my cat",
            limit=5
        )
        
        optimized_results = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="my cat",
            query_type="conversation_recall",
            user_history=user_preferences,
            limit=5
        )
        
        logger.info(f"Basic search: {len(basic_results)} results")
        logger.info(f"Optimized search: {len(optimized_results)} results")
        
        if optimized_results:
            logger.info("Optimization features detected:")
            sample_result = optimized_results[0]
            if 'reranked_score' in sample_result:
                logger.info("  ✅ Result re-ranking active")
            if 'scoring_breakdown' in sample_result:
                logger.info("  ✅ Detailed scoring breakdown available")
        
        logger.info("\n🎉 Optimization integration tests completed successfully!")
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure the optimization module is available")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_optimization_fallback():
    """Test that the system gracefully falls back to basic search if optimization fails."""
    
    logger.info("\n🔄 Testing optimization fallback...")
    
    try:
        from src.memory.vector_memory_system import VectorMemoryManager
        
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'collection_name': 'test_fallback'
            },
            'embeddings': {
                'model_name': 'snowflake/snowflake-arctic-embed-xs',
                'device': 'cpu'
            }
        }
        
        memory_manager = VectorMemoryManager(config)
        
        # This should still work even if optimization components have issues
        results = await memory_manager.retrieve_relevant_memories_optimized(
            user_id="test_user",
            query="test query"
        )
        
        logger.info(f"✅ Fallback test successful: {len(results)} results")
        
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_optimization_integration())
    asyncio.run(test_optimization_fallback())