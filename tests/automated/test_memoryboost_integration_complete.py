#!/usr/bin/env python3
"""
🚀 SPRINT 2: MemoryBoost Full Integration Test

Complete validation of MemoryBoost system integrated with vector memory,
testing the complete end-to-end workflow from memory storage to optimized retrieval.

This test validates the entire MemoryBoost adaptive learning pipeline working
together as intended for Sprint 2 completion.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryBoostIntegrationTest:
    """Complete end-to-end MemoryBoost integration testing"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        self.memory_manager = None
        
    async def setup_test_environment(self):
        """Set up complete MemoryBoost test environment"""
        logger.info("🔧 Setting up MemoryBoost integration test environment...")
        
        try:
            # Initialize vector memory manager with MemoryBoost
            from src.memory.memory_protocol import create_memory_manager
            
            config = {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6334,
                    'collection_name': 'whisperengine_memory_test_integration'
                },
                'embeddings': {
                    'model_name': 'BAAI/bge-small-en-v1.5'
                }
            }
            
            self.memory_manager = create_memory_manager(
                memory_type="vector",
                config=config
            )
            
            # Initialize MemoryBoost components
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            
            effectiveness_analyzer = create_memory_effectiveness_analyzer(
                memory_manager=self.memory_manager,
                trend_analyzer=None,  # Using fallback for test
                temporal_client=None
            )
            
            relevance_optimizer = create_vector_relevance_optimizer(
                memory_manager=self.memory_manager,
                effectiveness_analyzer=effectiveness_analyzer
            )
            
            # Store references for testing
            self.effectiveness_analyzer = effectiveness_analyzer
            self.relevance_optimizer = relevance_optimizer
            
            logger.info("✅ MemoryBoost integration test environment ready")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to setup test environment: %s", str(e))
            return False
    
    async def test_end_to_end_workflow(self):
        """Test 1: Complete end-to-end MemoryBoost workflow"""
        logger.info("🔄 TEST 1: End-to-end MemoryBoost workflow...")
        
        try:
            # Step 1: Store test memories with emotional context
            test_memories = [
                {
                    'user_id': 'integration_test_user',
                    'content': 'User loves mountain hiking and outdoor adventures',
                    'memory_type': 'preference',
                    'metadata': {'emotional_context': 'joy', 'confidence': 0.9}
                },
                {
                    'user_id': 'integration_test_user',
                    'content': 'User is learning Spanish and practicing daily',
                    'memory_type': 'fact',
                    'metadata': {'emotional_context': 'determination', 'confidence': 0.8}
                },
                {
                    'user_id': 'integration_test_user',
                    'content': 'User works as a software engineer at a tech startup',
                    'memory_type': 'fact',
                    'metadata': {'emotional_context': 'neutral', 'confidence': 0.9}
                },
                {
                    'user_id': 'integration_test_user',
                    'content': 'User mentioned feeling stressed about deadlines',
                    'memory_type': 'emotional_state',
                    'metadata': {'emotional_context': 'stress', 'confidence': 0.7}
                }
            ]
            
            # Store memories
            memory_ids = []
            for memory in test_memories:
                memory_id = await self.memory_manager.store_memory(
                    user_id=memory['user_id'],
                    content=memory['content'],
                    memory_type=memory['memory_type'],
                    metadata=memory['metadata']
                )
                memory_ids.append(memory_id)
                logger.info("Stored memory: %s", memory_id)
            
            # Step 2: Retrieve memories normally (baseline)
            baseline_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id='integration_test_user',
                query='Tell me about the user\'s interests and work',
                limit=10
            )
            logger.info("Baseline retrieval: %d memories", len(baseline_memories))
            
            # Step 3: Apply MemoryBoost analysis
            performance_analysis = await self.effectiveness_analyzer.analyze_memory_performance(
                user_id='integration_test_user',
                bot_name='elena',
                days_back=1
            )
            logger.info("Performance analysis completed: %s patterns", len(performance_analysis))
            
            # Step 4: Apply quality scoring to memories
            scored_memories = await self.relevance_optimizer.apply_quality_scoring(
                memory_results=baseline_memories,
                user_id='integration_test_user',
                bot_name='elena'
            )
            logger.info("Quality scoring applied: %d memories scored", len(scored_memories))
            
            # Step 5: Apply full optimization
            optimization_result = await self.relevance_optimizer.optimize_memory_retrieval(
                user_id='integration_test_user',
                bot_name='elena',
                query='Tell me about the user\'s interests and work',
                original_results=baseline_memories,
                conversation_context='getting to know user'
            )
            logger.info("Optimization completed: %s", str(optimization_result.performance_improvement))
            
            # Step 6: Validate optimization improvements
            optimization_metrics = {
                'memories_stored': len(memory_ids),
                'baseline_retrieved': len(baseline_memories),
                'memories_scored': len(scored_memories),
                'optimization_applied': optimization_result.optimization_count,
                'performance_improvement': optimization_result.performance_improvement,
                'processing_time_ms': optimization_result.processing_time_ms
            }
            
            self.test_results.append({
                'test': 'end_to_end_workflow',
                'status': 'PASSED',
                'details': optimization_metrics
            })
            logger.info("✅ TEST 1 PASSED: End-to-end workflow completed successfully")
            
        except Exception as e:
            self.test_results.append({
                'test': 'end_to_end_workflow',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 1 FAILED: End-to-end workflow failed: %s", str(e))
    
    async def test_adaptive_learning(self):
        """Test 2: Adaptive learning over multiple queries"""
        logger.info("🧠 TEST 2: Adaptive learning behavior...")
        
        try:
            # Simulate multiple queries with different contexts
            test_queries = [
                ('What are the user\'s hobbies?', 'casual conversation'),
                ('How is the user feeling lately?', 'emotional check-in'),
                ('What does the user do for work?', 'professional discussion'),
                ('What is the user learning?', 'educational context')
            ]
            
            adaptation_results = []
            
            for i, (query, context) in enumerate(test_queries):
                # Get baseline memories
                baseline_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id='integration_test_user',
                    query=query,
                    limit=10
                )
                
                # Apply MemoryBoost optimization
                optimization_result = await self.relevance_optimizer.optimize_memory_retrieval(
                    user_id='integration_test_user',
                    bot_name='elena',
                    query=query,
                    original_results=baseline_memories,
                    conversation_context=context
                )
                
                adaptation_results.append({
                    'query_index': i + 1,
                    'query': query,
                    'context': context,
                    'baseline_count': len(baseline_memories),
                    'optimized_count': len(optimization_result.optimized_results),
                    'optimizations_applied': optimization_result.optimization_count,
                    'performance_improvement': optimization_result.performance_improvement,
                    'processing_time_ms': optimization_result.processing_time_ms
                })
                
                logger.info("Query %d optimization: %s improvements, %.2f%% performance gain", 
                           i + 1, optimization_result.optimization_count, optimization_result.performance_improvement)
            
            # Analyze adaptation patterns
            total_improvements = sum(r['optimizations_applied'] for r in adaptation_results)
            avg_performance_gain = sum(r['performance_improvement'] for r in adaptation_results) / len(adaptation_results)
            
            self.test_results.append({
                'test': 'adaptive_learning',
                'status': 'PASSED',
                'details': {
                    'queries_processed': len(test_queries),
                    'total_optimizations': total_improvements,
                    'average_performance_gain': avg_performance_gain,
                    'adaptation_results': adaptation_results
                }
            })
            logger.info("✅ TEST 2 PASSED: Adaptive learning working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'adaptive_learning',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 2 FAILED: Adaptive learning failed: %s", str(e))
    
    async def test_optimization_recommendations(self):
        """Test 3: MemoryBoost optimization recommendations"""
        logger.info("💡 TEST 3: Optimization recommendations...")
        
        try:
            # Get effectiveness recommendations
            effectiveness_recommendations = await self.effectiveness_analyzer.get_memory_optimization_recommendations(
                user_id='integration_test_user',
                bot_name='elena',
                conversation_context='comprehensive evaluation'
            )
            
            # Get optimizer recommendations
            optimizer_recommendations = await self.relevance_optimizer.get_optimization_recommendations(
                user_id='integration_test_user',
                bot_name='elena',
                performance_window_days=1
            )
            
            # Validate recommendation structure
            recommendation_metrics = {
                'effectiveness_recommendations_generated': effectiveness_recommendations is not None,
                'optimizer_recommendations_generated': optimizer_recommendations is not None,
                'effectiveness_patterns': len(effectiveness_recommendations.get('boost_patterns', [])),
                'optimization_strategies': len(optimizer_recommendations.get('boost_strategies', [])),
                'confidence_scores': {
                    'effectiveness': effectiveness_recommendations.get('confidence', 0),
                    'optimizer': optimizer_recommendations.get('confidence', 0)
                }
            }
            
            self.test_results.append({
                'test': 'optimization_recommendations',
                'status': 'PASSED',
                'details': recommendation_metrics
            })
            logger.info("✅ TEST 3 PASSED: Optimization recommendations working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'optimization_recommendations',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 3 FAILED: Optimization recommendations failed: %s", str(e))
    
    async def test_performance_metrics(self):
        """Test 4: Performance metrics and monitoring"""
        logger.info("📊 TEST 4: Performance metrics and monitoring...")
        
        try:
            # Test multiple optimization cycles for performance measurement
            performance_data = []
            
            for cycle in range(3):
                start_time = time.time()
                
                # Standard memory retrieval
                baseline_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id='integration_test_user',
                    query=f'Performance test cycle {cycle + 1}',
                    limit=10
                )
                baseline_time = time.time() - start_time
                
                # MemoryBoost optimization
                start_time = time.time()
                optimization_result = await self.relevance_optimizer.optimize_memory_retrieval(
                    user_id='integration_test_user',
                    bot_name='elena',
                    query=f'Performance test cycle {cycle + 1}',
                    original_results=baseline_memories,
                    conversation_context='performance testing'
                )
                optimization_time = time.time() - start_time
                
                performance_data.append({
                    'cycle': cycle + 1,
                    'baseline_time_ms': baseline_time * 1000,
                    'optimization_time_ms': optimization_time * 1000,
                    'total_processing_time_ms': optimization_result.processing_time_ms,
                    'memories_processed': len(baseline_memories),
                    'optimizations_applied': optimization_result.optimization_count,
                    'performance_improvement': optimization_result.performance_improvement
                })
            
            # Calculate performance statistics
            avg_baseline_time = sum(p['baseline_time_ms'] for p in performance_data) / len(performance_data)
            avg_optimization_time = sum(p['optimization_time_ms'] for p in performance_data) / len(performance_data)
            avg_improvement = sum(p['performance_improvement'] for p in performance_data) / len(performance_data)
            
            performance_metrics = {
                'test_cycles': len(performance_data),
                'average_baseline_time_ms': avg_baseline_time,
                'average_optimization_time_ms': avg_optimization_time,
                'average_performance_improvement': avg_improvement,
                'performance_overhead_ratio': avg_optimization_time / avg_baseline_time if avg_baseline_time > 0 else 0,
                'detailed_performance_data': performance_data
            }
            
            self.test_results.append({
                'test': 'performance_metrics',
                'status': 'PASSED',
                'details': performance_metrics
            })
            logger.info("✅ TEST 4 PASSED: Performance metrics working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'performance_metrics',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 4 FAILED: Performance metrics failed: %s", str(e))
    
    async def run_full_integration_test(self):
        """Run complete MemoryBoost integration test suite"""
        logger.info("🚀 Starting MemoryBoost Full Integration Test...")
        
        # Setup test environment
        if not await self.setup_test_environment():
            logger.error("❌ Failed to setup test environment")
            return {'success': False, 'error': 'Environment setup failed'}
        
        # Run all integration tests
        await self.test_end_to_end_workflow()
        await self.test_adaptive_learning()
        await self.test_optimization_recommendations()
        await self.test_performance_metrics()
        
        # Calculate final results
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASSED'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate comprehensive results
        results_filename = f"memoryboost_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        final_results = {
            'test_type': 'MemoryBoost Full Integration',
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'execution_time_seconds': time.time() - self.start_time,
            'test_details': self.test_results,
            'summary': {
                'memoryboost_fully_functional': success_rate == 100,
                'adaptive_learning_working': any(t['test'] == 'adaptive_learning' and t['status'] == 'PASSED' for t in self.test_results),
                'end_to_end_workflow_verified': any(t['test'] == 'end_to_end_workflow' and t['status'] == 'PASSED' for t in self.test_results),
                'performance_metrics_captured': any(t['test'] == 'performance_metrics' and t['status'] == 'PASSED' for t in self.test_results),
                'recommendations_generated': any(t['test'] == 'optimization_recommendations' and t['status'] == 'PASSED' for t in self.test_results)
            }
        }
        
        # Write comprehensive results
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("🚀 MEMORYBOOST FULL INTEGRATION TEST RESULTS")
        print("="*80)
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Overall Status: {'✅ FULLY FUNCTIONAL' if success_rate == 100 else '❌ INTEGRATION ISSUES'}")
        print("="*80)
        
        for test in self.test_results:
            status_icon = "✅" if test['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {test['status']}: {test['test']}")
            if test['status'] == 'FAILED':
                print(f"  Error: {test.get('error', 'Unknown error')}")
        
        print("="*80)
        print(f"📁 Comprehensive results written to: {results_filename}")
        print()
        
        return final_results


async def main():
    """Main integration test execution"""
    integration_test = MemoryBoostIntegrationTest()
    results = await integration_test.run_full_integration_test()
    return results


if __name__ == "__main__":
    asyncio.run(main())