"""
Production Phase 4 Concurrency Demonstration

This script demonstrates the optimized Phase 4 system handling multiple
concurrent users with parallel processing, batch operations, and proper
resource management.
"""

import asyncio
import logging
import time
import random
from typing import List, Dict, Any
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import our optimized engine
try:
    from src.intelligence.production_phase4_engine import create_production_phase4_engine

    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    logger.warning("Production engine not available - using simulation")


class ConcurrencyDemo:
    """Demonstrate concurrent user processing with performance monitoring"""

    def __init__(self, num_users: int = 50, messages_per_user: int = 5):
        self.num_users = num_users
        self.messages_per_user = messages_per_user
        self.engine = None
        self.results = []

    async def setup(self):
        """Initialize the optimized engine"""
        if ENGINE_AVAILABLE:
            self.engine = create_production_phase4_engine(
                max_workers=16,  # Optimize for demo machine
                batch_size=32,
                enable_multiprocessing=True,
            )
            await self.engine.start_engine()
            logger.info("✅ Production Phase 4 engine started")
        else:
            logger.info("⚠️ Using simulation mode")

    async def cleanup(self):
        """Clean up resources"""
        if self.engine:
            await self.engine.stop_engine()
            logger.info("✅ Engine stopped gracefully")

    def generate_realistic_conversations(self) -> List[List[str]]:
        """Generate realistic conversation patterns"""
        conversation_templates = [
            # Career development conversation
            [
                "I've been thinking about changing my career path",
                "The tech industry seems really interesting",
                "But I'm worried about the learning curve",
                "Do you think it's worth the risk?",
                "I guess I need to start somewhere",
            ],
            # Personal reflection conversation
            [
                "I had a really productive day today",
                "Finished that project I've been working on",
                "It feels good to accomplish something meaningful",
                "I should celebrate these small wins more",
                "Tomorrow I want to tackle that next challenge",
            ],
            # Problem-solving conversation
            [
                "I'm dealing with a difficult situation at work",
                "My team lead and I have different approaches",
                "It's creating tension in our meetings",
                "I need to find a way to address this professionally",
                "Maybe I should schedule a one-on-one conversation",
            ],
            # Learning and growth
            [
                "Started learning Python last week",
                "The syntax is much cleaner than I expected",
                "Working through some data analysis tutorials",
                "It's connecting to my career change goals",
                "I'm excited about the possibilities",
            ],
            # Emotional support
            [
                "Feeling a bit overwhelmed lately",
                "There's a lot going on in my personal life",
                "Work has been demanding too",
                "I know I need to take better care of myself",
                "Thanks for listening to me vent",
            ],
        ]

        conversations = []
        for i in range(self.num_users):
            # Pick random conversation template
            template = random.choice(conversation_templates)
            # Add some variation
            conversation = []
            for j, message in enumerate(template[: self.messages_per_user]):
                if j < len(template):
                    conversation.append(f"{message}")
                else:
                    conversation.append(f"Message {j+1} from user {i+1}")
            conversations.append(conversation)

        return conversations

    async def simulate_concurrent_users(self):
        """Simulate multiple users having conversations simultaneously"""
        logger.info(
            f"🚀 Starting concurrency demo: {self.num_users} users, {self.messages_per_user} messages each"
        )

        conversations = self.generate_realistic_conversations()
        start_time = time.time()

        # Create tasks for all users
        user_tasks = []
        for user_id, conversation in enumerate(conversations):
            task = asyncio.create_task(
                self.process_user_conversation(f"demo_user_{user_id}", conversation)
            )
            user_tasks.append(task)

        # Process all users concurrently
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        successful_users = len([r for r in user_results if not isinstance(r, Exception)])
        failed_users = len(user_results) - successful_users
        total_messages = successful_users * self.messages_per_user

        logger.info(f"📊 CONCURRENCY DEMO RESULTS:")
        logger.info(f"   Total time: {total_time:.2f} seconds")
        logger.info(f"   Successful users: {successful_users}/{self.num_users}")
        logger.info(f"   Failed users: {failed_users}")
        logger.info(f"   Total messages processed: {total_messages}")
        logger.info(f"   Messages per second: {total_messages/total_time:.1f}")
        logger.info(f"   Average time per user: {total_time/max(successful_users, 1):.2f}s")

        # Performance analysis
        if self.engine:
            stats = self.engine.performance_stats
            logger.info(f"📈 ENGINE PERFORMANCE:")
            logger.info(f"   Concurrent users peak: {stats['concurrent_users']}")
            logger.info(f"   Average response time: {stats['avg_response_time_ms']:.1f}ms")
            logger.info(f"   Batch efficiency: {stats['batch_efficiency']*100:.1f}%")

        return {
            "total_time": total_time,
            "successful_users": successful_users,
            "failed_users": failed_users,
            "messages_per_second": total_messages / total_time,
            "user_results": user_results,
        }

    async def process_user_conversation(
        self, user_id: str, conversation: List[str]
    ) -> Dict[str, Any]:
        """Process a full conversation for one user"""
        user_start = time.time()
        message_results = []

        try:
            for i, message in enumerate(conversation):
                if self.engine:
                    # Use the optimized engine
                    result = await self.engine.process_user_interaction_optimized(
                        user_id=user_id,
                        message=message,
                        context={"message_index": i, "conversation_length": len(conversation)},
                    )
                else:
                    # Simulate processing
                    await asyncio.sleep(
                        0.01 + random.uniform(0, 0.02)
                    )  # Simulate variable processing time
                    result = {
                        "user_id": user_id,
                        "message_index": i,
                        "processing_time_ms": random.uniform(10, 50),
                        "simulated": True,
                    }

                message_results.append(result)

                # Add small delay between messages to simulate realistic timing
                await asyncio.sleep(0.1)

            user_time = time.time() - user_start

            return {
                "user_id": user_id,
                "total_time": user_time,
                "messages_processed": len(message_results),
                "results": message_results,
                "success": True,
            }

        except Exception as e:
            logger.error(f"❌ User {user_id} conversation failed: {e}")
            return {"user_id": user_id, "error": str(e), "success": False}

    async def run_stress_test(self):
        """Run increasingly demanding stress tests"""
        test_scenarios = [
            (10, 3),  # 10 users, 3 messages each - baseline
            (25, 4),  # 25 users, 4 messages each - moderate load
            (50, 5),  # 50 users, 5 messages each - high load
            (100, 3),  # 100 users, 3 messages each - stress test
        ]

        logger.info("🔥 STARTING STRESS TEST SUITE")

        stress_results = []

        for users, messages in test_scenarios:
            logger.info(f"\n📈 STRESS TEST: {users} users, {messages} messages each")

            # Update test parameters
            self.num_users = users
            self.messages_per_user = messages

            # Run the test
            result = await self.simulate_concurrent_users()
            result["test_config"] = {"users": users, "messages": messages}
            stress_results.append(result)

            # Brief pause between tests
            await asyncio.sleep(2)

        # Analyze stress test results
        logger.info("\n🏆 STRESS TEST SUMMARY:")
        for i, result in enumerate(stress_results):
            config = result["test_config"]
            logger.info(
                f"Test {i+1}: {config['users']} users × {config['messages']} msgs = "
                f"{result['messages_per_second']:.1f} msg/s, "
                f"{result['successful_users']}/{config['users']} success"
            )

        return stress_results


async def main():
    """Run the concurrency demonstration"""
    logger.info("🚀 WhisperEngine Production Concurrency Demonstration")

    # Create demo with moderate load
    demo = ConcurrencyDemo(num_users=30, messages_per_user=4)

    try:
        # Setup
        await demo.setup()

        # Run basic concurrency demo
        logger.info("\n" + "=" * 60)
        logger.info("BASIC CONCURRENCY DEMONSTRATION")
        logger.info("=" * 60)
        await demo.simulate_concurrent_users()

        # Run stress tests
        logger.info("\n" + "=" * 60)
        logger.info("STRESS TEST SUITE")
        logger.info("=" * 60)
        await demo.run_stress_test()

        logger.info("\n✅ Concurrency demonstration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")

    finally:
        # Cleanup
        await demo.cleanup()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
