# Character Emotional State Engine - Strategic Intelligence Engine 10/10

**Status**: 📋 Planned (Not Started)  
**Priority**: Medium (Quality-of-Life Enhancement)  
**Created**: October 31, 2025  
**Target**: Q1 2026  
**Complexity**: Moderate (2-3 weeks)

---

## 🎯 Executive Summary

Add **Character Emotional State tracking as the 10th Strategic Intelligence Engine** in the enrichment worker. This resurrects the orphaned v2 11-emotion implementation (created Oct 29, removed Oct 31) and places it in the correct architectural layer: **background strategic processing, not real-time**.

### The Opportunity

We have **707 lines of fully-implemented 11-emotion tracking code** sitting unused on disk:
- ✅ `src/intelligence/character_emotional_state_v2.py` (30KB, complete implementation)
- ✅ Full RoBERTa 11-emotion spectrum
- ✅ EMA-ready architecture
- ✅ Computed properties for emotional analysis
- ❌ Never deployed (removed as "overengineered" for real-time)

### The Solution

**Move it to enrichment worker** (like the other 9 strategic engines):
- Zero real-time latency impact
- Preserves character emotional evolution
- Enables authentic self-awareness
- Follows established architectural pattern

---

## 🏗️ Current Architecture Context

### **Existing Enrichment Engines** (9/10)

```
src/enrichment/
├── memory_aging_engine.py               # 1/10 ✅
├── character_performance_engine.py      # 2/10 ✅
├── context_switch_engine.py             # 3/10 ✅
├── conversation_pattern_engine.py       # 4/10 ✅
├── personality_profile_engine.py        # 5/10 ✅
├── human_memory_behavior_engine.py      # 6/10 ✅
├── proactive_engagement_engine.py       # 7/10 ✅
├── fact_extraction_engine.py            # 8/10 ✅
├── summarization_engine.py              # 9/10 ✅
└── character_emotional_state_engine.py  # 10/10 ❌ MISSING
```

### **Enrichment Worker Pattern**

All engines follow the same pattern:
1. **Input**: Query Qdrant/InfluxDB for recent data (7-day lookback)
2. **Processing**: Analyze patterns, compute metrics, run ML/LLM analysis
3. **Output**: Store results in PostgreSQL `strategic_*_cache` tables
4. **Retrieval**: Message processor reads cache (fast, no computation)
5. **Cycle**: Runs every 11 minutes (background)

---

## 📊 Timeline: How We Got Here

### **October 22, 2025** - Database Removal
- Removed PostgreSQL `character_emotional_states` table
- Made 5-dimension system in-memory only
- Justification: "InfluxDB sufficient for persistence"

### **October 29, 2025** - v2 Implementation
- Created `character_emotional_state_v2.py` (707 lines)
- Implemented full 11-emotion RoBERTa spectrum
- Upgraded from 5 dimensions to 11 emotions
- Never integrated into message processor

### **October 30, 2025** - Pipeline Optimization
- Created roadmap to move 7 strategic components to background
- Identified Character Emotional State as "❓ requires audit"
- Never explicitly planned enrichment worker path

### **October 31, 2025** - Feature Removal
- Removed `CharacterEmotionalStateManager` from message processor
- Justification: "100-150ms overhead, overengineered, duplicates CDL"
- **BUT**: v1 and v2 files still exist on disk (orphaned code)

### **The Gap**

Two roadmaps existed but never converged:
- ✅ **Character Emotional State Redesign** → Assumed real-time integration
- ✅ **Pipeline Optimization** → Moved 7 components to background
- ❌ **Missing link**: Character Emotional State → 10th Strategic Engine

---

## 🎯 What This Achieves

### **✅ Performance**
- **Zero real-time latency** (background processing every 11 minutes)
- **Maintains 150-300ms savings** from October 31 removal
- **Minimal memory overhead** (cache table only)

### **✅ Character Authenticity**
- **Characters evolve emotionally** over time
- **Self-awareness is genuine**: "I've been feeling energized" = statistically true
- **No mood whiplash**: 11-minute processing = natural smoothing window
- **Full 11-emotion fidelity**: anger, anticipation, disgust, fear, joy, love, optimism, pessimism, sadness, surprise, trust

### **✅ Architectural Consistency**
- **Follows established pattern**: 10th strategic intelligence engine
- **Uses existing infrastructure**: Enrichment worker, PostgreSQL cache, Qdrant queries
- **Matches other engines**: Similar API, similar processing cycle, similar value

### **✅ Value Preservation**
- **Resurrects 707 lines of quality code** (already written, already tested)
- **Preserves designer intent**: 11-emotion system is better than 5-dimension
- **Enables future features**: Character learning, relationship evolution, emotional memory

---

## 🚀 Implementation Plan

### **Phase 1: Create Engine** (Week 1 - 3 days)

#### **Step 1.1: Create CharacterEmotionalStateEngine**

**File**: `src/enrichment/character_emotional_state_engine.py`

```python
"""
Strategic Intelligence Engine 10/10 - Character Emotional Evolution

Analyzes bot's emotional patterns over time to track character emotional
state evolution. Runs in background enrichment worker (11-minute cycle).

This engine queries bot emotion data from Qdrant vector memory, calculates
EMA-smoothed emotional trajectories, and stores character emotional profiles
in PostgreSQL cache for prompt injection.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class CharacterEmotionalStateEngine:
    """
    Strategic Intelligence Engine 10/10 - Character Emotional State Evolution
    
    Analyzes character emotional patterns from bot responses stored in Qdrant.
    Computes EMA-smoothed trajectories for all 11 RoBERTa emotions.
    """
    
    def __init__(self, qdrant_client: QdrantClient):
        """Initialize engine with Qdrant client."""
        self.qdrant_client = qdrant_client
        self.logger = logger
    
    async def analyze_character_emotions(
        self,
        bot_name: str,
        user_id: str,
        lookback_hours: int = 168  # 7 days
    ) -> Dict[str, Any]:
        """
        Analyze character's emotional trajectory from bot responses.
        
        Args:
            bot_name: Name of the character/bot
            user_id: User ID to analyze emotions for
            lookback_hours: Hours to look back (default: 7 days)
            
        Returns:
            Dict containing:
            - Current emotional state (11 emotions with EMA smoothing)
            - Emotional trajectories (escalating/stable/declining per emotion)
            - Dominant emotion
            - Emotional intensity, valence, complexity
            - Metadata (total interactions, last updated, etc.)
        """
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Query bot emotions from Qdrant
            bot_emotions = await self._query_bot_emotions_from_qdrant(
                bot_name=bot_name,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )
            
            if not bot_emotions or len(bot_emotions) < 3:
                self.logger.debug(
                    f"Insufficient bot emotion data for {bot_name}/{user_id}: "
                    f"{len(bot_emotions) if bot_emotions else 0} messages"
                )
                return self._empty_result(bot_name, user_id)
            
            # Calculate EMA-smoothed emotional state
            emotional_state = await self._calculate_emotional_state_with_ema(
                bot_emotions=bot_emotions,
                alpha=0.3  # Moderate smoothing for 11-minute cycle
            )
            
            # Analyze emotional trajectories
            trajectories = await self._analyze_emotional_trajectories(
                bot_emotions=bot_emotions
            )
            
            # Compute derived metrics
            derived_metrics = self._compute_derived_metrics(emotional_state)
            
            return {
                'bot_name': bot_name,
                'user_id': user_id,
                'lookback_hours': lookback_hours,
                'analyzed_at': end_time.isoformat(),
                
                # Current emotional state (11 emotions with EMA)
                'emotional_state': emotional_state,
                
                # Trajectories (per emotion)
                'trajectories': trajectories,
                
                # Derived metrics
                'dominant_emotion': derived_metrics['dominant_emotion'],
                'emotional_intensity': derived_metrics['emotional_intensity'],
                'emotional_valence': derived_metrics['emotional_valence'],
                'emotional_complexity': derived_metrics['emotional_complexity'],
                
                # Metadata
                'total_interactions': len(bot_emotions),
                'data_quality': 'sufficient'
            }
            
        except Exception as e:
            self.logger.error(
                f"Error analyzing character emotions for {bot_name}/{user_id}: {e}",
                exc_info=True
            )
            return self._empty_result(bot_name, user_id, error=str(e))
    
    async def _query_bot_emotions_from_qdrant(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Query bot emotion data from Qdrant vector memory.
        
        Retrieves bot_primary_emotion, bot_emotional_intensity, and
        bot emotion scores from memory payloads.
        """
        collection_name = f"whisperengine_memory_{bot_name.lower()}"
        
        # Query with filter for user_id and time range
        results = self.qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=200,  # Last ~200 messages (covers 7 days typically)
            with_payload=True,
            with_vectors=False
        )
        
        # Extract bot emotion data from payloads
        bot_emotions = []
        for point in results[0]:
            payload = point.payload
            
            # Check if bot emotion data exists
            if 'bot_primary_emotion' not in payload:
                continue
            
            timestamp = payload.get('timestamp')
            if not timestamp:
                continue
            
            # Filter by time range
            msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if msg_time < start_time or msg_time > end_time:
                continue
            
            bot_emotions.append({
                'timestamp': timestamp,
                'primary_emotion': payload.get('bot_primary_emotion'),
                'intensity': payload.get('bot_emotional_intensity', 0.5),
                'confidence': payload.get('bot_roberta_confidence', 0.7),
                # All 11 emotions (if available)
                'all_emotions': payload.get('bot_all_emotions', {})
            })
        
        # Sort by timestamp (oldest first)
        bot_emotions.sort(key=lambda x: x['timestamp'])
        
        return bot_emotions
    
    async def _calculate_emotional_state_with_ema(
        self,
        bot_emotions: List[Dict[str, Any]],
        alpha: float = 0.3
    ) -> Dict[str, float]:
        """
        Calculate EMA-smoothed emotional state from bot emotions.
        
        Uses Exponential Moving Average to smooth emotional trajectories
        over the 7-day lookback window.
        """
        # Initialize with first message emotions
        if not bot_emotions:
            return self._default_emotional_state()
        
        # Start with first message
        current_state = bot_emotions[0]['all_emotions'].copy() if bot_emotions[0]['all_emotions'] else {}
        
        # Ensure all 11 emotions exist
        emotion_names = [
            'anger', 'anticipation', 'disgust', 'fear', 'joy', 'love',
            'optimism', 'pessimism', 'sadness', 'surprise', 'trust'
        ]
        for emotion in emotion_names:
            if emotion not in current_state:
                current_state[emotion] = 0.3  # Neutral default
        
        # Apply EMA across all messages
        for bot_emotion in bot_emotions[1:]:
            all_emotions = bot_emotion['all_emotions']
            if not all_emotions:
                continue
            
            # Update each emotion with EMA formula
            for emotion in emotion_names:
                detected_value = all_emotions.get(emotion, current_state[emotion])
                current_value = current_state[emotion]
                
                # EMA: new_value = α * detected + (1 - α) * current
                new_value = alpha * detected_value + (1 - alpha) * current_value
                new_value = max(0.0, min(1.0, new_value))  # Clamp to [0, 1]
                
                current_state[emotion] = new_value
        
        return current_state
    
    async def _analyze_emotional_trajectories(
        self,
        bot_emotions: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Analyze trajectory pattern for each emotion.
        
        Returns 'escalating', 'stable', or 'declining' for each emotion.
        """
        trajectories = {}
        
        emotion_names = [
            'anger', 'anticipation', 'disgust', 'fear', 'joy', 'love',
            'optimism', 'pessimism', 'sadness', 'surprise', 'trust'
        ]
        
        for emotion in emotion_names:
            # Extract emotion values over time
            values = []
            for bot_emotion in bot_emotions:
                all_emotions = bot_emotion.get('all_emotions', {})
                if emotion in all_emotions:
                    values.append(all_emotions[emotion])
            
            if len(values) < 3:
                trajectories[emotion] = 'unknown'
                continue
            
            # Calculate trend
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            change = second_half_avg - first_half_avg
            
            if change > 0.15:
                trajectories[emotion] = 'escalating'
            elif change < -0.15:
                trajectories[emotion] = 'declining'
            else:
                trajectories[emotion] = 'stable'
        
        return trajectories
    
    def _compute_derived_metrics(self, emotional_state: Dict[str, float]) -> Dict[str, Any]:
        """Compute derived metrics from emotional state."""
        # Dominant emotion
        dominant_emotion = max(emotional_state.items(), key=lambda x: x[1])[0]
        
        # Emotional intensity (how far from neutral on average)
        intensities = [abs(v - 0.3) for v in emotional_state.values()]
        emotional_intensity = sum(intensities) / len(intensities)
        
        # Emotional valence (positive vs negative tone)
        positive = (
            emotional_state.get('joy', 0) + 
            emotional_state.get('love', 0) + 
            emotional_state.get('optimism', 0) + 
            emotional_state.get('trust', 0) + 
            emotional_state.get('anticipation', 0)
        )
        negative = (
            emotional_state.get('anger', 0) + 
            emotional_state.get('disgust', 0) + 
            emotional_state.get('fear', 0) + 
            emotional_state.get('pessimism', 0) + 
            emotional_state.get('sadness', 0)
        )
        total = positive + negative
        emotional_valence = (positive - negative) / total if total > 0 else 0.0
        
        # Emotional complexity (how many emotions simultaneously active)
        active_count = sum(1 for v in emotional_state.values() if v > 0.3)
        emotional_complexity = active_count / len(emotional_state)
        
        return {
            'dominant_emotion': dominant_emotion,
            'emotional_intensity': round(emotional_intensity, 3),
            'emotional_valence': round(emotional_valence, 3),
            'emotional_complexity': round(emotional_complexity, 3)
        }
    
    def _default_emotional_state(self) -> Dict[str, float]:
        """Default emotional state (neutral)."""
        return {
            'anger': 0.1,
            'anticipation': 0.4,
            'disgust': 0.05,
            'fear': 0.1,
            'joy': 0.7,
            'love': 0.6,
            'optimism': 0.6,
            'pessimism': 0.2,
            'sadness': 0.15,
            'surprise': 0.2,
            'trust': 0.7
        }
    
    def _empty_result(self, bot_name: str, user_id: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Return empty result when insufficient data."""
        return {
            'bot_name': bot_name,
            'user_id': user_id,
            'emotional_state': self._default_emotional_state(),
            'trajectories': {},
            'dominant_emotion': 'unknown',
            'emotional_intensity': 0.0,
            'emotional_valence': 0.0,
            'emotional_complexity': 0.0,
            'total_interactions': 0,
            'data_quality': 'insufficient',
            'error': error
        }
```

#### **Step 1.2: Add PostgreSQL Cache Table**

**Migration**: `alembic/versions/XXX_add_strategic_character_emotional_state_cache.py`

```sql
CREATE TABLE strategic_character_emotional_state_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    
    -- Current emotional state (11 RoBERTa emotions with EMA)
    anger_ema FLOAT NOT NULL,
    anticipation_ema FLOAT NOT NULL,
    disgust_ema FLOAT NOT NULL,
    fear_ema FLOAT NOT NULL,
    joy_ema FLOAT NOT NULL,
    love_ema FLOAT NOT NULL,
    optimism_ema FLOAT NOT NULL,
    pessimism_ema FLOAT NOT NULL,
    sadness_ema FLOAT NOT NULL,
    surprise_ema FLOAT NOT NULL,
    trust_ema FLOAT NOT NULL,
    
    -- Derived metrics
    dominant_emotion VARCHAR(50),
    emotional_intensity FLOAT,
    emotional_valence FLOAT,
    emotional_complexity FLOAT,
    
    -- Trajectory patterns (last 7 days)
    joy_trajectory VARCHAR(20),
    trust_trajectory VARCHAR(20),
    anticipation_trajectory VARCHAR(20),
    
    -- Metadata
    total_interactions INTEGER,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_window_hours INTEGER,
    data_quality VARCHAR(20),
    
    UNIQUE(bot_name, user_id)
);

CREATE INDEX idx_character_emotion_bot_user 
ON strategic_character_emotional_state_cache(bot_name, user_id);

CREATE INDEX idx_character_emotion_updated 
ON strategic_character_emotional_state_cache(last_updated);
```

---

### **Phase 2: Integrate with Enrichment Worker** (Week 2 - 2 days)

#### **Step 2.1: Add to Worker Processing**

**File**: `src/enrichment/worker.py`

```python
# Add to imports
from src.enrichment.character_emotional_state_engine import CharacterEmotionalStateEngine

# Add to worker initialization
character_emotional_state_engine = CharacterEmotionalStateEngine(qdrant_client)

# Add to processing loop
async def process_user_data(user_id: str, bot_name: str):
    """Process all strategic intelligence for user."""
    
    # ... existing engines ...
    
    # NEW: Character Emotional State Engine (10/10)
    character_emotions = await character_emotional_state_engine.analyze_character_emotions(
        bot_name=bot_name,
        user_id=user_id,
        lookback_hours=168  # 7 days
    )
    
    # Store in PostgreSQL cache
    await store_character_emotional_state(character_emotions)
```

#### **Step 2.2: Add Cache Storage Function**

```python
async def store_character_emotional_state(state_data: Dict[str, Any]):
    """Store character emotional state in PostgreSQL cache."""
    await db.execute(
        """
        INSERT INTO strategic_character_emotional_state_cache (
            bot_name, user_id,
            anger_ema, anticipation_ema, disgust_ema, fear_ema, joy_ema,
            love_ema, optimism_ema, pessimism_ema, sadness_ema, surprise_ema, trust_ema,
            dominant_emotion, emotional_intensity, emotional_valence, emotional_complexity,
            joy_trajectory, trust_trajectory, anticipation_trajectory,
            total_interactions, analysis_window_hours, data_quality
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
            $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
        )
        ON CONFLICT (bot_name, user_id) DO UPDATE SET
            anger_ema = EXCLUDED.anger_ema,
            -- ... all other fields ...
            last_updated = NOW()
        """,
        state_data['bot_name'],
        state_data['user_id'],
        state_data['emotional_state']['anger'],
        # ... all 11 emotions ...
    )
```

---

### **Phase 3: Prompt Integration** (Week 2 - 2 days)

#### **Step 3.1: Add Cache Retrieval Helper**

**File**: `src/core/message_processor.py`

```python
async def _get_character_emotional_context(self, user_id: str) -> Optional[str]:
    """
    Retrieve character emotional state from cache (if available).
    
    Returns prompt guidance for character self-awareness.
    """
    if not self.db_pool:
        return None
    
    try:
        result = await self.db_pool.fetchrow(
            """
            SELECT dominant_emotion, emotional_intensity, emotional_valence,
                   joy_trajectory, trust_trajectory
            FROM strategic_character_emotional_state_cache
            WHERE bot_name = $1 AND user_id = $2
            AND last_updated > NOW() - INTERVAL '2 hours'
            """,
            self.character_name,
            user_id
        )
        
        if not result:
            return None
        
        # Only inject if meaningful pattern detected
        trajectories = []
        if result['joy_trajectory'] in ['escalating', 'declining']:
            trajectories.append(f"joy {result['joy_trajectory']}")
        if result['trust_trajectory'] in ['escalating', 'declining']:
            trajectories.append(f"trust {result['trust_trajectory']}")
        
        if not trajectories:
            return None  # No interesting patterns
        
        return (
            f"\n**CHARACTER SELF-AWARENESS**:\n"
            f"Your emotional state with this user: {result['dominant_emotion']} "
            f"(intensity: {result['emotional_intensity']:.2f}, "
            f"tone: {'positive' if result['emotional_valence'] > 0 else 'neutral'}). "
            f"Emotional trajectory: {', '.join(trajectories)}. "
            f"This reflects your genuine emotional evolution in this relationship."
        )
        
    except Exception as e:
        logger.warning(f"Failed to retrieve character emotional context: {e}")
        return None
```

#### **Step 3.2: Inject into Prompt Building**

**File**: `src/prompts/emotional_intelligence_component.py`

```python
# Add to build_emotional_guidance()
character_emotional_context = await self._get_character_emotional_context(user_id)
if character_emotional_context:
    guidance_sections.append(character_emotional_context)
```

---

## 📋 Success Criteria

### **Quantitative**

1. **Zero latency impact**: <5ms cache retrieval (vs 100-150ms removed)
2. **Coverage**: 80%+ of active users have emotional state cached
3. **Freshness**: 95%+ of cache entries updated within last 2 hours
4. **Data quality**: 90%+ of analyses marked as "sufficient" (enough data)

### **Qualitative**

1. **Character continuity**: Characters reference own emotional evolution naturally
2. **Self-awareness**: "I've been feeling energized" statements are statistically accurate
3. **No complaints**: No user reports of characters seeming emotionally inconsistent
4. **Developer confidence**: Team approves enrichment worker approach

---

## 🚨 Risks & Mitigations

### **Risk 1: Insufficient Bot Emotion Data**

**Risk**: Not all bot responses have emotion analysis in Qdrant

**Mitigation**:
- ✅ Check `bot_primary_emotion` field existence before processing
- ✅ Require minimum 3 messages for analysis (otherwise return "insufficient")
- ✅ Graceful degradation: System works fine without this feature

### **Risk 2: 11-Minute Lag**

**Risk**: Character emotional state lags real-time by up to 11 minutes

**Mitigation**:
- ✅ This is acceptable for strategic feature (not tactical)
- ✅ EMA smoothing makes lag less noticeable (gradual shifts)
- ✅ Characters don't need real-time mood updates

### **Risk 3: Cache Staleness**

**Risk**: Cache becomes stale if enrichment worker fails

**Mitigation**:
- ✅ Check `last_updated < 2 hours ago` before using
- ✅ Fall back to no guidance if cache stale
- ✅ Monitor enrichment worker health separately

---

## 📊 Comparison: Old vs New

| Feature | Old (5D Real-Time) | New (11E Background) |
|---------|-------------------|---------------------|
| **Emotions Tracked** | 5 dimensions (lossy) | 11 emotions (full fidelity) |
| **Architecture** | Real-time per message | Background every 11 min |
| **Latency Impact** | 100-150ms | <5ms (cache read) |
| **Mood Stability** | Volatile (spikes) | Stable (EMA smoothed) |
| **Memory Usage** | 35-40MB per bot | Minimal (cache only) |
| **Data Storage** | In-memory only | PostgreSQL cache |
| **Self-Awareness** | Per-message | 7-day trajectory |
| **Production Ready** | ❌ Removed Oct 31 | ✅ Planned Q1 2026 |

---

## 🎯 Why This is Better

### **Compared to Real-Time (Removed System)**

- ✅ **Zero latency** vs 100-150ms overhead
- ✅ **Stable patterns** vs mood whiplash
- ✅ **11 emotions** vs 5 dimensions (better fidelity)
- ✅ **Persistent storage** vs in-memory only

### **Compared to No Bot Emotions**

- ✅ **Character evolution** vs static personality
- ✅ **Self-awareness memory** vs shallow references
- ✅ **Relationship depth** vs transactional interactions
- ✅ **Long-term value** vs short-term optimization

---

## 📝 Implementation Checklist

### **Phase 1: Engine Creation** 🔲 Not Started

- [ ] Create `character_emotional_state_engine.py` (copy skeleton above)
- [ ] Implement `analyze_character_emotions()` method
- [ ] Implement `_query_bot_emotions_from_qdrant()` method
- [ ] Implement EMA calculation logic
- [ ] Implement trajectory analysis
- [ ] Write unit tests for engine
- [ ] Create Alembic migration for cache table
- [ ] Test migration on local database

### **Phase 2: Worker Integration** 🔲 Not Started

- [ ] Add engine to `enrichment/worker.py`
- [ ] Implement cache storage function
- [ ] Add to worker processing loop
- [ ] Test with 1 bot (Jake - simple personality)
- [ ] Verify cache table populated correctly
- [ ] Check processing time (<30 seconds per user)

### **Phase 3: Prompt Integration** 🔲 Not Started

- [ ] Add `_get_character_emotional_context()` to message processor
- [ ] Integrate with emotional intelligence component
- [ ] Test prompt injection with Elena bot
- [ ] Verify character self-awareness statements
- [ ] Validate cache retrieval performance (<5ms)

### **Phase 4: Testing & Validation** 🔲 Not Started

- [ ] Unit tests: Engine logic
- [ ] Integration tests: Worker → Cache → Prompt
- [ ] Performance tests: Cache retrieval latency
- [ ] Character tests: Emotional continuity per bot
- [ ] User tests: Discord feedback (1 week monitoring)

### **Phase 5: Production Rollout** 🔲 Not Started

- [ ] Deploy to staging (1-2 test bots)
- [ ] Monitor for 1 week
- [ ] Fix any issues discovered
- [ ] Roll out to all 12 bots
- [ ] Update documentation
- [ ] Mark roadmap as complete

---

## 🔗 Related Documents

- **Original Roadmap**: `CHARACTER_EMOTIONAL_STATE_FULL_SPECTRUM_REDESIGN.md`
- **EMA Implementation**: `EMOTIONAL_TRAJECTORY_SMOOTHING_EMA.md`
- **Pipeline Optimization**: `docs/optimization/PIPELINE_OPTIMIZATION_ROADMAP.md`
- **Orphaned v2 Code**: `src/intelligence/character_emotional_state_v2.py`
- **Removal Commit**: `efbf16d` (Oct 31, 2025)

---

## 🚀 Timeline

**Target: Q1 2026 (January-February)**

- Week 1: Engine creation + database migration
- Week 2: Worker integration + prompt integration
- Week 3: Testing and validation
- Week 4: Staging deployment and monitoring
- Week 5+: Production rollout

**Estimated Effort**: 2-3 weeks full-time (moderate complexity)

---

## 💡 Key Insights

1. **We already wrote this feature** - 707 lines of quality code sitting unused
2. **We removed it for the right reason** - 100-150ms is too much for real-time
3. **We forgot the enrichment option** - Background processing solves the performance problem
4. **The pattern already exists** - 9 other engines follow the same architecture
5. **The value is real** - Character emotional evolution enhances authenticity

---

## ✅ Approval & Commitment

**Status**: 📋 **COMMITTED TO ROADMAP**  
**Document Created**: October 31, 2025  
**Implementation Start**: Q1 2026  
**Owner**: TBD  
**Priority**: Medium (after critical features)

This document serves as the implementation guide for adding Character Emotional State
as the 10th Strategic Intelligence Engine. Code will be implemented following this
specification when development capacity allows.

---

**END OF DOCUMENT**
