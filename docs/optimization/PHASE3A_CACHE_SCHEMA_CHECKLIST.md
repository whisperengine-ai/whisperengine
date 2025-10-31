# Phase 3A Implementation Checklist: Strategic Cache Schema

**Phase**: Database Schema Migration  
**Duration**: Week 1 of Phase 3  
**Status**: 📋 Ready to Start

---

## 🎯 Objective

Create PostgreSQL cache tables for storing strategic component results computed by the background enrichment worker.

**Target Performance**:
- Cache read time: <5ms per lookup
- Cache freshness: 5-minute TTL
- Cache hit rate: >95%

---

## 📋 Implementation Tasks

### Task 1: Create Alembic Migration Script

**File**: `alembic/versions/YYYYMMDD_HHMM_add_strategic_cache_tables.py`

**Tables to Create** (6 total):

1. **strategic_memory_health**
   - Tracks memory aging, staleness, retrieval patterns
   - UNIQUE constraint: `(user_id, bot_name)`
   - Index: `expires_at` for fast cleanup

2. **strategic_character_performance**
   - 7-day rolling performance metrics
   - UNIQUE constraint: `(bot_name, time_window_hours)`
   - Index: `expires_at`

3. **strategic_personality_profiles**
   - User-bot personality interaction evolution
   - UNIQUE constraint: `(user_id, bot_name)`
   - Index: `expires_at`

4. **strategic_conversation_patterns**
   - Topic switches, conversation flow, patterns
   - UNIQUE constraint: `(user_id, bot_name)`
   - Index: `expires_at`

5. **strategic_memory_behavior**
   - Human-like forgetting/recall modeling
   - UNIQUE constraint: `(user_id, bot_name)`
   - Index: `expires_at`

6. **strategic_engagement_opportunities**
   - Proactive engagement timing and topics
   - UNIQUE constraint: `(user_id, bot_name)`
   - Index: `expires_at`

**Schema Reference**: See `PHASE3_BACKGROUND_WORKER_DESIGN.md` for full SQL

**Command**:
```bash
cd /Users/markcastillo/git/whisperengine
source .venv/bin/activate
alembic revision --autogenerate -m "Add strategic component cache tables"
```

**Validation**:
- [ ] Review generated migration file
- [ ] Verify all 6 tables included
- [ ] Check UNIQUE constraints and indexes
- [ ] Test migration: `alembic upgrade head`
- [ ] Verify tables created: `\dt strategic_*` in psql

---

### Task 2: Cache Helper Functions

**File**: `src/core/message_processor.py` (add new methods)

**Methods to Add**:

```python
async def _get_cached_strategic_data(
    self,
    table_name: str,
    user_id: str,
    bot_name: str
) -> Optional[Dict[str, Any]]:
    """
    Fast cache lookup for strategic component data.
    
    Returns None if cache miss or stale (>5 min).
    Target: <5ms query time.
    """
    pass

async def _check_cache_freshness(
    self,
    table_name: str,
    user_id: str,
    bot_name: str
) -> bool:
    """
    Check if cached data is fresh (<5 min old).
    Returns True if fresh, False if stale/missing.
    """
    pass
```

**Implementation Details**:
- Use `self.db_pool` for PostgreSQL queries
- Add query timing logs (DEBUG level)
- Handle connection errors gracefully
- Return `None` on any error (graceful degradation)

**Testing**:
```bash
# Direct Python validation
source .venv/bin/activate
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
export DISCORD_BOT_NAME=elena
python -c "
import asyncio
from src.core.message_processor import MessageProcessor
# Test cache read performance
"
```

---

### Task 3: Test Cache Performance

**Script**: `tests/performance/test_strategic_cache_performance.py`

**Test Cases**:
1. **Cold Cache Read** (cache miss)
   - Expected: <5ms query time
   - Return: `None`

2. **Warm Cache Read** (fresh data)
   - Expected: <5ms query time
   - Return: Full cached data dict

3. **Stale Cache Read** (>5 min old)
   - Expected: <5ms query time
   - Return: `None` (treated as miss)

4. **Concurrent Reads** (10 parallel users)
   - Expected: <10ms avg per query
   - No connection pool exhaustion

**Success Criteria**:
- ✅ All queries <5ms (p95)
- ✅ Cache hit rate >95% in simulation
- ✅ No connection errors under load

---

### Task 4: Add Cache Monitoring

**InfluxDB Metrics**:

Add to `src/metrics/temporal_metrics_client.py`:

```python
async def record_strategic_cache_metrics(
    self,
    table_name: str,
    cache_hit: bool,
    query_time_ms: float,
    cache_age_minutes: Optional[float],
    bot_name: str
):
    """Record strategic cache performance metrics"""
    pass
```

**Grafana Dashboard**:

Create panel in Grafana:
- Cache hit rate by table (line chart)
- Cache query latency (histogram)
- Cache age distribution (gauge)
- Cache misses by bot (bar chart)

---

### Task 5: Documentation

**File**: `docs/optimization/STRATEGIC_CACHE_USAGE.md`

**Content**:
- Cache table schemas
- TTL policy (5 minutes)
- Helper function usage examples
- Graceful degradation behavior
- Monitoring dashboard screenshots

---

## 🧪 Testing Plan

### Unit Tests
```bash
# Test cache helper functions
pytest tests/unit/test_strategic_cache_helpers.py -v
```

### Integration Tests
```bash
# Test with live PostgreSQL
pytest tests/integration/test_strategic_cache_integration.py -v
```

### Performance Tests
```bash
# Benchmark cache read latency
python tests/performance/test_strategic_cache_performance.py
```

### Manual Validation
```bash
# Create cache entries manually
psql -h localhost -p 5433 -U whisperengine whisperengine

# Insert test data
INSERT INTO strategic_memory_health (user_id, bot_name, memory_snapshot, computed_at, expires_at)
VALUES ('test_user_123', 'elena', '{"test": "data"}', NOW(), NOW() + INTERVAL '5 minutes');

# Query from MessageProcessor
python tests/manual/test_cache_read_direct.py
```

---

## ✅ Acceptance Criteria

- [ ] All 6 strategic cache tables created via Alembic migration
- [ ] Cache helper functions implemented in `MessageProcessor`
- [ ] Cache read latency <5ms (p95) validated
- [ ] Unit tests pass (100% coverage for cache helpers)
- [ ] Integration tests pass with live PostgreSQL
- [ ] Performance benchmarks meet targets
- [ ] Monitoring metrics added to InfluxDB
- [ ] Grafana dashboard created
- [ ] Documentation complete

---

## 🚀 Deployment Steps

### Local Development
```bash
# Apply migration
cd /Users/markcastillo/git/whisperengine
source .venv/bin/activate
alembic upgrade head

# Verify tables
docker exec -it whisperengine-multi-postgres-1 psql -U whisperengine -d whisperengine -c "\dt strategic_*"

# Test cache functions
pytest tests/unit/test_strategic_cache_helpers.py -v
```

### Docker Environment
```bash
# Restart PostgreSQL with new schema
./multi-bot.sh down
./multi-bot.sh infra

# Migration runs automatically in init container
# Verify via logs
docker logs whisperengine-multi-postgres-1 | grep strategic_
```

---

## 📊 Success Metrics

| Metric | Target | Validation Method |
|--------|--------|------------------|
| Cache read latency (p95) | <5ms | Performance tests |
| Cache hit rate | >95% | Simulation tests |
| Migration success | 100% | Alembic upgrade logs |
| Zero downtime | ✅ | Rolling schema changes |
| No hot path impact | <1ms overhead | Benchmark comparison |

---

## 🔗 Related Documents

- **Phase 3 Design**: `PHASE3_BACKGROUND_WORKER_DESIGN.md`
- **Alembic Guide**: `alembic/README.md`
- **Database Schema**: `docs/architecture/DATABASE_SCHEMA.md`

---

**Next Phase**: Phase 3B - Implement Strategic Component Engines

**Estimated Completion**: Week 1 of Phase 3 (5 working days)
