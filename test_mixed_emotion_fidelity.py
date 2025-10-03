#!/usr/bin/env python3
"""
Mixed Emotion Fidelity Test for WhisperEngine
============================================

Tests the enhanced mixed emotion embedding system to ensure we preserve
RoBERTa's multi-emotion analysis in vector embeddings.

This validates that the system can:
1. Store mixed emotion data with fidelity-preserving embeddings
2. Retrieve memories using complex emotional queries
3. Understand emotional nuance like "excited but nervous" or "bittersweet joy"

Usage:
    python test_mixed_emotion_fidelity.py
"""

import asyncio
import logging
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

def main():
    print("🎭 Mixed Emotion Fidelity Test for WhisperEngine")
    print("=" * 55)
    
    # Load environment
    load_dotenv()
    
    # Run async test
    asyncio.run(test_mixed_emotion_fidelity())

async def test_mixed_emotion_fidelity():
    """Test enhanced mixed emotion embedding system"""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("\n🔧 Setting up test environment...")
    
    try:
        # Import WhisperEngine components
        from src.memory.memory_protocol import create_memory_manager
        from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
        
        # Create memory manager (vector-based)
        memory_manager = create_memory_manager("vector")
        print("✅ Memory manager created")
        
        # Create emotion analyzer
        emotion_analyzer = EnhancedVectorEmotionAnalyzer()
        print("✅ Emotion analyzer created")
        
        # Test cases with known mixed emotions
        test_cases = [
            {
                "content": "I'm so excited about the new job but also terrified about moving to a new city!",
                "expected_primary": "joy",  # or "excitement"
                "expected_mixed": ["joy", "fear", "anxiety"],
                "description": "Excited but nervous"
            },
            {
                "content": "Watching my daughter graduate made me incredibly proud yet sad she's growing up so fast.",
                "expected_primary": "pride",
                "expected_mixed": ["pride", "joy", "sadness"],
                "description": "Bittersweet pride"
            },
            {
                "content": "I love this song but it always makes me cry thinking about my grandmother.",
                "expected_primary": "love",
                "expected_mixed": ["love", "sadness", "nostalgia"],
                "description": "Love with grief"
            },
            {
                "content": "I'm frustrated with the project delays but hopeful we can still deliver quality work.",
                "expected_primary": "anger",
                "expected_mixed": ["anger", "optimism", "determination"],
                "description": "Frustrated optimism"
            }
        ]
        
        print(f"\n🎭 Testing {len(test_cases)} mixed emotion scenarios...")
        
        test_results = []
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {case['description']} ---")
            print(f"Content: '{case['content']}'")
            
            try:
                # Step 1: Analyze emotion with RoBERTa
                print("🤖 Step 1: Analyzing emotions with RoBERTa...")
                emotion_result = await emotion_analyzer.analyze_emotion(
                    content=case['content'],
                    user_id="test_user_mixed_emotions"
                )
                
                print(f"Primary emotion: {emotion_result.primary_emotion}")
                print(f"All emotions: {emotion_result.all_emotions}")
                print(f"Confidence: {emotion_result.confidence:.3f}")
                
                # Step 2: Store memory and check embedding
                print("\n💾 Step 2: Storing memory with mixed emotion embedding...")
                
                # Store memory using the store_conversation method with emotion metadata
                memory_id = await memory_manager.store_conversation(
                    user_id="test_user_mixed_emotions",
                    user_message=case['content'],
                    bot_response="Test response for mixed emotion",
                    pre_analyzed_emotion_data={
                        'primary_emotion': emotion_result.primary_emotion,
                        'all_emotions': emotion_result.all_emotions,
                        'mixed_emotions': list(emotion_result.all_emotions.keys()),
                        'confidence': emotion_result.confidence,
                        'is_multi_emotion': len(emotion_result.all_emotions) > 1
                    }
                )
                print(f"✅ Memory stored with ID: {memory_id}")
                
                # Step 3: Test mixed emotion retrieval
                print("\n🔍 Step 3: Testing mixed emotion retrieval...")
                
                # Test queries that should find this memory
                test_queries = [
                    f"times when I felt {emotion_result.primary_emotion}",
                    f"mixed emotions about {case['description'].split()[0]}",
                    f"feeling {' and '.join(list(emotion_result.all_emotions.keys())[:2])}",
                    case['content'][:30] + "..."  # Partial content match
                ]
                
                retrieval_success = 0
                for query in test_queries:
                    print(f"  Query: '{query}'")
                    results = await memory_manager.retrieve_relevant_memories(
                        user_id="test_user_mixed_emotions",
                        query=query,
                        limit=5
                    )
                    
                    # Check if our stored memory is retrieved
                    found = any(
                        result.get('content', '') == case['content'] 
                        for result in results
                    )
                    
                    if found:
                        retrieval_success += 1
                        print(f"    ✅ Found memory (score: {results[0].get('score', 0):.3f})")
                    else:
                        print(f"    ❌ Memory not found in top results")
                
                # Calculate success metrics
                emotion_accuracy = emotion_result.primary_emotion.lower() in [e.lower() for e in case['expected_mixed']]
                mixed_detection = len(emotion_result.all_emotions) > 1
                retrieval_rate = retrieval_success / len(test_queries)
                
                test_results.append({
                    'case': case['description'],
                    'emotion_accuracy': emotion_accuracy,
                    'mixed_detection': mixed_detection,
                    'retrieval_rate': retrieval_rate,
                    'primary_emotion': emotion_result.primary_emotion,
                    'all_emotions': emotion_result.all_emotions,
                    'confidence': emotion_result.confidence
                })
                
                print(f"\n📊 Test {i} Results:")
                print(f"  Emotion accuracy: {'✅' if emotion_accuracy else '❌'}")
                print(f"  Mixed emotion detection: {'✅' if mixed_detection else '❌'}")
                print(f"  Retrieval success rate: {retrieval_rate:.1%}")
                
            except Exception as e:
                print(f"❌ Test case {i} failed: {e}")
                test_results.append({
                    'case': case['description'],
                    'error': str(e)
                })
        
        # Final Results Summary
        print("\n" + "=" * 55)
        print("🎭 MIXED EMOTION FIDELITY TEST RESULTS")
        print("=" * 55)
        
        successful_tests = [r for r in test_results if 'error' not in r]
        if successful_tests:
            avg_retrieval = sum(r['retrieval_rate'] for r in successful_tests) / len(successful_tests)
            emotion_accuracy = sum(1 for r in successful_tests if r['emotion_accuracy']) / len(successful_tests)
            mixed_detection = sum(1 for r in successful_tests if r['mixed_detection']) / len(successful_tests)
            
            print(f"📈 Overall Performance:")
            print(f"  Tests completed: {len(successful_tests)}/{len(test_cases)}")
            print(f"  Emotion accuracy: {emotion_accuracy:.1%}")
            print(f"  Mixed emotion detection: {mixed_detection:.1%}")
            print(f"  Average retrieval success: {avg_retrieval:.1%}")
            
            # Fidelity assessment
            if avg_retrieval >= 0.75 and mixed_detection >= 0.75:
                print(f"\n🎉 EXCELLENT: Mixed emotion fidelity is preserved!")
                print(f"   System successfully captures and retrieves complex emotional nuance.")
            elif avg_retrieval >= 0.5 and mixed_detection >= 0.5:
                print(f"\n⚠️  MODERATE: Some mixed emotion fidelity preserved.")
                print(f"   System has partial success with emotional complexity.")
            else:
                print(f"\n❌ POOR: Mixed emotion fidelity needs improvement.")
                print(f"   System struggles with complex emotional context.")
        else:
            print("❌ All tests failed - unable to assess mixed emotion fidelity")
        
        print("\n🔍 Detailed Results:")
        for result in test_results:
            if 'error' in result:
                print(f"  ❌ {result['case']}: {result['error']}")
            else:
                print(f"  📊 {result['case']}:")
                print(f"     Primary: {result['primary_emotion']}")
                print(f"     Mixed: {len(result['all_emotions'])} emotions detected")
                print(f"     Retrieval: {result['retrieval_rate']:.1%}")
        
        print(f"\n✅ Mixed emotion fidelity test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the WhisperEngine root directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error details:")

if __name__ == "__main__":
    main()