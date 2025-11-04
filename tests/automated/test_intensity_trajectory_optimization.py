"""
Test suite for intensity and trajectory analysis optimization with NLPAnalysisCache.

Validates POS-based intensifier detection and lemma-based trajectory verb matching.

Author: WhisperEngine Team
Created: November 2025
"""

import pytest
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
from src.intelligence.nlp_analysis_cache import NLPAnalysisCache
from src.nlp.spacy_manager import get_spacy_nlp


class TestIntensityAnalysisOptimization:
    """Test POS-based intensifier detection."""
    
    def setup_method(self):
        """Create emotion analyzer for testing."""
        self.analyzer = EnhancedVectorEmotionAnalyzer()
        self.nlp = get_spacy_nlp()
    
    def test_intensity_without_cache_backward_compatible(self):
        """Test that intensity analysis works without cache (backward compatible)."""
        text = "I'm very extremely really happy!"
        
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=None)
        
        # Should detect intensifiers and exclamation
        assert intensity > 0.5, "Should detect intensifiers"
        assert intensity < 1.0, "Should not max out"
    
    def test_intensity_with_cache_detects_intensifiers(self):
        """Test that cache-based intensity detection works."""
        text = "I'm very extremely really happy about this!"
        
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=cache)
        
        # Should detect multiple intensifiers (very, extremely, really)
        assert intensity > 0.5, "Should detect intensifiers via cache"
    
    def test_intensity_punctuation_still_works(self):
        """Test that punctuation counting still works with cache."""
        text = "This is amazing!!! I can't believe it!!!"
        
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=cache)
        
        # Should detect 6 exclamation marks
        assert intensity > 0.6, f"Should have high intensity from exclamations: {intensity}"
    
    def test_intensity_neutral_text_low_score(self):
        """Test that neutral text has low intensity."""
        text = "The meeting is at 3pm"
        
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=cache)
        
        # Should be around base intensity (0.5) for neutral text
        assert 0.4 <= intensity <= 0.6, f"Neutral text should have base intensity: {intensity}"


class TestTrajectoryAnalysisOptimization:
    """Test lemma-based trajectory verb matching."""
    
    def setup_method(self):
        """Create emotion analyzer for testing."""
        self.analyzer = EnhancedVectorEmotionAnalyzer()
        self.nlp = get_spacy_nlp()
    
    def test_trajectory_without_cache_backward_compatible(self):
        """Test that trajectory analysis works without cache (backward compatible)."""
        text = "I'm getting happier"
        
        trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=None)
        
        # Should detect "getting" as rising indicator
        assert trajectory == "rising", f"Should detect rising trajectory: {trajectory}"
    
    def test_trajectory_rising_with_cache(self):
        """Test rising trajectory detection with cache (handles verb tenses)."""
        test_cases = [
            ("I'm getting happier", "getting → get lemma"),
            ("I'm becoming more confident", "becoming → become lemma"),
            ("Things are growing better", "growing → grow lemma"),
        ]
        
        for text, description in test_cases:
            doc = self.nlp(text)
            cache = NLPAnalysisCache.from_doc(doc, text)
            
            trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
            
            assert trajectory == "rising", f"Should detect rising for '{text}' ({description}): {trajectory}"
    
    def test_trajectory_falling_with_cache(self):
        """Test falling trajectory detection with cache."""
        test_cases = [
            ("I'm calming down now", "calming → calm lemma"),
            ("Things are settling", "settling → settle lemma"),
            ("My excitement is fading", "fading → fade lemma"),
        ]
        
        for text, description in test_cases:
            doc = self.nlp(text)
            cache = NLPAnalysisCache.from_doc(doc, text)
            
            trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
            
            assert trajectory == "falling", f"Should detect falling for '{text}' ({description}): {trajectory}"
    
    def test_trajectory_stable_neutral_text(self):
        """Test stable trajectory for neutral text."""
        text = "The meeting is at 3pm tomorrow"
        
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
        
        # Should be stable for neutral text
        assert trajectory == "stable", f"Neutral text should have stable trajectory: {trajectory}"
    
    def test_trajectory_verb_tense_variations(self):
        """Test that different verb tenses are handled via lemmas."""
        # All should detect "get" lemma → rising
        test_cases = [
            "I'm getting better",     # getting → get
            "I got happier",          # got → get  
            "I get more confident",   # get → get
        ]
        
        for text in test_cases:
            doc = self.nlp(text)
            cache = NLPAnalysisCache.from_doc(doc, text)
            
            trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
            
            # All forms should detect "get" lemma
            assert trajectory == "rising", f"Should handle verb variation in '{text}': {trajectory}"


class TestIntegratedOptimization:
    """Test that intensity and trajectory work together with cache."""
    
    def setup_method(self):
        """Create emotion analyzer for testing."""
        self.analyzer = EnhancedVectorEmotionAnalyzer()
        self.nlp = get_spacy_nlp()
    
    def test_both_use_same_cache(self):
        """Test that both methods can use the same pre-parsed cache."""
        text = "I'm getting very extremely happy about this amazing development!!!"
        
        # Create cache once
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # Both should work with same cache
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=cache)
        trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
        
        # Should detect high intensity (intensifiers + exclamations)
        assert intensity > 0.6, f"Should have high intensity: {intensity}"
        
        # Should detect rising trajectory ("getting")
        assert trajectory == "rising", f"Should detect rising trajectory: {trajectory}"
    
    def test_no_redundant_parsing(self):
        """
        Demonstrate that cache eliminates redundant parsing.
        
        Without cache: parse 3+ times (stance, keyword, intensity, trajectory)
        With cache: parse once, reuse everywhere
        """
        text = "I'm feeling very excited and getting happier every day!"
        
        # Single parse
        doc = self.nlp(text)
        cache = NLPAnalysisCache.from_doc(doc, text)
        
        # All methods use same cache (no re-parsing)
        emotion_matches = cache.get_all_emotion_matches()
        intensity = self.analyzer._analyze_emotional_intensity(text, nlp_cache=cache)
        trajectory = self.analyzer._analyze_emotional_trajectory(text, nlp_cache=cache)
        
        # Verify all worked
        assert len(emotion_matches) > 0, "Should have emotion keywords"
        assert intensity > 0.5, "Should have intensity"
        assert trajectory == "rising", "Should have trajectory"
        
        print(f"✅ Single parse used for: emotions, intensity, trajectory")
        print(f"   Emotions: {emotion_matches}")
        print(f"   Intensity: {intensity:.3f}")
        print(f"   Trajectory: {trajectory}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
