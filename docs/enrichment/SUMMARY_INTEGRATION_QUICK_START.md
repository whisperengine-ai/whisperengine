# Summary Integration Quick Start Guide

**For:** Implementing conversation summary prompt integration  
**Time:** 2-3 hours for MVP (Phase 1)  
**Goal:** Get summaries working with RECALL intent  
**Last Updated:** October 19, 2025

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. Read the strategy
cat docs/enrichment/SUMMARY_PROMPT_INTEGRATION_STRATEGY.md

# 2. Review the roadmap
cat docs/enrichment/SUMMARY_INTEGRATION_ROADMAP.md

# 3. Start implementation
# Follow steps below ↓
```

---

## 📋 Phase 1 Implementation Checklist

### Step 1: Add Summary Retrieval to SemanticRouter (45 min)

**File:** `src/knowledge/semantic_router.py`

**Add method after `get_user_facts()`:**

```python
async def get_relevant_summaries(
    self,
    user_id: str,
    bot_name: str,
    intent: IntentAnalysisResult,
    message: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Retrieve conversation summaries based on query intent.
    
    Only triggers for RECALL and CONVERSATION_STYLE intents.
    Returns empty list for GENERAL intent (no token waste).
    """
    # Skip for non-recall intents
    if intent.intent_type not in [QueryIntent.FACTUAL_RECALL, QueryIntent.CONVERSATION_STYLE]:
        logger.debug(f"🎯 SUMMARIES: Skipping for {intent.intent_type.value} intent")
        return []
    
    # Extract timeframe from natural language
    timeframe = self._extract_timeframe_from_message(message)
    
    async with self.postgres_pool.acquire() as conn:
        if timeframe:
            # Specific timeframe (e.g., "last week")
            summaries = await conn.fetch("""
                SELECT 
                    summary_text,
                    start_timestamp,
                    end_timestamp,
                    key_topics,
                    emotional_tone,
                    message_count
                FROM conversation_summaries
                WHERE user_id = $1 
                  AND bot_name = $2
                  AND start_timestamp >= $3 
                  AND end_timestamp <= $4
                ORDER BY start_timestamp DESC
                LIMIT $5
            """, user_id, bot_name, timeframe['start'], timeframe['end'], limit)
        else:
            # Recent summaries (last 30 days)
            summaries = await conn.fetch("""
                SELECT 
                    summary_text,
                    start_timestamp,
                    end_timestamp,
                    key_topics,
                    emotional_tone,
                    message_count
                FROM conversation_summaries
                WHERE user_id = $1 
                  AND bot_name = $2
                  AND created_at >= NOW() - INTERVAL '30 days'
                ORDER BY start_timestamp DESC
                LIMIT $5
            """, user_id, bot_name, limit)
        
        logger.info(f"🎯 SUMMARIES: Retrieved {len(summaries)} summaries")
    
    return [dict(s) for s in summaries]


def _extract_timeframe_from_message(self, message: str) -> Optional[Dict]:
    """Extract timeframe from natural language patterns."""
    from datetime import datetime, timedelta
    
    message_lower = message.lower()
    now = datetime.utcnow()
    
    # Common patterns
    if "yesterday" in message_lower:
        return {
            'start': now - timedelta(days=1),
            'end': now,
            'label': 'yesterday'
        }
    
    if "last week" in message_lower or "past week" in message_lower:
        return {
            'start': now - timedelta(days=7),
            'end': now,
            'label': 'last week'
        }
    
    if "last month" in message_lower:
        return {
            'start': now - timedelta(days=30),
            'end': now,
            'label': 'last month'
        }
    
    if "today" in message_lower:
        return {
            'start': now.replace(hour=0, minute=0, second=0),
            'end': now,
            'label': 'today'
        }
    
    return None
```

**Test:**
```python
# In Python console or test script
from src.knowledge.semantic_router import create_semantic_knowledge_router

router = create_semantic_knowledge_router(postgres_pool)
intent = await router.analyze_query_intent("What did we talk about yesterday?")
summaries = await router.get_relevant_summaries(
    user_id="test_user",
    bot_name="elena",
    intent=intent,
    message="What did we talk about yesterday?"
)

print(f"Found {len(summaries)} summaries")
```

---

### Step 2: Integrate into CDL Prompt Builder (45 min)

**File:** `src/prompts/cdl_ai_integration.py`

**Find the facts integration section (~line 1500):**

```python
# 🎯 SEMANTIC KNOWLEDGE INTEGRATION: Retrieve structured facts from PostgreSQL
if self.knowledge_router:
    try:
        # Analyze query intent to determine what facts to retrieve
        intent = await self.knowledge_router.analyze_query_intent(message_content)
        # ... existing facts code ...
```

**Add AFTER the facts section:**

```python
        # 📚 CONVERSATION SUMMARIES: Add when semantically relevant
        if self.knowledge_router:
            try:
                # Use same intent from facts analysis above
                summaries = await self.knowledge_router.get_relevant_summaries(
                    user_id=user_id,
                    bot_name=character_name,
                    intent=intent,
                    message=message_content
                )
                
                if summaries:
                    prompt += "\n\n📚 RELEVANT CONVERSATION SUMMARIES:\n"
                    prompt += "Past conversations that may be relevant:\n\n"
                    
                    for summary in summaries:
                        # Format timeframe nicely
                        start = summary['start_timestamp'].strftime('%B %d')
                        end = summary['end_timestamp'].strftime('%B %d, %Y')
                        
                        # Extract key topics (limit to 3)
                        topics = ', '.join(summary['key_topics'][:3]) if summary['key_topics'] else 'various topics'
                        
                        # Add formatted summary
                        prompt += f"**{start} - {end}** ({summary['message_count']} messages):\n"
                        prompt += f"{summary['summary_text']}\n"
                        prompt += f"Topics: {topics}\n"
                        
                        # Add emotional context if available
                        if summary.get('emotional_tone'):
                            prompt += f"Tone: {summary['emotional_tone']}\n"
                        
                        prompt += "\n"
                    
                    # Add synthesis guidance for character
                    prompt += "Use these summaries to inform your response - the user is asking about past conversations.\n"
                    prompt += "Reference specific details naturally, as if recalling from memory.\n"
                    
                    logger.info(f"📚 SUMMARIES: Added {len(summaries)} conversation summaries for {intent.intent_type.value} intent")
                else:
                    logger.debug(f"📚 SUMMARIES: No summaries found for {intent.intent_type.value} intent")
                    
            except Exception as e:
                logger.error(f"❌ SUMMARIES: Retrieval failed: {e}")
```

---

### Step 3: Test with HTTP API (30 min)

**Prerequisites:**
```bash
# Make sure enrichment worker is running and has generated summaries
./multi-bot.sh status | grep enrichment

# Start Elena bot if not running
./multi-bot.sh bot elena
```

**Test 1: RECALL Intent (should trigger summaries)**

```bash
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_recall_12345",
    "message": "What did we talk about yesterday?",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'
```

**Expected:**
- Logs show: `🎯 SUMMARIES: Retrieved N summaries`
- Logs show: `📚 SUMMARIES: Added N conversation summaries`
- Response references specific past conversation details

**Test 2: GENERAL Intent (should skip summaries)**

```bash
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_general_67890",
    "message": "How are you doing today?",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'
```

**Expected:**
- Logs show: `🎯 SUMMARIES: Skipping for general intent`
- No summary section in prompt
- Normal conversational response

---

### Step 4: Validate Token Overhead (15 min)

**Check prompt logs:**

```bash
# Enable prompt logging in .env
echo "ENABLE_PROMPT_LOGGING=true" >> .env.elena

# Restart Elena
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena

# Check prompt files
ls -lh logs/prompts/Elena_*.json

# Analyze token counts
cat logs/prompts/Elena_*.json | jq '.token_estimates'
```

**Expected:**
- Baseline (no summaries): ~2,700 tokens
- With summaries (3 summaries): ~3,100-3,300 tokens
- Overhead: ~400-600 tokens (acceptable)

---

## ✅ Phase 1 Success Criteria

- [ ] `get_relevant_summaries()` method implemented
- [ ] Summary section added to CDL prompt builder
- [ ] RECALL intent triggers summary retrieval
- [ ] GENERAL intent skips summaries (no waste)
- [ ] HTTP API test returns response with past details
- [ ] Token overhead < 500 tokens when summaries added
- [ ] Logs show intent detection working correctly
- [ ] Character references specific conversation details

---

## 🐛 Troubleshooting

### Issue: No summaries retrieved

**Check:**
```sql
-- Verify summaries exist in database
SELECT COUNT(*), user_id, bot_name 
FROM conversation_summaries 
GROUP BY user_id, bot_name;

-- Check recent summaries for test user
SELECT * FROM conversation_summaries 
WHERE user_id = 'test_recall_12345' 
ORDER BY created_at DESC;
```

**Fix:** If no summaries, run enrichment worker for this user first.

### Issue: Intent detection not working

**Check:**
```python
# Test intent detection directly
from src.knowledge.semantic_router import create_semantic_knowledge_router

router = create_semantic_knowledge_router(postgres_pool)
intent = await router.analyze_query_intent("What did we talk about yesterday?")

print(f"Intent: {intent.intent_type}")
print(f"Confidence: {intent.confidence}")
```

**Fix:** If intent is GENERAL instead of FACTUAL_RECALL, check intent patterns in `semantic_router.py`.

### Issue: Summaries added but not referenced in response

**Check:**
- Prompt logging enabled?
- Character synthesis guidance present?
- Summary content actually relevant?

**Fix:** Review prompt logs to see if summaries are formatted correctly.

### Issue: Token budget overflow

**Check:**
```python
# In CDL integration, add limit
summaries = await self.knowledge_router.get_relevant_summaries(
    ...,
    limit=2  # Reduce from 3 to 2
)
```

**Fix:** Reduce summary limit or truncate summary_text.

---

## 📊 Monitoring (Post-Implementation)

### Key Metrics to Track

```bash
# 1. Summary usage rate
SELECT 
    COUNT(*) FILTER (WHERE summaries_retrieved > 0) AS with_summaries,
    COUNT(*) AS total_messages,
    (COUNT(*) FILTER (WHERE summaries_retrieved > 0)::float / COUNT(*)) * 100 AS usage_rate
FROM message_logs
WHERE created_at > NOW() - INTERVAL '24 hours';

# Expected: 5-10% usage rate

# 2. Intent distribution
SELECT intent_type, COUNT(*) 
FROM intent_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY intent_type;

# Expected: Most are GENERAL, some FACTUAL_RECALL

# 3. Token overhead
SELECT 
    AVG(token_count) FILTER (WHERE summaries_added = true) AS avg_with_summaries,
    AVG(token_count) FILTER (WHERE summaries_added = false) AS avg_without,
    AVG(token_count) FILTER (WHERE summaries_added = true) - AVG(token_count) FILTER (WHERE summaries_added = false) AS overhead
FROM prompt_logs
WHERE created_at > NOW() - INTERVAL '24 hours';

# Expected: ~400-500 token overhead when summaries added
```

---

## 🚀 Next Steps (After Phase 1)

### Phase 2: Enhanced Triggering
- Add topic matching (auto-detect when user mentions past topics)
- Add emotional tone routing (RoBERTa matching)
- Add conversation rhythm detection

### Phase 3: Unified Presentation
- Merge facts + summaries into unified 🧠 INTELLIGENCE section
- Test character response quality

### Phase 4: Multi-Vector Search
- Store summary embeddings in Qdrant
- Implement semantic similarity search
- Compare keyword vs semantic accuracy

---

## 📚 Quick Reference Links

**Strategy Document:**
- Full design: `docs/enrichment/SUMMARY_PROMPT_INTEGRATION_STRATEGY.md`

**Roadmap:**
- Implementation plan: `docs/enrichment/SUMMARY_INTEGRATION_ROADMAP.md`

**Key Files to Edit:**
- `src/knowledge/semantic_router.py` - Summary retrieval logic
- `src/prompts/cdl_ai_integration.py` - Prompt integration

**Testing:**
- HTTP API: `http://localhost:9091/api/chat` (Elena)
- Direct Python: `tests/automated/test_summary_integration.py`

**Monitoring:**
- Prompt logs: `logs/prompts/Elena_*.json`
- Bot logs: `docker compose -p whisperengine-multi logs elena-bot`

---

## 💡 Pro Tips

1. **Start with Elena** - Richest CDL character, best for testing
2. **Use fresh user IDs** - Avoid polluted conversation history
3. **Enable prompt logging** - Essential for debugging
4. **Test both intents** - RECALL (should add) and GENERAL (should skip)
5. **Monitor token counts** - Keep overhead < 500 tokens
6. **Check enrichment worker** - Make sure summaries are being generated
7. **Use HTTP API first** - Faster iteration than Discord testing

---

**Status:** 🟢 Ready to Start  
**Estimated Time:** 2-3 hours for Phase 1  
**Success Rate:** High (leveraging existing infrastructure)  
**Risk Level:** Low (additive feature, no breaking changes)
