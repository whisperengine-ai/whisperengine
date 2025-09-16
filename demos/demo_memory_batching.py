#!/usr/bin/env python3
"""
Demo: Advanced Memory Batching Performance Testing
Tests the optimized memory batching system with intelligent caching and parallel processing
"""

import asyncio
import logging
import random
import time
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd

    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False


# Mock ChromaDB manager for testing
class MockChromaDBManager:
    """Mock ChromaDB manager for testing without real database"""

    def __init__(self):
        self.conversations = []
        self.user_facts = []
        self.operation_delay = 0.01  # Simulate database latency

    def store_conversation(
        self, user_id: str, message: str, response: str, metadata: dict[str, Any]
    ) -> str:
        """Mock conversation storage"""
        time.sleep(self.operation_delay)  # Simulate DB latency

        conversation_id = f"conv_{len(self.conversations)}_{random.randint(1000, 9999)}"
        self.conversations.append(
            {
                "id": conversation_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "metadata": metadata,
            }
        )
        return conversation_id

    def store_user_fact(self, user_id: str, fact: str, metadata: dict[str, Any]) -> str:
        """Mock user fact storage"""
        time.sleep(self.operation_delay)  # Simulate DB latency

        fact_id = f"fact_{len(self.user_facts)}_{random.randint(1000, 9999)}"
        self.user_facts.append(
            {"id": fact_id, "user_id": user_id, "fact": fact, "metadata": metadata}
        )
        return fact_id

    def retrieve_relevant_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Mock memory retrieval"""
        time.sleep(self.operation_delay * 2)  # Queries are slower

        # Simulate returning relevant conversations
        user_conversations = [conv for conv in self.conversations if conv["user_id"] == user_id]

        # Simple relevance simulation
        relevant = []
        for conv in user_conversations[-limit:]:  # Return most recent
            relevant.append(
                {
                    "id": conv["id"],
                    "document": f"{conv['message']} | {conv['response']}",
                    "metadata": conv["metadata"],
                    "score": random.uniform(0.5, 1.0),
                }
            )

        return relevant


def generate_test_data(num_users: int, conversations_per_user: int) -> list[dict[str, Any]]:
    """Generate realistic test data for batching performance tests"""

    conversation_templates = [
        "Hello! How can I help you today?",
        "I'm working on a project and need some advice.",
        "Can you explain how machine learning works?",
        "What's the weather like in San Francisco?",
        "I'm feeling stressed about work lately.",
        "Thanks for all your help! You're amazing.",
        "I have a question about programming in Python.",
        "What do you think about the latest AI developments?",
        "I'm planning a trip to Europe next month.",
        "Can you help me debug this code issue?",
    ]

    response_templates = [
        "I'd be happy to help you with that!",
        "That's a great question. Let me explain...",
        "Based on what you've told me, I think...",
        "I understand your concern. Here's what I suggest...",
        "That sounds exciting! Tell me more about...",
        "I'm glad I could help! Is there anything else?",
        "Let me break that down for you step by step...",
        "That's definitely something worth considering...",
        "I can see why that would be important to you.",
        "Thanks for sharing that with me!",
    ]

    test_data = []

    for user_num in range(num_users):
        user_id = f"test_user_{user_num:04d}"

        for conv_num in range(conversations_per_user):
            message = random.choice(conversation_templates)
            response = random.choice(response_templates)

            # Add some variation
            if random.random() < 0.3:
                message += f" This is conversation #{conv_num + 1} for me."

            test_data.append(
                {
                    "operation": "store_conversation",
                    "user_id": user_id,
                    "message": message,
                    "response": response,
                    "metadata": {
                        "conversation_number": conv_num + 1,
                        "timestamp": time.time() + conv_num,
                        "channel": f"channel_{random.randint(1, 5)}",
                    },
                }
            )

    return test_data


async def test_batching_performance():
    """Test batching system performance vs direct operations"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.memory.advanced_memory_batcher import BatchedMemoryAdapter

        # Create mock database
        mock_db = MockChromaDBManager()

        # Test configurations
        test_configs = [
            {"name": "Small Load", "users": 5, "conversations": 10, "batch_size": 10},
            {"name": "Medium Load", "users": 20, "conversations": 15, "batch_size": 25},
            {"name": "Large Load", "users": 50, "conversations": 20, "batch_size": 50},
            {"name": "High Concurrency", "users": 100, "conversations": 10, "batch_size": 75},
        ]

        for config in test_configs:

            # Generate test data
            test_data = generate_test_data(config["users"], config["conversations"])
            total_operations = len(test_data)


            # Test 1: Direct operations (no batching)
            start_time = time.time()

            direct_results = []
            for op in test_data:
                if op["operation"] == "store_conversation":
                    result = mock_db.store_conversation(
                        op["user_id"], op["message"], op["response"], op["metadata"]
                    )
                    direct_results.append(result)

            direct_time = time.time() - start_time
            total_operations / direct_time


            # Reset mock database for fair comparison
            mock_db.conversations.clear()
            mock_db.user_facts.clear()

            # Test 2: Batched operations

            adapter = BatchedMemoryAdapter(mock_db, enable_batching=True)
            await adapter.start()

            start_time = time.time()

            # Process operations concurrently
            tasks = []
            for op in test_data:
                if op["operation"] == "store_conversation":
                    task = adapter.store_conversation(
                        op["user_id"], op["message"], op["response"], op["metadata"]
                    )
                    tasks.append(task)

            await asyncio.gather(*tasks)

            batch_time = time.time() - start_time
            total_operations / batch_time


            # Get performance metrics
            stats = adapter.get_performance_stats()
            stats.get("batch_metrics", {})
            stats.get("cache_metrics", {})


            await adapter.stop()

            # Compare results


    except Exception:
        import traceback

        traceback.print_exc()


async def test_caching_performance():
    """Test caching system performance with repeated queries"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.memory.advanced_memory_batcher import BatchedMemoryAdapter

        # Create mock database with some initial data
        mock_db = MockChromaDBManager()

        # Pre-populate with some conversations
        for i in range(100):
            mock_db.store_conversation(
                f"user_{i % 10}", f"Test message {i}", f"Test response {i}", {"test": True}
            )

        adapter = BatchedMemoryAdapter(mock_db, enable_batching=True)
        await adapter.start()

        # Test query patterns
        test_queries = [
            ("user_1", "test message"),
            ("user_2", "help with project"),
            ("user_3", "machine learning"),
            ("user_1", "test message"),  # Repeat for cache testing
            ("user_4", "programming"),
            ("user_2", "help with project"),  # Repeat for cache testing
        ]


        # Execute queries and measure performance
        query_times = []

        for i, (user_id, query) in enumerate(test_queries):
            start_time = time.time()

            await adapter.retrieve_relevant_memories(user_id, query, limit=5)

            query_time = time.time() - start_time
            query_times.append(query_time)


        # Get final cache statistics
        stats = adapter.get_performance_stats()
        stats.get("cache_metrics", {})


        await adapter.stop()

    except Exception:
        pass


async def test_concurrent_users():
    """Test performance with many concurrent users"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.memory.advanced_memory_batcher import BatchedMemoryAdapter

        mock_db = MockChromaDBManager()
        adapter = BatchedMemoryAdapter(mock_db, enable_batching=True)
        await adapter.start()

        # Simulate concurrent user scenarios
        user_scenarios = [
            {"users": 10, "ops_per_user": 5},
            {"users": 25, "ops_per_user": 8},
            {"users": 50, "ops_per_user": 6},
            {"users": 100, "ops_per_user": 3},
        ]

        for scenario in user_scenarios:
            num_users = scenario["users"]
            ops_per_user = scenario["ops_per_user"]
            total_ops = num_users * ops_per_user


            async def simulate_user(user_id: str, operations: int):
                """Simulate a single user's operations"""
                results = []
                for i in range(operations):
                    # Mix of store and query operations
                    if i % 3 == 0:  # Query every 3rd operation
                        result = await adapter.retrieve_relevant_memories(
                            user_id, f"query {i}", limit=3
                        )
                    else:  # Store operation
                        result = await adapter.store_conversation(
                            user_id,
                            f"Message {i} from {user_id}",
                            f"Response {i} to {user_id}",
                            {"operation": i},
                        )
                    results.append(result)
                return results

            # Create and run concurrent user tasks
            start_time = time.time()

            user_tasks = [
                simulate_user(f"concurrent_user_{i}", ops_per_user) for i in range(num_users)
            ]

            all_results = await asyncio.gather(*user_tasks)

            total_time = time.time() - start_time
            total_ops / total_time


            # Validate results
            sum(1 for results in all_results if len(results) == ops_per_user)

            # Get performance stats
            stats = adapter.get_performance_stats()
            stats.get("batch_metrics", {})


        await adapter.stop()

    except Exception:
        pass


async def test_deduplication():
    """Test automatic deduplication features"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.memory.advanced_memory_batcher import BatchedMemoryAdapter

        mock_db = MockChromaDBManager()
        adapter = BatchedMemoryAdapter(mock_db, enable_batching=True)
        await adapter.start()

        # Test duplicate detection
        duplicate_operations = [
            ("user_dedup", "Hello, how are you?", "I'm doing well, thanks!"),
            ("user_dedup", "Hello, how are you?", "I'm doing well, thanks!"),  # Exact duplicate
            ("user_dedup", "Hello, how are you?", "I'm doing well, thanks!"),  # Another duplicate
            ("user_dedup", "How's the weather today?", "It's sunny and warm!"),  # Different
            (
                "user_dedup",
                "How's the weather today?",
                "It's sunny and warm!",
            ),  # Duplicate of different
        ]


        start_time = time.time()

        # Submit all operations
        tasks = []
        for user_id, message, response in duplicate_operations:
            task = adapter.store_conversation(user_id, message, response, {"test": True})
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        time.time() - start_time

        # Analyze results
        unique_results = set(results)
        1 - (len(unique_results) / len(results))


        await adapter.stop()

    except Exception:
        pass


async def main():
    """Run all memory batching performance tests"""


    if not LIBRARIES_AVAILABLE:
        return

    # Run all tests
    await test_batching_performance()
    await test_caching_performance()
    await test_concurrent_users()
    await test_deduplication()



if __name__ == "__main__":
    asyncio.run(main())
