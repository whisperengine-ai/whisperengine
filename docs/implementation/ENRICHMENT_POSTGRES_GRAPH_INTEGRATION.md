# Enrichment Worker PostgreSQL Graph Integration

## 🎯 Purpose

Ensure the enrichment worker fully leverages WhisperEngine's **PostgreSQL graph features** for user facts, matching (and enhancing) the capabilities of inline fact extraction.

---

## 📊 PostgreSQL Graph Schema (Current State)

### **Tables:**

1. **`fact_entities`** - Core entity storage
   - Stores entities users can relate to (foods, hobbies, places, etc.)
   - Full-text search with `tsvector`
   - Trigram similarity matching (pg_trgm)
   - JSONB attributes for flexible metadata

2. **`user_fact_relationships`** - Knowledge graph core
   - User → Entity relationships ("User likes Pizza")
   - Confidence scores (0-1)
   - Emotional context
   - Character awareness (mentioned_by_character)
   - **JSONB `related_entities` array** for graph traversal

3. **`entity_relationships`** - Entity → Entity edges
   - Graph edges between entities
   - Relationship types: `similar_to`, `part_of`, `category_of`, `related_to`, `opposite_of`, `requires`
   - Weight scores (0-1)
   - Bidirectional support
   - Used for: semantic similarity, category hierarchies, concept relationships

4. **`character_interactions`** - Character-aware tracking
   - Which characters mentioned which entities
   - Interaction types (conversation, fact_mention, education, etc.)
   - JSONB `entity_references` array

### **Graph Features:**

- ✅ **Trigram similarity**: Auto-discover similar entities (pg_trgm)
- ✅ **Full-text search**: tsvector for entity search
- ✅ **Graph traversal**: entity_relationships for 1-2 hop queries
- ✅ **Character awareness**: Track which character learned each fact
- ✅ **Emotional context**: Link facts to emotional states
- ✅ **JSONB flexibility**: Attributes and metadata as JSON

---

## 🔄 Current Enrichment Worker Implementation

### ✅ **What We're Already Doing:**

1. **Correct schema usage**:
   ```python
   # fact_entities table
   entity_id = await conn.fetchval("""
       INSERT INTO fact_entities (entity_type, entity_name, attributes)
       VALUES ($1, $2, $3)
       ON CONFLICT (entity_type, entity_name) DO UPDATE ...
   """)
   
   # user_fact_relationships table
   await conn.execute("""
       INSERT INTO user_fact_relationships 
       (user_id, entity_id, relationship_type, confidence, ...)
       VALUES ($1, $2, $3, $4, ...)
   """)
   ```

2. **Conflict detection** (opposing relationships):
   ```python
   # Matches semantic_router.py logic
   await self._detect_opposing_relationships_inline_style(...)
   ```

3. **Trigram similarity** (auto-discover similar entities):
   ```python
   # Auto-discover similar entities using trigram similarity
   similar_entities = await conn.fetch("""
       SELECT id, entity_name, similarity(entity_name, $1) as sim_score
       FROM fact_entities
       WHERE entity_type = $2 AND id != $3
       AND similarity(entity_name, $1) > 0.3
       ORDER BY sim_score DESC LIMIT 5
   """)
   ```

4. **Entity relationships** (graph edges):
   ```python
   # Create entity relationships for similar entities
   await conn.execute("""
       INSERT INTO entity_relationships 
       (from_entity_id, to_entity_id, relationship_type, weight)
       VALUES ($1, $2, 'similar_to', $3)
   """)
   ```

---

## ❌ **What We're MISSING (Graph Features):**

### **1. related_entities JSONB Array in user_fact_relationships**

**Current State:** NOT populated  
**Schema:** `related_entities JSONB DEFAULT '[]'`  
**Purpose:** Store graph relationships directly in user_fact_relationships for fast traversal

**Example:**
```json
{
  "related_entities": [
    {"entity_id": "uuid-1", "relation": "similar_to", "weight": 0.8},
    {"entity_id": "uuid-2", "relation": "part_of", "weight": 0.9}
  ]
}
```

### **2. context_metadata JSONB in user_fact_relationships**

**Current State:** NOT populated  
**Schema:** `context_metadata JSONB DEFAULT '{}'`  
**Purpose:** Rich metadata from conversation-level analysis

**Example:**
```json
{
  "confirmation_count": 3,
  "related_facts": ["homemade pizza", "weekend baking"],
  "temporal_context": "long-term preference",
  "reasoning": "User mentioned across multiple conversations",
  "source_messages": ["msg1", "msg2", "msg3"],
  "extraction_method": "enrichment_worker",
  "extracted_at": "2024-10-19T..."
}
```

### **3. character_interactions Tracking**

**Current State:** NOT populated  
**Purpose:** Track which character learned each fact for character-aware responses

**Example:**
```sql
INSERT INTO character_interactions (
  user_id, character_name, interaction_type,
  entity_references, emotional_tone, metadata
) VALUES (
  'user123', 'elena', 'fact_mention',
  '["pizza", "cooking skills", "weekend baking"]',
  'excited', '{"extraction_method": "enrichment_worker"}'
)
```

### **4. Hierarchical Relationships (part_of, category_of)**

**Current State:** Only using `similar_to`  
**Missing:** Category hierarchy relationships

**Example:**
```python
# Pizza → Italian Food (category_of)
# Hiking → Outdoor Activities (part_of)
# Guitar → Musical Skills (category_of)
await conn.execute("""
    INSERT INTO entity_relationships 
    (from_entity_id, to_entity_id, relationship_type, weight)
    VALUES ($1, $2, 'category_of', 0.9)
""")
```

### **5. Bidirectional Relationships**

**Current State:** NOT using `bidirectional` flag  
**Missing:** Mark symmetric relationships

**Example:**
```python
# "similar_to" is bidirectional
await conn.execute("""
    INSERT INTO entity_relationships 
    (from_entity_id, to_entity_id, relationship_type, weight, bidirectional)
    VALUES ($1, $2, 'similar_to', $3, true)
""")
```

---

## 🚀 **Enhancement Plan**

### **Phase 1: Complete Current Graph Features**

#### **1.1 Populate context_metadata JSONB**

```python
# In _store_facts_in_postgres()
context_metadata = {
    'confirmation_count': fact.confirmation_count,
    'related_facts': fact.related_facts,
    'temporal_context': fact.temporal_context,
    'reasoning': fact.reasoning,
    'source_messages': fact.source_messages,
    'extraction_method': 'enrichment_worker',
    'extracted_at': datetime.utcnow().isoformat(),
    'conversation_window_size': len(messages),  # How many messages analyzed
    'multi_message_confirmed': fact.confirmation_count > 1
}

await conn.execute("""
    INSERT INTO user_fact_relationships 
    (user_id, entity_id, relationship_type, confidence, 
     emotional_context, mentioned_by_character, context_metadata)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (user_id, entity_id, relationship_type)
    DO UPDATE SET
        confidence = GREATEST(user_fact_relationships.confidence, $4),
        context_metadata = user_fact_relationships.context_metadata || $7,
        updated_at = NOW()
""", user_id, entity_id, fact.relationship_type, fact.confidence,
     emotional_context, bot_name, json.dumps(context_metadata))
```

#### **1.2 Populate related_entities JSONB Array**

```python
# After storing fact, update related_entities array
related_entities_array = []
for related_fact in fact.related_facts:
    # Find related entity ID
    related_entity_id = await conn.fetchval("""
        SELECT id FROM fact_entities 
        WHERE entity_name = $1
    """, related_fact)
    
    if related_entity_id:
        related_entities_array.append({
            'entity_id': str(related_entity_id),
            'relation': 'semantic_link',
            'weight': 0.8
        })

# Update user_fact_relationships with related_entities
await conn.execute("""
    UPDATE user_fact_relationships
    SET related_entities = $1
    WHERE user_id = $2 AND entity_id = $3 AND relationship_type = $4
""", json.dumps(related_entities_array), user_id, entity_id, fact.relationship_type)
```

#### **1.3 Add character_interactions Tracking**

```python
# After storing facts, log character interaction
entity_names = [fact.entity_name for fact in facts]

await conn.execute("""
    INSERT INTO character_interactions (
        user_id, character_name, interaction_type,
        entity_references, emotional_tone, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6)
""", user_id, bot_name, 'fact_mention',
     json.dumps(entity_names),
     'analytical',  # Enrichment worker tone
     json.dumps({
         'extraction_method': 'enrichment_worker',
         'facts_extracted': len(facts),
         'conversation_window_size': len(messages),
         'extracted_at': datetime.utcnow().isoformat()
     }))
```

#### **1.4 Add Hierarchical Relationships**

```python
# In build_knowledge_graph_relationships()
# Detect hierarchical relationships

# Category relationships
category_mappings = {
    'food': {
        'pizza': 'italian_food',
        'pasta': 'italian_food',
        'sushi': 'japanese_food',
        'hiking': 'outdoor_activities',
        'camping': 'outdoor_activities',
        'guitar': 'musical_skills',
        'piano': 'musical_skills'
    }
}

for fact in facts:
    if fact.entity_type in category_mappings:
        category = category_mappings[fact.entity_type].get(fact.entity_name.lower())
        if category:
            # Create category entity if doesn't exist
            category_entity_id = await conn.fetchval("""
                INSERT INTO fact_entities (entity_type, entity_name, category)
                VALUES ('category', $1, $2)
                ON CONFLICT (entity_type, entity_name) DO UPDATE SET updated_at = NOW()
                RETURNING id
            """, category, fact.entity_type)
            
            # Create "part_of" relationship
            await conn.execute("""
                INSERT INTO entity_relationships 
                (from_entity_id, to_entity_id, relationship_type, weight, bidirectional)
                VALUES ($1, $2, 'part_of', 0.9, false)
                ON CONFLICT DO NOTHING
            """, entity_id, category_entity_id)
```

#### **1.5 Mark Bidirectional Relationships**

```python
# Update similar_to relationships to be bidirectional
await conn.execute("""
    INSERT INTO entity_relationships 
    (from_entity_id, to_entity_id, relationship_type, weight, bidirectional)
    VALUES ($1, $2, 'similar_to', $3, true)
    ON CONFLICT (from_entity_id, to_entity_id, relationship_type) 
    DO UPDATE SET bidirectional = true
""", entity_id, similar["id"], min(float(similar["sim_score"]), 0.9))
```

---

### **Phase 2: Leverage Graph Features for Fact Extraction**

#### **2.1 Use Graph Traversal for Related Facts**

```python
# When extracting facts, query graph for related entities
async def _get_related_entities_from_graph(
    self,
    conn,
    entity_id: int,
    max_hops: int = 2
) -> List[str]:
    """
    Use PostgreSQL graph to find related entities via traversal.
    """
    related = await conn.fetch("""
        WITH RECURSIVE entity_graph AS (
            -- Start with direct relationships
            SELECT 
                er.to_entity_id as entity_id,
                er.relationship_type,
                er.weight,
                1 as hop_count
            FROM entity_relationships er
            WHERE er.from_entity_id = $1
            
            UNION
            
            -- Traverse to 2nd hop (if bidirectional or forward)
            SELECT 
                er.to_entity_id as entity_id,
                er.relationship_type,
                er.weight,
                eg.hop_count + 1
            FROM entity_graph eg
            JOIN entity_relationships er ON eg.entity_id = er.from_entity_id
            WHERE eg.hop_count < $2
        )
        SELECT DISTINCT fe.entity_name, eg.relationship_type, eg.weight
        FROM entity_graph eg
        JOIN fact_entities fe ON eg.entity_id = fe.id
        ORDER BY eg.weight DESC, eg.hop_count ASC
        LIMIT 10
    """, entity_id, max_hops)
    
    return [row['entity_name'] for row in related]
```

#### **2.2 Use Full-Text Search for Entity Classification**

```python
# Use tsvector for better entity type classification
async def _classify_entity_using_fulltext(
    self,
    conn,
    entity_name: str
) -> str:
    """
    Use PostgreSQL full-text search to classify entity type.
    """
    # Find similar entities using search_vector
    matches = await conn.fetch("""
        SELECT entity_type, 
               ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM fact_entities
        WHERE search_vector @@ plainto_tsquery('english', $1)
        ORDER BY rank DESC
        LIMIT 5
    """, entity_name)
    
    if matches:
        # Most common entity_type among top matches
        type_counts = {}
        for match in matches:
            entity_type = match['entity_type']
            type_counts[entity_type] = type_counts.get(entity_type, 0) + match['rank']
        
        return max(type_counts.items(), key=lambda x: x[1])[0]
    
    return 'other'
```

---

## 📊 **Implementation Checklist**

### **✅ Phase 1: Complete Graph Features (Priority 1)**

- [x] Use fact_entities and user_fact_relationships tables (DONE)
- [x] Conflict detection with opposing relationships (DONE)
- [x] Trigram similarity for similar entities (DONE)
- [x] Create entity_relationships for similar_to (DONE)
- [ ] **Populate context_metadata JSONB** (MISSING)
- [ ] **Populate related_entities JSONB array** (MISSING)
- [ ] **Track character_interactions** (MISSING)
- [ ] **Add hierarchical relationships** (part_of, category_of) (MISSING)
- [ ] **Mark bidirectional relationships** (MISSING)

### **⏳ Phase 2: Advanced Graph Features (Priority 2)**

- [ ] Graph traversal for related facts
- [ ] Full-text search for entity classification
- [ ] Use `discover_similar_entities()` function
- [ ] Use `get_user_facts_with_relations()` function
- [ ] Emotional context enrichment (link to user's emotional state)

---

## 🎯 **Expected Benefits**

### **Storage Quality:**
- ✅ **Richer metadata**: context_metadata with extraction reasoning
- ✅ **Graph traversal**: related_entities array for fast queries
- ✅ **Character awareness**: Track which character learned each fact
- ✅ **Hierarchical knowledge**: Category relationships for concept understanding

### **Query Performance:**
- ✅ **Faster related fact queries**: Use related_entities JSONB instead of joins
- ✅ **Better semantic search**: Full-text search with tsvector
- ✅ **Character-aware responses**: Query character_interactions for context

### **Quality Improvements:**
- ✅ **Better entity classification**: Use graph + full-text search
- ✅ **Conflict resolution**: Leverage opposing_relationships mapping
- ✅ **Semantic relationships**: Automatically discover similar entities

---

## 📝 **Next Steps**

1. **Implement missing JSONB fields** (context_metadata, related_entities)
2. **Add character_interactions tracking**
3. **Implement hierarchical relationships** (part_of, category_of)
4. **Mark bidirectional relationships properly**
5. **Test with enrichment worker**
6. **Validate graph queries work correctly**

**Result:** Enrichment worker will fully leverage PostgreSQL graph features, matching (and exceeding) inline extraction capabilities while providing superior quality through conversation-level analysis!
