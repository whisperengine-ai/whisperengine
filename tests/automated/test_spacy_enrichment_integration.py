#!/usr/bin/env python3
"""
Direct Python test for spaCy enrichment integration.

Tests all three spaCy code paths:
1. Preference extraction (names, locations, pronouns, Q&A)
2. Fact extraction (entities, SVO relationships)
3. Summarization (scaffold with entities/actions)

Usage:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/automated/test_spacy_enrichment_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor
from src.enrichment.fact_extraction_engine import FactExtractionEngine
from src.enrichment.summarization_engine import SummarizationEngine


def test_preprocessor_availability():
    """Test 1: Verify spaCy preprocessor loads correctly."""
    print("\n" + "="*80)
    print("TEST 1: SpaCy Preprocessor Availability")
    print("="*80)
    
    try:
        preprocessor = EnrichmentNLPPreprocessor()
        
        if preprocessor.is_available():
            print("✅ spaCy preprocessor loaded successfully")
            print(f"   Model: {preprocessor._nlp.meta['name']}")
            print(f"   Language: {preprocessor._nlp.meta['lang']}")
            print(f"   Version: {preprocessor._nlp.meta['version']}")
            return preprocessor
        else:
            print("❌ spaCy preprocessor not available")
            return None
    except Exception as e:
        print(f"❌ Failed to load preprocessor: {e}")
        return None


def test_preference_indicators(preprocessor):
    """Test 2: Extract preference indicators from sample conversation."""
    print("\n" + "="*80)
    print("TEST 2: Preference Indicator Extraction")
    print("="*80)
    
    # Sample conversation with rich preference signals
    conversation = """
    User: Hi! My name is Mark and I'm from San Francisco.
    Bot: Nice to meet you, Mark! How can I help you today?
    User: I prefer brief responses, please. What's the weather like?
    Bot: Sunny, 72°F.
    User: Perfect! By the way, you can call me Marc with a 'c' if you prefer.
    Bot: Got it, Marc! Anything else I can help with?
    User: Do you remember where I'm from?
    Bot: Yes, you mentioned San Francisco!
    User: Great memory! I also live near Golden Gate Park.
    """
    
    try:
        signals = preprocessor.extract_preference_indicators(conversation)
        
        print(f"✅ Extracted preference indicators:")
        print(f"   Names found: {signals.get('names', [])}")
        print(f"   Locations found: {signals.get('locations', [])}")
        print(f"   Pronoun counts: {signals.get('pronoun_counts', {})}")
        print(f"   Question sentences: {len(signals.get('question_sentences', []))} total")
        
        # Show first few questions
        questions = signals.get('question_sentences', [])[:3]
        if questions:
            print(f"   Sample questions:")
            for q in questions:
                print(f"     - {q}")
        
        # Validate expected signals
        assert len(signals.get('names', [])) >= 2, "Should find at least 2 names (Mark, Marc)"
        assert len(signals.get('locations', [])) >= 1, "Should find at least 1 location (San Francisco)"
        assert len(signals.get('question_sentences', [])) >= 1, "Should find at least 1 question"
        
        print("✅ All preference indicator assertions passed")
        return True
        
    except Exception as e:
        print(f"❌ Preference indicator extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_entity_extraction(preprocessor):
    """Test 3: Extract entities and relationships from conversation."""
    print("\n" + "="*80)
    print("TEST 3: Entity and Relationship Extraction")
    print("="*80)
    
    conversation = """
    User: I work at Google in Mountain View, California. My manager is Sarah Johnson.
    Bot: That sounds interesting! What do you do at Google?
    User: I'm a software engineer working on machine learning projects.
    Bot: Impressive! How long have you been there?
    User: Started in January 2023, so about two years now.
    """
    
    try:
        entities = preprocessor.extract_entities(conversation)
        relationships = preprocessor.extract_dependency_relationships(conversation)
        
        print("✅ Extracted entities:")
        # Group entities by label
        entities_by_label = {}
        for ent in entities:
            entities_by_label.setdefault(ent['label'], []).append(ent['text'])
        
        for entity_type, entity_list in entities_by_label.items():
            if entity_list:
                print(f"   {entity_type}: {entity_list}")
        
        print("\n✅ Extracted relationships (SVO triples):")
        for rel in relationships[:5]:  # Show first 5
            print(f"   {rel['subject']} --[{rel['verb']}]--> {rel['object']}")
        
        # Validate expected entities
        assert len(entities) >= 3, f"Should find at least 3 entities, found {len(entities)}"
        assert len(relationships) >= 1, f"Should find at least 1 SVO relationship, found {len(relationships)}"
        
        print(f"\n✅ All entity extraction assertions passed ({len(entities)} entities, {len(relationships)} relationships)")
        return True
        
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_context_prefix(preprocessor):
    """Test 4: Build LLM context prefix for fact extraction."""
    print("\n" + "="*80)
    print("TEST 4: LLM Context Prefix Generation (Fact Extraction)")
    print("="*80)
    
    conversation = """
    User: I recently moved to Seattle and started a new job at Microsoft.
    Bot: Congratulations on the new role! What will you be working on?
    User: I'll be joining the Azure team as a cloud architect.
    """
    
    try:
        context_prefix = preprocessor.build_llm_context_prefix(conversation)
        
        print(f"✅ Generated LLM context prefix ({len(context_prefix)} chars):")
        print("-" * 80)
        print(context_prefix)
        print("-" * 80)
        
        # Validate expected content
        assert len(context_prefix) > 50, "Context prefix should be substantial"
        assert "Entities:" in context_prefix or "Relationships:" in context_prefix, \
               "Should contain entity or relationship information"
        
        print("\n✅ Context prefix generation passed")
        return True
        
    except Exception as e:
        print(f"❌ Context prefix generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_scaffold(preprocessor):
    """Test 5: Build summary scaffold for conversation summarization."""
    print("\n" + "="*80)
    print("TEST 5: Summary Scaffold Generation")
    print("="*80)
    
    conversation = """
    User: I've been learning Python for the past three months.
    Bot: That's great! What inspired you to start learning Python?
    User: I want to transition into data science. I've been working through online courses.
    Bot: Excellent choice! Have you started any projects yet?
    User: Yes, I built a simple data visualization tool using matplotlib and pandas.
    Bot: That's a solid start! Data visualization is crucial in data science.
    """
    
    try:
        scaffold_dict = preprocessor.build_summary_scaffold(conversation)
        scaffold_string = preprocessor.build_scaffold_string(scaffold_dict)
        
        print(f"✅ Generated summary scaffold dict:")
        print("-" * 80)
        print(f"Entities: {scaffold_dict.get('entities', {})}")
        print(f"Main Actions: {scaffold_dict.get('main_actions', [])}")
        print(f"Topics: {scaffold_dict.get('topics', [])}")
        print("-" * 80)
        print(f"\n✅ Scaffold string ({len(scaffold_string)} chars):")
        print("-" * 80)
        print(scaffold_string)
        print("-" * 80)
        
        # Validate expected content
        assert isinstance(scaffold_dict, dict), "Scaffold should be a dictionary"
        assert 'entities' in scaffold_dict or 'main_actions' in scaffold_dict, \
               "Should contain entities or actions"
        assert len(scaffold_string) > 50, "Scaffold string should be substantial"
        
        print("\n✅ Summary scaffold generation passed")
        return True
        
    except Exception as e:
        print(f"❌ Summary scaffold generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fact_extraction_integration(preprocessor):
    """Test 6: Integration test with FactExtractionEngine."""
    print("\n" + "="*80)
    print("TEST 6: FactExtractionEngine Integration with spaCy")
    print("="*80)
    
    try:
        # Initialize fact extraction engine with preprocessor
        fact_engine = FactExtractionEngine(
            llm_client=None,  # Mock LLM - we're testing preprocessing only
            model="anthropic/claude-sonnet-4.5",
            preprocessor=preprocessor
        )
        
        print("✅ FactExtractionEngine initialized with spaCy preprocessor")
        print(f"   Preprocessor available: {fact_engine.preprocessor is not None}")
        print(f"   Preprocessor type: {type(fact_engine.preprocessor).__name__}")
        
        # Test context prefix generation (simulating what happens in _extract_facts_from_chunk)
        conversation = "User works at Apple in Cupertino. Manager is Tim Cook."
        
        if fact_engine.preprocessor and fact_engine.preprocessor.is_available():
            context_prefix = fact_engine.preprocessor.build_llm_context_prefix(conversation)
            print(f"✅ Generated context prefix via FactExtractionEngine:")
            print(f"   Length: {len(context_prefix)} chars")
            print(f"   Preview: {context_prefix[:100]}...")
        
        print("\n✅ FactExtractionEngine integration passed")
        return True
        
    except Exception as e:
        print(f"❌ FactExtractionEngine integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_summarization_integration(preprocessor):
    """Test 7: Integration test with SummarizationEngine."""
    print("\n" + "="*80)
    print("TEST 7: SummarizationEngine Integration with spaCy")
    print("="*80)
    
    try:
        # Initialize summarization engine with preprocessor
        summary_engine = SummarizationEngine(
            llm_client=None,  # Mock LLM - we're testing preprocessing only
            llm_model="anthropic/claude-sonnet-4.5",
            preprocessor=preprocessor
        )
        
        print("✅ SummarizationEngine initialized with spaCy preprocessor")
        print(f"   Preprocessor available: {summary_engine.preprocessor is not None}")
        print(f"   Preprocessor type: {type(summary_engine.preprocessor).__name__}")
        
        # Test scaffold generation (simulating what happens in generate_conversation_summary)
        conversation = "User discussed career transition to data science. Learning Python and pandas."
        
        if summary_engine.preprocessor and summary_engine.preprocessor.is_available():
            scaffold = summary_engine.preprocessor.build_summary_scaffold(conversation)
            scaffold_str = summary_engine.preprocessor.build_scaffold_string(scaffold)
            print(f"✅ Generated summary scaffold via SummarizationEngine:")
            print(f"   Dict length: {len(str(scaffold))} chars")
            print(f"   String length: {len(scaffold_str)} chars")
            print(f"   Preview: {scaffold_str[:100]}...")
        
        print("\n✅ SummarizationEngine integration passed")
        return True
        
    except Exception as e:
        print(f"❌ SummarizationEngine integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all spaCy enrichment integration tests."""
    print("\n" + "="*80)
    print("🧪 SPACY ENRICHMENT INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing spaCy integration in WhisperEngine enrichment worker")
    print("Models: spaCy 3.8.7 with en_core_web_md")
    print("="*80)
    
    results = []
    
    # Test 1: Preprocessor availability
    preprocessor = test_preprocessor_availability()
    results.append(("Preprocessor Availability", preprocessor is not None))
    
    if not preprocessor:
        print("\n❌ Cannot continue - spaCy preprocessor failed to load")
        return False
    
    # Test 2-5: Core preprocessing functions
    results.append(("Preference Indicators", test_preference_indicators(preprocessor)))
    results.append(("Entity Extraction", test_entity_extraction(preprocessor)))
    results.append(("LLM Context Prefix", test_llm_context_prefix(preprocessor)))
    results.append(("Summary Scaffold", test_summary_scaffold(preprocessor)))
    
    # Test 6-7: Engine integrations
    results.append(("FactExtractionEngine Integration", await test_fact_extraction_integration(preprocessor)))
    results.append(("SummarizationEngine Integration", await test_summarization_integration(preprocessor)))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SpaCy enrichment integration is working correctly!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review output above")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
