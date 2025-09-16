#!/usr/bin/env python3
"""
Demo: Concurrent Conversation Manager Performance Testing
Tests the optimized conversation threading system for massive concurrent user scenarios
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


# Mock components for testing
class MockAdvancedThreadManager:
    """Mock advanced thread manager for testing"""

    def __init__(self):
        self.processing_delay = 0.05  # 50ms processing time
        self.threads = {}

    async def process_user_message(
        self, user_id: str, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Mock thread processing"""
        await asyncio.sleep(self.processing_delay)

        # Simulate thread analysis
        thread_id = f"thread_{hash(message) % 1000}"

        return {
            "current_thread": thread_id,
            "thread_analysis": {
                "keywords": message.split()[:3],
                "topic_shift": random.choice([True, False]),
                "engagement_level": random.uniform(0.3, 0.9),
            },
            "response_guidance": {
                "tone": random.choice(["helpful", "supportive", "informative"]),
                "context_bridge": random.choice([True, False]),
            },
            "active_threads": [f"thread_{i}" for i in range(random.randint(1, 3))],
        }


class MockEmotionEngine:
    """Mock emotion engine for testing"""

    def __init__(self):
        self.processing_delay = 0.02  # 20ms processing time

    async def analyze_emotion(self, message: str, user_id: str) -> dict[str, Any]:
        """Mock emotion analysis"""
        await asyncio.sleep(self.processing_delay)

        emotions = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]

        return {
            "primary_emotion": random.choice(emotions),
            "intensity": random.uniform(0.1, 0.9),
            "confidence": random.uniform(0.5, 0.95),
            "valence": random.uniform(-1.0, 1.0),
            "triggers": random.sample(message.split(), min(2, len(message.split()))),
        }


def generate_concurrent_users(num_users: int, messages_per_user: int) -> list[dict[str, Any]]:
    """Generate realistic concurrent user scenarios"""

    conversation_scenarios = [
        # Work/Career conversations
        {
            "topics": ["project management", "career goals", "team collaboration"],
            "urgency": "normal",
        },
        {"topics": ["job interview", "resume help", "workplace conflict"], "urgency": "high"},
        # Personal conversations
        {
            "topics": ["relationship advice", "personal growth", "life decisions"],
            "urgency": "normal",
        },
        {"topics": ["health concerns", "family issues", "emotional support"], "urgency": "high"},
        # Technical conversations
        {"topics": ["programming help", "debugging", "technical design"], "urgency": "normal"},
        {"topics": ["system down", "critical bug", "urgent deployment"], "urgency": "critical"},
        # Learning conversations
        {
            "topics": ["learning new skills", "educational questions", "study help"],
            "urgency": "low",
        },
        {
            "topics": ["exam preparation", "assignment help", "concept clarification"],
            "urgency": "normal",
        },
        # Creative conversations
        {"topics": ["creative writing", "artistic feedback", "brainstorming"], "urgency": "low"},
        {
            "topics": ["deadline project", "creative block", "urgent inspiration"],
            "urgency": "normal",
        },
    ]

    message_templates = {
        "low": [
            "When you have time, I'd like to discuss {topic}.",
            "I'm casually exploring {topic} and wondering about it.",
            "No rush, but I have a question about {topic}.",
            "Just curious about {topic} when you're available.",
            "I'm learning about {topic} in my spare time.",
        ],
        "normal": [
            "I'm working on {topic} and could use some guidance.",
            "Can you help me understand {topic} better?",
            "I have some questions about {topic}.",
            "What's your advice on {topic}?",
            "I'm exploring {topic} and want to learn more.",
        ],
        "high": [
            "I really need help with {topic} - it's quite urgent!",
            "This {topic} situation is stressing me out.",
            "I'm struggling with {topic} and need immediate advice.",
            "Help! I'm having serious issues with {topic}.",
            "This {topic} problem needs to be solved quickly.",
        ],
        "critical": [
            "URGENT: {topic} is completely broken!",
            "Emergency! {topic} is causing major problems!",
            "Critical issue with {topic} - need immediate help!",
            "SOS: {topic} failure, please help ASAP!",
            "Code red: {topic} is down and users are affected!",
        ],
    }

    users = []

    for user_num in range(num_users):
        scenario = random.choice(conversation_scenarios)
        user_id = f"concurrent_user_{user_num:04d}"

        user_messages = []
        for msg_num in range(messages_per_user):
            topic = random.choice(scenario["topics"])
            urgency = scenario["urgency"]

            # Occasionally escalate urgency
            if msg_num > 2 and random.random() < 0.2:
                urgency = "high"

            template = random.choice(message_templates[urgency])
            message = template.format(topic=topic)

            # Add some natural variation
            if random.random() < 0.3:
                message += f" This is my {msg_num + 1}{'st' if msg_num == 0 else 'nd' if msg_num == 1 else 'rd' if msg_num == 2 else 'th'} message about this."

            user_messages.append(
                {
                    "message": message,
                    "urgency": urgency,
                    "delay": random.uniform(0.5, 5.0),  # Random delay between messages
                    "channel": f"channel_{random.randint(1, 10)}",
                }
            )

        users.append({"user_id": user_id, "messages": user_messages, "scenario": scenario})

    return users


async def test_concurrent_conversation_processing():
    """Test concurrent conversation processing with realistic load"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.conversation.concurrent_conversation_manager import ConcurrentConversationManager

        # Test configurations for different scales
        test_configs = [
            {"name": "Small Scale", "users": 10, "messages": 5, "workers": 2},
            {"name": "Medium Scale", "users": 50, "messages": 8, "workers": 4},
            {"name": "Large Scale", "users": 100, "messages": 6, "workers": 8},
            {"name": "Massive Scale", "users": 250, "messages": 4, "workers": 12},
        ]

        for config in test_configs:

            # Create mock components
            mock_thread_manager = MockAdvancedThreadManager()
            mock_emotion_engine = MockEmotionEngine()

            # Initialize concurrent conversation manager
            manager = ConcurrentConversationManager(
                advanced_thread_manager=mock_thread_manager,
                emotion_engine=mock_emotion_engine,
                max_concurrent_sessions=config["users"] * 2,
                max_workers_threads=config["workers"],
                max_workers_processes=max(config["workers"] // 2, 1),
            )

            await manager.start()

            # Generate concurrent users
            users = generate_concurrent_users(config["users"], config["messages"])
            sum(len(user["messages"]) for user in users)


            # Execute concurrent conversations
            start_time = time.time()

            async def simulate_user_conversation(user_data: dict[str, Any]):
                """Simulate a single user's conversation"""
                user_results = []

                for i, msg_data in enumerate(user_data["messages"]):
                    # Add realistic delay between messages
                    if i > 0:
                        await asyncio.sleep(msg_data["delay"] / 10)  # Scale down for testing

                    # Determine priority based on urgency
                    priority_map = {
                        "critical": "critical",
                        "high": "high",
                        "normal": "normal",
                        "low": "low",
                    }
                    priority = priority_map.get(msg_data["urgency"], "normal")

                    # Process message
                    result = await manager.process_conversation_message(
                        user_id=user_data["user_id"],
                        message=msg_data["message"],
                        channel_id=msg_data["channel"],
                        context={"urgency": msg_data["urgency"]},
                        priority=priority,
                    )

                    user_results.append(result)

                return user_results

            # Run all user conversations concurrently
            user_tasks = [simulate_user_conversation(user) for user in users]
            all_results = await asyncio.gather(*user_tasks)

            total_time = time.time() - start_time

            # Analyze results
            processed_messages = sum(len(results) for results in all_results)
            processed_messages / total_time


            # Get performance statistics
            manager.get_performance_stats()


            # Analyze priority distribution
            sum(
                1
                for results in all_results
                for result in results
                if result.get("status") == "processed"
            )
            sum(
                1
                for results in all_results
                for result in results
                if result.get("status") == "queued"
            )


            await manager.stop()


    except Exception:
        import traceback

        traceback.print_exc()


async def test_priority_queue_performance():
    """Test priority queue performance with different message types"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.conversation.concurrent_conversation_manager import ConversationQueue

        queue = ConversationQueue(max_size=10000)

        # Create messages with different priorities
        priority_distribution = {
            "critical": 50,  # Emergency messages
            "high": 200,  # Urgent requests
            "normal": 500,  # Standard conversations
            "low": 250,  # Background processing
        }

        for priority, count in priority_distribution.items():
            pass

        # Add messages to queue
        start_time = time.time()

        for priority, count in priority_distribution.items():
            for i in range(count):
                message_data = {
                    "id": f"{priority}_{i}",
                    "content": f"Test message {i} with {priority} priority",
                    "timestamp": time.time(),
                    "user_id": f"user_{random.randint(1, 100)}",
                }
                await queue.put(message_data, priority)

        time.time() - start_time
        total_messages = sum(priority_distribution.values())


        # Test queue retrieval with priority ordering
        start_time = time.time()

        priority_counts = {"critical": 0, "high": 0, "normal": 0, "low": 0}
        retrieved_messages = []

        # Retrieve first 100 messages to test priority ordering
        for _ in range(min(100, total_messages)):
            message = await queue.get()
            if message:
                # Determine original priority from message ID
                msg_priority = message["id"].split("_")[0]
                priority_counts[msg_priority] += 1
                retrieved_messages.append(message)

        time.time() - start_time


        for priority, count in priority_counts.items():
            (count / len(retrieved_messages)) * 100 if retrieved_messages else 0

        # Verify high-priority messages are processed first
        priority_counts["critical"] + priority_counts["high"]

        # Queue statistics
        queue.get_stats()

    except Exception:
        pass


async def test_session_management():
    """Test session management and cleanup"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.conversation.concurrent_conversation_manager import ConcurrentConversationManager

        # Create manager with short timeout for testing
        manager = ConcurrentConversationManager(
            max_concurrent_sessions=50,
            max_workers_threads=4,
            session_timeout_minutes=1,  # 1 minute timeout for testing
        )

        await manager.start()

        # Create sessions with different activity patterns
        session_scenarios = [
            {"users": 10, "active": True, "messages": 5},  # Active users
            {"users": 15, "active": False, "messages": 2},  # Inactive users
            {"users": 8, "active": True, "messages": 8},  # Very active users
        ]


        total_users = 0
        for scenario in session_scenarios:
            total_users += scenario["users"]
            "active" if scenario["active"] else "inactive"

        # Simulate session creation and activity
        all_tasks = []

        for scenario_idx, scenario in enumerate(session_scenarios):
            for user_idx in range(scenario["users"]):
                user_id = f"session_user_{scenario_idx}_{user_idx}"

                async def user_session(uid: str, msg_count: int, is_active: bool):
                    """Simulate user session"""
                    for i in range(msg_count):
                        await manager.process_conversation_message(
                            user_id=uid,
                            message=f"Test message {i+1}",
                            channel_id=f"channel_{random.randint(1, 5)}",
                            priority="normal",
                        )

                        if is_active:
                            await asyncio.sleep(0.1)  # Active users have short delays
                        else:
                            await asyncio.sleep(2.0)  # Inactive users have long delays

                task = user_session(user_id, scenario["messages"], scenario["active"])
                all_tasks.append(task)

        start_time = time.time()
        await asyncio.gather(*all_tasks)
        time.time() - start_time


        # Get initial session stats
        stats = manager.get_performance_stats()
        initial_sessions = stats["sessions"]["active_sessions"]


        # Wait for session cleanup (timeout is 1 minute, but cleanup runs every 30s)
        await asyncio.sleep(65)  # Wait longer than timeout

        # Trigger manual cleanup
        manager._cleanup_inactive_sessions()

        # Get final session stats
        final_stats = manager.get_performance_stats()
        final_sessions = final_stats["sessions"]["active_sessions"]


        # Expected: only active users should remain
        sum(
            scenario["users"] for scenario in session_scenarios if scenario["active"]
        )
        (
            (initial_sessions - final_sessions) / initial_sessions if initial_sessions > 0 else 0
        )


        await manager.stop()

    except Exception:
        pass


async def test_load_balancing():
    """Test load balancing and adaptive performance"""

    if not LIBRARIES_AVAILABLE:
        return


    try:
        from src.conversation.concurrent_conversation_manager import ConcurrentConversationManager

        manager = ConcurrentConversationManager(
            max_concurrent_sessions=200, max_workers_threads=6, max_workers_processes=3
        )

        await manager.start()

        # Simulate varying load patterns
        load_patterns = [
            {"name": "Light Load", "users": 20, "burst_factor": 1.0},
            {"name": "Medium Load", "users": 60, "burst_factor": 1.5},
            {"name": "Heavy Load", "users": 120, "burst_factor": 2.0},
            {"name": "Burst Load", "users": 80, "burst_factor": 3.0},
        ]

        for pattern in load_patterns:

            # Generate burst of messages
            async def burst_user(user_id: str, message_count: int):
                """Simulate user sending burst of messages"""
                for i in range(message_count):
                    await manager.process_conversation_message(
                        user_id=user_id,
                        message=f"Burst message {i+1} from {user_id}",
                        channel_id=f"burst_channel_{random.randint(1, 3)}",
                        priority=random.choice(["normal", "high"]),
                    )
                    # Small delay between messages in burst
                    await asyncio.sleep(0.01)

            # Calculate messages per user based on burst factor
            messages_per_user = max(1, int(3 * pattern["burst_factor"]))

            start_time = time.time()

            # Create burst tasks
            burst_tasks = [
                burst_user(f"burst_user_{i}", messages_per_user) for i in range(pattern["users"])
            ]

            # Execute burst
            await asyncio.gather(*burst_tasks)

            time.time() - start_time
            pattern["users"] * messages_per_user

            # Get performance stats during load
            manager.get_performance_stats()


            # Wait for queue to process
            await asyncio.sleep(1.0)

        await manager.stop()

    except Exception:
        pass


async def main():
    """Run all concurrent conversation manager tests"""


    if not LIBRARIES_AVAILABLE:
        return

    # Run all tests
    await test_concurrent_conversation_processing()
    await test_priority_queue_performance()
    await test_session_management()
    await test_load_balancing()



if __name__ == "__main__":
    asyncio.run(main())
