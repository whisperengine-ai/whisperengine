# Holistic Knowledge Intelligence System

## 🎯 **Vision: From Single-Message Extraction to Knowledge Intelligence**

The enrichment worker enables a **paradigm shift** in how WhisperEngine understands users:

### **Before: Inline Single-Message Extraction**
```python
# In message_processor.py (Phase 9b)
# Problem: Analyzes ONE message at a time
await self._extract_user_facts(user_message)  # 200-500ms blocking LLM call

Result:
- Single message context: "I love pizza" → fact("loves", "pizza", confidence=0.7)
- No confirmation patterns
- No conflict detection
- No relationship building
- Blocks user response by 200-500ms
```

### **After: Conversation-Level Knowledge Intelligence**
```python
# In enrichment worker (background process)
# Analyzes 5-10 message WINDOWS for context
extracted_facts = await fact_extractor.extract_facts_from_conversation_window(
    messages=[5-10 messages],  # Conversation context!
    user_id=user_id,
    bot_name=bot_name
)

Result:
- Conversation context: "I love pizza" + "pepperoni is my favorite" + "I make my own dough"
  → fact("loves", "pepperoni pizza", confidence=0.95)
  → fact("has", "cooking skills", confidence=0.9)
  → relationship("pepperoni pizza" → "cooking skills")
- Confirmation patterns detected
- Conflicts identified and resolved
- Knowledge graph built
- Zero user-facing latency
```

---

## 🧠 **Core Intelligence Capabilities**

### **1. Conversation-Level Context Analysis**

**The Game Changer**: Analyze conversation windows, not individual messages

```python
# Example conversation window:
messages = [
    "User: I love pizza",
    "Bot: What's your favorite kind?",
    "User: Definitely pepperoni! I actually make my own dough",
    "Bot: That's impressive! How long have you been baking?",
    "User: Started during lockdown, now I do it every weekend"
]

# Inline extraction (old way):
Message 1: fact("loves", "pizza", confidence=0.7)
Message 3: fact("loves", "pepperoni", confidence=0.7)
Message 3: fact("makes", "pizza dough", confidence=0.6)
Message 5: fact("does", "baking", confidence=0.6)

# Enrichment extraction (new way):
Conversation analysis:
- fact("loves", "pepperoni pizza", confidence=0.95)
  ↳ confirmed across 2 messages with specificity
- fact("has", "cooking skills", confidence=0.9)
  ↳ inferred from "makes own dough" + "baking every weekend"
- fact("practices", "weekend baking", confidence=0.9)
  ↳ temporal pattern: "every weekend"
- relationship("pepperoni pizza" → "cooking skills" → "weekend baking")
  ↳ lifestyle pattern detected
```

### **2. Conflict Detection & Resolution**

**The Intelligence**: Identify contradictions and resolve them holistically

```python
# Conflict scenarios:

# Scenario 1: Direct contradiction
existing_fact = fact("loves", "cats", confidence=0.8, date="2024-01-15")
new_fact = fact("allergic_to", "cats", confidence=0.9, date="2024-10-15")

conflict = {
    'type': 'direct_contradiction',
    'resolution': 'keep_recent',
    'reasoning': 'User developed allergy - archive old preference'
}

# Scenario 2: Preference evolution
existing_fact = fact("dislikes", "coffee", confidence=0.7, date="2024-01-15")
new_fact = fact("loves", "coffee", confidence=0.9, date="2024-10-15")

conflict = {
    'type': 'preference_change',
    'resolution': 'track_evolution',
    'reasoning': 'Taste evolved - keep both with temporal context'
}

# Scenario 3: Temporal conflict
existing_fact = fact("lives_in", "NYC", confidence=0.9, date="2024-01-15")
new_fact = fact("lives_in", "LA", confidence=0.95, date="2024-10-15")

conflict = {
    'type': 'temporal_conflict',
    'resolution': 'update_with_history',
    'reasoning': 'User moved - archive old location, keep new'
}
```

### **3. Knowledge Graph Relationship Building**

**The Structure**: Connect facts to understand the user holistically

```python
# Knowledge graph connections:

# Semantic relationships
fact("loves", "hiking") + fact("loves", "camping") + fact("loves", "biking")
  → category("outdoor lifestyle", confidence=0.95)
  → relationship("hiking" ← "outdoor lifestyle" → "camping")

# Causal relationships  
fact("makes", "homemade pizza") + fact("has", "cooking skills")
  → relationship("homemade pizza" ← "caused_by" → "cooking skills")

# Hierarchical relationships
fact("plays", "guitar") 
  → category("musical skills")
  → category("artistic interests")
  → lifestyle_pattern("creative person")

# Temporal relationships
fact("started", "hiking", date="2024-03-01")
fact("moved_to", "Colorado", date="2024-02-15")
  → relationship("moved to Colorado" → "started hiking")
  → inference("move motivated by outdoor lifestyle")
```

### **4. Fact Organization & Classification**

**The Holistic View**: Organize facts for efficient retrieval and pattern detection

```python
organized_facts = {
    'preferences': [
        fact("loves", "pepperoni pizza", confidence=0.95),
        fact("prefers", "Italian food", confidence=0.85),
        fact("dislikes", "sushi", confidence=0.7)
    ],
    'skills': [
        fact("skilled_in", "cooking", confidence=0.9),
        fact("skilled_in", "baking", confidence=0.9),
        fact("learning", "pastry making", confidence=0.8)
    ],
    'lifestyle': [
        fact("practices", "weekend baking", confidence=0.9),
        fact("does", "meal prep", confidence=0.8)
    ],
    'goals': [
        fact("wants_to", "open bakery", confidence=0.7)
    ]
}

# Pattern detection:
culinary_pattern = {
    'preferences': 3 food facts,
    'skills': 3 cooking-related skills,
    'lifestyle': 2 cooking habits,
    'goals': 1 culinary aspiration,
    → INFERENCE: "User has strong culinary identity"
}
```

---

## 🚀 **Implementation Architecture**

### **Fact Extraction Engine** (`src/enrichment/fact_extraction_engine.py`)

```python
class FactExtractionEngine:
    """
    Conversation-level fact extraction with intelligence features
    """
    
    async def extract_facts_from_conversation_window(
        messages: List[Dict],  # 5-10 message window
        user_id: str,
        bot_name: str
    ) -> List[ExtractedFact]:
        """
        Extract facts with multi-message context
        
        Returns:
        - Higher confidence (multi-message confirmation)
        - Related facts (linked by context)
        - Temporal context (recent, long-term, past)
        - Reasoning (why this fact was extracted)
        """
    
    async def detect_fact_conflicts(
        new_facts: List[ExtractedFact],
        existing_facts: List[Dict]
    ) -> List[FactConflict]:
        """
        Detect conflicts between new and existing facts
        
        Types:
        - Direct contradiction (loves X vs hates X)
        - Preference evolution (changed over time)
        - Temporal conflict (location/ownership changes)
        """
    
    async def resolve_fact_conflicts(
        conflicts: List[FactConflict]
    ) -> List[Dict]:
        """
        Resolve conflicts intelligently
        
        Strategies:
        - Keep recent (for temporal facts)
        - Track evolution (for preferences)
        - Merge (for compatible facts)
        - Flag for review (unclear conflicts)
        """
    
    async def build_knowledge_graph_relationships(
        facts: List[ExtractedFact],
        user_id: str,
        bot_name: str
    ) -> List[Dict]:
        """
        Build semantic relationships between facts
        
        Relationships:
        - Semantic links (related entities)
        - Causal links (X causes Y)
        - Hierarchical (X belongs to category Y)
        - Temporal (X before Y)
        - Lifestyle patterns (multiple Xs = pattern Y)
        """
    
    async def organize_and_classify_facts(
        facts: List[ExtractedFact]
    ) -> Dict[str, List[ExtractedFact]]:
        """
        Organize facts into categories
        
        Categories:
        - preferences, skills, possessions
        - relationships, goals, experiences
        - lifestyle, habits
        """
```

### **Enrichment Worker Integration** (`src/enrichment/worker.py`)

```python
class EnrichmentWorker:
    async def _enrichment_cycle(self):
        """Process all bots"""
        for bot in bots:
            # 1. Conversation summaries (already implemented)
            await self._process_conversation_summaries(bot)
            
            # 2. Fact extraction with intelligence (NEW!)
            await self._process_fact_extraction(bot)
    
    async def _process_fact_extraction(self, bot_name: str):
        """
        Extract facts with full intelligence pipeline:
        1. Analyze conversation windows (5-10 messages)
        2. Detect conflicts with existing facts
        3. Resolve conflicts intelligently
        4. Build knowledge graph relationships
        5. Organize and classify facts
        6. Store in PostgreSQL (SAME tables as inline)
        """
        
        # Extract facts from conversations
        extracted_facts = await self.fact_extractor.extract_facts_from_conversation_window(
            messages=conversation_window,
            user_id=user_id,
            bot_name=bot_name
        )
        
        # Detect conflicts
        conflicts = await self.fact_extractor.detect_fact_conflicts(
            new_facts=extracted_facts,
            existing_facts=existing_facts
        )
        
        # Resolve conflicts
        if conflicts:
            resolutions = await self.fact_extractor.resolve_fact_conflicts(conflicts)
            await self._apply_conflict_resolutions(resolutions)
        
        # Build knowledge graph
        relationships = await self.fact_extractor.build_knowledge_graph_relationships(
            facts=extracted_facts,
            user_id=user_id,
            bot_name=bot_name
        )
        
        # Organize facts
        organized = await self.fact_extractor.organize_and_classify_facts(
            facts=extracted_facts
        )
        
        # Store in PostgreSQL (same tables!)
        await self._store_facts_in_postgres(
            facts=extracted_facts,
            relationships=relationships,
            user_id=user_id,
            bot_name=bot_name
        )
```

### **Database Schema** (UNCHANGED - Zero Breaking Changes!)

```sql
-- Same tables as inline extraction
CREATE TABLE user_facts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(255) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, bot_name, entity_name, relationship_type)
);

CREATE TABLE user_fact_relationships (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(255) NOT NULL,
    source_entity VARCHAR(255) NOT NULL,
    target_entity VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, bot_name, source_entity, target_entity, relationship_type)
);
```

**Key Point**: Enrichment worker uses SAME tables, so bots see facts from both inline AND enrichment extraction via `_get_user_facts_from_postgres()` unchanged!

---

## 📊 **Quality Comparison**

| Feature | Inline Extraction | Enrichment Intelligence |
|---------|------------------|------------------------|
| **Context** | Single message | 5-10 message window |
| **Confidence** | 0.6-0.7 (single source) | 0.85-0.95 (multi-source) |
| **Confirmation** | No pattern detection | Detects confirmation patterns |
| **Conflicts** | No detection | Identifies & resolves |
| **Relationships** | None | Full knowledge graph |
| **Organization** | Flat facts | Categorized & structured |
| **Model Quality** | GPT-3.5-turbo (fast) | Claude 3.5 Sonnet (quality) |
| **User Latency** | 200-500ms blocking | 0ms (background) |
| **Temporal Analysis** | No | Tracks evolution over time |
| **Meta-Facts** | No | Infers patterns & lifestyle |

### **Real Example: User Mentions Pizza**

**Conversation:**
```
User: I love pizza
Bot: What's your favorite kind?
User: Definitely pepperoni! I actually make my own dough
Bot: That's impressive!
User: Yeah, I've been baking every weekend since lockdown
```

**Inline Extraction** (old way):
```python
facts = [
    ("loves", "pizza", confidence=0.7),
    ("loves", "pepperoni", confidence=0.7),
    ("makes", "pizza dough", confidence=0.6),
    ("does", "baking", confidence=0.6)
]
# No relationships, no patterns, no confidence from confirmation
```

**Enrichment Intelligence** (new way):
```python
facts = [
    ExtractedFact(
        entity_name="pepperoni pizza",
        entity_type="food",
        relationship_type="loves",
        confidence=0.95,  # Confirmed across messages
        confirmation_count=3,
        related_facts=["homemade pizza", "cooking skills", "weekend baking"],
        temporal_context="long-term hobby (started lockdown, continues)",
        reasoning="User mentioned loving pizza, specified pepperoni, revealed making own dough with regular practice"
    ),
    ExtractedFact(
        entity_name="cooking skills",
        entity_type="skill",
        relationship_type="has",
        confidence=0.9,
        related_facts=["makes homemade pizza", "weekend baking"],
        reasoning="Inferred from 'makes own dough' + 'baking every weekend'"
    ),
    ExtractedFact(
        entity_name="weekend baking",
        entity_type="hobby",
        relationship_type="practices",
        confidence=0.9,
        temporal_context="regular habit (every weekend)",
        reasoning="Explicit mention of weekend frequency"
    )
]

relationships = [
    ("pepperoni pizza" → "cooking skills", type="requires", confidence=0.85),
    ("cooking skills" → "weekend baking", type="manifests_as", confidence=0.9),
    ("all three" → "culinary lifestyle", type="lifestyle_pattern", confidence=0.9)
]

categories = {
    'preferences': ["pepperoni pizza"],
    'skills': ["cooking skills"],
    'lifestyle': ["weekend baking"],
    'pattern': "culinary identity"
}
```

---

## 🎯 **Benefits**

### **1. Superior Quality**
- **0.95 confidence vs 0.7**: Multi-message confirmation
- **Richer facts**: "loves pepperoni pizza" vs "loves pizza"
- **Context aware**: Temporal patterns, lifestyle inference
- **Better models**: Claude 3.5 Sonnet (not time-critical)

### **2. Zero User-Facing Latency**
- **200-500ms faster responses**: No blocking LLM call
- **Background processing**: Runs independently
- **Same PostgreSQL tables**: Bots see all facts unchanged

### **3. Conflict Resolution**
- **Detects contradictions**: "loves X" vs "hates X"
- **Tracks evolution**: Preferences change over time
- **Resolves intelligently**: Keep recent, merge compatible, flag unclear

### **4. Knowledge Graph**
- **Semantic relationships**: Connect related facts
- **Lifestyle patterns**: Infer from multiple facts
- **Hierarchical organization**: Categories and subcategories
- **Temporal relationships**: Track causality over time

### **5. Holistic Understanding**
- **Pattern detection**: Multiple outdoor activities → "outdoor lifestyle"
- **Meta-facts**: Infer higher-level traits from patterns
- **Organization**: Categorized facts for efficient retrieval
- **Evolution tracking**: Understand how user changes over time

---

## 🚀 **Migration Path**

### **Phase 1: Enable Enrichment Worker** (DONE!)
```bash
# Already deployed and running
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d enrichment-worker
```

### **Phase 2: Add Feature Flag** (Next)
```python
# In .env files
ENABLE_INLINE_FACT_EXTRACTION=false  # Disable inline, use enrichment only

# In message_processor.py (Phase 9b)
if os.getenv("ENABLE_INLINE_FACT_EXTRACTION", "true") == "true":
    await self._extract_user_facts(user_message)  # Old way
else:
    # Enrichment worker handles it in background
    pass
```

### **Phase 3: Test with One Bot** (Recommended)
```bash
# Test with Jake (minimal personality complexity)
echo "ENABLE_INLINE_FACT_EXTRACTION=false" >> .env.jake
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart jake-bot

# Monitor:
# - Response times (expect 200-500ms improvement)
# - Fact quality (expect higher confidence scores)
# - Enrichment worker logs (facts being extracted)
```

### **Phase 4: Gradual Rollout**
```bash
# After 48-72 hours of Jake testing, expand to all bots
for bot in elena marcus dream gabriel sophia ryan dotty aetheris aethys; do
    echo "ENABLE_INLINE_FACT_EXTRACTION=false" >> .env.$bot
done

docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart
```

---

## 📈 **Future Enhancements**

### **Cross-User Pattern Detection**
```python
# Detect patterns across multiple users
pattern = detect_cross_user_pattern(
    fact_type="outdoor activities",
    users_with_pattern=["user1", "user2", "user3"]
)
# Result: "30% of users have outdoor lifestyle"
```

### **Fact Validation**
```python
# Validate facts against knowledge bases
validated_fact = await validate_fact(
    fact("lives_in", "Mars"),
    knowledge_base="world_locations"
)
# Result: confidence=0.01 (unlikely)
```

### **Proactive Fact Updates**
```python
# Bot suggests updates when facts seem outdated
if fact("works_at", "Company X", last_updated="2023-01-15"):
    bot.ask("Do you still work at Company X?")
```

### **Fact-Driven Conversations**
```python
# Use knowledge graph to drive conversations
if user.has_fact("loves", "hiking") and user.has_fact("lives_in", "Colorado"):
    bot.suggest("Have you hiked any 14ers?")  # Colorado-specific question
```

---

## 🎯 **Summary**

The enrichment worker transforms WhisperEngine from **single-message fact extraction** to **holistic knowledge intelligence**:

✅ **Conversation-level context** (5-10 message windows)  
✅ **Conflict detection & resolution** (handle contradictions)  
✅ **Knowledge graph relationships** (connect facts semantically)  
✅ **Fact organization & classification** (structured understanding)  
✅ **Superior quality** (0.95 confidence vs 0.7)  
✅ **Zero latency** (200-500ms faster responses)  
✅ **Zero breaking changes** (same PostgreSQL tables)  

**This is not just an optimization - it's a quality improvement that makes WhisperEngine understand users holistically!**
