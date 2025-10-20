# Bot Self-Fact Extraction - Phase 1 Implementation Complete

**Date**: October 20, 2025  
**Status**: ✅ IMPLEMENTED - Ready for Testing  
**Branch**: feature/async-enrichment-worker

---

## What Was Implemented

### 1. Dual Fact Extraction (User + Bot)

**File**: `src/enrichment/fact_extraction_engine.py`

**Changes**:
- ✅ Updated `extract_facts_from_conversation_window()` to return `Tuple[List[ExtractedFact], List[ExtractedFact]]` (user_facts, bot_facts)
- ✅ Enhanced LLM prompt to extract BOTH user facts AND bot self-facts
- ✅ Added comprehensive priority filtering instructions (HIGH/MEDIUM/LOW)
- ✅ Implemented priority-based fact filtering in `_parse_fact_extraction_result()`
- ✅ Bot facts limited to 3-5 per conversation window (quality over quantity)

**Priority Levels** (in LLM prompt):
```
✅ HIGH PRIORITY (always extract):
  - Strong preferences: "I love X", "I prefer Y over Z"
  - Core passions: "My passion is X", "I'm fascinated by X"
  - Defining habits: "Every morning I X"
  - Professional identity: "My research focuses on X"

✅ MEDIUM PRIORITY (extract if clear):
  - Moderate preferences: "I enjoy X", "I like Y"
  - Hobbies/interests: "I often X"
  - Communication styles: "I prefer collaborative discussions"

❌ LOW PRIORITY (skip):
  - Temporary states: "I'm tired"
  - Generic ownership: "I have a laptop"
  - Politeness: "I appreciate that"
  - Casual mentions: "I saw", "I heard"
```

**Example LLM Response**:
```json
{
  "user_facts": [
    {
      "entity_name": "pizza",
      "entity_type": "food",
      "relationship_type": "likes",
      "confidence": 0.9,
      "priority": "medium",
      "reasoning": "User explicitly stated they love pizza"
    }
  ],
  "bot_facts": [
    {
      "entity_name": "ocean exploration",
      "entity_type": "passion",
      "relationship_type": "loves",
      "confidence": 0.95,
      "priority": "high",
      "reasoning": "Elena said 'I absolutely love exploring ocean depths' - strong preference, identity-defining"
    }
  ]
}
```

---

### 2. Bot Fact Storage with "myself" Convention

**File**: `src/enrichment/worker.py`

**New Method**: `_store_bot_facts_in_postgres()`

**Storage Pattern**:
```sql
-- Bot self-facts use "myself" convention
INSERT INTO user_fact_relationships (
    user_id,               -- "myself" (universal bot self-reference) ✨
    entity_id,             -- FK to fact_entities
    relationship_type,     -- "loves", "prefers", "enjoys", etc.
    confidence,            -- 0.8-0.95 (HIGH/MEDIUM priority only)
    mentioned_by_character,-- "elena", "marcus", etc. (bot isolation)
    source                 -- "enrichment_worker"
) VALUES ('myself', entity_id, 'loves', 0.95, 'elena', 'enrichment_worker');
```

**Query to Retrieve Bot Facts**:
```sql
-- Get Elena's self-facts
SELECT fe.entity_name, ufr.relationship_type, ufr.confidence
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'myself' 
  AND ufr.mentioned_by_character = 'elena'
  AND ufr.confidence >= 0.75
ORDER BY ufr.confidence DESC, ufr.updated_at DESC
LIMIT 10;
```

**Example Stored Facts**:
```
user_id   | entity_name          | relationship_type | confidence | mentioned_by_character
----------|----------------------|-------------------|------------|----------------------
myself    | ocean exploration    | loves             | 0.95       | elena
myself    | tidal pool exploring | enjoys            | 0.90       | elena
myself    | crustacean behavior  | fascinates        | 0.88       | elena
myself    | Earl Grey tea        | prefers           | 0.92       | marcus
myself    | collaborative talks  | prefers           | 0.85       | marcus
```

---

### 3. Worker Integration

**File**: `src/enrichment/worker.py`

**Changes to `extract_facts_for_conversations()` method**:
```python
# BEFORE: Only extracted user facts
extracted_facts = await self.fact_extractor.extract_facts_from_conversation_window(...)
stored_count = await self._store_facts_in_postgres(extracted_facts, ...)

# AFTER: Extracts BOTH user and bot facts
user_facts, bot_facts = await self.fact_extractor.extract_facts_from_conversation_window(...)

# Store user facts (existing logic)
user_stored_count = await self._store_facts_in_postgres(user_facts, ...)

# Store bot self-facts (NEW!)
bot_stored_count = await self._store_bot_facts_in_postgres(bot_facts, bot_name, ...)

total_stored = user_stored_count + bot_stored_count
```

**Logging Output**:
```
📊 Extracted 3 user facts + 2 bot self-facts (user 123456789)
🤖 BOT SELF-FACT: Stored 'ocean exploration' (elena loves it, confidence: 0.95)
🤖 BOT SELF-FACT: Stored 'tidal pool exploring' (elena enjoys it, confidence: 0.90)
✅ Stored 3 user facts + 2 bot self-facts for user 123456789
✅ Stored 2/2 bot self-facts for elena
```

---

## Files Modified

### `src/enrichment/fact_extraction_engine.py`
- **Lines changed**: ~150 lines modified/added
- **Key changes**:
  - Return type: `List[ExtractedFact]` → `Tuple[List[ExtractedFact], List[ExtractedFact]]`
  - LLM prompt: Added bot fact extraction with priority filtering
  - Response parsing: Dual fact lists with priority-based filtering
  - Logging: Separate counts for user vs bot facts

### `src/enrichment/worker.py`
- **Lines changed**: ~120 lines modified/added
- **Key changes**:
  - Dual fact extraction: `user_facts, bot_facts = await extract_facts...`
  - New method: `_store_bot_facts_in_postgres()` (~80 lines)
  - Logging: Separate storage counts for user vs bot facts
  - Storage: "myself" user_id + mentioned_by_character isolation

---

## Testing Plan

### Phase 1: Extraction Quality Test

**Run enrichment worker against Elena's conversations**:
```bash
# Restart enrichment worker to load new code
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker

# Watch logs for bot fact extraction
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker | grep "BOT SELF-FACT"
```

**Expected Behavior**:
- ✅ Only HIGH/MEDIUM priority facts extracted
- ✅ 3-5 facts per conversation window (not 20+)
- ✅ Identity-defining facts ("I love X", "My passion is Y")
- ❌ NO trivial facts ("I have a laptop", "I'm typing")
- ❌ NO temporary states ("I'm tired right now")
- ❌ NO politeness phrases ("I appreciate that")

### Phase 2: Database Validation

**Query bot self-facts**:
```sql
-- Check what facts were extracted for Elena
SELECT 
    fe.entity_name,
    fe.entity_type,
    ufr.relationship_type,
    ufr.confidence,
    ufr.updated_at,
    ufr.conversation_context
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'myself' 
  AND ufr.mentioned_by_character = 'elena'
ORDER BY ufr.confidence DESC, ufr.updated_at DESC;

-- Count facts per bot
SELECT 
    mentioned_by_character as bot_name,
    COUNT(*) as fact_count,
    COUNT(*) FILTER (WHERE confidence > 0.9) as high_confidence,
    COUNT(*) FILTER (WHERE confidence > 0.75) as medium_confidence
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
ORDER BY fact_count DESC;
```

**Success Criteria**:
- Elena has 10-20 core defining facts (not 100+)
- All facts have confidence >= 0.75
- Facts are identity-defining (passions, preferences, habits)
- No "I have a pen" type trivial facts

### Phase 3: A/B Test (Future)

Once confident in extraction quality:
- Enable bot self-fact injection in system prompts
- Compare personality consistency: WITH vs WITHOUT bot facts
- Measure user perception: "Does Elena feel more consistent?"

---

## Monitoring Queries

### Check Bot Self-Fact Extraction Rate
```sql
-- Facts extracted per day
SELECT 
    DATE(updated_at) as date,
    mentioned_by_character as bot_name,
    COUNT(*) as facts_extracted
FROM user_fact_relationships
WHERE user_id = 'myself'
  AND updated_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(updated_at), mentioned_by_character
ORDER BY date DESC, facts_extracted DESC;
```

### Alert: Too Many Facts
```sql
-- Bots with excessive fact counts (needs curation)
SELECT 
    mentioned_by_character as bot_name,
    COUNT(*) as fact_count,
    'REQUIRES CURATION' as status
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
HAVING COUNT(*) > 50
ORDER BY fact_count DESC;
```

### View Recent Bot Facts
```sql
-- Most recently extracted bot facts
SELECT 
    mentioned_by_character as bot_name,
    fe.entity_name,
    ufr.relationship_type,
    ufr.confidence,
    ufr.updated_at,
    LEFT(ufr.conversation_context, 100) as context_preview
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'myself'
ORDER BY ufr.updated_at DESC
LIMIT 20;
```

---

## Next Steps

### Immediate (Testing Phase)
1. ✅ **Phase 1 Complete**: Implementation done, code ready
2. 🧪 **Test Extraction**: Restart enrichment worker, watch logs
3. 🔍 **Validate Quality**: Check database for Elena's bot facts
4. 📊 **Monitor Metrics**: Track extraction rate and fact count

### Short-Term (Phase 2)
- Implement bot fact retrieval in `src/memory/knowledge_router.py`
- Add `get_bot_facts(bot_name, min_confidence=0.75, limit=10)` method
- Test retrieval performance (should be <50ms)

### Medium-Term (Phase 3)
- Inject bot facts into system prompts via `CDLAIPromptIntegration`
- A/B test: 50% users get bot facts, 50% don't
- Measure personality consistency scores

### Long-Term (Phase 4)
- Admin UI for curating bot facts
- Temporal decay mechanism (60-day half-life)
- CDL compatibility validation

---

## Configuration

**Environment Variables** (optional, for future):
```bash
# Enable bot self-fact extraction (currently hard-coded to true)
ENABLE_BOT_SELF_FACT_EXTRACTION=true

# Minimum confidence threshold for bot facts
BOT_FACT_MIN_CONFIDENCE=0.75

# Maximum bot facts per conversation window
BOT_FACT_MAX_PER_WINDOW=5

# Maximum total bot facts per character
BOT_FACT_MAX_TOTAL=50
```

---

## Success Metrics

### Quantitative
- ✅ Each bot has 10-20 core defining facts within 1 month
- ✅ Extraction rate: 3-5 facts per 24-hour window (not 20-30)
- ✅ Zero "I have a pen" type trivial facts in database
- ✅ 90%+ of stored facts have confidence > 0.75
- ✅ Storage performance: <100ms per fact

### Qualitative
- ✅ Users perceive bot personalities as more consistent
- ✅ Bot responses naturally reference their own past statements
- ✅ Emergent personality traits align with CDL definitions
- ✅ No database flooding or query performance issues

---

## Known Limitations

1. **Not Yet Injected**: Bot facts are extracted and stored but NOT YET injected into system prompts
2. **No Contradiction Detection**: Bot facts don't check for conflicts with CDL database yet
3. **No Temporal Decay**: Facts persist indefinitely (60-day decay planned for Phase 4)
4. **Manual Curation Needed**: No admin UI yet - requires SQL queries to review/edit facts

---

## Rollback Plan

If extraction quality is poor:

```bash
# Stop enrichment worker
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop enrichment-worker

# Delete all bot self-facts
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "
DELETE FROM user_fact_relationships WHERE user_id = 'myself';
"

# Revert code changes
git checkout HEAD~1 src/enrichment/fact_extraction_engine.py src/enrichment/worker.py

# Restart worker with old code
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d enrichment-worker
```

---

**Status**: ✅ **READY FOR TESTING**

**Next Command**: Restart enrichment worker to begin extracting bot self-facts from conversations!

```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker
```
