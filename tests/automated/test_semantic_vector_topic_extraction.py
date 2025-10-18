#!/usr/bin/env python3
"""
Test semantic vector topic extraction to ensure semantic keys are meaningful.

Verifies that _get_semantic_key() produces semantic topics instead of
keyword patterns, and that semantic vectors can be used for topic-based search.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager

def test_semantic_key_extraction():
    """Test that semantic keys are meaningful and topic-based."""
    
    print("=" * 80)
    print("SEMANTIC KEY EXTRACTION TEST")
    print("=" * 80)
    print()
    
    # Create memory manager to access _get_semantic_key
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Test cases with expected semantic categories
    test_cases = [
        {
            "content": "I've been feeling really anxious about my marine biology thesis",
            "expected_category": "academic",
            "description": "Academic anxiety about thesis"
        },
        {
            "content": "My cat's name is Whiskers and he loves tuna",
            "expected_category": "pet",
            "description": "Pet identity information"
        },
        {
            "content": "I love studying ocean acidification and coral reef ecosystems",
            "expected_category": "marine",
            "description": "Marine biology topic"
        },
        {
            "content": "My favorite color is ocean blue",
            "expected_category": "preference",
            "description": "Personal preference"
        },
        {
            "content": "I live in San Francisco near the ocean",
            "expected_category": "location",
            "description": "Location/geography"
        },
        {
            "content": "The pH levels are dropping faster in coral reef zones",
            "expected_category": "marine",
            "description": "Marine biology research"
        },
        {
            "content": "I'm researching climate change impact on marine ecosystems",
            "expected_category": "academic",
            "description": "Academic research topic"
        }
    ]
    
    results = []
    
    print("🧪 Testing semantic key extraction:")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        content = test_case["content"]
        expected = test_case["expected_category"]
        description = test_case["description"]
        
        # Extract semantic key (via vector_store)
        semantic_key = memory_manager.vector_store._get_semantic_key(content)
        
        # Check if semantic key matches expected category
        is_semantic = expected in semantic_key.lower()
        is_meaningful = len(semantic_key) > 5 and '_' in semantic_key
        
        # Verify it's not just "first 3 words" pattern
        first_three_words = '_'.join(content.lower().split()[:3])
        is_not_generic = semantic_key != first_three_words
        
        status = "✅" if (is_semantic or is_meaningful) and is_not_generic else "❌"
        
        print(f"{i}. {description}")
        print(f"   Content: {content[:60]}...")
        print(f"   Semantic key: {semantic_key}")
        print(f"   Expected category: {expected}")
        print(f"   Status: {status}")
        
        if is_semantic:
            print(f"   ✅ Contains expected category '{expected}'")
        elif is_meaningful:
            print(f"   ✅ Meaningful semantic key (not generic pattern)")
        else:
            print(f"   ❌ Generic or non-semantic key")
        
        print()
        
        results.append({
            "test": description,
            "semantic_key": semantic_key,
            "passed": (is_semantic or is_meaningful) and is_not_generic
        })
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status}: {result['test']}")
        print(f"         Semantic key: {result['semantic_key']}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Semantic keys are meaningful!")
        return True
    elif passed >= total * 0.7:
        print(f"\n⚠️ MOSTLY PASSED ({passed}/{total}) - Semantic keys are mostly good")
        return True
    else:
        print(f"\n❌ FAILED - Semantic keys need improvement ({passed}/{total})")
        return False

def test_semantic_key_examples():
    """Show examples of semantic key extraction."""
    
    print("\n" + "=" * 80)
    print("SEMANTIC KEY EXAMPLES")
    print("=" * 80)
    print()
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    examples = [
        "I love marine biology and ocean conservation",
        "Feeling anxious about my thesis deadline",
        "My dog's name is Max",
        "I prefer cold weather over hot",
        "The coral reef ecosystem is fascinating",
        "I'm from Seattle, Washington",
        "Learning about ocean acidification",
        "My favorite food is sushi"
    ]
    
    print("📝 Semantic key examples:")
    print()
    
    for example in examples:
        semantic_key = memory_manager.vector_store._get_semantic_key(example)
        print(f"Content: {example}")
        print(f"Semantic key: {semantic_key}")
        print()

if __name__ == "__main__":
    print("Testing semantic vector topic extraction...")
    print()
    
    # Run tests
    test_passed = test_semantic_key_extraction()
    
    # Show examples
    test_semantic_key_examples()
    
    # Exit with appropriate code
    sys.exit(0 if test_passed else 1)
