#!/usr/bin/env python3
"""
FastEmbed Model Comparison for WhisperEngine
Analyzes different embedding models for conversational AI use case
"""

import asyncio
import sys
import os
import time
import statistics

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_model_performance(model_name, test_texts):
    """Test a specific embedding model"""
    
    try:
        from fastembed import TextEmbedding
        
        print(f"\n🧪 Testing {model_name}")
        print("=" * 50)
        
        # Initialize model
        start_time = time.time()
        model = TextEmbedding(model_name=model_name)
        init_time = time.time() - start_time
        
        # Get model info
        test_embedding = list(model.embed(["test"]))[0]
        dimension = len(test_embedding)
        
        print(f"⚡ Initialization: {init_time:.2f}s")
        print(f"📏 Dimensions: {dimension}")
        
        # Test single embedding speed
        single_times = []
        for text in test_texts[:5]:  # Test 5 samples
            start = time.time()
            list(model.embed([text]))
            single_times.append((time.time() - start) * 1000)
        
        avg_single = statistics.mean(single_times)
        
        # Test batch embedding speed
        start = time.time()
        list(model.embed(test_texts))
        batch_time = (time.time() - start) * 1000
        per_item_batch = batch_time / len(test_texts)
        
        print(f"🚀 Single embedding: {avg_single:.2f}ms")
        print(f"📦 Batch per item: {per_item_batch:.2f}ms")
        print(f"📊 Batch efficiency: {(avg_single/per_item_batch):.1f}x")
        
        return {
            'model_name': model_name,
            'init_time': init_time,
            'dimensions': dimension,
            'single_speed': avg_single,
            'batch_speed': per_item_batch,
            'batch_efficiency': avg_single/per_item_batch
        }
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return None


async def compare_embedding_models():
    """Compare different fastembed models for conversational AI"""
    
    print("🔍 FastEmbed Model Comparison for WhisperEngine")
    print("=" * 60)
    
    # Test texts representing typical WhisperEngine use cases
    test_texts = [
        "How are you feeling today?",
        "I love my goldfish named Bubbles",
        "Can you help me with a programming question?",
        "My favorite color is blue and I enjoy hiking",
        "I had a great conversation yesterday about AI",
        "What's the weather like in your area?",
        "I'm working on a new project using Python",
        "My cat is very playful and loves toys",
        "I enjoy reading science fiction novels",
        "Can you remember what we talked about last time?"
    ]
    
    # Models to test (compatible with fastembed)
    models_to_test = [
        # Small, fast models (good for real-time chat)
        "BAAI/bge-small-en-v1.5",      # Current choice - 384 dim
        "sentence-transformers/all-MiniLM-L6-v2",  # Previous choice - 384 dim
        "sentence-transformers/all-MiniLM-L12-v2", # Slightly larger - 384 dim
        
        # Medium models (balance speed/quality)
        "BAAI/bge-base-en-v1.5",       # 768 dim - better quality
        "sentence-transformers/all-mpnet-base-v2",  # 768 dim - high quality
        
        # Small multilingual (if needed)
        "BAAI/bge-small-en-v1.5",      # English-focused
    ]
    
    results = []
    
    for model_name in models_to_test[:3]:  # Test first 3 to avoid long runtime
        result = await test_model_performance(model_name, test_texts)
        if result:
            results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Analysis and recommendations
    print(f"\n📊 Model Comparison Summary")
    print("=" * 60)
    
    for result in results:
        print(f"\n🏷️  {result['model_name']}")
        print(f"   📏 Dimensions: {result['dimensions']}")
        print(f"   ⚡ Init time: {result['init_time']:.2f}s")
        print(f"   🚀 Single: {result['single_speed']:.2f}ms")
        print(f"   📦 Batch: {result['batch_speed']:.2f}ms")
        print(f"   📈 Efficiency: {result['batch_efficiency']:.1f}x")
    
    # Recommendations
    print(f"\n🎯 Recommendations for WhisperEngine")
    print("=" * 50)
    
    if results:
        # Find fastest model
        fastest = min(results, key=lambda x: x['single_speed'])
        most_efficient = max(results, key=lambda x: x['batch_efficiency'])
        
        print(f"🏃 Fastest single: {fastest['model_name']} ({fastest['single_speed']:.2f}ms)")
        print(f"📦 Most efficient batch: {most_efficient['model_name']} ({most_efficient['batch_efficiency']:.1f}x)")
        
        # Recommendation logic
        print(f"\n✅ Recommended for WhisperEngine:")
        
        # For conversational AI, prioritize speed while maintaining quality
        if any(r['model_name'] == 'BAAI/bge-small-en-v1.5' for r in results):
            bge_result = next(r for r in results if r['model_name'] == 'BAAI/bge-small-en-v1.5')
            print(f"   🥇 BAAI/bge-small-en-v1.5")
            print(f"   📝 Reasons:")
            print(f"      • Optimized for English conversations")
            print(f"      • 384 dimensions (good for memory efficiency)")
            print(f"      • Modern BAAI architecture (2023+)")
            print(f"      • {bge_result['single_speed']:.2f}ms per embedding")
            print(f"      • Compatible with Qdrant (same team)")
        
        print(f"\n⚖️  Speed vs Quality Trade-offs:")
        print(f"   🚀 For real-time chat: Prefer <5ms single embedding")
        print(f"   🎯 For quality: 768-dim models (but 2x slower)")
        print(f"   💾 For memory: 384-dim models (current choice)")
        
    return results


if __name__ == "__main__":
    asyncio.run(compare_embedding_models())