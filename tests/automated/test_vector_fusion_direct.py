"""
Direct Python Validation: Vector Fusion Module

Tests Reciprocal Rank Fusion algorithm and query classification
for multi-vector memory retrieval.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.vector_fusion import (
    ReciprocalRankFusion,
    FusionConfig,
    VectorFusionCoordinator
)


def test_rrf_algorithm():
    """Test Reciprocal Rank Fusion algorithm correctness."""
    print("\n" + "="*80)
    print("TEST 1: RRF Algorithm Correctness")
    print("="*80)
    
    rrf = ReciprocalRankFusion(FusionConfig(k=60))
    
    # Mock search results from different vectors
    content_results = [
        {'content': 'Memory A', 'timestamp': '2024-01-01', 'score': 0.9},
        {'content': 'Memory B', 'timestamp': '2024-01-02', 'score': 0.8},
        {'content': 'Memory C', 'timestamp': '2024-01-03', 'score': 0.7},
    ]
    
    semantic_results = [
        {'content': 'Memory B', 'timestamp': '2024-01-02', 'score': 0.85},  # Also in content
        {'content': 'Memory D', 'timestamp': '2024-01-04', 'score': 0.75},
        {'content': 'Memory A', 'timestamp': '2024-01-01', 'score': 0.70},  # Also in content
    ]
    
    results_by_vector = {
        'content': content_results,
        'semantic': semantic_results
    }
    
    fused = rrf.fuse(results_by_vector, limit=10)
    
    print(f"✓ Input: {len(content_results)} content results + {len(semantic_results)} semantic results")
    print(f"✓ Output: {len(fused)} fused results")
    
    # Memory B should rank highest (appears in both lists at good positions)
    memory_b = next((m for m in fused if m['content'] == 'Memory B'), None)
    assert memory_b is not None, "Memory B should be in fused results"
    
    print(f"✓ Memory B fusion metadata: {memory_b['fusion_metadata']}")
    assert 'content' in memory_b['fusion_metadata']['sources']
    assert 'semantic' in memory_b['fusion_metadata']['sources']
    assert memory_b['fusion_metadata']['fusion_strategy'] == 'reciprocal_rank_fusion'
    
    # Memory A should also appear (in both lists)
    memory_a = next((m for m in fused if m['content'] == 'Memory A'), None)
    assert memory_a is not None, "Memory A should be in fused results"
    print(f"✓ Memory A fusion metadata: {memory_a['fusion_metadata']}")
    
    # Memory C and D should appear (unique to one list each)
    memory_c = next((m for m in fused if m['content'] == 'Memory C'), None)
    memory_d = next((m for m in fused if m['content'] == 'Memory D'), None)
    assert memory_c is not None, "Memory C should be in fused results"
    assert memory_d is not None, "Memory D should be in fused results"
    
    print("\n✅ TEST 1 PASSED: RRF algorithm working correctly")
    return True


def test_single_vector_passthrough():
    """Test that single vector type returns results without fusion."""
    print("\n" + "="*80)
    print("TEST 2: Single Vector Passthrough")
    print("="*80)
    
    rrf = ReciprocalRankFusion()
    
    content_results = [
        {'content': 'Memory A', 'timestamp': '2024-01-01', 'score': 0.9},
        {'content': 'Memory B', 'timestamp': '2024-01-02', 'score': 0.8},
    ]
    
    results_by_vector = {'content': content_results}
    
    fused = rrf.fuse(results_by_vector, limit=10)
    
    print(f"✓ Input: {len(content_results)} content-only results")
    print(f"✓ Output: {len(fused)} results (should be same)")
    
    assert len(fused) == len(content_results), "Should return all results unchanged"
    assert 'fusion_metadata' not in fused[0], "Should not have fusion metadata for single vector"
    
    print("\n✅ TEST 2 PASSED: Single vector returns unchanged")
    return True


def test_fusion_coordinator_conversational():
    """Test that coordinator detects conversational queries."""
    print("\n" + "="*80)
    print("TEST 3: Fusion Coordinator - Conversational Detection")
    print("="*80)
    
    coordinator = VectorFusionCoordinator()
    
    conversational_queries = [
        "What did we discuss about marine biology?",
        "Remember when we talked about coral reefs?",
        "What topics have we covered in our conversations?",
        "Tell me about things we discussed yesterday"
    ]
    
    non_conversational_queries = [
        "What is photosynthesis?",
        "Tell me about coral reefs",
        "Explain marine ecosystems"
    ]
    
    print("\n📝 Testing conversational queries:")
    for query in conversational_queries:
        should_fuse = coordinator.should_use_fusion(query)
        print(f"  '{query[:50]}...' → fusion={should_fuse}")
        assert should_fuse, f"Should detect conversational: {query}"
    
    print("\n📝 Testing non-conversational queries:")
    for query in non_conversational_queries:
        should_fuse = coordinator.should_use_fusion(query)
        print(f"  '{query[:50]}...' → fusion={should_fuse}")
        assert not should_fuse, f"Should NOT trigger fusion: {query}"
    
    print("\n✅ TEST 3 PASSED: Conversational detection working")
    return True


def test_fusion_coordinator_pattern():
    """Test that coordinator detects pattern/relationship queries."""
    print("\n" + "="*80)
    print("TEST 4: Fusion Coordinator - Pattern Detection")
    print("="*80)
    
    coordinator = VectorFusionCoordinator()
    
    pattern_queries = [
        "What's the relationship between temperature and coral health?",
        "Show me patterns in ocean acidification",
        "How do these concepts connect?",
        "What similarities exist between species?"
    ]
    
    print("\n📝 Testing pattern queries:")
    for query in pattern_queries:
        should_fuse = coordinator.should_use_fusion(query)
        print(f"  '{query[:50]}...' → fusion={should_fuse}")
        assert should_fuse, f"Should detect pattern query: {query}"
    
    print("\n✅ TEST 4 PASSED: Pattern detection working")
    return True


def test_fusion_vector_selection():
    """Test vector type selection for different queries."""
    print("\n" + "="*80)
    print("TEST 5: Fusion Vector Selection")
    print("="*80)
    
    coordinator = VectorFusionCoordinator()
    
    # Pattern query should include semantic
    pattern_query = "What's the relationship between coral and temperature?"
    vectors = coordinator.get_fusion_vectors(pattern_query)
    print(f"✓ Pattern query: {vectors}")
    assert 'content' in vectors, "Should always include content"
    assert 'semantic' in vectors, "Pattern query should include semantic"
    
    # Emotional query should include emotion
    emotion_query = "I feel worried about climate change patterns"
    vectors = coordinator.get_fusion_vectors(emotion_query)
    print(f"✓ Emotion query: {vectors}")
    assert 'content' in vectors, "Should always include content"
    assert 'emotion' in vectors, "Emotion query should include emotion"
    
    # Mixed query should include both
    mixed_query = "I feel the connection between emotions and conservation"
    vectors = coordinator.get_fusion_vectors(mixed_query)
    print(f"✓ Mixed query: {vectors}")
    assert 'content' in vectors
    assert 'emotion' in vectors
    assert 'semantic' in vectors  # 'connection' triggers semantic
    
    print("\n✅ TEST 5 PASSED: Vector selection working correctly")
    return True


def test_rrf_score_ordering():
    """Test that RRF scores order results correctly."""
    print("\n" + "="*80)
    print("TEST 6: RRF Score Ordering")
    print("="*80)
    
    rrf = ReciprocalRankFusion(FusionConfig(k=60))
    
    # Memory appearing in top positions of multiple lists should rank higher
    content_results = [
        {'content': 'Top memory', 'timestamp': '2024-01-01', 'score': 0.9},  # Rank 1
        {'content': 'Mid memory', 'timestamp': '2024-01-02', 'score': 0.7},   # Rank 2
        {'content': 'Low memory', 'timestamp': '2024-01-03', 'score': 0.5},   # Rank 3
    ]
    
    semantic_results = [
        {'content': 'Top memory', 'timestamp': '2024-01-01', 'score': 0.85},  # Rank 1 - also in content!
        {'content': 'Other memory', 'timestamp': '2024-01-04', 'score': 0.8}, # Rank 2
        {'content': 'Mid memory', 'timestamp': '2024-01-02', 'score': 0.75},  # Rank 3 - also in content!
    ]
    
    results_by_vector = {
        'content': content_results,
        'semantic': semantic_results
    }
    
    fused = rrf.fuse(results_by_vector, limit=10)
    
    print(f"✓ Fused {len(fused)} results")
    print("\n📊 RRF Score Ranking:")
    for i, memory in enumerate(fused, 1):
        rrf_score = memory['fusion_metadata']['rrf_score']
        sources = memory['fusion_metadata']['sources']
        print(f"  {i}. {memory['content']} - RRF: {rrf_score:.4f} - Sources: {sources}")
    
    # "Top memory" should rank #1 (appears at rank 1 in BOTH lists)
    assert fused[0]['content'] == 'Top memory', "Top memory should rank first"
    
    # "Mid memory" should rank higher than "Other memory" (appears in both lists vs one)
    mid_idx = next(i for i, m in enumerate(fused) if m['content'] == 'Mid memory')
    other_idx = next(i for i, m in enumerate(fused) if m['content'] == 'Other memory')
    print(f"\n✓ Mid memory rank: {mid_idx + 1}, Other memory rank: {other_idx + 1}")
    assert mid_idx < other_idx, "Memory appearing in multiple lists should rank higher"
    
    print("\n✅ TEST 6 PASSED: RRF scoring orders results correctly")
    return True


def run_all_tests():
    """Run all vector fusion tests."""
    print("\n" + "="*80)
    print("🔀 VECTOR FUSION MODULE - DIRECT PYTHON VALIDATION")
    print("="*80)
    print("Testing Reciprocal Rank Fusion algorithm and query classification")
    
    tests = [
        test_rrf_algorithm,
        test_single_vector_passthrough,
        test_fusion_coordinator_conversational,
        test_fusion_coordinator_pattern,
        test_fusion_vector_selection,
        test_rrf_score_ordering
    ]
    
    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_func.__name__}")
            print(f"Assertion Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
        except (ImportError, AttributeError, KeyError, ValueError, TypeError) as e:
            print(f"\n❌ TEST FAILED: {test_func.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Vector fusion module ready for integration.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
