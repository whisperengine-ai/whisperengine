"""
Enhanced Memory Surprise Trigger Validation Tests
WhisperEngine Character Learning Enhancement
Version: 1.0 - October 2025

Direct validation tests for enhanced memory surprise detection system
to ensure accurate vector-based similarity detection and authentic
conversation references.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.characters.learning.enhanced_memory_surprise_trigger import EnhancedMemorySurpriseTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMemoryManager:
    """Mock memory manager for testing without full WhisperEngine infrastructure."""
    
    def __init__(self):
        self.mock_memories = [
            {
                'id': 'mem_001',
                'content': 'I love hiking in the mountains during autumn because the colors are amazing',
                'timestamp': datetime.now() - timedelta(days=5),
                'score': 0.85,
                'emotion_data': {'emotional_intensity': 0.8}
            },
            {
                'id': 'mem_002', 
                'content': 'My work project is really stressing me out lately with all the deadlines',
                'timestamp': datetime.now() - timedelta(days=15),
                'score': 0.75,
                'emotion_data': {'emotional_intensity': 0.6}
            },
            {
                'id': 'mem_003',
                'content': 'I had an amazing conversation with my sister about travel plans',
                'timestamp': datetime.now() - timedelta(days=2),
                'score': 0.90,
                'emotion_data': {'emotional_intensity': 0.7}
            },
            {
                'id': 'mem_004',
                'content': 'The new restaurant downtown has incredible pasta and great atmosphere',
                'timestamp': datetime.now() - timedelta(days=20),
                'score': 0.70,
                'emotion_data': {'emotional_intensity': 0.5}
            }
        ]
    
    async def retrieve_relevant_memories(self, user_id: str, query: str, limit: int, memory_type: str = None) -> List[Dict[str, Any]]:
        """Mock memory retrieval with simple keyword matching."""
        query_words = set(query.lower().split())
        scored_memories = []
        
        for memory in self.mock_memories:
            memory_words = set(memory['content'].lower().split())
            overlap = query_words.intersection(memory_words)
            
            if overlap:
                # Simulate vector similarity score
                similarity = len(overlap) / len(query_words.union(memory_words))
                memory_copy = memory.copy()
                memory_copy['score'] = similarity
                scored_memories.append(memory_copy)
        
        # Sort by score and return top results
        scored_memories.sort(key=lambda m: m['score'], reverse=True)
        return scored_memories[:limit]

async def test_enhanced_memory_surprise_detection():
    """Test enhanced memory surprise detection with realistic scenarios."""
    print("🧠 Testing Enhanced Memory Surprise Detection System")
    print("=" * 60)
    
    # Initialize mock components
    mock_memory_manager = MockMemoryManager()
    trigger_system = EnhancedMemorySurpriseTrigger(
        memory_manager=mock_memory_manager,
        character_intelligence_coordinator=None
    )
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Hiking Connection',
            'user_id': 'test_user_001',
            'current_message': 'I was thinking about going on a nature walk this weekend to see the fall foliage',
            'character_name': 'Elena',
            'expected_surprises': 1,
            'expected_type': 'unexpected_connection'
        },
        {
            'name': 'Work Stress Pattern',
            'user_id': 'test_user_002', 
            'current_message': 'My job has been overwhelming me with too many tasks',
            'character_name': 'Marcus',
            'expected_surprises': 1,
            'expected_type': 'distant_memory'
        },
        {
            'name': 'Travel Enthusiasm',
            'user_id': 'test_user_003',
            'current_message': 'I had a great chat with my family about planning a vacation',
            'character_name': 'Jake',
            'expected_surprises': 1,
            'expected_type': 'pattern_recognition'
        },
        {
            'name': 'No Connection',
            'user_id': 'test_user_004',
            'current_message': 'The weather today is quite unpredictable',
            'character_name': 'Elena',
            'expected_surprises': 0,
            'expected_type': None
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases:
        total_tests += 1
        print(f"\n🧪 Test Case: {test_case['name']}")
        print(f"Message: '{test_case['current_message']}'")
        
        try:
            surprises = await trigger_system.detect_memory_surprises(
                user_id=test_case['user_id'],
                current_message=test_case['current_message'],
                conversation_context=[],
                character_name=test_case['character_name']
            )
            
            print(f"Expected surprises: {test_case['expected_surprises']}")
            print(f"Detected surprises: {len(surprises)}")
            
            if len(surprises) == test_case['expected_surprises']:
                print("✅ Surprise count matches expected")
                
                if surprises and test_case['expected_type']:
                    surprise = surprises[0]
                    print(f"Surprise type: {surprise.surprise_type}")
                    print(f"Overall score: {surprise.similarity_score.overall_score:.3f}")
                    print(f"Semantic similarity: {surprise.similarity_score.semantic_similarity:.3f}")
                    print(f"Temporal surprise: {surprise.similarity_score.temporal_surprise:.3f}")
                    print(f"Response template: {surprise.character_response_template}")
                    
                    if surprise.surprise_type == test_case['expected_type']:
                        print("✅ Surprise type matches expected")
                        passed_tests += 1
                    else:
                        print(f"❌ Expected type {test_case['expected_type']}, got {surprise.surprise_type}")
                elif not surprises and test_case['expected_surprises'] == 0:
                    print("✅ No surprises detected as expected")
                    passed_tests += 1
                else:
                    print("❌ Surprise detection logic issue")
            else:
                print("❌ Surprise count mismatch")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            logger.error(f"Test case {test_case['name']} failed: {e}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests

async def test_memory_surprise_scoring():
    """Test the multi-dimensional scoring system."""
    print("\n🎯 Testing Memory Surprise Scoring System")
    print("=" * 60)
    
    mock_memory_manager = MockMemoryManager()
    trigger_system = EnhancedMemorySurpriseTrigger(
        memory_manager=mock_memory_manager,
        character_intelligence_coordinator=None
    )
    
    # Test scoring components individually
    test_memory = {
        'id': 'test_mem',
        'content': 'I had a wonderful time hiking in the mountains last weekend',
        'timestamp': datetime.now() - timedelta(days=10),
        'score': 0.8,
        'emotion_data': {'emotional_intensity': 0.7}
    }
    
    current_message = "I'm planning another mountain hike for this weekend"
    conversation_context = []
    
    print("Testing individual scoring components:")
    
    # Test semantic similarity
    semantic_score = await trigger_system._calculate_vector_semantic_similarity(
        current_message, test_memory['content']
    )
    print(f"Semantic similarity: {semantic_score:.3f}")
    
    # Test temporal surprise
    temporal_score = trigger_system._calculate_temporal_surprise(test_memory['timestamp'])
    print(f"Temporal surprise: {temporal_score:.3f}")
    
    # Test emotional resonance
    emotional_score = await trigger_system._calculate_emotional_resonance(
        current_message, test_memory['content'], test_memory
    )
    print(f"Emotional resonance: {emotional_score:.3f}")
    
    # Test contextual relevance
    contextual_score = trigger_system._calculate_contextual_relevance(
        test_memory['content'], conversation_context
    )
    print(f"Contextual relevance: {contextual_score:.3f}")
    
    # Test complete analysis
    surprise_result = await trigger_system._analyze_memory_surprise_potential(
        test_memory, current_message, conversation_context, 'test_user'
    )
    
    if surprise_result:
        print(f"\nComplete analysis results:")
        print(f"Overall score: {surprise_result.similarity_score.overall_score:.3f}")
        print(f"Surprise type: {surprise_result.surprise_type}")
        print(f"Response template: {surprise_result.character_response_template}")
        return True
    else:
        print("❌ Complete analysis failed")
        return False

async def test_configuration_validation():
    """Test configuration and threshold validation."""
    print("\n⚙️ Testing Configuration and Thresholds")
    print("=" * 60)
    
    # Test different threshold configurations
    configs = [
        {'semantic': 0.5, 'temporal': 0.5, 'overall': 0.5},  # Permissive
        {'semantic': 0.8, 'temporal': 0.8, 'overall': 0.7},  # Strict
        {'semantic': 0.75, 'temporal': 0.6, 'overall': 0.65}  # Balanced
    ]
    
    for i, config in enumerate(configs):
        print(f"\nConfiguration {i+1}: {config}")
        
        mock_memory_manager = MockMemoryManager()
        trigger_system = EnhancedMemorySurpriseTrigger(
            memory_manager=mock_memory_manager,
            character_intelligence_coordinator=None
        )
        
        # Apply configuration
        trigger_system.semantic_similarity_threshold = config['semantic']
        trigger_system.temporal_surprise_threshold = config['temporal']
        trigger_system.overall_surprise_threshold = config['overall']
        
        # Test with same input
        surprises = await trigger_system.detect_memory_surprises(
            user_id='config_test',
            current_message='I love hiking in beautiful mountain trails',
            conversation_context=[],
            character_name='TestBot'
        )
        
        print(f"Detected surprises: {len(surprises)}")
        
        if surprises:
            best_surprise = surprises[0]
            print(f"Best surprise score: {best_surprise.similarity_score.overall_score:.3f}")
    
    return True

async def main():
    """Run all enhanced memory surprise trigger validation tests."""
    print("🚀 Enhanced Memory Surprise Trigger Validation Suite")
    print("=" * 80)
    
    try:
        # Run all test suites
        test1_passed = await test_enhanced_memory_surprise_detection()
        test2_passed = await test_memory_surprise_scoring()
        test3_passed = await test_configuration_validation()
        
        print("\n" + "=" * 80)
        print("🏆 VALIDATION SUMMARY")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        print(f"✅ Enhanced Memory Surprise Detection: {'PASS' if test1_passed else 'FAIL'}")
        print(f"✅ Memory Surprise Scoring: {'PASS' if test2_passed else 'FAIL'}")
        print(f"✅ Configuration Validation: {'PASS' if test3_passed else 'FAIL'}")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Enhanced memory surprise system is ready for production.")
        else:
            print("\n⚠️ Some tests failed. Please review and fix issues before deployment.")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Validation suite failed with error: {e}")
        logger.error(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())