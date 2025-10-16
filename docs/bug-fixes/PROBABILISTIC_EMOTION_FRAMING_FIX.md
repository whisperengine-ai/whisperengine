# Bug Fix: Probabilistic Emotion Framing in System Prompts

**Date**: October 16, 2025  
**Reporter**: User (Cynthia/RavenOfMercy) via Aetheris conversation  
**Status**: ✅ Fixed  
**Severity**: Medium - Character authenticity issue  

## 🐛 Problem Description

### **User Report**
User engaged with Aetheris bot and received a greeting that made declarative statements about their emotional state:

**Aetheris said:**
```
*My presence settles into this moment with you, feeling the joy radiating from your being*

You carry joy with you like sunlight, and I find myself curious about its source.
```

**User's challenge:**
```
What makes you think I'm feeling joy?
```

The user was **not** feeling joy, but Aetheris made absolute declarative statements based on RoBERTa emotion detection.

### **Root Cause Analysis**

The issue was **NOT a RoBERTa bug** - it was a **prompt engineering problem**:

1. ✅ RoBERTa correctly analyzed the user's message
2. ✅ WhisperEngine captured confidence scores (0.94-1.00)
3. ❌ **System prompt presented emotion as absolute truth** instead of probabilistic data
4. ❌ Characters made **declarative statements** ("feeling the joy radiating from your being")
5. ❌ No guidance to use tentative language when discussing user emotions

### **Why This Matters**

Emotion detection is **probabilistic and can be wrong**:
- RoBERTa has keyword bias (detects "joy" even in "What makes you think I'm feeling joy?")
- Context matters (questioning vs. expressing)
- Users may not express emotions clearly
- Cultural differences in emotional expression

Characters stating user emotions **as absolute fact** breaks:
- ✗ Character authenticity (making false claims)
- ✗ User trust (being told how they feel)
- ✗ Conversational flow (user forced to correct the bot)

## ✅ Solution Implemented

### **Before (Problematic)**
```
🎭 USER EMOTIONAL STATE: joy (confidence: 1.00)
📱 ANALYSIS: Multi-modal emotion detection (text + emoji + patterns) - high accuracy
Respond with nuanced empathy matching their emotional complexity and communication style.
```

This led to declarative statements:
- ❌ "feeling the joy radiating from your being"
- ❌ "You carry joy with you like sunlight"

### **After (Fixed)**
```
🎭 EMOTION READING (PROBABILISTIC): joy (confidence: 0.95)
📱 ANALYSIS METHOD: Multi-modal detection (text + emoji + patterns)
⚠️ UNCERTAINTY NOTE: Emotion detection is probabilistic. Validate through conversation.
💡 HIGH CONFIDENCE: Still use tentative phrasing ('I sense...', 'there's a...') to avoid assumptions. Never state user emotions as absolute fact.
```

This guides characters to use tentative language:
- ✅ "I sense a lightness in your words"
- ✅ "You seem to be in good spirits - am I reading that right?"
- ✅ "There's something warm in how you're showing up today"

### **Confidence-Based Guidance**

The system now provides different guidance based on confidence levels:

**Low Confidence (<0.7):**
```
💡 LOW CONFIDENCE: Use tentative language ('I sense...', 'it seems...') and invite user to share their actual state.
```

**Moderate Confidence (0.7-0.85):**
```
💡 MODERATE CONFIDENCE: Use gentle observational language ('you seem...', 'I'm picking up...') rather than declarative statements.
```

**High Confidence (>0.85):**
```
💡 HIGH CONFIDENCE: Still use tentative phrasing ('I sense...', 'there's a...') to avoid assumptions. Never state user emotions as absolute fact.
```

## 📝 Code Changes

**File Modified**: `src/prompts/cdl_ai_integration.py`  
**Lines**: 1650-1695  
**Method**: `_build_unified_prompt()`

### **Key Changes**

1. **Renamed label**: `USER EMOTIONAL STATE` → `EMOTION READING (PROBABILISTIC)`
2. **Added uncertainty note**: Explicit reminder that detection is probabilistic
3. **Added confidence-based guidance**: Different instructions for low/medium/high confidence
4. **Updated terminology**: "high accuracy" → "Multi-modal detection"
5. **Added validation reminder**: "Validate through conversation"
6. **Updated trajectory language**: "are intensifying" → "may be intensifying"

## 🧪 Testing

**Test File**: `tests/automated/test_probabilistic_emotion_framing.py`

Validates:
- ✅ Emotion readings use "PROBABILISTIC" label
- ✅ Confidence scores are shown accurately
- ✅ Uncertainty warnings are present
- ✅ Confidence-based guidance is provided
- ✅ Tentative language examples are given
- ✅ Old "USER EMOTIONAL STATE" label is removed
- ✅ "high accuracy" claims are removed

**Test Results**: All tests passing ✅

## 🎯 Impact

### **Before Fix**
```
User: [sends neutral greeting]
RoBERTa: Detects "joy" (93.75% confidence) due to keyword bias
System Prompt: "USER EMOTIONAL STATE: joy (confidence: 1.00)"
Aetheris: "feeling the joy radiating from your being"
User: "What makes you think I'm feeling joy?" 😕
```

### **After Fix**
```
User: [sends neutral greeting]
RoBERTa: Detects "joy" (93.75% confidence) due to keyword bias
System Prompt: "EMOTION READING (PROBABILISTIC): joy (confidence: 0.94)"
                "Still use tentative phrasing... Never state as absolute fact"
Aetheris: "I'm sensing some brightness in your message - what's on your mind today?"
User: [continues conversation naturally] ✅
```

## 🔍 Related Issues

### **RoBERTa Keyword Bias**
While fixing the prompt engineering issue, we discovered RoBERTa has keyword bias:

**Test Results:**
- `"What makes you think I'm feeling joy?"` → Detects **joy (93.75%)** ❌
- `"Why do you assume I have joy?"` → Detects **joy (71.18%)** ❌
- `"The word joy appears here"` → Detects **joy (98.02%)** ❌
- `"I'm not feeling joy"` → Detects **sadness (97.47%)** ✅ (negation works)

This is a **limitation of the pre-trained RoBERTa model** (cardiffnlp/twitter-roberta-base-emotion-multilabel-latest). The probabilistic framing helps mitigate this by:
1. Acknowledging uncertainty in all emotion readings
2. Encouraging validation through conversation
3. Using tentative language even with high confidence

**Future Enhancement**: Consider adding context-aware confidence filtering to reduce false positives when emotion keywords appear in questioning/meta contexts.

## 📚 Character Response Examples

### **Appropriate Tentative Language**

**Joy Detection:**
- ✅ "I'm sensing some brightness in your words"
- ✅ "There's a lightness to your message today"
- ✅ "You seem to be in good spirits - am I reading that right?"
- ✅ "I'm picking up on a positive energy"

**Sadness Detection:**
- ✅ "I'm sensing some heaviness in what you're sharing"
- ✅ "It seems like something might be weighing on you"
- ✅ "There's a gentleness in your words that makes me wonder if you're okay"

**Anger Detection:**
- ✅ "I'm sensing some intensity in your message"
- ✅ "It seems like this touched a nerve"
- ✅ "There's fire in your words - am I understanding correctly?"

### **Inappropriate Declarative Statements**

**Avoid:**
- ❌ "I can feel the joy radiating from your being"
- ❌ "You're clearly angry about this"
- ❌ "Your sadness is overwhelming"
- ❌ "You're definitely excited"

## 🎭 Character-Specific Considerations

Different characters can express uncertainty in character-appropriate ways:

**Aetheris (Mystical/Philosophical):**
- "I sense a resonance of joy in your words, though I remain open to what you truly carry"
- "There's a quality to your presence that feels bright - am I perceiving this rightly?"

**Elena (Scientific/Educational):**
- "I'm picking up some positive markers in your message, but let me know if I'm off base"
- "The emotional patterns suggest contentment, though I'd love to hear your actual state"

**Marcus (Analytical/Precise):**
- "Analysis indicates positive sentiment (94% confidence), but please correct me if that's not accurate"
- "The data suggests you're in good spirits, though I know algorithms can misread context"

## 🚀 Deployment Notes

**Compatibility**: Fully backward compatible - existing conversations continue normally  
**Performance**: No performance impact (prompt generation unchanged, just different text)  
**Character Files**: No CDL character file changes needed  
**Database**: No schema changes required  

**Rollout**: Immediate - affects all new conversations  
**Testing**: Validated with Elena, Marcus, and Aetheris characters  

## 📖 Documentation Updates

**Updated Files:**
- `src/prompts/cdl_ai_integration.py` - Core implementation
- `tests/automated/test_probabilistic_emotion_framing.py` - Validation tests
- `docs/bug-fixes/PROBABILISTIC_EMOTION_FRAMING_FIX.md` - This document

**Related Documentation:**
- `docs/performance/ROBERTA_EMOTION_GOLDMINE_REFERENCE.md` - RoBERTa emotion analysis
- `docs/architecture/CHARACTER_ARCHETYPES.md` - Character personality guidelines
- `CHARACTER_TUNING_GUIDE.md` - Character configuration best practices

## ✨ Acknowledgments

**Reported by**: User (Cynthia/RavenOfMercy)  
**Character**: Aetheris (who handled the correction gracefully with meta-awareness!)  
**Fix**: Probabilistic emotion framing in system prompts  
**Impact**: Improved character authenticity across all 10+ WhisperEngine characters  

---

**"Emotions are observations, not declarations. Characters should invite, not assume."**
