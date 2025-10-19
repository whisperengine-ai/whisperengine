# Fact Extraction → Async Enrichment Migration Plan

## 🎯 CRITICAL DISCOVERY

**User insight #1**: Fact extraction happens **AFTER response generation** (Phase 9b, line 817), meaning:
- Facts extracted from current message don't affect current response
- Facts are used for FUTURE conversations only
- Message is already stored in Qdrant/PostgreSQL before extraction
- **Perfect candidate for async enrichment worker!**

**User insight #2 (GAME CHANGER)**: Enrichment worker can extract facts from **ENTIRE CONVERSATION WINDOWS**, not just individual messages:
- **Current inline**: Extracts from single user message only
- **Enrichment worker**: Can analyze 5-10 message exchanges as context
- **Better accuracy**: Understands context and confirmation patterns
- **Richer facts**: "User mentioned they love pizza in 3 different conversations" vs "User mentioned pizza once"
- **Temporal patterns**: "User started liking hiking after moving to Colorado"
- **Relationship evolution**: Facts emerge from conversation flow, not isolated statements

**This makes async fact extraction SUPERIOR, not just faster!** 🚀

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
- 🚀 **Same PostgreSQL tables** - zero breaking changes to fact retrieval
- 🚀 **Better scalability** - enrichment worker handles burst loads

### 🎯 CONVERSATION-LEVEL EXTRACTION (SUPERIOR QUALITY!)

**Current inline extraction**: Analyzes single user message in isolation
```
User: "I love pizza"
Bot: "That's great! What kind of pizza do you like?"
User: "Pepperoni is my favorite"

Inline extraction sees:
- Message 1: "loves pizza" ← Extracted
- Message 3: "favorite pepperoni" ← Extracted separately
Result: 2 disconnected facts
```

**Enrichment worker**: Analyzes conversation window as context
```
User: "I love pizza"
Bot: "That's great! What kind of pizza do you like?"
User: "Pepperoni is my favorite"
Bot: "Nice! Do you make it at home or get delivery?"
User: "I actually make my own dough from scratch"

Enrichment extraction sees WHOLE conversation:
- "User loves pizza, specifically pepperoni"
- "User makes homemade pizza with scratch dough"
- "User has cooking skills (baking)"
- Confidence: 0.95 (confirmed across 3 messages)
Result: Rich, contextual facts with higher confidence
```

**Why This Is Better**:
- ✅ **Context awareness**: Understands follow-up clarifications
- ✅ **Confirmation patterns**: "loves pizza" + "pepperoni favorite" = higher confidence
- ✅ **Temporal understanding**: Can track fact evolution over time
- ✅ **Relationship detection**: Links related facts (pizza → cooking → baking skills)
- ✅ **Deduplication**: Avoids extracting "loves pizza" from every pizza mention
- ✅ **Quality over speed**: Can use better models (Claude vs GPT-3.5-turbo)

**Example: Advanced Fact Extraction from Conversation Window**
```python
async def _extract_facts_from_conversation_window(
    self,
    messages: List[Dict],  # 5-10 message window
    user_id: str,
    bot_name: str
) -> List[Dict]:
    """
    Extract facts from entire conversation window for context-aware extraction
    
    This is SUPERIOR to single-message extraction because:
    - Sees confirmation patterns across messages
    - Understands context and clarifications
    - Links related facts together
    - Higher confidence scores from repeated mentions
    """
    
    # Build conversation context from window
    conversation_text = self._format_conversation_window(messages)
    
    extraction_prompt = f"""Analyze this conversation and extract clear, confirmed personal facts about the user.

Conversation:
{conversation_text}

Instructions:
- Look for facts CONFIRMED across multiple messages (higher confidence)
- Link related facts together (e.g., "loves pizza" + "makes dough" = "cooking skills")
- Note temporal patterns (e.g., preferences that emerged recently)
- Extract preferences, skills, possessions, relationships, goals
- Higher confidence for facts mentioned multiple times

Return JSON:
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food",
            "relationship_type": "loves",
            "confidence": 0.95,
            "confirmation_count": 3,
            "related_facts": ["makes homemade pizza", "baking skills"],
            "temporal_context": "long-term preference, mentioned across conversations",
            "reasoning": "User mentioned loving pizza, specified pepperoni, and revealed making own dough - high confidence"
        }}
    ]
}}
"""
    
    # Use better model for enrichment (not time-critical)
    result = await self._call_llm(
        prompt=extraction_prompt,
        model="anthropic/claude-3.5-sonnet",  # Better quality
        max_tokens=1000
    )
    
    return self._parse_fact_extraction_result(result)
```

**Real-World Example**:

Inline extraction (current):
```
Message 1: "I love hiking" → Fact: loves hiking (confidence: 0.7)
Message 2: "I go every weekend" → Fact: goes every weekend (confidence: 0.6)
Message 3: "I moved to Colorado for the mountains" → Fact: lives in Colorado (confidence: 0.8)
```

Conversation-level extraction (enrichment):
```
Conversation window (3 messages):
→ Fact: "loves hiking" (confidence: 0.95, confirmed 2x)
→ Fact: "hikes weekly" (confidence: 0.9, regular activity)
→ Fact: "lives in Colorado" (confidence: 0.95)
→ Fact: "outdoor lifestyle" (confidence: 0.85, inferred from pattern)
→ Relationship: hiking ← motivated move to Colorado (temporal link)
```

**Quality Improvements**:
- **Higher confidence** from multi-message confirmation
- **Richer context** from conversation flow
- **Temporal relationships** between facts
- **Better deduplication** - avoids duplicate facts from related mentions
- **Smarter inference** - can infer meta-facts from patterns

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

### Quality Improvements (THE BIG WIN!)
- **🎯 Conversation-level context** - analyzes 5-10 message windows instead of single messages
- **🎯 Higher confidence scores** - confirmation patterns across messages
- **🎯 Richer facts** - temporal relationships and fact evolution
- **🎯 Better deduplication** - avoids extracting same fact from every mention
- **🎯 Smarter inference** - can infer meta-facts from conversation patterns
- **🎯 Better models** - can use Claude 3.5 Sonnet instead of GPT-3.5-turbo (not time-critical)

### Scalability Benefits
- **Enrichment worker handles bursts** - no user-facing impact
- **Better resource utilization** - fact extraction runs when system is idle
- **Easier to scale** - add more enrichment workers if needed

### Architecture Benefits
- **Cleaner separation** - response generation vs. data enrichment
- **More resilient** - fact extraction failures don't block responses
- **Better monitoring** - track enrichment worker metrics separately
- **Same PostgreSQL schema** - zero breaking changes to fact retrieval

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

## 🚨 CRITICAL INSIGHTS

**User Discovery #1**: Fact extraction runs **after** response generation (Phase 9b), meaning:
- ✅ Facts don't affect current response
- ✅ Message is already in Qdrant
- ✅ Perfect candidate for async enrichment
- ✅ Can safely move to background worker
- ✅ Will improve response time by 200-500ms

**User Discovery #2 (GAME CHANGER)**: Enrichment worker can analyze **ENTIRE CONVERSATION WINDOWS**, not just single messages:
- ✅ **Higher quality facts** - confirmation patterns across messages
- ✅ **Better context** - understands conversation flow
- ✅ **Temporal relationships** - tracks fact evolution
- ✅ **Smarter inference** - derives meta-facts from patterns
- ✅ **Better models** - can use Claude 3.5 Sonnet (not time-critical)

**User Confirmation**: "As long as enrichment populates existing facts tables in PostgreSQL, we're good"
- ✅ **Same PostgreSQL schema** - zero breaking changes
- ✅ **Same tables**: `user_facts`, `user_fact_relationships`
- ✅ **Same retrieval**: `_get_user_facts_from_postgres()` works unchanged
- ✅ **Seamless migration** - bots don't know the difference

**This is not just an optimization - it's a QUALITY IMPROVEMENT!** 🎯

The enrichment worker will produce:
1. **Faster responses** (200-500ms improvement)
2. **Better facts** (conversation-level context)
3. **Higher confidence** (multi-message confirmation)
4. **Richer relationships** (temporal and semantic links)

**This is a no-brainer - all upside, zero downside!** 🚀
