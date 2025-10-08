# CDL Graph Intelligence - Implementation Roadmap

**Created**: October 8, 2025  
**Updated**: October 8, 2025
**Status**: STEP 2 in progress (Cross-Pollination Enhancement)

---

## 🎯 Project Overview

**Goal**: Enhance CDL character knowledge with PostgreSQL graph intelligence, creating richer, more contextually-aware character responses.

**Architecture**: Build on existing WhisperEngine graph infrastructure (SemanticKnowledgeRouter for user facts) and extend to character personal knowledge (CharacterGraphManager).

**Design Philosophy**: 
- ✅ Keep it simple first, enhance progressively
- ✅ Personality-first - graph supports authenticity, doesn't override it
- ✅ No "Phase" or "Sprint" terminology - use clear STEP numbering

---

## 📋 Implementation Steps

### ✅ **Foundation Complete** (Pre-Step 1)

**Character Property Access** ✅
- Added 5 lazy-loading properties to SimpleCDLManager
- Docker database validation with 4 characters
- Personal knowledge extraction working

**CharacterGraphManager** ✅ 
- 712 lines, fully tested with real database
- Importance-weighted background queries
- Trigger-based memory activation
- Strength-weighted relationships
- Proficiency-filtered abilities
- Intent detection (9 query types)
- **All tests passed**: Jake, Aetheris, Aethys, Elena

---

### ✅ **STEP 1: Basic CDL Integration** (COMPLETE)

**Goal**: Replace direct property access with graph queries for personal knowledge extraction

**Files Modified**:
- `src/prompts/cdl_ai_integration.py` - Method: `_extract_cdl_personal_knowledge_sections()`

**Changes**:
```python
# BEFORE (direct property access):
if hasattr(character, 'backstory') and character.backstory:
    backstory = character.backstory
    if hasattr(backstory, 'family_background'):
        personal_sections.append(f"Family: {backstory.family_background}")

# AFTER (graph-aware query):
graph_result = await character_graph_manager.query_character_knowledge(
    character_name=character_name,
    query_text=message,
    intent=CharacterKnowledgeIntent.FAMILY
)
    
if graph_result.background:
    # Returns prioritized, importance-weighted results
    personal_sections.append(
        f"Family Background: {graph_result.background[0]['description']}"
    )
```

**✅ Results**: Character responses are now:
- Importance-weighted (most important information first)
- Trigger-based (memories activate on relevant keywords)
- Strength-weighted (strongest relationships emphasized)
- Contextually appropriate (filtered by intent)

---

### 🔨 **STEP 2: Cross-Pollination Enhancement** (IN PROGRESS)

**Goal**: Connect character knowledge with user facts for personalized responses

**Files Modified**:
- `src/characters/cdl/character_graph_manager.py`:
  - Added `semantic_router` parameter to constructor
  - Added `user_id` parameter to `query_character_knowledge()`
  - Implemented new `query_cross_pollination()` method with 3 sub-methods:
    - `_find_shared_interests()` - Character interests matching user facts
    - `_find_relevant_abilities()` - Character skills relevant to user interests
    - `_find_character_knowledge_about_user_facts()` - Character memories related to user topics

**New Capabilities**:
```python
# New cross-pollination method
async def query_cross_pollination(
    self,
    character_id: int,
    user_id: str,
    limit: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Cross-reference character knowledge with user facts.
    
    Enables:
    - Finding shared interests between character and user
    - Connecting character abilities to user mentioned entities
    - Discovering character knowledge relevant to user facts
    """
family_data = character.backstory.family_background if character.backstory else ""

# AFTER (graph intelligence):
result = await graph_manager.query_character_knowledge(
    character_name='elena',
    query_text='family background',
    intent=CharacterKnowledgeIntent.FAMILY,
    limit=3
)
# Returns: Importance-weighted background + triggered memories + relationships
```

**Scope**: 
- ✅ Keep simple - no user context yet
- ✅ No cross-pollination with user facts
- ✅ Just replace property access with graph queries

**Testing**:
- Personal knowledge extraction tests (existing)
- Discord message testing with character questions
- Validate graph results appear in responses

**Expected Outcome**:
```
User: "Elena, tell me about your family"
BEFORE: "Has supportive family" (one generic string)
AFTER: 3 importance-weighted family background entries + family relationships by strength
```

**Estimated Time**: 2-3 hours  
**Priority**: HIGH - Foundation for all other enhancements

---

### 🔗 **STEP 2: Cross-Pollination Enhancement**

**Goal**: Connect character knowledge with user facts for authentic relationship building

**Files to Modify**:
- `src/characters/cdl/character_graph_manager.py` - Add `query_with_user_context()` method

**Changes**:
```python
async def query_with_user_context(
    self,
    character_name: str,
    query_text: str,
    user_id: str,  # NEW
    semantic_router,  # NEW - access to user facts
    intent: Optional[CharacterKnowledgeIntent] = None
) -> CharacterKnowledgeResult:
    """
    Cross-reference character abilities/interests with user fact entities.
    
    Example: "Have you read any books I mentioned?"
    1. Get character's reading abilities/interests
    2. Get user's book entities from semantic router
    3. Find overlaps and return enriched response
    """
```

**Use Cases**:
- "Elena, have you read any books I mentioned?"
- "Jake, do you use any photography equipment I own?"
- "Marcus, have you heard of the AI companies I work with?"

**Database Queries**:
```sql
-- Find character abilities that match user fact entities
SELECT ca.ability_name, fe.entity_name, ufr.confidence
FROM character_abilities ca
JOIN user_fact_relationships ufr ON ca.character_id = $1 AND ufr.user_id = $2
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ca.ability_name ILIKE '%' || fe.entity_name || '%'
   OR fe.entity_name ILIKE '%' || ca.ability_name || '%'
ORDER BY ufr.confidence DESC
```

**Expected Outcome**:
```
User: "Elena, have you read any books I mentioned?"
Elena: "You mentioned 'The Soul of an Octopus' - I haven't read it yet, but it 
relates directly to my cephalopod intelligence research! I did read 'The Hidden 
Life of Trees' which you also mentioned. The interconnected communication systems 
reminded me of coral reef ecosystems."
```

**Estimated Time**: 4-5 hours  
**Priority**: HIGH - Highest impact enhancement  
**Dependencies**: Step 1 complete

**Next Tasks**:
- [ ] Integrate with CDL AI Integration to use cross-pollination results
- [ ] Test with real user facts from SemanticKnowledgeRouter
- [ ] Add unit tests for cross-pollination methods

---

### 🧠 **STEP 3: Memory Trigger Enhancement**

**Goal**: Activate character memories from user facts context, not just message keywords

**Files to Modify**:
- `src/characters/cdl/character_graph_manager.py` - Method: `_query_memories()`

**Changes**:
```python
async def _query_memories_with_user_triggers(
    self,
    character_id: int,
    keywords: List[str],
    user_facts: Optional[List[Dict]] = None  # NEW
) -> List[Dict]:
    """
    Trigger memories from:
    1. Direct query keywords (current)
    2. User fact entities (NEW - auto-activation)
    """
    
    # Extract user entity names as additional triggers
    if user_facts:
        user_triggers = [fact['entity_name'] for fact in user_facts]
        combined_keywords = keywords + user_triggers
    else:
        combined_keywords = keywords
    
    # Query with combined trigger set
    query = """
        SELECT title, description, emotional_impact, triggers
        FROM character_memories
        WHERE character_id = $1
          AND triggers && $2::TEXT[]  -- Array overlap
        ORDER BY importance_level DESC, emotional_impact DESC
        LIMIT $3
    """
```

**Use Cases**:
- User mentions "diving" in conversation → Elena's diving memories auto-trigger
- User mentions "photography" → Jake's photo expedition memories surface
- User discusses "stress" → Character's stress-related memories activate

**Expected Outcome**:
```
User: "I went diving last weekend at Catalina Island"
Elena: *diving memory auto-triggers*
"Catalina! I did my dissertation research there. The kelp forests are incredible - 
did you see the garibaldi? There's this particular reef at about 60 feet where I 
documented a stable octopus population."
```

**Estimated Time**: 3-4 hours  
**Priority**: HIGH - Creates "she just gets me" moments  
**Dependencies**: Step 1 complete

---

### 💙 **STEP 4: Emotional Context Synchronization**

**Goal**: Link user emotional patterns to character memories for authentic empathy

**Files to Modify**:
- `src/characters/cdl/character_graph_manager.py` - Add `get_emotionally_resonant_memories()`

**Changes**:
```python
async def get_emotionally_resonant_memories(
    self,
    character_name: str,
    user_emotional_context: str,  # From user facts: "stressed", "happy", "anxious"
    emotional_intensity: float  # From current message analysis
) -> List[Dict]:
    """
    Find character memories that emotionally resonate with user state.
    
    User stressed about work → Character's work stress memories
    User excited about achievement → Character's success memories
    User grieving → Character's loss/grief memories
    """
    
    # Map user emotions to character memory emotional_impact
    emotion_mapping = {
        "stressed": ["overwhelmed", "pressure", "deadline"],
        "happy": ["joy", "success", "achievement"],
        "anxious": ["nervous", "worried", "uncertain"],
        "sad": ["loss", "grief", "disappointment"]
    }
    
    # Query for matching emotional context
    query = """
        SELECT title, description, emotional_impact
        FROM character_memories
        WHERE character_id = $1
          AND emotional_impact >= $2  -- Match intensity threshold
          AND (
              description ILIKE ANY($3::TEXT[])  -- Emotion keywords
              OR emotional_context = $4
          )
        ORDER BY emotional_impact DESC
        LIMIT 3
    """
```

**Use Cases**:
- User: "Work has been really stressful" → Elena shares overwhelming deadline memory
- User: "I'm so excited about my promotion!" → Character shares achievement memory
- User: "I miss my grandmother" → Character shares loss/grief memory

**Expected Outcome**:
```
User: "Work has been really stressful lately"
Elena: *recognizes stress pattern*
"I hear you. I remember when I was preparing my dissertation defense - I was 
working 80-hour weeks, barely sleeping. The pressure felt overwhelming. What 
helped me was breaking things into smaller milestones. What's the biggest 
stressor right now?"
```

**Estimated Time**: 4-5 hours  
**Priority**: HIGH - Core to personality-first empathy  
**Dependencies**: Step 3 complete (memory trigger system)

---

### 🎯 **STEP 5: Proactive Context Injection**

**Goal**: Characters proactively inject relevant knowledge when user mentions topics

**Files to Create**:
- `src/characters/cdl/character_context_enhancer.py` - New class

**Architecture**:
```python
class CharacterContextEnhancer:
    """
    Detects topics in user messages and proactively injects 
    relevant character knowledge into system prompt.
    """
    
    async def detect_and_inject_context(
        self,
        user_message: str,
        character_name: str,
        base_system_prompt: str
    ) -> str:
        """
        1. Extract topics/entities from user message (diving, photography, etc.)
        2. Query CharacterGraphManager for matching background/abilities
        3. Calculate relevance scores
        4. Inject high-relevance context into system prompt
        
        Example:
        User mentions "diving" → Elena's diving research auto-injected
        User mentions "photography" → Jake's photo expertise auto-injected
        """
```

**Use Cases**:
- User mentions "diving" → Elena's background injected: "You're a marine biologist who researches coral reefs through diving"
- User mentions "photography" → Jake's expertise injected: "You're an adventure photographer with 15 years experience"
- User mentions "AI ethics" → Marcus's research injected: "You research AI safety and alignment"

**Expected Outcome**:
```
User: "I'm thinking about getting into underwater photography"
Elena: *diving + research background auto-injected into context*
"That's exciting! Underwater photography is how I document much of my research. 
The challenges are unique - you need to understand marine behavior, lighting in 
water, and equipment maintenance. I use a Canon in an Ikelite housing for my 
coral documentation. What draws you to underwater photography specifically?"
```

**Estimated Time**: 6-8 hours  
**Priority**: MEDIUM-HIGH - Powerful but complex  
**Dependencies**: Steps 1-4 complete

---

### 🎚️ **STEP 6: Confidence-Aware Conversations**

**Goal**: Characters use confidence scores from user facts for conversational nuance

**Files to Modify**:
- `src/prompts/cdl_ai_integration.py` - Enhance prompt building with confidence levels

**Changes**:
```python
async def build_confidence_aware_context(
    self,
    user_facts: List[Dict],
    confidence_threshold_high: float = 0.9,
    confidence_threshold_medium: float = 0.6
) -> str:
    """
    Format user facts with confidence-aware language:
    
    High confidence (0.9+): "The user loves pizza"
    Medium confidence (0.6-0.8): "The user mentioned liking pizza"
    Low confidence (<0.6): "The user may like pizza (unconfirmed)"
    """
    
    context_parts = []
    for fact in user_facts:
        confidence = fact['confidence']
        entity = fact['entity_name']
        
        if confidence >= confidence_threshold_high:
            context_parts.append(f"The user loves {entity} (high confidence)")
        elif confidence >= confidence_threshold_medium:
            context_parts.append(f"The user mentioned {entity} (medium confidence)")
        else:
            context_parts.append(f"The user may like {entity} (unconfirmed)")
```

**Use Cases**:
- High confidence: "I know you love pizza!" (mentioned 5+ times)
- Medium confidence: "I think you mentioned liking Thai food?" (mentioned once)
- Low confidence: "Do you like sushi?" (casual mention, unsure)

**Expected Outcome**:
```
User: "What should I eat for dinner?"
Elena: "Well, I know you love Italian food - pizza and pasta are your go-tos! 
I think you mentioned liking Thai food too, though I'm not as sure about that. 
Have you tried the new Thai place downtown?"
```

**Estimated Time**: 2-3 hours  
**Priority**: MEDIUM - Polish feature  
**Dependencies**: Step 2 complete (cross-pollination)

---

### ❓ **STEP 7: Intelligent Question Generation**

**Goal**: Characters ask follow-up questions based on knowledge gaps

**Files to Modify**:
- `src/prompts/cdl_ai_integration.py` - Add gap analysis and question generation

**Changes**:
```python
async def generate_curiosity_questions(
    self,
    user_id: str,
    character_name: str,
    semantic_router
) -> Optional[str]:
    """
    Analyze user facts for knowledge gaps and generate natural questions.
    
    Known: User loves marine biology (confidence 0.9)
    Unknown: How they learned about it, what aspect interests them
    Generate: "How did you get interested in marine biology?"
    """
    
    # Get high-confidence facts
    facts = await semantic_router.get_user_facts(user_id, limit=50)
    high_confidence_facts = [f for f in facts if f['confidence'] > 0.8]
    
    # For each fact, check for missing context
    gap_questions = []
    for fact in high_confidence_facts:
        entity = fact['entity_name']
        
        # Check if we know HOW they got interested
        origin_facts = [f for f in facts if 'learned' in f.get('relationship_type', '')]
        if not origin_facts:
            gap_questions.append(f"How did you get interested in {entity}?")
```

**Use Cases**:
- Known: User loves diving (0.9) → Unknown: Where they dive → "Where do you usually dive?"
- Known: User reads sci-fi (0.85) → Unknown: Favorite authors → "Who are your favorite sci-fi authors?"
- Known: User plays guitar (0.9) → Unknown: How long → "How long have you been playing guitar?"

**Expected Outcome**:
```
Elena: "I can tell you're really into marine biology - you light up when we 
discuss it! How did you first get interested in the ocean? Was it a childhood 
experience, or something that came later?"
```

**Estimated Time**: 5-6 hours  
**Priority**: MEDIUM - Adds conversational depth  
**Dependencies**: Steps 2 & 6 complete

---

### 🚀 **STEP 8: Database Performance Indexes**

**Goal**: Optimize graph query performance to sub-millisecond response times

**Files to Create**:
- `database/migrations/add_character_graph_indexes.sql`

**SQL Changes**:
```sql
-- GIN index for trigger array overlap queries
CREATE INDEX idx_character_memories_triggers 
ON character_memories USING GIN(triggers);

-- Trigram indexes for text similarity search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_character_background_description_trgm 
ON character_background USING GIN(description gin_trgm_ops);

-- Indexes for importance/strength/proficiency sorting
CREATE INDEX idx_character_background_importance 
ON character_background(character_id, importance_level DESC);

CREATE INDEX idx_character_relationships_strength 
ON character_relationships(character_id, relationship_strength DESC);

CREATE INDEX idx_character_abilities_proficiency 
ON character_abilities(character_id, proficiency_level DESC);

-- Composite index for filtered queries
CREATE INDEX idx_character_background_category_importance 
ON character_background(character_id, category, importance_level DESC);
```

**Performance Goals**:
- Background queries: <10ms
- Memory trigger queries: <15ms (GIN array overlap)
- Relationship queries: <10ms
- Ability queries: <10ms
- Overall graph query: <50ms total

**Testing**:
```bash
# Before indexes
EXPLAIN ANALYZE SELECT * FROM character_memories WHERE triggers && ARRAY['diving'];
# Seq Scan: 120ms

# After GIN index
# Index Scan: 2ms
```

**Estimated Time**: 2-3 hours  
**Priority**: MEDIUM - Performance optimization  
**Dependencies**: Step 1 complete (queries under load)

---

## 🔮 Optional Enhancements

### **OPTIONAL A: Multi-Character Knowledge Synthesis**

**Goal**: Correlate facts across characters for holistic user understanding

**Privacy Considerations**:
- Requires explicit user consent
- Toggle per character: "Allow Elena to know what I discuss with Jake"
- Default: OFF (strict privacy)

**Use Cases**:
- Elena knows user loves diving + Jake knows user loves photography → "underwater photographer"
- Marcus knows tech discussions + Sophia knows marketing → "works in tech marketing"

**Complexity**: HIGH - Privacy-sensitive feature  
**Priority**: LOW - Powerful but requires careful implementation

---

### **OPTIONAL B: Temporal Intelligence**

**Goal**: Track when character knowledge developed and evolved

**Schema Changes**:
```sql
ALTER TABLE character_background ADD COLUMN knowledge_date DATE;
ALTER TABLE character_memories ADD COLUMN memory_date DATE;
ALTER TABLE character_relationships ADD COLUMN relationship_start_date DATE;
ALTER TABLE character_abilities ADD COLUMN skill_acquired_date DATE;
```

**Use Cases**:
- "I've been researching coral reefs for 5 years, since 2020"
- "I learned underwater photography in 2022"
- "I've known Dr. Rodriguez for 10 years"

**Complexity**: LOW-MEDIUM - Schema changes + query updates  
**Priority**: LOW - Adds depth but not critical

---

## 📊 Success Metrics

### Quantitative
- **Query Performance**: <50ms for full character graph query
- **Cross-reference Hit Rate**: % of user questions that find character-user overlaps
- **Memory Activation Rate**: % of memories triggered by user facts vs keywords
- **Emotional Resonance**: % of responses matching user emotional context

### Qualitative
- **"She just gets me" moments**: Proactive memory sharing feels natural
- **Conversational depth**: Back-and-forth dialogue vs Q&A pattern
- **Emotional authenticity**: Empathy responses feel genuine
- **Knowledge richness**: Responses show deep character understanding

---

## 🎯 Recommended Implementation Order

### **Immediate** (This Week)
1. ✅ **STEP 1**: Basic CDL integration (2-3 hours)
2. ✅ **STEP 2**: Cross-pollination enhancement (4-5 hours)

### **Short-term** (Next Week)
3. ✅ **STEP 3**: Memory trigger enhancement (3-4 hours)
4. ✅ **STEP 4**: Emotional context sync (4-5 hours)
5. ✅ **STEP 8**: Database indexes (2-3 hours)

### **Medium-term** (Following Week)
6. ✅ **STEP 5**: Proactive context injection (6-8 hours)
7. ✅ **STEP 6**: Confidence-aware conversations (2-3 hours)
8. ✅ **STEP 7**: Question generation (5-6 hours)

### **Long-term** (Future)
9. ⏳ **OPTIONAL A**: Multi-character synthesis (if needed)
10. ⏳ **OPTIONAL B**: Temporal intelligence (if desired)

---

## 🚨 Design Principles (Maintain Throughout)

### 1. Personality-First Architecture
- ✅ Graph intelligence **supports** personality, doesn't override it
- ✅ Character authenticity > Data completeness
- ❌ Don't become a fact-retrieval bot

### 2. Progressive Enhancement
- ✅ Each step builds on previous foundations
- ✅ Can stop at any point and have working features
- ✅ No dependencies on future optional steps

### 3. Privacy and Isolation
- ✅ User fact access requires explicit parameters
- ✅ Cross-character synthesis requires user consent
- ✅ Bot-specific collections maintain boundaries

### 4. Testing Requirements
- ✅ Direct Python validation for each step
- ✅ Discord integration testing
- ✅ Real database validation with multiple characters

---

## 📝 Testing Checklist (Per Step)

### Basic Tests (Every Step)
- [ ] Direct Python validation script
- [ ] Unit tests for new methods
- [ ] Integration tests with real database
- [ ] Docker container testing

### Conversation Tests (Steps 1-7)
- [ ] Discord message testing with character questions
- [ ] Validate graph results appear in responses
- [ ] Check personality authenticity maintained
- [ ] Verify no semantic drift (invented content)

### Performance Tests (Step 8)
- [ ] Query execution time benchmarks
- [ ] Index usage validation (EXPLAIN ANALYZE)
- [ ] Load testing with concurrent queries

---

## 🎉 Expected Final Outcomes

### User Experience Before
```
User: "Elena, have you read any books I mentioned?"
Elena: "I enjoy reading marine biology books and scientific literature."
(Generic, no connection to user context)
```

### User Experience After (All Steps)
```
User: "Elena, have you read any books I mentioned?"
Elena: "You mentioned 'The Soul of an Octopus' - I haven't read it yet, but 
it sounds fascinating and relates directly to my cephalopod intelligence research! 
I did read 'The Hidden Life of Trees' which you also mentioned. The interconnected 
communication systems reminded me of coral reef ecosystems I study. Have you read 
'Lab Girl' by Hope Jahren? Based on your love of nature writing, I think you'd 
really enjoy it."

Features demonstrated:
✅ Cross-pollination (knows user's books)
✅ Character knowledge (cephalopod research)
✅ Emotional resonance (enthusiasm matching)
✅ Question generation (recommends based on user interests)
```

---

**Ready to begin STEP 1: Basic CDL Integration!**

**Next Action**: Integrate CharacterGraphManager with `cdl_ai_integration.py` to replace direct property access with graph queries.
