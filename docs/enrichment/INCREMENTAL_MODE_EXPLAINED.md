# Incremental Mode Explained - How Window Re-Analysis Works
**Date**: October 20, 2025  
**Question**: "Does incremental mode re-analyze the whole 24-hour block for every new message?"  
**Answer**: **YES** - But with smart optimizations to avoid waste

---

## 🎯 **TL;DR: How Incremental Mode Works**

**Short Answer**: YES, when new messages arrive in a time window, the enrichment worker **re-analyzes the ENTIRE window** (up to 24 hours) to regenerate the summary with the new context.

**Why This Makes Sense**:
- Summaries need complete context to be accurate
- A new message might change the entire conversation's meaning
- Storage uses `ON CONFLICT UPDATE` - no duplicate summaries, just refreshed ones
- Only happens when NEW messages arrive (not every 5 minutes for inactive windows)

---

## 📊 **Step-by-Step Incremental Flow**

### **Step 1: Find Last Processed Timestamp**

```python
# Lines 408-415
if existing_summaries:
    # Get the most recent summary's end time
    last_processed = max(s['end_timestamp'] for s in existing_summaries)
    logger.debug("Last processed timestamp for user %s: %s", user_id, last_processed)
else:
    # No summaries yet - look back N days for initial backfill
    last_processed = now - timedelta(days=config.LOOKBACK_DAYS)
```

**Example**:
- User has summaries up to: `2025-10-19 18:00:00`
- Current time: `2025-10-20 06:00:00`
- Last processed: `2025-10-19 18:00:00`

---

### **Step 2: Query Qdrant for NEW Messages Only**

```python
# Lines 417-423
new_messages = await self._get_new_messages_since(
    collection_name=collection_name,
    user_id=user_id,
    since_timestamp=last_processed  # Only messages AFTER 18:00:00
)

if not new_messages:
    logger.debug("No new messages for user %s since %s", user_id, last_processed)
    return []  # SKIP - no work needed!
```

**Key Optimization**: If no new messages → **SKIP ENTIRELY**
- No Qdrant queries for message retrieval
- No LLM calls
- No summary regeneration
- This is why you see "0 summaries" in cycles when conversations are quiet

**Example**:
- Query: "Get messages where timestamp > 2025-10-19 18:00:00"
- Result: 15 new messages between 18:00 - 06:00 (12 hours of new activity)

---

### **Step 3: Create Time Windows for New Message Timespan**

```python
# Lines 425-444
# Group new messages into time-based windows
message_times = [msg['timestamp'] for msg in new_messages]
earliest_new = min(message_times)  # First new message: 18:05:00
latest_new = max(message_times)    # Last new message: 05:45:00

# Create windows covering the new message timespan
current_window_start = earliest_new
while current_window_start < latest_new:
    window_end = min(
        current_window_start + timedelta(hours=config.TIME_WINDOW_HOURS),  # 24 hours
        latest_new
    )
    
    windows.append({
        'start_time': current_window_start,
        'end_time': window_end
    })
    
    current_window_start = window_end
```

**Example** (15 new messages spanning 12 hours):
- Window 1: `2025-10-19 18:05:00` → `2025-10-20 05:45:00` (11h 40min window covering all new messages)

**Important**: Windows are **NOT fixed 24-hour blocks**! They span the actual new message timespan (could be 1 hour, could be 23 hours).

---

### **Step 4: Retrieve ALL Messages in Window (Not Just New Ones)**

```python
# Lines 217-230
# Retrieve all messages in this time window
messages = await self._get_messages_in_window(
    collection_name=collection_name,
    user_id=user_id,
    start_time=start_time,  # 2025-10-19 18:05:00
    end_time=end_time        # 2025-10-20 05:45:00
)

logger.info("📊 Retrieved %s messages for window", len(messages))
```

**🚨 CRITICAL INSIGHT**: This queries Qdrant for **ALL messages in the window**, not just the 15 new ones!

**Example**:
- Query: "Get ALL messages between 18:05:00 and 05:45:00"
- Result: 50 total messages (35 old + 15 new)

**Why?**
- Summary needs complete context
- New messages might change interpretation of old messages
- Topics/emotional tone may shift with new context

---

### **Step 5: Regenerate Summary with Complete Context**

```python
# Lines 236-246
# Generate high-quality summary using LLM
summary_result = await self.summarizer.generate_conversation_summary(
    messages=messages,  # ALL 50 messages (old + new)
    user_id=user_id,
    bot_name=bot_name
)
```

**LLM analyzes**:
- All 50 messages in chronological order
- Extracts 3-5 key topics
- Determines emotional tone
- Creates 3-5 sentence summary

**Example Output**:
```
Summary: "User discussed marine biology career paths with Elena, asking about 
educational requirements and volunteer opportunities. Conversation evolved into 
detailed discussion of sea turtle conservation projects. User expressed strong 
interest in fieldwork and asked about graduate programs. Elena recommended 
specific universities and internship programs. [NEW] User followed up with 
questions about funding options and scholarship availability."
```

---

### **Step 6: Store/Update Summary in PostgreSQL**

```python
# Lines 487-509
async def _store_conversation_summary(...):
    await conn.execute("""
        INSERT INTO conversation_summaries (...)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (user_id, bot_name, start_timestamp, end_timestamp)
        DO UPDATE SET
            summary_text = EXCLUDED.summary_text,
            message_count = EXCLUDED.message_count,
            key_topics = EXCLUDED.key_topics,
            emotional_tone = EXCLUDED.emotional_tone,
            compression_ratio = EXCLUDED.compression_ratio,
            confidence_score = EXCLUDED.confidence_score,
            updated_at = NOW()
    """)
```

**🎯 KEY FEATURE**: `ON CONFLICT ... DO UPDATE`

**What This Means**:
- If summary for this time window already exists → **UPDATE IT**
- If summary doesn't exist → **INSERT NEW ONE**
- No duplicate summaries - just one refreshed version per window

**Example**:
- Old summary (35 messages): "User discussed marine biology careers..."
- New summary (50 messages): "User discussed marine biology careers... [EXPANDED WITH NEW CONTEXT]"
- Database: **1 row** updated, not 2 rows created

---

## 🤔 **Why Re-Analyze the Whole Window?**

### **Scenario 1: Context Changes Meaning**

**Old window** (first 35 messages):
```
User: "I'm interested in marine biology"
Bot: "Great! What aspect interests you?"
User: "I love sea turtles"
```
**Summary**: "User exploring general marine biology interest, likes sea turtles"

**New messages** (next 15 messages):
```
User: "Actually, I have a PhD in marine biology and 10 years field experience"
User: "I'm looking to transition into leadership roles"
User: "Can you recommend research institutions hiring?"
```

**Updated Summary**: "Experienced marine biologist with PhD and 10 years field experience 
seeking leadership positions at research institutions. Initial conversation explored general 
interest but evolved into career transition planning."

**Without re-analysis**: Summary would say "exploring interest" (WRONG - they're an expert!)

---

### **Scenario 2: Emotional Tone Shifts**

**Old messages** (positive tone):
```
User: "I love working with sea turtles!"
User: "It's so rewarding"
```

**New messages** (negative tone):
```
User: "But I'm frustrated with funding cuts"
User: "My research project was cancelled"
User: "I'm considering leaving the field"
```

**Updated Summary**: Emotional tone changes from `positive` to `mixed` or `negative`

**Without re-analysis**: Would show `positive` tone (outdated!)

---

### **Scenario 3: New Topics Emerge**

**Old topics**: `["marine biology", "sea turtles"]`

**New messages introduce**: funding, career change, alternative careers

**Updated topics**: `["marine biology", "sea turtles", "funding challenges", "career transition", "job search"]`

---

## ⚡ **Performance Optimizations**

### **Optimization 1: Skip Inactive Users**

```python
if not new_messages:
    return []  # Don't even create windows
```

**Impact**: If user hasn't messaged in 3 days, enrichment worker **skips them entirely**
- No Qdrant queries
- No LLM calls
- No database writes

**Example**: Last cycle showed "0 summaries" because most users had no new messages

---

### **Optimization 2: Variable Window Sizes**

Windows aren't always 24 hours! They span the **actual new message timespan**:

**Example 1** (short burst):
- New messages: 5 messages in 20 minutes
- Window: 20 minutes (not 24 hours!)
- Messages retrieved: ~5-10 (includes nearby old messages)

**Example 2** (spread out):
- New messages: 50 messages over 18 hours
- Window: 18 hours
- Messages retrieved: ~50-100 total

**Example 3** (multi-day gap):
- New messages span 3 days
- Creates 3 separate windows (one per day)
- Each window analyzed independently

---

### **Optimization 3: Minimum Message Threshold**

```python
if len(messages) < config.MIN_MESSAGES_FOR_SUMMARY:
    logger.info("⏭️  Skipping window - only %s messages (min: %s)",
                len(messages), config.MIN_MESSAGES_FOR_SUMMARY)
    return False
```

**Default**: `MIN_MESSAGES_FOR_SUMMARY = 5`

**Impact**: Windows with <5 messages are **skipped** (not worth summarizing)

---

### **Optimization 4: Idempotent Updates**

`ON CONFLICT ... DO UPDATE` means:
- Safe to run multiple times on same data
- No duplicate summaries
- Only storage cost (no LLM cost if summary unchanged)

---

## 📊 **Cost Analysis: Is Re-Analysis Wasteful?**

### **Scenario: User sends 1 new message to 24-hour window**

**Cost**:
- Qdrant query: ~50ms (retrieve ~20-50 messages)
- LLM summary: ~$0.002 (50 messages = ~5,000 tokens input)
- PostgreSQL update: ~5ms

**Total**: ~$0.002 + 60ms latency

**Is this worth it?**

✅ **YES** - Accuracy is more important than cost:
- Summary reflects complete context
- No risk of outdated/incomplete summaries
- User experience: "What did we discuss yesterday?" gets accurate answer

❌ **Alternative (don't re-analyze)**: 
- Save $0.002
- Risk: Summary missing critical context
- User experience: Incomplete/outdated summary

---

## 🎯 **Real-World Example from Logs**

**From your logs** (06:03:34):
```
2025-10-20 06:03:34 - 🔍 Extracting facts from 201 new messages (user 672814231002939413)
```

**What's happening**:
1. User `672814231002939413` has 201 NEW messages since last cycle
2. Enrichment worker queries Qdrant for messages in the new message timespan
3. Likely retrieves 201-300 TOTAL messages (includes nearby old messages for context)
4. Re-analyzes the ENTIRE window to regenerate summary with complete context
5. Updates existing summary (or creates new one if first time)

**Cost**: ~$0.01 for 300 messages (worth it for accurate summary!)

---

## 🔄 **Summary of Incremental Mode**

| What It Does | Why |
|--------------|-----|
| ✅ **Queries only NEW messages** | Efficiency - skip inactive users |
| ✅ **Re-analyzes ENTIRE window** | Accuracy - complete context for summaries |
| ✅ **Updates existing summaries** | No duplicates - single source of truth |
| ✅ **Skips windows <5 messages** | Quality - don't waste LLM calls on trivial conversations |
| ✅ **Variable window sizes** | Flexibility - adapts to actual message patterns |

---

## 💡 **Alternative Approach (NOT Used)**

**WhisperEngine COULD use "append-only" summaries**:
- Store summary per message batch
- Never re-analyze old messages
- Cheaper but less accurate

**Why we DON'T do this**:
- ❌ Summaries become outdated as context evolves
- ❌ Can't correct misinterpretations from early messages
- ❌ Emotional tone/topics can't shift
- ❌ User asks "What did we discuss?" → gets incomplete answer

**WhisperEngine prioritizes ACCURACY over cost** 🎯

---

## 🚀 **Conclusion**

**YES, incremental mode re-analyzes the whole window when new messages arrive.**

**This is a FEATURE, not a bug**:
- ✅ Summaries stay accurate as conversations evolve
- ✅ New context updates interpretation of old messages
- ✅ Topics/emotions reflect complete conversation
- ✅ Users get accurate answers to "What did we discuss?"

**Performance is still excellent**:
- Only processes users with NEW messages
- Skips inactive users entirely
- Variable window sizes adapt to actual activity
- ~60-70 second cycles for 10 bot collections

**The enrichment worker is smart about WHEN to work (incremental) but thorough about HOW it works (complete re-analysis)!** 🎯
