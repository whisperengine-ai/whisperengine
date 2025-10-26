"""
Test semantic pattern matching in UnifiedQueryClassifier.

Tests the new word vector similarity feature that catches semantic variations
beyond exact keyword matching.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.unified_query_classification import (
    UnifiedQueryClassifier,
    QueryIntent
)


def test_semantic_emotion_matching():
    """Test semantic matching for emotional patterns."""
    print("\n" + "="*80)
    print("TEST: Semantic Emotion Matching")
    print("="*80)
    
    classifier = UnifiedQueryClassifier()
    
    # Check if we have word vectors
    if not classifier.has_vectors:
        print("⚠️  WARNING: No word vectors available. Semantic matching disabled.")
        print("   Install en_core_web_md: python -m spacy download en_core_web_md")
        return False
    
    if classifier.nlp:
        print(f"✅ Word vectors loaded: {classifier.nlp.vocab.vectors.size} vectors\n")
    else:
        print("✅ Classifier initialized\n")
    
    test_cases = [
        {
            "query": "I'm feeling joyful today",
            "expected_match": "happy",
            "description": "joyful → happy (semantic variation)"
        },
        {
            "query": "I'm absolutely furious",
            "expected_match": "angry",
            "description": "furious → angry (semantic variation)"
        },
        {
            "query": "I'm terrified of spiders",
            "expected_match": "scared",
            "description": "terrified → scared (semantic variation)"
        },
        {
            "query": "I feel ecstatic!",
            "expected_match": "happy",
            "description": "ecstatic → happy (semantic variation)"
        },
        {
            "query": "I'm melancholy today",
            "expected_match": "sad",
            "description": "melancholy → sad (semantic variation)"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"Query: \"{test['query']}\"")
        print(f"Expected: {test['description']}")
        
        # Run classification
        result = asyncio.run(classifier.classify(test['query']))
        
        # Check for semantic matches
        if result.semantic_matches:
            match = result.semantic_matches[0]
            print(f"✅ MATCHED: '{match['query_token']}' ≈ '{match['matched_keyword']}' "
                  f"(similarity: {match['similarity']})")
            print(f"   Intent: {result.intent_type.value} (confidence: {result.intent_confidence:.2f})")
            
            # Check if it's the expected match
            if test['expected_match'] in match['matched_keyword']:
                results.append(True)
                print(f"   ✓ Correct semantic match!\n")
            else:
                results.append(False)
                print(f"   ✗ Unexpected match (expected '{test['expected_match']}')\n")
        else:
            print(f"✗ NO MATCH: No semantic matches found")
            print(f"   Intent: {result.intent_type.value}")
            print(f"   Matched patterns: {result.matched_patterns}\n")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print("="*80)
    print(f"RESULTS: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print("="*80)
    
    return passed == total


def test_exact_keyword_still_works():
    """Ensure exact keyword matching still works."""
    print("\n" + "="*80)
    print("TEST: Exact Keyword Matching (Baseline)")
    print("="*80)
    
    classifier = UnifiedQueryClassifier()
    
    test_cases = [
        {
            "query": "I feel happy today",
            "expected_intent": QueryIntent.FACTUAL_RECALL,
            "expected_pattern": "emotional"
        },
        {
            "query": "I'm sad about this",
            "expected_intent": QueryIntent.FACTUAL_RECALL,
            "expected_pattern": "emotional"
        },
        {
            "query": "I'm angry right now",
            "expected_intent": QueryIntent.FACTUAL_RECALL,
            "expected_pattern": "emotional"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"Query: \"{test['query']}\"")
        
        result = asyncio.run(classifier.classify(test['query']))
        
        if test['expected_pattern'] in result.matched_patterns:
            print(f"✅ MATCHED: Pattern '{test['expected_pattern']}' detected")
            print(f"   Intent: {result.intent_type.value}\n")
            results.append(True)
        else:
            print(f"✗ NO MATCH: Expected pattern '{test['expected_pattern']}'")
            print(f"   Got: {result.matched_patterns}\n")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print("="*80)
    print(f"RESULTS: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print("="*80)
    
    return passed == total


def test_false_positives():
    """Test that semantic matching doesn't create too many false positives."""
    print("\n" + "="*80)
    print("TEST: False Positive Prevention")
    print("="*80)
    
    classifier = UnifiedQueryClassifier()
    
    if not classifier.has_vectors:
        print("⚠️  Skipping (no word vectors)")
        return True
    
    test_cases = [
        {
            "query": "The weather is nice today",
            "should_not_match": "emotional",
            "description": "'nice' should not match 'happy' above threshold"
        },
        {
            "query": "I need to run an errand",
            "should_not_match": "emotional",
            "description": "'run' should not match emotional patterns"
        },
        {
            "query": "Can you book a table?",
            "should_not_match": "emotional",
            "description": "'book' should not match emotional patterns"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"Query: \"{test['query']}\"")
        print(f"Check: {test['description']}")
        
        result = asyncio.run(classifier.classify(test['query']))
        
        if test['should_not_match'] not in result.matched_patterns:
            print(f"✅ CORRECT: No false positive")
            print(f"   Patterns: {result.matched_patterns}\n")
            results.append(True)
        else:
            print(f"✗ FALSE POSITIVE: Incorrectly matched '{test['should_not_match']}'")
            if result.semantic_matches:
                for match in result.semantic_matches:
                    print(f"   Match: '{match['query_token']}' ≈ '{match['matched_keyword']}' "
                          f"(similarity: {match['similarity']})")
            print()
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print("="*80)
    print(f"RESULTS: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print("="*80)
    
    return passed == total


def test_performance():
    """Test classification performance with semantic matching."""
    print("\n" + "="*80)
    print("TEST: Performance Benchmark")
    print("="*80)
    
    classifier = UnifiedQueryClassifier()
    
    test_queries = [
        "I'm feeling joyful today",
        "What did we talk about yesterday?",
        "I love pizza",
        "What's my favorite food?",
        "I'm terrified of heights"
    ]
    
    import time
    
    times = []
    for query in test_queries:
        start = time.time()
        result = asyncio.run(classifier.classify(query))
        elapsed_ms = (time.time() - start) * 1000
        times.append(elapsed_ms)
        
        print(f"Query: \"{query[:40]}...\"")
        print(f"  Time: {elapsed_ms:.2f}ms | "
              f"Semantic matches: {len(result.semantic_matches)} | "
              f"Intent: {result.intent_type.value}")
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print("\n" + "="*80)
    print(f"Average: {avg_time:.2f}ms | Max: {max_time:.2f}ms")
    
    if max_time < 15.0:
        print(f"✅ PASS: All queries under 15ms target")
        print("="*80)
        return True
    else:
        print(f"✗ FAIL: Some queries exceeded 15ms target")
        print("="*80)
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SEMANTIC PATTERN MATCHING TEST SUITE")
    print("="*80)
    
    # Run tests
    test_results = []
    
    test_results.append(("Semantic Emotion Matching", test_semantic_emotion_matching()))
    test_results.append(("Exact Keyword Matching", test_exact_keyword_still_works()))
    test_results.append(("False Positive Prevention", test_false_positives()))
    test_results.append(("Performance Benchmark", test_performance()))
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    for name, passed in test_results:
        status = "✅ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, p in test_results if p)
    total = len(test_results)
    
    print("="*80)
    print(f"Overall: {passed}/{total} test suites passed ({100*passed/total:.0f}%)")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
