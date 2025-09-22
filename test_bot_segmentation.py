#!/usr/bin/env python3
"""
Test Bot Memory Segmentation

Simple test to verify bot_name field is being added to Qdrant payloads
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

async def test_bot_segmentation():
    """Test that bot names are properly segmented in memory storage"""
    
    # Set local Qdrant configuration
    os.environ["VECTOR_QDRANT_HOST"] = "localhost"
    os.environ["VECTOR_QDRANT_PORT"] = "6333" 
    os.environ["VECTOR_QDRANT_GRPC_PORT"] = "6334"
    os.environ["VECTOR_QDRANT_COLLECTION"] = "whisperengine_memory"
    os.environ["MEMORY_SYSTEM_TYPE"] = "vector"
    
    try:
        from memory.memory_protocol import create_memory_manager
        from memory.vector_memory_system import MemoryType, VectorMemory
        
        print("🧪 Testing Bot Memory Segmentation")
        print("=" * 40)
        
        test_user_id = "test_user_segmentation"
        
        # Test 1: Create Elena memory
        print("\n🤖 Creating memory as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_memory = create_memory_manager(memory_type="vector")
        
        elena_test_memory = VectorMemory(
            id=str(uuid.uuid4()),  # Use proper UUID
            user_id=test_user_id,
            content="Elena test memory for segmentation testing",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            confidence=0.9,
            source="test_segmentation"
        )
        
        await elena_memory.vector_store.store_memory(elena_test_memory)
        print("   ✅ Elena memory stored successfully")
        
        # Test 2: Create Gabriel memory  
        print("\n🤖 Creating memory as Gabriel...")
        os.environ["DISCORD_BOT_NAME"] = "Gabriel"
        gabriel_memory = create_memory_manager(memory_type="vector")
        
        gabriel_test_memory = VectorMemory(
            id=str(uuid.uuid4()),  # Use proper UUID
            user_id=test_user_id,
            content="Gabriel test memory for segmentation testing",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            confidence=0.9,
            source="test_segmentation"
        )
        
        await gabriel_memory.vector_store.store_memory(gabriel_test_memory)
        print("   ✅ Gabriel memory stored successfully")
        
        # Small delay for indexing
        await asyncio.sleep(1)
        
        # Test 3: Search as Elena
        print("\n🔍 Searching as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_search = create_memory_manager(memory_type="vector")
        
        elena_results = await elena_search.vector_store.search_memories_with_qdrant_intelligence(
            query="segmentation testing",
            user_id=test_user_id,
            top_k=5,
            min_score=0.0
        )
        
        print(f"   📊 Elena found {len(elena_results)} memories:")
        elena_found_own = False
        elena_found_gabriel = False
        
        for result in elena_results:
            content = result.get('content', '')
            print(f"      - {content}")
            if "Elena test memory" in content:
                elena_found_own = True
            elif "Gabriel test memory" in content:
                elena_found_gabriel = True
        
        # Test 4: Search as Gabriel
        print("\n🔍 Searching as Gabriel...")
        os.environ["DISCORD_BOT_NAME"] = "Gabriel"
        gabriel_search = create_memory_manager(memory_type="vector")
        
        gabriel_results = await gabriel_search.vector_store.search_memories_with_qdrant_intelligence(
            query="segmentation testing",
            user_id=test_user_id,
            top_k=5,
            min_score=0.0
        )
        
        print(f"   📊 Gabriel found {len(gabriel_results)} memories:")
        gabriel_found_own = False
        gabriel_found_elena = False
        
        for result in gabriel_results:
            content = result.get('content', '')
            print(f"      - {content}")
            if "Gabriel test memory" in content:
                gabriel_found_own = True
            elif "Elena test memory" in content:
                gabriel_found_elena = True
        
        # Results Analysis
        print("\n📊 Segmentation Test Results:")
        print("=" * 35)
        
        elena_isolation = elena_found_own and not elena_found_gabriel
        gabriel_isolation = gabriel_found_own and not gabriel_found_elena
        
        print(f"🤖 Elena segmentation: {'✅ WORKING' if elena_isolation else '❌ FAILED'}")
        print(f"   - Found own memory: {'✅' if elena_found_own else '❌'}")
        print(f"   - Isolated from Gabriel: {'✅' if not elena_found_gabriel else '❌'}")
        
        print(f"🤖 Gabriel segmentation: {'✅ WORKING' if gabriel_isolation else '❌ FAILED'}")
        print(f"   - Found own memory: {'✅' if gabriel_found_own else '❌'}")
        print(f"   - Isolated from Elena: {'✅' if not gabriel_found_elena else '❌'}")
        
        overall_success = elena_isolation and gabriel_isolation
        
        print(f"\n🎯 Overall Bot Segmentation: {'✅ SUCCESS - Bots properly isolated!' if overall_success else '❌ FAILED'}")
        
        if overall_success:
            print("\n🎉 Memory segmentation is working correctly!")
            print("   Each bot only sees its own memories in searches.")
            print("   The bot_name payload field is properly filtering results.")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot_segmentation())
    sys.exit(0 if result else 1)