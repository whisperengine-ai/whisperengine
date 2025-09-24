#!/usr/bin/env python3
"""
Test script to verify that the vector memory system 'str' object has no attribute 'value' error is fixed.
This sends a message to Elena bot and checks if the memory operations work correctly.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append('src')

async def test_memory_operations():
    """Test memory operations to verify the fix"""
    try:
        # Set environment variables for Elena bot
        os.environ['DISCORD_BOT_NAME'] = 'elena'
        os.environ['POSTGRES_HOST'] = 'localhost'
        os.environ['POSTGRES_PORT'] = '5433'
        os.environ['POSTGRES_DB'] = 'whisperengine'
        os.environ['POSTGRES_USER'] = 'whisperengine'
        os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'
        os.environ['QDRANT_HOST'] = 'localhost'
        os.environ['QDRANT_PORT'] = '6334'
        os.environ['REDIS_HOST'] = 'localhost'
        os.environ['REDIS_PORT'] = '6380'
        
        from memory.memory_protocol import create_memory_manager
        print("✅ Creating vector memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Test 1: Store a conversation
        print("✅ Testing store_conversation...")
        success = await memory_manager.store_conversation(
            user_id="test_user_123",
            user_message="Hello Elena! How are you doing today?",
            bot_response="Hi there! I'm doing great, thanks for asking!",
            pre_analyzed_emotion_data={"primary_emotion": "joy", "confidence": 0.8}
        )
        print(f"   Store conversation result: {success}")
        
        # Test 2: Retrieve relevant memories - this is where the error was occurring
        print("✅ Testing retrieve_context_aware_memories (this is where the error occurred)...")
        memories = await memory_manager.retrieve_context_aware_memories(
            user_id="test_user_123",
            query="How have you been?",
            limit=5
        )
        print(f"   Retrieved {len(memories) if memories else 0} memories")
        
        # Test 3: Get conversation history
        print("✅ Testing get_conversation_history...")
        history = await memory_manager.get_conversation_history(
            user_id="test_user_123",
            limit=5
        )
        print(f"   Retrieved {len(history) if history else 0} conversation entries")
        
        print("\n🎉 ALL TESTS PASSED! The vector memory system type error has been fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_memory_operations())
    sys.exit(0 if success else 1)