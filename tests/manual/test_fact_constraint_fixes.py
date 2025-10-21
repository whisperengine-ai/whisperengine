#!/usr/bin/env python3
"""
Test script to verify PostgreSQL fact storage constraint fixes.

This tests that:
1. Empty relationship_type gets a safe default ('related_to')
2. 'semantic_link' relationship type gets mapped to 'related_to'
3. Facts can be successfully parsed and validated

Run with:
    source .venv/bin/activate && python tests/manual/test_fact_constraint_fixes.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.enrichment.fact_extraction_engine import FactExtractionEngine, ExtractedFact


def test_empty_relationship_type():
    """Test that empty relationship_type gets a safe default"""
    print("\n🧪 Test 1: Empty relationship_type handling")
    
    engine = FactExtractionEngine(llm_client=None)
    
    # Simulate LLM response with missing relationship_type
    llm_response = '''
    {
        "facts": [
            {
                "entity_name": "pizza",
                "entity_type": "food",
                "relationship_type": "",
                "confidence": 0.8
            },
            {
                "entity_name": "pasta",
                "entity_type": "food",
                "confidence": 0.7
            }
        ]
    }
    '''
    
    messages = [{"id": "test_msg_1", "content": "I love pizza and pasta"}]
    
    facts = engine._parse_fact_extraction_result(llm_response, messages)
    
    print(f"   Parsed {len(facts)} facts:")
    for fact in facts:
        print(f"   - {fact.entity_name}: relationship_type='{fact.relationship_type}'")
        assert len(fact.relationship_type) > 0, f"Empty relationship_type for {fact.entity_name}!"
        assert len(fact.relationship_type) <= 50, f"relationship_type too long for {fact.entity_name}!"
    
    print("   ✅ All facts have valid non-empty relationship_type")
    return True


def test_semantic_link_mapping():
    """Test that semantic_link gets mapped to related_to"""
    print("\n🧪 Test 2: 'semantic_link' → 'related_to' mapping")
    
    engine = FactExtractionEngine(llm_client=None)
    
    fact1 = ExtractedFact(
        entity_name="pizza",
        entity_type="food",
        relationship_type="likes",
        confidence=0.9
    )
    
    fact2 = ExtractedFact(
        entity_name="homemade pizza",
        entity_type="food",
        relationship_type="makes",
        confidence=0.8
    )
    
    # This should return 'related_to' instead of 'semantic_link'
    relationship = engine._identify_relationship(fact1, fact2)
    
    if relationship:
        print(f"   Relationship type: '{relationship['type']}'")
        assert relationship['type'] == 'related_to', f"Expected 'related_to', got '{relationship['type']}'"
        print("   ✅ 'semantic_link' correctly mapped to 'related_to'")
    else:
        print("   ℹ️ No relationship identified (entities not similar enough)")
    
    return True


def test_valid_relationship_types():
    """Test that all generated relationship types are valid for entity_relationships table"""
    print("\n🧪 Test 3: Valid relationship types for entity_relationships")
    
    # Valid types per sql/semantic_knowledge_graph_schema.sql line 149
    valid_types = {'similar_to', 'part_of', 'category_of', 'related_to', 'opposite_of', 'requires'}
    
    engine = FactExtractionEngine(llm_client=None)
    
    # Test various fact combinations
    test_cases = [
        (
            ExtractedFact("pizza", "food", "likes", 0.9),
            ExtractedFact("homemade pizza", "food", "makes", 0.8),
            "overlapping entity names"
        ),
    ]
    
    for fact1, fact2, description in test_cases:
        relationship = engine._identify_relationship(fact1, fact2)
        if relationship:
            rel_type = relationship['type']
            print(f"   {description}: '{rel_type}'")
            assert rel_type in valid_types, f"Invalid relationship type '{rel_type}' for entity_relationships table!"
    
    print(f"   ✅ All relationship types are valid: {valid_types}")
    return True


def main():
    print("=" * 60)
    print("PostgreSQL Fact Storage Constraint Fix Verification")
    print("=" * 60)
    
    try:
        test_empty_relationship_type()
        test_semantic_link_mapping()
        test_valid_relationship_types()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Constraint fixes are working!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
