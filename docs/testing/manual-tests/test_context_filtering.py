#!/usr/bin/env python3
"""
Test script for enhanced context-based fact filtering.

Tests the new context-aware filtering to ensure relevant facts are prioritized
based on conversation topic.
"""

import asyncio
import os
import sys
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')


async def test_context_based_filtering():
    """Test context-based fact filtering with different message topics."""
    print("🎯 Testing context-based fact filtering...")
    
    try:
        # Set environment variables
        os.environ['QDRANT_HOST'] = 'localhost'
        os.environ['QDRANT_PORT'] = '6334'
        os.environ['POSTGRES_HOST'] = 'localhost'
        os.environ['POSTGRES_PORT'] = '5433'
        os.environ['DISCORD_BOT_NAME'] = 'elena'
        
        from src.core.message_processor import MessageProcessor
        from src.knowledge.semantic_router import SemanticKnowledgeRouter
        import asyncpg
        
        # Create PostgreSQL pool
        postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5433")),
            "database": os.getenv("POSTGRES_DB", "whisperengine"),
            "user": os.getenv("POSTGRES_USER", "whisperengine"),
            "password": os.getenv("POSTGRES_PASSWORD", "whisperengine_password")
        }
        postgres_pool = await asyncpg.create_pool(**postgres_config)
        
        # Create semantic router
        router = SemanticKnowledgeRouter(postgres_pool)
        
        # Create bot core mock
        class MockBotCore:
            def __init__(self):
                self.knowledge_router = router
        
        # Create message processor
        bot_core = MockBotCore()
        message_processor = MessageProcessor(
            bot_core=bot_core,
            memory_manager=None,
            llm_client=None
        )
        
        test_user_id = "672814231002939413"
        
        # Test different conversation contexts
        test_contexts = [
            ("I'm hungry, what should I eat for dinner?", "🍕 FOOD CONTEXT"),
            ("Tell me about my cats", "🐱 PET CONTEXT"),
            ("What do you remember about my work?", "💼 WORK CONTEXT"),
            ("Just a general question", "❓ GENERAL CONTEXT"),
            ("I love coral reefs and marine biology", "🌊 MARINE CONTEXT"),
        ]
        
        print(f"Testing context filtering for user {test_user_id}...")
        
        for message_content, context_label in test_contexts:
            print(f"\n{context_label}: '{message_content}'")
            
            # Generate facts with context filtering
            facts_content = await message_processor._build_user_facts_content(
                test_user_id, 
                message_content
            )
            
            if facts_content:
                print(f"  ✅ Generated facts ({len(facts_content)} chars):")
                print(f"     {facts_content}")
            else:
                print(f"  ❌ No facts generated")
        
        await postgres_pool.close()
        print("\n✅ Context-based filtering test completed!")
        
    except Exception as e:
        print(f"❌ Error during context filtering test: {e}")
        import traceback
        traceback.print_exc()


async def test_length_limits():
    """Test that facts stay within character limits even with many facts."""
    print("\n📏 Testing fact length limits...")
    
    try:
        # Set environment variables
        os.environ['QDRANT_HOST'] = 'localhost'
        os.environ['QDRANT_PORT'] = '6334'
        os.environ['POSTGRES_HOST'] = 'localhost'
        os.environ['POSTGRES_PORT'] = '5433'
        os.environ['DISCORD_BOT_NAME'] = 'elena'
        
        from src.core.message_processor import MessageProcessor
        from src.knowledge.semantic_router import SemanticKnowledgeRouter
        import asyncpg
        
        # Create PostgreSQL pool
        postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5433")),
            "database": os.getenv("POSTGRES_DB", "whisperengine"),
            "user": os.getenv("POSTGRES_USER", "whisperengine"),
            "password": os.getenv("POSTGRES_PASSWORD", "whisperengine_password")
        }
        postgres_pool = await asyncpg.create_pool(**postgres_config)
        
        # Create semantic router
        router = SemanticKnowledgeRouter(postgres_pool)
        
        # Create bot core mock
        class MockBotCore:
            def __init__(self):
                self.knowledge_router = router
        
        # Create message processor
        bot_core = MockBotCore()
        message_processor = MessageProcessor(
            bot_core=bot_core,
            memory_manager=None,
            llm_client=None
        )
        
        test_user_id = "672814231002939413"
        
        # Test with general context to get maximum facts
        facts_content = await message_processor._build_user_facts_content(
            test_user_id, 
            "Tell me everything you know about me"
        )
        
        print(f"Facts content length: {len(facts_content)} characters")
        print(f"Within 400 char limit: {'✅' if len(facts_content) <= 400 else '❌'}")
        print(f"Content: {facts_content}")
        
        await postgres_pool.close()
        print("\n✅ Length limits test completed!")
        
    except Exception as e:
        print(f"❌ Error during length limits test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Testing Enhanced Context-Based Fact Filtering\n")
    
    # Test 1: Context-based filtering
    asyncio.run(test_context_based_filtering())
    
    # Test 2: Length limits
    asyncio.run(test_length_limits())