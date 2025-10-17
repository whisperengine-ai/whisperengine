# Character Learning Persistence - Implementation Plan

**Branch**: `feat/character-learning-persistence`  
**Date**: October 17, 2025  
**Estimated Duration**: 2-3 weeks  
**Status**: 🚧 IN PROGRESS

---

## 🎯 Goal

Implement the persistence layer for character learning moments, enabling characters to:
- Accumulate self-knowledge over time
- Reference learned insights in future conversations
- Track character evolution longitudinally
- Build self-knowledge graphs

---

## 📋 Implementation Phases

### ✅ **PHASE 0: Setup & Planning** (Day 1 - CURRENT)

**Tasks**:
- [x] Create feature branch `feat/character-learning-persistence`
- [x] Review design document (`CHARACTER_SELF_LEARNING_DESIGN.md`)
- [x] Create implementation plan
- [ ] Review existing detection system integration points
- [ ] Identify PostgreSQL connection patterns

**Deliverables**:
- Implementation roadmap (this document)
- Clear understanding of integration points

---

### 🔨 **PHASE 1: Database Schema** (Day 1-2)

**Goal**: Create PostgreSQL tables for character learning persistence

#### **Task 1.1: Create Alembic Migration**
```bash
alembic revision -m "add_character_learning_persistence_tables"
```

**Tables to Create**:

1. **`character_insights`** - Store discovered learning moments
   - Primary storage for persistent learning
   - Links to existing `characters` table
   - Supports confidence scoring and importance ranking
   
2. **`character_insight_relationships`** - Graph relationships between insights
   - Mirrors `user_fact_relationships` pattern
   - Enables self-knowledge graph traversal
   
3. **`character_learning_timeline`** - Temporal evolution tracking
   - Records character development over time
   - Captures before/after states

**File**: `alembic/versions/20251017_XXXX_add_character_learning_persistence_tables.py`

**Schema Design** (from CHARACTER_SELF_LEARNING_DESIGN.md):
```sql
CREATE TABLE character_insights (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    insight_content TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 0.5,
    discovery_date TIMESTAMP DEFAULT NOW(),
    conversation_context TEXT,
    importance_level INTEGER DEFAULT 5,
    emotional_valence FLOAT DEFAULT 0.0,
    triggers TEXT[],
    supporting_evidence TEXT[],
    user_id VARCHAR(255),  -- Which user triggered this learning
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(character_id, insight_content)
);

CREATE INDEX idx_character_insights_character_id ON character_insights(character_id);
CREATE INDEX idx_character_insights_type ON character_insights(insight_type);
CREATE INDEX idx_character_insights_confidence ON character_insights(confidence_score DESC);

CREATE TABLE character_insight_relationships (
    id SERIAL PRIMARY KEY,
    from_insight_id INTEGER REFERENCES character_insights(id) ON DELETE CASCADE,
    to_insight_id INTEGER REFERENCES character_insights(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    strength FLOAT DEFAULT 0.5,
    created_date TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_insight_id, to_insight_id, relationship_type)
);

CREATE INDEX idx_character_insight_relationships_from ON character_insight_relationships(from_insight_id);
CREATE INDEX idx_character_insight_relationships_to ON character_insight_relationships(to_insight_id);

CREATE TABLE character_learning_timeline (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    learning_event TEXT NOT NULL,
    learning_type VARCHAR(50) NOT NULL,
    before_state TEXT,
    after_state TEXT,
    trigger_conversation TEXT,
    user_id VARCHAR(255),
    learning_date TIMESTAMP DEFAULT NOW(),
    significance_score FLOAT DEFAULT 0.5
);

CREATE INDEX idx_character_learning_timeline_character_id ON character_learning_timeline(character_id);
CREATE INDEX idx_character_learning_timeline_date ON character_learning_timeline(learning_date DESC);
```

**Success Criteria**:
- [ ] Migration runs successfully
- [ ] Tables created with proper indexes
- [ ] Foreign key constraints working
- [ ] Test data insertion works

---

### 🧩 **PHASE 2: CharacterSelfInsightExtractor** (Day 3-4)

**Goal**: Convert detected learning moments into persistent insights

**File**: `src/characters/learning/character_self_insight_extractor.py`

**Core Responsibilities**:
1. Convert `LearningMoment` objects (from detector) → `CharacterInsight` database records
2. Extract metadata (confidence, triggers, evidence) from learning moments
3. Determine insight type and importance level
4. Handle deduplication (check for existing similar insights)

**Integration Point**: 
- Input: `LearningMoment` objects from `CharacterLearningMomentDetector`
- Output: Database-ready insight dictionaries

**Key Methods**:
```python
class CharacterSelfInsightExtractor:
    def __init__(self, postgres_pool):
        self.postgres_pool = postgres_pool
        
    async def extract_insights_from_learning_moments(
        self,
        learning_moments: List[LearningMoment],
        character_name: str,
        user_id: str,
        conversation_context: str
    ) -> List[CharacterInsight]:
        """Convert detected learning moments into persistent insights"""
        pass
    
    async def determine_insight_importance(
        self,
        moment: LearningMoment,
        existing_insights: List[CharacterInsight]
    ) -> int:
        """Calculate importance level (1-10) for insight"""
        pass
    
    async def extract_triggers_from_moment(
        self,
        moment: LearningMoment
    ) -> List[str]:
        """Extract keyword triggers that activate this insight"""
        pass
    
    async def check_for_similar_insights(
        self,
        character_id: int,
        insight_content: str,
        similarity_threshold: float = 0.85
    ) -> Optional[CharacterInsight]:
        """Check if similar insight already exists"""
        pass
```

**Success Criteria**:
- [ ] Successfully converts learning moments to insights
- [ ] Handles all 6 learning moment types
- [ ] Deduplication logic prevents duplicates
- [ ] Importance scoring is consistent
- [ ] Unit tests pass

---

### 💾 **PHASE 3: CharacterInsightStorage** (Day 5-6)

**Goal**: Database storage and retrieval for character insights

**File**: `src/characters/learning/character_insight_storage.py`

**Core Responsibilities**:
1. Store insights in PostgreSQL `character_insights` table
2. Retrieve relevant insights for character responses
3. Update insight confidence based on reinforcement
4. Build insight relationships (graph connections)

**Key Methods**:
```python
class CharacterInsightStorage:
    def __init__(self, postgres_pool):
        self.postgres_pool = postgres_pool
        
    async def store_insight(
        self,
        character_id: int,
        insight: CharacterInsight
    ) -> int:
        """Store insight in database, return insight_id"""
        pass
    
    async def get_relevant_insights(
        self,
        character_id: int,
        query_context: str,
        limit: int = 5,
        min_confidence: float = 0.6
    ) -> List[CharacterInsight]:
        """Retrieve insights relevant to conversation context"""
        pass
    
    async def update_insight_confidence(
        self,
        insight_id: int,
        reinforcement: float
    ):
        """Update confidence when insight is used/validated"""
        pass
    
    async def build_insight_relationship(
        self,
        from_insight_id: int,
        to_insight_id: int,
        relationship_type: str,
        strength: float = 0.5
    ):
        """Create relationship between two insights"""
        pass
    
    async def get_character_learning_timeline(
        self,
        character_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent character learning events"""
        pass
```

**Success Criteria**:
- [ ] Insights stored successfully
- [ ] Retrieval queries are performant (<50ms)
- [ ] Deduplication works (UNIQUE constraint)
- [ ] Relationships can be built and queried
- [ ] Integration tests pass

---

### 🔗 **PHASE 4: Message Processor Integration** (Day 7-8)

**Goal**: Connect detection → extraction → storage pipeline

**File**: `src/core/message_processor.py`

**Integration Points**:

#### **4.1: After Learning Moment Detection**
```python
# In _process_character_learning_moments() method
# CURRENT: Only stores in ai_components (temporary)
learning_moments_result = await self._process_character_learning_moments(...)

if learning_moments_result:
    ai_components['character_learning_moments'] = learning_moments_result
    
# NEW: Also persist to database
if learning_moments_result and learning_moments_result.get('moments'):
    await self._persist_learning_moments(
        learning_moments_result['moments'],
        message_context,
        conversation_context
    )
```

#### **4.2: New Method - Persist Learning Moments**
```python
async def _persist_learning_moments(
    self,
    learning_moments: List[LearningMoment],
    message_context: MessageContext,
    conversation_context: List[Dict[str, str]]
) -> bool:
    """Persist detected learning moments to database"""
    try:
        # Convert learning moments to insights
        insights = await self.insight_extractor.extract_insights_from_learning_moments(
            learning_moments=learning_moments,
            character_name=get_normalized_bot_name_from_env(),
            user_id=message_context.user_id,
            conversation_context=str(conversation_context)
        )
        
        # Store in database
        for insight in insights:
            await self.insight_storage.store_insight(
                character_id=self.character_id,
                insight=insight
            )
        
        logger.info("💾 PERSISTENCE: Stored %d character insights", len(insights))
        return True
        
    except Exception as e:
        logger.error("Failed to persist learning moments: %s", e)
        return False
```

**Success Criteria**:
- [ ] Learning moments automatically persisted
- [ ] No performance impact on message processing
- [ ] Error handling prevents message failures
- [ ] Logging provides visibility

---

### 🎭 **PHASE 5: CDL Prompt Integration** (Day 9-10)

**Goal**: Include learned insights in character system prompts

**File**: `src/prompts/cdl_ai_integration.py`

**Integration Point**: In `create_character_aware_prompt()` method

#### **Current Flow**:
```python
# Gets static CDL knowledge from database
background = await self.character_graph_manager.query_character_knowledge(...)
```

#### **Enhanced Flow**:
```python
# Get static CDL knowledge
background = await self.character_graph_manager.query_character_knowledge(...)

# Get learned insights (NEW)
if self.insight_storage:
    learned_insights = await self.insight_storage.get_relevant_insights(
        character_id=character_id,
        query_context=message_content,
        limit=3,
        min_confidence=0.7
    )
    
    if learned_insights:
        insight_guidance = self._format_learned_insights(learned_insights)
        # Add to system prompt guidance section
```

#### **Prompt Formatting**:
```python
def _format_learned_insights(
    self,
    insights: List[CharacterInsight]
) -> str:
    """Format learned insights for system prompt"""
    if not insights:
        return ""
    
    guidance = "\n🧠 **CHARACTER SELF-AWARENESS** (Learned Insights):\n"
    for insight in insights:
        guidance += f"- {insight.insight_type}: {insight.insight_content}\n"
        guidance += f"  (Confidence: {int(insight.confidence_score * 100)}%, "
        guidance += f"Learned: {insight.discovery_date.strftime('%b %d')})\n"
    
    return guidance
```

**Success Criteria**:
- [ ] Learned insights appear in system prompts
- [ ] Character responses reference learned knowledge
- [ ] Natural integration with CDL personality
- [ ] Testing shows character memory persistence

---

### 🧪 **PHASE 6: Testing & Validation** (Day 11-13)

**Goal**: Comprehensive testing of persistence system

#### **6.1: Unit Tests**
**File**: `tests/automated/test_character_learning_persistence.py`

Tests:
- [ ] Insight extraction from learning moments
- [ ] Database storage and retrieval
- [ ] Deduplication logic
- [ ] Confidence updating
- [ ] Relationship building

#### **6.2: Integration Tests**
**File**: `tests/automated/test_character_learning_integration.py`

Tests:
- [ ] End-to-end: detection → extraction → storage → retrieval
- [ ] Message processor integration
- [ ] CDL prompt integration
- [ ] Performance benchmarks

#### **6.3: Manual Testing**
**Procedure**:
```bash
# 1. Start Elena bot
./multi-bot.sh bot elena

# 2. Have conversation triggering learning moments
# User: "I love quantum physics!"
# Elena: "I've noticed you light up when we discuss quantum mechanics"

# 3. Check database
psql -U whisperengine -d whisperengine -h localhost -p 5433
SELECT * FROM character_insights WHERE character_id = (SELECT id FROM characters WHERE name = 'Elena Rodriguez');

# 4. Continue conversation next day
# User: "Tell me about string theory"
# Elena: "Remember how excited you were about quantum physics? String theory connects to that!"
```

**Success Criteria**:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing shows persistence working
- [ ] Performance acceptable (<100ms added to message processing)

---

### 📊 **PHASE 7: Monitoring & Metrics** (Day 14)

**Goal**: Add observability for character learning

#### **7.1: InfluxDB Metrics**
**File**: `src/temporal/temporal_intelligence_client.py`

Add measurements:
- `character_learning_storage` - Storage operations and success rates
- `character_insight_retrieval` - Query performance
- `character_learning_timeline` - Learning event tracking

#### **7.2: Logging Enhancements**
Key log events:
- `💾 PERSISTENCE: Stored N character insights`
- `🧠 RETRIEVAL: Retrieved N learned insights for prompt`
- `🎯 LEARNING: Character self-knowledge updated`

**Success Criteria**:
- [ ] Metrics tracking learning activity
- [ ] Logs provide debugging visibility
- [ ] Dashboard shows character learning stats

---

### 📝 **PHASE 8: Documentation** (Day 15)

**Goal**: Document the persistence system

**Documents to Create/Update**:
- [ ] `docs/features/CHARACTER_LEARNING_PERSISTENCE.md` - System overview
- [ ] `docs/architecture/CHARACTER_LEARNING_ARCHITECTURE.md` - Technical details
- [ ] Update `CHARACTER_LEARNING_ROADMAP_STATUS.md` - Mark Phase 6 complete
- [ ] Update `.github/copilot-instructions.md` - Note persistence system
- [ ] Update `README.md` - Mention character learning capabilities

**Success Criteria**:
- [ ] Complete system documentation
- [ ] Architecture diagrams
- [ ] Usage examples
- [ ] Migration guide

---

## 🎯 Success Metrics

### **Functional Requirements**:
- [x] Characters can accumulate self-knowledge over time
- [ ] Learned insights appear in character responses naturally
- [ ] Character evolution trackable via timeline
- [ ] No duplicate insights stored

### **Performance Requirements**:
- [ ] Storage adds <50ms to message processing
- [ ] Retrieval queries complete in <50ms
- [ ] No impact on existing response quality

### **Quality Requirements**:
- [ ] All tests passing (unit + integration)
- [ ] Code review approved
- [ ] Documentation complete

---

## 🚧 Current Status Tracking

### **Completed** ✅:
- [x] Branch created
- [x] Implementation plan created

### **In Progress** 🔨:
- [ ] Database schema design
- [ ] Integration point analysis

### **Pending** 📋:
- Everything else!

---

## 📁 Files to Create/Modify

### **New Files**:
1. `alembic/versions/20251017_XXXX_add_character_learning_persistence_tables.py`
2. `src/characters/learning/character_self_insight_extractor.py`
3. `src/characters/learning/character_insight_storage.py`
4. `tests/automated/test_character_learning_persistence.py`
5. `tests/automated/test_character_learning_integration.py`
6. `docs/features/CHARACTER_LEARNING_PERSISTENCE.md`

### **Files to Modify**:
1. `src/core/message_processor.py` - Add persistence after detection
2. `src/prompts/cdl_ai_integration.py` - Include learned insights in prompts
3. `src/core/bot.py` - Initialize insight storage components
4. `docs/reports/CHARACTER_LEARNING_ROADMAP_STATUS.md` - Update status

---

## 🎯 Next Immediate Actions

### **Day 1 - Today**:
1. [x] Create branch ✅
2. [x] Create implementation plan ✅
3. [ ] Review existing PostgreSQL connection patterns
4. [ ] Review `user_facts` table schema for pattern matching
5. [ ] Start alembic migration file

### **Day 2**:
1. [ ] Complete database migration
2. [ ] Test migration with sample data
3. [ ] Start CharacterSelfInsightExtractor implementation

---

**Status**: 📋 READY TO START IMPLEMENTATION  
**Next Action**: Review PostgreSQL patterns and create alembic migration  
**Target Completion**: November 1, 2025 (2 weeks)
