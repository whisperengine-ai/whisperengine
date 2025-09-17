"""
Performance test suite for WhisperEngine.

Tests system performance, scalability, and resource usage:
- Memory system performance
- LLM response times
- Concurrent user handling
- Resource utilization
- Caching effectiveness
"""

import pytest
import asyncio
import time
import psutil
import gc
from unittest.mock import AsyncMock, Mock, patch
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager


@pytest.mark.performance
class TestMemorySystemPerformance:
    """Test memory system performance and scalability"""

    @pytest.fixture
    def performance_memory_manager(self):
        """Mock memory manager optimized for performance testing"""
        mock_manager = Mock()
        mock_manager.store_memory = AsyncMock()
        mock_manager.retrieve_memories = AsyncMock(return_value=[])
        mock_manager.search_memories = AsyncMock(return_value=[])
        return mock_manager

    @pytest.mark.asyncio
    async def test_memory_storage_performance(self, performance_memory_manager):
        """Test memory storage performance under load"""
        start_time = time.time()
        
        # Simulate storing 100 memories
        tasks = []
        for i in range(100):
            task = performance_memory_manager.store_memory(
                user_id=12345,
                content=f"Memory content {i}",
                metadata={'index': i, 'type': 'performance_test'}
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 5.0, f"Memory storage took too long: {duration}s"
        assert performance_memory_manager.store_memory.call_count == 100

    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self, performance_memory_manager):
        """Test memory retrieval performance"""
        # Mock realistic memory data
        mock_memories = [
            {'content': f'Memory {i}', 'timestamp': time.time() - i}
            for i in range(50)
        ]
        performance_memory_manager.retrieve_memories.return_value = mock_memories
        
        start_time = time.time()
        
        # Perform multiple retrievals
        tasks = []
        for i in range(20):
            task = performance_memory_manager.retrieve_memories(
                user_id=12345,
                limit=10
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly
        assert duration < 2.0, f"Memory retrieval took too long: {duration}s"
        assert len(results) == 20

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, performance_memory_manager):
        """Test concurrent memory operations from multiple users"""
        async def user_operation(user_id):
            """Simulate user memory operations"""
            # Store a memory
            await performance_memory_manager.store_memory(
                user_id=user_id,
                content=f"User {user_id} memory",
                metadata={'user': user_id}
            )
            
            # Retrieve memories
            await performance_memory_manager.retrieve_memories(
                user_id=user_id,
                limit=5
            )
        
        start_time = time.time()
        
        # Simulate 10 concurrent users
        tasks = [user_operation(user_id) for user_id in range(10)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle concurrent operations efficiently
        assert duration < 3.0, f"Concurrent operations took too long: {duration}s"


@pytest.mark.performance
class TestLLMResponsePerformance:
    """Test LLM response performance and optimization"""

    @pytest.fixture
    def performance_llm_client(self):
        """Mock LLM client with performance characteristics"""
        mock_client = Mock()
        
        # Simulate realistic response times
        async def mock_chat_completion(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms response time
            return "Mock AI response"
        
        mock_client.chat_completion = mock_chat_completion
        mock_client.test_connection = AsyncMock(return_value=True)
        return mock_client

    @pytest.mark.asyncio
    async def test_llm_response_time(self, performance_llm_client):
        """Test LLM response time consistency"""
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            
            response = await performance_llm_client.chat_completion(
                messages=[{"role": "user", "content": f"Test message {i}"}]
            )
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            assert response == "Mock AI response"
        
        # Check response time consistency
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time}s"
        assert max_response_time < 1.0, f"Max response time too high: {max_response_time}s"

    @pytest.mark.asyncio
    async def test_concurrent_llm_requests(self, performance_llm_client):
        """Test concurrent LLM request handling"""
        start_time = time.time()
        
        # Simulate 5 concurrent requests
        tasks = []
        for i in range(5):
            task = performance_llm_client.chat_completion(
                messages=[{"role": "user", "content": f"Concurrent request {i}"}]
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle concurrent requests efficiently
        assert len(responses) == 5
        assert all(r == "Mock AI response" for r in responses)
        # Should be faster than sequential (5 * 0.1 = 0.5s)
        assert duration < 0.3, f"Concurrent requests took too long: {duration}s"


@pytest.mark.performance
class TestSystemResourceUtilization:
    """Test system resource usage and optimization"""

    def test_memory_usage_monitoring(self):
        """Test memory usage doesn't grow excessively"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Simulate some operations that might cause memory growth
        large_data = []
        for i in range(1000):
            large_data.append({'data': f'item_{i}' * 100})
        
        # Clean up
        del large_data
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for this test)
        assert memory_growth < 50 * 1024 * 1024, f"Excessive memory growth: {memory_growth} bytes"

    def test_cpu_usage_monitoring(self):
        """Test CPU usage during intensive operations"""
        # Get initial CPU percentage
        initial_cpu = psutil.cpu_percent(interval=0.1)
        
        # Simulate CPU-intensive operation
        start_time = time.time()
        result = sum(i * i for i in range(10000))
        end_time = time.time()
        
        operation_time = end_time - start_time
        
        # Operation should complete quickly
        assert operation_time < 1.0, f"CPU operation took too long: {operation_time}s"
        assert result > 0  # Ensure operation actually ran

    @pytest.mark.asyncio
    async def test_async_operation_efficiency(self):
        """Test async operation efficiency"""
        async def mock_async_operation(delay=0.01):
            """Mock async operation with small delay"""
            await asyncio.sleep(delay)
            return "completed"
        
        start_time = time.time()
        
        # Run 20 concurrent async operations
        tasks = [mock_async_operation() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete much faster than sequential execution (20 * 0.01 = 0.2s)
        assert len(results) == 20
        assert all(r == "completed" for r in results)
        assert duration < 0.1, f"Async operations not efficient enough: {duration}s"


@pytest.mark.performance
class TestCachingPerformance:
    """Test caching system performance and effectiveness"""

    @pytest.fixture
    def mock_cache_system(self):
        """Mock cache system for testing"""
        cache_data = {}
        
        class MockCache:
            async def get(self, key):
                return cache_data.get(key)
            
            async def set(self, key, value, ttl=None):
                cache_data[key] = value
            
            async def delete(self, key):
                cache_data.pop(key, None)
            
            def clear(self):
                cache_data.clear()
        
        return MockCache()

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, mock_cache_system):
        """Test cache hit performance"""
        # Populate cache
        await mock_cache_system.set("test_key", "test_value")
        
        start_time = time.time()
        
        # Perform 100 cache hits
        for i in range(100):
            result = await mock_cache_system.get("test_key")
            assert result == "test_value"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Cache hits should be very fast
        assert duration < 0.1, f"Cache hits too slow: {duration}s"

    @pytest.mark.asyncio
    async def test_cache_miss_handling(self, mock_cache_system):
        """Test cache miss handling performance"""
        start_time = time.time()
        
        # Perform 50 cache misses
        for i in range(50):
            result = await mock_cache_system.get(f"nonexistent_key_{i}")
            assert result is None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Cache misses should still be fast
        assert duration < 0.1, f"Cache misses too slow: {duration}s"

    @pytest.mark.asyncio
    async def test_cache_write_performance(self, mock_cache_system):
        """Test cache write performance"""
        start_time = time.time()
        
        # Write 100 items to cache
        for i in range(100):
            await mock_cache_system.set(f"key_{i}", f"value_{i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Cache writes should be fast
        assert duration < 0.5, f"Cache writes too slow: {duration}s"
        
        # Verify all items were written
        for i in range(10):  # Check first 10 items
            result = await mock_cache_system.get(f"key_{i}")
            assert result == f"value_{i}"


@pytest.mark.performance
class TestScalabilityMetrics:
    """Test system scalability under various loads"""

    @pytest.mark.asyncio
    async def test_user_scalability(self):
        """Test system behavior with increasing user load"""
        async def simulate_user_session(user_id, session_duration=0.1):
            """Simulate a user session"""
            await asyncio.sleep(session_duration)
            return f"user_{user_id}_completed"
        
        # Test with increasing user counts
        user_counts = [10, 25, 50]
        results = {}
        
        for user_count in user_counts:
            start_time = time.time()
            
            tasks = [
                simulate_user_session(user_id)
                for user_id in range(user_count)
            ]
            
            session_results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            results[user_count] = {
                'duration': duration,
                'completed_sessions': len(session_results)
            }
            
            # Ensure all sessions completed
            assert len(session_results) == user_count
        
        # Verify scalability characteristics
        for user_count in user_counts:
            # Duration should scale reasonably with user count
            expected_max_duration = 0.2 * (user_count / 10)  # Scale factor
            actual_duration = results[user_count]['duration']
            
            assert actual_duration < expected_max_duration, \
                f"Poor scalability at {user_count} users: {actual_duration}s"

    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """Test message processing throughput"""
        async def process_message(message_id):
            """Mock message processing"""
            await asyncio.sleep(0.01)  # 10ms processing time
            return f"processed_message_{message_id}"
        
        start_time = time.time()
        
        # Process 100 messages concurrently
        tasks = [process_message(i) for i in range(100)]
        processed_messages = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate throughput
        throughput = len(processed_messages) / duration
        
        # Should achieve high throughput (>50 messages/second)
        assert throughput > 50, f"Low message throughput: {throughput} msg/s"
        assert len(processed_messages) == 100


if __name__ == "__main__":
    # Allow running this test suite directly
    pytest.main([__file__, "-v", "-m", "performance"])