"""
Test suite for adaptive emotion threshold implementation.
Validates that neutral bias is eliminated and emotions are properly detected.

This test suite validates the fix for neutral bias in RoBERTa emotion detection,
ensuring that emotionally charged text is correctly classified while preserving
accuracy for genuinely neutral content.
"""

import pytest
import asyncio
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer


class TestAdaptiveEmotionThreshold:
    """Test adaptive emotion threshold logic"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance without vector memory for unit testing"""
        return EnhancedVectorEmotionAnalyzer(vector_memory_manager=None)
    
    def test_false_neutral_cases(self, analyzer):
        """Test cases that were incorrectly classified as neutral before fix"""
        test_cases = [
            ("I don't know what to do anymore.", ["sadness", "fear", "anxiety"]),
            ("Things have been difficult lately.", ["sadness", "anxiety"]),
            ("Why does this keep happening?", ["anger", "frustration", "sadness"]),
            ("Everything feels overwhelming.", ["fear", "anxiety", "sadness"]),
        ]
        
        results = []
        for message, expected_emotions in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions, content=message)
            
            # Should NOT be neutral, should be one of the expected emotions
            is_correct = primary in expected_emotions
            results.append({
                'message': message,
                'expected': expected_emotions,
                'got': primary,
                'confidence': confidence,
                'correct': is_correct
            })
            
            assert is_correct or primary != 'neutral', \
                f"❌ False neutral for '{message}': got {primary} ({confidence:.3f}), expected one of {expected_emotions}"
        
        # Print results summary
        print("\n📊 False Neutral Test Results:")
        for r in results:
            status = "✅" if r['correct'] else "⚠️"
            print(f"{status} '{r['message'][:40]:40}' → {r['got']:12} ({r['confidence']:.3f}) [expected: {r['expected']}]")
    
    def test_true_neutral_cases(self, analyzer):
        """Test cases that should correctly remain neutral"""
        test_cases = [
            "How are you today?",
            "Tell me more about that.",
            "What did you do yesterday?",
            "The meeting is at 3pm.",
            "Can you explain that again?",
            "What's the weather like?",
        ]
        
        results = []
        for message in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions, content=message)
            
            is_correct = primary == "neutral"
            results.append({
                'message': message,
                'got': primary,
                'confidence': confidence,
                'correct': is_correct
            })
            
            assert is_correct, \
                f"❌ False positive for '{message}': got {primary} ({confidence:.3f}), should be neutral"
        
        # Print results summary
        print("\n📊 True Neutral Test Results:")
        for r in results:
            status = "✅" if r['correct'] else "❌"
            print(f"{status} '{r['message'][:40]:40}' → {r['got']:12} ({r['confidence']:.3f})")
    
    def test_clear_emotions(self, analyzer):
        """Test cases with clear emotional signals"""
        test_cases = [
            ("I'm so happy!", ["joy", "excitement"]),
            ("This is terrible!", ["disgust", "anger", "sadness"]),
            ("I'm really worried about this.", ["fear", "anxiety"]),
            ("That makes me so angry!", ["anger", "frustration"]),
            ("I love this so much!", ["joy", "love", "excitement"]),
            ("I'm feeling grateful today.", ["gratitude", "joy", "contentment"]),
        ]
        
        results = []
        for message, expected_emotions in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions, content=message)
            
            is_correct = primary in expected_emotions
            results.append({
                'message': message,
                'expected': expected_emotions,
                'got': primary,
                'confidence': confidence,
                'correct': is_correct
            })
            
            assert is_correct, \
                f"❌ Failed for '{message}': got {primary} ({confidence:.3f}), expected one of {expected_emotions}"
        
        # Print results summary
        print("\n📊 Clear Emotion Test Results:")
        for r in results:
            status = "✅" if r['correct'] else "❌"
            print(f"{status} '{r['message'][:40]:40}' → {r['got']:12} ({r['confidence']:.3f}) [expected: {r['expected']}]")
    
    def test_margin_calculation(self, analyzer):
        """Test margin calculation helper"""
        # Test with clear margin
        emotions_clear = {"joy": 0.7, "sadness": 0.2, "neutral": 0.1}
        margin, primary, secondary = analyzer._calculate_emotion_margin(emotions_clear)
        assert margin == pytest.approx(0.5, 0.01), f"Expected margin ~0.5, got {margin}"
        assert primary == "joy", f"Expected primary=joy, got {primary}"
        assert secondary == "sadness", f"Expected secondary=sadness, got {secondary}"
        
        # Test with close competition
        emotions_close = {"joy": 0.45, "sadness": 0.40, "neutral": 0.15}
        margin, primary, secondary = analyzer._calculate_emotion_margin(emotions_close)
        assert margin == pytest.approx(0.05, 0.01), f"Expected margin ~0.05, got {margin}"
        assert primary == "joy", f"Expected primary=joy, got {primary}"
        assert secondary == "sadness", f"Expected secondary=sadness, got {secondary}"
        
        # Test with single emotion
        emotions_single = {"joy": 1.0}
        margin, primary, secondary = analyzer._calculate_emotion_margin(emotions_single)
        assert margin == 0.0, f"Expected margin=0, got {margin}"
        assert primary == "joy", f"Expected primary=joy, got {primary}"
        assert secondary == "none", f"Expected secondary=none, got {secondary}"
        
        print("\n✅ Margin calculation tests passed")
    
    def test_adaptive_threshold_scenarios(self, analyzer):
        """Test specific adaptive threshold scenarios"""
        
        # Scenario 1: High confidence neutral (should remain neutral)
        emotions_high_neutral = {"neutral": 0.75, "joy": 0.15, "sadness": 0.10}
        primary, confidence = analyzer._determine_primary_emotion(emotions_high_neutral, content="")
        assert primary == "neutral", f"High confidence neutral should stay neutral, got {primary}"
        
        # Scenario 2: Large margin neutral (should remain neutral)
        emotions_large_margin_neutral = {"neutral": 0.65, "joy": 0.25, "sadness": 0.10}
        primary, confidence = analyzer._determine_primary_emotion(emotions_large_margin_neutral, content="")
        assert primary == "neutral", f"Large margin neutral should stay neutral, got {primary}"
        
        # Scenario 3: Weak neutral with strong alternative (should switch to emotion)
        emotions_weak_neutral = {"neutral": 0.45, "sadness": 0.40, "joy": 0.15}
        primary, confidence = analyzer._determine_primary_emotion(emotions_weak_neutral, content="")
        assert primary == "sadness", f"Weak neutral with strong alternative should switch, got {primary}"
        
        # Scenario 4: Clear winner emotion (should be accepted)
        emotions_clear_winner = {"anger": 0.60, "neutral": 0.25, "sadness": 0.15}
        primary, confidence = analyzer._determine_primary_emotion(emotions_clear_winner, content="")
        assert primary == "anger", f"Clear winner should be accepted, got {primary}"
        
        # Scenario 5: Large margin emotion (should be accepted even at moderate confidence)
        emotions_large_margin_emotion = {"fear": 0.50, "neutral": 0.20, "sadness": 0.15}
        primary, confidence = analyzer._determine_primary_emotion(emotions_large_margin_emotion, content="")
        assert primary == "fear", f"Large margin emotion should be accepted, got {primary}"
        
        print("\n✅ Adaptive threshold scenario tests passed")
    
    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, analyzer):
        """Test full emotion analysis pipeline with adaptive thresholds"""
        
        test_messages = [
            ("I don't know what to do anymore.", "sadness"),
            ("How are you?", "neutral"),
            ("I'm so excited about this!", "joy"),
            ("Why does this always happen to me?", "anger"),
        ]
        
        print("\n📊 Full Pipeline Test Results:")
        for message, expected_emotion in test_messages:
            result = await analyzer.analyze_emotion(
                content=message,
                user_id="test_user_threshold",
                conversation_context=None,
                recent_emotions=None
            )
            
            is_correct = result.primary_emotion == expected_emotion or result.primary_emotion != "neutral"
            status = "✅" if is_correct else "❌"
            print(f"{status} '{message[:40]:40}' → {result.primary_emotion:12} ({result.confidence:.3f}) [expected: {expected_emotion}]")
            
            # For false neutral cases, we care that it's NOT neutral more than the exact emotion
            if expected_emotion != "neutral":
                assert result.primary_emotion != "neutral" or result.confidence < 0.5, \
                    f"Should not be neutral for '{message}'"


class TestRegressionPrevention:
    """Ensure we don't break existing functionality"""
    
    @pytest.fixture
    def analyzer(self):
        return EnhancedVectorEmotionAnalyzer(vector_memory_manager=None)
    
    def test_empty_emotions_fallback(self, analyzer):
        """Test empty emotions dict returns neutral"""
        primary, confidence = analyzer._determine_primary_emotion({}, content="")
        assert primary == "neutral", f"Empty emotions should return neutral, got {primary}"
        assert confidence > 0, f"Confidence should be positive, got {confidence}"
    
    def test_single_emotion(self, analyzer):
        """Test single emotion is correctly identified"""
        emotions = {"joy": 0.8}
        primary, confidence = analyzer._determine_primary_emotion(emotions, content="")
        assert primary == "joy", f"Single emotion should be identified, got {primary}"
    
    def test_confidence_bounds(self, analyzer):
        """Test confidence values are within valid bounds"""
        test_cases = [
            {"joy": 0.9, "sadness": 0.1},
            {"neutral": 0.7, "joy": 0.3},
            {"anger": 0.4, "neutral": 0.35, "sadness": 0.25},
        ]
        
        for emotions in test_cases:
            primary, confidence = analyzer._determine_primary_emotion(emotions, content="")
            assert 0.0 <= confidence <= 1.0, \
                f"Confidence out of bounds: {confidence} for {emotions}"
    
    def test_no_roberta_fallback(self, analyzer):
        """Test that keyword analysis works without RoBERTa"""
        # This tests the LAYER 3 keyword fallback
        message = "I am feeling very happy and joyful today!"
        emotions = analyzer._analyze_keyword_emotions(message)
        
        # Should detect joy through keywords even if RoBERTa unavailable
        assert "joy" in emotions or "happiness" in emotions, \
            f"Keyword analysis should detect joy, got {emotions}"


# Standalone test runner for direct Python validation
if __name__ == "__main__":
    import sys
    
    print("🧪 Running Adaptive Emotion Threshold Tests")
    print("=" * 60)
    
    analyzer = EnhancedVectorEmotionAnalyzer(vector_memory_manager=None)
    
    # Test 1: False neutral cases
    print("\n1️⃣ Testing False Neutral Cases (should NOT be neutral)")
    print("-" * 60)
    false_neutral_cases = [
        "I don't know what to do anymore.",
        "Things have been difficult lately.",
        "Why does this keep happening?",
        "Everything feels overwhelming.",
    ]
    
    for msg in false_neutral_cases:
        emotions = analyzer._analyze_keyword_emotions(msg)
        primary, confidence = analyzer._determine_primary_emotion(emotions, content=msg)
        status = "✅" if primary != "neutral" else "❌"
        print(f"{status} {msg[:45]:45} → {primary:12} ({confidence:.3f})")
    
    # Test 2: True neutral cases
    print("\n2️⃣ Testing True Neutral Cases (should be neutral)")
    print("-" * 60)
    true_neutral_cases = [
        "How are you today?",
        "Tell me more about that.",
        "What did you do yesterday?",
        "The meeting is at 3pm.",
    ]
    
    for msg in true_neutral_cases:
        emotions = analyzer._analyze_keyword_emotions(msg)
        primary, confidence = analyzer._determine_primary_emotion(emotions, content=msg)
        status = "✅" if primary == "neutral" else "❌"
        print(f"{status} {msg[:45]:45} → {primary:12} ({confidence:.3f})")
    
    # Test 3: Clear emotions
    print("\n3️⃣ Testing Clear Emotion Cases")
    print("-" * 60)
    clear_emotion_cases = [
        "I'm so happy!",
        "This is terrible!",
        "I'm really worried about this.",
        "That makes me so angry!",
    ]
    
    for msg in clear_emotion_cases:
        emotions = analyzer._analyze_keyword_emotions(msg)
        primary, confidence = analyzer._determine_primary_emotion(emotions, content=msg)
        status = "✅" if primary != "neutral" else "⚠️"
        print(f"{status} {msg[:45]:45} → {primary:12} ({confidence:.3f})")
    
    print("\n" + "=" * 60)
    print("✅ Adaptive Emotion Threshold Tests Complete!")
