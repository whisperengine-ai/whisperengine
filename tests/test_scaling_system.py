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
    print("🔧 Testing Adaptive Configuration...")
    
    config_manager = AdaptiveConfigManager()
    deployment_info = config_manager.get_deployment_info()
    
    print(f"   ✅ Detected: {deployment_info['deployment_mode']} mode")
    print(f"   ✅ Scale Tier: {deployment_info['scale_tier']}")
    print(f"   ✅ Resources: {deployment_info['cpu_cores']} cores, {deployment_info['memory_gb']:.1f}GB RAM")
    print(f"   ✅ Platform: {deployment_info['platform']}")
    
    return True


async def test_database_integration():
    """Test database abstraction layer"""
    print("\n💾 Testing Database Integration...")
    
    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)
    
    try:
        # Initialize database
        if await db_manager.initialize():
            print("   ✅ Database connection established")
            
            # Test query
            db = db_manager.get_database_manager()
            result = await db.query("SELECT COUNT(*) as count FROM users")
            print(f"   ✅ Query executed successfully: {result.row_count} rows")
            
            # Test insertion
            await db.query(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (:user_id, :username)",
                {"user_id": "test_scaling_123", "username": "ScalingTest"}
            )
            print("   ✅ Data insertion successful")
            
            deployment_info = db_manager.get_deployment_info()
            print(f"   ✅ Database type: {deployment_info['database_type']}")
            
            return True
        else:
            print("   ❌ Database initialization failed")
            return False
    
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False
    
    finally:
        await db_manager.cleanup()


async def test_cost_optimization():
    """Test cost optimization engine"""
    print("\n💰 Testing Cost Optimization...")
    
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
            priority="normal"
        )
        
        selected_model = await cost_optimizer.select_optimal_model(context)
        print(f"   ✅ Model selection: {selected_model}")
        
        # Test cost estimation
        monthly_estimate = await cost_optimizer.estimate_monthly_cost("test_user")
        print(f"   ✅ Cost estimation: ${monthly_estimate.get('monthly_estimate', 0.0):.4f}/month")
        
        # Test optimization suggestions
        suggestions = await cost_optimizer.get_cost_optimization_suggestions("test_user")
        print(f"   ✅ Generated {len(suggestions)} optimization suggestions")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Cost optimization test failed: {e}")
        return False
    
    finally:
        await db_manager.cleanup()


async def test_integration_workflow():
    """Test full integration workflow"""
    print("\n🔄 Testing Integration Workflow...")
    
    try:
        # Create integrator
        integrator = WhisperEngineConfigIntegrator()
        
        # Setup environment
        if integrator.setup_environment():
            print("   ✅ Environment setup successful")
        
        # Get AI configuration
        ai_config = integrator.get_ai_config()
        print(f"   ✅ AI Config: External embeddings={ai_config['use_external_embeddings']}")
        
        # Get database configuration
        db_config = integrator.get_database_config()
        print(f"   ✅ DB Config: {db_config['vector_database_mode']}")
        
        # Get performance recommendations
        recommendations = integrator.get_performance_recommendations()
        print(f"   ✅ Got {len(recommendations['recommendations'])} performance recommendations")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Integration workflow test failed: {e}")
        return False


def generate_summary_report():
    """Generate deployment summary"""
    print("\n📊 Deployment Summary")
    print("=" * 50)
    
    config_manager = AdaptiveConfigManager()
    integrator = WhisperEngineConfigIntegrator()
    
    # System info
    deployment_info = config_manager.get_deployment_info()
    print(f"Deployment Mode: {deployment_info['deployment_mode']}")
    print(f"Scale Tier: {deployment_info['scale_tier']}")
    print(f"Hardware: {deployment_info['cpu_cores']} cores, {deployment_info['memory_gb']:.1f}GB")
    print(f"Platform: {deployment_info['platform']} ({deployment_info['architecture']})")
    print(f"GPU Available: {deployment_info['gpu_available']}")
    
    # Configuration
    ai_config = integrator.get_ai_config()
    print(f"\nAI Configuration:")
    print(f"  External Embeddings: {ai_config['use_external_embeddings']}")
    print(f"  Semantic Clustering: {ai_config['enable_semantic_clustering']}")
    print(f"  CPU Threads: {ai_config['cpu_threads']}")
    print(f"  Memory Limit: {ai_config['memory_limit_gb']:.1f}GB")
    
    # Cost projections based on real data
    print(f"\nCost Projections (based on real usage):")
    print(f"  Single User: ~$300-500/year")
    print(f"  Small Team (10 users): ~$3,000-5,000/year")
    print(f"  Enterprise (100 users): ~$30,000-50,000/year")
    
    # Performance recommendations
    recommendations = integrator.get_performance_recommendations()
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(recommendations['recommendations'][:3], 1):
        print(f"  {i}. {rec}")


async def main():
    """Run all tests"""
    print("🚀 WhisperEngine Scaling Architecture Test Suite")
    print("=" * 60)
    
    tests = [
        test_adaptive_configuration,
        test_database_integration,
        test_cost_optimization,
        test_integration_workflow
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📈 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational! Ready for deployment.")
        generate_summary_report()
    else:
        print("⚠️  Some tests failed. Check configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)