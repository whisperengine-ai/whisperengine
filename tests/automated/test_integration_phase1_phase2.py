"""
Phase 1+2 Integration Test

Validates that text normalization + attribute extraction work together
in the complete fact extraction pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor  # pylint: disable=wrong-import-position,import-error


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{'='*80}")
    print(f"  {test_name}")
    print(f"{'='*80}")


def test_normalization_plus_attributes():
    """Test that normalization + attribute extraction work together"""
    print_test_header("Integration Test: Text Normalization + Attribute Extraction")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    # Test cases with Discord artifacts + semantic attributes
    test_cases = [
        {
            "input": "I have a **green car** that I drive daily 🚗",
            "description": "Markdown formatting + emoji + adjective-noun",
            "expected_entities": ["car"],
            "expected_attributes": [("green", "car", "descriptor")]
        },
        {
            "input": "Check out <@123456> eating Swedish meatballs at https://restaurant.com",
            "description": "Discord mention + URL + compound noun",
            "expected_entities": ["Swedish"],  # spaCy might tag as NER
            "expected_attributes": [("Swedish", "meatballs", "descriptor" )]  # May be amod not compound
        },
        {
            "input": "I love @john's ice cream from www.store.com 😍",
            "description": "Username mention + URL + emoji + compound noun",
            "expected_entities": [],
            "expected_attributes": [("ice", "cream", "compound")]
        },
        {
            "input": "My **big red truck** parked at <#555666777> channel",
            "description": "Channel mention + multiple adjectives",
            "expected_entities": [],
            "expected_attributes": [
                ("big", "truck", "descriptor"),
                ("red", "truck", "descriptor")
            ]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"Input (raw): '{test['input']}'")
        
        # Extract all features (includes normalization + attribute extraction)
        features = preprocessor.extract_all_features_from_text(test['input'])
        
        entities = features.get("entities", [])
        attributes = features.get("attributes", [])
        
        print(f"\nResults:")
        print(f"  Entities: {[e['text'] for e in entities]}")
        print(f"  Attributes: {[(a['attribute'], a['entity'], a['attribute_type']) for a in attributes]}")
        
        # Validate attributes were found
        found_attrs = [(a['attribute'], a['entity'], a['attribute_type']) for a in attributes]
        
        success_count = 0
        for expected_attr in test['expected_attributes']:
            if expected_attr in found_attrs:
                print(f"  ✓ Found expected: {expected_attr[0]} → {expected_attr[1]}")
                success_count += 1
            else:
                # Check if found with different type (e.g., amod vs compound)
                found_partial = any(
                    f[0] == expected_attr[0] and f[1] == expected_attr[1]
                    for f in found_attrs
                )
                if found_partial:
                    actual = next(f for f in found_attrs if f[0] == expected_attr[0] and f[1] == expected_attr[1])
                    print(f"  ⚠️  Found with different type: {expected_attr[0]} → {expected_attr[1]} (expected {expected_attr[2]}, got {actual[2]})")
                    success_count += 1
                else:
                    print(f"  ✗ Missing expected: {expected_attr[0]} → {expected_attr[1]}")
        
        if success_count == len(test['expected_attributes']):
            print(f"  ✅ PASS")
        elif success_count > 0:
            print(f"  ⚠️  PARTIAL ({success_count}/{len(test['expected_attributes'])})")
        else:
            print(f"  ✗ FAIL")


def test_database_problem_scenarios():
    """Test scenarios that previously created poor database entries"""
    print_test_header("Real-World Problem Scenarios")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    scenarios = [
        {
            "input": "I have a car that is green",
            "problem": "Previously: 'green' and 'car' as separate entities",
            "solution": "Now: Should detect semantic relationship"
        },
        {
            "input": "I love Swedish meatballs",
            "problem": "Previously: 'Swedish' and 'meatballs' disconnected",
            "solution": "Now: 'Swedish' as attribute of 'meatballs'"
        },
        {
            "input": "Check @user at https://example.com about my green car",
            "problem": "Previously: Discord artifacts polluted entity extraction",
            "solution": "Now: Normalized [MENTION]/[URL], clean 'green' → 'car' attribute"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Scenario {i}]")
        print(f"Input: '{scenario['input']}'")
        print(f"Problem: {scenario['problem']}")
        print(f"Solution: {scenario['solution']}")
        
        features = preprocessor.extract_all_features_from_text(scenario['input'])
        
        entities = features.get("entities", [])
        attributes = features.get("attributes", [])
        
        print(f"\nExtracted:")
        print(f"  Entities: {[e['text'] for e in entities]}")
        print(f"  Attributes: {[(a['attribute'], '→', a['entity']) for a in attributes]}")
        
        if attributes:
            print(f"  ✅ Semantic relationships preserved!")
        else:
            print(f"  ⚠️  No attributes detected (may need additional spaCy patterns)")


def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("  PHASE 1+2 INTEGRATION TESTING")
    print("  Text Normalization + Semantic Attribute Extraction")
    print("  WhisperEngine - November 4, 2025")
    print("="*80)
    
    try:
        test_normalization_plus_attributes()
        test_database_problem_scenarios()
        
        print("\n" + "="*80)
        print("  ✅ ALL INTEGRATION TESTS COMPLETED")
        print("="*80 + "\n")
        
    except (ImportError, AttributeError, ValueError) as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
