# WhisperEngine Async Enrichment Worker

Background intelligence enrichment system that processes conversations asynchronously, generating high-quality summaries and insights without impacting real-time bot performance.

## Overview

The enrichment worker is a **separate Docker container** that:
- Runs independently from Discord bots (zero impact on real-time performance)
- Scans Qdrant vector storage periodically for conversations
- Generates conversation summaries using high-quality LLMs
- Stores summaries in PostgreSQL for fast retrieval
- Enables time-anchored queries ("what did we talk about last week?")

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Platform                       │
├─────────────────────────────────────────────────────────────────┤
│  HOT PATH (Real-time)                                           │
│  Discord Message → Vector Storage → Response (FAST!)            │
│                          │                                       │
│  ════════════════════════════════════════════════════════════  │
│                          │                                       │
│  COLD PATH (Async)       v                                      │
│  Enrichment Worker → Qdrant Scan → LLM Summarization           │
│                                  → PostgreSQL Storage           │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 1. **Conversation Summaries**
- Time-windowed summaries (default: 24-hour windows)
- High-quality LLM analysis (Claude 3.5 Sonnet, GPT-4 Turbo)
- Key topics extraction
- Emotional tone analysis
- Compression ratio tracking

### 2. **Time-Anchored Queries**
- Pre-computed summaries enable "what did we talk about last week?"
- Summaries stored with start/end timestamps
- PostgreSQL indexed for fast temporal queries

### 3. **Independent Scaling**
- Worker scales separately from Discord bots
- No impact on real-time message processing
- Configurable enrichment intervals

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `qdrant` | Qdrant server host |
| `QDRANT_PORT` | `6333` | Qdrant server port |
| `POSTGRES_HOST` | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `whisperengine` | Database name |
| `POSTGRES_USER` | `whisperengine` | Database user |
| `POSTGRES_PASSWORD` | - | Database password (required) |
| `ENRICHMENT_INTERVAL_SECONDS` | `300` | How often to run enrichment (5 min) |
| `ENRICHMENT_BATCH_SIZE` | `50` | Messages per batch |
| `MIN_MESSAGES_FOR_SUMMARY` | `5` | Minimum messages to summarize |
| `TIME_WINDOW_HOURS` | `24` | Summary time window size |
| `LOOKBACK_DAYS` | `30` | How far back to process |
| `LLM_MODEL` | `anthropic/claude-3.5-sonnet` | LLM for enrichment |
| `OPENROUTER_API_KEY` | - | OpenRouter API key (required) |

### Tuning Recommendations

**High Volume (lots of users/messages)**:
```bash
ENRICHMENT_INTERVAL_SECONDS=600  # 10 minutes
ENRICHMENT_BATCH_SIZE=100
TIME_WINDOW_HOURS=12  # Smaller windows
```

**Cost Optimization**:
```bash
LLM_MODEL=anthropic/claude-3-haiku  # Cheaper model
ENRICHMENT_INTERVAL_SECONDS=900  # 15 minutes
MIN_MESSAGES_FOR_SUMMARY=10  # Require more messages
```

**Quality Priority**:
```bash
LLM_MODEL=anthropic/claude-3-opus  # Best quality
ENRICHMENT_INTERVAL_SECONDS=180  # 3 minutes
TIME_WINDOW_HOURS=6  # More granular summaries
```

## Deployment

### Using multi-bot.sh (Development)

```bash
# Start infrastructure + enrichment worker
./multi-bot.sh infra

# Check enrichment worker status
./multi-bot.sh logs enrichment-worker

# Monitor enrichment worker
docker logs -f enrichment-worker
```

### Manual Docker Compose

```bash
# Start enrichment worker only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d enrichment-worker

# View logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker

# Restart worker
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker
```

## Database Schema

### conversation_summaries Table

```sql
CREATE TABLE conversation_summaries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    
    summary_text TEXT NOT NULL,
    summary_type VARCHAR(50) DEFAULT 'time_window',
    
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    
    message_count INTEGER NOT NULL,
    key_topics TEXT[],
    emotional_tone VARCHAR(50),
    
    compression_ratio FLOAT,
    confidence_score FLOAT DEFAULT 0.5,
    
    enrichment_version VARCHAR(20) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, bot_name, start_timestamp, end_timestamp)
);
```

## Monitoring

### Logs

```bash
# Watch enrichment worker logs
tail -f logs/enrichment/worker.log

# Or via Docker
docker logs -f enrichment-worker
```

### Key Log Messages

- `🚀 Enrichment worker started` - Worker initialization
- `📊 Starting enrichment cycle` - Beginning of cycle
- `📝 Processing summaries for {bot}` - Bot processing
- `✅ Created {N} summaries` - Cycle completion
- `❌ Enrichment cycle failed` - Error occurred

### Health Check

```bash
# Check worker container health
docker ps | grep enrichment-worker

# Manual health check
docker exec enrichment-worker ps aux | grep worker
```

## Performance Impact

### Hot Path (Real-time)
- **Impact**: ZERO (worker runs independently)
- **Latency**: No change to bot response times
- **Resources**: Separate container, separate resources

### Cold Path (Enrichment)
- **Throughput**: ~50 messages per cycle (configurable)
- **LLM Calls**: 1-2 per time window (batched)
- **Storage**: ~1KB per summary (highly compressed)

## Cost Analysis

### LLM API Costs

**Example**: 1000 active users, 50 messages/day average

```
Daily messages: 1000 users × 50 messages = 50,000 messages
Time windows: 50,000 / 10 messages per window = 5,000 windows
LLM calls: 5,000 windows × 1 summary call = 5,000 calls

Claude 3.5 Sonnet:
- Input: ~500 tokens/summary × $3/1M = $1.50/day
- Output: ~200 tokens/summary × $15/1M = $1.50/day
Total: ~$3/day or $90/month
```

**Cost vs Value**:
- Removes ~1000ms from hot path = 25% performance improvement
- Enables time-based queries (new feature!)
- Higher quality intelligence (better model, more context)

## Troubleshooting

### Worker Not Starting

```bash
# Check logs for errors
docker logs enrichment-worker

# Common issues:
# 1. Missing OPENROUTER_API_KEY
# 2. PostgreSQL connection failed
# 3. Qdrant connection failed
```

### No Summaries Generated

```bash
# Check if messages exist in Qdrant
docker exec -it qdrant sh
# Use Qdrant API to check collections

# Check PostgreSQL connection
docker exec -it postgres psql -U whisperengine -d whisperengine -c "SELECT COUNT(*) FROM conversation_summaries;"
```

### High API Costs

```bash
# Reduce enrichment frequency
export ENRICHMENT_INTERVAL_SECONDS=900  # 15 minutes

# Use cheaper model
export LLM_MODEL=anthropic/claude-3-haiku

# Increase minimum message threshold
export MIN_MESSAGES_FOR_SUMMARY=15
```

## Development

### Local Testing

```bash
# Set up environment
source .venv/bin/activate
export QDRANT_HOST=localhost
export QDRANT_PORT=6334
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export OPENROUTER_API_KEY=your_key_here

# Run worker directly
python -m src.enrichment.worker
```

### Running Alembic Migration

```bash
# Apply conversation_summaries migration
source .venv/bin/activate
alembic upgrade head
```

## Future Enhancements

### Phase 2 Features
- [ ] Semantic search on conversation summaries
- [ ] Multi-bot conversation correlation
- [ ] Adaptive time window sizing
- [ ] Summary quality scoring and feedback loop

### Phase 3 Features
- [ ] Enhanced fact extraction (beyond current system)
- [ ] Relationship mapping and graph enrichment
- [ ] Temporal pattern analysis
- [ ] User preference learning

## Documentation

- **Architecture**: `docs/architecture/INCREMENTAL_ASYNC_ENRICHMENT.md`
- **Performance Optimization**: `docs/roadmaps/PERFORMANCE_OPTIMIZATION_ROADMAP.md`
- **Migration**: `alembic/versions/20251019_conversation_summaries.py`

## Support

For issues or questions:
1. Check logs: `docker logs enrichment-worker`
2. Review configuration in `.env` or docker-compose
3. Validate database migration: `alembic current`
4. Check Qdrant collections: Visit http://localhost:6334/dashboard

---

**Status**: ✅ Operational  
**Version**: 1.0.0  
**Last Updated**: October 19, 2025
