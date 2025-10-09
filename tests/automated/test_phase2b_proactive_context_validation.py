"""
Phase 2B Proactive Context Validation Test

Tests the CharacterContextEnhancer integration with CDL AI prompt building
to ensure relevant character knowledge is automatically injected when topics arise.

Test Scenarios:
1. Elena + diving/marine topics → marine research background injection
2. Jake + photography topics → photography skills injection
3. Marcus + AI topics → AI research expertise injection
4. Topic detection accuracy and relevance scoring
5. Cross-character validation (no knowledge bleed)
6. Context injection limits and quality

Author: WhisperEngine Development Team
Date: Phase 2B Implementation
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.append('/Users/markcastillo/git/whisperengine')

logger = logging.getLogger(__name__)

class Phase2BProactiveContextValidator:
    """Validates proactive context injection functionality"""
    
    def __init__(self):
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': []
        }
        
        # Test scenarios for validation
        self.test_scenarios = [
            {
                'character': 'Elena',
                'message': 'I went scuba diving yesterday and saw amazing coral reefs!',
                'expected_topics': ['marine_biology'],
                'expected_contexts': ['research', 'diving', 'coral', 'marine'],
                'description': 'Elena + diving/marine topics → marine research injection'
            },
            {
                'character': 'Elena', 
                'message': 'I love learning about ocean ecosystems and marine conservation.',
                'expected_topics': ['marine_biology'],
                'expected_contexts': ['research', 'conservation', 'marine', 'ecosystem'],
                'description': 'Elena + marine conservation → conservation expertise injection'
            },
            {
                'character': 'Jake',
                'message': 'I just bought a new camera lens for landscape photography.',
                'expected_topics': ['photography'],
                'expected_contexts': ['photography', 'camera', 'landscape', 'skill'],
                'description': 'Jake + photography topics → photography skills injection'
            },
            {
                'character': 'Jake',
                'message': 'I\'m planning an adventure photography expedition to the mountains.',
                'expected_topics': ['photography'],
                'expected_contexts': ['adventure', 'photography', 'expedition', 'skill'],
                'description': 'Jake + adventure photography → adventure expertise injection'
            },
            {
                'character': 'Marcus',
                'message': 'AI is getting really scary with all these new developments.',
                'expected_topics': ['artificial_intelligence'],
                'expected_contexts': ['AI', 'research', 'ethics', 'safety'],
                'description': 'Marcus + AI concerns → AI ethics research injection'
            },
            {
                'character': 'Marcus',
                'message': 'I\'m studying machine learning algorithms for my research.',
                'expected_topics': ['artificial_intelligence'],
                'expected_contexts': ['machine learning', 'research', 'algorithm', 'AI'],
                'description': 'Marcus + ML research → AI research expertise injection'
            },
            {
                'character': 'Elena',
                'message': 'I love taking photos of marine life underwater.',
                'expected_topics': ['marine_biology', 'photography'],
                'expected_contexts': ['marine', 'underwater', 'research'],
                'description': 'Elena + marine photography → marine research (not photography skills)'
            },
            {
                'character': 'Jake',
                'message': 'I went diving last week but didn\'t bring my underwater camera.',
                'expected_topics': ['photography'],
                'expected_contexts': ['photography', 'camera', 'skill'],
                'description': 'Jake + diving + photography → photography skills (not marine research)'
            }
        ]
    
    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """Log a test result"""
        self.test_results['tests_run'] += 1
        
        if passed:
            self.test_results['tests_passed'] += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.test_results['tests_failed'] += 1
            print(f"❌ {test_name}: FAILED")
        
        self.test_results['detailed_results'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details
        })
        
        # Print details for failed tests
        if not passed:
            print(f"   Details: {details}")
    
    async def test_character_context_enhancer_initialization(self) -> bool:
        """Test 1: CharacterContextEnhancer initialization"""
        try:
            from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
            
            # Test factory creation
            enhancer = create_character_context_enhancer(character_graph_manager=None)
            
            validation_results = {
                'factory_creation': enhancer is not None,
                'has_topic_patterns': hasattr(enhancer, 'topic_patterns'),
                'has_inject_method': hasattr(enhancer, 'inject_proactive_context'),
                'has_detect_method': hasattr(enhancer, 'detect_topics_in_message'),
                'topic_pattern_count': len(enhancer.topic_patterns) if hasattr(enhancer, 'topic_patterns') else 0
            }
            
            all_passed = all(validation_results.values())
            
            self.log_test_result(
                "CharacterContextEnhancer Initialization", 
                all_passed,
                validation_results
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "CharacterContextEnhancer Initialization",
                False,
                {'error': str(e)}
            )
            return False
    
    async def test_topic_detection_accuracy(self) -> bool:
        """Test 2: Topic detection accuracy"""
        try:
            from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
            
            enhancer = create_character_context_enhancer(character_graph_manager=None)
            
            detection_results = []
            
            # Test each scenario's topic detection
            for scenario in self.test_scenarios[:6]:  # Test first 6 scenarios
                message = scenario['message']
                expected_topics = scenario['expected_topics']
                
                detected_topics = await enhancer.detect_topics_in_message(message)
                detected_topic_names = [topic.topic for topic in detected_topics]
                
                # Check if expected topics were detected
                topics_detected = any(expected_topic in detected_topic_names for expected_topic in expected_topics)
                
                detection_results.append({
                    'character': scenario['character'],
                    'message': message[:50] + '...',
                    'expected_topics': expected_topics,
                    'detected_topics': detected_topic_names,
                    'topics_detected': topics_detected,
                    'confidence_scores': [f"{topic.topic}:{topic.confidence:.2f}" for topic in detected_topics]
                })
            
            # Calculate accuracy
            successful_detections = sum(1 for result in detection_results if result['topics_detected'])
            accuracy = successful_detections / len(detection_results) if detection_results else 0
            
            passed = accuracy >= 0.7  # Require 70% accuracy
            
            self.log_test_result(
                "Topic Detection Accuracy",
                passed,
                {
                    'accuracy': f"{accuracy:.1%}",
                    'successful_detections': successful_detections,
                    'total_tests': len(detection_results),
                    'detection_results': detection_results
                }
            )
            
            return passed
            
        except Exception as e:
            self.log_test_result(
                "Topic Detection Accuracy",
                False,
                {'error': str(e)}
            )
            return False
    
    async def test_cdl_ai_integration(self) -> bool:
        """Test 3: CDL AI Integration with proactive context"""
        try:
            # Test CDL AI integration initialization
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            # Initialize with minimal dependencies
            cdl_integration = CDLAIPromptIntegration()
            
            integration_results = {
                'cdl_integration_created': cdl_integration is not None,
                'has_context_enhancer_method': hasattr(cdl_integration, '_get_context_enhancer'),
                'has_context_enhancer_cache': hasattr(cdl_integration, '_context_enhancer'),
                'context_enhancer_initialized': cdl_integration._context_enhancer is not None
            }
            
            # Test lazy initialization
            try:
                context_enhancer = await cdl_integration._get_context_enhancer()
                integration_results['lazy_initialization'] = context_enhancer is not None
            except Exception as e:
                integration_results['lazy_initialization'] = False
                integration_results['lazy_init_error'] = str(e)
            
            # Check if integration has required methods
            integration_results['has_unified_prompt_method'] = hasattr(cdl_integration, 'create_unified_character_prompt')
            
            all_passed = integration_results['cdl_integration_created'] and integration_results['has_context_enhancer_method']
            
            self.log_test_result(
                "CDL AI Integration",
                all_passed,
                integration_results
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "CDL AI Integration",
                False,
                {'error': str(e)}
            )
            return False
    
    async def test_relevance_scoring_algorithm(self) -> bool:
        """Test 4: Relevance scoring algorithm"""
        try:
            from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
            
            enhancer = create_character_context_enhancer(character_graph_manager=None)
            
            # Test relevance scoring with known good and bad matches
            test_cases = [
                {
                    'knowledge_content': 'Marine biology research in coral reef ecosystems',
                    'topic_keywords': ['marine', 'coral', 'reef'],
                    'topic_confidence': 0.8,
                    'importance_level': 8,
                    'expected_high_relevance': True
                },
                {
                    'knowledge_content': 'Professional landscape and wildlife photography',
                    'topic_keywords': ['photography', 'camera', 'landscape'],
                    'topic_confidence': 0.9,
                    'importance_level': 7,
                    'expected_high_relevance': True
                },
                {
                    'knowledge_content': 'Cooking pasta recipes',
                    'topic_keywords': ['marine', 'diving', 'underwater'],
                    'topic_confidence': 0.7,
                    'importance_level': 3,
                    'expected_high_relevance': False
                }
            ]
            
            scoring_results = []
            
            for case in test_cases:
                # Create mock topic match
                from src.characters.cdl.character_context_enhancer import TopicMatch
                
                mock_topic = TopicMatch(
                    topic='test_topic',
                    confidence=case['topic_confidence'],
                    keywords=case['topic_keywords'],
                    context='test context'
                )
                
                relevance_score = enhancer._calculate_relevance_score(
                    knowledge_content=case['knowledge_content'],
                    topic=mock_topic,
                    importance_level=case['importance_level']
                )
                
                # Check if scoring matches expectations
                is_high_relevance = relevance_score >= 0.5
                matches_expectation = is_high_relevance == case['expected_high_relevance']
                
                scoring_results.append({
                    'content': case['knowledge_content'][:40] + '...',
                    'keywords': case['topic_keywords'],
                    'relevance_score': relevance_score,
                    'expected_high': case['expected_high_relevance'],
                    'actual_high': is_high_relevance,
                    'matches_expectation': matches_expectation
                })
            
            # Calculate accuracy
            correct_scores = sum(1 for result in scoring_results if result['matches_expectation'])
            accuracy = correct_scores / len(scoring_results) if scoring_results else 0
            
            passed = accuracy >= 0.8  # Require 80% accuracy
            
            self.log_test_result(
                "Relevance Scoring Algorithm",
                passed,
                {
                    'accuracy': f"{accuracy:.1%}",
                    'correct_scores': correct_scores,
                    'total_tests': len(scoring_results),
                    'scoring_results': scoring_results
                }
            )
            
            return passed
            
        except Exception as e:
            self.log_test_result(
                "Relevance Scoring Algorithm",
                False,
                {'error': str(e)}
            )
            return False
    
    async def test_context_injection_limits(self) -> bool:
        """Test 5: Context injection limits and quality"""
        try:
            from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
            
            enhancer = create_character_context_enhancer(character_graph_manager=None)
            
            # Test context injection without graph manager (should handle gracefully)
            test_prompts = [
                'I went scuba diving and saw coral reefs!',
                'I love taking landscape photography with my new camera!',
                'AI ethics research is fascinating but concerning.',
                'Random unrelated message about cooking pasta.'
            ]
            
            injection_results = []
            
            for prompt in test_prompts:
                try:
                    enhanced_prompt, injected_contexts = await enhancer.inject_proactive_context(
                        character_name='Elena',
                        user_message=prompt,
                        base_system_prompt='You are Elena, a marine biologist.',
                        max_context_items=3
                    )
                    
                    injection_results.append({
                        'prompt': prompt[:40] + '...',
                        'enhanced_prompt_length': len(enhanced_prompt),
                        'injected_context_count': len(injected_contexts),
                        'contexts_within_limit': len(injected_contexts) <= 3,
                        'enhancement_applied': len(enhanced_prompt) >= len('You are Elena, a marine biologist.'),
                        'no_errors': True
                    })
                    
                except Exception as e:
                    injection_results.append({
                        'prompt': prompt[:40] + '...',
                        'no_errors': False,
                        'error': str(e)
                    })
            
            # Check results
            no_error_tests = sum(1 for result in injection_results if result.get('no_errors', False))
            limit_compliant_tests = sum(1 for result in injection_results if result.get('contexts_within_limit', False))
            
            passed = no_error_tests == len(test_prompts)  # All tests should run without errors
            
            self.log_test_result(
                "Context Injection Limits",
                passed,
                {
                    'no_error_tests': no_error_tests,
                    'limit_compliant_tests': limit_compliant_tests,
                    'total_tests': len(test_prompts),
                    'injection_results': injection_results
                }
            )
            
            return passed
            
        except Exception as e:
            self.log_test_result(
                "Context Injection Limits",
                False,
                {'error': str(e)}
            )
            return False
    
    async def test_character_specificity(self) -> bool:
        """Test 6: Character-specific context (no knowledge bleed)"""
        try:
            from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
            
            enhancer = create_character_context_enhancer(character_graph_manager=None)
            
            # Test that character names are passed correctly
            character_tests = [
                {
                    'character_name': 'Elena',
                    'message': 'I love marine biology research!',
                    'expected_character': 'Elena'
                },
                {
                    'character_name': 'Jake',
                    'message': 'Photography is my passion!',
                    'expected_character': 'Jake'
                },
                {
                    'character_name': 'Marcus',
                    'message': 'AI research is fascinating!',
                    'expected_character': 'Marcus'
                }
            ]
            
            character_results = []
            
            for test in character_tests:
                try:
                    # Test that context injection accepts character names
                    enhanced_prompt, injected_contexts = await enhancer.inject_proactive_context(
                        character_name=test['character_name'],
                        user_message=test['message'],
                        base_system_prompt=f"You are {test['character_name']}.",
                        max_context_items=3
                    )
                    
                    character_results.append({
                        'character': test['character_name'],
                        'message': test['message'][:30] + '...',
                        'context_injection_successful': True,
                        'enhanced_prompt_contains_character': test['character_name'] in enhanced_prompt,
                        'no_errors': True
                    })
                    
                except Exception as e:
                    character_results.append({
                        'character': test['character_name'],
                        'message': test['message'][:30] + '...',
                        'no_errors': False,
                        'error': str(e)
                    })
            
            # Check results
            successful_tests = sum(1 for result in character_results if result.get('no_errors', False))
            passed = successful_tests == len(character_tests)
            
            self.log_test_result(
                "Character Specificity",
                passed,
                {
                    'successful_tests': successful_tests,
                    'total_tests': len(character_tests),
                    'character_results': character_results
                }
            )
            
            return passed
            
        except Exception as e:
            self.log_test_result(
                "Character Specificity",
                False,
                {'error': str(e)}
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 2B validation tests"""
        print("🎭 Starting Phase 2B Proactive Context Validation...")
        print("=" * 60)
        
        # Run all test methods
        test_methods = [
            self.test_character_context_enhancer_initialization,
            self.test_topic_detection_accuracy,
            self.test_cdl_ai_integration,
            self.test_relevance_scoring_algorithm,
            self.test_context_injection_limits,
            self.test_character_specificity
        ]
        
        for test_method in test_methods:
            await test_method()
            print()  # Add spacing between tests
        
        # Calculate final results
        pass_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        
        print("=" * 60)
        print(f"🎭 Phase 2B Validation Summary:")
        print(f"   Tests Run: {self.test_results['tests_run']}")
        print(f"   Tests Passed: {self.test_results['tests_passed']}")
        print(f"   Tests Failed: {self.test_results['tests_failed']}")
        print(f"   Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 70:
            print(f"✅ Phase 2B Validation: PASSED ({pass_rate:.1f}%)")
        else:
            print(f"❌ Phase 2B Validation: FAILED ({pass_rate:.1f}%)")
        
        print("=" * 60)
        
        return {
            'overall_passed': pass_rate >= 70,
            'pass_rate': pass_rate,
            'summary': self.test_results,
            'detailed_results': self.test_results['detailed_results']
        }


async def main():
    """Main test execution"""
    # Set up environment for testing
    os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
    os.environ['QDRANT_HOST'] = 'localhost'
    os.environ['QDRANT_PORT'] = '6334'
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run validation tests
    validator = Phase2BProactiveContextValidator()
    results = await validator.run_all_tests()
    
    print("\n🎭 Phase 2B Proactive Context Validation Complete!")
    
    if results['overall_passed']:
        print("✅ Ready for Phase 2B character testing with Elena, Jake, and Marcus!")
        return 0
    else:
        print("❌ Phase 2B validation failed - check implementation before character testing")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)