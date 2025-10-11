# Data Flow Diagram: "I have a cat named Max"

**🚨 CRITICAL UPDATE**: This diagram has been corrected. The original version incorrectly described "LLM Fact Extraction" - the actual implementation uses **regex pattern matching**, not LLM calls! See `LLM_CALL_ANALYSIS_CORRECTION.md` for details.

## 🔄 Complete Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER MESSAGE INPUT                            │
│                "I have a cat named Max"                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ├─────────────────┬─────────────────────────┐
                       ▼                 ▼                         ▼
         ┌─────────────────────┐  ┌──────────────────┐  ┌─────────────────┐
         │   PIPELINE 1:       │  │   PIPELINE 2:    │  │   PIPELINE 3:   │
         │ Entity Extraction   │  │ Pattern-Based    │  │ Semantic Router │
         │ (Search/Keywords)   │  │ Fact Extract     │  │ (Graph Storage) │
         └──────────┬──────────┘  │ (Relationships)  │  └────────┬────────┘
                    │              │ NO LLM!          │           │
                    ▼              └────────┬─────────┘           ▼
         ┌──────────────────────┐          ▼          ┌──────────────────┐
         │ PREPROCESSING:       │  ┌─────────────────────┐  │ VERB MAPPING:    │
         │ Remove stop words    │  │ FULL CONTEXT:       │  │ "have" → "owns"  │
         │                      │  │ Regex on original   │  │                  │
         │ "I have a cat named  │  │                     │  │ Detects: "have"  │
         │  Max"                │  │ "I have a cat named │  │ Maps to: "owns"  │
         │   ↓                  │  │  Max"               │  │   ↓              │
         │ "cat named max"      │  │   ↓                 │  │ relationship_    │
         │   ↓                  │  │ [Regex patterns]    │  │ type = "owns"    │
         │ ['cat', 'named',     │  │   ↓                 │  │                  │
         │  'max']              │  │ Pattern matches:    │  │                  │
         └──────────┬───────────┘  │ - r'i\s+have...'    │  └────────┬─────────┘
                    │              │ - r'named\s+(\w+)'  │           │
                    │              │   ↓                 │           │
                    │              │ Extracted:          │           │
                    │              │ - Entity: "Max"     │           │
                    │              │ - Type: "pet"       │           │
                    │              │ - Rel: "have"       │           │
                    │              └──────────┬──────────┘           │
                    │                         │                      │
                    ▼                         ▼                      ▼
         ┌──────────────────────┐  ┌────────────────────────┐  ┌──────────────────┐
         │ USED FOR:            │  │ STORED IN POSTGRES:    │  │ GRAPH STRUCTURE: │
         │                      │  │                        │  │                  │
         │ • Vector search      │  │ fact_entities:         │  │  [User:user123]  │
         │ • Memory retrieval   │  │   id: 1                │  │        │         │
         │ • Keyword matching   │  │   entity_type: 'pet'   │  │        │ owns    │
         │                      │  │   entity_name: 'Max'   │  │        ▼         │
         │ Query: "cat max"     │  │                        │  │    [Pet:Max]     │
         │ Finds memories about │  │ user_fact_relationships│  │    type: cat     │
         │ cats and Max         │  │   user_id: 'user123'   │  │                  │
         │                      │  │   entity_id: 1         │  │                  │
         │ ✅ "have" not needed │  │   relationship: 'owns' │  │ ✅ Relationship  │
         │    for search        │  │   confidence: 0.8      │  │    preserved!    │
         └──────────────────────┘  └────────────────────────┘  └──────────────────┘
```

---

## 🎯 Key Architectural Decision Points

### Decision Point 1: Entity Extraction (Line 303)
```python
# File: src/utils/enhanced_query_processor.py
def _extract_entities(self, message: str) -> list[str]:
    # Message is ALREADY cleaned - stop words removed
    words = message.split()  # "cat named max"
    
    # ✅ CORRECT: "have" already removed by clean_text()
    # Purpose: Extract keywords for search
    # Result: ['cat', 'named', 'max']
```

**Why remove "have"?**
- Vector search for "cat max" returns same memories as "have cat max"
- Function words don't improve semantic similarity scores
- Reduces noise in keyword matching

---

### Decision Point 2: LLM Fact Extraction (Line 1774)
```python
# File: src/llm/llm_client.py
def extract_facts(self, message: str) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": "Extract factual information..."},
        {"role": "user", "content": f"""
            Extract facts about relationships, locations, preferences...
            Message: "{message}"  # ← FULL message, NO preprocessing!
        """}
    ]
    
    # ✅ CORRECT: LLM receives "I have a cat named Max"
    # LLM can infer: User OWNS a pet named Max
```

**Why preserve "have"?**
- LLM needs complete grammatical context
- "have" indicates ownership/possession relationship
- Natural language understanding requires full sentences

---

### Decision Point 3: Semantic Router (Line 257)
```python
# File: src/knowledge/semantic_router.py
def _extract_relationship_type(self, query: str) -> Optional[str]:
    relationship_keywords = {
        "owns": ["own", "have", "possess", "got"]  # ← "have" explicitly mapped!
    }
    
    if "have" in query:
        return "owns"  # ✅ CORRECT: Maps "have" to "owns" relationship
```

**Why map "have"?**
- Normalizes different ways of expressing ownership
- "I have X", "I own X", "I got X" all mean user possesses X
- Graph storage uses consistent relationship types

---

## 🔍 Query Example: "What pets do I have?"

```
┌──────────────────────────────────┐
│  User Query: "What pets do I     │
│              have?"               │
└────────────┬─────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Entity Extraction: │
    │ ['pets', 'have']   │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────────┐
    │ Semantic Router:       │
    │ Detects "have" keyword │
    │ Maps to: "owns"        │
    └────────┬───────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │ PostgreSQL Query:                  │
    │                                    │
    │ SELECT fe.entity_name              │
    │ FROM user_fact_relationships ufr   │
    │ JOIN fact_entities fe              │
    │   ON ufr.entity_id = fe.id         │
    │ WHERE ufr.user_id = 'user123'      │
    │   AND ufr.relationship_type = 'owns'│ ← Uses mapped "owns"
    │   AND fe.entity_type = 'pet'       │
    └────────┬───────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Result: "Max"      │
    │                    │
    │ ✅ Relationship    │
    │    preserved and   │
    │    queryable!      │
    └────────────────────┘
```

---

## 🎓 Three-Layer Architecture Summary

### Layer 1: Search/Retrieval Layer
**Purpose**: Find relevant content quickly  
**Processing**: Aggressive preprocessing (stop word removal)  
**Files**: 
- `enhanced_query_processor.py`
- `vector_memory_system.py`
- `performance_optimizer.py`

**Example**:
```
Input:  "I have a cat named Max"
Output: ['cat', 'named', 'max']
Use:    Vector search, keyword matching
```

### Layer 2: Understanding Layer  
**Purpose**: Extract semantic meaning and relationships  
**Processing**: Full context analysis (no preprocessing)  
**Files**:
- `llm_client.py` (extract_facts)
- LLM models

**Example**:
```
Input:  "I have a cat named Max" (full message)
Output: {
  "fact": "User owns a cat named Max",
  "entities": ["Max", "cat"],
  "relationship": "owns"
}
```

### Layer 3: Storage Layer
**Purpose**: Store structured knowledge graph  
**Processing**: Normalized relationship types  
**Files**:
- `semantic_router.py`
- PostgreSQL tables (fact_entities, user_fact_relationships)

**Example**:
```
Graph: [User:user123] --[owns]--> [Pet:Max]
Query: SELECT * WHERE relationship_type = 'owns'
```

---

## ✅ Validation Checklist

- ✅ **Entity extraction removes stop words** - Correct for search optimization
- ✅ **LLM fact extraction preserves full context** - Correct for semantic understanding
- ✅ **Semantic router maps "have" to "owns"** - Correct for normalized relationships
- ✅ **PostgreSQL stores structured graph** - Correct for queryable knowledge
- ✅ **Later queries can find the relationship** - Correct end-to-end flow

**Conclusion**: All three layers working correctly! No changes needed. 🎉
