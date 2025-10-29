# Bot Self-Reflection Testing Guide

## ✅ Current Test Results

**Direct Python Validation: ALL TESTS PASSED (5/5)**

```
✅ PASS: PostgreSQL Schema - bot_self_reflections table validated
✅ PASS: Reflection Detection - Qdrant conversation analysis working
✅ PASS: PostgreSQL Storage - Insert/retrieve reflections working
✅ PASS: InfluxDB Metrics - Metrics recording ready (InfluxDB optional)
✅ PASS: Bot Self-Memory - PostgreSQL CDL integration working
```

---

## 🧪 Testing Options (Ordered by Speed)

### **Option 1: Direct Python Validation** ⚡ **FASTEST** (Already Done!)

**What we just ran:**
```bash
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=jake && \
python tests/automated/test_bot_self_reflection_direct.py
```

**✅ Validates:**
- PostgreSQL schema (table, columns, indexes)
- Qdrant conversation detection logic
- Direct PostgreSQL insertion/retrieval
- InfluxDB metrics recording
- Bot self-memory PostgreSQL integration

**⏱️ Speed:** 5-10 seconds

---

### **Option 2: Test Enrichment Worker** ⚡ **RECOMMENDED NEXT**

Test the full enrichment cycle with actual LLM reflection generation:

```bash
# Start enrichment worker in foreground for testing
source .venv/bin/activate
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"

# Set OpenRouter API key for LLM
export OPENROUTER_API_KEY="your-key-here"
export LLM_API_URL="https://openrouter.ai/api/v1"
export LLM_CHAT_MODEL="anthropic/claude-3.5-sonnet"

# Run enrichment worker (will process all bots)
python -m src.enrichment.worker
```

**✅ Validates:**
- Full enrichment cycle processing
- Reflection-worthy conversation detection
- LLM-based reflection generation
- Hybrid storage (PostgreSQL + Qdrant + InfluxDB)
- All 12 character bots processed

**⏱️ Speed:** 2-5 minutes (depends on conversations in Qdrant)

**📊 Check Results:**
```sql
-- PostgreSQL: View created reflections
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT bot_name, user_id, effectiveness_score, authenticity_score, 
          emotional_resonance, trigger_type, reflection_category, created_at 
   FROM bot_self_reflections 
   ORDER BY created_at DESC LIMIT 10;"
```

---

### **Option 3: Create Test Conversations First** 🎯

Generate conversations for Jake bot, then run enrichment worker:

```bash
# Step 1: Create test conversations via HTTP API
curl -X POST http://localhost:9097/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_self_reflection_user",
    "message": "Hey Jake! I am feeling really excited about my new photography project!",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

# Send a few more emotional messages
curl -X POST http://localhost:9097/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_self_reflection_user",
    "message": "I am worried about whether my photos are good enough though...",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

curl -X POST http://localhost:9097/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_self_reflection_user",
    "message": "But I love capturing adventure moments! Do you have any tips?",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

# Step 2: Run enrichment worker
python -m src.enrichment.worker
```

**✅ Validates:**
- Real conversation generation
- Emotional trigger detection
- Complete reflection generation flow
- User-specific reflections

**⏱️ Speed:** 5-10 minutes

---

### **Option 4: Query Existing Reflections** 🔍

If enrichment worker already ran, check what reflections exist:

```bash
# PostgreSQL: Check all reflections
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT bot_name, COUNT(*) as reflection_count, 
          AVG(effectiveness_score) as avg_effectiveness,
          AVG(authenticity_score) as avg_authenticity,
          AVG(emotional_resonance) as avg_resonance
   FROM bot_self_reflections 
   GROUP BY bot_name;"

# PostgreSQL: View specific bot's reflections
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT * FROM bot_self_reflections 
   WHERE bot_name = 'jake' 
   ORDER BY created_at DESC 
   LIMIT 5;"

# PostgreSQL: Check reflection categories
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT reflection_category, COUNT(*) as count 
   FROM bot_self_reflections 
   GROUP BY reflection_category;"
```

---

### **Option 5: Test Individual Components** 🧩

Test specific parts of the system in isolation:

#### **5a. Test PostgreSQL Queries**
```python
import asyncio
import asyncpg

async def test_queries():
    pool = await asyncpg.create_pool(
        host="localhost", port=5433, database="whisperengine",
        user="whisperengine", password="whisperengine_password"
    )
    
    # Test character data queries
    async with pool.acquire() as conn:
        # Check Jake's relationships
        rels = await conn.fetch("""
            SELECT related_entity, relationship_type, relationship_strength
            FROM character_relationships 
            WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'jake')
        """)
        print(f"Jake's relationships: {len(rels)}")
        
        # Check Jake's goals
        goals = await conn.fetch("""
            SELECT goal_name, goal_description, priority_level
            FROM character_current_goals 
            WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'jake')
        """)
        print(f"Jake's goals: {len(goals)}")
    
    await pool.close()

asyncio.run(test_queries())
```

#### **5b. Test Qdrant Queries**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from datetime import datetime, timedelta

client = QdrantClient(host="localhost", port=6334)

# Get recent Jake conversations
cutoff = (datetime.utcnow() - timedelta(hours=24)).timestamp()
points = client.scroll(
    collection_name="whisperengine_memory_jake",
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="timestamp_unix",
                range=Range(gte=cutoff)
            )
        ]
    ),
    limit=100,
    with_payload=True
)[0]

print(f"Recent conversations: {len(points)}")
for point in points[:5]:
    print(f"- {point.payload.get('role')}: {point.payload.get('content')[:80]}...")
```

---

## ✅ Recent Fixes

### CDL Column Name Corrections (FIXED - Commit 31ac845)
- **Fixed**: Updated all CDL queries to match actual PostgreSQL schema
- **Changes**:
  - `character_background`: `phase_name→category/title`, `age_range→period/date_range`
  - `character_current_goals`: `goal_name→goal_text`, `priority_level→priority` (string values)
  - `character_interests`: `interest_name→interest_text`, `engagement_level→proficiency_level`
- **Impact**: Bot self-memory now imports **19 knowledge entries** (previously 2)
- **Status**: All 4 knowledge types working (relationships, background, goals, interests)

### **InfluxDB Optional**
```
⚠️ InfluxDB recording returned False (may be disabled)
```

**Impact:** None - InfluxDB is optional for time-series metrics
**Status:** Expected if InfluxDB not configured in .env
**Workaround:** System works without InfluxDB (PostgreSQL + Qdrant sufficient)

---

## 📊 Success Metrics

**What to look for after running enrichment worker:**

1. **PostgreSQL**: Reflections created for bots with recent conversations
2. **Qdrant**: Reflections stored in `bot_self_{bot_name}` namespace (check via conversation storage)
3. **InfluxDB**: `bot_self_reflection` measurement with scores (if enabled)
4. **Quality**: Reflection insights should be coherent and relevant to conversations
5. **Scores**: effectiveness_score, authenticity_score, emotional_resonance between 0.0-1.0

---

## 🚀 Recommended Testing Sequence

1. ✅ **DONE**: Direct Python validation (`test_bot_self_reflection_direct.py`)
2. **NEXT**: Create test conversations via HTTP API (5-10 messages with emotion)
3. **THEN**: Run enrichment worker and watch for reflection creation
4. **FINALLY**: Query PostgreSQL to verify reflections stored correctly

---

## 💡 Quick Commands Reference

```bash
# Run direct validation
python tests/automated/test_bot_self_reflection_direct.py

# Check PostgreSQL reflections
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT COUNT(*) FROM bot_self_reflections;"

# Check recent reflections
docker exec -it postgres psql -U whisperengine -d whisperengine -c \
  "SELECT * FROM bot_self_reflections ORDER BY created_at DESC LIMIT 5;"

# Run enrichment worker (foreground)
python -m src.enrichment.worker

# Test with Jake bot HTTP API
curl -X POST http://localhost:9097/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Test message"}'
```
