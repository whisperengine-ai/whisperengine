#!/usr/bin/env python3
"""
Demo: Vectorized Emotional Intelligence Performance Testing
Tests the optimized emotion engine with pandas vectorization and parallel processing
"""

import asyncio
import random
import time
from typing import Any

try:
    import numpy as np
    import pandas as pd
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False


# Test data generator
def generate_test_messages(count: int) -> list[dict[str, Any]]:
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
            template = (
                template
                + " "
                + random.choice(
                    [
                        "What do you think?",
                        "Let me know your thoughts.",
                        "Hope this makes sense.",
                        "Looking forward to feedback.",
                    ]
                )
            )

        messages.append(
            {
                "text": template,
                "user_id": user_id,
                "metadata": {
                    "timestamp": time.time() + i,
                    "channel": f"channel_{random.randint(1, 10)}",
                },
            }
        )

    return messages


async def test_vectorized_emotion_processing():
    """Test the vectorized emotion processing engine"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.emotion.vectorized_emotion_engine import (
            ProductionEmotionEngine,
            VectorizedEmotionProcessor,
        )

        # Test configurations
        test_configs = [
            {"name": "Small Batch", "count": 10, "workers": 2},
            {"name": "Medium Batch", "count": 50, "workers": 4},
            {"name": "Large Batch", "count": 100, "workers": 4},
            {"name": "XL Batch", "count": 500, "workers": 8},
        ]

        for config in test_configs:

            # Generate test data
            test_messages = generate_test_messages(config["count"])
            texts = [msg["text"] for msg in test_messages]
            user_ids = [msg["user_id"] for msg in test_messages]
            metadata_list = [msg["metadata"] for msg in test_messages]

            # Test VectorizedEmotionProcessor
            processor = VectorizedEmotionProcessor(max_workers=config["workers"])

            start_time = time.time()
            processor.process_batch(texts, user_ids, metadata_list)
            time.time() - start_time


            # Test async processing
            start_time = time.time()
            await processor.process_batch_async(texts, user_ids, metadata_list)
            time.time() - start_time


            # Test ProductionEmotionEngine (with caching)
            engine = ProductionEmotionEngine(max_workers=config["workers"])

            start_time = time.time()
            await engine.analyze_emotions_batch(texts, user_ids, metadata_list)
            time.time() - start_time


            # Test caching performance (process same batch again)
            start_time = time.time()
            await engine.analyze_emotions_batch(texts, user_ids, metadata_list)
            time.time() - start_time


            # Get performance stats
            engine.get_comprehensive_stats()

            await engine.shutdown()
            processor.shutdown()


    except Exception:
        import traceback

        traceback.print_exc()


async def test_emotion_streaming():
    """Test streaming emotion processing"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.emotion.vectorized_emotion_engine import VectorizedEmotionProcessor

        processor = VectorizedEmotionProcessor(max_workers=4)

        # Create streaming queue
        stream_queue = asyncio.Queue()

        # Add test messages to stream
        test_messages = generate_test_messages(25)

        # Start streaming processor
        stream_task = asyncio.create_task(collect_streaming_results(processor, stream_queue))

        # Feed messages to stream with realistic timing
        for i, msg in enumerate(test_messages):
            await stream_queue.put(msg)
            if i % 5 == 4:  # Pause every 5 messages
                await asyncio.sleep(0.1)

        # Signal end of stream
        await stream_queue.put(None)

        # Collect results
        results = await stream_task

        sum(result.batch_size for result in results)
        sum(result.processing_time for result in results)


        processor.shutdown()

    except Exception:
        pass


async def collect_streaming_results(processor, stream_queue):
    """Collect results from streaming emotion processor"""
    results = []

    async for batch_result in processor.process_streaming(stream_queue, batch_size=5, timeout=0.5):
        results.append(batch_result)

        # Stop when we get a None marker or enough results
        if len(results) >= 10:
            break

    return results


async def test_emotion_accuracy():
    """Test emotion detection accuracy with known examples"""

    if not LIBRARIES_AVAILABLE:
        return


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


        correct_predictions = 0

        for i, case in enumerate(test_cases):
            emotion = await engine.analyze_emotion(case["text"], f"test_user_{i}")

            is_correct = emotion.primary_emotion == case["expected"]
            if is_correct:
                correct_predictions += 1


        correct_predictions / len(test_cases)

        # Test edge cases
        edge_cases = [
            "extremely happy and excited!",  # intensifier
            "somewhat sad but okay",  # mixed emotion
            "",  # empty text
            "123 456 789",  # numbers only
            "!!!",  # punctuation only
        ]

        for case in edge_cases:
            emotion = await engine.analyze_emotion(case, "edge_user")

        await engine.shutdown()

    except Exception:
        pass


async def test_concurrent_emotion_processing():
    """Test concurrent emotion processing with multiple users"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.emotion.vectorized_emotion_engine import ProductionEmotionEngine

        engine = ProductionEmotionEngine(max_workers=8, enable_caching=True)

        # Simulate concurrent users
        num_users = 20
        messages_per_user = 5


        async def process_user_emotions(user_id: str):
            """Process emotions for a single user"""
            user_messages = generate_test_messages(messages_per_user)
            texts = [msg["text"] for msg in user_messages]

            start_time = time.time()
            emotions = await engine.analyze_emotions_batch(
                texts, [user_id] * len(texts), [{"user": user_id} for _ in texts]
            )
            processing_time = time.time() - start_time

            return {
                "user_id": user_id,
                "message_count": len(emotions),
                "processing_time": processing_time,
                "emotions": [e.primary_emotion for e in emotions],
            }

        # Run concurrent processing
        start_time = time.time()

        tasks = [process_user_emotions(f"user_{i}") for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        time.time() - start_time

        # Analyze results
        sum(r["message_count"] for r in results)
        np.mean([r["processing_time"] for r in results])


        # Check cache performance
        engine.get_comprehensive_stats()

        await engine.shutdown()

    except Exception:
        pass


async def main():
    """Run all emotion processing performance tests"""


    if not LIBRARIES_AVAILABLE:
        return

    # Run all tests
    await test_vectorized_emotion_processing()
    await test_emotion_streaming()
    await test_emotion_accuracy()
    await test_concurrent_emotion_processing()



if __name__ == "__main__":
    asyncio.run(main())
