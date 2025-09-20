#!/usr/bin/env python3
"""
Test fresh model performance without cache
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.embedding_manager import LocalEmbeddingManager

async def test_fresh_performance():
    """Test with fresh model instance to get realistic timings"""
    
    print("🧊 Fresh Snowflake Arctic Model Performance Test")
    print("=" * 60)
    
    # Create fresh manager
    manager = LocalEmbeddingManager()
    
    # Test with varied texts to avoid any caching
    test_texts = [
        f"This is test message number {i} with unique content about various topics like {topic}" 
        for i, topic in enumerate([
            "machine learning algorithms", 
            "quantum computing principles",
            "sustainable energy solutions", 
            "space exploration missions",
            "biotechnology innovations"
        ])
    ]
    
    print(f"📋 Model: {manager.embedding_model_name}")
    
    # Test single embeddings with fresh texts
    print("\n🚀 Single Embedding Performance (Fresh)")
    print("-" * 40)
    
    times = []
    dimensions = None
    
    for i, text in enumerate(test_texts):
        start = time.time()
        embeddings = await manager.get_embeddings([text])
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        if dimensions is None:
            dimensions = len(embeddings[0])
            print(f"📏 Embedding dimensions: {dimensions}")
        
        print(f"   Text {i+1}: {elapsed:.2f}ms")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Fresh Performance Stats:")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Min: {min_time:.2f}ms")
    print(f"   Max: {max_time:.2f}ms")
    
    # Test batch performance
    batch_texts = [
        f"Batch test message {i}: {content}" 
        for i, content in enumerate([
            "artificial intelligence research",
            "climate change mitigation", 
            "cryptocurrency blockchain",
            "renewable energy storage",
            "neural network architectures",
            "quantum machine learning",
            "bioengineering applications",
            "autonomous vehicle systems"
        ])
    ]
    
    print(f"\n📦 Batch Performance Test ({len(batch_texts)} items)")
    print("-" * 40)
    
    start = time.time()
    batch_embeddings = await manager.get_embeddings(batch_texts)
    batch_time = time.time() - start
    
    per_item_time = (batch_time * 1000) / len(batch_texts)
    efficiency = avg_time / per_item_time if per_item_time > 0 else 0
    
    print(f"   Total time: {batch_time:.3f}s")
    print(f"   Per item: {per_item_time:.2f}ms")
    print(f"   Efficiency vs single: {efficiency:.1f}x")
    
    # Performance verdict
    print(f"\n🏆 Performance Verdict")
    print("=" * 60)
    print(f"✅ Model: snowflake/snowflake-arctic-embed-xs")
    print(f"✅ Dimensions: {dimensions}")
    print(f"✅ Single avg: {avg_time:.2f}ms")
    print(f"✅ Batch per-item: {per_item_time:.2f}ms")
    print(f"✅ Batch efficiency: {efficiency:.1f}x")
    
    if avg_time < 2.0:
        print("🎯 OUTSTANDING: Sub-2ms performance for real-time chat!")
    elif avg_time < 5.0:
        print("🎯 EXCELLENT: Well within real-time requirements!")
    else:
        print("⚠️  REVIEW: May need optimization for real-time use")
    
    return {
        'avg_single_ms': avg_time,
        'batch_per_item_ms': per_item_time,
        'efficiency': efficiency,
        'dimensions': dimensions
    }

if __name__ == "__main__":
    result = asyncio.run(test_fresh_performance())
    print(f"\n📋 Fresh performance test completed!")