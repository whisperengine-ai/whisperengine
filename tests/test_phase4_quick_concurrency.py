"""
Quick Phase 4 Concurrency Test

Simple test to validate Phase 4 components under concurrent load
and identify any performance bottlenecks or race conditions.
"""

import asyncio
import logging
import time
import uuid
import random

from src.personality.memory_moments import MemoryTriggeredMoments
from src.conversation.advanced_thread_manager import AdvancedConversationThreadManager
from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_thread_manager_concurrency():
    """Test thread manager with concurrent users"""
    logger.info("🧵 Testing thread manager concurrency...")
    
    thread_manager = AdvancedConversationThreadManager()
    
    start_time = time.time()
    successful_ops = 0
    failed_ops = 0
    
    async def user_conversation(user_id: str):
        nonlocal successful_ops, failed_ops
        
        messages = [
            "I want to discuss my career plans",
            "I'm thinking about learning Python", 
            "I need advice about relationships",
            "Let me tell you about my weekend"
        ]
        
        for message in messages:
            try:
                result = await thread_manager.process_user_message(user_id, message, {})
                successful_ops += 1
                await asyncio.sleep(0.01)  # Small delay
            except Exception as e:
                failed_ops += 1
                logger.error(f"Thread manager error for {user_id}: {e}")
    
    # Test with 20 concurrent users
    user_ids = [f"user_{i}" for i in range(20)]
    tasks = [user_conversation(user_id) for user_id in user_ids]
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    total_ops = successful_ops + failed_ops
    
    logger.info(f"✅ Thread manager: {successful_ops}/{total_ops} ops successful "
               f"({successful_ops/total_ops:.1%}) in {duration:.2f}s")
    
    return {
        "component": "thread_manager",
        "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
        "duration": duration,
        "ops_per_second": total_ops / duration if duration > 0 else 0
    }

async def test_memory_moments_concurrency():
    """Test memory moments with concurrent access"""
    logger.info("🧠 Testing memory moments concurrency...")
    
    memory_moments = MemoryTriggeredMoments()
    
    start_time = time.time()
    successful_ops = 0
    failed_ops = 0
    
    async def memory_worker(user_id: str):
        nonlocal successful_ops, failed_ops
        
        messages = [
            "I remember we talked about my goals",
            "This reminds me of our previous chat",
            "I'm thinking about what you said before",
            "This connects to our earlier discussion"
        ]
        
        for i, message in enumerate(messages):
            try:
                connections = await memory_moments.analyze_conversation_for_memories(
                    user_id, f"context_{i}", message, None
                )
                successful_ops += 1
                await asyncio.sleep(0.005)  # Small delay
            except Exception as e:
                failed_ops += 1
                logger.error(f"Memory moments error for {user_id}: {e}")
    
    # Test with 15 concurrent users
    user_ids = [f"memory_user_{i}" for i in range(15)]
    tasks = [memory_worker(user_id) for user_id in user_ids]
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    total_ops = successful_ops + failed_ops
    
    logger.info(f"✅ Memory moments: {successful_ops}/{total_ops} ops successful "
               f"({successful_ops/total_ops:.1%}) in {duration:.2f}s")
    
    return {
        "component": "memory_moments", 
        "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
        "duration": duration,
        "ops_per_second": total_ops / duration if duration > 0 else 0
    }

async def test_engagement_engine_concurrency():
    """Test engagement engine with concurrent analysis"""
    logger.info("💡 Testing engagement engine concurrency...")
    
    engagement_engine = ProactiveConversationEngagementEngine()
    
    start_time = time.time()
    successful_ops = 0
    failed_ops = 0
    
    async def engagement_worker(user_id: str):
        nonlocal successful_ops, failed_ops
        
        messages = [
            "This is really exciting!",
            "Yeah, I guess so...",
            "Hmm...", 
            "That's fascinating! Tell me more!"
        ]
        
        for message in messages:
            try:
                analysis = await engagement_engine.analyze_conversation_engagement(
                    user_id, message, []
                )
                successful_ops += 1
                await asyncio.sleep(0.01)  # Small delay
            except Exception as e:
                failed_ops += 1
                logger.error(f"Engagement engine error for {user_id}: {e}")
    
    # Test with 10 concurrent users
    user_ids = [f"engagement_user_{i}" for i in range(10)]
    tasks = [engagement_worker(user_id) for user_id in user_ids]
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    total_ops = successful_ops + failed_ops
    
    logger.info(f"✅ Engagement engine: {successful_ops}/{total_ops} ops successful "
               f"({successful_ops/total_ops:.1%}) in {duration:.2f}s")
    
    return {
        "component": "engagement_engine",
        "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
        "duration": duration,
        "ops_per_second": total_ops / duration if duration > 0 else 0
    }

async def main():
    """Run all Phase 4 concurrency tests"""
    logger.info("🚀 Starting Phase 4 Quick Concurrency Tests")
    logger.info("="*60)
    
    # Run tests sequentially to isolate any issues
    results = []
    
    try:
        thread_result = await test_thread_manager_concurrency()
        results.append(thread_result)
    except Exception as e:
        logger.error(f"❌ Thread manager test failed: {e}")
        results.append({"component": "thread_manager", "error": str(e)})
    
    try:
        memory_result = await test_memory_moments_concurrency()
        results.append(memory_result)
    except Exception as e:
        logger.error(f"❌ Memory moments test failed: {e}")
        results.append({"component": "memory_moments", "error": str(e)})
    
    try:
        engagement_result = await test_engagement_engine_concurrency()
        results.append(engagement_result)
    except Exception as e:
        logger.error(f"❌ Engagement engine test failed: {e}")
        results.append({"component": "engagement_engine", "error": str(e)})
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("🎉 PHASE 4 CONCURRENCY TEST SUMMARY")
    logger.info("="*60)
    
    for result in results:
        component = result["component"]
        if "error" in result:
            logger.info(f"❌ {component:20} - ERROR: {result['error']}")
        else:
            success_rate = result["success_rate"]
            ops_per_sec = result["ops_per_second"]
            status = "✅" if success_rate >= 0.95 else "⚠️" if success_rate >= 0.90 else "❌"
            logger.info(f"{status} {component:20} - {success_rate:6.1%} success, {ops_per_sec:6.1f} ops/sec")
    
    logger.info("="*60)
    logger.info("✅ Phase 4 concurrency testing complete!")

if __name__ == "__main__":
    asyncio.run(main())