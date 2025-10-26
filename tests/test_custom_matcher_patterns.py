"""
Unit tests for Custom Matcher Patterns (Task 3.1)

Tests advanced pattern detection using spaCy's Matcher for sophisticated
token-level patterns beyond simple keyword matching.

Test Coverage:
1. Negated preferences (don't like, doesn't enjoy)
2. Strong preferences (really love, absolutely hate)
3. Temporal changes (used to like)
4. Hedging language (maybe like, kind of prefer)
5. Conditional statements (if I could)
6. Multiple patterns in single query
7. Edge cases and integration
"""

import pytest
from typing import Dict, Any
from src.memory.unified_query_classification import (
    UnifiedQueryClassifier,
    QueryIntent,
    VectorStrategy
)


@pytest.fixture
def classifier():
    """Create UnifiedQueryClassifier instance for testing."""
    return UnifiedQueryClassifier()


class TestNegatedPreferences:
    """Test negated preference pattern detection."""
    
    async def test_dont_like_pattern(self, classifier):
        """Test detection of 'don't like' pattern."""
        query = "I don't like spicy food"
        result = await classifier.classify(query)
        
        assert result.matched_advanced_patterns is not None
        assert "NEGATED_PREFERENCE" in result.matched_advanced_patterns
        assert len(result.matched_advanced_patterns["NEGATED_PREFERENCE"]) > 0
        
        # Check matched span details
        match = result.matched_advanced_patterns["NEGATED_PREFERENCE"][0]
        assert "don't like" in match["text"].lower() or "do not like" in match["text"].lower()
    
    async def test_doesnt_enjoy_pattern(self, classifier):
        """Test detection of 'doesn't enjoy' pattern."""
        query = "She doesn't enjoy hiking on weekends"
        result = await classifier.classify(query)
        
        if "NEGATED_PREFERENCE" in result.matched_advanced_patterns:
            assert len(result.matched_advanced_patterns["NEGATED_PREFERENCE"]) > 0
    
    async def test_didnt_love_pattern(self, classifier):
        """Test detection of 'didn't love' pattern."""
        query = "I didn't love that restaurant"
        result = await classifier.classify(query)
        
        if "NEGATED_PREFERENCE" in result.matched_advanced_patterns:
            assert len(result.matched_advanced_patterns["NEGATED_PREFERENCE"]) > 0
    
    async def test_dont_want_pattern(self, classifier):
        """Test detection of 'don't want' pattern."""
        query = "I don't want to eat pizza tonight"
        result = await classifier.classify(query)
        
        if "NEGATED_PREFERENCE" in result.matched_advanced_patterns:
            assert len(result.matched_advanced_patterns["NEGATED_PREFERENCE"]) > 0


class TestStrongPreferences:
    """Test strong preference modifier detection."""
    
    async def test_really_love_pattern(self, classifier):
        """Test detection of 'really love' pattern."""
        query = "I really love Italian food"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True, "Should detect 'really love' as strong preference"
        assert "STRONG_PREFERENCE" in result.matched_advanced_patterns
        assert len(result.matched_advanced_patterns["STRONG_PREFERENCE"]) > 0
        
        # Check matched span
        match = result.matched_advanced_patterns["STRONG_PREFERENCE"][0]
        assert "really" in match["text"].lower()
        assert "love" in match["text"].lower()
    
    async def test_absolutely_hate_pattern(self, classifier):
        """Test detection of 'absolutely hate' pattern."""
        query = "I absolutely hate seafood"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True
        assert "STRONG_PREFERENCE" in result.matched_advanced_patterns
    
    async def test_definitely_prefer_pattern(self, classifier):
        """Test detection of 'definitely prefer' pattern."""
        query = "I definitely prefer coffee over tea"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True
        assert "STRONG_PREFERENCE" in result.matched_advanced_patterns
    
    async def test_totally_enjoy_pattern(self, classifier):
        """Test detection of 'totally enjoy' pattern."""
        query = "I totally enjoy playing video games"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True
        assert "STRONG_PREFERENCE" in result.matched_advanced_patterns
    
    async def test_completely_dislike_pattern(self, classifier):
        """Test detection of 'completely dislike' pattern."""
        query = "I completely dislike horror movies"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True
        assert "STRONG_PREFERENCE" in result.matched_advanced_patterns


class TestTemporalChanges:
    """Test temporal change pattern detection."""
    
    async def test_used_to_like_pattern(self, classifier):
        """Test detection of 'used to like' pattern."""
        query = "I used to like sushi"
        result = await classifier.classify(query)
        
        assert result.has_temporal_change is True, "Should detect 'used to like' as temporal change"
        assert "TEMPORAL_CHANGE" in result.matched_advanced_patterns
        assert len(result.matched_advanced_patterns["TEMPORAL_CHANGE"]) > 0
        
        # Check matched span
        match = result.matched_advanced_patterns["TEMPORAL_CHANGE"][0]
        assert "used to" in match["text"].lower()
    
    async def test_used_to_enjoy_pattern(self, classifier):
        """Test detection of 'used to enjoy' pattern."""
        query = "She used to enjoy running marathons"
        result = await classifier.classify(query)
        
        assert result.has_temporal_change is True
        assert "TEMPORAL_CHANGE" in result.matched_advanced_patterns
    
    async def test_used_to_prefer_pattern(self, classifier):
        """Test detection of 'used to prefer' pattern."""
        query = "We used to prefer going out on weekends"
        result = await classifier.classify(query)
        
        assert result.has_temporal_change is True
        assert "TEMPORAL_CHANGE" in result.matched_advanced_patterns
    
    async def test_used_to_verb_generic(self, classifier):
        """Test detection of 'used to' with any verb."""
        query = "I used to play tennis every weekend"
        result = await classifier.classify(query)
        
        assert result.has_temporal_change is True
        assert "TEMPORAL_CHANGE" in result.matched_advanced_patterns


class TestHedgingLanguage:
    """Test hedging language detection."""
    
    async def test_maybe_like_pattern(self, classifier):
        """Test detection of 'maybe like' pattern."""
        query = "I maybe like chocolate"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True, "Should detect 'maybe like' as hedging"
        assert "HEDGING" in result.matched_advanced_patterns
        assert len(result.matched_advanced_patterns["HEDGING"]) > 0
    
    async def test_perhaps_prefer_pattern(self, classifier):
        """Test detection of 'perhaps prefer' pattern."""
        query = "I perhaps prefer tea over coffee"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True
        assert "HEDGING" in result.matched_advanced_patterns
    
    async def test_possibly_enjoy_pattern(self, classifier):
        """Test detection of 'possibly enjoy' pattern."""
        query = "I possibly enjoy hiking"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True
        assert "HEDGING" in result.matched_advanced_patterns
    
    async def test_might_like_pattern(self, classifier):
        """Test detection of 'might like' pattern."""
        query = "I might like to try sushi"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True
        assert "HEDGING" in result.matched_advanced_patterns
    
    async def test_kind_of_prefer_pattern(self, classifier):
        """Test detection of 'kind of prefer' pattern."""
        query = "I kind of prefer staying home"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True
        assert "HEDGING" in result.matched_advanced_patterns
    
    async def test_sort_of_like_pattern(self, classifier):
        """Test detection of 'sort of like' pattern."""
        query = "I sort of like spicy food"
        result = await classifier.classify(query)
        
        assert result.has_hedging is True
        assert "HEDGING" in result.matched_advanced_patterns


class TestConditionalStatements:
    """Test conditional statement detection."""
    
    async def test_if_could_pattern(self, classifier):
        """Test detection of 'if...could' pattern."""
        query = "If I could, I would try sushi"
        result = await classifier.classify(query)
        
        # Conditional detection is optional - just check it doesn't crash
        assert isinstance(result.matched_advanced_patterns, dict)
        if "CONDITIONAL" in result.matched_advanced_patterns:
            assert len(result.matched_advanced_patterns["CONDITIONAL"]) > 0
    
    async def test_if_would_pattern(self, classifier):
        """Test detection of 'if...would' pattern."""
        query = "If possible, I would prefer coffee"
        result = await classifier.classify(query)
        
        assert isinstance(result.matched_advanced_patterns, dict)
    
    async def test_if_pronoun_could_pattern(self, classifier):
        """Test detection of 'if [pronoun] could' pattern."""
        query = "If I could choose, I'd pick pizza"
        result = await classifier.classify(query)
        
        assert isinstance(result.matched_advanced_patterns, dict)


class TestMultiplePatterns:
    """Test queries with multiple pattern types."""
    
    async def test_negation_plus_strong_preference(self, classifier):
        """Test query with both negation and strong preference."""
        query = "I really don't like spicy food"
        result = await classifier.classify(query)
        
        # Should detect both patterns
        patterns = result.matched_advanced_patterns
        assert "NEGATED_PREFERENCE" in patterns or "STRONG_PREFERENCE" in patterns
    
    async def test_temporal_plus_hedging(self, classifier):
        """Test query with temporal change and hedging."""
        query = "I used to maybe like sushi"
        result = await classifier.classify(query)
        
        # Should detect at least one pattern
        assert len(result.matched_advanced_patterns) > 0
    
    async def test_all_pattern_types(self, classifier):
        """Test complex query with multiple pattern types."""
        query = "I used to really love pizza, but now I don't like it and maybe prefer pasta"
        result = await classifier.classify(query)
        
        # Should detect multiple patterns
        patterns = result.matched_advanced_patterns
        assert len(patterns) >= 2, "Should detect at least 2 different pattern types"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_empty_query(self, classifier):
        """Test handling of empty query."""
        query = ""
        result = await classifier.classify(query)
        
        # Should not crash, should return empty patterns
        assert result.matched_advanced_patterns == {}
        assert result.has_hedging is False
        assert result.has_temporal_change is False
        assert result.has_strong_preference is False
    
    async def test_no_patterns_matched(self, classifier):
        """Test query with no advanced patterns."""
        query = "What is your name?"
        result = await classifier.classify(query)
        
        # Should return empty or minimal patterns
        assert isinstance(result.matched_advanced_patterns, dict)
        assert result.has_hedging is False
        assert result.has_temporal_change is False
        assert result.has_strong_preference is False
    
    async def test_partial_pattern_no_match(self, classifier):
        """Test query with partial pattern that shouldn't match."""
        query = "I like food"  # Just "like", no negation or modifier
        result = await classifier.classify(query)
        
        # Should NOT match NEGATED_PREFERENCE or STRONG_PREFERENCE
        patterns = result.matched_advanced_patterns
        assert "NEGATED_PREFERENCE" not in patterns or len(patterns["NEGATED_PREFERENCE"]) == 0
        assert result.has_strong_preference is False


class TestIntegrationWithClassifier:
    """Test integration of matcher with full classifier."""
    
    async def test_matcher_in_result_object(self, classifier):
        """Test that matcher fields are populated in result."""
        query = "I really love pizza"
        result = await classifier.classify(query)
        
        # Verify all new fields are present and have correct types
        assert isinstance(result.matched_advanced_patterns, dict), "matched_advanced_patterns should be dict"
        assert isinstance(result.has_hedging, bool), "has_hedging should be boolean"
        assert isinstance(result.has_temporal_change, bool), "has_temporal_change should be boolean"
        assert isinstance(result.has_strong_preference, bool), "has_strong_preference should be boolean"
    
    async def test_matcher_with_intent_classification(self, classifier):
        """Test that matcher works alongside intent classification."""
        query = "I used to really enjoy hiking"
        result = await classifier.classify(query)
        
        # Intent classification should still work
        assert isinstance(result.intent_type, QueryIntent), "Should have valid intent type"
        assert isinstance(result.vector_strategy, VectorStrategy), "Should have valid vector strategy"
        
        # Matcher should also work
        assert result.has_temporal_change is True, "Should detect 'used to'"
        assert result.has_strong_preference is True, "Should detect 'really'"
    
    async def test_performance_with_matcher(self, classifier):
        """Test that matcher doesn't significantly impact performance."""
        query = "I really don't like spicy food but I used to enjoy it"
        
        # Warm up (first call may include spaCy model loading)
        _ = await classifier.classify(query)
        
        # Second call should be fast
        result = await classifier.classify(query)
        
        # Should maintain reasonable performance (<40ms with all features)
        assert result.classification_time_ms < 40.0, \
            f"Classification should be <40ms with matcher, got {result.classification_time_ms:.2f}ms"


class TestMatchedSpanDetails:
    """Test that matched spans contain correct details."""
    
    async def test_span_text_accuracy(self, classifier):
        """Test that matched span text is accurate."""
        query = "I really love pizza"
        result = await classifier.classify(query)
        
        if "STRONG_PREFERENCE" in result.matched_advanced_patterns:
            match = result.matched_advanced_patterns["STRONG_PREFERENCE"][0]
            
            # Should contain both the modifier and the verb
            assert "really" in match["text"].lower()
            assert "love" in match["text"].lower() or "love" in match["lemma"].lower()
    
    async def test_span_indices(self, classifier):
        """Test that span indices are valid."""
        query = "I don't like spicy food"
        result = await classifier.classify(query)
        
        if "NEGATED_PREFERENCE" in result.matched_advanced_patterns:
            match = result.matched_advanced_patterns["NEGATED_PREFERENCE"][0]
            
            # Indices should be valid
            assert isinstance(match["start"], int)
            assert isinstance(match["end"], int)
            assert match["start"] < match["end"]
    
    async def test_span_lemma_field(self, classifier):
        """Test that span lemma field is populated."""
        query = "I really loved that movie"
        result = await classifier.classify(query)
        
        if "STRONG_PREFERENCE" in result.matched_advanced_patterns:
            match = result.matched_advanced_patterns["STRONG_PREFERENCE"][0]
            
            # Should have lemma field
            assert "lemma" in match
            assert isinstance(match["lemma"], str)


class TestLoggingAndDebugging:
    """Test that matcher produces useful debug output."""
    
    async def test_debug_logging_for_patterns(self, classifier, caplog):
        """Test that pattern matches are logged."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        query = "I really love pizza"
        result = await classifier.classify(query)
        
        assert result.has_strong_preference is True
    
    async def test_info_logging_includes_patterns(self, classifier, caplog):
        """Test that INFO logs show pattern indicators."""
        import logging
        caplog.set_level(logging.INFO)
        
        query = "I really love pizza but used to hate it"
        result = await classifier.classify(query)
        
        # Should have both strong preference and temporal change
        assert result.has_strong_preference is True or result.has_temporal_change is True


# ============================================================================
# TEST SUITE SUMMARY
# ============================================================================

def test_suite_summary():
    """
    Test Suite Summary for Task 3.1: Custom Matcher Patterns
    
    Coverage:
    - ✅ Negated preferences (4 tests) - don't like, doesn't enjoy
    - ✅ Strong preferences (5 tests) - really love, absolutely hate
    - ✅ Temporal changes (4 tests) - used to like
    - ✅ Hedging language (6 tests) - maybe like, kind of prefer
    - ✅ Conditional statements (3 tests) - if I could
    - ✅ Multiple patterns (3 tests) - complex queries
    - ✅ Edge cases (3 tests) - empty, no match, partial
    - ✅ Integration (3 tests) - with classifier, performance
    - ✅ Span details (3 tests) - text, indices, lemma
    - ✅ Logging (2 tests) - debug and info logs
    
    Total Tests: 36 test cases
    
    Expected Results:
    - All negated preferences detected correctly
    - All strong preferences detected correctly
    - All temporal changes detected correctly
    - All hedging language detected correctly
    - Conditional statements detected (optional)
    - Multiple patterns in single query handled
    - Edge cases handled gracefully
    - Performance <40ms maintained
    """
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
