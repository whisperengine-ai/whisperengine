# Quick Start Guide: Async Enrichment Worker

This guide walks you through deploying and testing the async enrichment worker.

## Prerequisites

- WhisperEngine infrastructure running (PostgreSQL, Qdrant)
- At least one bot with conversation data in Qdrant
- OpenRouter API key configured

## Step 1: Apply Database Migration

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migration to create conversation_summaries table
alembic upgrade head

# Verify table was created
docker exec -it postgres psql -U whisperengine -d whisperengine \
  -c "SELECT COUNT(*) FROM conversation_summaries;"
```

Expected output: `0` (table exists but empty)

## Step 2: Validate Setup

```bash
# Run setup validation script
source .venv/bin/activate

export QDRANT_HOST=localhost
export QDRANT_PORT=6334
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=whisperengine
export POSTGRES_USER=whisperengine
export POSTGRES_PASSWORD=whisperengine_password
export OPENROUTER_API_KEY=your_key_here

python scripts/test_enrichment_setup.py
```

Expected output:
```
✅ All tests passed (4/4)
🚀 Ready to start enrichment worker
```

## Step 3: Regenerate Docker Compose Config

The enrichment worker was added to the template, so regenerate the config:

```bash
source .venv/bin/activate
python scripts/generate_multi_bot_config.py
```

## Step 4: Start Enrichment Worker

### Option A: Using multi-bot.sh (Recommended)

```bash
# Start infrastructure + enrichment worker
./multi-bot.sh infra

# Check status
./multi-bot.sh status

# View logs
./multi-bot.sh logs enrichment-worker
```

### Option B: Direct Docker Compose

```bash
# Start enrichment worker
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d enrichment-worker

# View logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker
```

## Step 5: Monitor Enrichment

Watch the logs for enrichment cycles:

```bash
# Follow logs
docker logs -f whisperengine_enrichment_worker

# Or via file
tail -f logs/enrichment/worker.log
```

Expected log messages:
```
🚀 Enrichment worker started - interval: 300 seconds
📊 Starting enrichment cycle...
📝 Processing summaries for elena...
✅ Created 5 summaries for elena
✅ Enrichment cycle complete - 15 summaries created in 45.23s
```

## Step 6: Verify Summaries Created

```bash
# Check how many summaries were created
docker exec -it postgres psql -U whisperengine -d whisperengine \
  -c "SELECT bot_name, COUNT(*) as summary_count FROM conversation_summaries GROUP BY bot_name;"

# View sample summaries
docker exec -it postgres psql -U whisperengine -d whisperengine \
  -c "SELECT user_id, bot_name, start_timestamp, end_timestamp, message_count, key_topics FROM conversation_summaries ORDER BY created_at DESC LIMIT 5;"
```

## Step 7: Test Summary Retrieval (Optional)

Create a simple test script to retrieve summaries:

```python
# test_summary_retrieval.py
import asyncio
import asyncpg
from datetime import datetime, timedelta

async def test_retrieval():
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        database='whisperengine',
        user='whisperengine',
        password='whisperengine_password'
    )
    
    async with pool.acquire() as conn:
        # Get recent summaries
        rows = await conn.fetch("""
            SELECT 
                user_id,
                bot_name,
                summary_text,
                start_timestamp,
                end_timestamp,
                message_count,
                key_topics
            FROM conversation_summaries
            WHERE end_timestamp >= $1
            ORDER BY end_timestamp DESC
            LIMIT 10
        """, datetime.utcnow() - timedelta(days=7))
        
        print(f"Found {len(rows)} summaries from last 7 days:\n")
        
        for row in rows:
            print(f"User: {row['user_id']}")
            print(f"Bot: {row['bot_name']}")
            print(f"Period: {row['start_timestamp']} to {row['end_timestamp']}")
            print(f"Messages: {row['message_count']}")
            print(f"Topics: {row['key_topics']}")
            print(f"Summary: {row['summary_text'][:200]}...")
            print("-" * 60)
    
    await pool.close()

asyncio.run(test_retrieval())
```

Run it:
```bash
python test_summary_retrieval.py
```

## Troubleshooting

### Worker Not Starting

```bash
# Check logs
docker logs whisperengine_enrichment_worker

# Common issues:
# 1. Missing OPENROUTER_API_KEY - add to .env or docker-compose
# 2. PostgreSQL not accessible - check network connectivity
# 3. Qdrant not accessible - check if qdrant container is running
```

### No Summaries Generated

```bash
# Check if conversations exist in Qdrant
docker exec -it qdrant sh
# Inside container:
curl 'http://localhost:6333/collections'

# Check if enrichment cycle is running
docker logs whisperengine_enrichment_worker | grep "Starting enrichment cycle"

# Verify minimum message threshold (default: 5 messages)
# If conversations have fewer messages, they won't be summarized
```

### Worker Keeps Restarting

```bash
# Check health status
docker ps | grep enrichment-worker

# View full logs
docker logs whisperengine_enrichment_worker 2>&1 | less

# Common causes:
# - API key invalid
# - Database connection timeout
# - LLM client initialization failure
```

## Configuration Tuning

### For Testing (Fast Cycles)

```bash
# Edit .env or docker-compose.yml
ENRICHMENT_INTERVAL_SECONDS=60  # Run every minute
MIN_MESSAGES_FOR_SUMMARY=3      # Lower threshold
LOOKBACK_DAYS=7                 # Only last week
```

### For Production (Cost Optimized)

```bash
ENRICHMENT_INTERVAL_SECONDS=600  # Run every 10 minutes
MIN_MESSAGES_FOR_SUMMARY=10      # Higher threshold
LLM_MODEL=anthropic/claude-3-haiku  # Cheaper model
```

## Next Steps

Once enrichment worker is running:

1. **Monitor for 24 hours** - Let it build up summaries
2. **Check summary quality** - Review generated summaries in database
3. **Measure performance** - Track LLM API costs and throughput
4. **Phase 2: Bot Integration** - Enable bots to use summaries (optional enhancement)

## Stopping the Worker

```bash
# Using multi-bot.sh
./multi-bot.sh stop enrichment-worker

# Using docker compose
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop enrichment-worker

# Remove completely
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml rm -f enrichment-worker
```

## Support

- **Documentation**: `src/enrichment/README.md`
- **Architecture**: `docs/architecture/INCREMENTAL_ASYNC_ENRICHMENT.md`
- **Logs**: `logs/enrichment/worker.log`
- **Database**: Check `conversation_summaries` table in PostgreSQL

---

**Status**: Ready for testing  
**Version**: 1.0.0  
**Date**: October 19, 2025
