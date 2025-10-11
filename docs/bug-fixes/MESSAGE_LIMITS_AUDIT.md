# WhisperEngine Message/Memory Limits Audit
**Date**: October 11, 2025
**File**: src/core/message_processor.py

## 1. MEMORY RETRIEVAL FROM VECTOR STORAGE

### Initial Vector Search
- **Line 1364**: `user_memories[:6]` 
- **Limit**: 6 memories total
- **Type**: Individual messages (mix of user_message and bot_response)
- **Result**: ~3-6 conversation turns depending on semantic search ranking

## 2. MEMORY CONTENT WRAPPING (First Pass)

### Standard Memory Wrapping
- **Line 1392**: `content[:500]` - Previous conversation format
- **Line 1394**: `content[:500]` - Standard memory format
- **Purpose**: Preserve context before categorization
- **Increased from**: 120 chars → 500 chars

### Metadata Fallback (Legacy Path)
- **Line 1407**: `user_message[:300]` - User message from metadata
- **Line 1408**: `bot_response[:300]` - Bot response from metadata  
- **Line 1418**: `user_message[:300]` - Alternative metadata path
- **Line 1428**: `fact[:300]` - Fact extraction
- **Purpose**: Handle legacy metadata format
- **Increased from**: 100-120 chars → 300 chars

## 3. MEMORY PROCESSING & CATEGORIZATION

### Recent Conversations (<2 hours old)
- **Line 1487**: `clean_part[:1500]` per message
- **Line 1494**: `[:10]` max 10 unique recent messages
- **Total Context**: Up to 15,000 chars (1500 × 10)
- **Purpose**: Verbatim conversation continuity
- **Rationale**: Discord messages up to 2000 chars
- **Increased from**: 400 chars → 1500 chars per message

### Older Conversation Summaries (>2 hours old)
- **Line 1498**: `[:5]` max 5 summaries
- **Each summary**: Up to 400 chars (from _create_conversation_summary)
- **Total Context**: Up to 2,000 chars (400 × 5)
- **Purpose**: Compressed long-term memory

## 4. CONVERSATION HISTORY (Separate System)

### Conversation Cache/History
- **Line 1535**: `limit=15` messages from get_conversation_history()
- **Type**: Recent conversation messages (separate from vector search)
- **Purpose**: Immediate conversation continuity (last N turns)
- **Includes**: Both user and bot messages in order

## 5. SUMMARY GENERATION LIMITS

### Topic Extraction
- **Line 1853**: `[:5]` max 5 topics
- **Purpose**: Limit topic diversity in summaries

### Memory Snippet Creation
- **Line 1817**: `content[:400]` per snippet
- **Purpose**: Create memory summary snippets
- **Increased from**: 200 chars → 400 chars

### Conversation Summary Content
- **Line 1898**: `content_preview = clean_content[:400]`
- **Purpose**: Semantic categorization for older conversations
- **Used in**: _create_conversation_summary() function

## 6. OTHER LIMITS (Non-Critical)

### Debug/Logging
- **Line 4611**: `content[:100]` - Debug source message preview
- **Purpose**: Logging only, doesn't affect LLM context

### Entity Extraction
- **Line 4663**: `[:5]` max 5 entities per statement
- **Line 4668**: `[:3]` max 3 words per entity
- **Purpose**: Fact extraction limits

---

## TOTAL CONTEXT CALCULATION

### Maximum Memory Context Sent to LLM:

1. **USER FACTS**: Variable (names, preferences, relationships)
   - Extracted from memories
   - No hard limit

2. **RECENT CONVERSATIONS** (<2 hours):
   - 10 messages × 1500 chars = **15,000 chars max**

3. **PAST CONVERSATION SUMMARIES** (>2 hours):
   - 5 summaries × 400 chars = **2,000 chars max**

4. **CONVERSATION HISTORY** (immediate context):
   - 15 recent messages from conversation cache
   - No truncation at retrieval (full messages)

**TOTAL MEMORY CONTEXT**: ~17,000+ chars possible

---

## CONSISTENCY CHECK ✅

### Character Limits Progression (Logical Flow):

1. **Initial wrapping**: 500 chars (preserve semantic context)
2. **Metadata fallback**: 300 chars (legacy format)
3. **Recent messages**: 1500 chars (Discord message size)
4. **Older summaries**: 400 chars (compressed long-term)
5. **Summary generation**: 400 chars (semantic categorization)

### Design Rationale:

✅ **Recent > Older**: Recent messages get more space (1500 vs 400)
✅ **Verbatim > Summary**: Recent kept verbatim, older summarized
✅ **Discord-aware**: 1500 chars accommodates most Discord messages (2000 max)
✅ **Context budget**: ~17K chars is reasonable for modern LLM context windows
✅ **Progressive compression**: Memory gets more compressed as it ages

---

## RECOMMENDATIONS

### Current Limits are APPROPRIATE:

1. ✅ **6 memories from vector search**: Good balance (3-6 turns)
2. ✅ **1500 chars recent messages**: Captures most Discord messages
3. ✅ **10 recent messages**: Adequate continuity without bloat
4. ✅ **5 older summaries**: Reasonable long-term context
5. ✅ **15 conversation history**: Good immediate context window

### No Changes Needed:

The system now has consistent, logical limits that:
- Preserve conversation fidelity
- Accommodate Discord message lengths
- Use progressive compression for older content
- Maintain reasonable LLM context size
- Follow the two-tier memory architecture design

---

## BUGS FIXED (October 11, 2025):

1. ✅ Memory wrapping: 120 → 500 chars
2. ✅ Metadata fallback: 100-120 → 300 chars
3. ✅ Summary generation: 50 → 400 chars
4. ✅ Recent messages: 400 → 1500 chars
5. ✅ Recent conversation processing: Dead variable fixed
6. ✅ Anti-hallucination guidance: Added when memory empty

**Status**: All limits reviewed and confirmed consistent ✅
