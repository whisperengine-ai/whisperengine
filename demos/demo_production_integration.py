#!/usr/bin/env python3
"""
Demo: Production System Integration Testing
Tests the complete integration of all optimized components with WhisperEngine
"""

import asyncio
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_production_system_integration():
    """Test production system integration with all components"""

    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator

        # Initialize production system
        integrator = ProductionSystemIntegrator()

        start_time = time.time()
        success = await integrator.initialize_production_components()
        time.time() - start_time

        if success:
            pass
        else:
            pass

        # Get initial system metrics
        metrics = integrator.get_production_metrics()
        for _component, available in metrics["components_available"].items():
            pass

        # Test message processing pipeline

        test_scenarios = [
            {
                "name": "Standard User Message",
                "user_id": "user_001",
                "message": "Hello! I need help with my Python project. Can you assist me?",
                "context": {"channel_id": "general", "urgency": "normal", "priority": "normal"},
            },
            {
                "name": "High Priority Support",
                "user_id": "user_002",
                "message": "URGENT: My application is crashing and users are affected!",
                "context": {"channel_id": "support", "urgency": "high", "priority": "high"},
            },
            {
                "name": "Complex Technical Question",
                "user_id": "user_003",
                "message": "I'm implementing a machine learning pipeline and encountering memory issues with large datasets. What optimization strategies would you recommend?",
                "context": {
                    "channel_id": "tech-help",
                    "urgency": "normal",
                    "priority": "normal",
                    "enable_phase4": True,
                },
            },
            {
                "name": "Emotional Support Request",
                "user_id": "user_004",
                "message": "I'm feeling really overwhelmed with work lately and could use some guidance on managing stress.",
                "context": {"channel_id": "wellness", "urgency": "normal", "priority": "normal"},
            },
        ]

        for scenario in test_scenarios:

            start_time = time.time()
            result = await integrator.process_message_production(
                user_id=scenario["user_id"],
                message=scenario["message"],
                context=scenario["context"],
                priority=scenario["context"]["priority"],
            )
            time.time() - start_time

            # Show specific component results
            if "emotion_analysis" in result:
                result["emotion_analysis"].get("primary_emotion", "unknown")
                result["emotion_analysis"].get("confidence", 0)

            if "conversation_result" in result:
                result["conversation_result"].get("status", "unknown")

        # Test concurrent processing capabilities

        concurrent_users = 25
        messages_per_user = 3

        async def simulate_user_load(user_id: str, message_count: int):
            """Simulate concurrent user sending multiple messages"""
            results = []
            for i in range(message_count):
                message = f"Message {i+1} from {user_id}: Testing concurrent processing capabilities with message {i+1}"
                context = {
                    "channel_id": f"channel_{i % 5}",
                    "urgency": "normal",
                    "priority": "normal",
                }

                result = await integrator.process_message_production(
                    user_id=user_id, message=message, context=context
                )
                results.append(result)

                # Small delay between messages
                await asyncio.sleep(0.01)

            return results

        start_time = time.time()

        # Create concurrent user tasks
        user_tasks = [
            simulate_user_load(f"concurrent_user_{i:03d}", messages_per_user)
            for i in range(concurrent_users)
        ]

        # Execute all tasks concurrently
        all_results = await asyncio.gather(*user_tasks)

        total_time = time.time() - start_time
        total_messages = concurrent_users * messages_per_user
        total_messages / total_time

        # Analyze results
        successful_messages = sum(
            1
            for user_results in all_results
            for result in user_results
            if result.get("status") == "success"
        )

        (successful_messages / total_messages) * 100

        # Get final system metrics
        final_metrics = integrator.get_production_metrics()

        # Display component-specific metrics
        for component_name, available in final_metrics["components_available"].items():
            if available and f"{component_name}_metrics" in final_metrics:
                component_metrics = final_metrics[f"{component_name}_metrics"]

                # Display relevant metrics based on component
                if "throughput" in component_metrics:
                    pass
                if "avg_response_time_ms" in component_metrics:
                    pass
                if "cache_hit_rate" in component_metrics:
                    pass
                if "active_sessions" in component_metrics:
                    pass

        # Test graceful shutdown
        shutdown_start = time.time()
        await integrator.shutdown_production_system()
        time.time() - shutdown_start

    except Exception:
        import traceback

        traceback.print_exc()


async def test_production_adapter():
    """Test the WhisperEngine production adapter"""

    try:
        from src.integration.production_system_integration import WhisperEngineProductionAdapter

        # Initialize production adapter
        adapter = WhisperEngineProductionAdapter()

        success = await adapter.initialize_production_mode()

        if success:
            pass
        else:
            pass

        # Get system status
        adapter.get_system_status()

        # Test message processing through adapter

        test_messages = [
            {
                "user_id": "adapter_user_001",
                "message": "Testing adapter integration with optimized components",
                "context": {"source": "discord", "channel_id": "test-channel"},
            },
            {
                "user_id": "adapter_user_002",
                "message": "How does the production adapter handle message routing?",
                "context": {"source": "desktop", "priority": "high"},
            },
        ]

        for test_msg in test_messages:

            start_time = time.time()
            await adapter.process_user_message(
                user_id=test_msg["user_id"],
                message=test_msg["message"],
                context=test_msg["context"],
            )
            time.time() - start_time

        # Test shutdown
        await adapter.shutdown()

    except Exception:
        import traceback

        traceback.print_exc()


async def test_component_compatibility():
    """Test compatibility and fallback behavior"""

    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator

        # Test with limited components available
        integrator = ProductionSystemIntegrator()

        # Override config to simulate different scenarios
        test_configs = [
            {
                "name": "Minimal Configuration",
                "config": {
                    "production_engine": {
                        "max_workers_threads": 2,
                        "max_workers_processes": 1,
                        "batch_size": 16,
                    },
                    "faiss_memory": {"index_type": "Flat", "num_clusters": 64},
                    "vectorized_emotion": {"cache_size": 1000, "batch_size": 100},
                    "memory_batcher": {"batch_size": 25, "max_batch_wait_ms": 50},
                    "conversation_manager": {
                        "max_concurrent_sessions": 100,
                        "max_workers_threads": 4,
                        "max_workers_processes": 2,
                    },
                },
            },
            {
                "name": "High Performance Configuration",
                "config": {
                    "production_engine": {
                        "max_workers_threads": 16,
                        "max_workers_processes": 8,
                        "batch_size": 64,
                    },
                    "faiss_memory": {"index_type": "IVF", "num_clusters": 512},
                    "vectorized_emotion": {"cache_size": 50000, "batch_size": 1000},
                    "memory_batcher": {"batch_size": 100, "max_batch_wait_ms": 200},
                    "conversation_manager": {
                        "max_concurrent_sessions": 5000,
                        "max_workers_threads": 24,
                        "max_workers_processes": 12,
                    },
                },
            },
        ]

        for test_config in test_configs:

            integrator.config = test_config["config"]

            start_time = time.time()
            success = await integrator.initialize_production_components()
            time.time() - start_time

            # Get metrics
            metrics = integrator.get_production_metrics()
            sum(1 for available in metrics["components_available"].values() if available)
            len(metrics["components_available"])

            # Test basic functionality
            if success:
                try:
                    await integrator.process_message_production(
                        user_id="compatibility_test_user",
                        message="Testing compatibility with configuration",
                        context={"test": True},
                    )
                except Exception:
                    pass

            await integrator.shutdown_production_system()

    except Exception:
        import traceback

        traceback.print_exc()


async def main():
    """Run all production integration tests"""

    # Run all integration tests
    await test_production_system_integration()
    await test_production_adapter()
    await test_component_compatibility()


if __name__ == "__main__":
    asyncio.run(main())
