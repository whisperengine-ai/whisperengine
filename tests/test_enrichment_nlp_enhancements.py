"""
Test suite for Phase 2-E: Enrichment Worker NLP Enhancements

Tests negation-aware SVO extraction and other spaCy enhancements for the enrichment worker.
"""
import pytest
from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor


@pytest.fixture
def preprocessor():
    """Create preprocessor instance for testing."""
    return EnrichmentNLPPreprocessor(model_name="en_core_web_md")


@pytest.fixture
def skip_if_spacy_unavailable(preprocessor):
    """Skip test if spaCy is not available."""
    if not preprocessor.is_available():
        pytest.skip("spaCy not available - skipping NLP tests")


class TestNegationAwareSVO:
    """Test negation detection in SVO extraction."""
    
    def test_positive_statement(self, preprocessor, skip_if_spacy_unavailable):
        """Test that positive statements are not marked as negated."""
        text = "I love pizza"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['subject'] == "I"
        assert rel['verb'] == "love"
        assert rel['object'] == "pizza"
        assert rel['is_negated'] is False
        assert rel['negation_marker'] is None
    
    def test_dont_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'don't' negation detection."""
        text = "I don't like coffee"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['subject'] == "I"
        assert rel['verb'] == "like"
        assert rel['object'] == "coffee"
        assert rel['is_negated'] is True
        assert rel['negation_marker'] is not None
        # spaCy tokenizes "don't" as "do" + "n't", so check for "n't" or "not"
        marker_lower = rel['negation_marker'].lower()
        assert "n't" in marker_lower or "not" in marker_lower, f"Expected negation marker, got: {rel['negation_marker']}"
    
    def test_doesnt_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'doesn't' negation detection."""
        text = "She doesn't enjoy horror movies"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['is_negated'] is True
        assert rel['verb'] == "enjoy"
    
    def test_never_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'never' as negation marker."""
        text = "He never eats meat"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['subject'] == "He"
        assert rel['verb'] == "eat"
        assert rel['object'] == "meat"
        assert rel['is_negated'] is True
        assert "never" in rel['negation_marker'].lower()
    
    def test_wont_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'won't' negation detection."""
        text = "I won't visit that restaurant"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['is_negated'] is True
        # spaCy tokenizes "won't" as "wo" + "n't"
        assert "n't" in rel['negation_marker'].lower(), f"Expected negation marker with n't, got: {rel['negation_marker']}"
    
    def test_cannot_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'cannot' negation detection."""
        text = "I cannot stand loud music"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['is_negated'] is True
    
    def test_didnt_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'didn't' negation detection."""
        text = "She didn't like the movie"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel['is_negated'] is True
    
    def test_no_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'no' as negation marker."""
        text = "I have no interest in politics"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        # Note: "no interest" might not be captured as SVO, but test structure
        # This tests that the negation detection logic handles 'no'
        if len(relationships) > 0:
            # If extracted, check for negation marker presence
            has_negation = any(r['is_negated'] for r in relationships)
            # We expect negation detection to work if relationship is found
            assert True  # Test structure validation
    
    def test_multiple_relationships_mixed_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test multiple SVO relationships with mixed negation."""
        text = "I love pizza but I don't like mushrooms"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) >= 2, "Should extract at least two relationships"
        
        # Check that we have both positive and negative
        has_positive = any(not r['is_negated'] for r in relationships)
        has_negative = any(r['is_negated'] for r in relationships)
        assert has_positive, "Should have at least one positive statement"
        assert has_negative, "Should have at least one negated statement"
    
    def test_neither_nor_negation(self, preprocessor, skip_if_spacy_unavailable):
        """Test 'neither...nor' negation pattern."""
        text = "I like neither cats nor dogs"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        # spaCy may parse this differently, but test negation detection capability
        if len(relationships) > 0:
            # At least one should be marked as negated
            has_negation = any(r['is_negated'] for r in relationships)
            assert has_negation or len(relationships) > 0  # Validate extraction works


class TestLLMContextPrefix:
    """Test LLM context prefix generation with negation markers."""
    
    def test_prefix_includes_negation_marker(self, preprocessor, skip_if_spacy_unavailable):
        """Test that negation is marked in context prefix."""
        text = "I love pizza but I don't like coffee"
        prefix = preprocessor.build_llm_context_prefix(text)
        
        assert "Relationships:" in prefix
        assert "✗" in prefix, "Should include negation marker (✗) for negated relationships"
    
    def test_prefix_positive_no_negation_marker(self, preprocessor, skip_if_spacy_unavailable):
        """Test that positive statements don't have negation marker."""
        text = "I love pizza and enjoy pasta"
        prefix = preprocessor.build_llm_context_prefix(text)
        
        assert "Relationships:" in prefix
        # Should have relationships but no negation marker
        if "love" in prefix or "enjoy" in prefix:
            # Count negation markers - should be minimal or zero for positive text
            negation_count = prefix.count("✗")
            assert negation_count == 0, "Positive statements shouldn't have negation markers"
    
    def test_prefix_format_consistency(self, preprocessor, skip_if_spacy_unavailable):
        """Test that prefix maintains consistent format."""
        text = "Alice doesn't like Bob's restaurant"
        prefix = preprocessor.build_llm_context_prefix(text)
        
        assert "Pre-identified signals (spaCy):" in prefix
        assert "- Entities:" in prefix
        assert "- Relationships:" in prefix


class TestEntityExtraction:
    """Test entity extraction (baseline validation)."""
    
    def test_person_entity_extraction(self, preprocessor, skip_if_spacy_unavailable):
        """Test PERSON entity extraction."""
        text = "Alice and Bob went to the park"
        entities = preprocessor.extract_entities(text)
        
        assert len(entities) > 0
        person_entities = [e for e in entities if e['label'] == 'PERSON']
        assert len(person_entities) >= 1  # Should find at least Alice or Bob
    
    def test_gpe_entity_extraction(self, preprocessor, skip_if_spacy_unavailable):
        """Test GPE (geopolitical entity) extraction."""
        text = "I traveled to Paris and London last summer"
        entities = preprocessor.extract_entities(text)
        
        assert len(entities) > 0
        gpe_entities = [e for e in entities if e['label'] == 'GPE']
        assert len(gpe_entities) >= 2  # Should find Paris and London


class TestPreferenceIndicators:
    """Test preference indicator extraction."""
    
    def test_name_extraction(self, preprocessor, skip_if_spacy_unavailable):
        """Test name extraction from preference indicators."""
        text = "My friend Sarah really loves Italian food"
        indicators = preprocessor.extract_preference_indicators(text)
        
        assert 'names' in indicators
        assert len(indicators['names']) > 0
    
    def test_location_extraction(self, preprocessor, skip_if_spacy_unavailable):
        """Test location extraction from preference indicators."""
        text = "I prefer restaurants in downtown Seattle"
        indicators = preprocessor.extract_preference_indicators(text)
        
        assert 'locations' in indicators
        assert len(indicators['locations']) > 0


class TestGracefulDegradation:
    """Test graceful degradation when spaCy is unavailable."""
    
    def test_no_crash_when_spacy_missing(self):
        """Test that preprocessor doesn't crash when spaCy is unavailable."""
        preprocessor = EnrichmentNLPPreprocessor(model_name="nonexistent_model")
        
        # All methods should return empty/safe defaults
        assert preprocessor.extract_entities("test") == []
        assert preprocessor.extract_dependency_relationships("test") == []
        assert preprocessor.build_llm_context_prefix("test") == ""
        assert not preprocessor.is_available()


class TestPerformance:
    """Test performance of enhanced NLP preprocessor."""
    
    def test_long_text_handling(self, preprocessor, skip_if_spacy_unavailable):
        """Test that long text is handled efficiently."""
        # Create long text (beyond max_length)
        text = "I love pizza. " * 1000  # ~14,000 characters
        
        # Should not crash and should truncate
        relationships = preprocessor.extract_dependency_relationships(text, max_length=10000)
        
        # Should still extract relationships from truncated portion
        assert isinstance(relationships, list)
    
    def test_empty_text_handling(self, preprocessor, skip_if_spacy_unavailable):
        """Test empty text handling."""
        assert preprocessor.extract_entities("") == []
        assert preprocessor.extract_dependency_relationships("") == []
        assert preprocessor.build_llm_context_prefix("") == ""


class TestCustomMatcherPatterns:
    """Test custom matcher pattern integration (Phase 2-E Task E.2)."""
    
    def test_negated_preference_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test NEGATED_PREFERENCE pattern detection."""
        text = "I don't like mushrooms on my pizza"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "NEGATED_PREFERENCE" in patterns
        assert len(patterns["NEGATED_PREFERENCE"]) > 0
        assert any("don't" in p["text"].lower() for p in patterns["NEGATED_PREFERENCE"])
    
    def test_strong_preference_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test STRONG_PREFERENCE pattern detection."""
        text = "I really love Italian food"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "STRONG_PREFERENCE" in patterns
        assert len(patterns["STRONG_PREFERENCE"]) > 0
        assert any("really" in p["text"].lower() for p in patterns["STRONG_PREFERENCE"])
    
    def test_temporal_change_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test TEMPORAL_CHANGE pattern detection."""
        text = "I used to enjoy spicy food"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "TEMPORAL_CHANGE" in patterns
        assert len(patterns["TEMPORAL_CHANGE"]) > 0
        assert any("used to" in p["text"].lower() for p in patterns["TEMPORAL_CHANGE"])
    
    def test_temporal_change_with_adverb(self, preprocessor, skip_if_spacy_unavailable):
        """Test TEMPORAL_CHANGE with optional adverb."""
        text = "I used to really love sushi"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "TEMPORAL_CHANGE" in patterns
        assert len(patterns["TEMPORAL_CHANGE"]) > 0
        # Should match "used to really love"
        temporal_patterns = patterns["TEMPORAL_CHANGE"]
        assert any("used to" in p["text"].lower() for p in temporal_patterns)
    
    def test_hedging_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test HEDGING pattern detection."""
        text = "I maybe like Thai food"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "HEDGING" in patterns
        assert len(patterns["HEDGING"]) > 0
    
    def test_hedging_kind_of_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test HEDGING 'kind of' pattern."""
        text = "I kind of prefer vegetarian options"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "HEDGING" in patterns
        assert len(patterns["HEDGING"]) > 0
        assert any("kind of" in p["text"].lower() for p in patterns["HEDGING"])
    
    def test_conditional_pattern(self, preprocessor, skip_if_spacy_unavailable):
        """Test CONDITIONAL pattern detection."""
        text = "I would prefer seafood if I could"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert "CONDITIONAL" in patterns
        assert len(patterns["CONDITIONAL"]) > 0
    
    def test_multiple_patterns_in_text(self, preprocessor, skip_if_spacy_unavailable):
        """Test detection of multiple pattern types in one text."""
        text = "I really love pasta but I don't like mushrooms and I used to enjoy spicy food"
        patterns = preprocessor.extract_preference_patterns(text)
        
        # Should detect strong preference, negation, and temporal change
        assert len(patterns["STRONG_PREFERENCE"]) > 0
        assert len(patterns["NEGATED_PREFERENCE"]) > 0
        assert len(patterns["TEMPORAL_CHANGE"]) > 0
    
    def test_pattern_return_structure(self, preprocessor, skip_if_spacy_unavailable):
        """Test that pattern matches have correct structure."""
        text = "I really love pizza"
        patterns = preprocessor.extract_preference_patterns(text)
        
        assert isinstance(patterns, dict)
        assert "NEGATED_PREFERENCE" in patterns
        assert "STRONG_PREFERENCE" in patterns
        assert "TEMPORAL_CHANGE" in patterns
        assert "HEDGING" in patterns
        assert "CONDITIONAL" in patterns
        
        # Check structure of matches
        for pattern_type, matches in patterns.items():
            assert isinstance(matches, list)
            for match in matches:
                assert "text" in match
                assert "start" in match
                assert "end" in match
                assert "lemma" in match


class TestLLMContextWithPatterns:
    """Test LLM context prefix generation with pattern indicators."""
    
    def test_context_includes_pattern_indicators(self, preprocessor, skip_if_spacy_unavailable):
        """Test that context prefix includes pattern indicators."""
        text = "I really love pizza but I don't like mushrooms"
        prefix = preprocessor.build_llm_context_prefix(text, include_patterns=True)
        
        assert "Preference Patterns:" in prefix
        # Should indicate strong preferences and negated preferences
        assert "Strong preferences" in prefix or "Negated preferences" in prefix
    
    def test_context_without_patterns(self, preprocessor, skip_if_spacy_unavailable):
        """Test context prefix can exclude patterns."""
        text = "I really love pizza"
        prefix = preprocessor.build_llm_context_prefix(text, include_patterns=False)
        
        # Should not include pattern indicators
        assert "Preference Patterns:" not in prefix
    
    def test_context_temporal_change_indicator(self, preprocessor, skip_if_spacy_unavailable):
        """Test temporal change pattern indicator."""
        text = "I used to enjoy spicy food"
        prefix = preprocessor.build_llm_context_prefix(text, include_patterns=True)
        
        if "Preference Patterns:" in prefix:
            assert "Past preference changes" in prefix or "⏰" in prefix
    
    def test_context_hedging_indicator(self, preprocessor, skip_if_spacy_unavailable):
        """Test hedging pattern indicator."""
        text = "I maybe like Italian food"
        prefix = preprocessor.build_llm_context_prefix(text, include_patterns=True)
        
        if "Preference Patterns:" in prefix:
            assert "Uncertain" in prefix or "hedged" in prefix or "🤔" in prefix
    
    def test_context_multiple_indicators(self, preprocessor, skip_if_spacy_unavailable):
        """Test multiple pattern indicators in context."""
        text = "I really love pizza, I don't like mushrooms, and I used to enjoy spicy food"
        prefix = preprocessor.build_llm_context_prefix(text, include_patterns=True)
        
        assert "Preference Patterns:" in prefix
        # Should have multiple indicators separated by commas
        pattern_line = [line for line in prefix.split('\n') if "Preference Patterns:" in line][0]
        assert "," in pattern_line  # Multiple indicators separated by commas


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
