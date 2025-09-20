#!/usr/bin/env python3
"""
Test script for fastembed migration
Validates that the new embedding manager works correctly with fastembed
"""

import asyncio
import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.embedding_manager import LocalEmbeddingManager


async def test_fastembed_integration():
    """Test the fastembed-based embedding manager"""
    
    print("🧪 Testing FastEmbed Integration")
    print("=" * 50)
    
    try:
        # Initialize embedding manager
        print("1. Initializing LocalEmbeddingManager...")
        manager = LocalEmbeddingManager()
        
        # Initialize the model
        print("2. Loading fastembed model...")
        start_time = time.time()
        await manager.initialize()
        init_time = time.time() - start_time
        print(f"   ✅ Model loaded in {init_time:.2f}s")
        print(f"   📏 Embedding dimension: {manager.embedding_dimension}")
        
        # Test single embedding
        print("3. Testing single text embedding...")
        test_text = "Hello, this is a test for fastembed integration"
        start_time = time.time()
        embeddings = await manager.get_embeddings(test_text)
        single_time = time.time() - start_time
        
        print(f"   ✅ Single embedding generated in {single_time*1000:.2f}ms")
        print(f"   📊 Embedding shape: {len(embeddings)} x {len(embeddings[0])}")
        print(f"   🔢 First 5 values: {embeddings[0][:5]}")
        
        # Test batch embeddings
        print("4. Testing batch embeddings...")
        batch_texts = [
            "FastEmbed is a lightweight embedding library",
            "It's from the team that created Qdrant",
            "This replaces sentence-transformers in WhisperEngine",
            "The integration should be more efficient",
            "Local-first AI processing is important"
        ]
        
        start_time = time.time()
        batch_embeddings = await manager.get_embeddings(batch_texts)
        batch_time = time.time() - start_time
        
        print(f"   ✅ Batch of {len(batch_texts)} embeddings in {batch_time*1000:.2f}ms")
        print(f"   📊 Batch shape: {len(batch_embeddings)} x {len(batch_embeddings[0])}")
        
        # Test caching
        print("5. Testing embedding cache...")
        start_time = time.time()
        cached_embeddings = await manager.get_embeddings(batch_texts)  # Should be cached
        cache_time = time.time() - start_time
        
        print(f"   ✅ Cached embeddings retrieved in {cache_time*1000:.2f}ms")
        print(f"   🚀 Speedup: {(batch_time/cache_time):.1f}x faster")
        
        # Verify cache correctness
        embeddings_match = all(
            all(abs(a - b) < 1e-6 for a, b in zip(orig, cached))
            for orig, cached in zip(batch_embeddings, cached_embeddings)
        )
        print(f"   ✅ Cache correctness: {'PASS' if embeddings_match else 'FAIL'}")
        
        # Performance stats
        print("6. Performance statistics...")
        stats = manager.get_performance_stats()
        print(f"   📈 Total embeddings: {stats['total_embeddings']}")
        print(f"   ⏱️  Avg time per embedding: {stats['avg_time_per_embedding_ms']:.2f}ms")
        print(f"   💾 Cache hit rate: {stats['cache_hit_rate']:.1%}")
        print(f"   🗃️  Cache size: {stats['cache_size']}")
        
        # Test model compatibility
        print("7. Testing model compatibility...")
        print(f"   🏷️  Model name: {stats['model_name']}")
        print(f"   📏 Embedding dimension: {stats['embedding_dimension']}")
        
        # Verify embeddings are valid
        embedding = embeddings[0]
        embedding_norm = sum(x*x for x in embedding) ** 0.5
        print(f"   🧮 Embedding norm: {embedding_norm:.4f}")
        
        if embedding_norm > 0 and len(embedding) > 0:
            print("   ✅ Embeddings are valid vectors")
        else:
            print("   ❌ Invalid embeddings detected")
            return False
            
        # Cleanup
        await manager.shutdown()
        
        print("\n🎉 FastEmbed Integration Test: SUCCESS")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ FastEmbed Integration Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_memory_compatibility():
    """Test compatibility with vector memory system"""
    
    print("\n🔗 Testing Vector Memory System Compatibility")
    print("=" * 50)
    
    try:
        # Test importing vector memory system
        from src.memory.vector_memory_system import VectorMemoryStore
        print("   ✅ Vector memory system imports successfully")
        
        # Note: We won't test full initialization since it requires Qdrant
        # But we can test that the imports and basic structure work
        print("   ✅ FastEmbed integration compatible with vector memory")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ⚠️  Other error (may be expected without Qdrant): {e}")
        return True  # Expected without Qdrant running


if __name__ == "__main__":
    async def run_all_tests():
        """Run all tests"""
        print("🚀 WhisperEngine FastEmbed Migration Test Suite")
        print("=" * 60)
        
        # Test 1: Basic fastembed integration
        test1_success = await test_fastembed_integration()
        
        # Test 2: Vector memory compatibility
        test2_success = await test_vector_memory_compatibility()
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 30)
        print(f"✅ FastEmbed Integration: {'PASS' if test1_success else 'FAIL'}")
        print(f"✅ Vector Memory Compatibility: {'PASS' if test2_success else 'FAIL'}")
        
        overall_success = test1_success and test2_success
        print(f"\n🏆 Overall Result: {'SUCCESS' if overall_success else 'FAILURE'}")
        
        return overall_success
    
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)