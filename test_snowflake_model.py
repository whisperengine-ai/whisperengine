#!/usr/bin/env python3
"""
Test the new Snowflake Arctic embedding model integration
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.embedding_manager import LocalEmbeddingManager

async def test_snowflake_embeddings():
    """Test the new Snowflake model integration"""
    
    print("🧊 Testing Snowflake Arctic Embed XS Integration")
    print("=" * 60)
    
    # Initialize embedding manager
    print("🔧 Initializing LocalEmbeddingManager...")
    start_time = time.time()
    
    manager = LocalEmbeddingManager()
    
    # Test conversation samples
    test_messages = [
        "Hello! How are you today?",
        "I'm working on a Python project and need some help.",
        "The weather is beautiful outside.",
        "Can you explain machine learning concepts?",
        "I love listening to music while coding."
    ]
    
    print(f"⚡ Initialization completed in {time.time() - start_time:.2f}s")
    print(f"📋 Model: {manager.embedding_model_name}")
    
    # Test single embedding
    print("\n🚀 Testing Single Embedding Performance")
    print("-" * 40)
    
    test_text = "This is a test message for embedding generation."
    
    # Warm up
    warmup_embeddings = await manager.get_embeddings([test_text])
    
    # Time multiple runs
    times = []
    for i in range(5):
        start = time.time()
        embeddings = await manager.get_embeddings([test_text])
        embedding = embeddings[0]
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
        
        if i == 0:
            print(f"📏 Embedding dimensions: {len(embedding)}")
        
        print(f"   Run {i+1}: {elapsed:.2f}ms")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Single Embedding Stats:")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Min: {min_time:.2f}ms") 
    print(f"   Max: {max_time:.2f}ms")
    
    # Test batch processing
    print("\n📦 Testing Batch Embedding Performance")
    print("-" * 40)
    
    start = time.time()
    batch_embeddings = await manager.get_embeddings(test_messages)
    batch_time = time.time() - start
    
    per_item_time = (batch_time * 1000) / len(test_messages)
    
    print(f"   Batch size: {len(test_messages)}")
    print(f"   Total time: {batch_time:.3f}s")
    print(f"   Per item: {per_item_time:.2f}ms")
    print(f"   Efficiency vs single: {avg_time/per_item_time:.1f}x")
    
    # Quality check
    print("\n🎯 Quality Check")
    print("-" * 40)
    
    # Test semantic similarity
    similar_texts = [
        "I love programming in Python",
        "Python programming is my favorite"
    ]
    
    different_texts = [
        "I love programming in Python", 
        "The weather is sunny today"
    ]
    
    similar_embeddings = await manager.get_embeddings(similar_texts)
    different_embeddings = await manager.get_embeddings(different_texts)
    
    # Simple cosine similarity
    import numpy as np
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    similar_score = cosine_similarity(similar_embeddings[0], similar_embeddings[1])
    different_score = cosine_similarity(different_embeddings[0], different_embeddings[1])
    
    print(f"   Similar texts similarity: {similar_score:.3f}")
    print(f"   Different texts similarity: {different_score:.3f}")
    print(f"   Semantic distinction: {similar_score - different_score:.3f}")
    
    # Performance summary
    print("\n🏆 Performance Summary")
    print("=" * 60)
    print(f"✅ Model: {manager.embedding_model_name}")
    print(f"✅ Dimensions: {len(embedding)}")
    print(f"✅ Single embedding: {avg_time:.2f}ms (target: <3ms)")
    print(f"✅ Batch efficiency: {avg_time/per_item_time:.1f}x")
    print(f"✅ Semantic quality: {'Good' if similar_score - different_score > 0.1 else 'Needs review'}")
    
    if avg_time < 3.0:
        print("🎯 EXCELLENT: Single embedding time meets real-time chat requirements!")
    elif avg_time < 5.0:
        print("👍 GOOD: Single embedding time acceptable for most use cases")
    else:
        print("⚠️  WARNING: Single embedding time may impact real-time performance")
    
    return {
        'model': manager.embedding_model_name,
        'dimensions': len(embedding),
        'single_avg_ms': avg_time,
        'batch_per_item_ms': per_item_time,
        'efficiency': avg_time/per_item_time,
        'semantic_quality': similar_score - different_score
    }

if __name__ == "__main__":
    result = asyncio.run(test_snowflake_embeddings())
    print(f"\n📋 Test completed successfully!")