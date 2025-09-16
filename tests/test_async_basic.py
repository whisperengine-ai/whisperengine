#!/usr/bin/env python3
"""
Quick async/IO validation test - focused on core functionality without hanging
"""

import asyncio
import os
import sys
import threading
import time

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_basic_async_operations():
    """Test basic async operations without complex mocks"""

    # Test 1: Basic async/await functionality
    async def simple_async_task(delay, result):
        await asyncio.sleep(delay)
        return f"Task completed: {result}"

    start_time = time.time()
    tasks = [simple_async_task(0.1, i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time

    assert len(results) == 5
    assert duration < 0.5  # Should complete concurrently, not sequentially

    return True


async def test_threading_integration():
    """Test async/threading integration"""

    shared_data = {"counter": 0}
    lock = threading.Lock()

    def thread_work(task_id):
        time.sleep(0.1)  # Simulate work
        with lock:
            shared_data["counter"] += 1
        return f"Thread {task_id} done"

    # Run thread work in executor
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, thread_work, i) for i in range(5)]

    start_time = time.time()
    results = await asyncio.gather(*tasks)
    time.time() - start_time

    assert shared_data["counter"] == 5
    assert len(results) == 5

    return True


async def test_semaphore_limiting():
    """Test semaphore-based concurrency limiting"""

    semaphore = asyncio.Semaphore(2)  # Allow only 2 concurrent operations
    active_count = {"value": 0}
    max_concurrent = {"value": 0}

    async def limited_task(task_id):
        async with semaphore:
            active_count["value"] += 1
            max_concurrent["value"] = max(max_concurrent["value"], active_count["value"])
            await asyncio.sleep(0.1)  # Simulate work
            active_count["value"] -= 1
            return f"Task {task_id} completed"

    tasks = [limited_task(i) for i in range(6)]
    results = await asyncio.gather(*tasks)

    assert max_concurrent["value"] <= 2
    assert len(results) == 6

    return True


async def test_timeout_protection():
    """Test timeout protection mechanisms"""

    async def slow_task():
        await asyncio.sleep(2)  # Intentionally slow
        return "Should not complete"

    # Test timeout works
    try:
        await asyncio.wait_for(slow_task(), timeout=0.5)
        raise AssertionError("Should have timed out")
    except TimeoutError:
        return True

    return False


async def main():
    """Run focused async tests"""

    tests = [
        ("Basic Async Operations", test_basic_async_operations),
        ("Threading Integration", test_threading_integration),
        ("Semaphore Limiting", test_semaphore_limiting),
        ("Timeout Protection", test_timeout_protection),
    ]

    passed = 0
    total = len(tests)

    for _test_name, test_func in tests:
        try:
            success = await asyncio.wait_for(test_func(), timeout=10)
            if success:
                passed += 1
            else:
                pass
        except TimeoutError:
            pass
        except Exception:
            pass


    if passed == total:
        pass
    else:
        pass

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)
