# CDL Graph Intelligence Analysis

**Date**: October 8, 2025  
**Context**: Leveraging PostgreSQL graph features for character knowledge queries

---

## Current Architecture Analysis

### ✅ **User Facts System** (PRODUCTION - 304 entities, 45 relationships)

**Tables Used**:
- `fact_entities` - Stores entities (foods, hobbies, books, etc.)
- `user_fact_relationships` - User → Entity relationships with confidence scores
- `entity_relationships` - Entity → Entity graph relationships (`similar_to`, `part_of`, etc.)

**Query Pattern Example**:
```sql
-- User asks: "What books do I like that are similar to Dune?"
SELECT fe2.entity_name, er.weight as similarity
FROM user_fact_relationships ufr1
JOIN fact_entities fe1 ON ufr1.entity_id = fe1.id
JOIN entity_relationships er ON fe1.id = er.from_entity_id
JOIN fact_entities fe2 ON er.to_entity_id = fe2.id
WHERE ufr1.user_id = $1 
  AND fe1.entity_name = 'Dune'
  AND er.relationship_type = 'similar_to'
ORDER BY er.weight DESC;
```

**Intelligent Features**:
- Automatic trigram similarity detection (`similarity(entity_name, $1) > 0.3`)
- Weighted relationships (0-1 confidence scores)
- Character-aware fact tracking (`mentioned_by_character` field)
- Emotional context (`emotional_context` field)

---

### ⚠️ **CDL Character System** (CURRENT - NO GRAPH INTELLIGENCE)

**Current Approach**: Direct table queries only
```python
# Current SimpleCDLManager approach
background_records = await conn.fetch(
    "SELECT * FROM character_background WHERE character_id = $1", 
    character_id
)
# Returns: List of background records, NO relationship intelligence
```

**Tables Available but UNDERUTILIZED**:
- `character_relationships` - Character → Entity relationships (status, strength)
- `character_memories` - Key memories with triggers and emotional impact
- `character_abilities` - Skills with proficiency levels
- `character_background` - History with importance levels

**Missing Intelligence**:
- ❌ No similarity queries ("similar experiences", "related memories")
- ❌ No weighted importance filtering
- ❌ No trigger-based memory activation
- ❌ No relationship graph traversal
- ❌ No character knowledge graph queries

---

## Proposed Solution: CDL Graph Intelligence Layer

### 🎯 **Goal**: Enable graph-based character knowledge queries

When user asks: **"Elena, tell me about your family"**

**Current Behavior** (Direct query):
```sql
SELECT description FROM character_background 
WHERE character_id = 1 AND category = 'personal'
-- Returns: Generic list of background entries
```

**Proposed Behavior** (Graph intelligence):
```sql
-- Step 1: Find family-related background entries with importance weighting
SELECT cb.description, cb.importance_level,
       COUNT(cm.id) as related_memories
FROM character_background cb
LEFT JOIN character_memories cm ON cm.character_id = cb.character_id
  AND cm.triggers @> ARRAY['family']
WHERE cb.character_id = $1
  AND (cb.category = 'personal' OR cb.title ILIKE '%family%')
ORDER BY cb.importance_level DESC, related_memories DESC;

-- Step 2: Find related memories triggered by "family"
SELECT cm.title, cm.description, cm.emotional_impact
FROM character_memories cm
WHERE cm.character_id = $1
  AND 'family' = ANY(cm.triggers)
ORDER BY cm.importance_level DESC;

-- Step 3: Find relevant relationships
SELECT cr.related_entity, cr.relationship_type, cr.relationship_strength
FROM character_relationships cr
WHERE cr.character_id = $1
  AND cr.relationship_type IN ('family', 'close_friend')
  AND cr.status = 'active'
ORDER BY cr.relationship_strength DESC;
```

---

## Implementation Plan

### Phase 1: Character Knowledge Graph Manager

Create `src/characters/cdl/character_graph_manager.py`:

```python
class CharacterGraphManager:
    """
    PostgreSQL graph intelligence for CDL character data.
    Mirrors user facts architecture but for character knowledge.
    """
    
    async def query_character_knowledge(
        self,
        character_name: str,
        query_text: str,
        intent: str  # 'family', 'career', 'relationships', 'memories', 'skills'
    ) -> Dict[str, Any]:
        """
        Graph-aware character knowledge retrieval.
        
        Returns weighted, importance-ranked results with:
        - Background entries (importance_level weighted)
        - Related memories (trigger-activated)
        - Relevant relationships (strength weighted)
        - Connected abilities (proficiency weighted)
        """
        pass
    
    async def find_related_memories(
        self,
        character_id: int,
        trigger_keywords: List[str]
    ) -> List[Dict]:
        """Find memories activated by trigger keywords"""
        pass
    
    async def get_relationship_graph(
        self,
        character_id: int,
        relationship_types: Optional[List[str]] = None,
        min_strength: int = 5
    ) -> List[Dict]:
        """Get character's relationship network with strength weighting"""
        pass
    
    async def query_abilities_by_context(
        self,
        character_id: int,
        context: str  # 'professional', 'mystical', 'social'
    ) -> List[Dict]:
        """Query abilities filtered by usage context and proficiency"""
        pass
```

### Phase 2: Integration with CDL AI Integration

Modify `src/prompts/cdl_ai_integration.py`:

```python
# Current: Direct property access
if hasattr(character, 'backstory') and character.backstory:
    backstory = character.backstory
    if hasattr(backstory, 'family_background'):
        personal_sections.append(f"Family: {backstory.family_background}")

# Proposed: Graph-aware query
if 'family' in message_lower:
    graph_result = await character_graph_manager.query_character_knowledge(
        character_name=character.identity.name,
        query_text=message,
        intent='family'
    )
    
    # Returns prioritized, weighted results:
    # - Background entries sorted by importance_level
    # - Memories triggered by 'family' keyword
    # - Family relationships with strength scores
    # - Related formative experiences
    
    if graph_result['background']:
        personal_sections.append(
            f"Family Background: {graph_result['background'][0]['description']}"
        )
    if graph_result['memories']:
        personal_sections.append(
            f"Key Memory: {graph_result['memories'][0]['title']}"
        )
```

### Phase 3: Query Intent Detection

Extend `src/knowledge/semantic_router.py` intent detection:

```python
class QueryIntent(Enum):
    # Existing user fact intents
    FACTUAL_RECALL = "factual_recall"
    RELATIONSHIP_DISCOVERY = "relationship_discovery"
    
    # NEW: Character knowledge intents
    CHARACTER_BACKGROUND = "character_background"  # "Tell me about yourself"
    CHARACTER_RELATIONSHIPS = "character_relationships"  # "Who do you know?"
    CHARACTER_SKILLS = "character_skills"  # "What are you good at?"
    CHARACTER_MEMORIES = "character_memories"  # "What do you remember about X?"
```

---

## Benefits of Graph Approach

### 🎯 **Intelligence Improvements**

1. **Weighted Importance**: 
   - Background entries ranked by `importance_level` (1-10)
   - Memories ranked by `emotional_impact` (1-10)
   - Relationships ranked by `relationship_strength` (1-10)

2. **Trigger-Based Memory Activation**:
   - Memories have `triggers` TEXT[] field
   - "family" query → Activates memories with 'family' trigger
   - Natural conversation flow with relevant memories

3. **Relationship Graph Traversal**:
   - Character → Related Entities → Their attributes
   - "Tell me about your mentor" → Finds relationship → Retrieves relationship context
   - Multi-hop queries possible (mentor's mentor, colleague's projects)

4. **Context-Aware Skills**:
   - Filter by `usage_frequency` ('daily', 'regular', 'occasional')
   - Filter by `proficiency_level` (expert skills vs learning skills)
   - Filter by `category` (professional vs mystical)

### 📊 **Query Examples**

**User Query**: "Elena, tell me about your diving experience"

**Graph Query**:
```sql
-- Find diving-related background
SELECT cb.description, cb.importance_level
FROM character_background cb
WHERE cb.character_id = 1
  AND (cb.title ILIKE '%diving%' OR cb.description ILIKE '%diving%')
ORDER BY cb.importance_level DESC;

-- Find diving-related abilities
SELECT ca.ability_name, ca.proficiency_level, ca.usage_frequency
FROM character_abilities ca
WHERE ca.character_id = 1
  AND ca.ability_name ILIKE '%diving%'
ORDER BY ca.proficiency_level DESC;

-- Find diving-related memories
SELECT cm.title, cm.emotional_impact
FROM character_memories cm
WHERE cm.character_id = 1
  AND 'diving' = ANY(cm.triggers)
ORDER BY cm.emotional_impact DESC, cm.importance_level DESC;
```

**Result**: Weighted, prioritized diving knowledge across multiple dimensions

---

## Database Schema Enhancements Needed

### ✅ **Current Schema** (Already suitable for graph queries)

All tables have weighting/importance fields:
- `character_background.importance_level` (1-10)
- `character_memories.emotional_impact` (1-10)
- `character_memories.importance_level` (1-10)
- `character_relationships.relationship_strength` (1-10)
- `character_abilities.proficiency_level` (1-10)

### 🔧 **Recommended Indexes** (Performance optimization)

```sql
-- Trigger-based memory queries
CREATE INDEX idx_character_memories_triggers 
ON character_memories USING GIN(triggers);

-- Text search on descriptions
CREATE INDEX idx_character_background_description_trgm 
ON character_background USING GIN(description gin_trgm_ops);

-- Relationship graph traversal
CREATE INDEX idx_character_relationships_strength 
ON character_relationships(character_id, relationship_strength DESC);

-- Ability filtering
CREATE INDEX idx_character_abilities_proficiency 
ON character_abilities(character_id, proficiency_level DESC);
```

---

## Comparison: Current vs Proposed

| Feature | Current Approach | Graph Approach |
|---------|-----------------|----------------|
| **Family query** | Returns all personal background | Returns top 3 by importance + related memories |
| **Career query** | Returns all career background | Returns weighted by importance + relevant abilities |
| **Relationship query** | Returns raw relationship list | Returns active relationships sorted by strength |
| **Memory activation** | No trigger system | Automatic trigger-based memory retrieval |
| **Importance filtering** | No filtering | Automatic importance_level ranking |
| **Multi-dimensional** | Single table query | Cross-table graph traversal |
| **Similarity** | No similarity | Trigram similarity for fuzzy matching |

---

## Implementation Priority

### ✅ **HIGH PRIORITY** (Immediate Value)

1. **CharacterGraphManager** class creation
2. **Weighted importance queries** (importance_level, emotional_impact, relationship_strength)
3. **Trigger-based memory activation** (leverage existing `triggers` TEXT[] field)
4. **Integration with cdl_ai_integration.py** personal knowledge extraction

### 🟡 **MEDIUM PRIORITY** (Enhancement)

5. **Query intent detection** for character knowledge queries
6. **Cross-character relationship graphs** (Elena knows Marcus, Marcus knows...)
7. **Temporal filtering** (recent memories vs old memories)

### 🔵 **LOW PRIORITY** (Future)

8. **Character knowledge similarity** (similar backgrounds, similar abilities)
9. **Multi-hop relationship traversal** (friend of friend)
10. **Knowledge graph visualization** (for debugging/analysis)

---

## Code Location Strategy

**New File**: `src/characters/cdl/character_graph_manager.py`
- Mirrors `src/knowledge/semantic_router.py` architecture
- Uses same PostgreSQL graph patterns as user facts
- Integrated into SimpleCDLManager and EnhancedCDLManager

**Integration Point**: `src/prompts/cdl_ai_integration.py`
- Replace direct property access with graph queries
- Add query intent detection for character knowledge
- Weighted, prioritized personal knowledge extraction

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Personal knowledge relevance | Random order | Importance-weighted |
| Memory activation | Manual | Trigger-based automatic |
| Relationship context | Flat list | Strength-weighted graph |
| Query intelligence | Direct lookup | Multi-dimensional graph |
| Response quality | Generic | Contextual, prioritized |

---

## Next Steps

1. ✅ **Analysis Complete** (this document)
2. 🔨 **Create CharacterGraphManager** class
3. 🔗 **Add graph queries** for each intent type (family, career, relationships, memories)
4. 🎯 **Integrate with CDL AI Integration** personal knowledge extraction
5. 📊 **Add performance indexes** for graph query optimization
6. ✅ **Test with real queries** (Elena family, Jake career, Aetheris relationships)

---

**Conclusion**: YES, we should absolutely leverage PostgreSQL graph features for CDL character data. The architecture already supports it with importance/strength fields, trigger arrays, and relational structure. This will provide the same intelligent query capabilities for character knowledge that we have for user facts.

**Estimated Implementation Time**: 4-6 hours for Phase 1 (CharacterGraphManager + basic integration)

---

**Last Updated**: October 8, 2025  
**Author**: GitHub Copilot AI Agent  
**Status**: 📋 ANALYSIS COMPLETE - READY FOR IMPLEMENTATION
