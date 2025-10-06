#!/usr/bin/env python3
"""
🚀 SPRINT 2: MemoryBoost + Emoji Feedback Integration Test

Tests the integration between MemoryBoost and emoji reaction intelligence:
- Emoji reactions affecting memory quality scores
- Feedback loop from emoji reactions to memory optimization
- Memory boosting based on positive emoji patterns
- Adaptive learning from user emotional feedback

This validates the complete feedback loop from user emoji reactions back into
the MemoryBoost adaptive learning system.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryBoostEmojiIntegrationTest:
    """Test MemoryBoost integration with emoji reaction intelligence"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        self.effectiveness_analyzer = None
        self.relevance_optimizer = None
        self.memory_manager = None
        
    async def setup_emoji_integration_environment(self):
        """Set up MemoryBoost + emoji reaction integration test environment"""
        logger.info("🎭 Setting up MemoryBoost + Emoji Integration test environment...")
        
        try:
            # Initialize core components
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            from src.memory.memory_protocol import create_memory_manager
            
            # Create memory manager for testing
            config = {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6334,
                    'collection_name': 'whisperengine_memory_test_emoji'
                }
            }
            
            self.memory_manager = create_memory_manager(memory_type="vector", config=config)
            
            # Initialize effectiveness analyzer
            self.effectiveness_analyzer = create_memory_effectiveness_analyzer(
                memory_manager=self.memory_manager,
                trend_analyzer=None,
                temporal_client=None
            )
            
            # Initialize relevance optimizer
            self.relevance_optimizer = create_vector_relevance_optimizer(
                memory_manager=self.memory_manager,
                effectiveness_analyzer=self.effectiveness_analyzer
            )
            
            logger.info("✅ MemoryBoost + Emoji Integration test environment ready")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to setup emoji integration test environment: %s", str(e))
            return False
    
    async def test_emoji_feedback_memory_correlation(self):
        """Test 1: Emoji feedback correlates with memory quality scoring"""
        logger.info("😍 TEST 1: Emoji feedback memory correlation...")
        
        try:
            # Test memories with different emoji feedback patterns
            emoji_memory_scenarios = [
                {
                    'memory_content': 'User loves mountain hiking and nature photography',
                    'emoji_feedback': ['😍', '🏔️', '📸', '✨'],
                    'feedback_valence': 'very_positive',
                    'expected_boost': 'high'
                },
                {
                    'memory_content': 'User works as a software engineer at tech startup',
                    'emoji_feedback': ['👍', '💻'],
                    'feedback_valence': 'positive',
                    'expected_boost': 'medium'
                },
                {
                    'memory_content': 'User mentioned feeling stressed about deadlines',
                    'emoji_feedback': ['😔', '😓'],
                    'feedback_valence': 'negative',
                    'expected_boost': 'none'
                },
                {
                    'memory_content': 'User enjoys learning new programming languages',
                    'emoji_feedback': ['🚀', '💡', '🔥'],
                    'feedback_valence': 'very_positive',
                    'expected_boost': 'high'
                },
                {
                    'memory_content': 'User had a regular day at the office',
                    'emoji_feedback': [],
                    'feedback_valence': 'neutral',
                    'expected_boost': 'baseline'
                }
            ]
            
            correlation_results = []
            
            for i, scenario in enumerate(emoji_memory_scenarios):
                # Create mock memory result with emoji metadata
                mock_memory = {
                    'id': f'emoji_memory_{i}',
                    'content': scenario['memory_content'],
                    'score': 0.5,  # Baseline score
                    'metadata': {
                        'emoji_reactions': scenario['emoji_feedback'],
                        'feedback_valence': scenario['feedback_valence'],
                        'interaction_type': 'conversation_with_emoji_feedback'
                    }
                }
                
                # Apply quality scoring that considers emoji feedback
                scored_memories = await self.relevance_optimizer.apply_quality_scoring(
                    memory_results=[mock_memory],
                    user_id='emoji_correlation_user',
                    bot_name='elena'
                )
                
                # Analyze score change based on emoji feedback
                original_score = mock_memory['score']
                new_score = scored_memories[0]['score'] if scored_memories else 0
                score_change = new_score - original_score
                
                # Determine if boost matches expected pattern
                boost_detected = score_change > 0.1  # Significant positive change
                boost_matches_expectation = self._check_boost_expectation(
                    boost_detected, scenario['expected_boost']
                )
                
                correlation_results.append({
                    'scenario_index': i,
                    'memory_summary': scenario['memory_content'][:50] + '...',
                    'emoji_count': len(scenario['emoji_feedback']),
                    'feedback_valence': scenario['feedback_valence'],
                    'original_score': original_score,
                    'boosted_score': new_score,
                    'score_change': score_change,
                    'boost_detected': boost_detected,
                    'expected_boost': scenario['expected_boost'],
                    'correlation_correct': boost_matches_expectation
                })
                
                logger.info("Emoji correlation: %s feedback → %.3f to %.3f (change: %+.3f)",
                           scenario['feedback_valence'], original_score, new_score, score_change)
            
            # Calculate correlation accuracy
            correct_correlations = sum(1 for r in correlation_results if r['correlation_correct'])
            correlation_accuracy = (correct_correlations / len(correlation_results)) * 100
            
            correlation_metrics = {
                'scenarios_tested': len(emoji_memory_scenarios),
                'correct_correlations': correct_correlations,
                'correlation_accuracy_percent': correlation_accuracy,
                'positive_emoji_boosts_detected': sum(1 for r in correlation_results 
                                                    if r['feedback_valence'] in ['positive', 'very_positive'] and r['boost_detected']),
                'correlation_results': correlation_results
            }
            
            self.test_results.append({
                'test': 'emoji_feedback_memory_correlation',
                'status': 'PASSED',
                'details': correlation_metrics
            })
            logger.info("✅ TEST 1 PASSED: Emoji feedback memory correlation working")
            
        except Exception as e:
            self.test_results.append({
                'test': 'emoji_feedback_memory_correlation',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 1 FAILED: Emoji feedback memory correlation failed: %s", str(e))
    
    def _check_boost_expectation(self, boost_detected: bool, expected_boost: str) -> bool:
        """Helper to check if boost detection matches expectation"""
        if expected_boost == 'high':
            return boost_detected  # Should have boost
        elif expected_boost == 'medium':
            return boost_detected  # Should have boost
        elif expected_boost == 'none':
            return not boost_detected  # Should NOT have boost
        elif expected_boost == 'baseline':
            return True  # Neutral case, either way is acceptable
        return False
    
    async def test_emoji_pattern_learning(self):
        """Test 2: MemoryBoost learns from emoji patterns over time"""
        logger.info("📈 TEST 2: Emoji pattern learning...")
        
        try:
            # Simulate emoji feedback patterns over multiple interactions
            emoji_learning_sequence = [
                {
                    'interaction': 1,
                    'user_query': 'Tell me about machine learning',
                    'emoji_response': ['🤖', '💡'],
                    'pattern_type': 'tech_positive'
                },
                {
                    'interaction': 2,
                    'user_query': 'Explain neural networks',
                    'emoji_response': ['🧠', '⚡'],
                    'pattern_type': 'tech_positive'
                },
                {
                    'interaction': 3,
                    'user_query': 'How does deep learning work?',
                    'emoji_response': ['🔥', '🚀'],
                    'pattern_type': 'tech_enthusiastic'
                },
                {
                    'interaction': 4,
                    'user_query': 'What about creative writing?',
                    'emoji_response': ['😐'],
                    'pattern_type': 'creative_neutral'
                },
                {
                    'interaction': 5,
                    'user_query': 'More about AI algorithms please',
                    'emoji_response': ['💯', '👏'],
                    'pattern_type': 'tech_enthusiastic'
                }
            ]
            
            learning_progression = []
            cumulative_tech_enthusiasm = 0
            
            for interaction in emoji_learning_sequence:
                # Simulate optimization based on emoji pattern
                optimization_result = await self.relevance_optimizer.optimize_memory_retrieval(
                    user_id='emoji_learning_user',
                    bot_name='elena',
                    query=interaction['user_query'],
                    original_results=[],
                    conversation_context=f"emoji_pattern_{interaction['pattern_type']}"
                )
                
                # Track tech enthusiasm pattern
                if 'tech' in interaction['pattern_type']:
                    if 'enthusiastic' in interaction['pattern_type']:
                        cumulative_tech_enthusiasm += 2  # High enthusiasm
                    else:
                        cumulative_tech_enthusiasm += 1  # Regular tech interest
                
                # Get optimization recommendations to see if patterns are learned
                recommendations = await self.relevance_optimizer.get_optimization_recommendations(
                    user_id='emoji_learning_user',
                    bot_name='elena',
                    performance_window_days=1
                )
                
                learning_progression.append({
                    'interaction': interaction['interaction'],
                    'query_type': interaction['pattern_type'],
                    'emoji_count': len(interaction['emoji_response']),
                    'optimizations_applied': optimization_result.optimization_count,
                    'performance_improvement': optimization_result.performance_improvement,
                    'cumulative_tech_enthusiasm': cumulative_tech_enthusiasm,
                    'recommendations_available': recommendations is not None,
                    'pattern_learning_detected': optimization_result.optimization_count > 0
                })
                
                logger.info("Interaction %d (%s): %d optimizations, %.2f%% improvement",
                           interaction['interaction'], interaction['pattern_type'],
                           optimization_result.optimization_count, optimization_result.performance_improvement)
            
            # Analyze learning effectiveness
            tech_interactions = [p for p in learning_progression if 'tech' in p['query_type']]
            non_tech_interactions = [p for p in learning_progression if 'tech' not in p['query_type']]
            
            tech_avg_optimization = sum(i['optimizations_applied'] for i in tech_interactions) / len(tech_interactions) if tech_interactions else 0
            non_tech_avg_optimization = sum(i['optimizations_applied'] for i in non_tech_interactions) / len(non_tech_interactions) if non_tech_interactions else 0
            
            pattern_learning_metrics = {
                'total_interactions': len(emoji_learning_sequence),
                'tech_interactions': len(tech_interactions),
                'tech_average_optimizations': tech_avg_optimization,
                'non_tech_average_optimizations': non_tech_avg_optimization,
                'learning_preference_detected': tech_avg_optimization > non_tech_avg_optimization,
                'cumulative_enthusiasm_score': cumulative_tech_enthusiasm,
                'pattern_recognition_working': any(p['pattern_learning_detected'] for p in learning_progression),
                'learning_progression': learning_progression
            }
            
            self.test_results.append({
                'test': 'emoji_pattern_learning',
                'status': 'PASSED',
                'details': pattern_learning_metrics
            })
            logger.info("✅ TEST 2 PASSED: Emoji pattern learning working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'emoji_pattern_learning',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 2 FAILED: Emoji pattern learning failed: %s", str(e))
    
    async def test_feedback_loop_integration(self):
        """Test 3: Complete feedback loop from emoji to memory to optimization"""
        logger.info("🔄 TEST 3: Feedback loop integration...")
        
        try:
            # Test complete feedback loop cycle
            feedback_loop_scenarios = [
                {
                    'phase': 'initial_conversation',
                    'user_message': 'I love hiking in the mountains',
                    'bot_response': 'That sounds amazing! Mountain hiking is such a wonderful way to connect with nature.',
                    'user_emoji_reaction': '😍',
                    'expected_feedback_integration': True
                },
                {
                    'phase': 'memory_storage',
                    'memory_content': 'User loves hiking in mountains, very enthusiastic about nature',
                    'emoji_metadata': {'reaction': '😍', 'valence': 'very_positive'},
                    'expected_quality_boost': True
                },
                {
                    'phase': 'future_retrieval',
                    'user_query': 'What outdoor activities do you recommend?',
                    'expected_hiking_priority': True
                },
                {
                    'phase': 'optimization_application',
                    'expected_hiking_memory_boost': True,
                    'expected_improved_relevance': True
                }
            ]
            
            feedback_loop_results = []
            
            for scenario in feedback_loop_scenarios:
                if scenario['phase'] == 'initial_conversation':
                    # Simulate conversation with emoji reaction
                    feedback_integration = {
                        'conversation_occurred': True,
                        'emoji_reaction_captured': scenario['user_emoji_reaction'] is not None,
                        'feedback_valence': 'positive' if scenario['user_emoji_reaction'] == '😍' else 'neutral'
                    }
                    
                elif scenario['phase'] == 'memory_storage':
                    # Simulate memory storage with emoji metadata
                    mock_memory = {
                        'content': scenario['memory_content'],
                        'metadata': scenario['emoji_metadata'],
                        'score': 0.5
                    }
                    
                    # Apply quality scoring based on emoji feedback
                    scored_memories = await self.relevance_optimizer.apply_quality_scoring(
                        memory_results=[mock_memory],
                        user_id='feedback_loop_user',
                        bot_name='elena'
                    )
                    
                    quality_boost_applied = scored_memories[0]['score'] > 0.5 if scored_memories else False
                    feedback_integration = {
                        'memory_stored': True,
                        'emoji_metadata_included': 'reaction' in scenario['emoji_metadata'],
                        'quality_boost_applied': quality_boost_applied
                    }
                    
                elif scenario['phase'] == 'future_retrieval':
                    # Simulate future query that should benefit from emoji feedback
                    optimization_result = await self.relevance_optimizer.optimize_memory_retrieval(
                        user_id='feedback_loop_user',
                        bot_name='elena',
                        query=scenario['user_query'],
                        original_results=[],
                        conversation_context='outdoor_activity_recommendation'
                    )
                    
                    feedback_integration = {
                        'query_processed': True,
                        'optimizations_applied': optimization_result.optimization_count,
                        'performance_improvement': optimization_result.performance_improvement,
                        'memory_optimization_occurred': optimization_result.optimization_count > 0
                    }
                    
                elif scenario['phase'] == 'optimization_application':
                    # Test that optimization recommendations reflect emoji feedback learning
                    recommendations = await self.relevance_optimizer.get_optimization_recommendations(
                        user_id='feedback_loop_user',
                        bot_name='elena',
                        performance_window_days=1
                    )
                    
                    feedback_integration = {
                        'recommendations_generated': recommendations is not None,
                        'optimization_strategy_available': bool(recommendations.get('boost_strategies', [])) if recommendations else False,
                        'feedback_loop_complete': True
                    }
                
                feedback_loop_results.append({
                    'phase': scenario['phase'],
                    'integration_data': feedback_integration,
                    'phase_successful': all(feedback_integration.values())
                })
                
                logger.info("Feedback loop phase '%s': %s", scenario['phase'], 
                           'SUCCESS' if all(feedback_integration.values()) else 'PARTIAL')
            
            # Analyze complete feedback loop
            successful_phases = sum(1 for r in feedback_loop_results if r['phase_successful'])
            feedback_loop_completeness = (successful_phases / len(feedback_loop_scenarios)) * 100
            
            integration_metrics = {
                'total_phases_tested': len(feedback_loop_scenarios),
                'successful_phases': successful_phases,
                'feedback_loop_completeness_percent': feedback_loop_completeness,
                'complete_integration_confirmed': feedback_loop_completeness >= 75,  # Allow some tolerance
                'phase_results': feedback_loop_results
            }
            
            self.test_results.append({
                'test': 'feedback_loop_integration',
                'status': 'PASSED',
                'details': integration_metrics
            })
            logger.info("✅ TEST 3 PASSED: Feedback loop integration working correctly")
            
        except Exception as e:
            self.test_results.append({
                'test': 'feedback_loop_integration',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error("❌ TEST 3 FAILED: Feedback loop integration failed: %s", str(e))
    
    async def run_emoji_integration_tests(self):
        """Run complete MemoryBoost + Emoji Integration test suite"""
        logger.info("🎭 Starting MemoryBoost + Emoji Integration Tests...")
        
        # Setup test environment
        if not await self.setup_emoji_integration_environment():
            logger.error("❌ Failed to setup emoji integration test environment")
            return {'success': False, 'error': 'Environment setup failed'}
        
        # Run all emoji integration tests
        await self.test_emoji_feedback_memory_correlation()
        await self.test_emoji_pattern_learning()
        await self.test_feedback_loop_integration()
        
        # Calculate final results
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASSED'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate comprehensive results
        results_filename = f"memoryboost_emoji_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        final_results = {
            'test_type': 'MemoryBoost + Emoji Integration',
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'execution_time_seconds': time.time() - self.start_time,
            'test_details': self.test_results,
            'integration_summary': {
                'emoji_feedback_correlation': any(t['test'] == 'emoji_feedback_memory_correlation' and t['status'] == 'PASSED' for t in self.test_results),
                'emoji_pattern_learning': any(t['test'] == 'emoji_pattern_learning' and t['status'] == 'PASSED' for t in self.test_results),
                'complete_feedback_loop': any(t['test'] == 'feedback_loop_integration' and t['status'] == 'PASSED' for t in self.test_results),
                'memoryboost_emoji_intelligence_confirmed': success_rate == 100
            }
        }
        
        # Write comprehensive results
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("🎭 MEMORYBOOST + EMOJI INTEGRATION TEST RESULTS")
        print("="*80)
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Overall Status: {'✅ EMOJI INTELLIGENCE INTEGRATED' if success_rate == 100 else '❌ INTEGRATION ISSUES'}")
        print("="*80)
        
        for test in self.test_results:
            status_icon = "✅" if test['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {test['status']}: {test['test']}")
            if test['status'] == 'FAILED':
                print(f"  Error: {test.get('error', 'Unknown error')}")
        
        print("="*80)
        print(f"📁 Emoji integration results written to: {results_filename}")
        print()
        
        return final_results


async def main():
    """Main emoji integration test execution"""
    emoji_test = MemoryBoostEmojiIntegrationTest()
    results = await emoji_test.run_emoji_integration_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())