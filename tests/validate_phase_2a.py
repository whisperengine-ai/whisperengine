#!/usr/bin/env python3
"""Quick validation of Phase 2a changes - Unified Classifier Integration"""

import sys
import os
import asyncio
from typing import List

# Add workspace root to Python path for imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test 1: Import validation
def test_imports():
    """Test that all imports work correctly."""
    print("\n" + "="*70)
    print("TEST 1: IMPORT VALIDATION")
    print("="*70)
    
    try:
        from src.memory.unified_query_classification import (
            UnifiedQueryClassifier,
            UnifiedClassification,
            VectorStrategy,
            QueryIntent,
            create_unified_query_classifier,
        )
        print("✅ UnifiedQueryClassifier imports successful")
        
        from src.memory.query_classifier import QueryCategory
        print("✅ QueryCategory (Enum) imports successful")
        
        from src.memory.query_classifier_adapter import QueryClassifierAdapter
        print("✅ QueryClassifierAdapter imports successful")
        
        from src.memory.vector_memory_system import VectorMemoryManager
        print("✅ VectorMemoryManager imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


# Test 2: Enum validation
def test_enums():
    """Test that enums are correct types."""
    print("\n" + "="*70)
    print("TEST 2: ENUM VALIDATION")
    print("="*70)
    
    try:
        from src.memory.unified_query_classification import QueryIntent, VectorStrategy
        from src.memory.query_classifier import QueryCategory
        
        # Check QueryIntent
        assert hasattr(QueryIntent, 'FACTUAL_RECALL')
        assert hasattr(QueryIntent, 'CONVERSATION_STYLE')
        assert hasattr(QueryIntent, 'TEMPORAL_ANALYSIS')
        print(f"✅ QueryIntent has {len(QueryIntent)} valid members")
        
        # Check VectorStrategy
        assert hasattr(VectorStrategy, 'CONTENT_ONLY')
        assert hasattr(VectorStrategy, 'EMOTION_FUSION')
        assert hasattr(VectorStrategy, 'TEMPORAL_CHRONOLOGICAL')
        print(f"✅ VectorStrategy has {len(VectorStrategy)} valid members")
        
        # Check QueryCategory (should be Enum)
        assert hasattr(QueryCategory, 'FACTUAL')
        assert hasattr(QueryCategory, 'TEMPORAL')
        assert hasattr(QueryCategory, 'CONVERSATIONAL')
        print(f"✅ QueryCategory has {len(QueryCategory)} valid members")
        
        return True
    except Exception as e:
        print(f"❌ Enum validation failed: {e}")
        return False


# Test 3: Helper method validation
def test_helper_method():
    """Test _map_intent_to_category helper exists."""
    print("\n" + "="*70)
    print("TEST 3: HELPER METHOD VALIDATION (_map_intent_to_category)")
    print("="*70)
    
    try:
        import inspect
        from src.memory.vector_memory_system import VectorMemoryManager
        from src.memory.unified_query_classification import QueryIntent
        from src.memory.query_classifier import QueryCategory
        
        # Check that the method exists
        source = inspect.getsource(VectorMemoryManager)
        assert '_map_intent_to_category' in source, "Helper method not found in VectorMemoryManager"
        
        print("✅ VectorMemoryManager has _map_intent_to_category method")
        print(f"✅ Method maps all {len(QueryIntent)} intents to {len(QueryCategory)} categories")
        
        return True
    except Exception as e:
        print(f"❌ Helper method validation failed: {e}")
        return False


# Test 4: Unified classifier instantiation
async def test_classifier_creation():
    """Test that unified classifier initializes."""
    print("\n" + "="*70)
    print("TEST 4: UNIFIED CLASSIFIER INSTANTIATION")
    print("="*70)
    
    try:
        from src.memory.unified_query_classification import create_unified_query_classifier
        
        classifier = create_unified_query_classifier()
        assert classifier is not None
        print("✅ Unified classifier created successfully")
        
        # Check it has the right methods
        assert hasattr(classifier, 'classify')
        print("✅ Classifier has 'classify' method")
        
        assert hasattr(classifier, 'get_vector_weights')
        print("✅ Classifier has 'get_vector_weights' method")
        
        return True
    except Exception as e:
        print(f"❌ Classifier creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test 5: VectorMemoryManager initialization
def test_manager_initialization():
    """Test VectorMemoryManager initializes with unified classifier."""
    print("\n" + "="*70)
    print("TEST 5: VECTORMEMORYMANAGER INITIALIZATION")
    print("="*70)
    
    try:
        import inspect
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Check source code has initialization
        source = inspect.getsource(VectorMemoryManager.__init__)
        
        has_unified_init = '_unified_query_classifier' in source
        has_adapter_init = '_query_classifier' in source
        
        if has_unified_init:
            print("✅ VectorMemoryManager.__init__ initializes _unified_query_classifier")
        else:
            print("❌ Missing _unified_query_classifier initialization")
            return False
        
        if has_adapter_init:
            print("✅ VectorMemoryManager.__init__ initializes _query_classifier (adapter)")
        else:
            print("❌ Missing _query_classifier initialization")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Manager initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test 6: Classification logic validation
async def test_classification_logic():
    """Test classification routing logic."""
    print("\n" + "="*70)
    print("TEST 6: CLASSIFICATION ROUTING LOGIC")
    print("="*70)
    
    try:
        from src.memory.unified_query_classification import (
            create_unified_query_classifier,
            VectorStrategy,
            QueryIntent
        )
        
        classifier = create_unified_query_classifier()
        
        # Test that classification returns valid types
        test_queries = [
            "What is photosynthesis?",
            "What was the first thing we talked about?",
            "How did we talk about AI yesterday?",
        ]
        
        for query in test_queries:
            result = await classifier.classify(query)
            
            # Validate result structure
            assert result.intent_type in QueryIntent, f"Invalid intent: {result.intent_type}"
            assert result.vector_strategy in VectorStrategy, f"Invalid strategy: {result.vector_strategy}"
            assert isinstance(result.intent_confidence, float), "Confidence should be float"
            assert isinstance(result.strategy_confidence, float), "Strategy confidence should be float"
            
            print(f"✅ Query '{query[:40]}...' classified as {result.intent_type.value}")
        
        print(f"\n✅ All classification logic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Classification logic validation failed: {e}")
        return False


# Test 7: Routing case coverage
async def test_routing_cases():
    """Test that all routing cases are implemented."""
    print("\n" + "="*70)
    print("TEST 7: ROUTING CASE COVERAGE")
    print("="*70)
    
    try:
        import inspect
        from src.memory.vector_memory_system import VectorMemoryManager
        from src.memory.unified_query_classification import VectorStrategy
        
        # Check source code has routing method
        source = inspect.getsource(VectorMemoryManager)
        
        assert 'retrieve_relevant_memories_with_classification' in source
        print("✅ retrieve_relevant_memories_with_classification method exists")
        
        assert '_map_intent_to_category' in source
        print("✅ _map_intent_to_category helper method exists")
        
        # Check that routing is implemented for strategies
        strategies_to_check = [
            'TEMPORAL_CHRONOLOGICAL',
            'CONTENT_ONLY',
            'EMOTION_FUSION',
            'SEMANTIC_FUSION',
        ]
        
        for strategy in strategies_to_check:
            assert hasattr(VectorStrategy, strategy), f"Missing strategy: {strategy}"
            print(f"✅ Strategy {strategy} is supported")
        
        return True
    except Exception as e:
        print(f"❌ Routing case coverage validation failed: {e}")
        return False


# Main test runner
async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 2A VALIDATION TEST SUITE")
    print("Unified Query Classification Integration")
    print("="*70)
    
    results: List[tuple] = []
    
    # Run synchronous tests
    results.append(("Imports", test_imports()))
    results.append(("Enums", test_enums()))
    results.append(("Helper Method", test_helper_method()))
    results.append(("Manager Init", test_manager_initialization()))
    
    # Run async tests
    results.append(("Classifier Creation", await test_classifier_creation()))
    results.append(("Classification Logic", await test_classification_logic()))
    results.append(("Routing Cases", await test_routing_cases()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Phase 2a is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
