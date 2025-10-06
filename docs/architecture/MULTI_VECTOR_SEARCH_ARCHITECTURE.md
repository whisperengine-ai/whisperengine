# Multi-Vector Search Architecture

**Status**: Active (October 2025)  
**Decision**: Dual-system approach with specialized use cases

## Overview

WhisperEngine uses TWO complementary multi-vector search systems, each optimized for different use cases.

## System 1: MultiVectorIntelligence (NEW - Sprint 2 Enhancement)

**Location**: `src/memory/multi_vector_intelligence.py`  
**Purpose**: Automatic query-based vector intelligence  
**Use Case**: User-facing memory retrieval with automatic query classification

### Features:
- **Intelligent Query Classification**: Detects emotional, semantic, content, or hybrid queries
- **5 Fusion Strategies**: 
  - `content_primary`: Factual/semantic queries
  - `emotion_primary`: Emotional/feeling queries  
  - `semantic_primary`: Concept/relationship queries
  - `balanced_fusion`: Balanced multi-vector search
  - `weighted_combination`: Sophisticated score fusion
- **Automatic Strategy Selection**: No manual configuration needed
- **Vector Weights**: Dynamic weighting based on query type

### Integration Points:
```python
# Used by main user-facing retrieval methods
- retrieve_relevant_memories() ✅ ACTIVE
- retrieve_relevant_memories_with_memoryboost() ✅ ACTIVE (via above)
- TrendWise adaptive learning ✅ ACTIVE (via above)
```

### Query Examples:
```python
# Emotional query → emotion_primary strategy
"How did I feel about that movie?"

# Factual query → content_primary strategy  
"What books do I own?"

# Concept query → semantic_primary strategy
"What are my career goals?"

# Hybrid query → balanced_fusion or weighted_combination
"Why did I feel excited about that job opportunity?"
```

## System 2: search_with_multi_vectors() (EXISTING)

**Location**: `src/memory/vector_memory_system.py:2595`  
**Purpose**: Explicit multi-vector searches with manual configuration  
**Use Case**: Specialized emotional intelligence, personality-aware searches

### Features:
- **Explicit Vector Selection**: Caller specifies which vectors to use
- **3 Search Modes**:
  - Triple-vector: emotion + content + personality (when personality context provided)
  - Dual-vector: emotion + content (when emotional_query provided)
  - Single-vector: content fallback
- **Manual Configuration**: Full control over vector usage
- **Personality Integration**: Supports personality_context parameter

### Integration Points:
```python
# Used for specialized searches
- Explicit emotional intelligence searches
- Character personality-aware searches
- Advanced role-playing AI features
```

### Usage Example:
```python
results = await vector_store.search_with_multi_vectors(
    content_query="What makes me happy?",
    emotional_query="joy excitement",  # Explicit emotion
    personality_context="optimistic adventurous",  # Explicit personality
    user_id=user_id,
    top_k=10
)
```

## Architecture Decision

### Why Two Systems?

**Separation of Concerns**:
1. **Automatic Intelligence** (MultiVectorIntelligence): User queries with no configuration
2. **Manual Intelligence** (search_with_multi_vectors): Advanced features with explicit control

**Safety**:
- Zero breaking changes to existing code
- Gradual adoption of new intelligence
- Easy rollback if needed

**Performance**:
- Automatic system optimizes common user queries
- Manual system provides fine-grained control for specialized features

## Vector Usage Patterns

### Content Vector (`NamedVector(name="content", ...)`)
- **Prefix**: `"{raw_content}"`
- **Purpose**: Semantic/factual similarity
- **Best for**: "What", "Who", "Where" queries
- **Example**: "What books do I own?" → searches raw content

### Emotion Vector (`NamedVector(name="emotion", ...)`)
- **Prefix**: `"emotion {emotions}: {content}"`
- **Purpose**: Emotional context similarity
- **Best for**: "How did I feel", "emotional" queries
- **Example**: "emotion joy with excitement: I love pizza" → searches emotional context

### Semantic Vector (`NamedVector(name="semantic", ...)`)
- **Prefix**: `"concept {concept_key}: {content}"`
- **Purpose**: Concept/relationship similarity
- **Best for**: "Why", "relationship", "theme" queries
- **Example**: "concept food_preference: I love pizza" → searches conceptual meaning

## Migration Strategy

### Current Status (October 2025)

✅ **Phase 1 Complete**: MultiVectorIntelligence integrated into main retrieval paths
- `retrieve_relevant_memories()` → Uses MultiVectorIntelligence
- `retrieve_relevant_memories_with_memoryboost()` → Auto-benefits
- Sprint 1 TrendWise → Auto-benefits
- Sprint 2 MemoryBoost → Auto-benefits

🔄 **Phase 2 Pending**: Specialized search consolidation (OPTIONAL)
- Evaluate if `search_with_multi_vectors()` should migrate to MultiVectorIntelligence
- Currently: Keep both systems for specialized use cases
- Future: May consolidate if manual configuration becomes unnecessary

## Performance Characteristics

### MultiVectorIntelligence
- **Latency**: ~50-100ms (query classification + multi-vector search)
- **Accuracy**: High (keyword-based classification proven effective)
- **Overhead**: Minimal (no LLM calls, pure pattern matching)

### search_with_multi_vectors()
- **Latency**: ~30-80ms (direct vector search, no classification)
- **Accuracy**: High (when caller provides correct context)
- **Overhead**: None (direct Qdrant calls)

## Testing Strategy

### MultiVectorIntelligence Tests
```bash
# Direct validation testing
python tests/automated/test_multi_vector_intelligence_validation.py

# Integration testing
python tests/automated/test_memoryboost_complete_validation.py
```

### Validation Criteria
- ✅ Query classification accuracy (>90% on test queries)
- ✅ Vector strategy selection (correct strategy for query type)
- ✅ Multi-vector fusion (balanced results from all 3 vectors)
- ✅ Fallback handling (graceful degradation to content-only)
- ✅ Performance (sub-100ms query classification)

## Future Considerations

### Potential Unification
If manual configuration becomes unnecessary, consider:
1. Deprecate `search_with_multi_vectors()` in favor of MultiVectorIntelligence
2. Add explicit parameter overrides to MultiVectorIntelligence
3. Maintain backward compatibility during migration

### Performance Optimization
- Cache query classifications for repeated patterns
- Pre-compute emotion/semantic embeddings for common queries
- Optimize multi-vector fusion algorithms based on usage patterns

## References

- Multi-Vector Intelligence Implementation: `src/memory/multi_vector_intelligence.py`
- Vector Memory System: `src/memory/vector_memory_system.py`
- Sprint 2 MemoryBoost: `SPRINT_2_MEMORYBOOST_COMPLETE.md`
- Data Store Validation: `data_store_validation_report_20251006_065532.json`
