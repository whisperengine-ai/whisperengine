#!/usr/bin/env python3
"""
Vector Memory System Integration Tests - Final Validation
========================================================

Comprehensive test suite to verify all Phase 1.1, 1.2, and 1.3 features
are working correctly with the implementation fixes applied.
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.memory.memory_protocol import create_memory_manager

async def test_enhanced_emotional_detection():
    """Test Phase 1.1: Enhanced emotional detection with intensity scoring"""
    print("🧪 TEST 1: Enhanced Emotional Detection (Phase 1.1)")
    
    # Create memory manager with localhost config
    vector_config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'grpc_port': 6334,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        }
    }
    
    memory_manager = create_memory_manager("vector", config=vector_config)
    test_user_id = f"emotion_test_{int(datetime.now().timestamp())}"
    
    # Test emotional detection
    emotional_messages = [
        ("I'm absolutely devastated!", "very_negative", 0.8),
        ("I'm so incredibly happy!", "very_positive", 0.8),
        ("What time is it?", "neutral", 0.2),
        ("I feel anxious about tomorrow", "negative", 0.6)
    ]
    
    results = []
    for message, expected_emotion, min_intensity in emotional_messages:
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=message,
            bot_response="I understand."
        )
        
        # Get the stored memory - get more history to find user messages
        await asyncio.sleep(0.1)  # Small delay for processing
        history = await memory_manager.get_conversation_history(test_user_id, limit=10)
        
        user_memory = None
        # Look for the user message we just stored
        for memory in history:
            if (memory.get('role') == 'user' and 
                'metadata' in memory and 
                memory.get('content') == message):
                user_memory = memory
                break
        
        if user_memory and 'metadata' in user_memory:
            metadata = user_memory['metadata']
            emotion = metadata.get('emotional_context', 'unknown')
            intensity = metadata.get('emotional_intensity', 0.0)
            
            # Check emotion type and intensity
            emotion_correct = any(exp in emotion for exp in expected_emotion.split('_'))
            intensity_correct = intensity >= min_intensity
            
            results.append({
                'message': message,
                'expected': expected_emotion,
                'actual_emotion': emotion,
                'actual_intensity': intensity,
                'emotion_correct': emotion_correct,
                'intensity_correct': intensity_correct,
                'passed': emotion_correct and intensity_correct
            })
        else:
            # Memory not found or no metadata
            results.append({
                'message': message,
                'expected': expected_emotion,
                'actual_emotion': 'not_found',
                'actual_intensity': 0.0,
                'emotion_correct': False,
                'intensity_correct': False,
                'passed': False
            })
    
    # Evaluate results
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    print(f"   Results: {passed_tests}/{total_tests} passed")
    for result in results:
        status = "✅" if result['passed'] else "❌"
        print(f"   {status} '{result['message'][:30]}...' → {result['actual_emotion']} ({result['actual_intensity']:.2f})")
    
    return passed_tests == total_tests

async def test_emotional_trajectory_tracking():
    """Test Phase 1.2: Emotional trajectory tracking"""
    print("\n🧪 TEST 2: Emotional Trajectory Tracking (Phase 1.2)")
    
    vector_config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'grpc_port': 6334,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        }
    }
    
    memory_manager = create_memory_manager("vector", config=vector_config)
    test_user_id = f"trajectory_test_{int(datetime.now().timestamp())}"
    
    # Create emotional trajectory
    messages = [
        "I'm feeling great today!",
        "Something bad happened at work...",
        "But then my friend called and cheered me up!"
    ]
    
    for message in messages:
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=message,
            bot_response="I see."
        )
        await asyncio.sleep(0.1)  # Small delay
    
    # Check trajectory data
    history = await memory_manager.get_conversation_history(test_user_id, limit=10)
    
    trajectory_found = False
    velocity_found = False
    stability_found = False
    
    for memory in history:
        if memory.get('role') == 'user' and 'metadata' in memory:
            metadata = memory['metadata']
            
            if 'emotional_trajectory' in metadata and metadata['emotional_trajectory']:
                trajectory_found = True
            if 'emotional_velocity' in metadata:
                velocity_found = True
            if 'emotional_stability' in metadata:
                stability_found = True
    
    results = {
        'trajectory_tracking': trajectory_found,
        'velocity_calculation': velocity_found,
        'stability_measurement': stability_found
    }
    
    passed_tests = sum(1 for passed in results.values() if passed)
    total_tests = len(results)
    
    print(f"   Results: {passed_tests}/{total_tests} trajectory features working")
    for feature, working in results.items():
        status = "✅" if working else "❌"
        print(f"   {status} {feature.replace('_', ' ').title()}")
    
    return passed_tests == total_tests

async def test_memory_significance_scoring():
    """Test Phase 1.3: Memory significance scoring"""
    print("\n🧪 TEST 3: Memory Significance Scoring (Phase 1.3)")
    
    vector_config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'grpc_port': 6334,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        }
    }
    
    memory_manager = create_memory_manager("vector", config=vector_config)
    test_user_id = f"significance_test_{int(datetime.now().timestamp())}"
    
    # Test different significance levels
    test_messages = [
        ("My grandmother passed away yesterday", "high_significance"),
        ("What time is it?", "low_significance"),
        ("I just got promoted at work!", "high_significance"),
        ("How's the weather?", "low_significance")
    ]
    
    significance_scores = []
    
    for message, expected_significance in test_messages:
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=message,
            bot_response="I understand."
        )
        
        # Get significance data - wait and get more history
        await asyncio.sleep(0.1)
        history = await memory_manager.get_conversation_history(test_user_id, limit=10)
        
        user_memory = None
        # Look for the specific user message we just stored
        for memory in history:
            if (memory.get('role') == 'user' and 
                'metadata' in memory and 
                memory.get('content') == message):
                user_memory = memory
                break
        
        if user_memory and 'metadata' in user_memory:
            metadata = user_memory['metadata']
            significance = metadata.get('overall_significance', 0.0)
            factors = metadata.get('significance_factors', {})
            tier = metadata.get('significance_tier', 'unknown')
            
            significance_scores.append({
                'message': message,
                'expected': expected_significance,
                'significance_score': significance,
                'has_factors': bool(factors),
                'has_tier': tier != 'unknown'
            })
        else:
            # Memory not found, still add to list with default values
            significance_scores.append({
                'message': message,
                'expected': expected_significance,
                'significance_score': 0.0,
                'has_factors': False,
                'has_tier': False
            })
    
    # Evaluate significance scoring
    scoring_working = len([s for s in significance_scores if s['significance_score'] > 0]) > 0
    factors_working = len([s for s in significance_scores if s['has_factors']]) > 0
    tiers_working = len([s for s in significance_scores if s['has_tier']]) > 0
    
    # Check that high significance messages score higher than low significance
    high_scores = [s['significance_score'] for s in significance_scores if 'high' in s['expected']]
    low_scores = [s['significance_score'] for s in significance_scores if 'low' in s['expected']]
    
    proper_scoring = False
    if high_scores and low_scores:
        avg_high = sum(high_scores) / len(high_scores)
        avg_low = sum(low_scores) / len(low_scores)
        proper_scoring = avg_high > avg_low
    
    results = {
        'significance_scoring': scoring_working,
        'significance_factors': factors_working,
        'significance_tiers': tiers_working,
        'proper_score_ranking': proper_scoring
    }
    
    passed_tests = sum(1 for passed in results.values() if passed)
    total_tests = len(results)
    
    print(f"   Results: {passed_tests}/{total_tests} significance features working")
    for feature, working in results.items():
        status = "✅" if working else "❌"
        print(f"   {status} {feature.replace('_', ' ').title()}")
    
    return passed_tests == total_tests

async def test_api_compatibility():
    """Test API compatibility and method calls"""
    print("\n🧪 TEST 4: API Compatibility")
    
    vector_config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'grpc_port': 6334,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        }
    }
    
    try:
        memory_manager = create_memory_manager("vector", config=vector_config)
        test_user_id = f"api_test_{int(datetime.now().timestamp())}"
        
        # Test store_conversation
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message="Test message",
            bot_response="Test response"
        )
        
        # Test retrieve_relevant_memories
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query="test",
            limit=5
        )
        
        # Test get_conversation_history
        history = await memory_manager.get_conversation_history(
            user_id=test_user_id,
            limit=5
        )
        
        api_tests = {
            'store_conversation': True,
            'retrieve_relevant_memories': isinstance(memories, list),
            'get_conversation_history': isinstance(history, list)
        }
        
        passed_tests = sum(1 for passed in api_tests.values() if passed)
        total_tests = len(api_tests)
        
        print(f"   Results: {passed_tests}/{total_tests} API methods working")
        for method, working in api_tests.items():
            status = "✅" if working else "❌"
            print(f"   {status} {method}")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

async def test_production_integration():
    """Test full production integration"""
    print("\n🧪 TEST 5: Production Integration")
    
    # Test that memory manager can be created with default production config
    try:
        memory_type = os.getenv("MEMORY_SYSTEM_TYPE", "vector")
        
        # Override config for localhost
        vector_config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'grpc_port': 6334,
                'collection_name': 'whisperengine_memory',
                'vector_size': 384
            }
        }
        
        memory_manager = create_memory_manager(memory_type, config=vector_config)
        
        # Test realistic conversation flow
        test_user_id = f"production_test_{int(datetime.now().timestamp())}"
        
        conversation_flow = [
            ("Hello! I'm having a really tough day.", "I'm sorry to hear that. What's been troubling you?"),
            ("I lost my job and I'm feeling devastated.", "That's incredibly difficult. Job loss can be very emotionally challenging."),
            ("But I'm trying to stay positive and look for new opportunities.", "That's a great attitude. Your resilience is admirable.")
        ]
        
        for user_msg, bot_msg in conversation_flow:
            await memory_manager.store_conversation(
                user_id=test_user_id,
                user_message=user_msg,
                bot_response=bot_msg
            )
        
        # Test retrieval
        relevant_memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query="emotional support",
            limit=5
        )
        
        history = await memory_manager.get_conversation_history(
            user_id=test_user_id,
            limit=10
        )
        
        production_tests = {
            'manager_creation': True,
            'conversation_storage': len(history) > 0,
            'memory_retrieval': len(relevant_memories) > 0,
            'enhanced_features': any(
                'emotional_context' in str(memory) for memory in history
            )
        }
        
        passed_tests = sum(1 for passed in production_tests.values() if passed)
        total_tests = len(production_tests)
        
        print(f"   Results: {passed_tests}/{total_tests} production features working")
        for feature, working in production_tests.items():
            status = "✅" if working else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"   ❌ Production integration failed: {e}")
        return False

async def test_data_validation():
    """Test data validation and quality"""
    print("\n🧪 TEST 6: Data Validation")
    
    vector_config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'grpc_port': 6334,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        }
    }
    
    memory_manager = create_memory_manager("vector", config=vector_config)
    test_user_id = f"validation_test_{int(datetime.now().timestamp())}"
    
    # Store test data
    await memory_manager.store_conversation(
        user_id=test_user_id,
        user_message="I'm feeling extremely excited about my new adventure!",
        bot_response="That's wonderful! Tell me more about this adventure."
    )
    
    # Validate stored data structure
    history = await memory_manager.get_conversation_history(test_user_id, limit=2)
    
    validation_results = {
        'data_exists': len(history) > 0,
        'proper_structure': False,
        'emotional_data': False,
        'significance_data': False,
        'trajectory_data': False
    }
    
    if history:
        # Check first memory structure
        memory = history[0]
        if isinstance(memory, dict) and 'metadata' in memory:
            validation_results['proper_structure'] = True
            
            metadata = memory['metadata']
            if 'emotional_context' in metadata and 'emotional_intensity' in metadata:
                validation_results['emotional_data'] = True
            
            if 'overall_significance' in metadata and 'significance_factors' in metadata:
                validation_results['significance_data'] = True
            
            if 'emotional_trajectory' in metadata and 'emotional_velocity' in metadata:
                validation_results['trajectory_data'] = True
    
    passed_tests = sum(1 for passed in validation_results.values() if passed)
    total_tests = len(validation_results)
    
    print(f"   Results: {passed_tests}/{total_tests} validation checks passed")
    for check, passed in validation_results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check.replace('_', ' ').title()}")
    
    return passed_tests == total_tests

async def run_comprehensive_tests():
    """Run all integration tests"""
    print("🚀 COMPREHENSIVE VECTOR MEMORY INTEGRATION TESTS")
    print("=" * 70)
    print("Testing all Phase 1.1, 1.2, and 1.3 features with implementation fixes")
    print()
    
    test_functions = [
        test_enhanced_emotional_detection,
        test_emotional_trajectory_tracking,
        test_memory_significance_scoring,
        test_api_compatibility,
        test_production_integration,
        test_data_validation
    ]
    
    results = []
    
    for test_func in test_functions:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    passed_tests = sum(1 for result in results if result)
    total_tests = len(results)
    
    print("\n" + "=" * 70)
    print(f"🎯 FINAL RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Vector memory system is fully operational!")
        print("✅ Phase 1.1: Enhanced emotional detection - WORKING")
        print("✅ Phase 1.2: Emotional trajectory tracking - WORKING")  
        print("✅ Phase 1.3: Memory significance scoring - WORKING")
        print("🚀 Production system ready for deployment!")
    else:
        print(f"⚠️  {total_tests - passed_tests} tests still failing")
        print("🛠️  Additional fixes may be needed")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())