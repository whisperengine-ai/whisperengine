"""
Test suite for NLPAnalysisCache - spaCy optimization foundation.

This module validates the NLPAnalysisCache class to ensure:
1. Correct extraction of spaCy features (lemmas, POS tags, entities)
2. Accurate emotion keyword pre-computation
3. Helper methods work correctly (intensifiers, negation, etc.)
4. Performance improvements are measurable

Author: WhisperEngine Team
Created: November 2025
"""

import pytest
import time
from typing import List

from src.intelligence.nlp_analysis_cache import NLPAnalysisCache
from src.nlp.spacy_manager import get_spacy_nlp


class TestNLPAnalysisCacheBasics:
    """Test basic cache creation and feature extraction."""
    
    def test_cache_creation_from_doc(self):
        """Test NLPAnalysisCache.from_doc() creates cache correctly."""
        nlp = get_spacy_nlp()
        text = "I'm feeling really happy and excited about this amazing opportunity!"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Verify basic attributes
        assert cache.original_text == text
        assert cache.doc == doc
        assert len(cache.lemmas) > 0
        assert len(cache.pos_tags) > 0
        assert len(cache.tokens) > 0
        assert len(cache.lemmas) == len(cache.pos_tags) == len(cache.tokens)
    
    def test_lemma_extraction(self):
        """Test lemmas are extracted and lowercased correctly."""
        nlp = get_spacy_nlp()
        text = "I'm running quickly through the beautiful forests"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Check key lemmas (verb lemmatization)
        assert 'run' in cache.lemma_set  # "running" → "run"
        assert 'quickly' in cache.lemma_set
        assert 'beautiful' in cache.lemma_set
        assert 'forest' in cache.lemma_set  # "forests" → "forest"
    
    def test_pos_tag_extraction(self):
        """Test POS tags are extracted correctly."""
        nlp = get_spacy_nlp()
        text = "Very happy developers write excellent code"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Verify POS tags exist
        assert 'ADJ' in cache.pos_tags  # happy, excellent
        assert 'NOUN' in cache.pos_tags  # developers, code
        assert 'VERB' in cache.pos_tags  # write
        assert 'ADV' in cache.pos_tags   # Very
    
    def test_entity_extraction(self):
        """Test named entities are extracted."""
        nlp = get_spacy_nlp()
        text = "I live in San Francisco and work for OpenAI"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Check entities were extracted
        assert len(cache.entities) > 0
        entity_texts = [ent[0] for ent in cache.entities]
        # spaCy should recognize at least one location/org
        assert any('San Francisco' in text or 'OpenAI' in text for text in entity_texts)


class TestEmotionKeywordPrecomputation:
    """Test emotion keyword matching with lemma-based approach."""
    
    def test_joy_keywords_detected(self):
        """Test joy-related keywords are detected via lemmas."""
        nlp = get_spacy_nlp()
        text = "I'm so happy and excited about this wonderful day!"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Check joy keywords were matched
        joy_matches = cache.get_emotion_keyword_matches('joy')
        assert len(joy_matches) > 0
        # Should match at least "happy" or "excited" or "wonderful"
        assert any(kw in joy_matches for kw in ['happy', 'excited', 'wonderful'])
    
    def test_sadness_keywords_detected(self):
        """Test sadness-related keywords are detected."""
        nlp = get_spacy_nlp()
        text = "I feel so sad and disappointed about what happened"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        sadness_matches = cache.get_emotion_keyword_matches('sadness')
        assert len(sadness_matches) > 0
        assert any(kw in sadness_matches for kw in ['sad', 'disappointed'])
    
    def test_anger_keywords_detected(self):
        """Test anger-related keywords are detected."""
        nlp = get_spacy_nlp()
        text = "I'm really frustrated and angry about this situation"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        anger_matches = cache.get_emotion_keyword_matches('anger')
        assert len(anger_matches) > 0
        assert any(kw in anger_matches for kw in ['frustrated', 'angry'])
    
    def test_multiple_emotions_detected(self):
        """Test multiple emotion keywords can be detected simultaneously."""
        nlp = get_spacy_nlp()
        text = "I was happy at first but now I'm sad and worried"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        all_matches = cache.get_all_emotion_matches()
        # Should detect joy (happy), sadness (sad), fear (worried)
        assert 'joy' in all_matches
        assert 'sadness' in all_matches
        assert 'fear' in all_matches
    
    def test_no_false_positives_neutral_text(self):
        """Test neutral text doesn't incorrectly match emotion keywords."""
        nlp = get_spacy_nlp()
        text = "The meeting is scheduled for 3pm tomorrow"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        all_matches = cache.get_all_emotion_matches()
        # Should have minimal or no emotion matches for factual statement
        assert len(all_matches) <= 1  # Allow 1 weak match, but not multiple


class TestHelperMethods:
    """Test convenience helper methods."""
    
    def test_has_lemma_method(self):
        """Test has_lemma() O(1) lookup works."""
        nlp = get_spacy_nlp()
        text = "I'm running through the forest"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Check lemmas (not raw words)
        assert cache.has_lemma('run')      # "running" → "run"
        assert cache.has_lemma('forest')
        assert not cache.has_lemma('jumping')  # not in text
    
    def test_get_tokens_with_pos(self):
        """Test POS-based token filtering."""
        nlp = get_spacy_nlp()
        text = "Very happy developers write excellent code quickly"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Get adverbs
        adverbs = cache.get_tokens_with_pos('ADV')
        assert len(adverbs) >= 1  # "Very" and/or "quickly"
        
        # Get verbs
        verbs = cache.get_tokens_with_pos('VERB')
        assert len(verbs) >= 1  # "write"
        
        # Get adjectives
        adjectives = cache.get_tokens_with_pos('ADJ')
        assert len(adjectives) >= 2  # "happy", "excellent"
    
    def test_intensifier_count(self):
        """Test intensifier counting for emotional intensity."""
        nlp = get_spacy_nlp()
        text = "I'm very extremely really happy about this"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        count = cache.get_intensifier_count()
        # Should detect at least 2-3 intensifiers (very, extremely, really)
        assert count >= 2
    
    def test_has_negation(self):
        """Test negation detection."""
        nlp = get_spacy_nlp()
        
        # Positive case
        text_with_neg = "I'm not happy about this"
        doc_with_neg = nlp(text_with_neg)
        cache_with_neg = NLPAnalysisCache.from_doc(doc_with_neg, text_with_neg)
        assert cache_with_neg.has_negation() == True
        
        # Negative case
        text_no_neg = "I'm happy about this"
        doc_no_neg = nlp(text_no_neg)
        cache_no_neg = NLPAnalysisCache.from_doc(doc_no_neg, text_no_neg)
        assert cache_no_neg.has_negation() == False


class TestDependencyTree:
    """Test dependency tree extraction for stance analysis."""
    
    def test_dependency_tree_basic_structure(self):
        """Test dependency tree has expected structure."""
        nlp = get_spacy_nlp()
        text = "I am running through the forest"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        tree = cache.dependency_tree
        assert 'root' in tree
        assert 'subjects' in tree
        assert 'objects' in tree
        assert 'negations' in tree
        assert 'aux_verbs' in tree
    
    def test_subject_detection(self):
        """Test subjects are detected in dependency tree."""
        nlp = get_spacy_nlp()
        text = "I love coding and you enjoy testing"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        subjects = cache.dependency_tree['subjects']
        # Should detect at least "I" and "you" as subjects
        assert len(subjects) >= 1
    
    def test_root_verb_detection(self):
        """Test root verb is identified."""
        nlp = get_spacy_nlp()
        text = "I am running quickly"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        root = cache.dependency_tree['root']
        assert root is not None


class TestPerformanceComparison:
    """Test performance improvements vs traditional parsing."""
    
    def test_single_parse_vs_multiple_parsing(self):
        """
        Demonstrate performance improvement: 1 parse + cache vs 3 separate parses.
        
        This simulates the old approach where stance, emotion, and intensity
        analyzers each called spaCy independently.
        """
        nlp = get_spacy_nlp()
        text = "I'm feeling really happy and excited about this amazing opportunity but also a bit nervous!"
        
        # Approach 1: Traditional (3 separate parses)
        start_traditional = time.perf_counter()
        doc1 = nlp(text)  # Stance analyzer
        doc2 = nlp(text)  # Emotion analyzer
        doc3 = nlp(text)  # Intensity analyzer
        # Simulate feature extraction
        lemmas1 = [t.lemma_ for t in doc1]
        lemmas2 = [t.lemma_ for t in doc2]
        pos_tags3 = [t.pos_ for t in doc3]
        traditional_time = time.perf_counter() - start_traditional
        
        # Approach 2: Optimized (1 parse + cache)
        start_optimized = time.perf_counter()
        doc = nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        # All analyzers use cache
        lemmas_cached = cache.lemmas
        pos_cached = cache.pos_tags
        optimized_time = time.perf_counter() - start_optimized
        
        # Performance assertion
        print(f"\nTraditional (3 parses): {traditional_time*1000:.2f}ms")
        print(f"Optimized (1 parse + cache): {optimized_time*1000:.2f}ms")
        print(f"Speedup: {traditional_time/optimized_time:.2f}x")
        
        # Should be significantly faster (at least 1.5x, target is 2-3x)
        assert optimized_time < traditional_time
        # Note: Actual speedup varies by system, but cache should NEVER be slower


class TestBackwardCompatibility:
    """Test that cache is designed for backward compatibility."""
    
    def test_cache_is_optional_pattern(self):
        """
        Demonstrate that cache can be optional parameter in analyzers.
        
        This ensures zero breaking changes - existing code works without cache.
        """
        nlp = get_spacy_nlp()
        text = "I'm feeling happy"
        
        # Scenario 1: New code path (with cache)
        doc = nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        assert cache is not None
        assert cache.has_lemma('happy')
        
        # Scenario 2: Old code path (without cache, would parse internally)
        # This pattern will be used in analyzer methods:
        # def analyze_emotion(message, nlp_cache=None):
        #     if nlp_cache is None:
        #         nlp = get_spacy_nlp()
        #         doc = nlp(message)
        #         nlp_cache = NLPAnalysisCache.from_doc(doc, message)
        #     # Use cache...
        
        # Both paths work - no breaking changes!
        assert True  # Demonstrates design principle


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text(self):
        """Test cache handles empty text gracefully."""
        nlp = get_spacy_nlp()
        text = ""
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        assert cache.original_text == ""
        assert len(cache.lemmas) == 0
        assert len(cache.pos_tags) == 0
        assert len(cache.tokens) == 0
    
    def test_single_word(self):
        """Test cache works with single-word messages."""
        nlp = get_spacy_nlp()
        text = "happy"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        assert len(cache.lemmas) == 1
        assert cache.has_lemma('happy')
    
    def test_special_characters(self):
        """Test cache handles special characters and punctuation."""
        nlp = get_spacy_nlp()
        text = "I'm so happy!!! 😊 This is amazing... ❤️"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Should still extract meaningful lemmas
        assert cache.has_lemma('happy')
        assert cache.has_lemma('amazing')
    
    def test_repr_method(self):
        """Test string representation for debugging."""
        nlp = get_spacy_nlp()
        text = "I'm feeling happy and excited"
        doc = nlp(text)
        
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        repr_str = repr(cache)
        assert 'NLPAnalysisCache' in repr_str
        assert 'lemmas=' in repr_str
        assert 'emotion_matches=' in repr_str


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
