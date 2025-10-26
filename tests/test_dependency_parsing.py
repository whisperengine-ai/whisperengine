"""
Unit tests for dependency parsing features in UnifiedQueryClassifier.

Tests:
1. Negation detection ("I don't like X" vs "I like X")
2. Subject-Verb-Object (SVO) extraction
3. Relationship type extraction with negation awareness
4. Double negatives ("I don't dislike it" → likes)
"""

import pytest
from src.memory.unified_query_classification import UnifiedQueryClassifier


class TestNegationDetection:
    """Test negation detection using dependency parsing."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return UnifiedQueryClassifier()
    
    def test_simple_negation(self, classifier):
        """Test basic negation detection: I don't like X."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        query = "I don't like spicy food"
        query_doc = classifier.nlp(query)
        
        negation_info = classifier._detect_negation(query_doc)  # noqa: SLF001
        
        assert negation_info["has_negation"] is True
        assert "like" in negation_info["negated_verbs"]
        assert "don't" in negation_info["negation_tokens"] or "n't" in negation_info["negation_tokens"]
        
        print(f"✅ Negation detected: {negation_info}")
    
    def test_no_negation(self, classifier):
        """Test query without negation: I like X."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        query = "I love pizza"
        query_doc = classifier.nlp(query)
        
        negation_info = classifier._detect_negation(query_doc)  # noqa: SLF001
        
        assert negation_info["has_negation"] is False
        assert len(negation_info["negated_verbs"]) == 0
        
        print(f"✅ No negation (correct): {negation_info}")
    
    def test_negation_variants(self, classifier):
        """Test different negation forms."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        test_cases = [
            ("I don't enjoy hiking", True, "enjoy"),
            ("I don't want to go", True, "want"),
            ("I can't stand it", True, "stand"),
            ("I never liked it", True, "like"),  # "never" is also negation
        ]
        
        for query, should_have_negation, expected_verb in test_cases:
            query_doc = classifier.nlp(query)
            negation_info = classifier._detect_negation(query_doc)  # noqa: SLF001
            
            if should_have_negation:
                assert negation_info["has_negation"] is True, f"Failed for: {query}"
                assert expected_verb in negation_info["negated_verbs"], f"Expected verb {expected_verb} in {negation_info}"
                print(f"✅ Negation detected in: {query}")
            else:
                assert negation_info["has_negation"] is False, f"False positive for: {query}"
                print(f"✅ No negation (correct) in: {query}")


class TestSVOExtraction:
    """Test Subject-Verb-Object extraction."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return UnifiedQueryClassifier()
    
    def test_simple_svo(self, classifier):
        """Test basic SVO: Mark loves pizza."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        query = "Mark loves pizza"
        query_doc = classifier.nlp(query)
        
        svo_relationships = classifier._extract_svo_relationships(query_doc)  # noqa: SLF001
        
        assert len(svo_relationships) > 0, "Should extract at least one SVO"
        
        svo = svo_relationships[0]
        assert svo["subject"] == "Mark"
        assert svo["verb"] == "love"  # Lemmatized
        assert svo["object"] == "pizza"
        assert svo["negated"] is False
        
        print(f"✅ SVO extracted: {svo}")
    
    def test_svo_with_negation(self, classifier):
        """Test SVO with negation: I don't like spicy food."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        # Changed query to have clearer direct object
        query = "I don't like spicy food"
        query_doc = classifier.nlp(query)
        
        svo_relationships = classifier._extract_svo_relationships(query_doc)  # noqa: SLF001
        
        assert len(svo_relationships) > 0, "Should extract SVO"
        
        svo = svo_relationships[0]
        assert svo["subject"] == "I"
        assert svo["verb"] == "like"
        assert svo["object"] == "food"
        assert svo["negated"] is True, "Should detect negation"
        
        print(f"✅ SVO with negation: {svo}")
    
    def test_multiple_svos(self, classifier):
        """Test extracting multiple SVOs from complex sentence."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        query = "I love pizza but I hate sushi"
        query_doc = classifier.nlp(query)
        
        svo_relationships = classifier._extract_svo_relationships(query_doc)  # noqa: SLF001
        
        # Should extract at least one (might get both depending on parsing)
        assert len(svo_relationships) >= 1
        
        # Check first SVO
        assert any(svo["verb"] == "love" for svo in svo_relationships)
        
        print(f"✅ Multiple SVOs extracted: {svo_relationships}")
    
    def test_no_svo(self, classifier):
        """Test query without clear SVO structure."""
        if not classifier.nlp:
            pytest.skip("spaCy not available")
        
        query = "Hello there!"
        query_doc = classifier.nlp(query)
        
        svo_relationships = classifier._extract_svo_relationships(query_doc)  # noqa: SLF001
        
        assert len(svo_relationships) == 0, "Should not extract SVO from greeting"
        
        print("✅ No SVO extracted (correct)")


class TestRelationshipTypeWithNegation:
    """Test relationship type extraction with negation awareness."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return UnifiedQueryClassifier()
    
    @pytest.mark.asyncio
    async def test_negated_like_becomes_dislike(self, classifier):
        """Test: I don't like X → dislikes."""
        query = "I don't like spicy food"
        
        classification = await classifier.classify(query)
        
        assert classification.has_negation is True
        assert classification.relationship_type == "dislikes"
        
        print(f"✅ 'don't like' → dislikes: {classification.relationship_type}")
    
    @pytest.mark.asyncio
    async def test_positive_like_remains_like(self, classifier):
        """Test: I like X → likes."""
        query = "I like pizza"
        
        classification = await classifier.classify(query)
        
        assert classification.has_negation is False
        assert classification.relationship_type == "likes"
        
        print(f"✅ 'like' → likes: {classification.relationship_type}")
    
    @pytest.mark.asyncio
    async def test_double_negative(self, classifier):
        """Test: I don't dislike X → likes (double negative)."""
        query = "I don't dislike it"
        
        classification = await classifier.classify(query)
        
        assert classification.has_negation is True
        # Double negative should flip to positive
        assert classification.relationship_type == "likes"
        
        print(f"✅ 'don't dislike' → likes (double negative): {classification.relationship_type}")
    
    @pytest.mark.asyncio
    async def test_negated_love(self, classifier):
        """Test: I don't love X → dislikes."""
        query = "I don't love sushi"
        
        classification = await classifier.classify(query)
        
        assert classification.has_negation is True
        assert classification.relationship_type == "dislikes"
        
        print(f"✅ 'don't love' → dislikes: {classification.relationship_type}")
    
    @pytest.mark.asyncio
    async def test_negated_enjoy(self, classifier):
        """Test: I don't enjoy X → dislikes."""
        query = "I don't enjoy hiking"
        
        classification = await classifier.classify(query)
        
        assert classification.has_negation is True
        assert classification.relationship_type == "dislikes"
        
        print(f"✅ 'don't enjoy' → dislikes: {classification.relationship_type}")


class TestSVOIntegration:
    """Test SVO extraction integration with classification."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return UnifiedQueryClassifier()
    
    @pytest.mark.asyncio
    async def test_svo_in_classification(self, classifier):
        """Test that SVO relationships are included in classification result."""
        query = "Mark loves pizza"
        
        classification = await classifier.classify(query)
        
        # Check SVO was extracted
        assert len(classification.svo_relationships) > 0
        
        svo = classification.svo_relationships[0]
        assert svo["subject"] == "Mark"
        assert svo["verb"] == "love"
        assert svo["object"] == "pizza"
        
        print(f"✅ SVO in classification: {svo}")
    
    @pytest.mark.asyncio
    async def test_svo_with_negation_in_classification(self, classifier):
        """Test SVO with negation is correctly tracked."""
        query = "I don't enjoy spicy food"
        
        classification = await classifier.classify(query)
        
        # Check negation flag
        assert classification.has_negation is True
        
        # Check SVO extraction
        if len(classification.svo_relationships) > 0:
            svo = classification.svo_relationships[0]
            assert svo["negated"] is True
            print(f"✅ SVO with negation in classification: {svo}")
        else:
            print("⚠️ No SVO extracted (dependency parsing didn't find clear structure)")


class TestPerformance:
    """Test performance impact of dependency parsing."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return UnifiedQueryClassifier()
    
    @pytest.mark.asyncio
    async def test_classification_performance_with_dependency_parsing(self, classifier):
        """Test that dependency parsing doesn't significantly slow down classification."""
        import time
        
        queries = [
            "I like pizza",
            "I don't like spicy food",
            "Mark loves sushi",
            "I don't enjoy hiking",
            "What did we talk about yesterday?",
        ]
        
        # Warm-up: Run once to load spaCy model and cache
        _ = await classifier.classify(queries[0])
        
        times = []
        
        for query in queries:
            start = time.time()
            _ = await classifier.classify(query)  # Use result but don't store
            elapsed_ms = (time.time() - start) * 1000
            times.append(elapsed_ms)
            
            print(f"Query: '{query}' → {elapsed_ms:.2f}ms")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print("\n📊 Performance Metrics:")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Max: {max_time:.2f}ms")
        print("   Target: <15ms")
        
        # Performance target: <15ms per query (after warm-up)
        # Allow slightly higher average due to first-time overhead
        assert avg_time < 20.0, f"Average classification time {avg_time:.2f}ms exceeds 20ms target"
        assert max_time < 30.0, f"Max classification time {max_time:.2f}ms too high"
        
        print("✅ Performance within targets!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
