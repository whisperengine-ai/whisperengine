# TODO: Implement Missing InfluxDB Bot Emotion Query Methods

**Status**: 🔴 Not Started  
**Priority**: Medium (Functional workaround exists, but missing intended time-series capability)  
**Created**: October 15, 2025  
**Effort Estimate**: 2-4 hours  
**Related Issue**: Phase 6.5 Bot Emotion Retrieval Implementation Gap

---

## 📋 Problem Statement

**Phase 6.5 (Bot Emotional Self-Awareness) currently queries Qdrant for bot emotion trajectory, but the original design intended to query InfluxDB for true time-series emotion analysis.**

### Evidence of Missing Implementation:

1. **`CharacterTemporalEvolutionAnalyzer`** (line 220) calls:
   ```python
   bot_emotions = await temporal_client.get_bot_emotion_trend(...)
   ```

2. **But `TemporalIntelligenceClient` doesn't have these methods**:
   - `get_bot_emotion_trend()` - Missing!
   - `get_bot_emotion_overall_trend()` - Missing!

3. **Current Workaround**: Phase 6.5 uses Qdrant semantic search instead
   - Location: `src/core/message_processor.py:4173-4230`
   - Method: `_analyze_bot_emotional_trajectory()`

### Why This Matters:

| Aspect | Current (Qdrant) | Intended (InfluxDB) |
|--------|------------------|---------------------|
| **Query Type** | Semantic/vector search | Pure time-series chronological |
| **Results** | Context-relevant emotions | Complete chronological trajectory |
| **Use Case** | "Find emotional responses about dolphins" | "Show emotion trend over last 7 days" |
| **Ordering** | Relevance-based | Strictly chronological |
| **Completeness** | Limited to stored conversations | Full emotion history |

**Trade-off**: Qdrant provides context-aware retrieval; InfluxDB provides true temporal analysis.

---

## 🎯 Implementation Tasks

### Task 1: Add `get_bot_emotion_trend()` Method to TemporalIntelligenceClient

**File**: `src/temporal/temporal_intelligence_client.py`  
**Location**: After `get_relationship_evolution()` method (around line 880)

**Method Signature**:
```python
async def get_bot_emotion_trend(
    self,
    bot_name: str,
    user_id: str,
    hours_back: int = 24
) -> List[Dict[str, Any]]:
    """
    Get bot emotion trend for specific user over time.
    
    Retrieves chronological bot emotion data from InfluxDB for Phase 6.5
    bot emotional trajectory analysis.
    
    Args:
        bot_name: Name of the bot (elena, marcus, etc.)
        user_id: User identifier
        hours_back: How many hours of history to retrieve (default: 24)
        
    Returns:
        List of bot emotion measurements sorted chronologically:
        [
            {
                'timestamp': datetime,
                'primary_emotion': str,
                'intensity': float,
                'confidence': float
            },
            ...
        ]
        
    Example:
        >>> emotions = await client.get_bot_emotion_trend("elena", "123456", hours_back=48)
        >>> print(emotions[0])
        {'timestamp': '2025-10-15T10:30:00Z', 'primary_emotion': 'joy', 'intensity': 0.87}
    """
    if not self.enabled:
        return []

    try:
        query = f'''
            from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
            |> range(start: -{hours_back}h)
            |> filter(fn: (r) => r._measurement == "bot_emotion")
            |> filter(fn: (r) => r.bot == "{bot_name}")
            |> filter(fn: (r) => r.user_id == "{user_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: false)
        '''
        
        result = self.query_api.query(query)
        
        emotions = []
        for table in result:
            for record in table.records:
                emotions.append({
                    'timestamp': record.get_time(),
                    'primary_emotion': record.values.get('emotion', 'neutral'),  # From tag
                    'intensity': record.values.get('intensity', 0.0),
                    'confidence': record.values.get('confidence', 0.0)
                })
        
        return sorted(emotions, key=lambda x: x['timestamp'])
        
    except Exception as e:
        logger.error(f"Failed to get bot emotion trend: {e}")
        return []
```

**Implementation Notes**:
- Use existing pattern from `get_confidence_trend()` and `get_relationship_evolution()`
- Query `bot_emotion` measurement (stored by Phase 7.5)
- Sort by timestamp (chronological order)
- Return empty list if InfluxDB disabled or query fails

---

### Task 2: Add `get_bot_emotion_overall_trend()` Method

**File**: `src/temporal/temporal_intelligence_client.py`  
**Location**: After `get_bot_emotion_trend()` method

**Method Signature**:
```python
async def get_bot_emotion_overall_trend(
    self,
    bot_name: str,
    hours_back: int = 24
) -> List[Dict[str, Any]]:
    """
    Get bot emotion trend across ALL users (character-level analysis).
    
    Retrieves bot's emotional patterns aggregated across all conversations.
    Useful for character behavior analysis and emotional consistency monitoring.
    
    Args:
        bot_name: Name of the bot (elena, marcus, etc.)
        hours_back: How many hours of history to retrieve (default: 24)
        
    Returns:
        List of bot emotion measurements across all users:
        [
            {
                'timestamp': datetime,
                'primary_emotion': str,
                'intensity': float,
                'confidence': float,
                'user_id': str  # Which user triggered this emotion
            },
            ...
        ]
        
    Example:
        >>> emotions = await client.get_bot_emotion_overall_trend("elena", hours_back=168)
        >>> joy_count = sum(1 for e in emotions if e['primary_emotion'] == 'joy')
    """
    if not self.enabled:
        return []

    try:
        query = f'''
            from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
            |> range(start: -{hours_back}h)
            |> filter(fn: (r) => r._measurement == "bot_emotion")
            |> filter(fn: (r) => r.bot == "{bot_name}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: false)
        '''
        
        result = self.query_api.query(query)
        
        emotions = []
        for table in result:
            for record in table.records:
                emotions.append({
                    'timestamp': record.get_time(),
                    'primary_emotion': record.values.get('emotion', 'neutral'),  # From tag
                    'intensity': record.values.get('intensity', 0.0),
                    'confidence': record.values.get('confidence', 0.0),
                    'user_id': record.values.get('user_id', 'unknown')  # From tag
                })
        
        return sorted(emotions, key=lambda x: x['timestamp'])
        
    except Exception as e:
        logger.error(f"Failed to get bot emotion overall trend: {e}")
        return []
```

**Implementation Notes**:
- Same as Task 1 but WITHOUT user_id filter
- Returns emotions across ALL users for character-level analysis
- Includes `user_id` in results to track per-user patterns

---

### Task 3: Update Phase 6.5 to Use InfluxDB (Optional - Keep Qdrant as Fallback)

**File**: `src/core/message_processor.py`  
**Location**: `_analyze_bot_emotional_trajectory()` method (lines 4173-4230)

**Implementation Strategy**: Add InfluxDB as PRIMARY with Qdrant as FALLBACK

```python
async def _analyze_bot_emotional_trajectory(self, message_context: MessageContext) -> Optional[Dict[str, Any]]:
    """
    Analyze bot's emotional trajectory from recent conversation history.
    
    Phase 7.6: Bot Emotional Self-Awareness
    - PRIMARY: Retrieves bot's recent emotional responses from InfluxDB (time-series)
    - FALLBACK: Uses Qdrant vector memory if InfluxDB unavailable
    - Calculates emotional trajectory (improving, declining, stable)
    - Provides emotional state for prompt building (bot knows its own emotions)
    - Enables emotionally-aware responses (e.g., "I've been feeling down lately")
    
    Args:
        message_context: Message context with user ID
        
    Returns:
        Dict with current_emotion, trajectory_direction, emotional_velocity, recent_emotions
    """
    try:
        if not self.memory_manager:
            return None
        
        bot_name = get_normalized_bot_name_from_env()
        
        # PRIMARY: Try InfluxDB for chronological time-series (if available)
        recent_emotions = []
        if self.temporal_client and self.temporal_client.enabled:
            try:
                # Query last 24 hours of bot emotions from InfluxDB
                influx_emotions = await self.temporal_client.get_bot_emotion_trend(
                    bot_name=bot_name,
                    user_id=message_context.user_id,
                    hours_back=24
                )
                
                if influx_emotions:
                    recent_emotions = [
                        {
                            'emotion': e['primary_emotion'],
                            'intensity': e['intensity'],
                            'timestamp': e['timestamp'],
                            'mixed_emotions': []  # InfluxDB doesn't store mixed emotions
                        }
                        for e in influx_emotions[-10:]  # Last 10 emotions
                    ]
                    logger.debug(f"🎭 Retrieved {len(recent_emotions)} bot emotions from InfluxDB")
            except Exception as e:
                logger.debug(f"InfluxDB bot emotion query failed, falling back to Qdrant: {e}")
        
        # FALLBACK: Use Qdrant semantic search if InfluxDB unavailable or returned no data
        if not recent_emotions:
            bot_memory_query = f"emotional responses by {bot_name}"
            
            recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=message_context.user_id,
                query=bot_memory_query,
                limit=10
            )
            
            if not recent_bot_memories:
                return None
            
            # Extract bot emotions from memory metadata
            for memory in recent_bot_memories:
                if isinstance(memory, dict):
                    metadata = memory.get('metadata', {})
                    bot_emotion = metadata.get('bot_emotion')
                    
                    if bot_emotion and isinstance(bot_emotion, dict):
                        recent_emotions.append({
                            'emotion': bot_emotion.get('primary_emotion', 'neutral'),
                            'intensity': bot_emotion.get('intensity', 0.0),
                            'timestamp': memory.get('timestamp', ''),
                            'mixed_emotions': bot_emotion.get('mixed_emotions', [])
                        })
            
            logger.debug(f"🎭 Retrieved {len(recent_emotions)} bot emotions from Qdrant (fallback)")
        
        if not recent_emotions:
            return None
        
        # Rest of trajectory calculation remains the same...
        # (Calculate emotional velocity, trajectory direction, etc.)
        
    except Exception as e:
        logger.debug("Bot emotional trajectory analysis failed: %s", str(e))
        return None
```

**Implementation Notes**:
- Try InfluxDB first for true chronological time-series
- Fall back to Qdrant if InfluxDB unavailable or returns no data
- Log which data source was used for debugging
- Maintain backward compatibility with existing Qdrant-based implementation

---

### Task 4: Add Unit Tests

**File**: `tests/unit/test_temporal_intelligence_client.py`

**Test Cases**:
```python
import pytest
from datetime import datetime, timedelta
from src.temporal.temporal_intelligence_client import TemporalIntelligenceClient

@pytest.mark.asyncio
async def test_get_bot_emotion_trend_returns_chronological_order():
    """Verify bot emotions are returned in chronological order"""
    client = TemporalIntelligenceClient()
    
    if not client.enabled:
        pytest.skip("InfluxDB not available")
    
    # Record test emotions
    now = datetime.now()
    await client.record_bot_emotion("elena", "test_user", "joy", 0.8, 0.9, timestamp=now - timedelta(hours=2))
    await client.record_bot_emotion("elena", "test_user", "curiosity", 0.7, 0.85, timestamp=now - timedelta(hours=1))
    await client.record_bot_emotion("elena", "test_user", "excitement", 0.9, 0.95, timestamp=now)
    
    # Retrieve trend
    emotions = await client.get_bot_emotion_trend("elena", "test_user", hours_back=3)
    
    # Verify chronological order
    assert len(emotions) == 3
    assert emotions[0]['primary_emotion'] == 'joy'
    assert emotions[1]['primary_emotion'] == 'curiosity'
    assert emotions[2]['primary_emotion'] == 'excitement'
    
    # Verify timestamps are ascending
    for i in range(len(emotions) - 1):
        assert emotions[i]['timestamp'] < emotions[i+1]['timestamp']


@pytest.mark.asyncio
async def test_get_bot_emotion_trend_filters_by_user():
    """Verify emotions are filtered to specific user"""
    client = TemporalIntelligenceClient()
    
    if not client.enabled:
        pytest.skip("InfluxDB not available")
    
    # Record emotions for different users
    await client.record_bot_emotion("elena", "user_1", "joy", 0.8, 0.9)
    await client.record_bot_emotion("elena", "user_2", "sadness", 0.6, 0.85)
    
    # Retrieve for user_1 only
    emotions = await client.get_bot_emotion_trend("elena", "user_1", hours_back=1)
    
    # Should only get user_1's emotions
    assert all(e['primary_emotion'] != 'sadness' for e in emotions)


@pytest.mark.asyncio
async def test_get_bot_emotion_overall_trend_includes_all_users():
    """Verify overall trend includes emotions from all users"""
    client = TemporalIntelligenceClient()
    
    if not client.enabled:
        pytest.skip("InfluxDB not available")
    
    # Record emotions for multiple users
    await client.record_bot_emotion("elena", "user_1", "joy", 0.8, 0.9)
    await client.record_bot_emotion("elena", "user_2", "curiosity", 0.7, 0.85)
    
    # Retrieve overall trend
    emotions = await client.get_bot_emotion_overall_trend("elena", hours_back=1)
    
    # Should include both users
    assert len(emotions) >= 2
    user_ids = [e['user_id'] for e in emotions]
    assert 'user_1' in user_ids
    assert 'user_2' in user_ids
```

---

### Task 5: Update Documentation

**Files to Update**:

1. **`docs/architecture/PHASE_6_STORAGE_ANALYSIS.md`**:
   - Remove "⚠️ IMPLEMENTATION GAP" warnings
   - Update to show InfluxDB as PRIMARY data source
   - Keep Qdrant as documented fallback

2. **`docs/architecture/PHASE_7_10_11_STORAGE_ANALYSIS.md`**:
   - Update "Phase 6.5 Retrieves Phase 7.5 Data" section
   - Show InfluxDB query as implemented (not missing)
   - Remove implementation gap warnings

3. **`src/temporal/temporal_intelligence_client.py`** docstring:
   - Add bot emotion query methods to module docstring
   - Document PRIMARY/FALLBACK pattern for Phase 6.5

---

## 🧪 Testing Strategy

### Manual Testing Steps:

1. **Start Infrastructure**:
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant influxdb
   ```

2. **Verify InfluxDB Has Bot Emotion Data**:
   ```bash
   influx query 'from(bucket: "whisperengine")
     |> range(start: -24h)
     |> filter(fn: (r) => r._measurement == "bot_emotion")
     |> filter(fn: (r) => r.bot == "elena")
     |> limit(n: 10)'
   ```

3. **Test InfluxDB Query Method** (Python REPL):
   ```python
   import asyncio
   from src.temporal.temporal_intelligence_client import get_temporal_client
   
   client = get_temporal_client()
   emotions = asyncio.run(client.get_bot_emotion_trend("elena", "123456", hours_back=24))
   print(f"Retrieved {len(emotions)} emotions")
   for e in emotions[:5]:
       print(f"{e['timestamp']}: {e['primary_emotion']} (intensity: {e['intensity']:.2f})")
   ```

4. **Test Phase 6.5 Integration** (Discord message):
   - Send message to Elena bot
   - Check logs for "Retrieved X bot emotions from InfluxDB"
   - Verify bot response shows emotional self-awareness

5. **Test Fallback to Qdrant**:
   - Stop InfluxDB: `docker stop whisperengine-multi-influxdb-1`
   - Send message to Elena bot
   - Check logs for "falling back to Qdrant"
   - Verify bot still functions correctly

---

## 📊 Success Criteria

- ✅ `get_bot_emotion_trend()` method implemented and returns chronological data
- ✅ `get_bot_emotion_overall_trend()` method implemented for character-level analysis
- ✅ Phase 6.5 uses InfluxDB as PRIMARY with Qdrant as FALLBACK
- ✅ Unit tests pass with 100% coverage for new methods
- ✅ Manual testing confirms chronological bot emotion retrieval
- ✅ Fallback to Qdrant works when InfluxDB unavailable
- ✅ Documentation updated to reflect implemented changes
- ✅ No breaking changes to existing functionality

---

## 🚨 Potential Issues & Solutions

### Issue 1: InfluxDB Not Recording Bot Emotions

**Symptom**: Query returns empty list even though conversations happened  
**Cause**: Phase 7.5 might not be writing to InfluxDB successfully  
**Solution**: Check `temporal_client.record_bot_emotion()` calls in Phase 7.5 (message_processor.py:659-678)

### Issue 2: Query Performance with Large Datasets

**Symptom**: Slow query response times with thousands of bot emotions  
**Cause**: InfluxDB query scanning too much data  
**Solution**: 
- Reduce `hours_back` parameter (default 24 hours)
- Add `limit()` clause to Flux query
- Consider adding index on `bot` + `user_id` tags

### Issue 3: Timestamp Ordering Inconsistencies

**Symptom**: Emotions not returned in strict chronological order  
**Cause**: InfluxDB precision issues or network delays  
**Solution**: Add explicit `|> sort(columns: ["_time"], desc: false)` to Flux query

### Issue 4: Missing Mixed Emotions Data

**Symptom**: InfluxDB returns emotions but without `mixed_emotions` field  
**Cause**: InfluxDB only stores primary emotion fields (intensity, confidence)  
**Solution**: 
- Accept limitation (mixed emotions only available from Qdrant fallback)
- OR: Extend InfluxDB schema to store mixed emotions JSON (larger storage footprint)

---

## 📈 Performance Impact

**Expected Performance Characteristics**:

| Metric | InfluxDB Primary | Qdrant Fallback |
|--------|------------------|-----------------|
| **Query Latency** | 10-50ms (time-series) | 20-80ms (vector search) |
| **Data Completeness** | 100% chronological | Limited to stored memories |
| **Context Awareness** | None (pure time-series) | High (semantic relevance) |
| **Storage Overhead** | +200 bytes per emotion | Existing (no change) |

**No Performance Degradation Expected**: InfluxDB queries are typically FASTER than Qdrant vector search.

---

## 🔗 Related Documentation

- **Architecture**: `docs/architecture/PHASE_6_STORAGE_ANALYSIS.md`
- **Architecture**: `docs/architecture/PHASE_7_10_11_STORAGE_ANALYSIS.md`
- **Implementation**: `src/core/message_processor.py:4173-4230` (Phase 6.5)
- **Implementation**: `src/temporal/temporal_intelligence_client.py` (InfluxDB client)
- **Evidence**: `src/characters/learning/character_temporal_evolution_analyzer.py:220` (calls missing methods)

---

## 🎯 Next Steps

1. **Review this TODO** with team/project owner
2. **Create GitHub Issue** linking to this document
3. **Estimate sprint allocation** (recommend: Next available sprint, 2-4 hour task)
4. **Assign developer** familiar with InfluxDB and Phase 6.5 architecture
5. **Implement Task 1 & 2** (InfluxDB query methods) first
6. **Test independently** before touching Phase 6.5
7. **Implement Task 3** (Phase 6.5 integration) with fallback pattern
8. **Update documentation** (Task 5)

---

**Priority Justification**: Medium priority because:
- ✅ System functions correctly with Qdrant workaround
- ✅ No user-facing bugs or broken features
- ⚠️ Missing intended time-series analysis capability
- ⚠️ Technical debt (called methods don't exist)
- 💡 Low effort (2-4 hours) with high architectural clarity gain

**Recommendation**: Implement in next maintenance sprint or character tuning cycle.
