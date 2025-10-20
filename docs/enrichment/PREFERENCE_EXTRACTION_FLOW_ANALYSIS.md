# User Preference Extraction Flow - Complete Analysis
**Date**: October 19, 2025  
**System**: WhisperEngine Multi-Bot Platform  
**Status**: Runtime extraction DISABLED by default, Enrichment worker ACTIVE

---

## 🎯 **Executive Summary**

WhisperEngine has **TWO preference extraction systems** (similar to fact extraction):
1. **Runtime Preference Extraction** (Real-time) - ⛔ **DISABLED by default**
2. **Enrichment Worker Preference Extraction** (Background) - ✅ **ACTIVE**

Both write to the **SAME PostgreSQL storage** (`universal_users.preferences` JSONB column).

---

## 🔄 **Complete Preference Flow**

### **WRITE PATH (2 Sources → 1 Destination)**

```
┌─────────────────────────────────────────────────────────────────┐
│              PREFERENCE EXTRACTION SOURCES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📨 RUNTIME (Real-time)           🔄 ENRICHMENT (Async)        │
│  ─────────────────────           ───────────────────────        │
│  • During message processing     • Every 5 minutes              │
│  • REGEX PATTERNS ONLY          • LLM ANALYSIS                 │
│  • 4 types: name, timezone,     • UNLIMITED preference types   │
│    location, language           • Conversation context         │
│  • Explicit statements only     • Implicit patterns            │
│  • Adds 100-200ms latency       • No user-facing latency       │
│  • ⛔ DISABLED by default         • ✅ ACTIVE by default         │
│                                                                 │
│         ↓                                  ↓                    │
│  ┌──────────────────────┐    ┌──────────────────────────────┐ │
│  │ message_processor.py │    │ enrichment/worker.py         │ │
│  │ _extract_and_store_  │    │ _process_preference_         │ │
│  │ user_preferences()   │    │ extraction()                 │ │
│  └──────────────────────┘    └──────────────────────────────┘ │
│         ↓                                  ↓                    │
│         └────────────────┬────────────────┘                    │
│                          ↓                                      │
│      ┌──────────────────────────────────────────┐              │
│      │  semantic_router.py                      │              │
│      │  store_user_preference()                 │              │
│      └──────────────────────────────────────────┘              │
│                          ↓                                      │
│      ┌──────────────────────────────────────────┐              │
│      │  PostgreSQL: universal_users.preferences │              │
│      │  (JSONB column - deterministic storage)  │              │
│      └──────────────────────────────────────────┘              │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BOTS RETRIEVE PREFERENCES FROM SAME TABLE               │  │
│  │  (Elena, Marcus, Jake all query the same JSONB)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 **System 1: Runtime Preference Extraction (DISABLED)**

### **Configuration**
```bash
# .env.template + all bot .env files
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false  # Default: disabled
```

### **Implementation**
```python
# src/core/message_processor.py - Line 838
if os.getenv('ENABLE_RUNTIME_PREFERENCE_EXTRACTION', 'false').lower() == 'true':
    preference_stored = await self._extract_and_store_user_preferences(
        message_context
    )
else:
    logger.debug("⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled (enrichment worker handles preference extraction)")
```

### **Method: `_extract_and_store_user_preferences()` (Lines 6107-6200+)**

**Supported Preference Types (REGEX-BASED):**
1. **Preferred Name** (7 patterns)
   - "My name is Mark"
   - "Call me Mark"
   - "I prefer to be called Mark"
   - "I go by Mark"
   - "You can call me Mark"
   - "Just call me Mark"
   - "I'm Mark"

2. **Timezone** (3 patterns)
   - "I'm in EST", "I'm in Pacific time"
   - "My timezone is EST"
   - "I live in EST", "I'm on PST"

3. **Location** (3 patterns)
   - "I live in Seattle", "I'm from Chicago"
   - "I'm in New York", "I'm located in Boston"
   - "My location is Seattle"

4. **Language** (3 patterns)
   - "I speak Spanish", "I prefer French"
   - "My language is German"
   - "I use Italian"

**Limitations:**
- ❌ **Hardcoded patterns**: Only detects these 4 preference types
- ❌ **Regex-based**: Brittle, misses creative phrasing
- ❌ **No context**: Single message analysis only
- ❌ **Explicit only**: Cannot detect implied preferences
- ❌ **Performance**: Adds 100-200ms per message
- ❌ **No evolution tracking**: Doesn't handle preference changes

**Why It's Disabled:**
- Enrichment worker provides superior quality with LLM analysis
- No user-facing latency (background processing)
- Unlimited preference types (not hardcoded)
- Conversation context for better accuracy

---

## 🚀 **System 2: Enrichment Worker Preference Extraction (ACTIVE)**

### **Implementation**
```python
# src/enrichment/worker.py - Line 135
preferences_extracted = await self._process_preference_extraction(
    collection_name=collection_name,
    bot_name=bot_name
)
```

### **Method: `_process_preference_extraction()` (Lines 1116-1250+)**

**How It Works:**

1. **Incremental Processing**
   - Tracks last extraction timestamp per user
   - Only processes NEW messages since last run
   - Avoids re-processing old conversations

2. **LLM-Powered Analysis**
   - Uses conversation context (not single message)
   - Detects explicit AND implicit preferences
   - Handles Q&A patterns (Bot asks → User confirms)
   - Tracks preference evolution over time

3. **Rich Preference Types (UNLIMITED)**
   - `preferred_name`: What to call the user
   - `pronouns`: he/him, she/her, they/them, etc.
   - `timezone`: EST, PST, GMT+8, etc.
   - `location`: City, state, country
   - `communication_style`: brief, detailed, casual, formal, technical
   - `response_length`: short, medium, long
   - `language`: Preferred language
   - `topic_preferences`: Topics to focus on or avoid
   - `formality_level`: casual, professional, friendly, formal
   - **ANY OTHER TYPE**: LLM can extract new preference types dynamically

4. **Confidence Scoring**
   - **Explicit statements**: 0.9-1.0 confidence
   - **Implied/inferred**: 0.6-0.8 confidence
   - **Reasoning included**: Why preference was extracted
   - **Conversation context**: Shows source message(s)

### **LLM Prompt Strategy**

```python
# Lines 1262-1330
prompt = f"""Analyze this conversation and extract user preferences.

Conversation between user and {bot_name}:
{conversation_text}

Extract ANY of these preference types that are clearly stated or strongly implied:

**Preference Types**:
1. preferred_name, 2. pronouns, 3. timezone, 4. location, 
5. communication_style, 6. response_length, 7. language,
8. topic_preferences, 9. formality_level

**CRITICAL RULES**:
- ONLY extract if clearly stated OR strongly implied from repeated patterns
- Mark explicit statements with confidence 0.9-1.0
- Mark implied/inferred preferences with confidence 0.6-0.8
- Include conversation context showing where preference came from
- Detect preference CHANGES (user updated their preference)
- Handle Q&A patterns (Bot: "What should I call you?" User: "Mark is fine")

Return JSON with preferences array...
"""
```

### **Storage Method: `_store_preferences_in_postgres()` (Lines 1396-1450+)**

**Storage Format (JSONB):**
```json
{
  "preferred_name": {
    "value": "Mark",
    "confidence": 0.95,
    "updated_at": "2025-10-19T02:30:00",
    "metadata": {
      "extraction_method": "enrichment_worker",
      "reasoning": "User explicitly stated 'call me Mark' when asked",
      "conversation_context": "Bot: 'What should I call you?' User: 'Mark is fine'",
      "is_explicit": true,
      "is_preference_change": false,
      "bot_name": "elena"
    }
  },
  "communication_style": {
    "value": "brief",
    "confidence": 0.75,
    "updated_at": "2025-10-19T02:35:00",
    "metadata": {
      "extraction_method": "enrichment_worker",
      "reasoning": "User repeatedly asks for shorter responses and says 'keep it brief'",
      "conversation_context": "User: 'Can you keep answers shorter?', User: 'Just the key points please'",
      "is_explicit": false,
      "is_preference_change": false,
      "bot_name": "elena"
    }
  }
}
```

**Storage Advantages:**
- ✅ **Deterministic retrieval**: <1ms JSONB query (no vector search)
- ✅ **Unified schema**: Same format as runtime extraction
- ✅ **Rich metadata**: Extraction method, reasoning, context, confidence
- ✅ **Evolution tracking**: Timestamps + change detection
- ✅ **Bot visibility**: All bots see same preferences

---

## 📖 **READ PATH (Preference Retrieval)**

### **Storage Location**
```sql
-- PostgreSQL table: universal_users
-- Column: preferences (JSONB)

SELECT preferences 
FROM universal_users 
WHERE universal_id = 'user_discord_id';
```

### **Retrieval Method**
```python
# src/knowledge/semantic_router.py - Line 846
async def get_all_user_preferences(
    self,
    user_id: str
) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve all user preferences from PostgreSQL.
    
    Returns:
        Dict mapping preference_type -> preference_data
        Example:
        {
          'preferred_name': {
            'value': 'Mark',
            'confidence': 0.95,
            'updated_at': '2025-10-19T...',
            'metadata': {...}
          },
          'timezone': {
            'value': 'PST',
            'confidence': 0.90,
            ...
          }
        }
    """
```

### **Usage in Conversation**
Preferences are typically retrieved during:
1. **Prompt building**: Include user's preferred name, communication style
2. **Response formatting**: Adjust length/detail based on preferences
3. **Character adaptation**: Tailor bot behavior to user preferences

---

## 🔍 **Verification & Debugging**

### **Check Enrichment Worker Logs**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep "PREFERENCE"
```

**Expected Output:**
```
2025-10-20 02:45:21 - 👤 Processing preference extraction for elena...
2025-10-20 02:45:25 - 🔍 Extracting preferences from 15 new messages (user 123456789)
2025-10-20 02:45:28 - ✅ ENRICHMENT PREFERENCE: Stored 'preferred_name'='Mark' (confidence=0.95)
2025-10-20 02:45:28 - ✅ ENRICHMENT PREFERENCE: Stored 'communication_style'='brief' (confidence=0.75)
2025-10-20 02:45:28 - ✅ Extracted and stored 2 preferences for user 123456789
2025-10-20 02:45:30 - ✅ Extracted 8 total preferences for elena
```

### **Check PostgreSQL Directly**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres \
  psql -U whisperengine -d whisperengine -c \
  "SELECT universal_id, preferences 
   FROM universal_users 
   WHERE preferences IS NOT NULL 
   LIMIT 5;"
```

### **Check Specific User's Preferences**
```sql
SELECT 
    universal_id,
    jsonb_pretty(preferences) as preferences
FROM universal_users
WHERE universal_id = 'YOUR_DISCORD_USER_ID';
```

**Example Output:**
```json
{
  "preferred_name": {
    "value": "Mark",
    "confidence": 0.95,
    "updated_at": "2025-10-19T02:30:00",
    "metadata": {
      "extraction_method": "enrichment_worker",
      "reasoning": "User explicitly stated...",
      "is_explicit": true
    }
  },
  "timezone": {
    "value": "PST",
    "confidence": 0.90,
    "updated_at": "2025-10-19T02:32:00",
    "metadata": {
      "extraction_method": "enrichment_worker",
      "reasoning": "User mentioned living in California...",
      "is_explicit": false
    }
  }
}
```

---

## 📊 **Runtime vs Enrichment Comparison**

| Feature | Runtime Extraction | Enrichment Worker |
|---------|-------------------|-------------------|
| **Status** | ⛔ Disabled by default | ✅ Active |
| **Method** | Regex patterns | LLM analysis |
| **Preference Types** | 4 hardcoded types | Unlimited (dynamic) |
| **Context** | Single message | Conversation window |
| **Detection** | Explicit only | Explicit + Implicit |
| **Latency** | +100-200ms per message | 0ms (background) |
| **Quality** | Basic | Superior |
| **Evolution Tracking** | ❌ No | ✅ Yes |
| **Confidence Scores** | ✅ Yes | ✅ Yes (with reasoning) |
| **Q&A Patterns** | ❌ No | ✅ Yes |

---

## 🎯 **Key Takeaways**

1. **Runtime Extraction is DISABLED** - `ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false` in all `.env` files
2. **Enrichment Worker is ACTIVE** - Runs every 5 minutes with LLM-powered analysis
3. **Same Storage** - Both write to `universal_users.preferences` JSONB column
4. **Unified Retrieval** - All bots query the same PostgreSQL table
5. **Superior Quality** - Enrichment worker provides:
   - Unlimited preference types (not hardcoded)
   - Conversation context (not single message)
   - Implicit preference detection (not just explicit)
   - Preference evolution tracking
   - Zero user-facing latency

6. **Historical Data** - Preferences extracted before Oct 19 (runtime) are still visible alongside new enrichment preferences

---

## 🚀 **What's Next?**

The enrichment worker will continue to:
1. **Extract preferences** from conversations every 5 minutes
2. **Store in PostgreSQL** using the same schema as runtime extraction
3. **Enable bots** to adapt to user communication styles
4. **Track evolution** of preferences over time
5. **Provide context** showing where preferences came from

**Your preferences will grow organically** as both systems contribute to the unified knowledge base! 🎯

---

**Bottom Line**: Preference extraction is now **primarily handled by the enrichment worker** (LLM-powered, background processing) while **runtime extraction is disabled** (regex-based, performance overhead). Both write to the **same PostgreSQL storage**, giving all bots a unified view of user preferences! 🚀
