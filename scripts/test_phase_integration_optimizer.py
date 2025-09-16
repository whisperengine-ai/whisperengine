#!/usr/bin/env python3
"""
Test script for Phase Integration Optimizer

This script tests the optimization capabilities of the phase integration system,
demonstrating performance improvements and data consistency enhancements.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_phase_integration_optimizer():
    """Test the phase integration optimizer functionality"""


    try:
        from src.intelligence.phase_integration_optimizer import (
            OptimizationLevel,
            PhaseExecutionStrategy,
            PhaseIntegrationOptimizer,
            PhaseResult,
        )


        # Test 1: Initialize optimizer with different configurations

        # Balanced configuration
        optimizer_balanced = PhaseIntegrationOptimizer(
            optimization_level=OptimizationLevel.BALANCED,
            execution_strategy=PhaseExecutionStrategy.ADAPTIVE,
            enable_caching=True,
        )

        # Aggressive configuration
        PhaseIntegrationOptimizer(
            optimization_level=OptimizationLevel.AGGRESSIVE,
            execution_strategy=PhaseExecutionStrategy.PARALLEL,
            enable_caching=True,
            cache_ttl_seconds=600,
        )

        # Minimal configuration
        PhaseIntegrationOptimizer(
            optimization_level=OptimizationLevel.MINIMAL,
            execution_strategy=PhaseExecutionStrategy.SEQUENTIAL,
            enable_caching=False,
        )

        # Test 2: Test phase dependency mapping
        test_phases = ["phase2", "phase3", "memory_optimization"]

        optimizer_balanced._group_phases_by_dependencies(test_phases)

        optimizer_balanced._sort_phases_by_dependencies(test_phases)

        # Test 3: Test phase result standardization

        # Create sample phase results
        {
            "phase2": PhaseResult(
                phase_name="phase2",
                success=True,
                data={"emotion": "happy", "confidence": 0.8},
                processing_time=0.15,
            ),
            "phase3": PhaseResult(
                phase_name="phase3",
                success=True,
                data={"core_memories": ["test memory"], "insights": []},
                processing_time=0.25,
            ),
        }


        # Test 4: Test performance reporting

        # Simulate some performance data
        optimizer_balanced.performance_stats["total_requests"] = 100
        optimizer_balanced.performance_stats["cache_hits"] = 25
        optimizer_balanced.performance_stats["parallel_executions"] = 60
        optimizer_balanced.performance_stats["phase_timings"] = {
            "phase2": [0.1, 0.15, 0.12, 0.18, 0.14],
            "phase3": [0.3, 0.25, 0.35, 0.28, 0.32],
        }

        optimizer_balanced.get_performance_report()


        # Test 5: Test cache functionality

        # Test cache key generation
        import hashlib

        user_id = "test_user_123"
        message = "Hello, how are you?"
        cache_key = hashlib.md5(f"{user_id}:{message}".encode()).hexdigest()


        # Test cache storage and retrieval
        test_result = PhaseResult(
            phase_name="test_phase", success=True, data={"test": "data"}, processing_time=0.1
        )

        # Simulate caching
        optimizer_balanced.result_cache[cache_key] = {
            "timestamp": time.time(),
            "results": {"test_phase": test_result},
        }




        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def test_async_integration():
    """Test the async integration capabilities"""


    try:
        from src.intelligence.phase_integration_optimizer import (
            OptimizationLevel,
            PhaseExecutionStrategy,
            PhaseIntegrationOptimizer,
        )

        # Create optimizer for async testing
        optimizer = PhaseIntegrationOptimizer(
            optimization_level=OptimizationLevel.BALANCED,
            execution_strategy=PhaseExecutionStrategy.ADAPTIVE,
            enable_caching=True,
        )

        # Test async context creation
        user_id = "async_test_user"
        message = "This is a test message for async processing"
        conversation_context = [
            {"role": "user", "content": "Previous message 1"},
            {"role": "assistant", "content": "Previous response 1"},
        ]

        start_time = time.time()

        # This will run without actual phase components (graceful degradation)
        await optimizer.process_integrated_phases(
            user_id=user_id, message=message, conversation_context=conversation_context
        )

        time.time() - start_time


        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


def demonstrate_optimization_benefits():
    """Demonstrate the benefits of the optimization system"""


    # Simulate different scenarios
    scenarios = [
        {
            "name": "Simple Chat Message",
            "message": "Hello!",
            "expected_phases": ["phase2"],
            "optimization_note": "Minimal processing for simple messages",
        },
        {
            "name": "Complex Question",
            "message": "Can you help me understand machine learning algorithms and remember what we discussed about neural networks before?",
            "expected_phases": ["phase2", "phase3", "memory_optimization"],
            "optimization_note": "Full processing for complex queries",
        },
        {
            "name": "Emotional Support",
            "message": "I'm feeling really stressed about work today",
            "expected_phases": ["phase2", "memory_optimization"],
            "optimization_note": "Emotional intelligence prioritized",
        },
    ]

    for _i, _scenario in enumerate(scenarios, 1):
        pass




def main():
    """Main test function"""


    # Run synchronous tests
    sync_success = test_phase_integration_optimizer()

    if sync_success:
        # Run async tests
        async_success = asyncio.run(test_async_integration())

        if async_success:
            # Demonstrate benefits
            demonstrate_optimization_benefits()


            return True

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
