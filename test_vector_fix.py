#!/usr/bin/env python3
"""
Quick test script to verify Qdrant v1.15.4 compatibility fixes
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from memory.vector_memory_system import VectorMemoryStore, MemoryType, VectorMemory
from datetime import datetime
import uuid

async def test_vector_operations():
    """Test basic vector operations with the updated Qdrant v1.15.4"""
    print("🧪 Testing Qdrant v1.15.4 compatibility...")
    
    # Initialize memory system
    memory_system = VectorMemoryStore()
    await memory_system.initialize()
    
    # Create a test memory
    test_memory = VectorMemory(
        id=str(uuid.uuid4()),
        user_id="test_user_12345",
        memory_type=MemoryType.CONVERSATION,
        content="I love playing with my cat Luna. She's a gray tabby.",
        timestamp=datetime.now(),
        confidence=0.9,
        source="test",
        metadata={}
    )
    
    print(f"📝 Storing test memory: {test_memory.content}")
    
    try:
        # Test storage
        memory_id = await memory_system.store_memory(test_memory)
        print(f"✅ Memory stored successfully with ID: {memory_id}")
        
        # Test search
        search_results = await memory_system.search_memories(
            user_id="test_user_12345",
            query="cat pet",
            top_k=3
        )
        print(f"✅ Search completed, found {len(search_results)} results")
        
        if search_results:
            print(f"📋 Found: {search_results[0].content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector operation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_vector_operations())
    if result:
        print("🎉 All vector operations successful!")
        sys.exit(0)
    else:
        print("💥 Vector operations failed!")
        sys.exit(1)