# Runtime Fact Extraction Deprecation

## 🎯 **Decision: Disable Runtime Fact Extraction by Default**

**Date**: October 19, 2025  
**Feature Flag**: `ENABLE_RUNTIME_FACT_EXTRACTION=false` (default)

---

## 📊 **Context**

WhisperEngine previously extracted facts during message processing using an LLM call:
- **Location**: `src/core/message_processor.py` - `_extract_and_store_knowledge()`
- **Model**: GPT-4o-mini or GPT-3.5-turbo
- **Latency Impact**: 200-500ms per message
- **Quality**: Single-message context only

---

## ✅ **Why Disable Runtime Extraction?**

### **1. Performance: 200-500ms Faster Responses**
- **Before**: Every message triggers LLM fact extraction call
- **After**: No extra LLM call during message processing
- **Result**: Users get responses 200-500ms faster (significant UX improvement)

### **2. Better Quality: Enrichment Worker Superiority**
| Feature | Runtime Extraction | Enrichment Worker |
|---------|-------------------|-------------------|
| **Context** | Single message | 5-10 message conversation window |
| **Model** | GPT-3.5/4o-mini | Claude Sonnet 4.5 |
| **Analysis Depth** | Immediate parsing | Deep conversation analysis |
| **Conflict Detection** | Basic opposing relationships | Cross-message contradictions |
| **Knowledge Graph** | No relationship building | Auto-discover entity connections |
| **Pattern Detection** | No patterns | Multi-message behavioral patterns |

### **3. Simpler Debugging**
- **Single extraction path**: Only enrichment worker logs to check
- **No race conditions**: Runtime and enrichment can't conflict
- **Clearer architecture**: Separation of concerns (runtime = response, async = intelligence)

### **4. Non-Breaking Change**
- **Feature flag**: Can re-enable for testing or specific use cases
- **Same storage schema**: Both use `fact_entities` + `user_fact_relationships`
- **Backwards compatible**: Existing facts remain unchanged

---

## ⚠️ **Tradeoff: Delayed Fact Availability**

### **Immediate Impact Example**
```
❌ BEFORE (Runtime extraction enabled):
User: "My name is Alex"
Bot: "Nice to meet you, Alex!" [uses fact immediately]

✅ AFTER (Enrichment worker only):
User: "My name is Alex"
Bot: "Nice to meet you!" [fact stored in 5-15 minutes]
[Later conversation]
Bot: "Hey Alex, how's it going?" [fact available after enrichment]
```

### **When This Matters**
- **High priority**: Name extraction, immediate preferences
- **Medium priority**: Personal facts mentioned in current conversation
- **Low priority**: Historical facts, patterns over multiple conversations

### **Mitigation Strategy**
For critical immediate facts, we have alternatives:
1. **Discord Display Name**: Already available in real-time from platform
2. **CDL Character System**: Pre-configured character knowledge
3. **Vector Memory**: Conversation history provides context
4. **Optional Re-Enable**: Set `ENABLE_RUNTIME_FACT_EXTRACTION=true` for specific bots

---

## 🏗️ **Architecture After Change**

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE PROCESSING FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User sends message                                          │
│  2. Security validation                                         │
│  3. Retrieve vector memories                                    │
│  4. Query PostgreSQL facts (temporal filtering)                 │
│  5. Build conversation context                                  │
│  6. LLM generates response                   [NO FACT LLM CALL] │
│  7. Store in vector memory                                      │
│  8. ⏭️  SKIP runtime fact extraction                            │
│  9. Return response to user                  [200-500ms faster] │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              ENRICHMENT WORKER (Async Background)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Every 5 minutes:                                               │
│  1. Fetch conversation windows (5-10 messages)                  │
│  2. Generate conversation summaries (Claude Sonnet 4.5)         │
│  3. Extract facts from conversation holistically                │
│  4. Detect cross-message conflicts                              │
│  5. Build knowledge graph relationships                         │
│  6. Store in PostgreSQL (fact_entities + user_fact_relationships)│
│                                                                  │
│  Result: Higher quality facts, no user-facing latency           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 **Implementation Details**

### **Code Changes**
**File**: `src/core/message_processor.py` (line ~817)

```python
# BEFORE:
knowledge_stored = await self._extract_and_store_knowledge(
    message_context, ai_components, extract_from='user'
)

# AFTER:
knowledge_stored = False
if os.getenv('ENABLE_RUNTIME_FACT_EXTRACTION', 'false').lower() == 'true':
    knowledge_stored = await self._extract_and_store_knowledge(
        message_context, ai_components, extract_from='user'
    )
else:
    logger.debug("⏭️ RUNTIME FACT EXTRACTION: Disabled (enrichment worker handles fact extraction)")
```

### **Environment Variable**
**File**: `.env.template` and all `.env.{bot_name}` files

```bash
# Runtime Fact Extraction (optional - default: false)
# Controls whether facts are extracted during message processing (adds 200-500ms latency)
# RECOMMENDED: false (enrichment worker handles fact extraction asynchronously with better quality)
# Set to 'true' only for testing or if you need immediate fact capture
ENABLE_RUNTIME_FACT_EXTRACTION=false
```

---

## 📈 **Expected Performance Improvements**

### **Per-Message Latency Reduction**
- **Typical runtime extraction**: 200-500ms (LLM call + parsing + storage)
- **Removed from critical path**: 100% latency reduction for this step
- **Overall message processing**: ~15-25% faster response time

### **Cost Reduction**
- **Before**: 2 LLM calls per message (1 chat + 1 fact extraction)
- **After**: 1 LLM call per message (chat only)
- **Savings**: ~50% reduction in LLM API costs for message processing

### **Enrichment Worker Quality**
- **Better model**: Claude Sonnet 4.5 vs GPT-3.5/4o-mini
- **Better context**: 5-10 messages vs single message
- **Better features**: Knowledge graphs + conflict detection + pattern analysis

---

## 🧪 **Testing Strategy**

### **Verify Runtime Extraction is Disabled**
```bash
# Check logs for absence of runtime fact extraction
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot | grep "LLM FACT EXTRACTION"
# Should see: "⏭️ RUNTIME FACT EXTRACTION: Disabled"

# Verify enrichment worker is running
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep "ENRICHMENT FACT"
# Should see: "✅ ENRICHMENT FACT EXTRACTION: Processing conversation windows"
```

### **Measure Performance Improvement**
```bash
# Before change: Average response time with runtime extraction
# After change: Average response time without runtime extraction
# Compare: InfluxDB performance metrics

# Query InfluxDB for average message_processing duration
# Expected: 15-25% reduction in processing_time_ms
```

### **Validate Fact Quality**
```sql
-- Check fact extraction sources
SELECT 
    extraction_method,
    COUNT(*) as fact_count,
    AVG(confidence) as avg_confidence
FROM fact_entities
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY extraction_method;

-- Expected results:
-- extraction_method='enrichment_worker': Higher count, higher confidence
-- extraction_method='runtime': Zero count (disabled)
```

---

## 🔄 **Rollback Plan**

If enrichment worker quality is insufficient or delays are unacceptable:

```bash
# Re-enable runtime fact extraction
# Edit .env.{bot_name} files:
ENABLE_RUNTIME_FACT_EXTRACTION=true

# Restart affected bots
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart elena-bot marcus-bot

# Verify runtime extraction is active
docker logs elena-bot | grep "✅ LLM FACT EXTRACTION: Stored"
```

---

## 📋 **Related Documentation**

- **Enrichment Worker Implementation**: `src/enrichment/README.md`
- **Fact Storage Schema**: `docs/architecture/TEMPORAL_FACT_CONFLICT_RESOLUTION.md`
- **Performance Optimization**: `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md`
- **CDL Character System**: `docs/architecture/CHARACTER_ARCHETYPES.md`

---

## ✅ **Conclusion**

Disabling runtime fact extraction is the **correct architectural decision** for WhisperEngine:

1. ✅ **Performance**: 200-500ms faster responses (critical for UX)
2. ✅ **Quality**: Claude Sonnet 4.5 + conversation context > GPT-3.5 + single message
3. ✅ **Cost**: 50% reduction in LLM API calls during message processing
4. ✅ **Architecture**: Clean separation (runtime = response, async = intelligence)
5. ✅ **Flexibility**: Feature flag allows testing both approaches

The 5-15 minute delay for fact availability is an **acceptable tradeoff** for the significant performance and quality improvements.
