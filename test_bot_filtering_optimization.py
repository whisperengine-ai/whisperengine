#!/usr/bin/env python3
"""
Test Bot-Specific Filtering in Optimization System

Verifies that QdrantQueryOptimizer respects bot_name filtering 
for proper multi-bot segmentation and performance.
"""

import asyncio
import os
import sys
import logging
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_bot_filtering_optimization():
    """Test that bot filtering works correctly in the optimization system."""
    
    # Set up test environment
    os.environ["VECTOR_QDRANT_HOST"] = "localhost"
    os.environ["VECTOR_QDRANT_PORT"] = "6333"
    os.environ["VECTOR_QDRANT_COLLECTION"] = "test_bot_filtering"
    os.environ["MEMORY_SYSTEM_TYPE"] = "vector"
    
    print("🧪 Testing Bot-Specific Filtering in Optimization System")
    print("=" * 60)
    
    try:
        from memory.memory_protocol import create_memory_manager
        from memory.vector_memory_system import VectorMemory, MemoryType
        from memory.qdrant_optimization import QdrantQueryOptimizer
        
        test_user_id = "test_user_bot_filtering"
        
        # Test 1: Store memories as different bots
        print("\n🤖 Step 1: Storing memories as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_memory_manager = create_memory_manager(memory_type="vector")
        
        elena_memory = VectorMemory(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            content="Elena's marine biology knowledge about coral reefs",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            source="elena_test",
            metadata={"topic": "marine_biology", "bot_test": "elena"}
        )
        
        await elena_memory_manager.vector_store.store_memory(elena_memory)
        print("   ✅ Elena memory stored")
        
        print("\n🤖 Step 2: Storing memories as Marcus...")
        os.environ["DISCORD_BOT_NAME"] = "Marcus"
        marcus_memory_manager = create_memory_manager(memory_type="vector")
        
        marcus_memory = VectorMemory(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            content="Marcus's AI research insights about neural networks",
            memory_type=MemoryType.FACT,
            timestamp=datetime.utcnow(),
            source="marcus_test",
            metadata={"topic": "ai_research", "bot_test": "marcus"}
        )
        
        await marcus_memory_manager.vector_store.store_memory(marcus_memory)
        print("   ✅ Marcus memory stored")
        
        # Test 2: Test optimization as Elena (should only see Elena's memories)
        print("\n🔍 Step 3: Testing optimization filtering as Elena...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        elena_optimizer = QdrantQueryOptimizer(vector_manager=elena_memory_manager)
        
        elena_results = await elena_optimizer.optimized_search(
            query="research knowledge insights",
            user_id=test_user_id,
            query_type="fact_lookup",
            user_history={}
        )
        
        print(f"   📊 Elena optimizer found {len(elena_results)} memories:")
        elena_found_own = False
        elena_found_marcus = False
        
        for result in elena_results:
            content = result.get('content', '')
            print(f"      - {content}")
            if "marine biology" in content or "coral reefs" in content:
                elena_found_own = True
            elif "neural networks" in content or "AI research" in content:
                elena_found_marcus = True
        
        # Test 3: Test optimization as Marcus (should only see Marcus's memories)
        print("\n🔍 Step 4: Testing optimization filtering as Marcus...")
        os.environ["DISCORD_BOT_NAME"] = "Marcus"
        marcus_optimizer = QdrantQueryOptimizer(vector_manager=marcus_memory_manager)
        
        marcus_results = await marcus_optimizer.optimized_search(
            query="research knowledge insights",
            user_id=test_user_id,
            query_type="fact_lookup",
            user_history={}
        )
        
        print(f"   📊 Marcus optimizer found {len(marcus_results)} memories:")
        marcus_found_own = False
        marcus_found_elena = False
        
        for result in marcus_results:
            content = result.get('content', '')
            print(f"      - {content}")
            if "neural networks" in content or "AI research" in content:
                marcus_found_own = True
            elif "marine biology" in content or "coral reefs" in content:
                marcus_found_elena = True
        
        # Test 4: Test raw Qdrant filters in optimizer
        print("\n🔧 Step 5: Testing raw Qdrant filter generation...")
        os.environ["DISCORD_BOT_NAME"] = "Elena"
        
        filters = await elena_optimizer._build_qdrant_filters(
            user_id=test_user_id,
            filters={"memory_type": "fact"}
        )
        
        print(f"   🔍 Qdrant filters for Elena: {filters}")
        
        # Check if bot_name filter is present
        bot_filter_found = False
        for condition in filters.get('must', []):
            if hasattr(condition, 'key') and condition.key == 'bot_name':
                bot_filter_found = True
                print(f"   ✅ Bot filter found: {condition.match.value}")
                break
        
        # Test Results
        print("\n📊 Test Results:")
        print("=" * 40)
        
        success = True
        
        if elena_found_own and not elena_found_marcus:
            print("✅ Elena optimizer correctly isolated to Elena's memories")
        else:
            print(f"❌ Elena optimizer failed isolation (own: {elena_found_own}, marcus: {elena_found_marcus})")
            success = False
        
        if marcus_found_own and not marcus_found_elena:
            print("✅ Marcus optimizer correctly isolated to Marcus's memories")
        else:
            print(f"❌ Marcus optimizer failed isolation (own: {marcus_found_own}, elena: {marcus_found_elena})")
            success = False
        
        if bot_filter_found:
            print("✅ QdrantQueryOptimizer correctly adds bot_name filtering")
        else:
            print("❌ QdrantQueryOptimizer missing bot_name filtering")
            success = False
        
        if success:
            print("\n🎉 All bot filtering optimization tests passed!")
            print("   ✅ Multi-bot memory segmentation working correctly")
            print("   ✅ Performance optimized with bot-specific filtering")
            print("   ✅ No cross-bot contamination detected")
        else:
            print("\n⚠️  Some bot filtering tests failed!")
            print("   🔧 Check bot_name filtering implementation")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_bot_filtering_optimization())
    sys.exit(0 if result else 1)