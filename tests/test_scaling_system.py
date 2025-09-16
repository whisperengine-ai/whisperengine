#!/usr/bin/env python3
"""
WhisperEngine Scaling System Test
Quick test of the adaptive configuration, database abstraction, and cost optimization.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.adaptive_config import AdaptiveConfigManager
from src.config.config_integration import WhisperEngineConfigIntegrator
from src.database.database_integration import DatabaseIntegrationManager
from src.optimization.cost_optimizer import CostOptimizationEngine, RequestContext


async def test_adaptive_configuration():
    """Test adaptive configuration system"""

    config_manager = AdaptiveConfigManager()
    config_manager.get_deployment_info()


    return True


async def test_database_integration():
    """Test database abstraction layer"""

    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)

    try:
        # Initialize database
        if await db_manager.initialize():

            # Test query
            db = db_manager.get_database_manager()
            await db.query("SELECT COUNT(*) as count FROM users")

            # Test insertion
            await db.query(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (:user_id, :username)",
                {"user_id": "test_scaling_123", "username": "ScalingTest"},
            )

            db_manager.get_deployment_info()

            return True
        else:
            return False

    except Exception:
        return False

    finally:
        await db_manager.cleanup()


async def test_cost_optimization():
    """Test cost optimization engine"""

    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)

    try:
        await db_manager.initialize()
        cost_optimizer = CostOptimizationEngine(db_manager)

        # Test model selection
        context = RequestContext(
            user_id="test_user",
            conversation_length=3,
            prompt_tokens=1500,
            expected_output_tokens=150,
            conversation_type="casual",
            priority="normal",
        )

        await cost_optimizer.select_optimal_model(context)

        # Test cost estimation
        await cost_optimizer.estimate_monthly_cost("test_user")

        # Test optimization suggestions
        await cost_optimizer.get_cost_optimization_suggestions("test_user")

        return True

    except Exception:
        return False

    finally:
        await db_manager.cleanup()


async def test_integration_workflow():
    """Test full integration workflow"""

    try:
        # Create integrator
        integrator = WhisperEngineConfigIntegrator()

        # Setup environment
        if integrator.setup_environment():
            pass

        # Get AI configuration
        integrator.get_ai_config()

        # Get database configuration
        integrator.get_database_config()

        # Get performance recommendations
        integrator.get_performance_recommendations()

        return True

    except Exception:
        return False


def generate_summary_report():
    """Generate deployment summary"""

    config_manager = AdaptiveConfigManager()
    integrator = WhisperEngineConfigIntegrator()

    # System info
    config_manager.get_deployment_info()

    # Configuration
    integrator.get_ai_config()

    # Cost projections based on real data

    # Performance recommendations
    recommendations = integrator.get_performance_recommendations()
    for _i, _rec in enumerate(recommendations["recommendations"][:3], 1):
        pass


async def main():
    """Run all tests"""

    tests = [
        test_adaptive_configuration,
        test_database_integration,
        test_cost_optimization,
        test_integration_workflow,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception:
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)


    if passed == total:
        generate_summary_report()
    else:
        pass

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
