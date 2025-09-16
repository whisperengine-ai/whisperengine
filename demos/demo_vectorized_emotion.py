#!/usr/bin/env python3
"""
Demo: Vectorized Emotional Intelligence Performance Testing
Tests the optimized emotion engine with pandas vectorization and parallel processing
"""

import asyncio
import time
import random
from typing import List, Dict, Any

try:
    import pandas as pd
    import numpy as np
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    print(f"✅ pandas {pd.__version__}, numpy {np.__version__}")
    LIBRARIES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Missing libraries: {e}")
    LIBRARIES_AVAILABLE = False


# Test data generator
def generate_test_messages(count: int) -> List[Dict[str, Any]]:
    """Generate realistic test messages with various emotions"""
    
    emotions_templates = [
        # Joy
        "I'm so happy about this! Amazing work everyone!",
        "This is absolutely fantastic! I love it!",
        "Feeling great today, everything is going perfectly!",
        
        # Sadness
        "I'm feeling really down about this situation...",
        "This is so disappointing, I expected better.",
        "Having a tough time lately, nothing seems to work.",
        
        # Anger
        "This is absolutely frustrating! Why doesn't this work?",
        "I'm so annoyed with these constant issues!",
        "Getting really irritated with all these problems.",
        
        # Fear/Anxiety
        "I'm worried this won't work out as planned.",
        "Feeling anxious about the upcoming deadline.",
        "Scared that we might not be able to deliver on time.",
        
        # Excitement
        "Can't wait to see how this turns out!",
        "Super excited about the new features!",
        "Thrilled to be working on such an innovative project!",
        
        # Gratitude
        "Thank you so much for all your help!",
        "Really grateful for the team's support.",
        "Appreciate everyone's hard work on this.",
        
        # Neutral
        "The meeting is scheduled for tomorrow at 2 PM.",
        "Please review the documentation when you have time.",
        "The system is running normally today.",
    ]
    
    messages = []
    for i in range(count):
        template = random.choice(emotions_templates)
        user_id = f"user_{random.randint(1, 100)}"
        
        # Add some variations
        if random.random() < 0.3:
            template = template + " " + random.choice([
                "What do you think?",
                "Let me know your thoughts.",
                "Hope this makes sense.",
                "Looking forward to feedback."
            ])
        
        messages.append({
            "text": template,
            "user_id": user_id,
            "metadata": {
                "timestamp": time.time() + i,
                "channel": f"channel_{random.randint(1, 10)}"
            }
        })
    
    return messages


async def test_vectorized_emotion_processing():
    """Test the vectorized emotion processing engine"""
    
    if not LIBRARIES_AVAILABLE:
        print("❌ Cannot run tests - missing required libraries")
        return
    
    print("\n🧠 Testing Vectorized Emotional Intelligence Engine")
    print("=" * 60)
    
    try:
        from src.emotion.vectorized_emotion_engine import (
            VectorizedEmotionProcessor, 
            ProductionEmotionEngine,
            EmotionEngineAdapter
        )
        
        # Test configurations
        test_configs = [
            {"name": "Small Batch", "count": 10, "workers": 2},
            {"name": "Medium Batch", "count": 50, "workers": 4},
            {"name": "Large Batch", "count": 100, "workers": 4},
            {"name": "XL Batch", "count": 500, "workers": 8},
        ]
        
        for config in test_configs:
            print(f"\n📊 Testing {config['name']} ({config['count']} messages, {config['workers']} workers)")
            
            # Generate test data
            test_messages = generate_test_messages(config['count'])
            texts = [msg['text'] for msg in test_messages]
            user_ids = [msg['user_id'] for msg in test_messages]
            metadata_list = [msg['metadata'] for msg in test_messages]
            
            # Test VectorizedEmotionProcessor
            processor = VectorizedEmotionProcessor(max_workers=config['workers'])
            
            start_time = time.time()
            result = processor.process_batch(texts, user_ids, metadata_list)
            processing_time = time.time() - start_time
            
            print(f"  ⚡ Batch Processing: {processing_time*1000:.1f}ms")
            print(f"  📈 Throughput: {config['count']/processing_time:.1f} emotions/sec")
            print(f"  🎯 Avg Confidence: {result.avg_confidence:.2f}")
            print(f"  🎭 Emotion Distribution: {dict(list(result.emotion_distribution.items())[:3])}")
            
            # Test async processing
            start_time = time.time()
            async_result = await processor.process_batch_async(texts, user_ids, metadata_list)
            async_time = time.time() - start_time
            
            print(f"  ⚡ Async Processing: {async_time*1000:.1f}ms")
            print(f"  📈 Async Throughput: {config['count']/async_time:.1f} emotions/sec")
            
            # Test ProductionEmotionEngine (with caching)
            engine = ProductionEmotionEngine(max_workers=config['workers'])
            
            start_time = time.time()
            batch_emotions = await engine.analyze_emotions_batch(texts, user_ids, metadata_list)
            engine_time = time.time() - start_time
            
            print(f"  🚀 Production Engine: {engine_time*1000:.1f}ms")
            print(f"  📈 Engine Throughput: {config['count']/engine_time:.1f} emotions/sec")
            
            # Test caching performance (process same batch again)
            start_time = time.time()
            cached_emotions = await engine.analyze_emotions_batch(texts, user_ids, metadata_list)
            cached_time = time.time() - start_time
            
            print(f"  💾 Cached Processing: {cached_time*1000:.1f}ms")
            print(f"  🔥 Cache Speedup: {engine_time/cached_time:.1f}x faster")
            
            # Get performance stats
            stats = engine.get_comprehensive_stats()
            print(f"  📊 Cache Hit Rate: {stats['cache']['cache_hit_rate']:.1%}")
            
            await engine.shutdown()
            processor.shutdown()
        
        print(f"\n✅ Vectorized emotion processing tests completed!")
        
    except Exception as e:
        print(f"❌ Error in vectorized emotion tests: {e}")
        import traceback
        traceback.print_exc()


async def test_emotion_streaming():
    """Test streaming emotion processing"""
    
    if not LIBRARIES_AVAILABLE:
        return
    
    print("\n🌊 Testing Streaming Emotion Processing")
    print("=" * 50)
    
    try:
        from src.emotion.vectorized_emotion_engine import VectorizedEmotionProcessor
        
        processor = VectorizedEmotionProcessor(max_workers=4)
        
        # Create streaming queue
        stream_queue = asyncio.Queue()
        
        # Add test messages to stream
        test_messages = generate_test_messages(25)
        
        # Start streaming processor
        stream_task = asyncio.create_task(
            collect_streaming_results(processor, stream_queue)
        )
        
        # Feed messages to stream with realistic timing
        for i, msg in enumerate(test_messages):
            await stream_queue.put(msg)
            if i % 5 == 4:  # Pause every 5 messages
                await asyncio.sleep(0.1)
        
        # Signal end of stream
        await stream_queue.put(None)
        
        # Collect results
        results = await stream_task
        
        total_processed = sum(result.batch_size for result in results)
        total_time = sum(result.processing_time for result in results)
        
        print(f"  🌊 Processed {total_processed} emotions in {len(results)} batches")
        print(f"  ⚡ Total time: {total_time*1000:.1f}ms")
        print(f"  📈 Streaming throughput: {total_processed/total_time:.1f} emotions/sec")
        
        processor.shutdown()
        
    except Exception as e:
        print(f"❌ Error in streaming tests: {e}")


async def collect_streaming_results(processor, stream_queue):
    """Collect results from streaming emotion processor"""
    results = []
    
    async for batch_result in processor.process_streaming(stream_queue, batch_size=5, timeout=0.5):
        results.append(batch_result)
        print(f"    📦 Processed batch: {batch_result.batch_size} emotions, "
              f"{batch_result.processing_time*1000:.1f}ms")
        
        # Stop when we get a None marker or enough results
        if len(results) >= 10:
            break
    
    return results


async def test_emotion_accuracy():
    """Test emotion detection accuracy with known examples"""
    
    if not LIBRARIES_AVAILABLE:
        return
    
    print("\n🎯 Testing Emotion Detection Accuracy")
    print("=" * 45)
    
    try:
        from src.emotion.vectorized_emotion_engine import ProductionEmotionEngine
        
        engine = ProductionEmotionEngine(max_workers=2)
        
        # Test cases with expected emotions
        test_cases = [
            {"text": "I'm absolutely thrilled about this amazing news!", "expected": "joy"},
            {"text": "This is so frustrating and annoying!", "expected": "anger"},
            {"text": "I'm really worried about the upcoming presentation.", "expected": "fear"},
            {"text": "Feeling quite sad and depressed today.", "expected": "sadness"},
            {"text": "Thank you so much for your incredible help!", "expected": "gratitude"},
            {"text": "The meeting is scheduled for 3 PM tomorrow.", "expected": "neutral"},
            {"text": "I love working on this exciting new project!", "expected": "love"},
            {"text": "Surprised by the unexpected results!", "expected": "surprise"},
        ]
        
        print(f"  🧪 Testing {len(test_cases)} emotion samples...")
        
        correct_predictions = 0
        
        for i, case in enumerate(test_cases):
            emotion = await engine.analyze_emotion(case['text'], f"test_user_{i}")
            
            is_correct = emotion.primary_emotion == case['expected']
            if is_correct:
                correct_predictions += 1
            
            status = "✅" if is_correct else "❌"
            print(f"    {status} '{case['text'][:40]}...'")
            print(f"        Expected: {case['expected']}, Got: {emotion.primary_emotion} "
                  f"(confidence: {emotion.confidence:.2f})")
        
        accuracy = correct_predictions / len(test_cases)
        print(f"\n  🎯 Accuracy: {accuracy:.1%} ({correct_predictions}/{len(test_cases)})")
        
        # Test edge cases
        edge_cases = [
            "extremely happy and excited!",  # intensifier
            "somewhat sad but okay",         # mixed emotion
            "",                              # empty text
            "123 456 789",                   # numbers only
            "!!!",                           # punctuation only
        ]
        
        print(f"\n  🔍 Testing edge cases...")
        for case in edge_cases:
            emotion = await engine.analyze_emotion(case, "edge_user")
            print(f"    '{case}' -> {emotion.primary_emotion} "
                  f"(confidence: {emotion.confidence:.2f})")
        
        await engine.shutdown()
        
    except Exception as e:
        print(f"❌ Error in accuracy tests: {e}")


async def test_concurrent_emotion_processing():
    """Test concurrent emotion processing with multiple users"""
    
    if not LIBRARIES_AVAILABLE:
        return
    
    print("\n⚡ Testing Concurrent Emotion Processing")
    print("=" * 50)
    
    try:
        from src.emotion.vectorized_emotion_engine import ProductionEmotionEngine
        
        engine = ProductionEmotionEngine(max_workers=8, enable_caching=True)
        
        # Simulate concurrent users
        num_users = 20
        messages_per_user = 5
        
        print(f"  👥 Simulating {num_users} concurrent users with {messages_per_user} messages each")
        
        async def process_user_emotions(user_id: str):
            """Process emotions for a single user"""
            user_messages = generate_test_messages(messages_per_user)
            texts = [msg['text'] for msg in user_messages]
            
            start_time = time.time()
            emotions = await engine.analyze_emotions_batch(
                texts, [user_id] * len(texts), 
                [{"user": user_id} for _ in texts]
            )
            processing_time = time.time() - start_time
            
            return {
                "user_id": user_id,
                "message_count": len(emotions),
                "processing_time": processing_time,
                "emotions": [e.primary_emotion for e in emotions]
            }
        
        # Run concurrent processing
        start_time = time.time()
        
        tasks = [process_user_emotions(f"user_{i}") for i in range(num_users)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Analyze results
        total_messages = sum(r['message_count'] for r in results)
        avg_user_time = np.mean([r['processing_time'] for r in results])
        
        print(f"  ⚡ Total time: {total_time*1000:.1f}ms")
        print(f"  📊 Processed {total_messages} emotions across {num_users} users")
        print(f"  📈 Concurrent throughput: {total_messages/total_time:.1f} emotions/sec")
        print(f"  👤 Avg per-user time: {avg_user_time*1000:.1f}ms")
        print(f"  🚀 Concurrency speedup: ~{(num_users * avg_user_time)/total_time:.1f}x")
        
        # Check cache performance
        stats = engine.get_comprehensive_stats()
        print(f"  💾 Cache hit rate: {stats['cache']['cache_hit_rate']:.1%}")
        print(f"  📊 Total requests: {stats['total_requests']}")
        
        await engine.shutdown()
        
    except Exception as e:
        print(f"❌ Error in concurrent tests: {e}")


async def main():
    """Run all emotion processing performance tests"""
    
    print("🧠 WhisperEngine Vectorized Emotional Intelligence Performance Demo")
    print("=" * 70)
    
    if not LIBRARIES_AVAILABLE:
        print("❌ Required libraries not available. Please install:")
        print("   pip install pandas numpy vaderSentiment")
        return
    
    # Run all tests
    await test_vectorized_emotion_processing()
    await test_emotion_streaming()
    await test_emotion_accuracy()
    await test_concurrent_emotion_processing()
    
    print("\n🎉 All vectorized emotion intelligence tests completed!")
    print("📊 Performance Summary:")
    print("   • Vectorized batch processing with pandas")
    print("   • Async processing with ThreadPoolExecutor")
    print("   • Production-ready caching and optimization")
    print("   • Real-time streaming emotion analysis")
    print("   • High concurrency support for multiple users")


if __name__ == "__main__":
    asyncio.run(main())