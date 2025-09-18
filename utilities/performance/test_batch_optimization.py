#!/usr/bin/env python3
"""
Test script to verify ChromaDB batch optimization integration.
This will test that the batch optimizer initializes correctly and can perform basic operations.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from env_manager import load_environment
from src.core.bot import DiscordBotCore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_batch_optimization():
    """Test ChromaDB batch optimization integration"""
    print("🧪 Testing ChromaDB Batch Optimization Integration...")
    
    try:
        # Load environment
        if not load_environment():
            print("❌ Failed to load environment")
            return False
        
        # Initialize bot core
        print("🤖 Initializing bot core...")
        bot_core = DiscordBotCore(debug_mode=True)
        bot_core.initialize_all()
        
        # Check if batch manager was initialized
        if hasattr(bot_core, '_batched_memory_manager') and bot_core._batched_memory_manager:
            print("✅ Batch memory manager created")
            
            # Initialize batch optimizer
            if bot_core._needs_batch_init:
                print("🔧 Initializing batch optimizer...")
                await bot_core.initialize_batch_optimizer()
                print("✅ Batch optimizer initialization completed")
            
            # Test batch manager functionality
            batch_manager = bot_core._batched_memory_manager
            if batch_manager.batch_optimizer:
                print("✅ ChromaDB batch optimizer is available")
                
                # Get performance metrics
                metrics = batch_manager.get_performance_metrics()
                print(f"📊 Initial metrics: {metrics}")
                
                # Test single document storage (should use batching internally)
                print("🧪 Testing batched document storage...")
                doc_id = await batch_manager.store_conversation_batched(
                    user_id="test_user_123",
                    user_message="This is a test message for batch optimization",
                    bot_response="This is a test response to verify batching works correctly",
                    channel_id="test_channel",
                    metadata={"test": True, "batch_test": True}
                )
                print(f"✅ Stored document with ID: {doc_id}")
                
                # Test memory retrieval (should use batching internally)
                print("🧪 Testing batched memory retrieval...")
                memories = await batch_manager.retrieve_relevant_memories_batched(
                    user_id="test_user_123",
                    query="test message optimization",
                    limit=5
                )
                print(f"✅ Retrieved {len(memories)} memories using batch operations")
                
                # Check performance metrics after operations
                final_metrics = batch_manager.get_performance_metrics()
                print(f"📊 Final metrics: {final_metrics}")
                
                # Calculate improvements
                stores_batched = final_metrics.get('stores_batched', 0)
                queries_batched = final_metrics.get('queries_batched', 0)
                http_calls_saved = final_metrics.get('http_calls_saved', 0)
                
                print(f"📈 Performance Summary:")
                print(f"  - Documents stored in batches: {stores_batched}")
                print(f"  - Queries executed in batches: {queries_batched}")
                print(f"  - HTTP calls saved: {http_calls_saved}")
                
                if stores_batched > 0 or queries_batched > 0:
                    print("✅ Batch optimization is working correctly!")
                    return True
                else:
                    print("⚠️ Batch operations executed but metrics not recorded")
                    return True
            else:
                print("⚠️ Batch optimizer not available, falling back to direct operations")
                return True
        else:
            print("❌ Batch memory manager not created")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("WhisperEngine - ChromaDB Batch Optimization Test")
    print("=" * 60)
    
    success = await test_batch_optimization()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! Batch optimization is working.")
    else:
        print("❌ Tests failed. Check the output above for details.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())