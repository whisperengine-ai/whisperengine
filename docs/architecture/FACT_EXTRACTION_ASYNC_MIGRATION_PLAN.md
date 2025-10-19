# Fact Extraction → Async Enrichment Migration Plan

## 🎯 CRITICAL DISCOVERY

**User insight confirmed**: Fact extraction happens **AFTER response generation** (Phase 9b, line 817), meaning:
- Facts extracted from current message don't affect current response
- Facts are used for FUTURE conversations only
- Message is already stored in Qdrant/PostgreSQL before extraction
- **Perfect candidate for async enrichment worker!**

---

## 📊 CURRENT INLINE FACT EXTRACTION FLOW

### Location
`src/core/message_processor.py` - Phase 9b (lines 817-819)

### Execution Order
```python
# Phase 7: Generate response (LLM call)
response = await self._generate_response(...)

# Phase 8: Validate response
response = await self._validate_and_sanitize_response(...)

# Phase 9: Store conversation in Qdrant
memory_stored = await self._store_conversation_memory(...)

# Phase 9b: 👉 EXTRACT FACTS (runs AFTER response) 👈
knowledge_stored = await self._extract_and_store_knowledge(
    message_context, ai_components, extract_from='user'
)

# Phase 9c: Extract preferences
preference_stored = await self._extract_and_store_user_preferences(...)

# Return response to user
return ProcessingResult(response=response, ...)
```

### What It Does
1. **Calls LLM** for fact extraction (gpt-3.5-turbo by default)
2. **Extracts structured facts** from user message
3. **Stores in PostgreSQL** `user_facts` and `user_fact_relationships` tables
4. **Uses for NEXT conversation** (not current one)

### Performance Impact
- **Adds 200-500ms** to message processing (LLM call in critical path)
- **Blocks response** until facts extracted
- **User waits** for extraction even though it doesn't affect their response

---

## ✅ WHY ASYNC MIGRATION MAKES SENSE

### Facts Are Already in Memory
- ✅ Message stored in Qdrant (Phase 9)
- ✅ User message content available in `content` field
- ✅ Bot response available in `content` field  
- ✅ RoBERTa emotion data already stored
- ✅ Metadata includes user_id, timestamp, etc.

### Facts Don't Affect Current Response
- ❌ **Not used in Phase 7** (response generation) - that's BEFORE extraction
- ✅ **Used in Phase 3** (memory retrieval) - but for NEXT conversation
- ✅ **Perfect async candidate** - extract later, use later

### Performance Benefits
- 🚀 **Remove 200-500ms** from critical response path
- 🚀 **Faster user responses** (no LLM fact extraction blocking)
- 🚀 **Same result** - facts still extracted, just async
- 🚀 **Better scalability** - enrichment worker handles burst loads

---

## 🏗️ MIGRATION IMPLEMENTATION

### Phase 1: Add Fact Extraction to Enrichment Worker

**File**: `src/enrichment/worker.py`

**New Method**:
```python
async def _process_fact_extraction(
    self,
    collection_name: str,
    bot_name: str
) -> int:
    """Extract facts from recent conversations"""
    logger.info("🔍 Processing fact extraction for %s...", bot_name)
    
    # Get users with recent conversations
    users = await self._get_users_in_collection(collection_name)
    
    facts_extracted = 0
    
    for user_id in users:
        try:
            # Check what messages already have facts extracted
            last_fact_extraction = await self._get_last_fact_extraction_timestamp(
                user_id=user_id,
                bot_name=bot_name
            )
            
            # Get messages since last extraction
            recent_messages = await self._get_messages_since_timestamp(
                collection_name=collection_name,
                user_id=user_id,
                since_timestamp=last_fact_extraction
            )
            
            if not recent_messages:
                continue
            
            # Extract facts from each user message
            for message in recent_messages:
                if message.get('memory_type') == 'user_message':
                    facts = await self._extract_facts_from_message(
                        message_content=message['content'],
                        user_id=user_id,
                        bot_name=bot_name
                    )
                    
                    if facts:
                        await self._store_facts_in_postgres(
                            user_id=user_id,
                            bot_name=bot_name,
                            facts=facts
                        )
                        facts_extracted += len(facts)
            
            logger.debug("Extracted %s facts for user %s", facts_extracted, user_id)
            
        except Exception as e:
            logger.error("Failed to extract facts for user %s: %s", user_id, e)
    
    return facts_extracted
```

**Helper Methods**:
```python
async def _extract_facts_from_message(
    self,
    message_content: str,
    user_id: str,
    bot_name: str
) -> List[Dict]:
    """Extract facts using LLM"""
    # Reuse existing extraction logic from MessageProcessor
    # Or create dedicated fact extraction engine
    
    extraction_prompt = f"""Analyze this user message and extract clear, factual personal statements.

User message: "{message_content}"

Return JSON:
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food",
            "relationship_type": "likes",
            "confidence": 0.9
        }}
    ]
}}
"""
    
    try:
        result = await self.summarization_engine._call_llm(
            prompt=extraction_prompt,
            max_tokens=500
        )
        
        # Parse JSON response
        facts_data = json.loads(result)
        return facts_data.get('facts', [])
        
    except Exception as e:
        logger.error("Fact extraction failed: %s", e)
        return []


async def _store_facts_in_postgres(
    self,
    user_id: str,
    bot_name: str,
    facts: List[Dict]
) -> None:
    """Store extracted facts in PostgreSQL"""
    async with self.db_pool.acquire() as conn:
        for fact in facts:
            await conn.execute("""
                INSERT INTO user_facts (
                    user_id,
                    bot_name,
                    category,
                    fact_content,
                    confidence,
                    extracted_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (user_id, bot_name, fact_content) DO NOTHING
            """, user_id, bot_name, fact['entity_type'], 
                f"{fact['relationship_type']} {fact['entity_name']}", 
                fact['confidence'])


async def _get_last_fact_extraction_timestamp(
    self,
    user_id: str,
    bot_name: str
) -> datetime:
    """Get timestamp of last fact extraction for this user"""
    async with self.db_pool.acquire() as conn:
        result = await conn.fetchval("""
            SELECT MAX(extracted_at)
            FROM user_facts
            WHERE user_id = $1 AND bot_name = $2
        """, user_id, bot_name)
    
    # If no facts exist, start from 30 days ago
    return result or (datetime.utcnow() - timedelta(days=30))
```

**Update Main Enrichment Cycle**:
```python
async def _enrichment_cycle(self) -> None:
    """Run one enrichment cycle"""
    try:
        logger.info("📊 Starting enrichment cycle...")
        start_time = time.time()
        
        # Get all bot collections
        collections = self._get_bot_collections()
        logger.info("Found %s bot collections to process", len(collections))
        
        total_summaries = 0
        total_facts = 0
        
        for collection in collections:
            bot_name = self._extract_bot_name(collection)
            
            # Process conversation summaries
            summaries_count = await self._process_conversation_summaries(
                collection_name=collection,
                bot_name=bot_name
            )
            total_summaries += summaries_count
            
            # 🆕 Process fact extraction
            facts_count = await self._process_fact_extraction(
                collection_name=collection,
                bot_name=bot_name
            )
            total_facts += facts_count
        
        elapsed = time.time() - start_time
        logger.info(
            "✅ Enrichment cycle complete - %s summaries, %s facts in %.2fs",
            total_summaries, total_facts, elapsed
        )
        
    except Exception as e:
        logger.error("❌ Fatal error in enrichment cycle: %s", e)
```

---

### Phase 2: Add Feature Flag to Disable Inline Extraction

**File**: `src/core/message_processor.py`

**Add Environment Variable**:
```python
# Phase 9b: Knowledge extraction and storage (PostgreSQL)
# Can be disabled if async enrichment worker is handling this
if os.getenv('ENABLE_INLINE_FACT_EXTRACTION', 'true').lower() == 'true':
    knowledge_stored = await self._extract_and_store_knowledge(
        message_context, ai_components, extract_from='user'
    )
else:
    knowledge_stored = False
    logger.debug("Inline fact extraction disabled - handled by enrichment worker")
```

**Configuration**:
```env
# .env or .env.{bot_name}
ENABLE_INLINE_FACT_EXTRACTION=false  # Disable when enrichment worker is running
```

---

### Phase 3: Migration Strategy

#### Step 1: Test Enrichment Worker Fact Extraction (1 week)
1. **Add fact extraction** to enrichment worker (Phase 1 code above)
2. **Keep inline extraction enabled** (`ENABLE_INLINE_FACT_EXTRACTION=true`)
3. **Run both systems** in parallel
4. **Compare results** - ensure enrichment worker extracts same facts
5. **Monitor PostgreSQL** for duplicate facts (should be handled by ON CONFLICT)

**Validation Queries**:
```sql
-- Check facts extracted by inline system
SELECT COUNT(*), bot_name 
FROM user_facts 
WHERE extracted_at > NOW() - INTERVAL '1 day'
GROUP BY bot_name;

-- Compare fact counts before/after enrichment worker
SELECT 
    DATE(extracted_at) as date,
    COUNT(*) as fact_count
FROM user_facts
WHERE bot_name = 'elena'
GROUP BY DATE(extracted_at)
ORDER BY date DESC;
```

#### Step 2: Test Performance Impact (2-3 days)
1. **Monitor response times** with inline extraction enabled
2. **Disable inline extraction** for one bot (e.g., Jake)
   ```env
   # .env.jake
   ENABLE_INLINE_FACT_EXTRACTION=false
   ```
3. **Compare response times** (should be 200-500ms faster)
4. **Verify facts still extracted** via enrichment worker

**Performance Queries**:
```bash
# Check response times before/after
docker logs whisperengine-jake-bot 2>&1 | grep "processing_time_ms"

# Expected: 200-500ms reduction when inline extraction disabled
```

#### Step 3: Gradual Rollout (1-2 weeks)
1. **Disable for 2-3 bots** (Jake, Ryan, Dotty - low complexity)
2. **Monitor for 48 hours** - ensure no issues
3. **Disable for remaining bots** one at a time
4. **Monitor fact extraction coverage** - ensure no gaps

#### Step 4: Remove Inline Extraction Code (Future)
1. **After 2-4 weeks** of stable async extraction
2. **Verify no regression** in fact availability
3. **Remove feature flag** and extraction code
4. **Clean up imports** and dependencies

---

## 📊 EXPECTED BENEFITS

### Performance Improvements
- **200-500ms faster** bot responses (no LLM fact extraction blocking)
- **Better user experience** - instant responses
- **Reduced critical path latency** - only essential work in response flow

### Scalability Benefits
- **Enrichment worker handles bursts** - no user-facing impact
- **Better resource utilization** - fact extraction runs when system is idle
- **Easier to scale** - add more enrichment workers if needed

### Architecture Benefits
- **Cleaner separation** - response generation vs. data enrichment
- **More resilient** - fact extraction failures don't block responses
- **Better monitoring** - track enrichment worker metrics separately

---

## ⚠️ RISKS & MITIGATION

### Risk 1: Fact Extraction Delay
**Issue**: Facts extracted async won't be available for immediate next message

**Mitigation**:
- Enrichment worker runs every 5 minutes (configurable to 1-2 minutes)
- Most conversations have gaps >5 minutes between messages
- If needed, prioritize recent messages in enrichment queue

### Risk 2: Duplicate Facts During Migration
**Issue**: Both systems might extract same facts during parallel operation

**Mitigation**:
- PostgreSQL `ON CONFLICT (user_id, bot_name, fact_content) DO NOTHING`
- Automatic deduplication via unique constraint
- Monitor for duplicates anyway

### Risk 3: Missing Facts
**Issue**: Edge case where neither system extracts facts

**Mitigation**:
- Keep inline extraction enabled during migration
- Compare fact counts daily
- Alert if enrichment worker falls behind

---

## 🎯 DECISION MATRIX

| Scenario | Keep Inline? | Enable Async? | Notes |
|----------|-------------|---------------|-------|
| **Testing Phase** | ✅ Yes | ✅ Yes | Run both, compare results |
| **Performance Test** | ❌ No (1 bot) | ✅ Yes | Measure latency improvement |
| **Gradual Rollout** | 🟡 Some bots | ✅ Yes | Disable bot-by-bot |
| **Full Production** | ❌ No | ✅ Yes | All extraction async |

---

## ✅ RECOMMENDATION

### Immediate Action
1. ✅ **Implement fact extraction in enrichment worker** (Phase 1 code above)
2. ✅ **Add feature flag** `ENABLE_INLINE_FACT_EXTRACTION`
3. ✅ **Test with parallel operation** (both systems running)
4. ✅ **Measure performance improvement** when inline disabled

### Timeline
- **Week 1**: Implement + test in parallel
- **Week 2**: Disable inline for 1-2 bots, monitor
- **Week 3-4**: Gradual rollout to all bots
- **Month 2**: Remove inline extraction code (optional cleanup)

### Configuration
```env
# During migration (parallel operation)
ENABLE_INLINE_FACT_EXTRACTION=true

# After validation (async only)
ENABLE_INLINE_FACT_EXTRACTION=false
```

---

## 🔍 MONITORING QUERIES

### Check Fact Extraction Coverage
```sql
-- Ensure enrichment worker is extracting facts
SELECT 
    bot_name,
    COUNT(*) as facts_extracted_today,
    COUNT(DISTINCT user_id) as users_with_facts
FROM user_facts
WHERE extracted_at > NOW() - INTERVAL '24 hours'
GROUP BY bot_name
ORDER BY facts_extracted_today DESC;
```

### Compare Inline vs Async Extraction
```sql
-- Track fact extraction over time
SELECT 
    DATE(extracted_at) as date,
    COUNT(*) as fact_count,
    AVG(confidence) as avg_confidence
FROM user_facts
WHERE bot_name = 'elena'
  AND extracted_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(extracted_at)
ORDER BY date DESC;
```

### Check for Gaps
```sql
-- Find users with recent conversations but no facts
SELECT DISTINCT
    um.user_id,
    COUNT(*) as message_count,
    MAX(um.timestamp) as last_message,
    COALESCE(f.fact_count, 0) as fact_count
FROM user_messages um
LEFT JOIN (
    SELECT user_id, COUNT(*) as fact_count
    FROM user_facts
    GROUP BY user_id
) f ON um.user_id = f.user_id
WHERE um.timestamp > NOW() - INTERVAL '7 days'
GROUP BY um.user_id, f.fact_count
HAVING COALESCE(f.fact_count, 0) = 0
ORDER BY message_count DESC;
```

---

## 🚨 CRITICAL INSIGHT

**The user is 100% correct**: Fact extraction runs **after** response generation (Phase 9b), meaning:
- ✅ Facts don't affect current response
- ✅ Message is already in Qdrant
- ✅ Perfect candidate for async enrichment
- ✅ Can safely move to background worker
- ✅ Will improve response time by 200-500ms

**This is a no-brainer optimization!** 🎯
