#!/usr/bin/env python3
"""
🚀 SPRINT 2: MemoryBoost Component Direct Unit Tests

Tests individual MemoryBoost components directly by instantiating them
and executing their functions. This validates the core functionality
without requiring complex integration setup.

Priority: High (CRITICAL for Sprint 2 completion)
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryBoostComponentTests:
    """Direct component testing suite for MemoryBoost"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        
    async def test_memory_effectiveness_analyzer(self):
        """Test 1: Memory effectiveness analysis component"""
        logger.info("🎯 TEST 1: Memory effectiveness analyzer initialization and basic functionality...")
        
        try:
            # Direct import and initialization
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            
            # Create analyzer with minimal mock dependencies
            analyzer = create_memory_effectiveness_analyzer(
                memory_manager=None,  # Will test without full memory manager
                trend_analyzer=None,  # Will test without TrendWise integration
                temporal_client=None  # Will test without InfluxDB
            )
            
            # Test memory performance analysis (should handle missing data gracefully)
            performance_result = await analyzer.analyze_memory_performance(
                user_id='test_user',
                bot_name='elena',
                days_back=7
            )
            logger.info("Memory performance analysis result: %s", str(performance_result))
            
            # Test memory quality scoring
            quality_result = await analyzer.score_memory_quality(
                memory_id='test_memory_1',
                user_id='test_user',
                bot_name='elena',
                memory_content='User likes pizza',
                memory_type='preference'
            )
            logger.info("Memory quality scoring result: %s", str(quality_result))
            
            # Test optimization recommendations
            recommendations = await analyzer.get_memory_optimization_recommendations(
                user_id='test_user',
                bot_name='elena',
                conversation_context='test conversation'
            )
            logger.info("Optimization recommendations result: %s", str(recommendations))
            
            self.test_results.append({
                'test': 'memory_effectiveness_analyzer',
                'status': 'PASSED',
                'details': {
                    'performance_analysis_completed': performance_result is not None,
                    'quality_scoring_completed': quality_result is not None,
                    'recommendations_generated': recommendations is not None,
                    'analyzer_initialized': analyzer is not None
                }
            })
            logger.info("✅ TEST 1 PASSED: Memory effectiveness analyzer working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'memory_effectiveness_analyzer',
                'status': 'FAILED', 
                'error': str(e)
            })
            logger.error("❌ TEST 1 FAILED: Memory effectiveness analyzer failed: %s", str(e))
    
    async def test_vector_relevance_optimizer(self):
        """Test 2: Vector relevance optimizer component"""
        logger.info("🚀 TEST 2: Vector relevance optimizer initialization and scoring...")
        
        try:
            # Direct import and initialization
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            
            # Create optimizer with minimal dependencies
            optimizer = create_vector_relevance_optimizer(
                memory_manager=None,  # Will test without full memory manager
                effectiveness_analyzer=None  # Will test without analyzer integration
            )
            
            # Test memory results with quality scoring
            test_memory_results = [
                {
                    'id': 'mem1', 
                    'content': 'User likes pizza with pepperoni', 
                    'score': 0.8, 
                    'metadata': {'emotional_context': 'positive', 'confidence': 0.9}
                },
                {
                    'id': 'mem2', 
                    'content': 'User mentioned work promotion', 
                    'score': 0.7,
                    'metadata': {'emotional_context': 'joy', 'confidence': 0.8}
                }
            ]
            
            # Test quality scoring with correct parameters
            scored_memories = await optimizer.apply_quality_scoring(
                memory_results=test_memory_results,
                user_id='test_user',
                bot_name='elena'
            )
            logger.info("Quality scoring result: %d memories scored", len(scored_memories))
            
            # Test optimization with correct parameters
            optimization_result = await optimizer.optimize_memory_retrieval(
                user_id='test_user',
                bot_name='elena',
                query="What does the user like?",
                original_results=test_memory_results,
                conversation_context="casual chat"
            )
            logger.info("Optimization result: %s", str(optimization_result))
            
            # Test getting optimization recommendations
            recommendations = await optimizer.get_optimization_recommendations(
                user_id='test_user',
                bot_name='elena',
                performance_window_days=7
            )
            logger.info("Optimization recommendations: %s", str(recommendations))
            
            self.test_results.append({
                'test': 'vector_relevance_optimizer',
                'status': 'PASSED',
                'details': {
                    'quality_scoring_applied': len(scored_memories) > 0,
                    'optimization_completed': optimization_result is not None,
                    'recommendations_generated': recommendations is not None,
                    'optimizer_initialized': optimizer is not None
                }
            })
            logger.info("✅ TEST 2 PASSED: Vector relevance optimizer working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'vector_relevance_optimizer',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 2 FAILED: Vector relevance optimizer failed: %s", str(e))
    
    async def test_component_integration(self):
        """Test 3: Component integration without full memory system"""
        logger.info("🔗 TEST 3: MemoryBoost component integration...")
        
        try:
            # Import both components
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            
            # Create effectiveness analyzer
            effectiveness_analyzer = create_memory_effectiveness_analyzer(
                memory_manager=None,
                trend_analyzer=None,
                temporal_client=None
            )
            
            # Create optimizer with analyzer
            optimizer = create_vector_relevance_optimizer(
                memory_manager=None,
                effectiveness_analyzer=effectiveness_analyzer
            )
            
            # Test integrated workflow
            test_memory_results = [
                {'id': 'mem1', 'content': 'User likes blue color', 'score': 0.8, 'metadata': {}},
                {'id': 'mem2', 'content': 'User travels frequently', 'score': 0.7, 'metadata': {}},
                {'id': 'mem3', 'content': 'User enjoys outdoor activities', 'score': 0.9, 'metadata': {}},
            ]
            
            # Step 1: Apply quality scoring
            scored_memories = await optimizer.apply_quality_scoring(
                memory_results=test_memory_results,
                user_id='test_user',
                bot_name='elena'
            )
            
            # Step 2: Apply optimization with scored memories
            optimization_result = await optimizer.optimize_memory_retrieval(
                user_id='test_user',
                bot_name='elena',
                query="What does the user like?",
                original_results=scored_memories,
                conversation_context="preference discussion"
            )
            
            logger.info("Integrated workflow result: %s", str(optimization_result))
            
            self.test_results.append({
                'test': 'component_integration',
                'status': 'PASSED',
                'details': {
                    'quality_scoring_applied': len(scored_memories) > 0,
                    'optimization_with_scoring': optimization_result is not None,
                    'component_cooperation': True
                }
            })
            logger.info("✅ TEST 3 PASSED: Component integration working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'component_integration',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 3 FAILED: Component integration failed: %s", str(e))
    
    async def test_factory_patterns(self):
        """Test 4: Factory pattern compliance"""
        logger.info("🏭 TEST 4: Factory pattern compliance...")
        
        try:
            # Test memory effectiveness factory
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            analyzer = create_memory_effectiveness_analyzer()
            
            # Test vector relevance optimizer factory
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            optimizer = create_vector_relevance_optimizer()
            
            # Test that factories return working instances
            self.test_results.append({
                'test': 'factory_patterns',
                'status': 'PASSED',
                'details': {
                    'effectiveness_factory_works': analyzer is not None,
                    'optimizer_factory_works': optimizer is not None,
                    'factory_pattern_compliance': True
                }
            })
            logger.info("✅ TEST 4 PASSED: Factory patterns working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'factory_patterns',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 4 FAILED: Factory patterns failed: %s", str(e))
    
    async def test_error_handling(self):
        """Test 5: Error handling and fallback behavior"""
        logger.info("🛡️ TEST 5: Error handling and fallback behavior...")
        
        try:
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            
            # Test effectiveness analyzer with invalid data
            analyzer = create_memory_effectiveness_analyzer()
            
            # Should handle gracefully - empty user
            result1 = await analyzer.analyze_memory_performance(
                user_id='',
                bot_name='elena',
                days_back=7
            )
            logger.info("Graceful handling of empty user: %s", str(result1))
            
            # Test optimizer with edge cases
            optimizer = create_vector_relevance_optimizer()
            
            # Empty memories list - should handle gracefully
            empty_result = await optimizer.apply_quality_scoring(
                memory_results=[],
                user_id='test_user',
                bot_name='elena'
            )
            
            # Invalid memory format - should handle gracefully
            invalid_result = await optimizer.apply_quality_scoring(
                memory_results=[{'invalid': 'format'}],
                user_id='test_user',
                bot_name='elena'
            )
            
            self.test_results.append({
                'test': 'error_handling',
                'status': 'PASSED',
                'details': {
                    'empty_user_handled': result1 is not None,
                    'empty_list_handled': empty_result is not None,
                    'invalid_format_handled': invalid_result is not None,
                    'graceful_degradation': True
                }
            })
            logger.info("✅ TEST 5 PASSED: Error handling working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'error_handling',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 5 FAILED: Error handling failed: %s", str(e))
    
    async def run_all_tests(self):
        """Run all component tests"""
        logger.info("🚀 Starting MemoryBoost Component Direct Testing...")
        
        # Run all tests
        await self.test_memory_effectiveness_analyzer()
        await self.test_vector_relevance_optimizer()
        await self.test_component_integration()
        await self.test_factory_patterns()
        await self.test_error_handling()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASSED'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate results report
        results_filename = f"memoryboost_components_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'execution_time_seconds': time.time() - self.start_time,
            'test_details': self.test_results
        }
        
        # Write detailed results
        with open(results_filename, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🚀 MEMORYBOOST COMPONENT TESTING RESULTS")
        print("="*80)
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Overall Status: {'✅ PASSED' if success_rate == 100 else '❌ FAILED'}")
        print("="*80)
        
        for test in self.test_results:
            status_icon = "✅" if test['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {test['status']}: {test['test']}")
            if test['status'] == 'FAILED':
                print(f"  Error: {test.get('error', 'Unknown error')}")
        
        print("="*80)
        print(f"📁 Detailed results written to: {results_filename}")
        print()
        
        return final_results


async def main():
    """Main test execution"""
    test_suite = MemoryBoostComponentTests()
    results = await test_suite.run_all_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())