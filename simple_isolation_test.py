#!/usr/bin/env python3
"""
Simple Bot Memory Isolation Test

Tests that different bot names result in separate memory storage.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

async def test_memory_isolation():
    """Test basic memory isolation between bots"""
    
    try:
        from memory.memory_protocol import create_memory_manager
        from memory.vector_memory_system import MemoryType, VectorMemory
        
        print("🧪 Testing Bot Memory Isolation")
        print("=" * 40)
        
        test_user_id = "test_user_isolation"
        
        # Test with Elena bot
        print("\n🤖 Testing as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_memory = create_memory_manager(memory_type="vector")
        
        # Store a test memory for Elena
        elena_test_memory = VectorMemory(
            user_id=test_user_id,
            content="Elena loves helping with emotional support and caring conversations",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            confidence=0.9,
            source="test_isolation_elena"
        )
        
        await elena_memory.vector_store.store_memory(elena_test_memory)
        print("   ✅ Stored Elena's memory")
        
        # Test with Gabriel bot
        print("\n🤖 Testing as Gabriel...")
        os.environ["DISCORD_BOT_NAME"] = "Gabriel"
        gabriel_memory = create_memory_manager(memory_type="vector")
        
        # Store a test memory for Gabriel
        gabriel_test_memory = VectorMemory(
            user_id=test_user_id,
            content="Gabriel explores consciousness and philosophical questions about existence",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            confidence=0.9,
            source="test_isolation_gabriel"
        )
        
        await gabriel_memory.vector_store.store_memory(gabriel_test_memory)
        print("   ✅ Stored Gabriel's memory")
        
        # Wait for indexing
        await asyncio.sleep(1)
        
        # Search as Elena - should only see Elena's memories
        print("\n🔍 Searching as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_memory_search = create_memory_manager(memory_type="vector")
        
        elena_results = await elena_memory_search.vector_store.search_memories_with_qdrant_intelligence(
            query="test isolation",
            user_id=test_user_id,
            top_k=10,
            min_score=0.0
        )
        
        print(f"   📊 Elena found {len(elena_results)} memories:")
        elena_has_own = False
        elena_has_others = False
        
        for result in elena_results:
            content = result.get('content', '')
            print(f"      - {content[:60]}...")
            if "Elena loves helping" in content:
                elena_has_own = True
            elif "Gabriel explores" in content:
                elena_has_others = True
        
        # Search as Gabriel - should only see Gabriel's memories
        print("\n🔍 Searching as Gabriel...")
        os.environ["DISCORD_BOT_NAME"] = "Gabriel"
        gabriel_memory_search = create_memory_manager(memory_type="vector")
        
        gabriel_results = await gabriel_memory_search.vector_store.search_memories_with_qdrant_intelligence(
            query="test isolation",
            user_id=test_user_id,
            top_k=10,
            min_score=0.0
        )
        
        print(f"   📊 Gabriel found {len(gabriel_results)} memories:")
        gabriel_has_own = False
        gabriel_has_others = False
        
        for result in gabriel_results:
            content = result.get('content', '')
            print(f"      - {content[:60]}...")
            if "Gabriel explores" in content:
                gabriel_has_own = True
            elif "Elena loves helping" in content:
                gabriel_has_others = True
        
        # Results
        print("\n📊 Test Results:")
        print("=" * 30)
        
        elena_isolated = elena_has_own and not elena_has_others
        gabriel_isolated = gabriel_has_own and not gabriel_has_others
        
        print(f"🤖 Elena isolation: {'✅ PASSED' if elena_isolated else '❌ FAILED'}")
        print(f"   - Found own memory: {'✅' if elena_has_own else '❌'}")
        print(f"   - Found other memories: {'❌' if not elena_has_others else '⚠️'}")
        
        print(f"🤖 Gabriel isolation: {'✅ PASSED' if gabriel_isolated else '❌ FAILED'}")
        print(f"   - Found own memory: {'✅' if gabriel_has_own else '❌'}")
        print(f"   - Found other memories: {'❌' if not gabriel_has_others else '⚠️'}")
        
        overall_success = elena_isolated and gabriel_isolated
        print(f"\n🎯 Overall: {'✅ MEMORY ISOLATION WORKING' if overall_success else '❌ ISOLATION FAILED'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_memory_isolation())
    sys.exit(0 if result else 1)