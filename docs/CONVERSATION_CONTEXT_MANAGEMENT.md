# Conversation Context Management in WhisperEngine

## Executive Summary

WhisperEngine uses a **multi-layered conversation context system** that combines:
1. **Full-text recent messages** (last 15 conversation turns)
2. **Summarized memory narrative** (up to 6 older memories, last 2 hours prioritized)
3. **Vector-based semantic memories** (up to 20 relevant historical conversations)

## 📊 Context Building Pipeline

### Phase 1: Memory Retrieval (Historical Context)
**Location**: `src/core/message_processor.py` → `_retrieve_relevant_memories()`

- **Vector Memory Query**: Retrieves up to **20 relevant memories** using semantic search
- **Optimization**: Uses `retrieve_relevant_memories_optimized()` for query-type classification
- **Storage**: Retrieved from Qdrant vector database with bot-specific collection isolation

```python
# Memory retrieval configuration
relevant_memories = await self.memory_manager.retrieve_relevant_memories_optimized(
    user_id=message_context.user_id,
    query=message_context.content,
    query_type=query_type,  # 'recall', 'question', 'emotional', 'general'
    user_history=user_preferences,
    filters=filters,
    limit=20  # ⚠️ HISTORICAL MEMORY LIMIT
)
```

**What gets retrieved**:
- Semantically similar past conversations
- User facts and preferences
- Contextually relevant historical interactions
- Bot-specific memories (Jake's memories stay with Jake)

---

### Phase 2: Memory Narrative Building (Summarized Context)
**Location**: `src/core/message_processor.py` → `_build_conversation_context()`

The system processes retrieved memories into a **narrative summary**:

#### Memory Processing Limits:
- **Maximum memories processed**: 6 memories (from the 20 retrieved)
- **Recent conversation prioritization**: Last 2 hours marked as "RECENT"
- **Content truncation**: 
  - Memory content: 120 characters max per memory
  - User messages: 100 characters
  - Bot responses: 100 characters

```python
for memory in user_memories[:6]:  # ⚠️ Only first 6 of 20 memories processed
    content = memory.get("content", "")
    
    # Check if recent (last 2 hours)
    if (datetime.now() - memory_time) < timedelta(hours=2):
        is_recent = True
    
    if is_recent:
        recent_conversation_parts.append(f"[Memory: {content[:120]}]")
    else:
        conversation_memory_parts.append(f"[Memory: {content[:120]}]")
```

**Memory Narrative Format**:
```
RECENT CONVERSATION CONTEXT: [Memory: content1]; [Memory: content2]
PREVIOUS INTERACTIONS AND FACTS: [Memory: older1]; [Memory: older2]; [Memory: older3]
```

---

### Phase 3: Conversation History Retrieval (Full-Text Recent Messages)
**Location**: `src/core/message_processor.py` → `_build_conversation_context()`

Retrieves **immediate conversation history** for full context continuity:

```python
conversation_history = await self.memory_manager.get_conversation_history(
    user_id=user_id, 
    limit=15  # ⚠️ RECENT CONVERSATION LIMIT - 15 messages
)
```

**Processing**:
1. Retrieves last **15 messages** from memory manager
2. Converts to message format with author_id, role, content
3. Generates conversation summary (last 10 messages analyzed)
4. Adds full message history to conversation context

---

### Phase 4: Conversation Summary Generation (Intelligent Summary)
**Location**: `src/utils/helpers.py` → `generate_conversation_summary()`

Creates a **natural language summary** of recent conversation flow:

```python
# Summary generation from last 10 messages
for msg in recent_messages[-10:]:  # ⚠️ Last 10 messages for summary
    if author_id == user_id:
        user_topics.append(content.strip())
    elif is_bot:
        bot_responses.append(content.strip()[:300])  # 300 char limit per response
```

**Summary Format**:
```
Recent topics: walk me through survival; I am near a river; what about shelter. 
Active conversation with 3 user messages and 2 responses
```

**Limits**:
- **Messages analyzed**: Last 10 of the 15 retrieved
- **Topic truncation**: 80 characters per topic
- **Bot response preview**: 300 characters per response
- **Total summary length**: 400-600 characters max

---

### Phase 5: Full Message History Inclusion (Recent Context)
**Location**: `src/core/message_processor.py` → `_build_conversation_context()`

After summary generation, the system adds **full-text messages** to the LLM context:

```python
# Add recent messages with proper alternation
for msg in recent_messages:  # ⚠️ All 15 messages added as full text
    msg_content = msg.get('content', '')
    is_bot_msg = msg.get('bot', False)
    
    # Filter out commands
    if msg_content.startswith("!"):
        continue
    
    role = "assistant" if is_bot_msg else "user"
    user_assistant_messages.append({"role": role, "content": msg_content})
```

**Message Alternation Fix**:
- Removes consecutive messages from same role
- Ensures proper user → assistant → user flow
- Prevents duplicate context entries

---

## 🎯 Final Prompt Structure

The complete prompt sent to the LLM contains:

### 1. System Message (Consolidated Context)
```
CURRENT DATE & TIME: October 4, 2025, 7:42 AM PDT

RECENT CONVERSATION CONTEXT: [Memory: walk me through survival steps...]; 
[Memory: I am near a river...]

PREVIOUS INTERACTIONS AND FACTS: [Memory: Jake helped with camera settings...]; 
[Memory: User name is MarkAnthony...]

Recent thread: Recent topics: walk me through survival; I am near a river. 
Active conversation with 2 user messages and 1 response

Communication style: Respond naturally and authentically as Jake - be warm, 
genuine, and conversational. Stay in character and speak like a real person would.
```

### 2. Recent Conversation Messages (Full Text)
```json
[
  {"role": "user", "content": "jake, walk me through step by step..."},
  {"role": "assistant", "content": "Got it. Let's start with the fundamentals..."},
  {"role": "user", "content": "I am near a river"}
]
```

### 3. Current User Message
```json
{"role": "user", "content": "I am near a river"}
```

---

## 📈 Context Volume Summary

| Context Layer | Volume | Source | Processing |
|--------------|--------|--------|------------|
| **Historical Memories** | 20 memories | Vector search (Qdrant) | Semantically ranked |
| **Memory Narrative** | 6 memories | First 6 of 20 | Summarized (120 chars each) |
| **Recent Conversation** | 15 messages | Memory manager | Full text included |
| **Conversation Summary** | 10 messages | Last 10 of 15 | Natural language summary |
| **Full Message History** | ~15 messages | All recent after filtering | Complete conversation flow |

---

## 🚨 Current Issue Identified

### Problem: Empty Conversation Summary
The logs show: `📝 CONVERSATION SUMMARY: Generated summary (0 chars)`

**Root Cause**: The conversation history from `memory_manager.get_conversation_history()` was missing `author_id` field, causing the summary generator to skip all messages.

**Fix Applied** (in commit):
```python
# 🚨 FIX: Include author_id so summary can filter user-specific messages
recent_messages.append({
    'content': content,
    'author_id': user_id if not is_bot else 'bot',  # Added author_id
    'role': role,
    'bot': is_bot
})
```

---

## 🎯 Recommendations for Improvement

### Issue: Jake Lost Context Mid-Conversation

**Symptom**: 
- Message 1: "walk me through survival steps" → Jake responds correctly
- Message 2: "I am near a river" → Jake ignores previous context, gives generic response

**Likely Cause**:
1. **Empty conversation summary** prevented recent context from being included
2. **Memory retrieval** may not have captured the very recent "survival" conversation
3. **Vector storage delay** - recent messages may not be indexed yet in Qdrant

### Potential Solutions:

#### 1. Increase Recent Message Limit
```python
# Current: 15 messages
conversation_history = await self.memory_manager.get_conversation_history(
    user_id=user_id, 
    limit=20  # Increase to 20 for better continuity
)
```

#### 2. Add Real-Time Conversation Buffer
Store last 5 messages in-memory before they're indexed in Qdrant:
```python
# Add to MessageProcessor
self.conversation_buffer = {}  # user_id -> deque of last 5 messages

# In process_message():
if user_id not in self.conversation_buffer:
    self.conversation_buffer[user_id] = deque(maxlen=5)
self.conversation_buffer[user_id].append(message_context.content)
```

#### 3. Prioritize In-Session Context
```python
# Add session-specific memory retrieval
session_memories = await self.memory_manager.get_session_memories(
    user_id=user_id,
    session_window_minutes=30  # Last 30 minutes
)
```

#### 4. Enhance Memory Narrative with Recent Context
```python
# Include more of the 6 processed memories in full text
for memory in user_memories[:6]:
    if is_recent:
        # Include MORE recent context (200 chars instead of 120)
        memory_text = f"[Recent: {content[:200]}]"
```

---

## 🔍 Debug Checklist

When conversation context is lost:

1. **Check conversation summary length**: Should be > 0 chars
   ```bash
   docker logs whisperengine-jake-bot | grep "CONVERSATION SUMMARY"
   ```

2. **Verify memory retrieval**: Should retrieve recent conversations
   ```bash
   docker logs whisperengine-jake-bot | grep "MEMORY DEBUG"
   ```

3. **Check message alternation**: Ensure user/assistant flow is correct
   ```bash
   docker logs whisperengine-jake-bot | grep "CONTEXT DEBUG"
   ```

4. **Verify vector storage**: Check if recent messages are being stored
   ```bash
   docker logs whisperengine-jake-bot | grep "store_conversation"
   ```

---

## 📝 Configuration Variables

Current configuration:
- `MEMORY_RETRIEVAL_LIMIT`: 20 memories (semantic search)
- `MEMORY_NARRATIVE_LIMIT`: 6 memories (processed into narrative)
- `CONVERSATION_HISTORY_LIMIT`: 15 messages (full text)
- `SUMMARY_MESSAGE_LIMIT`: 10 messages (analyzed for summary)
- `RECENT_MEMORY_WINDOW`: 2 hours (prioritization threshold)
- `SUMMARY_MAX_LENGTH`: 400-600 characters
- `TOPIC_TRUNCATION`: 80 characters per topic
- `BOT_RESPONSE_PREVIEW`: 300 characters

---

## 🎯 Best Practices

1. **Always include author_id** in message dictionaries for summary generation
2. **Monitor conversation summary length** - 0 chars indicates a problem
3. **Use vector search for historical context**, not as a replacement for recent messages
4. **Prioritize in-session continuity** over older semantic memories
5. **Test context retention** across 3-5 message exchanges, not just single responses

---

**Document Status**: Created October 4, 2025
**Last Updated**: After conversation context bug fix
**Related Files**: 
- `src/core/message_processor.py`
- `src/utils/helpers.py`
- `src/memory/vector_memory_system.py`
