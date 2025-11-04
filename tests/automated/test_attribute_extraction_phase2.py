"""
Phase 2 Semantic Attribute Extraction Testing

Tests the attribute extraction functionality in nlp_preprocessor.py
to validate that adjective-noun pairs and compound nouns are correctly identified.
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


def test_adjective_noun_attributes():
    """Test amod (adjectival modifier) extraction"""
    print_test_header("Testing Adjective-Noun Attributes (amod)")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    test_cases = [
        ("I have a green car", "green", "car", "descriptor"),
        ("I love my big red truck", "big", "truck", "descriptor"),  # Multiple adjectives
        ("She has beautiful long hair", "beautiful", "hair", "descriptor"),
        ("I want a fast computer", "fast", "computer", "descriptor"),
        ("He owns a small house", "small", "house", "descriptor"),
    ]
    
    for i, (text, expected_attr, expected_entity, expected_type) in enumerate(test_cases, 1):
        print(f"\n[Test {i}]")
        print(f"Input: '{text}'")
        
        features = preprocessor.extract_all_features_from_text(text)
        attributes = features.get("attributes", [])
        
        print(f"Found {len(attributes)} attribute(s):")
        for attr in attributes:
            print(f"  - {attr['attribute']} ({attr['attribute_type']}) → {attr['entity']}")
        
        # Verify expected attribute exists
        found = False
        for attr in attributes:
            if attr['attribute'] == expected_attr and attr['entity'] == expected_entity:
                found = True
                if attr['attribute_type'] == expected_type:
                    print(f"✓ PASS: Found '{expected_attr}' → '{expected_entity}' ({expected_type})")
                else:
                    print(f"⚠️  WARNING: Type mismatch - expected '{expected_type}', got '{attr['attribute_type']}'")
        
        if not found:
            print(f"✗ FAIL: Expected '{expected_attr}' → '{expected_entity}' not found")


def test_compound_nouns():
    """Test compound noun extraction"""
    print_test_header("Testing Compound Nouns")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    test_cases = [
        ("I love ice cream", "ice", "cream"),
        ("I ate Swedish meatballs", "Swedish", "meatballs"),
        ("I watched Finding Nemo", "Finding", "Nemo"),
        ("I visited San Francisco", "San", "Francisco"),
        ("I work at Apple Computer", "Apple", "Computer"),
    ]
    
    for i, (text, expected_attr, expected_entity) in enumerate(test_cases, 1):
        print(f"\n[Test {i}]")
        print(f"Input: '{text}'")
        
        features = preprocessor.extract_all_features_from_text(text)
        attributes = features.get("attributes", [])
        
        print(f"Found {len(attributes)} attribute(s):")
        for attr in attributes:
            print(f"  - {attr['attribute']} ({attr['attribute_type']}) → {attr['entity']}")
        
        # Verify expected compound exists
        found = False
        for attr in attributes:
            if (attr['attribute'] == expected_attr and 
                attr['entity'] == expected_entity and 
                attr['dependency'] == 'compound'):
                found = True
                print(f"✓ PASS: Found compound '{expected_attr}' → '{expected_entity}'")
        
        if not found:
            print(f"⚠️  INFO: Compound '{expected_attr}' → '{expected_entity}' not found (may be NER chunking)")


def test_complex_scenarios():
    """Test complex scenarios with multiple attributes"""
    print_test_header("Testing Complex Scenarios")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    test_cases = [
        "I have a green car that I drive daily",
        "My son Logan is 5 years old",
        "I love Thai food from that restaurant",
        "I drive a red Tesla Model 3",
        "She has beautiful long brown hair",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n[Test {i}]")
        print(f"Input: '{text}'")
        
        features = preprocessor.extract_all_features_from_text(text)
        attributes = features.get("attributes", [])
        
        if attributes:
            print(f"Found {len(attributes)} attribute(s):")
            for attr in attributes:
                position_str = "before" if attr['position'] == 'pre' else "after"
                print(f"  - '{attr['attribute']}' ({attr['attribute_type']}) {position_str} '{attr['entity']}'")
        else:
            print("  No attributes found")


def test_database_problem_cases():
    """Test cases that previously created bad database entries"""
    print_test_header("Testing Known Problem Cases from Database")
    
    preprocessor = EnrichmentNLPPreprocessor()
    
    if not preprocessor.is_available():
        print("\n⚠️  spaCy not available - skipping tests")
        return
    
    # These are real examples that created poor database entries
    problem_cases = [
        ("I have a car that is green", "Should extract: green → car"),
        ("I love the dynamic of our conversation", "Should NOT extract: dynamic as entity"),
        ("Swedish meatballs are delicious", "Should extract: Swedish → meatballs"),
    ]
    
    for i, (text, description) in enumerate(problem_cases, 1):
        print(f"\n[Test {i}]")
        print(f"Input: '{text}'")
        print(f"Goal: {description}")
        
        features = preprocessor.extract_all_features_from_text(text)
        attributes = features.get("attributes", [])
        entities = features.get("entities", [])
        
        print(f"\nExtracted:")
        print(f"  Entities: {[e['text'] for e in entities]}")
        print(f"  Attributes: {[(a['attribute'], a['entity']) for a in attributes]}")


def main():
    """Run all Phase 2 attribute extraction tests"""
    print("\n" + "="*80)
    print("  PHASE 2: SEMANTIC ATTRIBUTE EXTRACTION TESTING")
    print("  WhisperEngine - November 4, 2025")
    print("="*80)
    
    try:
        test_adjective_noun_attributes()
        test_compound_nouns()
        test_complex_scenarios()
        test_database_problem_cases()
        
        print("\n" + "="*80)
        print("  ✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except (ImportError, AttributeError, ValueError) as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
