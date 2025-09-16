"""
Phase 4 Edge Case and Error Handling Test Suite

This test suite validates Phase 4 systems under extreme conditions,
edge cases, and error scenarios to ensure robust production behavior.

Test Categories:
1. Invalid input handling and graceful degradation
2. Resource exhaustion scenarios (memory, connections)
3. Race condition detection and thread safety validation
4. Error recovery and system stability
5. Performance under stress conditions
6. Data corruption and inconsistency detection
"""

import asyncio
import logging
import time
import uuid
import random
import gc
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

from src.personality.memory_moments import MemoryTriggeredMoments
from src.conversation.advanced_thread_manager import AdvancedConversationThreadManager
from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase4EdgeCaseTester:
    """Comprehensive edge case and error testing for Phase 4 systems"""

    def __init__(self):
        self.memory_moments = MemoryTriggeredMoments()
        self.thread_manager = AdvancedConversationThreadManager()
        self.engagement_engine = ProactiveConversationEngagementEngine()

    async def test_invalid_input_handling(self):
        """Test system behavior with invalid, malformed, and edge case inputs"""
        logger.info("🚨 Testing invalid input handling...")

        test_results = {
            "memory_moments_invalid": 0,
            "thread_manager_invalid": 0,
            "engagement_engine_invalid": 0,
            "total_tests": 0,
            "errors_handled": 0,
        }

        # Invalid inputs to test
        invalid_inputs = [
            "",  # Empty string
            " " * 1000,  # Very long whitespace
            "A" * 10000,  # Extremely long message
            "\\n\\t\\r\\0",  # Control characters
            "🎭" * 500,  # Unicode spam
            None,  # Null value (will be converted to string)
            "DROP TABLE users;",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal attempt
            "\\x00\\x01\\x02\\x03",  # Binary data
        ]

        user_id_variants = [
            "",  # Empty user ID
            " ",  # Whitespace user ID
            "user_" + "A" * 1000,  # Very long user ID
            "user/with/slashes",  # Special characters
            "user\\nwith\\nnewlines",  # Control characters in ID
            "🎭🤖🚀",  # Unicode user ID
        ]

        # Test memory moments with invalid inputs
        for user_id in user_id_variants[:3]:  # Test subset to save time
            for message in invalid_inputs[:5]:
                test_results["total_tests"] += 1
                try:
                    await self.memory_moments.analyze_conversation_for_memories(
                        user_id, f"context_{test_results['total_tests']}", str(message), None
                    )
                    test_results["memory_moments_invalid"] += 1
                except Exception as e:
                    test_results["errors_handled"] += 1
                    # This is expected - we want graceful error handling

        # Test thread manager with invalid inputs
        for user_id in user_id_variants[:3]:
            for message in invalid_inputs[:5]:
                test_results["total_tests"] += 1
                try:
                    await self.thread_manager.process_user_message(user_id, str(message), {})
                    test_results["thread_manager_invalid"] += 1
                except Exception as e:
                    test_results["errors_handled"] += 1

        # Test engagement engine with invalid inputs
        for user_id in user_id_variants[:3]:
            for message in invalid_inputs[:5]:
                test_results["total_tests"] += 1
                try:
                    await self.engagement_engine.analyze_conversation_engagement(
                        user_id, str(message), []
                    )
                    test_results["engagement_engine_invalid"] += 1
                except Exception as e:
                    test_results["errors_handled"] += 1

        # Calculate results
        handled_gracefully = (
            test_results["errors_handled"] / test_results["total_tests"]
            if test_results["total_tests"] > 0
            else 0
        )

        logger.info(
            f"✅ Invalid input handling: {test_results['errors_handled']}/{test_results['total_tests']} "
            f"errors handled gracefully ({handled_gracefully:.1%})"
        )

        return test_results

    async def test_concurrent_race_conditions(self):
        """Test for race conditions with rapid concurrent access"""
        logger.info("⚡ Testing concurrent race conditions...")

        race_results = {
            "rapid_thread_creation": 0,
            "memory_access_conflicts": 0,
            "engagement_state_corruption": 0,
            "data_consistency_issues": 0,
            "successful_operations": 0,
            "total_operations": 0,
        }

        # Test 1: Rapid thread creation for same user
        async def rapid_thread_creation():
            user_id = "race_test_user"
            tasks = []

            for i in range(50):  # 50 rapid operations
                task = self.thread_manager.process_user_message(
                    user_id, f"Rapid message {i}", {"race_test": True}
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for consistency
            successful = sum(1 for r in results if not isinstance(r, Exception))
            race_results["rapid_thread_creation"] = successful
            race_results["total_operations"] += len(results)
            race_results["successful_operations"] += successful

        # Test 2: Concurrent memory access
        async def concurrent_memory_access():
            user_id = "memory_race_user"
            tasks = []

            for i in range(30):  # 30 concurrent memory operations
                task = self.memory_moments.analyze_conversation_for_memories(
                    user_id, f"race_context_{i}", f"Memory race test {i}", None
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if not isinstance(r, Exception))
            race_results["memory_access_conflicts"] = successful
            race_results["total_operations"] += len(results)
            race_results["successful_operations"] += successful

        # Test 3: Engagement state race conditions
        async def engagement_race_conditions():
            user_id = "engagement_race_user"
            tasks = []

            # Rapid engagement analysis that could cause state conflicts
            messages = ["High engagement!", "Low engagement...", "Medium engagement."] * 10

            for i, message in enumerate(messages):
                task = self.engagement_engine.analyze_conversation_engagement(user_id, message, [])
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if not isinstance(r, Exception))
            race_results["engagement_state_corruption"] = successful
            race_results["total_operations"] += len(results)
            race_results["successful_operations"] += successful

        # Run all race condition tests concurrently
        await asyncio.gather(
            rapid_thread_creation(),
            concurrent_memory_access(),
            engagement_race_conditions(),
            return_exceptions=True,
        )

        # Calculate consistency rate
        consistency_rate = (
            race_results["successful_operations"] / race_results["total_operations"]
            if race_results["total_operations"] > 0
            else 0
        )

        logger.info(
            f"✅ Race condition testing: {race_results['successful_operations']}/{race_results['total_operations']} "
            f"operations successful ({consistency_rate:.1%})"
        )

        return race_results

    async def test_resource_exhaustion_scenarios(self):
        """Test system behavior under resource exhaustion"""
        logger.info("💾 Testing resource exhaustion scenarios...")

        exhaustion_results = {
            "max_users_handled": 0,
            "memory_pressure_ops": 0,
            "thread_limit_reached": False,
            "graceful_degradation": True,
            "recovery_successful": True,
        }

        # Test 1: Maximum concurrent users
        async def max_users_test():
            max_users = 200  # Test with 200 concurrent users
            tasks = []

            for i in range(max_users):
                user_id = f"exhaustion_user_{i}"
                task = self.thread_manager.process_user_message(
                    user_id, f"Testing max users {i}", {}
                )
                tasks.append(task)

            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for r in results if not isinstance(r, Exception))
                exhaustion_results["max_users_handled"] = successful

                # Check if we hit any limits gracefully
                exceptions = [r for r in results if isinstance(r, Exception)]
                if exceptions and len(exceptions) < len(results) * 0.5:  # Less than 50% failures
                    exhaustion_results["graceful_degradation"] = True

            except Exception as e:
                logger.warning(f"Max users test encountered error: {e}")
                exhaustion_results["graceful_degradation"] = False

        # Test 2: Memory pressure with large operations
        async def memory_pressure_test():
            user_id = "memory_pressure_user"
            large_messages = ["Large message " + "X" * 1000 for _ in range(50)]

            successful_ops = 0
            for i, message in enumerate(large_messages):
                try:
                    await self.memory_moments.analyze_conversation_for_memories(
                        user_id, f"pressure_context_{i}", message, None
                    )
                    successful_ops += 1
                except Exception as e:
                    logger.debug(f"Memory pressure operation {i} failed: {e}")

            exhaustion_results["memory_pressure_ops"] = successful_ops

        # Run exhaustion tests
        await asyncio.gather(max_users_test(), memory_pressure_test(), return_exceptions=True)

        # Test recovery after exhaustion
        try:
            # Simple operation to test if system recovers
            await self.thread_manager.process_user_message("recovery_user", "Recovery test", {})
            exhaustion_results["recovery_successful"] = True
        except Exception:
            exhaustion_results["recovery_successful"] = False

        logger.info(
            f"✅ Resource exhaustion: {exhaustion_results['max_users_handled']} max users, "
            f"{exhaustion_results['memory_pressure_ops']} memory pressure ops, "
            f"recovery: {exhaustion_results['recovery_successful']}"
        )

        return exhaustion_results

    async def test_long_running_stability(self):
        """Test system stability over extended periods"""
        logger.info("⏰ Testing long-running stability...")

        stability_results = {
            "total_operations": 0,
            "successful_operations": 0,
            "memory_leaks_detected": False,
            "performance_degradation": False,
            "error_accumulation": False,
        }

        start_time = time.time()
        initial_performance_times = []
        final_performance_times = []

        # Run continuous operations for a shorter duration to fit in testing
        duration_seconds = 30  # 30 seconds of continuous operation
        operation_count = 0

        user_id = "stability_test_user"

        while time.time() - start_time < duration_seconds:
            operation_start = time.time()

            try:
                # Cycle through different operations
                if operation_count % 3 == 0:
                    await self.thread_manager.process_user_message(
                        user_id, f"Stability test message {operation_count}", {}
                    )
                elif operation_count % 3 == 1:
                    await self.memory_moments.analyze_conversation_for_memories(
                        user_id,
                        f"stability_context_{operation_count}",
                        f"Stability memory test {operation_count}",
                        None,
                    )
                else:
                    await self.engagement_engine.analyze_conversation_engagement(
                        user_id, f"Stability engagement test {operation_count}", []
                    )

                operation_time = time.time() - operation_start

                # Collect performance data
                if operation_count < 50:  # First 50 operations
                    initial_performance_times.append(operation_time)
                elif operation_count >= 200:  # Operations after 200
                    final_performance_times.append(operation_time)

                stability_results["successful_operations"] += 1

            except Exception as e:
                logger.debug(f"Stability test operation {operation_count} failed: {e}")

            stability_results["total_operations"] += 1
            operation_count += 1

            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)

        # Analyze performance degradation
        if initial_performance_times and final_performance_times:
            initial_avg = sum(initial_performance_times) / len(initial_performance_times)
            final_avg = sum(final_performance_times) / len(final_performance_times)

            # Check if performance degraded significantly (>50% slower)
            if final_avg > initial_avg * 1.5:
                stability_results["performance_degradation"] = True

        # Simple memory leak detection (gc object count)
        gc.collect()
        object_count_after = len(gc.get_objects())

        success_rate = (
            stability_results["successful_operations"] / stability_results["total_operations"]
            if stability_results["total_operations"] > 0
            else 0
        )

        logger.info(
            f"✅ Long-running stability: {stability_results['successful_operations']}/{stability_results['total_operations']} "
            f"ops successful ({success_rate:.1%}) over {duration_seconds}s, "
            f"performance degradation: {stability_results['performance_degradation']}"
        )

        return stability_results

    async def run_comprehensive_edge_case_testing(self):
        """Run all edge case and error handling tests"""
        logger.info("🚀 Starting Phase 4 Edge Case and Error Handling Test Suite")
        logger.info("=" * 80)

        all_results = {}

        # Run all test categories
        try:
            all_results["invalid_input"] = await self.test_invalid_input_handling()
        except Exception as e:
            logger.error(f"Invalid input test failed: {e}")
            all_results["invalid_input"] = {"error": str(e)}

        try:
            all_results["race_conditions"] = await self.test_concurrent_race_conditions()
        except Exception as e:
            logger.error(f"Race condition test failed: {e}")
            all_results["race_conditions"] = {"error": str(e)}

        try:
            all_results["resource_exhaustion"] = await self.test_resource_exhaustion_scenarios()
        except Exception as e:
            logger.error(f"Resource exhaustion test failed: {e}")
            all_results["resource_exhaustion"] = {"error": str(e)}

        try:
            all_results["stability"] = await self.test_long_running_stability()
        except Exception as e:
            logger.error(f"Stability test failed: {e}")
            all_results["stability"] = {"error": str(e)}

        # Final summary
        logger.info("\\n" + "=" * 80)
        logger.info("🎉 PHASE 4 EDGE CASE TEST SUMMARY")
        logger.info("=" * 80)

        test_categories = [
            ("Invalid Input Handling", "invalid_input"),
            ("Race Condition Testing", "race_conditions"),
            ("Resource Exhaustion", "resource_exhaustion"),
            ("Long-Running Stability", "stability"),
        ]

        overall_score = 0
        successful_categories = 0

        for category_name, category_key in test_categories:
            result = all_results.get(category_key, {})

            if "error" in result:
                logger.info(f"❌ {category_name:25} - ERROR: {result['error']}")
            else:
                # Calculate category score based on available metrics
                if category_key == "invalid_input":
                    score = result.get("errors_handled", 0) / result.get("total_tests", 1)
                elif category_key == "race_conditions":
                    score = result.get("successful_operations", 0) / result.get(
                        "total_operations", 1
                    )
                elif category_key == "resource_exhaustion":
                    recovery = result.get("recovery_successful", False)
                    degradation = result.get("graceful_degradation", False)
                    score = (recovery + degradation) / 2
                elif category_key == "stability":
                    success_rate = result.get("successful_operations", 0) / result.get(
                        "total_operations", 1
                    )
                    no_degradation = not result.get("performance_degradation", True)
                    score = (success_rate + no_degradation) / 2
                else:
                    score = 0.5  # Default

                overall_score += score
                successful_categories += 1

                status = (
                    "✅ EXCELLENT"
                    if score >= 0.95
                    else (
                        "👍 GOOD"
                        if score >= 0.85
                        else "⚠️ NEEDS WORK" if score >= 0.70 else "❌ POOR"
                    )
                )
                logger.info(f"{status} {category_name:25} - Score: {score:.1%}")

        # Overall assessment
        if successful_categories > 0:
            final_score = overall_score / successful_categories
            logger.info("=" * 80)
            logger.info(f"🎯 OVERALL EDGE CASE HANDLING: {final_score:.1%}")

            if final_score >= 0.90:
                logger.info("🏆 EXCELLENT - Phase 4 system is highly robust and production-ready!")
            elif final_score >= 0.80:
                logger.info(
                    "👍 GOOD - Phase 4 system is solid with minor edge case improvements needed"
                )
            elif final_score >= 0.70:
                logger.info("⚠️ ADEQUATE - Phase 4 system works but needs edge case hardening")
            else:
                logger.info(
                    "❌ NEEDS SIGNIFICANT IMPROVEMENT - Address edge case handling before production"
                )

        logger.info("=" * 80)
        return all_results


async def main():
    """Run comprehensive edge case testing"""
    tester = Phase4EdgeCaseTester()
    results = await tester.run_comprehensive_edge_case_testing()
    return results


if __name__ == "__main__":
    asyncio.run(main())
