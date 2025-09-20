#!/usr/bin/env python3
"""
Comprehensive FastEmbed Model Analysis for WhisperEngine
Tests the top embedding models from the FastEmbed supported list
"""

import asyncio
import sys
import os
import time
import statistics

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_model_comprehensive(model_name, test_texts):
    """Test a specific embedding model comprehensively"""
    
    try:
        from fastembed import TextEmbedding
        
        print(f"\n🧪 Testing {model_name}")
        print("=" * 60)
        
        # Initialize model
        start_time = time.time()
        model = TextEmbedding(model_name=model_name)
        init_time = time.time() - start_time
        
        # Get model info
        test_embedding = list(model.embed(["test"]))[0]
        dimension = len(test_embedding)
        
        print(f"⚡ Initialization: {init_time:.2f}s")
        print(f"📏 Dimensions: {dimension}")
        
        # Test single embedding speed (10 samples)
        single_times = []
        for text in test_texts[:10]:
            start = time.time()
            list(model.embed([text]))
            single_times.append((time.time() - start) * 1000)
        
        avg_single = statistics.mean(single_times)
        min_single = min(single_times)
        max_single = max(single_times)
        
        # Test batch embedding speed
        start = time.time()
        list(model.embed(test_texts))
        batch_time = (time.time() - start) * 1000
        per_item_batch = batch_time / len(test_texts)
        
        # Test cache/warmup performance
        start = time.time()
        list(model.embed(test_texts))  # Second run
        batch_time_warm = (time.time() - start) * 1000
        per_item_warm = batch_time_warm / len(test_texts)
        
        print(f"🚀 Single embedding:")
        print(f"   Avg: {avg_single:.2f}ms, Min: {min_single:.2f}ms, Max: {max_single:.2f}ms")
        print(f"📦 Batch per item (cold): {per_item_batch:.2f}ms")
        print(f"🔥 Batch per item (warm): {per_item_warm:.2f}ms")
        print(f"📊 Batch efficiency: {(avg_single/per_item_batch):.1f}x")
        
        # Calculate quality score (higher dimensions generally = better quality)
        quality_score = dimension / 384  # Normalize to 384 as baseline
        
        # Calculate speed score (lower is better, normalized)
        speed_score = 10 / avg_single if avg_single > 0 else 0
        
        # Calculate size efficiency (smaller models are better for deployment)
        # Estimate model size based on dimensions (rough approximation)
        estimated_size_mb = (dimension * 0.15) + 50  # Rough estimate
        size_score = 100 / estimated_size_mb
        
        # Overall score for conversational AI
        overall_score = (speed_score * 0.4) + (quality_score * 0.3) + (size_score * 0.3)
        
        print(f"📊 Scores:")
        print(f"   Quality (dim/384): {quality_score:.2f}")
        print(f"   Speed (10/ms): {speed_score:.2f}")
        print(f"   Size efficiency: {size_score:.2f}")
        print(f"   🏆 Overall: {overall_score:.2f}")
        
        return {
            'model_name': model_name,
            'init_time': init_time,
            'dimensions': dimension,
            'single_avg': avg_single,
            'single_min': min_single,
            'single_max': max_single,
            'batch_cold': per_item_batch,
            'batch_warm': per_item_warm,
            'batch_efficiency': avg_single/per_item_batch,
            'quality_score': quality_score,
            'speed_score': speed_score,
            'size_score': size_score,
            'overall_score': overall_score,
            'estimated_size_mb': estimated_size_mb
        }
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return None


async def comprehensive_model_analysis():
    """Comprehensive analysis of top FastEmbed models for WhisperEngine"""
    
    print("🔍 Comprehensive FastEmbed Model Analysis for WhisperEngine")
    print("=" * 70)
    
    # Conversational AI test texts
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
        "Can you remember what we talked about last time?",
        "I feel stressed about work lately",
        "Let's discuss machine learning concepts",
        "My dog loves going for walks in the park",
        "I'm planning a vacation to Europe",
        "Could you explain quantum computing?"
    ]
    
    # Top models to test based on size, performance, and quality
    models_to_test = [
        # Current choice
        "BAAI/bge-small-en-v1.5",
        
        # Other small, fast options (384 dim)
        "snowflake/snowflake-arctic-embed-xs", 
        "sentence-transformers/all-MiniLM-L6-v2",
        
        # Slightly larger but potentially better quality (512 dim)
        "jinaai/jina-embeddings-v2-small-en",
        
        # Multimodal option (768 dim, but optimized)
        "nomic-ai/nomic-embed-text-v1.5-Q",
        
        # Medium quality option (768 dim)
        "BAAI/bge-base-en-v1.5",
    ]
    
    results = []
    
    for i, model_name in enumerate(models_to_test):
        print(f"\n[{i+1}/{len(models_to_test)}] Testing {model_name}")
        result = await test_model_comprehensive(model_name, test_texts)
        if result:
            results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    # Comprehensive analysis
    print(f"\n📊 Model Comparison Summary")
    print("=" * 70)
    
    # Sort by overall score
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    print(f"{'Model':<35} {'Dim':<4} {'Init':<5} {'Single':<6} {'Batch':<6} {'Score':<5}")
    print("-" * 70)
    
    for result in results:
        model_short = result['model_name'].split('/')[-1][:30]
        print(f"{model_short:<35} {result['dimensions']:<4} {result['init_time']:<5.1f} "
              f"{result['single_avg']:<6.1f} {result['batch_cold']:<6.1f} {result['overall_score']:<5.2f}")
    
    # Detailed analysis of top 3
    print(f"\n🏆 Top 3 Models Analysis")
    print("=" * 50)
    
    for i, result in enumerate(results[:3]):
        print(f"\n#{i+1} {result['model_name']}")
        print(f"   📏 Dimensions: {result['dimensions']}")
        print(f"   ⚡ Init time: {result['init_time']:.2f}s")
        print(f"   🚀 Single: {result['single_avg']:.2f}ms (min: {result['single_min']:.2f}ms)")
        print(f"   📦 Batch: {result['batch_cold']:.2f}ms (warm: {result['batch_warm']:.2f}ms)")
        print(f"   📊 Efficiency: {result['batch_efficiency']:.1f}x")
        print(f"   💾 Est. size: {result['estimated_size_mb']:.0f}MB")
        print(f"   🏆 Score: {result['overall_score']:.2f}")
    
    # Recommendations
    print(f"\n🎯 Recommendations for WhisperEngine")
    print("=" * 50)
    
    if results:
        best_overall = results[0]
        fastest_single = min(results, key=lambda x: x['single_avg'])
        best_efficiency = max(results, key=lambda x: x['batch_efficiency'])
        smallest_init = min(results, key=lambda x: x['init_time'])
        
        print(f"🥇 Best Overall: {best_overall['model_name']}")
        print(f"   Score: {best_overall['overall_score']:.2f}")
        print(f"   Why: Balanced speed, quality, and size")
        
        print(f"\n⚡ Fastest Single: {fastest_single['model_name']}")
        print(f"   Speed: {fastest_single['single_avg']:.2f}ms")
        
        print(f"\n📦 Most Efficient Batch: {best_efficiency['model_name']}")
        print(f"   Efficiency: {best_efficiency['batch_efficiency']:.1f}x")
        
        print(f"\n🚀 Fastest Init: {smallest_init['model_name']}")
        print(f"   Init: {smallest_init['init_time']:.2f}s")
        
        # Specific recommendation
        print(f"\n✅ Final Recommendation:")
        current_model = next((r for r in results if 'bge-small-en-v1.5' in r['model_name']), None)
        if current_model:
            current_rank = results.index(current_model) + 1
            print(f"   Current choice (BAAI/bge-small-en-v1.5) ranks #{current_rank}")
            
            if current_rank <= 2:
                print(f"   ✅ KEEP current choice - excellent performance")
            else:
                print(f"   🔄 CONSIDER switching to: {best_overall['model_name']}")
                print(f"   Improvement: {((best_overall['overall_score'] / current_model['overall_score']) - 1) * 100:.1f}% better")
        
        print(f"\n💡 Trade-off Analysis:")
        print(f"   🏃 For real-time chat: Prioritize <3ms single embedding")
        print(f"   🎯 For quality: Consider 512+ dimensions")
        print(f"   💾 For deployment: Keep under 200MB model size")
        print(f"   ⚖️  For balance: 384-dim models are sweet spot")
        
    return results


if __name__ == "__main__":
    asyncio.run(comprehensive_model_analysis())