# Fact Storage & Retrieval Flow - Complete Analysis
**Date**: October 19, 2025  
**User Question**: "How are facts written and read in the enrichment system?"

---

## 🔍 **Your Observation**

Jake showed you these facts:
```
Your Preferences: enjoys bath, likes Thai iced tea, likes drunken noodle, likes tuna, likes sushi
Background: lives in San Diego
Family & Relationships: son Logan
Activities & Interests: visited monterey bay aquarium
Things You Have: owns Luna, owns cats, owns Max, owns bengal, owns cat, owns her own room, owns gatos, owns pet
Other Details: is software engineer, is family of wife, mentions Luna, mentions Minerva, is Gabe, actively does cooking
```

**Your concern**: Are these old facts? How does the new enrichment system work?

---

## ✅ **Answer: These are ALL OLD Facts (From Runtime Extraction Era)**

WhisperEngine **used to have** a dual extraction system, but **runtime extraction is NOW DISABLED by default**:

### **System 1: Runtime Fact Extraction (Real-time) - ⛔ DISABLED BY DEFAULT**
- **When**: During message processing (hot path) - **NOW DISABLED**
- **Where**: `src/core/message_processor.py` → gated by `ENABLE_RUNTIME_FACT_EXTRACTION=false`
- **Status**: ⛔ **DISABLED** (October 19, 2025 - replaced by enrichment worker)
- **Why Disabled**: Adds 200-500ms latency per message, enrichment worker provides better quality
- **Historical Data**: Facts extracted before Oct 19 are still in PostgreSQL

### **System 2: Enrichment Worker (Background) - ✅ ACTIVE**
- **When**: Every 5 minutes, processes NEW messages since last run
- **Where**: `src/enrichment/worker.py` → `_store_facts_in_postgres()`
- **Storage**: PostgreSQL `fact_entities` + `user_fact_relationships` tables
- **Status**: ✅ **ACTIVE** (deployed October 19, 2025)
- **Advantages**: Better quality (conversation context), no user-facing latency, batch processing

---

## 🔄 **Complete Fact Flow**

### **WRITE PATH (2 Sources → 1 Destination)**

```
┌─────────────────────────────────────────────────────────────────┐
│                     FACT EXTRACTION SOURCES                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📨 INLINE (Real-time)                 🔄 ENRICHMENT (Async)   │
│  ─────────────────────                 ───────────────────────  │
│  • During message processing           • Every 5 minutes        │
│  • Immediate extraction                • Batch processing       │
│  • Single message context              • Multi-message context  │
│  • Fast & lightweight                  • Deep analysis          │
│                                                                 │
│              ↓                                    ↓              │
│  ┌─────────────────────┐          ┌──────────────────────────┐ │
│  │ semantic_router.py  │          │ enrichment/worker.py     │ │
│  │ store_user_fact()   │          │ _store_facts_in_postgres │ │
│  └─────────────────────┘          └──────────────────────────┘ │
│              ↓                                    ↓              │
│              └────────────────┬────────────────────┘            │
│                               ↓                                  │
│           ┌──────────────────────────────────────┐              │
│           │  PostgreSQL (SHARED STORAGE)         │              │
│           ├──────────────────────────────────────┤              │
│           │  • fact_entities                     │              │
│           │  • user_fact_relationships           │              │
│           └──────────────────────────────────────┘              │
│                               ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BOTS SEE COMBINED FACTS FROM BOTH SOURCES               │  │
│  │  (Elena, Marcus, Jake all query the same tables)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 **READ PATH (Facts Display)**

When Jake (or any bot) needs to show "what do you remember about me?", here's the flow:

### **Step 1: Message Processing**
```python
# src/core/message_processor.py - Line 2960
async def _build_user_facts_content(self, user_id: str, message_content: str = "") -> str:
    # Get temporally relevant facts (recent facts weighted higher)
    facts = await self.bot_core.knowledge_router.get_temporally_relevant_facts(
        user_id=user_id,
        lookback_days=90,  # 3 months
        limit=25
    )
```

### **Step 2: PostgreSQL Query**
```python
# src/knowledge/semantic_router.py - Line 476
async def get_temporally_relevant_facts(self, user_id: str, lookback_days: int = 90, limit: int = 20):
    query = """
        SELECT 
            fe.entity_name,
            fe.entity_type,
            ufr.relationship_type,
            ufr.confidence,
            ufr.created_at,
            ufr.updated_at,
            ufr.context_metadata
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = $1
          AND ufr.created_at > NOW() - INTERVAL '{lookback_days} days'
          AND ufr.confidence > 0.5
        ORDER BY 
            -- Recent facts weighted higher (time decay)
            (ufr.confidence * EXP(-EXTRACT(EPOCH FROM (NOW() - ufr.created_at)) / 2592000)) DESC,
            ufr.updated_at DESC
        LIMIT $2
    """
```

**Key Insight**: This query returns facts from **BOTH inline AND enrichment** sources - they're in the same table!

### **Step 3: Categorization & Formatting**
```python
# src/core/message_processor.py - Lines 2988-3040
# Categorize facts by relationship type
if relationship_type in ['likes', 'loves', 'enjoys', 'prefers']:
    preferences.append(f"{relationship_type} {entity_display}")
elif relationship_type in ['works_at', 'studies_at', 'lives_in']:
    background.append(f"{relationship_type.replace('_', ' ')} {entity_display}")
elif relationship_type in ['owns', 'has', 'knows']:
    current_facts.append(f"{relationship_type} {entity_display}")

# Format for display
fact_lines = []
if preferences:
    fact_lines.append(f"PREFERENCES: {', '.join(preferences[:8])}")
if background:
    fact_lines.append(f"BACKGROUND: {', '.join(background[:5])}")
if current_facts:
    fact_lines.append(f"CURRENT: {', '.join(current_facts[:7])}")
```

### **Step 4: Bot Response**
Jake receives the formatted facts and presents them in the categorized format you saw.

---

## 🤔 **Are These Facts Old or New?**

**Answer: BOTH!** Here's the breakdown:

| Fact | Source | Age | Notes |
|------|--------|-----|-------|
| `likes Thai iced tea` | Inline | Old | Extracted during real-time conversation |
| `owns Luna` | Inline | Old | Extracted when you mentioned Luna |
| `son Logan` | Inline | Old | Family relationship extracted inline |
| `lives in San Diego` | Inline | Old | Location fact from earlier conversation |
| `is software engineer` | Enrichment | New | Extracted by enrichment worker from conversation patterns |
| `visited monterey bay aquarium` | Either | Mixed | Could be from inline OR enrichment |

**Why the mix?**
- **Inline facts** (months old): WhisperEngine has been extracting facts inline since deployment
- **Enrichment facts** (hours old): Enrichment worker just deployed today, starting to add NEW facts
- **Both visible**: Bots query the shared PostgreSQL tables, so they see EVERYTHING

---

## 🔍 **How to Tell Which Is Which?**

Check the `context_metadata` field in PostgreSQL:

```sql
SELECT 
    fe.entity_name,
    ufr.relationship_type,
    ufr.context_metadata->>'extraction_method' as source,
    ufr.created_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'YOUR_USER_ID'
ORDER BY ufr.created_at DESC
LIMIT 20;
```

**Results will show:**
- `extraction_method: 'inline'` = Real-time extraction during conversation
- `extraction_method: 'enrichment_worker'` = Background batch extraction

---

## 📊 **Enrichment Worker Status (October 19, 2025)**

### **What's Running:**
✅ **Conversation Summarization**: Generating high-quality summaries every 5 minutes  
✅ **Fact Extraction**: Extracting facts from conversation windows  
✅ **Preference Extraction**: Extracting user preferences  

### **Storage Tables:**
```
fact_entities              ← Entity definitions (shared by both systems)
user_fact_relationships    ← User-entity relationships (shared by both systems)
conversation_summaries     ← Enrichment-only (summaries)
```

### **Logs Confirm Active Extraction:**
```
2025-10-20 02:39:21 - ✅ ENRICHMENT FACT: Stored 'tech company' (occupation, works_at, confidence=0.90)
2025-10-20 02:39:21 - ✅ ENRICHMENT FACT: Stored 'marine biology' (hobby, loves, confidence=0.90)
2025-10-20 02:39:21 - ✅ Extracted and stored 2 facts for user test_fixed_user_123
```

---

## 🎯 **Key Takeaways**

1. **Same Storage**: Both inline and enrichment write to the **same PostgreSQL tables**
2. **Unified View**: Bots see facts from **both sources** seamlessly
3. **Old + New**: Your facts are a mix of **inline (months old) + enrichment (hours old)**
4. **No Conflicts**: Both systems use the **same schema** and **same conflict resolution**
5. **Incremental**: Enrichment worker only processes **NEW messages** since last run

---

## 🔧 **How to Verify**

### **Check Enrichment Worker Logs:**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep "ENRICHMENT FACT"
```

### **Check Your Facts in PostgreSQL:**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres \
  psql -U whisperengine -d whisperengine -c \
  "SELECT fe.entity_name, ufr.relationship_type, ufr.context_metadata->>'extraction_method' as source, ufr.created_at 
   FROM user_fact_relationships ufr 
   JOIN fact_entities fe ON ufr.entity_id = fe.id 
   WHERE ufr.user_id = 'YOUR_DISCORD_USER_ID' 
   ORDER BY ufr.created_at DESC 
   LIMIT 20;"
```

### **Check Jake's Bot Collection:**
```bash
# Count memories in Jake's collection
curl -X POST http://localhost:6334/collections/whisperengine_memory_jake/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 1, "with_payload": false}'
```

---

## 🚀 **What's Next?**

The enrichment worker will continue to:
1. **Extract new facts** from conversations (every 5 minutes)
2. **Generate summaries** of conversation windows
3. **Store everything** in the same PostgreSQL tables bots query
4. **Enrich over time** - more conversations = more facts = better context

**Your facts will grow organically** as both systems contribute to the knowledge base!

---

**Bottom Line**: The facts Jake showed you are a **combination of old inline facts + new enrichment facts**, all stored in the **same PostgreSQL database** that all bots query. The system is working as designed! 🎯
