# Phase 6.5 & 6.7 Data Storage Analysis
**Date**: October 15, 2025  
**Question**: What gets stored from Phase 6.5 (Bot Emotional State) and Phase 6.7 (Adaptive Learning)?  
**Answer**: Some data goes to persistent storage, some is prompt-only

---

## 🎯 QUICK ANSWER

**Phase 6.5 (Bot Emotional State)**:
- 🔍 **CURRENTLY RETRIEVES from Qdrant**: Past bot emotions from conversation metadata (last 10 responses)
- ⚠️ **SHOULD RETRIEVE from InfluxDB**: Missing query methods in TemporalIntelligenceClient
- ✅ **STORED in InfluxDB**: Bot emotion metrics (phase 7.5, after LLM response)
- ✅ **STORED in Qdrant**: Bot emotion in conversation metadata (phase 9)
- ❌ **NOT stored separately**: `bot_emotional_state` dict (ephemeral/prompt-only)

**Phase 6.7 (Adaptive Learning)**:
- 🔍 **RETRIEVES from PostgreSQL**: Current relationship scores from `relationship_scores` table
- ✅ **STORED in InfluxDB**: Confidence evolution, relationship progression (phase 11)
- ✅ **ALREADY in PostgreSQL**: Relationship scores updated by phase 11
- ❌ **NOT stored separately**: `relationship_state` and `conversation_confidence` dicts (ephemeral/prompt-only)

---

## 📊 PHASE 6.5: BOT EMOTIONAL SELF-AWARENESS

### **Data Source: InfluxDB (PRIMARY) with Qdrant Fallback**

✅ **IMPLEMENTATION COMPLETE**: Phase 6.5 now queries InfluxDB for bot emotion time-series as PRIMARY data source, with Qdrant as FALLBACK when InfluxDB unavailable.

**CURRENT IMPLEMENTATION** (InfluxDB PRIMARY with Qdrant fallback):

```python
# Phase 6.5: Query InfluxDB for bot's recent emotional responses
# Source: message_processor.py lines 4173-4230
async def _analyze_bot_emotional_trajectory(self, message_context: MessageContext):
    bot_name = get_normalized_bot_name_from_env()
    recent_emotions = []
    
    # PRIMARY: Try InfluxDB for chronological time-series
    if self.temporal_client and self.temporal_client.enabled:
        try:
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
                        'mixed_emotions': []
                    }
                    for e in influx_emotions[-10:]
                ]
                logger.debug("Retrieved %d bot emotions from InfluxDB", len(recent_emotions))
        except Exception as e:
            logger.debug("InfluxDB bot emotion query failed, falling back to Qdrant: %s", e)
    
    # FALLBACK: Use Qdrant semantic search if InfluxDB unavailable
    if not recent_emotions:
        bot_memory_query = f"emotional responses by {bot_name}"
        recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=message_context.user_id,
            query=bot_memory_query,
            limit=10
        )
        
        # Extract bot emotions from Qdrant conversation metadata
        for memory in recent_bot_memories:
            metadata = memory.get('metadata', {})
            bot_emotion = metadata.get('bot_emotion')
        
        logger.debug("Retrieved %d bot emotions from Qdrant (fallback)", len(recent_emotions))
```

**Why Dual Data Sources**:
- **InfluxDB (primary)**: Pure time-series, chronological order, complete emotion history
- **Qdrant (fallback)**: Semantic search, context-aware, always available
- **Hybrid approach**: Best of both worlds - time-series analysis when available, context-aware fallback when needed

### **What Gets Created**

```python
# Phase 6.5: Analyze bot's emotional trajectory from retrieved memories
bot_emotional_state = await self._analyze_bot_emotional_trajectory(message_context)

# Result: Ephemeral dict stored in ai_components (NOT persisted)
{
    'current_emotion': 'joy',           # Most recent bot emotion from Qdrant
    'current_intensity': 0.82,
    'current_mixed_emotions': [],
    'trajectory_direction': 'stable',    # intensifying/calming/stable
    'emotional_velocity': 0.05,          # Rate of emotional change
    'recent_emotions': ['joy', 'excitement', 'neutral', 'joy', 'surprise'],
    'emotional_context': 'joy and stable',
    'self_awareness_available': True
}
```

**Source**: Lines 4173-4273 in `message_processor.py`

### **Where It Goes**

#### **1. Used in Prompt Building (Phase 5)**
```python
# CDL integration uses bot_emotional_state for character-aware prompts
if bot_emotional_state:
    prompt += f"\n\nCURRENT EMOTIONAL STATE: You are feeling {bot_emotional_state['current_emotion']}"
    prompt += f" and your emotional trajectory is {bot_emotional_state['trajectory_direction']}."
```

**Purpose**: Enables bot self-awareness ("I've been feeling down lately")

#### **2. NOT Stored Directly**
- ❌ The `bot_emotional_state` dict itself is **NOT** stored in any database
- ❌ It's **ephemeral** - calculated per-message for prompt context only

#### **3. BUT: Bot Emotion IS Stored Later (Phase 7.5 & Phase 9)**

**Phase 7.5: After LLM Response**
```python
# Analyze bot's response emotion (Phase 7.5)
bot_emotion = await self._analyze_bot_emotion_with_shared_analyzer(response)
ai_components['bot_emotion'] = {
    'primary_emotion': 'joy',
    'intensity': 0.85,
    'confidence': 0.92,
    'mixed_emotions': [('excitement', 0.65)]
}
```

**Phase 9a: InfluxDB Storage** (Lines 662-677)
```python
# Record bot emotion to InfluxDB time-series
await self.temporal_client.record_bot_emotion(
    bot_name=bot_name,
    user_id=message_context.user_id,
    primary_emotion=bot_emotion.get('primary_emotion'),
    intensity=bot_emotion.get('intensity'),
    confidence=bot_emotion.get('confidence')
)
```

**Phase 9b: Qdrant Storage** (Lines 5495-5503)
```python
# Store bot emotion in Qdrant conversation metadata
bot_metadata = {}
if bot_emotion:
    bot_metadata['bot_emotion'] = bot_emotion

await self.memory_manager.store_conversation(
    user_id=message_context.user_id,
    user_message=message_context.content,
    bot_response=response,
    metadata=bot_metadata  # Bot emotion stored here
)
```

### **Data Flow Diagram: Bot Emotional State**

```
Phase 6.5: _analyze_bot_emotional_trajectory()
    ↓
    PRIMARY: Query InfluxDB for bot emotion time-series
    ↓
    If InfluxDB available:
        └→ temporal_client.get_bot_emotion_trend(bot_name, user_id, hours_back=24)
        └→ Returns chronological emotions from InfluxDB
    ↓
    FALLBACK: If InfluxDB unavailable or returns no data:
        └→ Query Qdrant for bot's past responses
        └→ Extract bot emotions from stored metadata
    ↓
    Calculate trajectory (intensifying/calming/stable)
    ↓
    Create bot_emotional_state dict
    ↓
    Store in ai_components['bot_emotional_state']
    ↓
    ┌─────────────────────────────────────┐
    │ USAGE: Prompt Building (Phase 5)   │
    │ - CDL character prompt injection    │
    │ - Bot self-awareness context        │
    │ - NOT stored in database            │
    └─────────────────────────────────────┘
    
Phase 7: LLM generates response
    ↓
Phase 7.5: _analyze_bot_emotion_with_shared_analyzer(response)
    ↓
    RoBERTa analyzes bot's actual response
    ↓
    Create bot_emotion dict (NEW analysis)
    ↓
    Store in ai_components['bot_emotion']
    ↓
    ┌─────────────────────────────────────┐
    │ STORAGE: Persistent Databases       │
    │ • InfluxDB: Time-series metrics     │
    │   └→ Queryable by Phase 6.5         │
    │ • Qdrant: Conversation metadata     │
    │   └→ Fallback for Phase 6.5         │
    └─────────────────────────────────────┘
```

---

## 📊 PHASE 6.7: ADAPTIVE LEARNING ENRICHMENT

### **Data Source: Retrieves from PostgreSQL**

**Phase 6.7 RETRIEVES relationship scores from PostgreSQL** (not InfluxDB):

```python
# Phase 6.7: Query PostgreSQL for current relationship state
# Source: message_processor.py lines 935-1023
async def _enrich_ai_components_with_adaptive_learning(...):
    # CRITICAL: This queries POSTGRESQL, not InfluxDB!
    scores = await self.relationship_engine._get_current_scores(
        user_id=message_context.user_id,
        bot_name=bot_name
    )
    
    # PostgreSQL query (src/relationships/evolution_engine.py:366-371):
    # SELECT trust, affection, attunement, interaction_count
    # FROM relationship_scores
    # WHERE user_id = $1 AND bot_name = $2
```

**Source**: `src/relationships/evolution_engine.py:354-395`

**Why PostgreSQL instead of InfluxDB?**
- **PostgreSQL**: Current state lookup ("What is trust RIGHT NOW?") - Single authoritative value
- **InfluxDB**: Historical trends ("How did trust change over time?") - Time-series data
- Phase 6.7 needs **current relationship state**, not historical time-series

### **What Gets Created**

```python
# Phase 6.7: Enrich AI components with relationship & confidence intelligence
await self._enrich_ai_components_with_adaptive_learning(
    message_context, ai_components, relevant_memories
)

# Result: Two ephemeral dicts added to ai_components (NOT persisted)
ai_components['relationship_state'] = {
    'trust': 0.72,                          # Retrieved from PostgreSQL
    'affection': 0.68,                      # Retrieved from PostgreSQL
    'attunement': 0.75,                     # Retrieved from PostgreSQL
    'interaction_count': 42,                # Retrieved from PostgreSQL
    'relationship_depth': 'strong_connection'  # Calculated (not stored)
}

ai_components['conversation_confidence'] = {
    'overall_confidence': 0.85,             # Calculated (not stored)
    'context_confidence': 0.78,             # Calculated (not stored)
    'emotional_confidence': 0.91            # Calculated (not stored)
}
```

**Source**: Lines 935-1023 in `message_processor.py`

### **Where It Goes**

#### **1. Retrieved from PostgreSQL (Not Created Fresh)**
```python
# Relationship scores retrieved from existing database
scores = await self.relationship_engine._get_current_scores(
    user_id=message_context.user_id,
    bot_name=bot_name
)

# These scores are ALREADY in PostgreSQL from previous conversations
# Phase 6.7 just RETRIEVES them for prompt injection
```

**Source Database**: PostgreSQL table `relationship_scores`

#### **2. Used in Prompt Building (Phase 4 & 5)**

**Phase 4: Context Building** (Lines 300-350 in MESSAGE_PIPELINE_INTELLIGENCE_FLOW.md)
```python
# Relationship Intelligence Component
relationship_content = (
    f"RELATIONSHIP STATE: "
    f"Trust={relationship_state['trust']:.2f}, "
    f"Affection={relationship_state['affection']:.2f}, "
    f"Attunement={relationship_state['attunement']:.2f}"
)
assembler.add_component(PromptComponent(
    type=PromptComponentType.RELATIONSHIP_CONTEXT,
    content=relationship_content,
    priority=4
))

# Confidence Intelligence Component  
confidence_content = (
    f"CONVERSATION CONFIDENCE: "
    f"Overall={confidence['overall_confidence']:.2f}"
)
assembler.add_component(PromptComponent(
    type=PromptComponentType.CONFIDENCE_CONTEXT,
    content=confidence_content,
    priority=6
))
```

**Phase 5: CDL Integration**
```python
# Character response adapts based on relationship depth
if trust_level > 0.8:
    # Deep relationship → More intimate language
    prompt += self._build_intimate_relationship_guidance(character_data)
else:
    # Building relationship → Cautious language
    prompt += self._build_building_relationship_guidance(character_data)
```

#### **3. NOT Stored Separately**
- ❌ The `relationship_state` dict is **NOT** stored again (already in PostgreSQL)
- ❌ The `conversation_confidence` dict is **NOT** stored (calculated per-message)
- ✅ But relationship scores ARE updated later (Phase 11)

#### **4. Relationship Scores Updated (Phase 11)**

**After Response Delivered**:
```python
# Phase 11: Update relationship scores based on conversation quality
update = await self.relationship_engine.calculate_dynamic_relationship_score(
    user_id=message_context.user_id,
    bot_name=self.character_name,
    conversation_quality=quality,
    emotion_data=ai_components.get('emotion_data')
)

# Update PostgreSQL
await self.relationship_engine._update_scores(update.new_scores)

# Record progression to InfluxDB
await self.temporal_client.record_relationship_progression(
    bot_name=self.character_name,
    user_id=message_context.user_id,
    relationship_metrics=update.new_scores
)
```

**Storage Locations**:
- ✅ **PostgreSQL**: Updated relationship scores (permanent state)
- ✅ **InfluxDB**: Relationship progression time-series (trend tracking)

### **Data Flow Diagram: Adaptive Learning**

```
Phase 6.7: _enrich_ai_components_with_adaptive_learning()
    ↓
    ┌───────────────────────────────────────────┐
    │ RETRIEVE from PostgreSQL:                 │
    │ • relationship_metrics table              │
    │   - trust, affection, attunement scores   │
    │   - interaction_count                     │
    └───────────────────────────────────────────┘
    ↓
    Create relationship_state dict
    ↓
    ┌───────────────────────────────────────────┐
    │ CALCULATE (not stored):                   │
    │ • conversation_confidence dict            │
    │   - Based on memory quality               │
    │   - Based on emotion clarity              │
    └───────────────────────────────────────────┘
    ↓
    Store both in ai_components
    ↓
    ┌─────────────────────────────────────────┐
    │ USAGE: Prompt Building (Phase 4 & 5)   │
    │ - Relationship context injection        │
    │ - Confidence calibration                │
    │ - Character intimacy adjustment         │
    │ - NOT stored in database                │
    └─────────────────────────────────────────┘
    
Phase 7: LLM generates response
    ↓
Phase 11: _update_relationship_scores()
    ↓
    Calculate new scores based on conversation quality
    ↓
    ┌─────────────────────────────────────────┐
    │ STORAGE: Persistent Databases           │
    │ • PostgreSQL: Updated relationship      │
    │   scores (permanent state)              │
    │ • InfluxDB: Relationship progression    │
    │   time-series (trend tracking)          │
    └─────────────────────────────────────────┘
```

---

## 🎯 SUMMARY: WHAT GETS STORED WHERE

| Phase | Data Created | Stored in DB? | Where? | Purpose |
|-------|-------------|--------------|--------|---------|
| **6.5** | `bot_emotional_state` | ❌ **NO** | Ephemeral (prompt-only) | Bot self-awareness in prompt |
| **7.5** | `bot_emotion` (response) | ✅ **YES** | InfluxDB + Qdrant | Permanent emotion tracking |
| **6.7** | `relationship_state` | ⚠️ **RETRIEVED** | PostgreSQL (existing) | Relationship context for prompt |
| **6.7** | `conversation_confidence` | ❌ **NO** | Ephemeral (prompt-only) | Confidence context for prompt |
| **11** | Updated relationship scores | ✅ **YES** | PostgreSQL + InfluxDB | Permanent relationship evolution |

---

## 🔍 KEY INSIGHTS

### **1. Phase 6.5/6.7 Are "Intelligence Retrievers", Not "Intelligence Storers"**

These phases **gather and prepare intelligence** for LLM prompt injection:
- **Retrieve**: Past bot emotions, relationship scores from databases
- **Calculate**: Emotional trajectories, confidence metrics (ephemeral)
- **Format**: For prompt injection (human-readable context)
- **Don't Store**: These specific dicts are NOT persisted

### **2. Actual Storage Happens in Phase 7.5, 9, and 11**

**Phase 7.5**: Analyze bot's actual response emotion → Store to InfluxDB  
**Phase 9**: Store full conversation → Qdrant (with bot emotion metadata)  
**Phase 11**: Update relationship scores → PostgreSQL + InfluxDB  

### **3. Why Not Store Phase 6.5/6.7 Dicts?**

**Redundant**: The data comes from databases that already store the source:
- `bot_emotional_state`: Derived from Qdrant stored `bot_emotion` values
- `relationship_state`: Retrieved from PostgreSQL `relationship_metrics`
- `conversation_confidence`: Calculated per-message (not a stable metric)

**Efficient**: Avoid duplicate storage of derived/calculated data

### **4. The "Intelligence Sandwich" Pattern**

```
RETRIEVAL PHASES (6.5, 6.7)
    ↓ Query existing databases
    ↓ Calculate ephemeral metrics
    ↓ Format for prompt
PROMPT PHASES (4, 5)
    ↓ Inject intelligence into LLM context
LLM GENERATION (7)
    ↓ Generate response using intelligence
STORAGE PHASES (7.5, 9, 11)
    ↓ Store NEW data generated from conversation
    ↓ Update existing metrics (relationships)
```

---

## 📊 COMPLETE STORAGE MAP FOR PHASES 6.5 - 11

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6.5: Bot Emotional Self-Awareness                    │
├─────────────────────────────────────────────────────────────┤
│ Created:  bot_emotional_state dict                         │
│ Source:   Qdrant (past bot_emotion metadata)               │
│ Stored:   ❌ NO (ephemeral, prompt-only)                   │
│ Purpose:  Enable bot self-awareness in responses           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6.7: Adaptive Learning Enrichment                    │
├─────────────────────────────────────────────────────────────┤
│ Created:  relationship_state dict                          │
│ Source:   PostgreSQL relationship_metrics table            │
│ Stored:   ⚠️ RETRIEVED (already in PostgreSQL)            │
│ Purpose:  Relationship context for character responses     │
│                                                             │
│ Created:  conversation_confidence dict                     │
│ Source:   Calculated from memory quality + emotions        │
│ Stored:   ❌ NO (ephemeral, per-message calculation)       │
│ Purpose:  Confidence calibration for certainty expressions │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: LLM Response Generation                           │
├─────────────────────────────────────────────────────────────┤
│ Uses:     bot_emotional_state (from 6.5)                   │
│ Uses:     relationship_state (from 6.7)                    │
│ Uses:     conversation_confidence (from 6.7)               │
│ Produces: Raw LLM response text                            │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7.5: Bot Emotion Analysis (RESPONSE EMOTION)         │
├─────────────────────────────────────────────────────────────┤
│ Created:  bot_emotion dict (NEW RoBERTa analysis)          │
│ Stored:   ✅ InfluxDB (time-series)                        │
│           - Measurement: bot_emotion                        │
│           - Fields: intensity, confidence                   │
│           - Tags: bot, user_id, emotion                     │
│ Purpose:  Track bot emotional consistency over time        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 9: Storage & Recording (PARALLEL)                    │
├─────────────────────────────────────────────────────────────┤
│ 9a: Qdrant Vector Memory                                   │
│     Stored:   ✅ Full conversation pair                    │
│               ✅ bot_emotion in metadata                   │
│               ✅ User emotion data                         │
│               ✅ Content/emotion/semantic vectors          │
│                                                             │
│ 9b: InfluxDB Temporal Recording                            │
│     Stored:   ✅ User emotion time-series                  │
│               ✅ Bot emotion time-series                   │
│               ✅ Confidence evolution                      │
│               ✅ Conversation quality metrics              │
│                                                             │
│ 9c: PostgreSQL Knowledge Extraction                        │
│     Stored:   ✅ Extracted facts                           │
│               ✅ Entity relationships                      │
│               ⚠️ Relationship scores NOT updated here     │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 11: Relationship Evolution                           │
├─────────────────────────────────────────────────────────────┤
│ Updated:  relationship scores (trust/affection/attunement) │
│ Stored:   ✅ PostgreSQL relationship_metrics table         │
│           - New score values                                │
│           - Interaction count incremented                   │
│                                                             │
│ Stored:   ✅ InfluxDB relationship_progression             │
│           - Measurement: relationship_progression           │
│           - Fields: trust_level, affection_level, etc.      │
│           - Tags: bot, user_id, session_id                  │
│ Purpose:  Track relationship evolution over time           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 DATA RETRIEVAL PATTERNS: Where Phase 6.5 & 6.7 Get Their Data

### **Phase 6.5: Bot Emotional Trajectory**

**Source**: **Qdrant Vector Memory**

```python
# Phase 6.5 queries Qdrant for bot's past emotional responses
# Location: message_processor.py:4173-4230

recent_bot_memories = await self.memory_manager.retrieve_relevant_memories(
    user_id=message_context.user_id,
    query=f"emotional responses by {bot_name}",
    limit=10  # Last 10 bot responses with emotion metadata
)

# Extracts from Qdrant payload:
for memory in recent_bot_memories:
    bot_emotion = memory['metadata']['bot_emotion']  # Stored by Phase 9
    # Contains: primary_emotion, intensity, confidence, mixed_emotions
```

**Why Qdrant?**
- ✅ Semantic search: "Find bot's emotional responses about specific topics"
- ✅ Vector similarity: Retrieves contextually relevant emotional history
- ✅ Metadata filtering: Can filter by emotion type, intensity, time range
- ❌ InfluxDB can't do semantic search (only time-series queries)

**What Gets Retrieved**:
- `primary_emotion`: joy, sadness, curiosity, etc.
- `intensity`: 0.0-1.0 emotion strength
- `confidence`: 0.0-1.0 RoBERTa detection certainty
- `mixed_emotions`: Secondary emotions detected

### **Phase 6.7: Relationship Context**

**Source**: **PostgreSQL `relationship_scores` Table**

```python
# Phase 6.7 queries PostgreSQL for current relationship state
# Location: message_processor.py:967, evolution_engine.py:354-395

scores = await self.relationship_engine._get_current_scores(
    user_id=message_context.user_id,
    bot_name=bot_name
)

# PostgreSQL query:
# SELECT trust, affection, attunement, interaction_count, last_updated, created_at
# FROM relationship_scores
# WHERE user_id = $1 AND bot_name = $2
```

**Why PostgreSQL?**
- ✅ State lookup: "What is the current relationship score RIGHT NOW?"
- ✅ Single authoritative value: One row per user-bot pair
- ✅ ACID transactions: Prevents race conditions during updates
- ❌ InfluxDB stores trends, not current state (would need "get latest" query)

**What Gets Retrieved**:
- `trust`: 0.0-1.0 trust level
- `affection`: 0.0-1.0 affection level
- `attunement`: 0.0-1.0 understanding/attunement level
- `interaction_count`: Total conversation count
- `last_updated`: When relationship was last modified

### **Summary: Retrieval vs Storage**

| Phase | Intended Source | Current Source | Stores To | Purpose |
|-------|----------------|----------------|-----------|---------|
| **Phase 6.5** | ❌ InfluxDB (missing methods) | ✅ Qdrant (bot_emotion metadata) | ❌ Nothing | Build bot emotional trajectory for prompt |
| **Phase 6.7** | ✅ PostgreSQL (relationship_scores) | ✅ PostgreSQL (relationship_scores) | ❌ Nothing | Load relationship context for prompt |
| **Phase 7.5** | N/A | ❌ Nothing (creates new data) | ✅ InfluxDB + Qdrant | Store bot's CURRENT emotion after generation |
| **Phase 9** | N/A | ❌ Nothing (stores conversation) | ✅ Qdrant + InfluxDB | Store full conversation with all metadata |
| **Phase 11** | N/A | ✅ PostgreSQL (reads current scores) | ✅ PostgreSQL + InfluxDB | Update relationship scores after conversation |

**Key Pattern**: Phase 6.5/6.7 are **READERS** (retrieve data for prompts), Phase 7.5/9/11 are **WRITERS** (store data for future retrieval).

**Implementation Note**: Phase 6.5 has a **missing InfluxDB query implementation** - methods `get_bot_emotion_trend()` and `get_bot_emotion_overall_trend()` are called by `CharacterTemporalEvolutionAnalyzer` but don't exist in `TemporalIntelligenceClient`. Current workaround uses Qdrant semantic search instead.

---

## 🎯 ANSWER TO YOUR QUESTION

> "what gets stored in phase 6.5 and 6.7? do we store anything in persistent storage for these phases?"

**Phase 6.5**: 
- 🔍 **RETRIEVES from Qdrant**: Past bot emotions from conversation metadata (last 10 responses)
- ❌ **NO persistent storage**: `bot_emotional_state` dict is ephemeral (prompt-only)

**Phase 6.7**: 
- 🔍 **RETRIEVES from PostgreSQL**: Current relationship scores from `relationship_scores` table
- ❌ **NO persistent storage**: `relationship_state` and `conversation_confidence` dicts are ephemeral (prompt-only)

**BUT**: The *source data* for these phases IS stored elsewhere:
- Bot emotions → Stored in **Phase 7.5** (InfluxDB) and **Phase 9** (Qdrant) ← Phase 6.5 retrieves from here
- Relationship scores → Stored in **Phase 11** (PostgreSQL + InfluxDB) ← Phase 6.7 retrieves from here

**Pattern**: Phases 6.5 and 6.7 are **intelligence retrievers** that prepare context for prompts. The actual **intelligence storage** happens in Phases 7.5, 9, and 11. This creates a **data loop**:

```
Conversation 1: Phase 7.5/11 STORE data → Database
                                           ↓
Conversation 2: Phase 6.5/6.7 RETRIEVE data → Prompt → LLM → Response
                                           ↓
Conversation 2: Phase 7.5/11 STORE NEW data → Database (loop continues)
```

---

**Related Documents**:
- `docs/architecture/PHASE_7_10_11_STORAGE_ANALYSIS.md` - Where Phase 7.5/10/11 store their data
- `docs/architecture/MESSAGE_PIPELINE_INTELLIGENCE_FLOW.md` - Complete pipeline overview
- `src/core/message_processor.py` - Implementation (lines 4173-4300 for Phase 6.5, lines 935-1023 for Phase 6.7)
