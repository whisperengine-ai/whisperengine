# Semantic Knowledge Graph Architecture Design

**Date**: October 4, 2025  
**Status**: PRODUCTION IMPLEMENTATION  
**Branch**: `main`

## 🎯 Design Philosophy

WhisperEngine's personality-first architecture requires a data system that supports **authentic character responses** while providing **structured factual intelligence**. This design consolidates graph functionality into PostgreSQL while maintaining the sophisticated conversational AI features.

## 🏗️ Multi-Modal Data Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Data Ecosystem                          │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│   POSTGRESQL    │  VECTOR SPACE   │  TIME ANALYTICS │   CDL SYSTEM    │
│  (Structured)   │   (Semantic)    │   (Evolution)   │  (Character)    │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ • User Identity │ • Qdrant DB     │ • InfluxDB      │ • JSON Files    │
│ • Facts/Relations│ • Conversation │ • Confidence    │ • Personality   │
│ • Graph queries │   similarity    │   evolution     │ • Voice Style   │
│ • Recommendations│ • Emotion flow │ • Interaction   │ • AI Identity   │
│ • Analytics     │ • Context       │   frequency     │ • Background    │
│ • Transactions  │   switching     │ • Memory decay  │ • Conversation  │
│ • Full-text     │ • Character     │ • Trends        │   patterns      │
│   search        │   matching      │ • Analytics     │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

## 📊 Data Distribution Strategy

### **PostgreSQL: The Knowledge Foundation**

**Responsibilities:**
- User identity and authentication (existing)
- Fact entities and metadata
- Relationship graphs (1-3 hops typical)
- ACID transactions for consistency
- Complex analytical queries
- Full-text search for entity discovery

**Performance Profile:**
- Simple queries: < 1ms
- 2-hop relationships: 1-5ms
- Complex analytics: 10-50ms
- Full-text search: 5-15ms

### **Qdrant: The Conversation Intelligence**

**Responsibilities (unchanged):**
- Semantic conversation similarity
- Emotion flow analysis
- Context switching detection
- Character personality matching
- Vector-based memory retrieval

**Strengths:**
- Semantic search excellence
- 384D embeddings with fastembed
- Named vectors (content, emotion, semantic)
- Bot-specific memory isolation

### **InfluxDB: The Temporal Intelligence**

**Responsibilities:**
- Fact confidence evolution over time
- Interaction frequency tracking
- Memory decay modeling
- Preference trend analysis
- Analytics and metrics

**Use Cases:**
- "Your enthusiasm for pizza has grown from 0.7 to 0.9"
- "You've mentioned this 3 times in the past month"
- Confidence degradation over time

### **CDL: The Character Personality**

**Responsibilities (unchanged):**
- Character personality definitions
- Voice style and patterns
- AI identity handling
- Conversation flow guidance
- Personal background knowledge

**Integration:**
- Characters interpret facts through personality
- Elena uses marine biology metaphors
- Marcus adds analytical precision
- Each character maintains authentic voice

## 🗄️ PostgreSQL Schema Design

### **Core Tables**

```sql
-- Users (existing + enhanced)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_id BIGINT UNIQUE,
    username TEXT,
    preferred_name TEXT,
    user_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Fact entities with full-text search
CREATE TABLE fact_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL, -- 'food', 'hobby', 'person', 'place', 'media', 'activity'
    entity_name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    attributes JSONB DEFAULT '{}', -- Flexible additional attributes
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            COALESCE(entity_name, '') || ' ' || 
            COALESCE(category, '') || ' ' || 
            COALESCE(subcategory, '')
        )
    ) STORED,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(entity_type, entity_name)
);

-- User-fact relationships (the knowledge graph core)
CREATE TABLE user_fact_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES fact_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'likes', 'dislikes', 'knows', 'visited', 'wants', 'owns'
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1) DEFAULT 0.5,
    strength FLOAT CHECK (strength >= 0 AND strength <= 1) DEFAULT 0.5,
    
    -- Context metadata
    emotional_context TEXT, -- 'happy', 'excited', 'neutral', 'sad', etc.
    context_metadata JSONB DEFAULT '{}',
    
    -- Source tracking
    source_conversation_id TEXT,
    mentioned_by_character TEXT, -- Which character learned this fact
    source_platform TEXT DEFAULT 'discord',
    
    -- Graph relationships stored as JSONB for flexible traversal
    related_entities JSONB DEFAULT '[]', -- [{"entity_id": "uuid", "relation": "similar_to", "weight": 0.8}]
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, entity_id, relationship_type)
);

-- Entity relationships (like graph edges)
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id UUID REFERENCES fact_entities(id) ON DELETE CASCADE,
    to_entity_id UUID REFERENCES fact_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'similar_to', 'part_of', 'category_of', 'related_to', 'opposite_of'
    weight FLOAT CHECK (weight >= 0 AND weight <= 1) DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(from_entity_id, to_entity_id, relationship_type),
    CHECK(from_entity_id != to_entity_id) -- No self-relationships
);

-- Character interaction tracking
CREATE TABLE character_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_name TEXT NOT NULL,
    interaction_type TEXT NOT NULL, -- 'conversation', 'fact_mention', 'emotional_support', 'advice'
    session_id TEXT,
    entity_references JSONB DEFAULT '[]', -- Entities mentioned in this interaction
    emotional_tone TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_user_facts_lookup ON user_fact_relationships(user_id, confidence DESC, updated_at DESC);
CREATE INDEX idx_user_facts_type ON user_fact_relationships(user_id, relationship_type, confidence DESC);
CREATE INDEX idx_entity_search ON fact_entities USING GIN(search_vector);
CREATE INDEX idx_entity_attrs ON fact_entities USING GIN(attributes);
CREATE INDEX idx_relationship_graph ON user_fact_relationships USING GIN(related_entities);
CREATE INDEX idx_entity_relationships_forward ON entity_relationships(from_entity_id, weight DESC);
CREATE INDEX idx_entity_relationships_reverse ON entity_relationships(to_entity_id, weight DESC);
CREATE INDEX idx_character_interactions_user ON character_interactions(user_id, character_name, created_at DESC);
CREATE INDEX idx_entity_type_category ON fact_entities(entity_type, category);
```

## 🚀 Semantic Knowledge Router

### **Architecture**

```python
class SemanticKnowledgeRouter:
    """
    Smart query router that directs requests to optimal data stores
    based on query intent and data characteristics.
    """
    
    def __init__(self, postgres_pool, qdrant_client, influx_client):
        self.postgres = postgres_pool
        self.qdrant = qdrant_client
        self.influx = influx_client
    
    async def answer_user_query(
        self, 
        user_id: str, 
        query: str, 
        character: Character
    ) -> Dict[str, Any]:
        """Route query to appropriate data stores and synthesize response"""
        
        # 1. Analyze query intent
        intent = await self._analyze_query_intent(query)
        
        # 2. Route to appropriate stores
        if intent.type == "factual_recall":
            # PostgreSQL for structured facts
            facts = await self._get_user_facts(user_id, intent)
            confidence_trends = await self._get_confidence_trends(user_id, facts)
            
        elif intent.type == "conversation_style":
            # Qdrant for semantic similarity
            similar_convos = await self.qdrant.search_similar(query, user_id)
            
        elif intent.type == "temporal_analysis":
            # InfluxDB for trends
            trends = await self._get_preference_evolution(user_id)
        
        # 3. Character synthesizes through personality
        return await character.synthesize_response(
            facts=facts,
            conversations=similar_convos,
            trends=trends,
            query=query
        )
```

## 📈 Common Query Patterns

### **Pattern 1: Simple Fact Retrieval**

```sql
-- "What foods do I like?"
SELECT 
    fe.entity_name, 
    ufr.confidence, 
    ufr.emotional_context,
    ufr.mentioned_by_character,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = $1 
  AND fe.entity_type = 'food'
  AND ufr.relationship_type = 'likes'
  AND ufr.confidence > 0.5
ORDER BY ufr.confidence DESC, ufr.updated_at DESC
LIMIT 10;
```

### **Pattern 2: Character-Aware Facts**

```sql
-- "What foods have I mentioned to Elena?"
SELECT 
    fe.entity_name,
    ufr.confidence,
    COUNT(ci.id) as mention_count,
    MAX(ci.created_at) as last_mentioned,
    AVG(CASE WHEN ufr.emotional_context = 'happy' THEN 1.0 ELSE 0.5 END) as happiness_score
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
LEFT JOIN character_interactions ci ON ci.user_id = ufr.user_id 
    AND ci.character_name = $2
    AND ci.entity_references @> jsonb_build_array(fe.entity_name::text)
WHERE ufr.user_id = $1 
  AND fe.entity_type = 'food'
  AND (ufr.mentioned_by_character = $2 OR ci.id IS NOT NULL)
GROUP BY fe.entity_name, ufr.confidence
ORDER BY mention_count DESC, ufr.confidence DESC;
```

### **Pattern 3: Relationship Discovery (2-hop)**

```sql
-- "What foods are similar to pizza?"
WITH user_foods AS (
    SELECT fe.entity_name, ufr.confidence
    FROM user_fact_relationships ufr
    JOIN fact_entities fe ON ufr.entity_id = fe.id
    WHERE ufr.user_id = $1 AND fe.entity_type = 'food'
),
related_foods AS (
    SELECT DISTINCT
        fe2.entity_name,
        er.weight,
        er.relationship_type,
        uf.confidence as source_confidence
    FROM user_foods uf
    JOIN fact_entities fe1 ON fe1.entity_name = uf.entity_name
    JOIN entity_relationships er ON fe1.id = er.from_entity_id
    JOIN fact_entities fe2 ON er.to_entity_id = fe2.id
    WHERE er.relationship_type IN ('similar_to', 'related_to')
      AND er.weight > 0.5
      AND fe2.entity_name != uf.entity_name
)
SELECT entity_name, weight, relationship_type, source_confidence
FROM related_foods
ORDER BY weight * source_confidence DESC
LIMIT 20;
```

### **Pattern 4: Full-Text Entity Search**

```sql
-- "Find entities related to Italian cuisine"
SELECT 
    entity_name, 
    category, 
    entity_type,
    ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance
FROM fact_entities
WHERE search_vector @@ plainto_tsquery('english', $1)
ORDER BY relevance DESC
LIMIT 20;
```

## 🔄 Data Flow Integration

### **Conversation → Knowledge Extraction**

```
1. User: "I love pizza!"
   ↓
2. MessageProcessor detects factual content
   ↓
3. Extract: Entity="pizza", Type="food", Relationship="likes", Confidence=0.9
   ↓
4. Store in PostgreSQL:
   - Insert/Update fact_entities
   - Insert/Update user_fact_relationships
   - Auto-discover similar entities
   - Create entity_relationships
   ↓
5. Track in InfluxDB:
   - confidence_evolution measurement
   - interaction_frequency measurement
   ↓
6. Store conversation in Qdrant (existing flow)
```

### **Query → Response Synthesis**

```
1. User: "What foods do I like?"
   ↓
2. SemanticKnowledgeRouter analyzes intent: "factual_recall"
   ↓
3. PostgreSQL query: Get user food preferences
   ↓
4. InfluxDB query: Get confidence trends
   ↓
5. Qdrant query: Get conversation context
   ↓
6. CDL Character (Elena) synthesizes:
   "¡Ay! Looking at our conversations, I see you've mentioned 
    pizza 3 times with growing enthusiasm - your confidence has 
    grown from 0.7 to 0.9! That crispy crust texture reminds me 
    of calcium carbonate structures in coral reefs..."
```

## 🎭 Character Integration

### **Personality-First Response Pattern**

```python
class ElenaCharacter:
    async def synthesize_factual_response(
        self, 
        facts: List[Dict], 
        trends: List[Dict],
        query: str
    ) -> str:
        """Elena interprets facts through marine biologist personality"""
        
        # Facts provide structure
        top_foods = [f['entity_name'] for f in facts[:3]]
        confidence_growth = trends[0]['confidence_delta'] if trends else 0
        
        # Elena adds personality
        response = f"¡Ay, {self.user_name}! "
        
        if confidence_growth > 0.2:
            response += f"I've noticed your enthusiasm growing - "
        
        response += f"You've been talking about {', '.join(top_foods)} "
        
        # Marine biology metaphor (personality-driven)
        if 'pizza' in top_foods:
            response += "and that crispy texture reminds me of the "
            response += "layered calcium carbonate in coral formations! "
        
        return response
```

## 🔧 Implementation Phases

### **Phase 1: PostgreSQL Schema (Current)**
- ✅ Create enhanced schema SQL file
- ✅ Add migration script
- ✅ Create indexes for performance
- ✅ Add JSONB flexibility for future needs

### **Phase 2: SemanticKnowledgeRouter**
- Build query intent analyzer
- Implement PostgreSQL graph queries
- Add InfluxDB temporal tracking
- Integrate with existing Qdrant flow

### **Phase 3: Extraction Pipeline**
- Enhance factual detection in MessageProcessor
- Auto-extract entities and relationships
- Store in PostgreSQL + InfluxDB
- Maintain existing Qdrant storage

### **Phase 4: Character Integration**
- Update CDL prompt integration
- Add fact interpretation layer
- Maintain personality-first synthesis
- Preserve existing conversation features

## 📊 Performance Expectations

**Query Performance:**
- Simple fact lookup: < 1ms
- Character-aware queries: 1-5ms
- 2-hop relationship traversal: 5-10ms
- Complex analytics: 10-50ms

**Scalability:**
- Handles 1000s of facts per user
- Sub-second response times
- Partitioning available if needed
- Horizontal scaling with read replicas

## 🚨 Design Principles

1. **Personality-First**: Facts are interpreted through character personality
2. **Non-Disruptive**: All existing conversation features preserved
3. **Graduated Optimization**: Start with full fidelity, optimize only if needed
4. **Character Agnostic**: Works for any CDL character
5. **Temporal Intelligence**: Track how knowledge evolves
6. **Operational Simplicity**: PostgreSQL consolidation reduces complexity

## 🔒 Data Consistency

- ACID transactions for fact storage
- Eventual consistency with InfluxDB trends
- Qdrant remains independent (conversation intelligence)
- Foreign key constraints for referential integrity

## 🎯 Success Metrics

1. **Factual Recall Accuracy**: > 95% correct fact retrieval
2. **Response Time**: < 50ms for complex queries
3. **Character Consistency**: Personality-driven responses maintained
4. **User Satisfaction**: Natural, human-like memory recall
5. **System Stability**: No regressions in existing features

---

**Next Steps**: Implement Phase 1 schema and begin SemanticKnowledgeRouter integration.
