#!/usr/bin/env python3
"""
Test script for async/IO enhancements and concurrent user operations
Tests thread safety, rate limiting, and performance under load
"""

import asyncio
import os
import random
import sys
import threading
import time
from unittest.mock import Mock

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from async_enhancements import (
        AsyncLLMManager,
        AsyncMemoryManager,
        AsyncUtilities,
        ConcurrentImageProcessor,
        initialize_async_components,
    )
    from conversation_cache import HybridConversationCache
    from lmstudio_client import LMStudioClient
    from memory_manager import UserMemoryManager

except ImportError:
    sys.exit(1)


class MockLLMClient:
    """Mock LLM client for testing"""

    def __init__(self):
        self.request_count = 0
        self.request_times = []

    def get_chat_response(self, conversation_context):
        self.request_count += 1
        self.request_times.append(time.time())
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))
        return f"Mock response {self.request_count} to context with {len(conversation_context)} messages"

    def analyze_emotion_and_relationships(self, message):
        time.sleep(random.uniform(0.05, 0.2))
        return {
            "detected_emotion": "neutral",
            "confidence": random.uniform(0.6, 0.9),
            "intensity": random.uniform(0.3, 0.7),
        }


class MockMemoryManager:
    """Mock memory manager for testing"""

    def __init__(self):
        self.stored_conversations = []
        self.storage_times = []
        self.lock = threading.Lock()

    def store_conversation(
        self,
        user_id,
        user_message,
        bot_response,
        channel_id=None,
        pre_analyzed_emotion_data=None,
        **kwargs,
    ):
        with self.lock:
            self.stored_conversations.append(
                {
                    "user_id": user_id,
                    "user_message": user_message,
                    "bot_response": bot_response,
                    "timestamp": time.time(),
                    **kwargs,
                }
            )
            self.storage_times.append(time.time())
        # Simulate storage time
        time.sleep(random.uniform(0.02, 0.1))

    def retrieve_relevant_memories(self, user_id, query, limit=10):
        time.sleep(random.uniform(0.01, 0.05))
        return [{"text": f"Memory for {user_id}: {query}", "metadata": {}}]


class MockImageProcessor:
    """Mock image processor for testing"""

    def __init__(self):
        self.processed_count = 0

    async def process_multiple_attachments(self, attachments):
        self.processed_count += len(attachments)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return [{"type": "image", "processed": True} for _ in attachments]


class ConcurrencyTester:
    """Test suite for concurrent operations"""

    def __init__(self):
        self.mock_llm = MockLLMClient()
        self.mock_memory = MockMemoryManager()
        self.mock_image = MockImageProcessor()

        # Initialize async components
        self.async_memory = AsyncMemoryManager(self.mock_memory)
        self.async_llm = AsyncLLMManager(self.mock_llm, max_concurrent_requests=3)
        self.concurrent_image = ConcurrentImageProcessor(
            self.mock_image, max_concurrent_downloads=2
        )

        self.cache = HybridConversationCache(
            cache_timeout_minutes=1, bootstrap_limit=5, max_local_messages=10
        )

        self.results = {}

    async def test_concurrent_memory_storage(self, num_users=5, messages_per_user=3):
        """Test concurrent memory storage operations"""

        async def store_messages_for_user(user_id):
            user_results = []
            for i in range(messages_per_user):
                start_time = time.time()
                await self.async_memory.store_conversation_async(
                    f"user_{user_id}",
                    f"Message {i+1} from user {user_id}",
                    f"Response {i+1} to user {user_id}",
                    channel_id=f"channel_{user_id % 3}",  # Multiple users per channel
                )
                duration = time.time() - start_time
                user_results.append(duration)
            return user_results

        start_time = time.time()
        tasks = [store_messages_for_user(i) for i in range(num_users)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Analyze results
        total_operations = num_users * messages_per_user
        expected_stored = len(self.mock_memory.stored_conversations)

        # Verify thread safety - no corrupted data
        user_counts = {}
        for conv in self.mock_memory.stored_conversations:
            user_id = conv["user_id"]
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

        return {
            "total_time": total_time,
            "operations": total_operations,
            "throughput": total_operations / total_time,
            "stored_conversations": expected_stored,
            "user_counts": user_counts,
        }

    async def test_llm_rate_limiting(self, num_users=4, requests_per_user=3):
        """Test LLM rate limiting and concurrency control"""

        async def make_requests_for_user(user_id):
            user_results = []
            for i in range(requests_per_user):
                start_time = time.time()
                response = await self.async_llm.get_chat_response_async(
                    [{"role": "user", "content": f"Test message {i+1}"}], f"user_{user_id}"
                )
                duration = time.time() - start_time
                user_results.append(
                    {
                        "duration": duration,
                        "response_length": len(response),
                        "timestamp": time.time(),
                    }
                )
            return user_results

        start_time = time.time()
        tasks = [make_requests_for_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Analyze rate limiting effectiveness
        all_durations = [r["duration"] for user_results in results for r in user_results]
        avg_duration = sum(all_durations) / len(all_durations)

        return {
            "total_time": total_time,
            "avg_duration": avg_duration,
            "total_requests": self.mock_llm.request_count,
            "rate_limiting_effective": total_time
            > num_users * requests_per_user * 1.0,  # Rate limit should add delay
        }

    async def test_cache_concurrent_access(self, num_users=6, operations_per_user=5):
        """Test conversation cache under concurrent access"""

        # Create mock Discord objects
        class MockMessage:
            def __init__(self, content, message_id):
                self.content = content
                self.id = message_id
                self.author = Mock()
                self.author.name = f"User_{message_id % 3}"
                # Add required discord.Message attributes
                self.attachments = []
                self.embeds = []

        class MockChannel:
            def __init__(self, channel_id):
                self.id = channel_id
                self.messages = []

            async def history(self, limit=None):
                messages_to_yield = (
                    self.messages[-limit:]
                    if limit and len(self.messages) > limit
                    else self.messages
                )
                for msg in messages_to_yield:
                    yield msg

        channels = [MockChannel(i) for i in range(3)]  # 3 channels, multiple users per channel

        async def user_operations(user_id):
            channel = channels[user_id % len(channels)]
            results = []

            for i in range(operations_per_user):
                # Add message to cache
                msg = MockMessage(f"Message {i} from user {user_id}", user_id * 1000 + i)
                channel.messages.append(msg)
                self.cache.add_message(str(channel.id), msg)

                # Retrieve context
                start_time = time.time()
                context = await self.cache.get_conversation_context(channel, limit=3)
                duration = time.time() - start_time

                results.append(
                    {"operation": "get_context", "duration": duration, "context_size": len(context)}
                )

                # Small delay to simulate real usage
                await asyncio.sleep(random.uniform(0.01, 0.05))

            return results

        start_time = time.time()
        tasks = [user_operations(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Analyze cache performance
        all_operations = [op for user_results in results for op in user_results]
        avg_duration = sum(op["duration"] for op in all_operations) / len(all_operations)

        cache_stats = self.cache.get_cache_stats()

        return {
            "total_time": total_time,
            "avg_duration": avg_duration,
            "cache_stats": cache_stats,
            "operations_completed": len(all_operations),
        }

    async def test_mixed_workload(self, duration_seconds=5):
        """Test mixed workload with all components under stress"""

        completed_operations = {"storage": 0, "llm": 0, "cache": 0}
        stop_flag = asyncio.Event()

        # Set timeout to stop workers
        async def timeout_handler():
            await asyncio.sleep(duration_seconds)
            stop_flag.set()

        async def storage_worker():
            user_counter = 0
            try:
                while not stop_flag.is_set():
                    await self.async_memory.store_conversation_async(
                        f"stress_user_{user_counter % 5}",  # Reduce to 5 users
                        f"Stress test message {user_counter}",
                        f"Stress test response {user_counter}",
                    )
                    completed_operations["storage"] += 1
                    user_counter += 1
                    await asyncio.sleep(0.2)  # Fixed delay to prevent overwhelming
            except Exception:
                pass

        async def llm_worker():
            request_counter = 0
            try:
                while not stop_flag.is_set():
                    await self.async_llm.get_chat_response_async(
                        [{"role": "user", "content": f"Stress test {request_counter}"}],
                        f"stress_user_{request_counter % 5}",
                    )
                    completed_operations["llm"] += 1
                    request_counter += 1
                    await asyncio.sleep(0.3)  # Fixed delay
            except Exception:
                pass

        async def cache_worker():
            op_counter = 0
            try:
                # Create a proper mock channel
                class MockChannel:
                    def __init__(self):
                        self.id = "stress_channel"

                    async def history(self, limit=None):
                        # Return empty async generator
                        return
                        yield  # Never reached, but makes this an async generator

                mock_channel = MockChannel()

                while not stop_flag.is_set():
                    await self.cache.get_conversation_context(mock_channel, limit=5)
                    completed_operations["cache"] += 1
                    op_counter += 1
                    await asyncio.sleep(0.1)  # Fixed delay
            except Exception:
                pass

        # Run all workers concurrently with timeout
        try:
            workers = [storage_worker(), llm_worker(), cache_worker(), timeout_handler()]
            await asyncio.gather(*workers, return_exceptions=True)
        except Exception:
            pass
        finally:
            stop_flag.set()  # Ensure all workers stop

        total_operations = sum(completed_operations.values())
        throughput = total_operations / duration_seconds

        return {
            "duration": duration_seconds,
            "operations": completed_operations,
            "total_operations": total_operations,
            "throughput": throughput,
        }

    async def run_all_tests(self):
        """Run all concurrency tests with timeout protection"""

        test_results = {}

        try:
            # Test 1: Concurrent memory storage
            test_results["memory_storage"] = await asyncio.wait_for(
                self.test_concurrent_memory_storage(), timeout=30
            )

            # Test 2: LLM rate limiting
            test_results["llm_rate_limiting"] = await asyncio.wait_for(
                self.test_llm_rate_limiting(), timeout=30
            )

            # Test 3: Cache concurrent access
            test_results["cache_concurrent"] = await asyncio.wait_for(
                self.test_cache_concurrent_access(), timeout=30
            )

            # Test 4: Mixed workload stress test (shorter duration)
            test_results["mixed_workload"] = await asyncio.wait_for(
                self.test_mixed_workload(duration_seconds=3), timeout=15
            )

            # Summary
            for _test_name, results in test_results.items():
                if "throughput" in results:
                    pass
                if "total_time" in results:
                    pass
                if "operations" in results:
                    pass

            return test_results

        except Exception:
            import traceback

            traceback.print_exc()
            return None
        finally:
            # Cleanup
            self.async_memory.cleanup()


async def main():
    """Main test function"""

    tester = ConcurrencyTester()
    results = await tester.run_all_tests()

    if results:

        return True
    else:
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
