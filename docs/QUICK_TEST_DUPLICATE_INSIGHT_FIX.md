# Quick Test - Duplicate Insight Fix Verification

## What Was Fixed

1. **Duplicate Insight Warnings** - Silent handling instead of error spam
2. **AttributeError** - `self_focus_ratio` → `self_focus` fix

## How to Test

### Test 1: Start Bot and Check Logs

```bash
# Stop any running bot
./multi-bot.sh stop-bot elena

# Start Elena with fresh logs
./multi-bot.sh bot elena

# In another terminal, check logs for the warning
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot --tail=100 | grep -E "Duplicate|duplicate|self_focus"
```

**Expected Result**: ✅ NO warnings about duplicate insights

**Old Behavior**: ⚠️ Warning like:
```
⚠️ Duplicate insight content for character 1: 'That resonates with me...'
duplicate key value violates unique constraint "uq_character_insight_content"
```

### Test 2: Send Messages and Observe Learning

```bash
# Use HTTP API to send a message
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_Elena_20251103",
    "message": "I love learning about marine biology! Tell me about coral reefs.",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

# Bot should respond without stance analysis errors
# Expected: 200 OK with bot response
```

### Test 3: Check Stance Analysis is Working

Look for INFO level logs showing stance analysis:

```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot --tail=50 | grep -i "stance\|self_focus"
```

**Expected Output** (if stance analysis runs):
```
INFO - USER STANCE ANALYSIS: self_focus=1.0, type=direct, emotions=['love', 'enthusiastic']
INFO - EARLY EMOTION DETECTION: joy (for context-aware memory retrieval)
```

NOT:
```
ERROR - 'StanceAnalysis' object has no attribute 'self_focus_ratio'
```

### Test 4: Verify Database - No Duplicate Errors

Connect to PostgreSQL and check if character learning is working:

```bash
# Connect to postgres
./multi-bot.sh db

# In psql:
SELECT character_id, insight_content, created_at 
FROM character_insights 
WHERE character_id = 1 
ORDER BY created_at DESC 
LIMIT 10;

# Should see unique insight records without duplicates
```

## Regression Testing

### Things That Should Still Work ✅

1. **Character Learning**: Bot learns about users
2. **Memory System**: Insights are stored and retrieved
3. **Stance Analysis**: Emotional attribution is detected
4. **Bot Responses**: Messages are generated normally
5. **Other Characters**: Elena, Marcus, Jake, etc. all work

### Things That Should Be Fixed ✅

1. **No More Warnings**: Duplicate insight warnings gone
2. **Clean Logs**: No AttributeError for `self_focus_ratio`
3. **Graceful Degradation**: Duplicate insights handled without errors

## Success Criteria

✅ **PASS** if:
- Bot starts without errors
- No "duplicate key value violates unique constraint" warnings in logs
- No "AttributeError: 'StanceAnalysis' object has no attribute 'self_focus_ratio'" errors
- Stance analysis logs show `self_focus` (not `self_focus_ratio`)
- Bot continues learning and responding normally

❌ **FAIL** if:
- Any duplicate constraint warnings appear
- Any AttributeError appears
- Bot crashes during learning
- Stance analysis doesn't run

## Log Patterns to Look For

### Good Signs ✅
```
INFO - Stored insight ID 42 for character 1
DEBUG - Insight already exists for character 1 (ID: 42), skipping duplicate
INFO - USER STANCE ANALYSIS: self_focus=0.85, type=direct
```

### Bad Signs ❌
```
WARNING - Duplicate insight content for character 1
ERROR - 'StanceAnalysis' object has no attribute 'self_focus_ratio'
```

## Debugging Help

If you see warnings:

1. Check if insight content is exactly the same:
   ```sql
   SELECT insight_content, COUNT(*) FROM character_insights 
   GROUP BY insight_content HAVING COUNT(*) > 1;
   ```

2. Check the extraction logic in `character_self_insight_extractor.py` to see why duplicates are generated

3. Verify the pre-check is running:
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot | grep -i "already exists"
   ```

## Files Modified

- `src/characters/learning/character_insight_storage.py` ✅
- `src/core/message_processor.py` ✅

## Related Documentation

- Full summary: `docs/DUPLICATE_INSIGHT_FIX_SUMMARY.md`
- Code changes: `docs/CODE_CHANGES_DUPLICATE_INSIGHT_FIX.md`
- Character learning: `docs/architecture/CHARACTER_LEARNING_PERSISTENCE.md`
