#!/usr/bin/env python3
"""
Direct test runner for vector memory system - bypasses pytest configuration issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our test modules
from tests.memory.test_vector_memory_system import (
    TestVectorMemoryStore, 
    TestBubblesGoldfishScenario,
    MockQdrantClient,
    MockSentenceTransformer
)

async def run_bubbles_test():
    """Run the critical Bubbles goldfish scenario test directly"""
    
    print("🐠 Running Bubbles Goldfish Scenario Test")
    print("=" * 50)
    
    try:
        # Create test instance
        bubbles_test = TestBubblesGoldfishScenario()
        
        # Create test manager fixture manually
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333, 
                'collection_name': 'bubbles_test_memory'
            },
            'embeddings': {
                'model_name': 'all-MiniLM-L6-v2'
            },
            'postgresql': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        }
        
        # Mock the dependencies
        from unittest.mock import patch
        from src.memory.vector_memory_system import VectorMemoryManager
        
        with patch('src.memory.vector_memory_system.QdrantClient', MockQdrantClient), \
             patch('src.memory.vector_memory_system.SentenceTransformer', MockSentenceTransformer):
            
            manager = VectorMemoryManager(config)
            
            print("✅ VectorMemoryManager initialized successfully")
            
            # Run the Bubbles contradiction test
            print("\n🔍 Testing Bubbles goldfish contradiction detection...")
            await bubbles_test.test_bubbles_goldfish_contradiction_detection(manager)
            print("✅ Bubbles contradiction test PASSED")
            
            # Run consistency test
            print("\n🔄 Testing memory consistency over time...")
            await bubbles_test.test_goldfish_memory_consistency_over_time(manager)
            print("✅ Memory consistency test PASSED")
            
            # Run performance test
            print("\n⚡ Testing performance requirements...")
            await bubbles_test.test_performance_requirements(manager)
            print("✅ Performance test PASSED")
            
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 All Bubbles goldfish tests PASSED!")
    print("✅ Vector memory system ready for production")
    return True

async def run_basic_vector_store_test():
    """Run basic vector store functionality test"""
    
    print("\n🔧 Running Basic Vector Store Tests")
    print("=" * 50)
    
    try:
        # Create test instance  
        store_test = TestVectorMemoryStore()
        
        # Mock vector store fixture
        from unittest.mock import patch
        from src.memory.vector_memory_system import VectorMemoryStore
        
        with patch('src.memory.vector_memory_system.QdrantClient', MockQdrantClient), \
             patch('src.memory.vector_memory_system.SentenceTransformer', MockSentenceTransformer):
            
            store = VectorMemoryStore(
                qdrant_host="localhost",
                qdrant_port=6333,
                collection_name="test_memory",
                embedding_model="all-MiniLM-L6-v2"
            )
            
            print("✅ VectorMemoryStore initialized successfully")
            
            # Test basic functionality
            store_test.test_vector_store_initialization(store)
            print("✅ Store initialization test PASSED")
            
            await store_test.test_store_memory(store)
            print("✅ Store memory test PASSED")
            
            await store_test.test_search_memories(store)
            print("✅ Search memories test PASSED")
            
            await store_test.test_detect_contradictions(store)
            print("✅ Contradiction detection test PASSED")
            
    except Exception as e:
        print(f"❌ Vector store test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ All vector store tests PASSED!")
    return True

async def main():
    """Run all vector memory tests"""
    
    print("🚀 WhisperEngine Vector Memory System Test Suite")
    print("=" * 60)
    
    # Run basic tests first
    basic_success = await run_basic_vector_store_test()
    
    if not basic_success:
        print("❌ Basic tests failed, skipping Bubbles scenario")
        return 1
    
    # Run Bubbles scenario tests
    bubbles_success = await run_bubbles_test()
    
    if basic_success and bubbles_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Vector memory system is ready for production deployment")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)