# Memory Hierarchy Fix - October 2025

## Problem Identified

Elena's prompts showed redundant memory sections with the SAME recent messages appearing in multiple places:

```
🧠 RELEVANT CONVERSATION CONTEXT:
1. When can we meet for coffee...
2. Let's get coffee at the pier! Want to meet up?...
3. haha. yep! Hey, can we meet for dinner?...

RELEVANT MEMORIES:
CONVERSATION TOPICS: Conversation about When can we meet for coff...; 
Conversation about Let's get coffee at the p...; 
Conversation about haha. yep! Hey, can we me...
```

**The Issue**: Both sections were showing the SAME recent messages, just with different truncation lengths. This wasted valuable context space and didn't provide proper temporal hierarchy.

## Root Cause

Location: `src/core/message_processor.py` lines 1190-1235

The code was:
1. Taking recent conversation parts (last 2 hours)
2. Extracting "topic labels" like "Food discussion" or "Beach activities"
3. Taking older conversation parts (beyond 2 hours)
4. Extracting MORE "topic labels" from them
5. Both ended up being just shortened versions of recent messages

**Problem**: Topic extraction was applying to BOTH recent AND older memories, when it should only apply to older memories as SUMMARIES.

## Solution Implemented

### New Memory Hierarchy (Proper 3-Tier System)

1. **RECENT MESSAGES** (Last 2 hours) - Full conversation context
   - Shown in: `🧠 RELEVANT CONVERSATION CONTEXT` section
   - Format: Full message pairs with 300-char previews
   - Purpose: Immediate conversation continuity

2. **PAST CONVERSATION SUMMARIES** (Older than 2 hours) - Actual summaries
   - Shown in: `PAST CONVERSATION SUMMARIES` section (renamed from "CONVERSATION TOPICS")
   - Format: "Discussed meeting plans: can we meet for coffee", "Talked about food preferences: pizza and burgers"
   - Purpose: Medium-term context from beyond recent conversation

3. **USER FACTS** (All time) - Persistent facts
   - Shown in: `USER FACTS` section
   - Format: "[Preferred name: Mark]", "[Activities: beach activities, diving]"
   - Purpose: Long-term user identity and preferences

### Code Changes

**File**: `src/core/message_processor.py`

**Changed** (lines 1188-1227):
- Removed `conversation_topics` extraction from recent messages
- Replaced `_extract_topic_from_memory()` with `_create_conversation_summary()`
- Changed label from "CONVERSATION TOPICS" to "PAST CONVERSATION SUMMARIES"
- Now creates ACTUAL summaries like "Discussed meeting plans: ..." instead of just "Food discussion"

**Added** (lines 1590-1635): New `_create_conversation_summary()` method
- Parses user/bot conversation structure
- Creates contextual summaries based on content keywords
- Returns descriptive summaries: "Discussed beach/ocean activities: ..." instead of just "Beach activities"
- Skips very short/greeting-only content
- Provides fallback generic summaries for unmatched content

### Summary Format Examples

**Before** (topic labels - not helpful):
```
CONVERSATION TOPICS: Food discussion; Beach activities; Greetings and social
```

**After** (actual summaries - much more useful):
```
PAST CONVERSATION SUMMARIES: Discussed meeting plans: can we meet for coffee; 
Talked about food preferences: pizza sounds delicious; 
Discussed beach/ocean activities: swimming and diving plans
```

## Benefits

1. **No More Redundancy**: Recent messages only appear in one section (RELEVANT CONVERSATION CONTEXT)
2. **True Temporal Hierarchy**: Recent (full) → Medium-term (summaries) → Long-term (facts)
3. **Better Context Utilization**: Summaries are more informative than topic labels
4. **Clearer Intent**: Each section has a distinct purpose and temporal scope
5. **More Efficient**: Older conversations are compressed into summaries, not just truncated

## Response Length Impact

This fix should ALSO help with Elena's verbosity because:
- Less redundant context = more focused prompt
- Clear distinction between "what we just said" vs "what we discussed before"
- Summaries of older conversations prevent Elena from re-addressing already-resolved topics

## Testing

1. Send Elena a new message
2. Check prompt logs: `logs/prompts/elena_*.json`
3. Verify:
   - ✅ Recent messages appear in `🧠 RELEVANT CONVERSATION CONTEXT` section
   - ✅ Older conversations appear as summaries in `PAST CONVERSATION SUMMARIES` section
   - ✅ No redundancy between sections
   - ✅ User facts remain in `USER FACTS` section

## Files Modified

- `src/core/message_processor.py`:
  - Lines 1188-1227: Memory hierarchy logic fix
  - Lines 1590-1635: New `_create_conversation_summary()` method
  - Line 1234: Updated logging message

## Deployment Status

- ✅ Code changes applied
- ✅ Elena bot restarted with new memory hierarchy
- ⏳ Waiting for user testing to validate improvements
