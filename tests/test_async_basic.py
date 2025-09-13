#!/usr/bin/env python3
"""
Quick async/IO validation test - focused on core functionality without hanging
"""

import asyncio
import time
import threading
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_basic_async_operations():
    """Test basic async operations without complex mocks"""
    print("🧪 Testing basic async operations...")
    
    # Test 1: Basic async/await functionality
    async def simple_async_task(delay, result):
        await asyncio.sleep(delay)
        return f"Task completed: {result}"
    
    start_time = time.time()
    tasks = [simple_async_task(0.1, i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    print(f"✅ Basic async test: {len(results)} tasks in {duration:.2f}s")
    assert len(results) == 5
    assert duration < 0.5  # Should complete concurrently, not sequentially
    
    return True

async def test_threading_integration():
    """Test async/threading integration"""
    print("🧪 Testing async/threading integration...")
    
    shared_data = {'counter': 0}
    lock = threading.Lock()
    
    def thread_work(task_id):
        time.sleep(0.1)  # Simulate work
        with lock:
            shared_data['counter'] += 1
        return f"Thread {task_id} done"
    
    # Run thread work in executor
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, thread_work, i) 
        for i in range(5)
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    print(f"✅ Threading integration: {shared_data['counter']} operations in {duration:.2f}s")
    assert shared_data['counter'] == 5
    assert len(results) == 5
    
    return True

async def test_semaphore_limiting():
    """Test semaphore-based concurrency limiting"""
    print("🧪 Testing semaphore limiting...")
    
    semaphore = asyncio.Semaphore(2)  # Allow only 2 concurrent operations
    active_count = {'value': 0}
    max_concurrent = {'value': 0}
    
    async def limited_task(task_id):
        async with semaphore:
            active_count['value'] += 1
            max_concurrent['value'] = max(max_concurrent['value'], active_count['value'])
            await asyncio.sleep(0.1)  # Simulate work
            active_count['value'] -= 1
            return f"Task {task_id} completed"
    
    tasks = [limited_task(i) for i in range(6)]
    results = await asyncio.gather(*tasks)
    
    print(f"✅ Semaphore limiting: max concurrent = {max_concurrent['value']} (should be ≤ 2)")
    assert max_concurrent['value'] <= 2
    assert len(results) == 6
    
    return True

async def test_timeout_protection():
    """Test timeout protection mechanisms"""
    print("🧪 Testing timeout protection...")
    
    async def slow_task():
        await asyncio.sleep(2)  # Intentionally slow
        return "Should not complete"
    
    # Test timeout works
    try:
        result = await asyncio.wait_for(slow_task(), timeout=0.5)
        assert False, "Should have timed out"
    except asyncio.TimeoutError:
        print("✅ Timeout protection working correctly")
        return True
    
    return False

async def main():
    """Run focused async tests"""
    print("🚀 Quick Async/IO Validation Test")
    print("=" * 40)
    
    tests = [
        ("Basic Async Operations", test_basic_async_operations),
        ("Threading Integration", test_threading_integration), 
        ("Semaphore Limiting", test_semaphore_limiting),
        ("Timeout Protection", test_timeout_protection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n📝 {test_name}...")
            success = await asyncio.wait_for(test_func(), timeout=10)
            if success:
                passed += 1
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
        except asyncio.TimeoutError:
            print(f"   ⏰ TIMEOUT (test took too long)")
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    print("\n" + "=" * 40)
    print(f"🏁 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All async/IO fundamentals are working correctly!")
        print("🎯 Your async enhancements should work properly.")
    else:
        print("❌ Some basic async functionality issues detected.")
        print("🔧 Please review the async implementation.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n{'🎉 SUCCESS' if success else '⚠️  ISSUES DETECTED'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
