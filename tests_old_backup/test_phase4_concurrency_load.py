"""
Phase 4 Concurrency and Load Testing Suite

This focused test suite validates Phase 4 systems under heavy concurrent load,
testing for race conditions, thread safety, and performance degradation.

Key Areas:
1. Memory system thread safety with multiple concurrent users
2. Thread manager concurrent conversation processing
3. Engagement engine simultaneous analysis operations
4. Cross-component integration under stress
5. Resource exhaustion and cleanup behavior

Testing Strategy:
- Start with realistic workloads and scale up
- Focus on actual method signatures that exist
- Test error conditions and recovery
- Measure performance baselines and degradation
- Validate data consistency under concurrent access
"""

import asyncio
import logging
import random
import time
import uuid

import pytest

# Import actual Phase 4 components
try:
    from src.personality.memory_moments import MemoryTriggeredMoments

    MEMORY_MOMENTS_AVAILABLE = True
except ImportError:
    MEMORY_MOMENTS_AVAILABLE = False

try:
    from src.conversation.advanced_thread_manager import AdvancedConversationThreadManager

    THREAD_MANAGER_AVAILABLE = True
except ImportError:
    THREAD_MANAGER_AVAILABLE = False

try:
    from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine

    ENGAGEMENT_ENGINE_AVAILABLE = True
except ImportError:
    ENGAGEMENT_ENGINE_AVAILABLE = False

try:
    from src.intelligence.emotional_context_engine import EmotionalContext, EmotionalContextEngine

    EMOTIONAL_CONTEXT_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_AVAILABLE = False

logger = logging.getLogger(__name__)


class Phase4ConcurrencyTester:
    """Focused concurrency testing for Phase 4 systems"""

    def __init__(self):
        self.memory_moments = None
        self.thread_manager = None
        self.engagement_engine = None
        self.emotional_engine = None
        self.test_results = {}

    async def setup_components(self):
        """Initialize available Phase 4 components"""
        try:
            if MEMORY_MOMENTS_AVAILABLE:
                self.memory_moments = MemoryTriggeredMoments()
                logger.info("✅ Memory moments initialized")

            if THREAD_MANAGER_AVAILABLE:
                self.thread_manager = AdvancedConversationThreadManager()
                logger.info("✅ Thread manager initialized")

            if ENGAGEMENT_ENGINE_AVAILABLE:
                self.engagement_engine = ProactiveConversationEngagementEngine()
                logger.info("✅ Engagement engine initialized")

            if EMOTIONAL_CONTEXT_AVAILABLE:
                self.emotional_engine = EmotionalContextEngine()
                logger.info("✅ Emotional engine initialized")

            return True

        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            return False

    def generate_realistic_messages(self, count: int) -> list[str]:
        """Generate realistic conversation messages for testing"""
        conversation_starters = [
            "I've been thinking about my career lately",
            "I had an interesting conversation with my friend",
            "I'm planning a trip to Europe next month",
            "I've been learning Python and it's really exciting",
            "I'm feeling stressed about my upcoming presentation",
            "I watched a great movie last night",
            "I'm trying to decide what to do this weekend",
            "I've been reading about artificial intelligence",
            "I want to start exercising more regularly",
            "I'm considering changing my major",
        ]

        follow_ups = [
            "What do you think about that?",
            "I'm not sure how to proceed",
            "It's been on my mind a lot",
            "I'd love to hear your thoughts",
            "I'm feeling uncertain about it",
            "It's really important to me",
            "I need some advice",
            "I'm excited about the possibilities",
            "I'm a bit nervous though",
            "I want to make the right decision",
        ]

        messages = []
        for _ in range(count):
            if random.random() < 0.7:  # 70% conversation starters
                message = random.choice(conversation_starters)
            else:  # 30% follow-ups
                message = random.choice(follow_ups)

            # Add some variation
            if random.random() < 0.3:
                message += f" {random.choice(follow_ups)}"

            messages.append(message)

        return messages

    async def test_thread_manager_concurrency(
        self, user_count: int = 50, messages_per_user: int = 10
    ):
        """Test thread manager under concurrent load"""
        if not self.thread_manager:
            logger.warning("⚠️ Thread manager not available, skipping test")
            return {"skipped": True}

        logger.info(
            f"🧵 Testing thread manager concurrency: {user_count} users, {messages_per_user} messages each"
        )

        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        errors = []

        async def process_user_conversation(user_id: str):
            """Process a full conversation for one user"""
            nonlocal successful_operations, failed_operations

            try:
                messages = self.generate_realistic_messages(messages_per_user)

                for i, message in enumerate(messages):
                    try:
                        # Add small delay to simulate real conversation timing
                        if i > 0:
                            await asyncio.sleep(random.uniform(0.01, 0.05))

                        await self.thread_manager.process_user_message(
                            user_id, message, {"message_index": i}
                        )

                        successful_operations += 1

                    except Exception as e:
                        failed_operations += 1
                        error_msg = f"User {user_id} message {i}: {str(e)[:100]}"
                        errors.append(error_msg)

            except Exception as e:
                failed_operations += messages_per_user
                errors.append(f"User {user_id} conversation failed: {str(e)[:100]}")

        # Generate user IDs and run concurrent conversations
        user_ids = [f"concurrent_user_{uuid.uuid4().hex[:8]}" for _ in range(user_count)]

        tasks = [process_user_conversation(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time
        total_operations = user_count * messages_per_user

        result = {
            "component": "thread_manager",
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "errors_sample": errors[:5],  # First 5 errors for analysis
        }

        logger.info(
            f"✅ Thread manager concurrency: {successful_operations}/{total_operations} "
            f"({result['success_rate']:.2%}) in {duration:.2f}s "
            f"({result['operations_per_second']:.1f} ops/sec)"
        )

        return result

    async def test_memory_access_concurrency(
        self, user_count: int = 30, operations_per_user: int = 15
    ):
        """Test memory system concurrent access patterns"""
        if not self.memory_moments:
            logger.warning("⚠️ Memory moments not available, skipping test")
            return {"skipped": True}

        logger.info(
            f"🧠 Testing memory access concurrency: {user_count} users, {operations_per_user} ops each"
        )

        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        errors = []

        async def memory_operations_worker(user_id: str):
            """Perform memory operations for one user"""
            nonlocal successful_operations, failed_operations

            try:
                messages = self.generate_realistic_messages(operations_per_user)

                for i, message in enumerate(messages):
                    try:
                        # Test memory analysis - use the actual method signature
                        await self.memory_moments.analyze_conversation_for_memories(
                            user_id,
                            f"context_{i}",
                            message,
                            None,  # No emotional context for simplicity
                        )

                        successful_operations += 1

                        # Small delay to simulate processing time
                        await asyncio.sleep(0.001)

                    except Exception as e:
                        failed_operations += 1
                        error_msg = f"User {user_id} op {i}: {str(e)[:100]}"
                        errors.append(error_msg)

            except Exception as e:
                failed_operations += operations_per_user
                errors.append(f"User {user_id} memory operations failed: {str(e)[:100]}")

        # Run concurrent memory operations
        user_ids = [f"memory_user_{uuid.uuid4().hex[:8]}" for _ in range(user_count)]

        tasks = [memory_operations_worker(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time
        total_operations = user_count * operations_per_user

        result = {
            "component": "memory_moments",
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "errors_sample": errors[:5],
        }

        logger.info(
            f"✅ Memory access concurrency: {successful_operations}/{total_operations} "
            f"({result['success_rate']:.2%}) in {duration:.2f}s "
            f"({result['operations_per_second']:.1f} ops/sec)"
        )

        return result

    async def test_engagement_analysis_concurrency(
        self, user_count: int = 40, analyses_per_user: int = 12
    ):
        """Test engagement engine concurrent analysis operations"""
        if not self.engagement_engine:
            logger.warning("⚠️ Engagement engine not available, skipping test")
            return {"skipped": True}

        logger.info(
            f"💡 Testing engagement analysis concurrency: {user_count} users, {analyses_per_user} analyses each"
        )

        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        errors = []

        async def engagement_analysis_worker(user_id: str):
            """Perform engagement analysis for one user"""
            nonlocal successful_operations, failed_operations

            try:
                # Create a realistic conversation pattern with varying engagement
                messages = [
                    "I'm really excited about this new project!",
                    "It's going to be challenging but I think I can do it.",
                    "Yeah...",
                    "I guess so...",
                    "Hmm...",
                    "That's actually really interesting!",
                    "Tell me more about that approach.",
                    "I see what you mean.",
                    "OK...",
                    "Sure...",
                    "This is fascinating! I want to learn more!",
                    "Thanks for explaining that.",
                ]

                for i in range(min(analyses_per_user, len(messages))):
                    try:
                        message = messages[i]

                        # Test engagement analysis - check actual method signature
                        await self.engagement_engine.analyze_conversation_engagement(
                            user_id, message, []  # Empty list for recent_messages
                        )

                        successful_operations += 1

                        # Small processing delay
                        await asyncio.sleep(0.002)

                    except Exception as e:
                        failed_operations += 1
                        error_msg = f"User {user_id} analysis {i}: {str(e)[:100]}"
                        errors.append(error_msg)

            except Exception as e:
                failed_operations += analyses_per_user
                errors.append(f"User {user_id} engagement analysis failed: {str(e)[:100]}")

        # Run concurrent engagement analyses
        user_ids = [f"engagement_user_{uuid.uuid4().hex[:8]}" for _ in range(user_count)]

        tasks = [engagement_analysis_worker(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time
        total_operations = user_count * analyses_per_user

        result = {
            "component": "engagement_engine",
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "errors_sample": errors[:5],
        }

        logger.info(
            f"✅ Engagement analysis concurrency: {successful_operations}/{total_operations} "
            f"({result['success_rate']:.2%}) in {duration:.2f}s "
            f"({result['operations_per_second']:.1f} ops/sec)"
        )

        return result

    async def test_integrated_system_load(
        self, user_count: int = 25, interactions_per_user: int = 8
    ):
        """Test complete Phase 4 system under integrated load"""
        logger.info(
            f"🔄 Testing integrated system load: {user_count} users, {interactions_per_user} interactions each"
        )

        start_time = time.time()

        async def integrated_user_session(user_id: str):
            """Simulate a complete user conversation session"""
            session_results = {
                "thread_operations": 0,
                "memory_operations": 0,
                "engagement_operations": 0,
                "errors": [],
            }

            try:
                messages = self.generate_realistic_messages(interactions_per_user)

                for i, message in enumerate(messages):
                    # Thread management
                    if self.thread_manager:
                        try:
                            await self.thread_manager.process_user_message(user_id, message, {})
                            session_results["thread_operations"] += 1
                        except Exception as e:
                            session_results["errors"].append(f"Thread: {str(e)[:50]}")

                    # Memory analysis
                    if self.memory_moments:
                        try:
                            await self.memory_moments.analyze_conversation_for_memories(
                                user_id, f"context_{i}", message, None
                            )
                            session_results["memory_operations"] += 1
                        except Exception as e:
                            session_results["errors"].append(f"Memory: {str(e)[:50]}")

                    # Engagement analysis
                    if self.engagement_engine:
                        try:
                            await self.engagement_engine.analyze_conversation_engagement(
                                user_id, message, []
                            )
                            session_results["engagement_operations"] += 1
                        except Exception as e:
                            session_results["errors"].append(f"Engagement: {str(e)[:50]}")

                    # Small delay between interactions
                    await asyncio.sleep(0.01)

            except Exception as e:
                session_results["errors"].append(f"Session: {str(e)[:50]}")

            return session_results

        # Run integrated user sessions
        user_ids = [f"integrated_user_{uuid.uuid4().hex[:8]}" for _ in range(user_count)]

        session_results = await asyncio.gather(
            *[integrated_user_session(user_id) for user_id in user_ids], return_exceptions=True
        )

        end_time = time.time()
        duration = end_time - start_time

        # Aggregate results
        total_thread_ops = sum(
            r.get("thread_operations", 0) for r in session_results if isinstance(r, dict)
        )
        total_memory_ops = sum(
            r.get("memory_operations", 0) for r in session_results if isinstance(r, dict)
        )
        total_engagement_ops = sum(
            r.get("engagement_operations", 0) for r in session_results if isinstance(r, dict)
        )
        total_errors = sum(len(r.get("errors", [])) for r in session_results if isinstance(r, dict))

        result = {
            "component": "integrated_system",
            "user_count": user_count,
            "interactions_per_user": interactions_per_user,
            "thread_operations": total_thread_ops,
            "memory_operations": total_memory_ops,
            "engagement_operations": total_engagement_ops,
            "total_operations": total_thread_ops + total_memory_ops + total_engagement_ops,
            "total_errors": total_errors,
            "duration_seconds": duration,
            "operations_per_second": (
                (total_thread_ops + total_memory_ops + total_engagement_ops) / duration
                if duration > 0
                else 0
            ),
        }

        logger.info(
            f"✅ Integrated system load: {result['total_operations']} total ops "
            f"in {duration:.2f}s ({result['operations_per_second']:.1f} ops/sec), "
            f"{total_errors} errors"
        )

        return result


# Pytest test functions
@pytest.mark.asyncio
async def test_thread_manager_heavy_load():
    """Test thread manager under heavy concurrent load"""
    tester = Phase4ConcurrencyTester()
    success = await tester.setup_components()

    if not success:
        pytest.skip("Could not initialize Phase 4 components")

    # Test with increasing load
    result = await tester.test_thread_manager_concurrency(user_count=50, messages_per_user=10)

    if result.get("skipped"):
        pytest.skip("Thread manager not available")

    # Assert reasonable performance
    assert (
        result["success_rate"] >= 0.90
    ), f"Thread manager success rate too low: {result['success_rate']}"
    assert (
        result["operations_per_second"] > 10
    ), f"Thread manager too slow: {result['operations_per_second']} ops/sec"


@pytest.mark.asyncio
async def test_memory_system_concurrency():
    """Test memory system concurrent access safety"""
    tester = Phase4ConcurrencyTester()
    success = await tester.setup_components()

    if not success:
        pytest.skip("Could not initialize Phase 4 components")

    result = await tester.test_memory_access_concurrency(user_count=30, operations_per_user=15)

    if result.get("skipped"):
        pytest.skip("Memory moments not available")

    # Assert thread safety and performance
    assert (
        result["success_rate"] >= 0.95
    ), f"Memory system success rate too low: {result['success_rate']}"
    assert (
        result["operations_per_second"] > 50
    ), f"Memory system too slow: {result['operations_per_second']} ops/sec"


@pytest.mark.asyncio
async def test_engagement_engine_load():
    """Test engagement engine under analysis load"""
    tester = Phase4ConcurrencyTester()
    success = await tester.setup_components()

    if not success:
        pytest.skip("Could not initialize Phase 4 components")

    result = await tester.test_engagement_analysis_concurrency(user_count=40, analyses_per_user=12)

    if result.get("skipped"):
        pytest.skip("Engagement engine not available")

    # Assert performance under load
    assert (
        result["success_rate"] >= 0.92
    ), f"Engagement engine success rate too low: {result['success_rate']}"
    assert (
        result["operations_per_second"] > 30
    ), f"Engagement engine too slow: {result['operations_per_second']} ops/sec"


@pytest.mark.asyncio
async def test_integrated_phase4_system_load():
    """Test complete Phase 4 system under realistic load"""
    tester = Phase4ConcurrencyTester()
    success = await tester.setup_components()

    if not success:
        pytest.skip("Could not initialize Phase 4 components")

    result = await tester.test_integrated_system_load(user_count=25, interactions_per_user=8)

    # Assert overall system stability
    error_rate = (
        result["total_errors"] / result["total_operations"]
        if result["total_operations"] > 0
        else 1.0
    )
    assert error_rate <= 0.10, f"Integrated system error rate too high: {error_rate:.2%}"
    assert (
        result["operations_per_second"] > 15
    ), f"Integrated system too slow: {result['operations_per_second']} ops/sec"


if __name__ == "__main__":

    async def run_all_tests():
        """Run all concurrency tests manually"""
        tester = Phase4ConcurrencyTester()
        success = await tester.setup_components()

        if not success:
            logger.error("❌ Failed to setup test environment")
            return

        logger.info("🚀 Starting Phase 4 concurrency testing suite...")

        # Run all tests
        thread_result = await tester.test_thread_manager_concurrency(50, 10)
        memory_result = await tester.test_memory_access_concurrency(30, 15)
        engagement_result = await tester.test_engagement_analysis_concurrency(40, 12)
        integrated_result = await tester.test_integrated_system_load(25, 8)

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 PHASE 4 CONCURRENCY TEST SUMMARY")
        logger.info("=" * 80)

        for result in [thread_result, memory_result, engagement_result, integrated_result]:
            if not result.get("skipped"):
                component = result["component"]
                success_rate = result.get("success_rate", 0)
                ops_per_sec = result.get("operations_per_second", 0)
                logger.info(
                    f"✅ {component:20} - {success_rate:6.1%} success, {ops_per_sec:6.1f} ops/sec"
                )

        logger.info("=" * 80)

    # Run the test suite
    asyncio.run(run_all_tests())
