# Bot Self-Fact Extraction - Design Improvements

**Date**: October 20, 2025  
**Context**: User feedback session on bot self-fact extraction design

---

## Key Improvements Made

### 1. **"myself" Convention** ✨

**Problem**: Original design used `user_id = "bot:elena"` which required parsing bot name from string

**Solution**: Use universal `user_id = "myself"` convention
- Cleaner queries: `WHERE user_id = 'myself' AND mentioned_by_character = $1`
- Semantic clarity: "myself" is self-documenting
- No parsing needed: Bot isolation via `mentioned_by_character` field
- Universal convention: All bots use same identifier

**Storage Pattern**:
```sql
-- User facts
user_id = "123456789"                -- Discord user ID
mentioned_by_character = "elena"     -- Which bot learned this

-- Bot facts
user_id = "myself"                   -- Universal self-reference ✨
mentioned_by_character = "elena"     -- Which bot this fact belongs to
```

**Query Examples**:
```sql
-- Get Elena's self-facts
SELECT * FROM user_fact_relationships
WHERE user_id = 'myself' AND mentioned_by_character = 'elena';

-- Get all bot self-facts
SELECT * FROM user_fact_relationships
WHERE user_id = 'myself';

-- Compare to old pattern (more verbose)
WHERE user_id LIKE 'bot:%'  -- Required LIKE pattern matching
```

---

### 2. **Priority Filtering** 🎯

**Problem**: Without filtering, database would flood with trivial facts
- "I have a computer" (generic ownership)
- "I'm typing right now" (temporary state)
- "I like this conversation" (politeness)
- Could accumulate 100+ meaningless facts per bot

**Solution**: Extract ONLY identity-defining facts

**Priority Levels**:
- **HIGH**: "I love", "I prefer", "I always", "My passion is" (✅ Always store)
- **MEDIUM**: "I enjoy", "I like", "I tend to" (✅ Store if confident)
- **LOW**: Temporary states, generic ownership, politeness (❌ Skip)

**Limits**:
- Max 3-5 facts per conversation window (24 hours)
- Target 10-20 core facts per bot (not 100+)
- Alert if bot exceeds 50 total facts

**Examples**:

✅ **Extract** (Identity-Defining):
- "I **love** exploring ocean depths" → Strong preference, HIGH priority
- "**My passion** is marine conservation" → Identity-defining, HIGH priority
- "I **always** review research papers in the morning" → Defining habit, HIGH priority
- "I **prefer** collaborative discussions" → Communication style, MEDIUM priority

❌ **Skip** (Trivial):
- "I'm having coffee right now" → Temporary state
- "I have a laptop" → Generic ownership
- "I like this conversation" → Politeness
- "I saw your message" → Obvious interaction

**LLM Prompt Instructions**:
```
IMPORTANT: For {bot_name}'s self-facts, ONLY extract statements that are:
1. Identity-defining (core personality traits, strong preferences)
2. Declarative "I/my/mine" statements
3. High confidence (clear, unambiguous)
4. Not trivial (skip casual mentions)

CRITICAL: Limit to 3-5 HIGHEST PRIORITY bot facts per conversation window.
Quality over quantity!
```

---

### 3. **Focus on "I/My/Mine" Declarations**

**Rationale**: Most defining self-facts use first-person possessive language

**Pattern Matching** (for LLM guidance):
- "I love..." → Strong preference
- "I prefer..." → Clear choice
- "I always..." → Consistent behavior
- "My passion is..." → Core identity
- "My approach is..." → Methodology
- "I find X fascinating" → Strong interest

**Not Included**:
- Third-person descriptions
- Passive observations
- Weak opinions ("I think", "Maybe I")

---

## Benefits of These Improvements

### 1. Database Efficiency
- **Before**: Could accumulate 100+ trivial facts per bot
- **After**: 10-20 carefully curated defining facts
- **Storage Savings**: 80-90% reduction in fact records
- **Query Performance**: Faster retrieval, less noise

### 2. Personality Authenticity
- **Before**: Mix of meaningful and trivial facts dilutes character
- **After**: Only identity-defining facts reinforce core personality
- **User Experience**: Bot responses feel more consistent and authentic
- **Character Depth**: Quality over quantity creates deeper personalities

### 3. Maintainability
- **Cleaner Queries**: `user_id = 'myself'` is more readable than `user_id LIKE 'bot:%'`
- **No Parsing**: Don't need to extract bot name from "bot:elena" string
- **Universal Convention**: All bots follow same pattern
- **Monitoring**: Easy to count facts per bot, alert on thresholds

### 4. LLM Cost Savings
- **Smaller Context**: Inject 10-20 facts instead of 100+
- **Token Reduction**: ~80% fewer tokens for bot self-facts
- **Extraction Cost**: Only 3-5 facts extracted per window (not 20-30)

---

## Implementation Checklist

### Phase 1: Storage Updates
- [ ] Verify `user_fact_relationships` table supports "myself" user_id
- [ ] Update `store_bot_fact()` to use `user_id="myself"`
- [ ] Update `get_bot_facts()` query to filter by "myself"

### Phase 2: Extraction Updates
- [ ] Add priority filtering to LLM prompt
- [ ] Implement 3-5 fact limit per conversation window
- [ ] Add HIGH/MEDIUM/LOW priority detection
- [ ] Filter out LOW priority facts before storage

### Phase 3: Testing
- [ ] Test with Jake character (simple personality)
- [ ] Verify only 3-5 facts extracted per window
- [ ] Confirm total facts stay under 20 per bot
- [ ] Validate fact quality (no "I have a pen" type facts)

### Phase 4: Monitoring
- [ ] SQL query to count facts per bot
- [ ] Alert if bot exceeds 50 facts (requires curation)
- [ ] Dashboard showing fact distribution by priority
- [ ] Track extraction rate (facts per conversation window)

---

## Example Monitoring Queries

```sql
-- Count bot self-facts by character
SELECT 
    mentioned_by_character as bot_name,
    COUNT(*) as total_facts,
    COUNT(*) FILTER (WHERE confidence > 0.9) as high_confidence,
    COUNT(*) FILTER (WHERE confidence > 0.75) as medium_confidence
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
ORDER BY total_facts DESC;

-- Alert if any bot has too many facts
SELECT 
    mentioned_by_character,
    COUNT(*) as fact_count,
    'REQUIRES CURATION' as status
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
HAVING COUNT(*) > 50;

-- Most recent bot facts
SELECT 
    mentioned_by_character,
    fe.entity_name,
    ufr.relationship_type,
    ufr.confidence,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'myself'
ORDER BY ufr.updated_at DESC
LIMIT 20;
```

---

## Success Metrics

### Quantitative
- ✅ Each bot has 10-20 core defining facts (not 100+)
- ✅ Extraction rate: 3-5 facts per 24-hour window (not 20-30)
- ✅ Zero "I have a pen" type trivial facts
- ✅ 90%+ of stored facts have confidence > 0.75

### Qualitative
- ✅ Users perceive bot personalities as consistent
- ✅ Bot responses reference their own past statements naturally
- ✅ Emergent personality traits align with CDL definitions
- ✅ No database flooding or query performance issues

---

## Comparison: Before vs After

| Aspect | Original Design | Improved Design |
|--------|----------------|-----------------|
| **User ID** | `"bot:elena"` | `"myself"` ✨ |
| **Bot Isolation** | Parse from user_id | `mentioned_by_character` field |
| **Query Pattern** | `WHERE user_id LIKE 'bot:%'` | `WHERE user_id = 'myself'` |
| **Fact Quantity** | No limit (100+ possible) | 10-20 core facts |
| **Extraction Rate** | All "I" statements | Priority-filtered (3-5 per window) |
| **Priority Levels** | None | HIGH/MEDIUM/LOW |
| **LLM Instructions** | Generic extraction | "Only identity-defining facts" |
| **Storage Size** | Large (many trivial facts) | Compact (curated facts) |
| **Context Injection** | All facts (verbose) | Top 10 facts (concise) |
| **Database Queries** | Slower (more rows) | Faster (fewer rows) |

---

## Next Steps

1. ✅ **Documentation Complete**: Both design documents updated with improvements
2. 📝 **Implementation Ready**: Clear technical specifications provided
3. 🧪 **Testing Strategy**: Start with Jake character (simple personality)
4. 🚀 **Rollout Plan**: Gradual deployment to all 10 bots

**Estimated Timeline**: 2-3 weeks from implementation to production

**User Impact**: High - dramatically improves personality consistency without database bloat

---

**Recommendation**: ✅ **PROCEED** with Phase 1 implementation using "myself" convention and priority filtering. This design is cleaner, more efficient, and more maintainable than the original approach.
