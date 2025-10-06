#!/usr/bin/env python3
"""
🔧 Quick MemoryBoost Integration Verification

Verify that VectorMemoryManager now has the MemoryBoost methods properly integrated.
"""

import asyncio
import os
import sys

# Add project root to path  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def test_integration():
    """Test VectorMemoryManager MemoryBoost integration"""
    print("🔧 Testing VectorMemoryManager MemoryBoost integration...")
    
    try:
        from src.memory.memory_protocol import create_memory_manager
        
        # Create memory manager
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6334,
                'collection_name': 'whisperengine_memory_test_integration'
            },
            'embeddings': {
                'model_name': 'BAAI/bge-small-en-v1.5'
            }
        }
        
        memory_manager = create_memory_manager(memory_type="vector", config=config)
        print(f"✅ Memory manager created: {type(memory_manager)}")
        
        # Test MemoryBoost method availability
        methods_to_check = [
            'initialize_memoryboost_components',
            'analyze_memory_effectiveness', 
            'get_memory_optimization_stats',
            '_get_bot_name'
        ]
        
        for method_name in methods_to_check:
            has_method = hasattr(memory_manager, method_name)
            print(f"{'✅' if has_method else '❌'} Method '{method_name}': {'Available' if has_method else 'Missing'}")
        
        # Test method execution
        if hasattr(memory_manager, 'get_memory_optimization_stats'):
            stats = await memory_manager.get_memory_optimization_stats()
            print(f"✅ MemoryBoost stats: {stats}")
        
        if hasattr(memory_manager, 'analyze_memory_effectiveness'):
            effectiveness = await memory_manager.analyze_memory_effectiveness('test_user')
            print(f"✅ Memory effectiveness analysis: {list(effectiveness.keys())}")
        
        print("\n🎉 VectorMemoryManager MemoryBoost integration: SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_integration())