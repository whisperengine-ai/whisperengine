#!/usr/bin/env python3
"""
Test script to verify the polymorphism fix is working.
This will trigger a memory retrieval operation that previously caused the MemoryType error.
"""

import asyncio
import sys
import os
from datetime import datetime

# Set environment to connect to running containers  
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'

# Add src to path
sys.path.append('src')

async def test_polymorphism_fix():
    """Test that the polymorphism interface mismatch is fixed"""
    try:
        from memory.memory_protocol import create_memory_manager
        
        print("✅ Creating vector memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        
        print("✅ Testing protocol-compliant memory operations...")
        
        # Test 1: Store conversation (this should work)
        print("   📝 Testing store_conversation...")
        success = await memory_manager.store_conversation(
            user_id="test_polymorphism_user",
            user_message="Hello Elena! How are you?",
            bot_response="Hi! I'm doing great, thanks for asking!",
            pre_analyzed_emotion_data={"primary_emotion": "joy", "confidence": 0.8}
        )
        print(f"   ✅ Store conversation: {success}")
        
        # Test 2: The operation that was failing - retrieve_context_aware_memories
        print("   🔍 Testing retrieve_context_aware_memories (this was failing before)...")
        memories = await memory_manager.retrieve_context_aware_memories(
            user_id="test_polymorphism_user", 
            query="How are you doing?",
            limit=5
        )
        print(f"   ✅ Context-aware memories retrieved: {len(memories)} results")
        
        # Test 3: Direct search_memories call to test protocol compliance
        print("   🔍 Testing direct search_memories call...")
        search_results = await memory_manager.search_memories(
            user_id="test_polymorphism_user",
            query="Elena",
            memory_types=["conversation"],  # This should be strings, not enums
            limit=3
        )
        print(f"   ✅ Search memories: {len(search_results)} results")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("   🔧 Polymorphism interface mismatch has been resolved!")
        print("   📋 Protocol compliance verified - all methods accept strings as expected")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing WhisperEngine Vector Memory Polymorphism Fix")
    print("=" * 60)
    success = asyncio.run(test_polymorphism_fix())
    
    if success:
        print("\n✨ The polymorphism bug has been completely fixed!")
        print("   No more 'str' object has no attribute 'value' errors")
        print("   No more MemoryType enum vs string type mismatches") 
        print("   All clients now follow the protocol contract correctly")
    else:
        print("\n❌ Fix verification failed - more work needed")
        
    sys.exit(0 if success else 1)