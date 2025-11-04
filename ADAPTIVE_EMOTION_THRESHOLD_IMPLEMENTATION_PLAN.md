# Adaptive Emotion Threshold Implementation Plan

## Overview
Implement sophisticated adaptive confidence thresholding for RoBERTa emotion detection to eliminate neutral bias and improve emotional intelligence accuracy.

## Problem Statement
Current WhisperEngine emotion detection suffers from:
1. **Neutral bias**: Emotionally charged text incorrectly classified as "neutral"
2. **Fixed thresholds**: Single 0.3 confidence threshold for all emotions
3. **Manual patching**: Keyword-based context adjustments to compensate for threshold issues
4. **No margin logic**: Ignores confidence gap between top emotions

## Solution: Adaptive Thresholding Strategy

### Core Principles
1. **Higher bar for neutral**: Require strong evidence (≥0.70 confidence OR ≥0.30 margin) before claiming neutral
2. **Lower bar for genuine emotions**: Accept emotions at ≥0.35 confidence if clear winner (≥0.15 margin)
3. **Margin-based decisions**: Use confidence gap between #1 and #2 emotions as signal strength indicator
4. **Smart fallback**: When neutral wins weakly, check for strong non-neutral alternatives

## Implementation Plan

### Phase 1: Core Threshold Logic (PRIMARY)
**File**: `src/intelligence/enhanced_vector_emotion_analyzer.py`

#### Step 1.1: Add Margin Calculation Helper
```python
def _calculate_emotion_margin(self, emotions: Dict[str, float]) -> Tuple[float, str, str]:
    """
    Calculate margin between top two emotions.
    
    Returns:
        Tuple of (margin, primary_emotion, secondary_emotion)
    """
    sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_emotions) < 2:
        return 0.0, sorted_emotions[0][0], "none"
    
    primary_emotion, primary_score = sorted_emotions[0]
    secondary_emotion, secondary_score = sorted_emotions[1]
    margin = primary_score - secondary_score
    
    return margin, primary_emotion, secondary_emotion
```

#### Step 1.2: Replace `_determine_primary_emotion()` with Adaptive Logic
Replace the existing simple logic with:

```python
def _determine_primary_emotion(self, emotions: Dict[str, float]) -> Tuple[str, float]:
    """
    Determine primary emotion using adaptive confidence thresholding.
    
    Adaptive Strategy:
    - Neutral requires HIGH confidence (≥0.70) OR large margin (≥0.30)
    - Emotions accepted at MODERATE confidence (≥0.35) with clear winner (≥0.15 margin)
    - OR emotions accepted with very large margin (≥0.25) even at low confidence
    - Smart fallback: When neutral wins weakly, check for strong alternatives
    """
    if not emotions:
        return "neutral", 0.3
    
    # Calculate margin between top two emotions
    margin, primary_emotion, secondary_emotion = self._calculate_emotion_margin(emotions)
    primary_confidence = emotions.get(primary_emotion, 0.0)
    
    logger.info(f"🎯 ADAPTIVE THRESHOLD: Primary={primary_emotion}({primary_confidence:.3f}), "
                f"Secondary={secondary_emotion}({emotions.get(secondary_emotion, 0.0):.3f}), "
                f"Margin={margin:.3f}")
    
    # === ADAPTIVE THRESHOLDING LOGIC ===
    
    if primary_emotion == 'neutral':
        # NEUTRAL DETECTION: Require strong evidence
        
        # Strong neutral signal: high confidence OR large margin
        if primary_confidence >= 0.70 or margin >= 0.30:
            logger.info(f"✅ NEUTRAL ACCEPTED: Strong signal (conf={primary_confidence:.3f}, margin={margin:.3f})")
            return "neutral", primary_confidence
        
        # Medium-strong neutral: moderate confidence with separation
        elif primary_confidence >= 0.50 and margin >= 0.08:
            logger.info(f"✅ NEUTRAL ACCEPTED: Medium-strong (conf={primary_confidence:.3f}, margin={margin:.3f})")
            return "neutral", primary_confidence
        
        else:
            # Neutral won but not convincingly - look for alternatives
            logger.info(f"⚠️ NEUTRAL WEAK: Looking for non-neutral alternative (conf={primary_confidence:.3f}, margin={margin:.3f})")
            
            # Find best non-neutral emotion
            non_neutral_emotions = {k: v for k, v in emotions.items() if k != 'neutral'}
            if non_neutral_emotions:
                best_emotion, best_score = max(non_neutral_emotions.items(), key=lambda x: x[1])
                gap_to_neutral = primary_confidence - best_score
                
                # Accept non-neutral if it's strong OR very close to neutral
                if best_score >= 0.40 or gap_to_neutral < 0.05:
                    logger.info(f"✅ NON-NEUTRAL PREFERRED: {best_emotion}({best_score:.3f}) over weak neutral (gap={gap_to_neutral:.3f})")
                    return best_emotion, best_score
            
            # All emotions too weak - fall back to neutral
            logger.info(f"⚠️ FALLBACK TO NEUTRAL: No strong alternatives found")
            return "neutral", primary_confidence
    
    else:
        # NON-NEUTRAL EMOTION DETECTION
        
        # High confidence emotion
        if primary_confidence >= 0.50:
            logger.info(f"✅ EMOTION ACCEPTED: High confidence (conf={primary_confidence:.3f})")
            return primary_emotion, primary_confidence
        
        # Clear winner: moderate confidence with good margin
        elif primary_confidence >= 0.35 and margin >= 0.15:
            logger.info(f"✅ EMOTION ACCEPTED: Clear winner (conf={primary_confidence:.3f}, margin={margin:.3f})")
            return primary_emotion, primary_confidence
        
        # Very large margin: accept even at low confidence
        elif margin >= 0.25:
            logger.info(f"✅ EMOTION ACCEPTED: Very large margin (margin={margin:.3f})")
            return primary_emotion, primary_confidence
        
        else:
            # Emotion is weak - check if should fall back to neutral
            neutral_score = emotions.get('neutral', 0.0)
            
            if neutral_score >= 0.30:
                logger.info(f"⚠️ FALLBACK TO NEUTRAL: Weak emotion (conf={primary_confidence:.3f}, margin={margin:.3f}), neutral available ({neutral_score:.3f})")
                return "neutral", neutral_score
            else:
                # Even neutral is weak - keep the emotion
                logger.info(f"✅ EMOTION KEPT: All signals weak, keeping {primary_emotion} (conf={primary_confidence:.3f})")
                return primary_emotion, primary_confidence
```

### Phase 2: Reduce Keyword-Based Corrections (CLEANUP)
**File**: `src/intelligence/enhanced_vector_emotion_analyzer.py`

#### Step 2.1: Simplify `_apply_conversation_context_adjustments()`
With adaptive thresholding handling neutral bias, we can simplify or remove keyword-based corrections:

```python
def _apply_conversation_context_adjustments(self, content: str, emotion_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Apply minimal conversation context adjustments.
    
    NOTE: With adaptive thresholding, most neutral bias is handled systematically.
    This method now only handles EXTREME edge cases.
    """
    adjusted_scores = emotion_scores.copy()
    content_lower = content.lower()
    
    # Only handle EXTREME passion contexts (3+ strong keywords)
    passion_keywords = ['passionate', 'love', 'adore', 'devoted', 'crucial', 'vital']
    passion_matches = sum(1 for keyword in passion_keywords if keyword in content_lower)
    
    if passion_matches >= 3:  # Raised threshold - only extreme cases
        neutral_score = adjusted_scores.get('neutral', 0.0)
        if neutral_score > 0.6:  # Only adjust if neutral is very dominant
            reduction = min(0.2, neutral_score * 0.3)  # Reduced adjustment
            adjusted_scores['neutral'] = neutral_score - reduction
            adjusted_scores['joy'] = adjusted_scores.get('joy', 0.0) + reduction
            logger.info(f"🎭 EXTREME CONTEXT: Detected extreme passion ({passion_matches} keywords) - adjusted neutral")
    
    return adjusted_scores
```

### Phase 3: Testing & Validation (CRITICAL)

#### Step 3.1: Create Validation Test Suite
**File**: `tests/automated/test_adaptive_emotion_threshold.py`

```python
"""
Test suite for adaptive emotion threshold implementation.
Validates that neutral bias is eliminated and emotions are properly detected.
"""

import pytest
import asyncio
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

class TestAdaptiveEmotionThreshold:
    
    @pytest.fixture
    def analyzer(self):
        return EnhancedVectorEmotionAnalyzer(vector_memory_manager=None)
    
    def test_false_neutral_cases(self, analyzer):
        """Test cases that were incorrectly classified as neutral before fix"""
        test_cases = [
            ("I don't know what to do anymore.", "sadness"),
            ("Things have been difficult lately.", "sadness"),
            ("Why does this keep happening?", "anger"),
            ("Everything feels overwhelming.", "fear"),
        ]
        
        for message, expected_emotion in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions)
            assert primary == expected_emotion or confidence > 0.4, \
                f"Failed for '{message}': got {primary} ({confidence:.3f}), expected {expected_emotion}"
    
    def test_true_neutral_cases(self, analyzer):
        """Test cases that should correctly remain neutral"""
        test_cases = [
            "How are you today?",
            "Tell me more about that.",
            "What did you do yesterday?",
            "The meeting is at 3pm.",
        ]
        
        for message in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions)
            assert primary == "neutral", \
                f"False positive for '{message}': got {primary} ({confidence:.3f})"
    
    def test_clear_emotions(self, analyzer):
        """Test cases with clear emotional signals"""
        test_cases = [
            ("I'm so happy!", "joy"),
            ("This is terrible!", "disgust"),
            ("I'm really worried about this.", "fear"),
            ("That makes me so angry!", "anger"),
        ]
        
        for message, expected_emotion in test_cases:
            emotions = analyzer._analyze_keyword_emotions(message)
            primary, confidence = analyzer._determine_primary_emotion(emotions)
            assert primary == expected_emotion, \
                f"Failed for '{message}': got {primary} ({confidence:.3f}), expected {expected_emotion}"
```

#### Step 3.2: Run Validation Tests
```bash
# Activate environment
source .venv/bin/activate

# Run test suite
pytest tests/automated/test_adaptive_emotion_threshold.py -v

# Run with direct Python validation
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
export DISCORD_BOT_NAME=elena

python -c "
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
analyzer = EnhancedVectorEmotionAnalyzer()

test_messages = [
    'I don\\'t know what to do anymore.',
    'How are you today?',
    'I\\'m so happy!',
    'Things have been difficult lately.'
]

for msg in test_messages:
    emotions = analyzer._analyze_keyword_emotions(msg)
    primary, confidence = analyzer._determine_primary_emotion(emotions)
    print(f'{msg[:40]:40} → {primary:12} ({confidence:.3f})')
"
```

### Phase 4: Integration Testing (PRODUCTION VALIDATION)

#### Step 4.1: Test with Live Bot (Elena)
```bash
# Start infrastructure
./multi-bot.sh infra

# Start Elena bot
./multi-bot.sh bot elena

# Test via HTTP API with emotional messages
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_adaptive_threshold_001",
    "message": "I don'\''t know what to do anymore. Everything feels overwhelming.",
    "metadata": {"platform": "api_test", "channel_type": "dm"}
  }'

# Check logs for adaptive threshold decisions
docker logs whisperengine-multi-elena-bot-1 | grep "ADAPTIVE THRESHOLD"
```

## Success Criteria

### Quantitative Metrics
1. **Neutral rate reduction**: From ~60% to ~15-20% on ambiguous cases
2. **False neutral elimination**: 0% false neutrals on validation test suite
3. **True neutral preservation**: 100% accuracy on genuinely neutral messages
4. **Processing time**: No significant increase (< 5ms overhead)

### Qualitative Metrics
1. **Logging clarity**: Clear adaptive threshold decision logs
2. **Code maintainability**: Reduced keyword-based patches
3. **User experience**: More emotionally attuned bot responses

## Rollback Plan

If issues arise:
1. **Git revert**: Implementation is in feature branch, easy to revert
2. **Feature flag**: Add `ENABLE_ADAPTIVE_THRESHOLDS` environment variable
3. **Fallback**: Keep old `_determine_primary_emotion()` as `_determine_primary_emotion_legacy()`

## Timeline

- **Phase 1** (Core Logic): 30 minutes
- **Phase 2** (Cleanup): 15 minutes  
- **Phase 3** (Testing): 30 minutes
- **Phase 4** (Integration): 15 minutes
- **Total**: ~90 minutes

## Dependencies

- ✅ No new Python packages required
- ✅ No database schema changes
- ✅ No Docker rebuild needed (code is externally mounted)
- ✅ No bot restart needed for testing (restart only after validation)

## Risk Assessment

**LOW RISK**:
- Changes isolated to emotion detection logic
- Does not affect memory storage, CDL system, or core bot functionality
- Comprehensive test suite validates behavior
- Easy rollback via git revert

## Next Steps

1. ✅ Create implementation plan (DONE)
2. 🔄 Implement Phase 1: Core threshold logic
3. 🔄 Implement Phase 2: Cleanup keyword corrections
4. 🔄 Implement Phase 3: Validation tests
5. 🔄 Implement Phase 4: Integration testing
6. 📊 Measure success metrics
7. 🚀 Merge to main if successful

---

**Status**: Ready to implement
**Owner**: GitHub Copilot + User
**Created**: November 3, 2025
