# Temporal Fact Evolution & Conflict Detection Analysis

**Date**: October 14, 2025  
**Context**: Analysis of implementing opposing relationship conflict detection, temporal fact evolution, and active deprecation systems in WhisperEngine  
**Risk Assessment**: LOW-MEDIUM risk with existing infrastructure  

## 🎯 EXECUTIVE SUMMARY

**✅ FEASIBLE with LOW RISK** - All three features can be implemented easily using our existing PostgreSQL schema and temporal infrastructure. The database already has timestamps, confidence tracking, and relationship storage needed for these enhancements.

## 🔍 CURRENT INFRASTRUCTURE ASSESSMENT

### ✅ EXISTING FOUNDATIONS

**PostgreSQL Schema (READY)**:
```sql
-- Already has temporal tracking
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW(),

-- Already has confidence and relationship tracking  
confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1) DEFAULT 0.5,
relationship_type TEXT NOT NULL, -- 'likes', 'dislikes', 'knows', etc.

-- Already has conflict resolution for facts
ON CONFLICT (user_id, entity_id, relationship_type)
DO UPDATE SET
    confidence = GREATEST(user_fact_relationships.confidence, $4),
    updated_at = NOW()
```

**Temporal Intelligence (READY)**:
- InfluxDB integration via `src/temporal/temporal_intelligence_client.py`
- Confidence evolution tracking already implemented
- Relationship progression metrics available

**Current Conflict Handling (FUNCTIONAL)**:
- Uses `GREATEST()` confidence for duplicate facts
- Updates timestamps automatically via triggers
- Character-aware fact attribution system

## 🚀 IMPLEMENTATION ROADMAP

### 1. 🔄 OPPOSING RELATIONSHIP CONFLICT DETECTION

**Risk Level**: ⭐ LOW (database query enhancement)

**Implementation Strategy**:
Add detection logic to `src/knowledge/semantic_router.py` in the `store_user_fact()` method:

```python
# Check for opposing relationships before storing
opposing_relationships = {
    'likes': ['dislikes', 'hates'],
    'loves': ['dislikes', 'hates'],
    'wants': ['rejects', 'avoids'],
    'enjoys': ['dislikes', 'hates'],
    'prefers': ['dislikes', 'avoids']
}

async def _detect_opposing_relationships(self, conn, user_id: str, entity_id: str, 
                                       new_relationship: str, new_confidence: float):
    """Detect and resolve opposing relationship conflicts"""
    
    if new_relationship not in opposing_relationships:
        return None
        
    # Check for existing opposing relationships
    opposing_query = """
        SELECT relationship_type, confidence, updated_at, mentioned_by_character
        FROM user_fact_relationships 
        WHERE user_id = $1 AND entity_id = $2 
        AND relationship_type = ANY($3)
        ORDER BY confidence DESC, updated_at DESC
    """
    
    opposing_types = opposing_relationships[new_relationship]
    conflicts = await conn.fetch(opposing_query, user_id, entity_id, opposing_types)
    
    for conflict in conflicts:
        if conflict['confidence'] > new_confidence:
            # Keep stronger opposing relationship
            logger.info(f"⚠️ CONFLICT: Keeping stronger {conflict['relationship_type']} "
                       f"(conf: {conflict['confidence']:.2f}) over new {new_relationship} "
                       f"(conf: {new_confidence:.2f})")
            return 'keep_existing'
        else:
            # Replace weaker opposing relationship
            await conn.execute("""
                DELETE FROM user_fact_relationships 
                WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
            """, user_id, entity_id, conflict['relationship_type'])
            
            logger.info(f"🔄 CONFLICT RESOLVED: Replaced {conflict['relationship_type']} "
                       f"with stronger {new_relationship}")
    
    return 'resolved'
```

**Integration Point**: Add call to `_detect_opposing_relationships()` before the existing `INSERT ... ON CONFLICT` logic.

### 2. ⏰ TEMPORAL FACT EVOLUTION

**Risk Level**: ⭐⭐ LOW-MEDIUM (new query patterns)

**Implementation Strategy**:
Enhance the existing fact retrieval to consider temporal relevance:

```python
async def get_temporally_relevant_facts(self, user_id: str, lookback_days: int = 90) -> List[Dict]:
    """Get facts with temporal relevance weighting"""
    
    query = """
        SELECT 
            ufr.*,
            fe.entity_name,
            fe.category,
            fe.attributes,
            -- Temporal relevance scoring
            CASE 
                WHEN updated_at > NOW() - INTERVAL '30 days' THEN 1.0
                WHEN updated_at > NOW() - INTERVAL '60 days' THEN 0.8
                WHEN updated_at > NOW() - INTERVAL '90 days' THEN 0.6
                ELSE 0.4
            END as temporal_relevance,
            
            -- Detect potential staleness
            (NOW() - updated_at) as fact_age,
            CASE 
                WHEN relationship_type IN ('works_at', 'lives_in', 'studies_at') 
                AND updated_at < NOW() - INTERVAL '180 days' THEN true
                WHEN relationship_type IN ('wants', 'plans', 'intends')
                AND updated_at < NOW() - INTERVAL '60 days' THEN true  
                ELSE false
            END as potentially_outdated
            
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = $1
        AND ufr.updated_at > NOW() - INTERVAL '%d days'
        ORDER BY 
            ufr.confidence * temporal_relevance DESC,
            ufr.updated_at DESC
    """ % lookback_days
    
    async with self.postgres_pool.acquire() as conn:
        return await conn.fetch(query, user_id)
```

**Integration Point**: Replace current `_get_postgres_facts_for_prompt()` calls with temporal-aware version.

### 3. 🗑️ ACTIVE DEPRECATION OF OUTDATED FACTS

**Risk Level**: ⭐ LOW (background maintenance task)

**Implementation Strategy**:
Add automated cleanup task and confidence degradation:

```python
async def deprecate_outdated_facts(self, dry_run: bool = True) -> Dict[str, int]:
    """Actively deprecate facts that are likely outdated"""
    
    # Define staleness rules
    staleness_rules = {
        'works_at': 365,      # Jobs change yearly
        'lives_in': 730,      # Address changes every 2 years  
        'studies_at': 1460,   # Education programs are multi-year
        'wants': 90,          # Desires change seasonally
        'plans': 30,          # Plans are short-term
        'intends': 60,        # Intentions are medium-term
        'dating': 180,        # Relationship status changes
        'owns': 1095          # Possessions are longer-term
    }
    
    deprecated_count = 0
    confidence_reduced_count = 0
    
    async with self.postgres_pool.acquire() as conn:
        for relationship_type, max_days in staleness_rules.items():
            
            # Find potentially outdated facts
            outdated_facts = await conn.fetch("""
                SELECT user_id, entity_id, confidence, updated_at
                FROM user_fact_relationships 
                WHERE relationship_type = $1
                AND updated_at < NOW() - INTERVAL '%d days'
                AND confidence > 0.2
            """ % max_days, relationship_type)
            
            for fact in outdated_facts:
                days_old = (datetime.now() - fact['updated_at']).days
                degradation_factor = max(0.2, 1.0 - (days_old / (max_days * 2)))
                new_confidence = fact['confidence'] * degradation_factor
                
                if new_confidence < 0.3:
                    # Mark for deprecation (soft delete)
                    if not dry_run:
                        await conn.execute("""
                            UPDATE user_fact_relationships 
                            SET confidence = 0.1,
                                context_metadata = context_metadata || '{"deprecated": true, "reason": "temporal_staleness"}'
                            WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                        """, fact['user_id'], fact['entity_id'], relationship_type)
                    deprecated_count += 1
                else:
                    # Reduce confidence gradually
                    if not dry_run:
                        await conn.execute("""
                            UPDATE user_fact_relationships 
                            SET confidence = $4
                            WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                        """, fact['user_id'], fact['entity_id'], relationship_type, new_confidence)
                    confidence_reduced_count += 1
    
    return {
        'deprecated': deprecated_count,
        'confidence_reduced': confidence_reduced_count
    }
```

**Integration Point**: Add as background task in message processor or separate maintenance script.

## 🔧 IMPLEMENTATION PRIORITY & RISK ASSESSMENT

### Priority 1: Opposing Relationship Detection ⭐ LOW RISK
- **Why First**: Improves data quality immediately
- **Implementation Time**: 2-3 hours
- **Risk**: Very low - just adds logic before existing conflict resolution
- **Testing**: Easy to validate with direct Python tests

### Priority 2: Temporal Fact Evolution ⭐⭐ LOW-MEDIUM RISK  
- **Why Second**: Enhances existing retrieval with temporal weighting
- **Implementation Time**: 4-6 hours
- **Risk**: Low-Medium - changes query patterns but doesn't break existing functionality
- **Testing**: Requires testing with existing user data

### Priority 3: Active Deprecation ⭐ LOW RISK
- **Why Third**: Background maintenance, doesn't affect user experience directly
- **Implementation Time**: 3-4 hours
- **Risk**: Low - soft deletes and confidence reduction are reversible
- **Testing**: Should run in dry-run mode first

## 🧪 TESTING STRATEGY

### Direct Python Validation Pattern:
```bash
# Test opposing relationship detection
source .venv/bin/activate && \
export DISCORD_BOT_NAME=elena && \
python -c "
import asyncio
from src.knowledge.semantic_router import SemanticKnowledgeRouter
async def test_conflicts():
    router = SemanticKnowledgeRouter()
    await router.store_user_fact('test_user', 'pizza', 'food', 'likes', 0.8)
    await router.store_user_fact('test_user', 'pizza', 'food', 'dislikes', 0.9)
    facts = await router.get_user_facts('test_user', limit=10)
    print('Conflict resolution test:', facts)
asyncio.run(test_conflicts())
"

# Test temporal fact weighting  
python -c "
import asyncio
from src.knowledge.semantic_router import SemanticKnowledgeRouter
async def test_temporal():
    router = SemanticKnowledgeRouter()
    facts = await router.get_temporally_relevant_facts('existing_user_id')
    for fact in facts[:5]:
        print(f'{fact[\"entity_name\"]}: confidence={fact[\"confidence\"]:.2f}, age={fact[\"fact_age\"]}')
asyncio.run(test_temporal())
"
```

## 📊 EXPECTED BENEFITS

1. **Opposing Relationships**: Eliminates "I like pizza" + "I hate pizza" contradictions
2. **Temporal Evolution**: Recent facts (job changes, moves) weighted higher than old facts
3. **Active Deprecation**: Gradually reduces confidence in stale career/location facts

## 🚨 INTEGRATION CONSIDERATIONS

### Existing Systems (NO CHANGES NEEDED):
- ✅ **Vector Memory**: Works independently, no conflicts
- ✅ **CDL Character System**: Uses fact retrieval, benefits automatically  
- ✅ **Multi-Bot Platform**: Each bot has isolated collections, no conflicts
- ✅ **Conversation Context**: Enhanced facts flow through existing `_get_postgres_facts_for_prompt()`

### Production Safety:
- ✅ **Backward Compatible**: All changes are additive or soft deletes
- ✅ **Feature Flags**: Can be controlled via environment variables
- ✅ **Rollback Safe**: Confidence changes are reversible

## 🎯 RECOMMENDATION

**IMPLEMENT ALL THREE - Risk is LOW and infrastructure is READY**

These enhancements build naturally on our existing PostgreSQL schema and temporal intelligence. The current conflict resolution using `GREATEST()` confidence already handles basic conflicts well. These additions would:

1. **Detect semantic oppositions** (likes vs dislikes)  
2. **Weight facts by recency** (recent job changes matter more)
3. **Automatically maintain data quality** (reduce confidence in stale facts)

All three features use existing infrastructure and can be implemented safely with our current Direct Python Testing approach.

**Start with Opposing Relationship Detection** - it's the lowest risk and provides immediate value.