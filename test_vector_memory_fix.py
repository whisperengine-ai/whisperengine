#!/usr/bin/env python3
"""
Quick test to verify vector memory system loads without type errors
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append('src')

async def test_vector_memory_import():
    """Test that vector memory system can be imported and instantiated"""
    try:
        from memory.vector_memory_system import VectorMemorySystem
        print("✅ VectorMemorySystem imported successfully")
        
        # Try to create the memory manager using the factory
        from memory.memory_protocol import create_memory_manager
        memory_manager = create_memory_manager(memory_type="vector")
        print("✅ Memory manager created successfully")
        
        # Test a basic method call with the fixed interface
        try:
            # This should not crash with the type error anymore
            results = await memory_manager.retrieve_context_aware_memories(
                user_id="test_user",
                query="test query",
                limit=5
            )
            print("✅ retrieve_context_aware_memories called successfully")
            print(f"   Results: {len(results) if results else 0} memories found")
        except Exception as e:
            print(f"❌ Method call failed: {e}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_vector_memory_import())
    sys.exit(0 if success else 1)