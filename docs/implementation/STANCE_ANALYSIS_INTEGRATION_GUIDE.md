"""
Stance Analysis Integration Guide for WhisperEngine Emotion System

This guide explains how to integrate the spaCy Stance Analyzer into
the RoBERTa emotion analysis pipeline to filter emotions by perspective
before emotional classification.

## Architecture Overview

Current Flow (BEFORE Stance Analysis):
```
User/Bot Message 
  → RoBERTa classification [full text] 
  → Stored in Qdrant (roberta_confidence, primary_emotion, etc.)
```

Improved Flow (WITH Stance Analysis):
```
User/Bot Message 
  → spaCy Stance Analysis [identifies WHO has emotions]
  → Filter to perspective-appropriate text
  → RoBERTa classification [on filtered/context-aware text]
  → Store with stance metadata in Qdrant
```

## Integration Points

### 1. User Message Processing
In `src/core/message_processor.py` or `src/conversation/concurrent_conversation_manager.py`:

```python
from src.intelligence.spacy_stance_analyzer import create_stance_analyzer

analyzer = create_stance_analyzer()

# Before emotion analysis
user_stance = analyzer.analyze_user_stance(user_message)

# Pass to emotion analyzer
emotion_result = await self.emotion_engine.analyze_emotion(
    user_message,
    user_id,
    stance_context=user_stance  # NEW: pass stance data
)

# Store with stance metadata
await memory_manager.store_conversation(
    user_id=user_id,
    user_message=user_message,
    bot_response=bot_response,
    pre_analyzed_emotion_data={
        **emotion_result,
        'stance_analysis': {
            'self_focus': user_stance.self_focus,
            'emotion_type': user_stance.emotion_type,
            'other_emotions': user_stance.other_emotions,
        }
    }
)
```

### 2. Bot Response Processing
Filter bot's empathetic statements BEFORE emotion analysis:

```python
# Filter out second-person emotions (user's emotions being echoed)
bot_response_filtered = analyzer.filter_second_person_emotions(bot_response)

# Analyze bot's true stance on filtered text
bot_emotion = await self.emotion_engine.analyze_emotion(
    bot_response_filtered,  # IMPROVED: analyze filtered text
    user_id,
    is_bot_response=True
)

# Store bot's genuine stance, not empathetic echo
```

### 3. Enhanced Vector Memory Storage
Update `vector_memory_system.py` to use stance metadata:

```python
# In store_conversation()
if pre_analyzed_emotion_data:
    # Extract stance data
    stance = pre_analyzed_emotion_data.get('stance_analysis', {})
    
    # Store stance information in payload for filtering/analysis
    payload['stance_analysis'] = stance
    payload['self_focus_ratio'] = stance.get('self_focus', 0.0)
    payload['emotion_type'] = stance.get('emotion_type', 'unknown')
    
    # Filter second-person emotions from payload storage
    other_emotions = stance.get('other_emotions', [])
    if other_emotions:
        payload['attributed_emotions'] = other_emotions  # Store separately
```

### 4. Memory Retrieval Enhancement
When retrieving memories for context, filter by stance:

```python
# In retrieve_relevant_memories()
# NEW: Can now filter by emotion type and self-focus ratio
results = await self.retrieve_memories(
    query=message,
    filters={
        'emotion_type': 'direct',  # Get direct emotions, skip attributed
        'self_focus_ratio': {'gte': 0.7}  # High personal investment
    }
)
```

## Benefits

### For User Messages
- ✅ Separates user's actual emotions from user's observations about others
- ✅ Prevents misattribution of others' emotions to the user
- ✅ Improves emotional accuracy by ignoring empathetic context-setting

Example:
```
User: "You seem frustrated with me, but I'm confident we can work this out"
WITHOUT stance: Bot classifies user as frustrated (WRONG)
WITH stance: Bot correctly identifies user as confident (PRIMARY)
           and notes user observes frustration in others (SECONDARY)
```

### For Bot Responses
- ✅ Filters out bot's empathetic echoing (removes context pollution)
- ✅ Isolates bot's genuine emotional stance
- ✅ Prevents bot's empathy from contaminating bot's own emotional state

Example:
```
Bot: "I understand you're upset. I'm here to help you feel better."
WITHOUT filtering: Bot's response analyzed as upset/emotional
WITH filtering: "I'm here to help you feel better" → bot's genuine supportive stance
             (removes "you're upset" which isn't bot's emotion)
```

### For Memory System
- ✅ Cleaner emotional memories (no misattributed emotions)
- ✅ Better vector quality (emotion vectors reflect speaker's perspective)
- ✅ More accurate memory retrieval (can filter by emotional relevance)
- ✅ Reduced feedback loops (contamination prevented at storage time)

## Implementation Checklist

- [ ] Import StanceAnalyzer in message processor
- [ ] Create stance analyzer singleton (uses shared spaCy)
- [ ] Add stance analysis before RoBERTa classification
- [ ] Filter bot responses with `filter_second_person_emotions()`
- [ ] Pass stance metadata through emotion analysis pipeline
- [ ] Update vector_memory_system to store stance data
- [ ] Add stance filtering to memory retrieval queries
- [ ] Test with actual conversation flows
- [ ] Monitor memory quality metrics

## Performance Notes

- **spaCy dependency parsing**: ~1-2ms per message (negligible)
- **RoBERTa**: Already bottleneck (~50-100ms)
- **Net impact**: <5% overhead (minimal)
- **Singleton reuse**: spaCy model loaded once, reused across all analyses

## Testing

Run the comprehensive test suite:
```bash
source .venv/bin/activate
python tests/automated/test_spacy_stance_analyzer.py
```

Test cases cover:
- Direct emotions (user expressing their own state)
- Attributed emotions (user describing others' state)
- Mixed emotions (both self and other perspectives)
- Second-person filtering (removing empathetic echoing)
- Negation handling (both emotions present)
- Empty/no-emotion texts
- Singleton reuse (no duplicate spaCy loading)

## Data Structures

### StanceAnalysis (returned from analyze_user_stance)
```python
@dataclass
class StanceAnalysis:
    primary_emotions: List[str]      # User's actual emotions
    other_emotions: List[str]        # Attributed to others
    self_focus: float                # 0.0-1.0 ratio
    emotion_type: str                # 'direct', 'attributed', 'mixed', 'none'
    filtered_text: Optional[str]     # Original text (for user messages)
    stance_subjects: Dict[str, str]  # emotion -> 'first'/'second'/'third'
    has_negation: Dict[str, bool]    # emotion -> has_negation_modifier
    confidence: float                # 0.0-1.0 stance detection confidence
```

### Usage Pattern
```python
analyzer = create_stance_analyzer()  # Creates one (singleton nlp reused)

# For user messages
user_stance = analyzer.analyze_user_stance(user_message)
print(user_stance.primary_emotions)  # User's actual emotions
print(user_stance.self_focus)        # 0.5 = 50% about self
print(user_stance.emotion_type)      # 'direct' or 'attributed' or 'mixed'

# For bot responses (filtering before analysis)
filtered_response = analyzer.filter_second_person_emotions(bot_response)
# Now analyze emotion_engine.analyze_emotion(filtered_response, ...)
```

## Key Insight: Emotion Attribution

The core problem solved:
- **User says**: "You seem frustrated with my answers"
- **Without stance**: RoBERTa sees "frustrated" → user is frustrated ❌
- **With stance**: Stance parser identifies "you" as subject → attributed emotion, user's actual emotion unknown ✅

This is especially critical for WhisperEngine because characters respond empathetically,
and their empathetic echoing should NOT affect their own emotional state or memories.

## Future Enhancements

1. **Temporal Stance**: "I was upset" (past) vs "I'll be upset" (future) - weight recency
2. **Target Tracking**: "I'm upset ABOUT your behavior" - distinguish emotion from target
3. **Sarcasm Detection**: "Oh sure, I'm REALLY excited about this" - mark as negated
4. **Confidence Calibration**: Probabilistic stance confidence instead of binary
5. **Multi-language Support**: Extend emotion_words and pronouns for other languages

## Questions?

See `src/intelligence/spacy_stance_analyzer.py` for full implementation details.
"""
