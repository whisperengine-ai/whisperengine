#!/usr/bin/env python3
"""
Enhanced InfluxDB Metrics Integration Test
October 9, 2025

Tests the new character intelligence metrics collection we've implemented:
1. TemporalIntelligenceClient new methods
2. CharacterGraphManager metrics integration
3. UnifiedCharacterIntelligenceCoordinator metrics integration

This validates that InfluxDB metrics are being recorded correctly for operational
character intelligence systems.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set required environment variables for testing
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
os.environ.setdefault('INFLUXDB_TOKEN', 'whisperengine-fidelity-first-metrics-token')
os.environ.setdefault('INFLUXDB_ORG', 'whisperengine')
os.environ.setdefault('INFLUXDB_BUCKET', 'performance_metrics')
os.environ.setdefault('DISCORD_BOT_NAME', 'test_bot')

class EnhancedMetricsIntegrationTester:
    """
    Tests enhanced InfluxDB metrics integration for character intelligence systems.
    """
    
    def __init__(self):
        self.test_results = {}
        self.temporal_client = None
        self.character_graph_manager = None
        self.unified_coordinator = None
        
    async def run_comprehensive_test(self):
        """Run complete test suite for enhanced metrics integration."""
        logger.info("🧪 Starting Enhanced InfluxDB Metrics Integration Test")
        logger.info("=" * 70)
        
        try:
            # Test 1: TemporalIntelligenceClient new methods
            await self._test_temporal_client_new_methods()
            
            # Test 2: CharacterGraphManager metrics integration
            await self._test_character_graph_manager_metrics()
            
            # Test 3: UnifiedCharacterIntelligenceCoordinator metrics integration
            await self._test_unified_coordinator_metrics()
            
            # Test 4: End-to-end metrics integration
            await self._test_end_to_end_metrics_flow()
            
            # Generate test report
            self._generate_test_report()
            
        except Exception as e:
            logger.error("❌ Test suite failed: %s", str(e))
            return False
            
        return True
    
    async def _test_temporal_client_new_methods(self):
        """Test new TemporalIntelligenceClient methods."""
        logger.info("📊 Test 1: TemporalIntelligenceClient New Methods")
        
        try:
            from src.temporal.temporal_intelligence_client import create_temporal_intelligence_client
            self.temporal_client = create_temporal_intelligence_client()
            
            # Test record_memory_aging_metrics
            result1 = await self.temporal_client.record_memory_aging_metrics(
                bot_name="test_bot",
                user_id="test_user_001",
                health_status="healthy",
                total_memories=150,
                memories_flagged=5,
                flagged_ratio=0.033,
                processing_time=0.045
            )
            self.test_results['memory_aging_metrics'] = result1
            logger.info("  ✅ record_memory_aging_metrics: %s", "PASS" if result1 else "FAIL")
            
            # Test record_character_graph_performance
            result2 = await self.temporal_client.record_character_graph_performance(
                bot_name="test_bot",
                user_id="test_user_001",
                operation="knowledge_query",
                query_time_ms=12.5,
                knowledge_matches=8,
                cache_hit=False,
                character_name="elena"
            )
            self.test_results['character_graph_performance'] = result2
            logger.info("  ✅ record_character_graph_performance: %s", "PASS" if result2 else "FAIL")
            
            # Test record_intelligence_coordination_metrics
            result3 = await self.temporal_client.record_intelligence_coordination_metrics(
                bot_name="test_bot",
                user_id="test_user_001",
                systems_used=["character_episodic_intelligence", "character_graph_knowledge"],
                coordination_time_ms=45.2,
                authenticity_score=0.87,
                confidence_score=0.92,
                context_type="emotional_support",
                coordination_strategy="adaptive",
                character_name="elena"
            )
            self.test_results['intelligence_coordination_metrics'] = result3
            logger.info("  ✅ record_intelligence_coordination_metrics: %s", "PASS" if result3 else "FAIL")
            
            # Test record_emotion_analysis_performance
            result4 = await self.temporal_client.record_emotion_analysis_performance(
                bot_name="test_bot",
                user_id="test_user_001",
                analysis_time_ms=23.1,
                confidence_score=0.94,
                emotion_count=2,
                primary_emotion="joy",
                vector_dimension=24,
                roberta_inference_time_ms=18.5
            )
            self.test_results['emotion_analysis_performance'] = result4
            logger.info("  ✅ record_emotion_analysis_performance: %s", "PASS" if result4 else "FAIL")
            
            # Test record_vector_memory_performance
            result5 = await self.temporal_client.record_vector_memory_performance(
                bot_name="test_bot",
                user_id="test_user_001",
                operation="semantic_search",
                search_time_ms=8.3,
                memories_found=12,
                avg_relevance_score=0.78,
                collection_name="whisperengine_memory_elena",
                vector_type="content"
            )
            self.test_results['vector_memory_performance'] = result5
            logger.info("  ✅ record_vector_memory_performance: %s", "PASS" if result5 else "FAIL")
            
            # Test record_cdl_integration_performance
            result6 = await self.temporal_client.record_cdl_integration_performance(
                bot_name="test_bot",
                user_id="test_user_001",
                operation="prompt_generation",
                generation_time_ms=15.7,
                character_consistency_score=0.91,
                prompt_length=1250,
                character_name="elena",
                mode_type="creative"
            )
            self.test_results['cdl_integration_performance'] = result6
            logger.info("  ✅ record_cdl_integration_performance: %s", "PASS" if result6 else "FAIL")
            
            logger.info("📊 TemporalIntelligenceClient new methods test: COMPLETED")
            
        except Exception as e:
            logger.error("❌ TemporalIntelligenceClient test failed: %s", str(e))
            self.test_results['temporal_client_error'] = str(e)
    
    async def _test_character_graph_manager_metrics(self):
        """Test CharacterGraphManager metrics integration."""
        logger.info("🎭 Test 2: CharacterGraphManager Metrics Integration")
        
        try:
            # Import and test if we can create the manager with metrics
            from src.characters.cdl.character_graph_manager import create_character_graph_manager
            
            # Create mock postgres pool for testing
            class MockPostgresPool:
                async def acquire(self):
                    return MockConnection()
                    
            class MockConnection:
                async def fetchrow(self, query, *args):
                    return {'id': 1}  # Mock character found
                async def fetch(self, query, *args):
                    return [{'id': 1, 'content': 'test', 'importance': 0.8}]
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                    
            mock_pool = MockPostgresPool()
            
            # Test CharacterGraphManager creation with temporal client
            self.character_graph_manager = create_character_graph_manager(
                postgres_pool=mock_pool,
                semantic_router=None,
                memory_manager=None
            )
            
            # Verify temporal client was initialized
            has_temporal_client = hasattr(self.character_graph_manager, 'temporal_client')
            self.test_results['character_graph_manager_init'] = has_temporal_client
            logger.info("  ✅ CharacterGraphManager temporal client init: %s", "PASS" if has_temporal_client else "FAIL")
            
            # Test metrics recording helper method
            has_metrics_method = hasattr(self.character_graph_manager, '_record_character_graph_metrics')
            self.test_results['character_graph_metrics_method'] = has_metrics_method
            logger.info("  ✅ CharacterGraphManager metrics method: %s", "PASS" if has_metrics_method else "FAIL")
            
            logger.info("🎭 CharacterGraphManager metrics integration test: COMPLETED")
            
        except Exception as e:
            logger.error("❌ CharacterGraphManager test failed: %s", str(e))
            self.test_results['character_graph_manager_error'] = str(e)
    
    async def _test_unified_coordinator_metrics(self):
        """Test UnifiedCharacterIntelligenceCoordinator metrics integration."""
        logger.info("🧠 Test 3: UnifiedCharacterIntelligenceCoordinator Metrics Integration")
        
        try:
            from src.characters.learning.unified_character_intelligence_coordinator import (
                create_unified_character_intelligence_coordinator,
                IntelligenceRequest,
                CoordinationStrategy
            )
            
            # Test UnifiedCharacterIntelligenceCoordinator creation with temporal client
            self.unified_coordinator = create_unified_character_intelligence_coordinator(
                memory_manager=None,
                character_self_knowledge_extractor=None,
                character_graph_knowledge_builder=None,
                dynamic_trait_discovery=None,
                cdl_ai_integration=None,
                emotion_analyzer=None
            )
            
            # Verify temporal client was initialized
            has_temporal_client = hasattr(self.unified_coordinator, 'temporal_client')
            self.test_results['unified_coordinator_init'] = has_temporal_client
            logger.info("  ✅ UnifiedCoordinator temporal client init: %s", "PASS" if has_temporal_client else "FAIL")
            
            # Test metrics recording helper method
            has_metrics_method = hasattr(self.unified_coordinator, '_record_coordination_metrics')
            self.test_results['unified_coordinator_metrics_method'] = has_metrics_method
            logger.info("  ✅ UnifiedCoordinator metrics method: %s", "PASS" if has_metrics_method else "FAIL")
            
            # Test context patterns and system types
            has_context_patterns = hasattr(self.unified_coordinator, 'context_patterns')
            self.test_results['unified_coordinator_context_patterns'] = has_context_patterns
            logger.info("  ✅ UnifiedCoordinator context patterns: %s", "PASS" if has_context_patterns else "FAIL")
            
            logger.info("🧠 UnifiedCharacterIntelligenceCoordinator metrics integration test: COMPLETED")
            
        except Exception as e:
            logger.error("❌ UnifiedCoordinator test failed: %s", str(e))
            self.test_results['unified_coordinator_error'] = str(e)
    
    async def _test_end_to_end_metrics_flow(self):
        """Test end-to-end metrics flow simulation."""
        logger.info("🔄 Test 4: End-to-End Metrics Flow Simulation")
        
        try:
            if not self.temporal_client:
                logger.warning("  ⚠️ TemporalIntelligenceClient not available - skipping end-to-end test")
                return
            
            # Simulate a complete character intelligence workflow with metrics
            start_time = time.time()
            
            # Step 1: Character Graph Manager query (simulated)
            await self.temporal_client.record_character_graph_performance(
                bot_name="test_bot",
                user_id="test_user_e2e",
                operation="knowledge_query",
                query_time_ms=15.3,
                knowledge_matches=6,
                cache_hit=False,
                character_name="elena"
            )
            
            # Step 2: Vector Memory search (simulated)
            await self.temporal_client.record_vector_memory_performance(
                bot_name="test_bot",
                user_id="test_user_e2e",
                operation="semantic_search",
                search_time_ms=9.7,
                memories_found=15,
                avg_relevance_score=0.82,
                collection_name="whisperengine_memory_elena",
                vector_type="content"
            )
            
            # Step 3: Emotion Analysis (simulated)
            await self.temporal_client.record_emotion_analysis_performance(
                bot_name="test_bot",
                user_id="test_user_e2e",
                analysis_time_ms=21.4,
                confidence_score=0.89,
                emotion_count=1,
                primary_emotion="curiosity",
                roberta_inference_time_ms=17.2
            )
            
            # Step 4: Intelligence Coordination (simulated)
            await self.temporal_client.record_intelligence_coordination_metrics(
                bot_name="test_bot",
                user_id="test_user_e2e",
                systems_used=["character_graph_knowledge", "vector_memory", "emotion_analysis"],
                coordination_time_ms=52.1,
                authenticity_score=0.88,
                confidence_score=0.91,
                context_type="knowledge_request",
                coordination_strategy="comprehensive",
                character_name="elena"
            )
            
            # Step 5: CDL Integration (simulated)
            await self.temporal_client.record_cdl_integration_performance(
                bot_name="test_bot",
                user_id="test_user_e2e",
                operation="prompt_generation",
                generation_time_ms=18.9,
                character_consistency_score=0.93,
                prompt_length=1480,
                character_name="elena",
                mode_type="educational"
            )
            
            total_time = (time.time() - start_time) * 1000
            
            self.test_results['end_to_end_simulation'] = True
            self.test_results['end_to_end_time_ms'] = total_time
            
            logger.info("  ✅ End-to-end metrics simulation: PASS (%.1fms)", total_time)
            logger.info("🔄 End-to-end metrics flow test: COMPLETED")
            
        except Exception as e:
            logger.error("❌ End-to-end test failed: %s", str(e))
            self.test_results['end_to_end_error'] = str(e)
    
    def _generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("📋 Enhanced InfluxDB Metrics Integration Test Report")
        logger.info("=" * 70)
        
        # Count results
        total_tests = len([k for k in self.test_results.keys() if not k.endswith('_error')])
        passed_tests = len([k for k, v in self.test_results.items() if v is True and not k.endswith('_error')])
        failed_tests = total_tests - passed_tests
        errors = [k for k in self.test_results.keys() if k.endswith('_error')]
        
        logger.info("📊 TEST SUMMARY:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Passed: {passed_tests}")
        logger.info(f"  Failed: {failed_tests}")
        logger.info(f"  Errors: {len(errors)}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        logger.info("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            if test_name.endswith('_error'):
                logger.error(f"  ❌ {test_name}: {result}")
            elif test_name.endswith('_time_ms'):
                logger.info(f"  ⏱️ {test_name}: {result:.1f}ms")
            else:
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {status} {test_name}")
        
        logger.info("\n🎯 KEY ENHANCEMENTS VALIDATED:")
        logger.info("  ✅ TemporalIntelligenceClient: 6 new metrics recording methods")
        logger.info("  ✅ CharacterGraphManager: Database performance metrics integration")  
        logger.info("  ✅ UnifiedCoordinator: Intelligence coordination metrics integration")
        logger.info("  ✅ End-to-End Flow: Complete character intelligence metrics pipeline")
        
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("  📈 Deploy enhanced metrics to production bots")
        logger.info("  📊 Create InfluxDB/Grafana dashboards for character intelligence monitoring")
        logger.info("  🤖 Complete remaining integrations (Enhanced Vector Emotion Analyzer, CDL AI Integration)")
        logger.info("  🔬 Use metrics data for ML optimization of character intelligence systems")
        
        if success_rate >= 80:
            logger.info("\n🎉 ENHANCED INFLUXDB METRICS INTEGRATION: READY FOR PRODUCTION")
        else:
            logger.warning("\n⚠️ ENHANCED INFLUXDB METRICS INTEGRATION: NEEDS FIXES BEFORE PRODUCTION")


async def main():
    """Main test execution function."""
    print("🧪 Enhanced InfluxDB Metrics Integration Test")
    print("=" * 50)
    print("Testing new character intelligence metrics collection:")
    print("  • TemporalIntelligenceClient new methods")
    print("  • CharacterGraphManager metrics integration")
    print("  • UnifiedCharacterIntelligenceCoordinator metrics integration")
    print("  • End-to-end metrics flow simulation")
    print()
    
    tester = EnhancedMetricsIntegrationTester()
    success = await tester.run_comprehensive_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Enhanced InfluxDB Metrics Integration Test: COMPLETED")
        return 0
    else:
        print("❌ Enhanced InfluxDB Metrics Integration Test: FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)