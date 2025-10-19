# Enrichment Worker Role Field Fix - October 19, 2025

## 🐛 Critical Bug Discovery: The 468-Token Mystery

### Symptom
All enrichment worker LLM requests were sending **exactly 468 input tokens** regardless of message count:
- 7 messages → 468 tokens
- 68 messages → 468 tokens  
- 640 messages → 468 tokens

This constant size proved conversation content was NOT being included in LLM requests.

### Root Cause
**Schema Field Mismatch**: Enrichment code was looking for wrong field to identify message speakers.

**Expected (by code)**:
```python
memory_type == 'user_message'  # For user messages
memory_type == 'bot_response'  # For bot messages
```

**Actual (in Qdrant)**:
```python
role == 'user'          # For user messages
role == 'bot'           # For bot messages
memory_type == 'conversation'  # For ALL messages (not speaker-specific!)
```

### Impact
- ❌ Fact extraction: 0 facts from ALL users
- ❌ Preference extraction: Would have been 0 results
- ⚠️ Summarization: Partially affected (less severe due to different logic)
- 💸 Cost waste: ~$0.0025 per useless API call × dozens per enrichment cycle

### Why 468 Tokens?
The LLM was only receiving the **prompt template** without any conversation content:
- System message: ~100 tokens
- Instruction prompt: ~350 tokens
- Empty conversation section: 0 tokens
- **Total**: ~468 tokens (constant)

## ✅ Complete Fix Applied

### Files Modified

#### 1. `src/enrichment/fact_extraction_engine.py`
**Function**: `_format_conversation_window()`

**Before**:
```python
memory_type = msg.get('memory_type', '')
if memory_type == 'user_message':
    formatted.append(f"User: {content}")
elif memory_type == 'bot_response':
    formatted.append(f"Bot: {content}")
```

**After**:
```python
role = msg.get('role', '')
if role == 'user':
    formatted.append(f"User: {content}")
elif role in ('bot', 'assistant'):
    formatted.append(f"Bot: {content}")
# FALLBACK for backward compatibility
elif msg.get('memory_type') == 'user_message':
    formatted.append(f"User: {content}")
elif msg.get('memory_type') == 'bot_response':
    formatted.append(f"Bot: {content}")
```

#### 2. `src/enrichment/summarization_engine.py`
**Function**: `_format_messages_for_llm()`

**Before**:
```python
role = "User" if msg.get('memory_type') == 'user_message' else bot_name
```

**After**:
```python
msg_role = msg.get('role', '')
if msg_role == 'user':
    role = "User"
elif msg_role in ('bot', 'assistant'):
    role = bot_name
# FALLBACK for backward compatibility
elif msg.get('memory_type') == 'user_message':
    role = "User"
else:
    role = bot_name
```

#### 3. `src/enrichment/worker.py`
**Function**: `_format_messages_for_preference_analysis()`

Applied same fix as fact_extraction_engine.py

**Function**: Message fetching (2 locations)

**CRITICAL**: Added `'role'` field to message dictionaries when fetching from Qdrant:

**Before**:
```python
messages.append({
    'content': point.payload.get('content', ''),
    'timestamp': point.payload.get('timestamp', ''),
    'memory_type': point.payload.get('memory_type', ''),
    'emotion_label': point.payload.get('emotion_label', 'neutral')
})
```

**After**:
```python
messages.append({
    'content': point.payload.get('content', ''),
    'timestamp': point.payload.get('timestamp', ''),
    'memory_type': point.payload.get('memory_type', ''),
    'role': point.payload.get('role', ''),  # CRITICAL FIX
    'emotion_label': point.payload.get('emotion_label', 'neutral')
})
```

## 🧪 Validation Test Results

### Test Configuration
- User: `672814231002939413`
- Messages: 10 (mixed user/bot)
- Collection: `whisperengine_memory_elena`

### Before Fix
- Conversation text: **EMPTY** (0 chars)
- Total prompt: ~468 tokens
- Facts extracted: **0**
- Cost: $0.0025 wasted per request

### After Fix
- Conversation text: **1,531 chars** ✅
- Total prompt: **2,865 chars** ✅
- Facts extracted: **3 facts** ✅
  - tacos (food): tried
  - coding (hobby): does
  - Luna (pet): has
- Token usage: **VARIES by message count** (as expected!)

### Debug Output Confirming Fix
```
🔍 _format_conversation_window ENTRY: Received 10 messages
🔍 Sample message role: user (memory_type: conversation)
🔍 FORMATTED CONVERSATION: 1531 chars, 10 lines
🔍 CONVERSATION TEXT BUILT: 1531 chars
🔍 EXTRACTION PROMPT SIZE: 2865 chars (conversation: 1531 chars)
```

## 📊 Qdrant Schema Reference

### Current Schema (as of Oct 2025)
- **`role`**: Speaker identification (`'user'`, `'bot'`, `'assistant'`)
- **`memory_type`**: Content classification (`'conversation'`, `'fact'`, `'bot_self_reflection_llm'`, etc.)
- **Usage**: Use `role` for speaker, `memory_type` for content type

### Distribution in Elena Collection (sample of 100 points)
**Memory Types**:
- `conversation`: 92 points
- `fact`: 5 points
- `bot_self_reflection_llm`: 1 point
- `bot_self_knowledge_llm`: 2 points

**Roles** (within conversation type):
- `bot`: 56 messages
- `user`: 34 messages
- `assistant`: 3 messages
- `conversation_pair`: 2 messages

## 🎯 Impact & Lessons Learned

### Immediate Impact
- ✅ Fact extraction now works correctly
- ✅ Preference extraction will work correctly
- ✅ Summarization improved (was partially working)
- ✅ Token usage varies correctly with message count
- ✅ No more money wasted on empty LLM calls

### Prevention Strategy
1. **Schema validation**: Add tests verifying field names match between code and storage
2. **Debug logging**: Aggressive logging caught this issue immediately
3. **Token monitoring**: User's OpenRouter dashboard observation was critical
4. **Test with real data**: Container tests revealed actual field names
5. **Backward compatibility**: Fallback checks prevent future schema migrations from breaking silently

### Why This Wasn't Caught Earlier
1. **Summarization partially worked** - used different field access pattern
2. **No error messages** - Empty conversation is valid, just useless
3. **LLM calls succeeded** - Returns valid JSON with 0 facts
4. **Schema evolution** - Code written for old schema, data migrated to new schema

## 🔒 Backward Compatibility

All formatting functions include fallback checks for old `memory_type` field:
- If `role` field exists → use it (current schema)
- Else if `memory_type == 'user_message'` → treat as user (legacy)
- Else if `memory_type == 'bot_response'` → treat as bot (legacy)

This ensures the code works with both old and new Qdrant collections.

## 📝 Testing Checklist

- [x] Fact extraction with role field
- [x] Message formatting builds conversation text
- [x] Token count varies with message length
- [x] Facts successfully extracted from real conversations
- [x] Debug logging shows correct conversation content
- [ ] Full enrichment cycle test (all users)
- [ ] Preference extraction test
- [ ] Summarization verification

## 🚀 Next Steps

1. **Resume enrichment worker** - Now safe to run without burning money
2. **Monitor token usage** - Should see varying token counts based on message count
3. **Verify fact extraction** - Check PostgreSQL for newly extracted facts
4. **Full regression test** - Run complete enrichment cycle on all users
5. **Schema documentation** - Update docs to clarify role vs memory_type usage

---

**Fixed by**: AI Assistant  
**Discovered by**: User via OpenRouter dashboard token analysis  
**Date**: October 19, 2025  
**Build**: whisperengine-multi-enrichment-worker (post-fix)
