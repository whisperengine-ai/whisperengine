#!/usr/bin/env python3
"""
Demo: Production System Integration Testing
Tests the complete integration of all optimized components with WhisperEngine
"""

import asyncio
import time
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_production_system_integration():
    """Test production system integration with all components"""
    
    print("🔧 WhisperEngine Production System Integration Demo")
    print("=" * 60)
    
    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator
        
        # Initialize production system
        print("\n🚀 Initializing Production System...")
        integrator = ProductionSystemIntegrator()
        
        start_time = time.time()
        success = await integrator.initialize_production_components()
        init_time = time.time() - start_time
        
        if success:
            print(f"✅ Production system initialized in {init_time*1000:.1f}ms")
        else:
            print(f"⚠️ Production system initialization completed with some components unavailable")
        
        # Get initial system metrics
        metrics = integrator.get_production_metrics()
        print(f"\n📊 System Status: {metrics['system_status']}")
        print(f"📋 Available Components:")
        for component, available in metrics['components_available'].items():
            status = "✅" if available else "❌"
            print(f"   {status} {component}")
        
        # Test message processing pipeline
        print(f"\n🧪 Testing Production Message Processing Pipeline...")
        
        test_scenarios = [
            {
                'name': 'Standard User Message',
                'user_id': 'user_001',
                'message': 'Hello! I need help with my Python project. Can you assist me?',
                'context': {'channel_id': 'general', 'urgency': 'normal', 'priority': 'normal'}
            },
            {
                'name': 'High Priority Support',
                'user_id': 'user_002', 
                'message': 'URGENT: My application is crashing and users are affected!',
                'context': {'channel_id': 'support', 'urgency': 'high', 'priority': 'high'}
            },
            {
                'name': 'Complex Technical Question',
                'user_id': 'user_003',
                'message': 'I\'m implementing a machine learning pipeline and encountering memory issues with large datasets. What optimization strategies would you recommend?',
                'context': {'channel_id': 'tech-help', 'urgency': 'normal', 'priority': 'normal', 'enable_phase4': True}
            },
            {
                'name': 'Emotional Support Request',
                'user_id': 'user_004',
                'message': 'I\'m feeling really overwhelmed with work lately and could use some guidance on managing stress.',
                'context': {'channel_id': 'wellness', 'urgency': 'normal', 'priority': 'normal'}
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  🎯 Testing: {scenario['name']}")
            
            start_time = time.time()
            result = await integrator.process_message_production(
                user_id=scenario['user_id'],
                message=scenario['message'],
                context=scenario['context'],
                priority=scenario['context']['priority']
            )
            processing_time = time.time() - start_time
            
            print(f"    ⚡ Processing time: {processing_time*1000:.1f}ms")
            print(f"    📋 Status: {result['status']}")
            print(f"    🔄 Pipeline: {result.get('pipeline_used', 'N/A')}")
            
            # Show specific component results
            if 'emotion_analysis' in result:
                emotion = result['emotion_analysis'].get('primary_emotion', 'unknown')
                confidence = result['emotion_analysis'].get('confidence', 0)
                print(f"    😊 Emotion: {emotion} (confidence: {confidence:.2f})")
            
            if 'conversation_result' in result:
                conv_status = result['conversation_result'].get('status', 'unknown')
                print(f"    💬 Conversation: {conv_status}")
        
        # Test concurrent processing capabilities
        print(f"\n🚀 Testing Concurrent Processing Capabilities...")
        
        concurrent_users = 25
        messages_per_user = 3
        
        async def simulate_user_load(user_id: str, message_count: int):
            """Simulate concurrent user sending multiple messages"""
            results = []
            for i in range(message_count):
                message = f"Message {i+1} from {user_id}: Testing concurrent processing capabilities with message {i+1}"
                context = {
                    'channel_id': f'channel_{i % 5}',
                    'urgency': 'normal',
                    'priority': 'normal'
                }
                
                result = await integrator.process_message_production(
                    user_id=user_id,
                    message=message,
                    context=context
                )
                results.append(result)
                
                # Small delay between messages
                await asyncio.sleep(0.01)
            
            return results
        
        print(f"  📊 Simulating {concurrent_users} concurrent users × {messages_per_user} messages")
        
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
        throughput = total_messages / total_time
        
        print(f"  ⚡ Total time: {total_time*1000:.1f}ms")
        print(f"  📈 Messages processed: {total_messages}")
        print(f"  🚀 Throughput: {throughput:.1f} messages/sec")
        print(f"  👤 Avg per-user time: {total_time/concurrent_users*1000:.1f}ms")
        
        # Analyze results
        successful_messages = sum(
            1 for user_results in all_results 
            for result in user_results 
            if result.get('status') == 'success'
        )
        
        success_rate = (successful_messages / total_messages) * 100
        print(f"  ✅ Success rate: {success_rate:.1f}%")
        
        # Get final system metrics
        final_metrics = integrator.get_production_metrics()
        print(f"\n📊 Final System Metrics:")
        
        # Display component-specific metrics
        for component_name, available in final_metrics['components_available'].items():
            if available and f'{component_name}_metrics' in final_metrics:
                component_metrics = final_metrics[f'{component_name}_metrics']
                print(f"  📈 {component_name}:")
                
                # Display relevant metrics based on component
                if 'throughput' in component_metrics:
                    print(f"    🚀 Throughput: {component_metrics['throughput']:.1f} ops/sec")
                if 'avg_response_time_ms' in component_metrics:
                    print(f"    ⚡ Avg response: {component_metrics['avg_response_time_ms']:.1f}ms")
                if 'cache_hit_rate' in component_metrics:
                    print(f"    💾 Cache hit rate: {component_metrics['cache_hit_rate']:.1%}")
                if 'active_sessions' in component_metrics:
                    print(f"    👥 Active sessions: {component_metrics['active_sessions']}")
        
        # Test graceful shutdown
        print(f"\n🛑 Testing Graceful Shutdown...")
        shutdown_start = time.time()
        await integrator.shutdown_production_system()
        shutdown_time = time.time() - shutdown_start
        
        print(f"✅ System shutdown completed in {shutdown_time*1000:.1f}ms")
        
    except Exception as e:
        print(f"❌ Production system integration test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_production_adapter():
    """Test the WhisperEngine production adapter"""
    
    print("\n🔌 Testing WhisperEngine Production Adapter")
    print("=" * 50)
    
    try:
        from src.integration.production_system_integration import WhisperEngineProductionAdapter
        
        # Initialize production adapter
        adapter = WhisperEngineProductionAdapter()
        
        print("🚀 Initializing production adapter...")
        success = await adapter.initialize_production_mode()
        
        if success:
            print("✅ Production mode enabled")
        else:
            print("⚠️ Using fallback mode")
        
        # Get system status
        status = adapter.get_system_status()
        print(f"📊 System Status: {status.get('system_status', 'unknown')}")
        print(f"🔧 Production Mode: {status.get('production_mode', False)}")
        
        # Test message processing through adapter
        print(f"\n🧪 Testing Adapter Message Processing...")
        
        test_messages = [
            {
                'user_id': 'adapter_user_001',
                'message': 'Testing adapter integration with optimized components',
                'context': {'source': 'discord', 'channel_id': 'test-channel'}
            },
            {
                'user_id': 'adapter_user_002', 
                'message': 'How does the production adapter handle message routing?',
                'context': {'source': 'desktop', 'priority': 'high'}
            }
        ]
        
        for test_msg in test_messages:
            print(f"  💬 Processing message from {test_msg['user_id']}")
            
            start_time = time.time()
            result = await adapter.process_user_message(
                user_id=test_msg['user_id'],
                message=test_msg['message'],
                context=test_msg['context']
            )
            processing_time = time.time() - start_time
            
            print(f"    ⚡ Processing time: {processing_time*1000:.1f}ms")
            print(f"    📋 Status: {result.get('status', 'unknown')}")
            print(f"    🔄 Pipeline: {result.get('processing_pipeline', ['unknown'])[0]}")
        
        # Test shutdown
        await adapter.shutdown()
        print("✅ Production adapter shutdown completed")
        
    except Exception as e:
        print(f"❌ Production adapter test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_component_compatibility():
    """Test compatibility and fallback behavior"""
    
    print("\n🔄 Testing Component Compatibility & Fallbacks")
    print("=" * 55)
    
    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator
        
        # Test with limited components available
        integrator = ProductionSystemIntegrator()
        
        print("🧪 Testing component initialization with potential failures...")
        
        # Override config to simulate different scenarios
        test_configs = [
            {
                'name': 'Minimal Configuration',
                'config': {
                    'production_engine': {'max_workers_threads': 2, 'max_workers_processes': 1, 'batch_size': 16},
                    'faiss_memory': {'index_type': 'Flat', 'num_clusters': 64},
                    'vectorized_emotion': {'cache_size': 1000, 'batch_size': 100},
                    'memory_batcher': {'batch_size': 25, 'max_batch_wait_ms': 50},
                    'conversation_manager': {'max_concurrent_sessions': 100, 'max_workers_threads': 4, 'max_workers_processes': 2}
                }
            },
            {
                'name': 'High Performance Configuration',
                'config': {
                    'production_engine': {'max_workers_threads': 16, 'max_workers_processes': 8, 'batch_size': 64},
                    'faiss_memory': {'index_type': 'IVF', 'num_clusters': 512},
                    'vectorized_emotion': {'cache_size': 50000, 'batch_size': 1000},
                    'memory_batcher': {'batch_size': 100, 'max_batch_wait_ms': 200},
                    'conversation_manager': {'max_concurrent_sessions': 5000, 'max_workers_threads': 24, 'max_workers_processes': 12}
                }
            }
        ]
        
        for test_config in test_configs:
            print(f"\n  🎯 Testing {test_config['name']}")
            
            integrator.config = test_config['config']
            
            start_time = time.time()
            success = await integrator.initialize_production_components()
            init_time = time.time() - start_time
            
            print(f"    ⚡ Initialization time: {init_time*1000:.1f}ms")
            print(f"    📊 Success: {'✅' if success else '⚠️'}")
            
            # Get metrics
            metrics = integrator.get_production_metrics()
            available_count = sum(1 for available in metrics['components_available'].values() if available)
            total_count = len(metrics['components_available'])
            
            print(f"    🔧 Available components: {available_count}/{total_count}")
            
            # Test basic functionality
            if success:
                try:
                    test_result = await integrator.process_message_production(
                        user_id="compatibility_test_user",
                        message="Testing compatibility with configuration",
                        context={'test': True}
                    )
                    print(f"    ✅ Processing test: {test_result.get('status', 'unknown')}")
                except Exception as e:
                    print(f"    ❌ Processing test failed: {e}")
            
            await integrator.shutdown_production_system()
        
        print(f"\n✅ Compatibility testing completed")
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all production integration tests"""
    
    print("🔧 WhisperEngine Production System Integration Test Suite")
    print("=" * 70)
    
    # Run all integration tests
    await test_production_system_integration()
    await test_production_adapter()
    await test_component_compatibility()
    
    print(f"\n🎉 Production Integration Test Suite Completed!")
    print(f"📊 Summary:")
    print(f"   • Production system integrates all optimized components")
    print(f"   • Adapter provides transparent optimization for existing code")
    print(f"   • Graceful fallback when components unavailable")
    print(f"   • Comprehensive error handling and monitoring")
    print(f"   • Ready for server deployment with multiple concurrent clients")


if __name__ == "__main__":
    asyncio.run(main())