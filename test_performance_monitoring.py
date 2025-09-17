#!/usr/bin/env python3
"""
Performance Monitoring Test Script
Test the new performance monitoring system and generate sample data
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import environment manager to load configuration
from env_manager import load_environment

# Load environment configuration
if not load_environment():
    print("❌ Failed to load environment configuration")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_performance_monitoring():
    """Test the performance monitoring system with realistic workloads"""
    
    try:
        # Import performance monitoring
        from src.utils.performance_monitor import performance_monitor, performance_optimizer, monitor_performance
        from src.llm.llm_client import LLMClient
        from src.memory.integrated_memory_manager import IntegratedMemoryManager
        
        logger.info("🔄 Starting performance monitoring system...")
        performance_monitor.start_monitoring()
        
        # Initialize test components
        logger.info("⚙️ Initializing test components...")
        llm_client = LLMClient()
        memory_manager = IntegratedMemoryManager(llm_client=llm_client)
        
        logger.info("📊 Running performance test scenarios...")
        
        # Test scenario 1: LLM Performance
        logger.info("🤖 Testing LLM performance...")
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you today?"}
        ]
        
        # Generate multiple requests with monitoring
        for i in range(5):
            try:
                start_time = time.time()
                response = llm_client.generate_chat_completion(
                    messages=test_messages,
                    max_tokens=100
                )
                duration_ms = (time.time() - start_time) * 1000
                
                success = 'choices' in response and response['choices']
                performance_monitor.record_metric(
                    operation="test_llm_request",
                    duration_ms=duration_ms,
                    success=success,
                    metadata={'test_iteration': i + 1}
                )
                
                logger.info(f"   • LLM request {i+1}: {duration_ms:.0f}ms ({'✅' if success else '❌'})")
                await asyncio.sleep(0.5)  # Small delay between requests
                
            except Exception as e:
                logger.error(f"   • LLM request {i+1} failed: {e}")
                performance_monitor.record_metric(
                    operation="test_llm_request",
                    duration_ms=5000,  # Penalty for failure
                    success=False,
                    metadata={'error': str(e)}
                )
        
        # Test scenario 2: Memory Performance
        logger.info("🧠 Testing memory performance...")
        test_user_id = "test_user_12345"
        
        for i in range(3):
            try:
                start_time = time.time()
                memories = await memory_manager.retrieve_contextual_memories(
                    user_id=test_user_id,
                    query=f"test query {i+1}",
                    limit=5
                )
                duration_ms = (time.time() - start_time) * 1000
                
                success = isinstance(memories, list)
                performance_monitor.record_metric(
                    operation="test_memory_retrieval",
                    duration_ms=duration_ms,
                    success=success,
                    metadata={'memory_count': len(memories) if success else 0}
                )
                
                logger.info(f"   • Memory query {i+1}: {duration_ms:.0f}ms ({'✅' if success else '❌'}) - {len(memories) if success else 0} memories")
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.info(f"   • Memory query {i+1} failed: {e} (this is expected if no memory data exists)")
                performance_monitor.record_metric(
                    operation="test_memory_retrieval",
                    duration_ms=1000,
                    success=False,
                    metadata={'error': str(e)}
                )
        
        # Test scenario 3: Simulate slow operations
        logger.info("⏳ Testing slow operation detection...")
        for i in range(3):
            start_time = time.time()
            # Simulate a slow operation
            await asyncio.sleep(0.8 + (i * 0.4))  # 0.8s, 1.2s, 1.6s
            duration_ms = (time.time() - start_time) * 1000
            
            performance_monitor.record_metric(
                operation="test_slow_operation",
                duration_ms=duration_ms,
                success=True,
                metadata={'simulated_delay': True}
            )
            
            logger.info(f"   • Slow operation {i+1}: {duration_ms:.0f}ms")
        
        # Give monitoring system time to process
        logger.info("⏱️ Waiting for monitoring analysis...")
        await asyncio.sleep(2)
        
        # Get performance analysis
        logger.info("📈 Performance Analysis Results:")
        logger.info("=" * 50)
        
        # System health
        health = performance_monitor.get_system_health()
        logger.info(f"🏥 System Health: {health['overall_health'].upper()}")
        logger.info(f"   • Success Rate: {health['avg_success_rate']:.1%}")
        logger.info(f"   • Avg Response Time: {health['avg_response_time_ms']:.0f}ms")
        logger.info(f"   • Memory Usage: {health['memory_usage_mb']:.0f}MB")
        logger.info(f"   • Active Operations: {health['active_operations']}")
        
        # All operation stats
        all_stats = performance_monitor.get_all_stats()
        if all_stats:
            logger.info("\n📊 Operation Statistics:")
            for operation, stats in all_stats.items():
                status = "⚠️ SLOW" if stats.is_degraded() else "✅ OK"
                logger.info(f"   {status} {operation}:")
                logger.info(f"      • Calls: {stats.total_calls}")
                logger.info(f"      • Success Rate: {stats.success_rate:.1%}")
                logger.info(f"      • Avg/P95: {stats.avg_duration_ms:.0f}ms / {stats.p95_duration_ms:.0f}ms")
                logger.info(f"      • Range: {stats.min_duration_ms:.0f}ms - {stats.max_duration_ms:.0f}ms")
        
        # Bottlenecks
        bottlenecks = performance_monitor.get_bottlenecks()
        if bottlenecks:
            logger.info("\n🚨 Performance Bottlenecks:")
            for bottleneck in bottlenecks:
                logger.info(f"   • {bottleneck['operation']} ({bottleneck['severity']} priority)")
                for issue in bottleneck['issues']:
                    logger.info(f"     - {issue}")
                if bottleneck['recommendations']:
                    logger.info(f"     💡 Recommendation: {bottleneck['recommendations'][0]}")
        else:
            logger.info("\n✅ No performance bottlenecks detected")
        
        # Optimization suggestions
        suggestions = performance_optimizer.suggest_optimizations()
        if suggestions:
            logger.info("\n💡 Optimization Suggestions:")
            for suggestion in suggestions:
                logger.info(f"   • {suggestion['description']} ({suggestion['priority']} priority)")
                if suggestion['actions']:
                    logger.info(f"     Action: {suggestion['actions'][0]}")
        else:
            logger.info("\n✅ No immediate optimizations needed")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Performance monitoring test completed successfully!")
        logger.info("💡 To see these metrics in Discord, use: !perf, !optimize, !perf-details")
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Stop monitoring
        if 'performance_monitor' in locals():
            performance_monitor.stop_monitoring()
            logger.info("🔄 Performance monitoring stopped")
    
    return True

async def main():
    """Main test function"""
    logger.info("🚀 Performance Monitoring Test Suite")
    logger.info("=" * 50)
    
    # Test environment
    logger.info("🔍 Environment Check:")
    logger.info(f"   • Python Path: {sys.executable}")
    logger.info(f"   • Working Directory: {os.getcwd()}")
    logger.info(f"   • LLM API URL: {os.getenv('LLM_CHAT_API_URL', 'Not set')}")
    logger.info(f"   • Environment Mode: {os.getenv('ENV_MODE', 'development')}")
    
    success = await test_performance_monitoring()
    
    if success:
        logger.info("\n🎉 All tests passed! Performance monitoring is working correctly.")
        sys.exit(0)
    else:
        logger.error("\n💥 Tests failed! Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())