"""
Test Lemmatization Feature in Query Classification

Tests that word form variations are correctly normalized:
- "loving" → "love"
- "hated" → "hate" 
- "recently" → "recent"
- "starting" → "start"
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.unified_query_classification import UnifiedQueryClassifier


def test_lemmatization():
    """Test lemmatization catches word form variations."""
    print("=" * 80)
    print("LEMMATIZATION TEST SUITE")
    print("=" * 80)
    print()
    
    classifier = UnifiedQueryClassifier()
    
    if not classifier.nlp:
        print("⚠️  spaCy not available - skipping lemmatization tests")
        return False
    
    print(f"✅ spaCy loaded: {classifier.nlp is not None}")
    print(f"✅ Classifier initialized with {len(classifier._keyword_vector_cache)} cached keywords")
    print()
    
    # =========================================================================
    # TEST 1: Emotional Word Forms
    # =========================================================================
    print("=" * 80)
    print("TEST 1: Emotional Word Form Variations")
    print("=" * 80)
    
    emotional_tests = [
        {
            "query": "I'm loving this new feature",
            "word_form": "loving",
            "base_form": "love",
            "expected_match": True,
        },
        {
            "query": "I hated that experience",
            "word_form": "hated",
            "base_form": "hate",
            "expected_match": True,
        },
        {
            "query": "I've been feeling happier lately",
            "word_form": "happier",
            "base_form": "happy",
            "expected_match": True,
        },
        {
            "query": "That made me angrier",
            "word_form": "angrier",
            "base_form": "angry",
            "expected_match": True,
        },
    ]
    
    emotional_pass = 0
    emotional_total = len(emotional_tests)
    
    for test in emotional_tests:
        result = asyncio.run(classifier.classify(test["query"], user_id="test_lemma"))
        
        # Check if emotional pattern was detected
        is_emotional = "emotional" in result.matched_patterns or "emotional_lemma" in result.matched_patterns
        
        if is_emotional:
            print(f"✅ MATCHED: '{test['query']}'")
            print(f"   Word form: {test['word_form']} → base: {test['base_form']}")
            print(f"   Patterns: {result.matched_patterns}")
            print(f"   Intent: {result.intent_type.value}")
            emotional_pass += 1
        else:
            print(f"✗ NO MATCH: '{test['query']}'")
            print(f"   Expected: {test['word_form']} → {test['base_form']}")
            print(f"   Patterns: {result.matched_patterns}")
        print()
    
    print(f"Results: {emotional_pass}/{emotional_total} tests passed")
    print()
    
    # =========================================================================
    # TEST 2: Temporal Word Forms
    # =========================================================================
    print("=" * 80)
    print("TEST 2: Temporal Word Form Variations")
    print("=" * 80)
    
    temporal_tests = [
        {
            "query": "What were we talking about most recently?",
            "word_form": "recently",
            "base_form": "recent",
            "expected_match": True,
        },
        {
            "query": "When are we starting this project?",
            "word_form": "starting",
            "base_form": "start",
            "expected_match": True,
        },
        {
            "query": "What happened earlier in our conversation?",
            "word_form": "earlier",
            "base_form": "early",
            "expected_match": True,
        },
    ]
    
    temporal_pass = 0
    temporal_total = len(temporal_tests)
    
    for test in temporal_tests:
        result = asyncio.run(classifier.classify(test["query"], user_id="test_lemma"))
        
        # Check if temporal pattern was detected
        is_temporal = "temporal" in result.matched_patterns or "temporal_lemma" in result.matched_patterns
        
        if is_temporal:
            print(f"✅ MATCHED: '{test['query']}'")
            print(f"   Word form: {test['word_form']} → base: {test['base_form']}")
            print(f"   Patterns: {result.matched_patterns}")
            print(f"   Intent: {result.intent_type.value}")
            temporal_pass += 1
        else:
            print(f"✗ NO MATCH: '{test['query']}'")
            print(f"   Expected: {test['word_form']} → {test['base_form']}")
            print(f"   Patterns: {result.matched_patterns}")
        print()
    
    print(f"Results: {temporal_pass}/{temporal_total} tests passed")
    print()
    
    # =========================================================================
    # TEST 3: Performance Check
    # =========================================================================
    print("=" * 80)
    print("TEST 3: Performance with Lemmatization")
    print("=" * 80)
    
    import time
    
    test_queries = [
        "I'm loving this new feature",
        "What were we talking about recently?",
        "I hated that experience",
        "When are we starting?",
    ]
    
    times = []
    for query in test_queries:
        start = time.time()
        asyncio.run(classifier.classify(query, user_id="test_perf"))
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f"  {elapsed:5.2f}ms - {query[:50]}")
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print()
    print(f"Average: {avg_time:.2f}ms")
    print(f"Max: {max_time:.2f}ms")
    
    performance_pass = max_time < 15.0
    if performance_pass:
        print(f"✅ Performance target achieved (<15ms)")
    else:
        print(f"⚠️  Some queries exceeded 15ms target")
    
    print()
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    all_tests = [
        ("Emotional Word Forms", emotional_pass == emotional_total, f"{emotional_pass}/{emotional_total}"),
        ("Temporal Word Forms", temporal_pass == temporal_total, f"{temporal_pass}/{temporal_total}"),
        ("Performance", performance_pass, f"{avg_time:.2f}ms avg"),
    ]
    
    for name, passed, result in all_tests:
        status = "✅ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name} ({result})")
    
    total_pass = sum(1 for _, passed, _ in all_tests if passed)
    total_tests = len(all_tests)
    
    print("=" * 80)
    print(f"Overall: {total_pass}/{total_tests} test suites passed")
    print("=" * 80)
    print()
    
    return total_pass == total_tests


if __name__ == "__main__":
    success = test_lemmatization()
    sys.exit(0 if success else 1)
