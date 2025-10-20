# Bot Self-Fact Extraction - Emergent Personality Persistence

**Date**: October 20, 2025 (Updated)  
**Status**: 🎯 Design Phase - Ready to Implement  
**Priority**: HIGH - Differentiating Feature

---

## 🎯 Key Design Decisions

1. **"myself" Convention**: Use `user_id = "myself"` instead of `"bot:elena"` for cleaner queries
2. **Priority Filtering**: Extract ONLY identity-defining facts (3-5 per window, 10-20 total per bot)
3. **I/My/Mine Focus**: Target declarative self-statements, skip casual mentions
4. **Quality Over Quantity**: Better 15 defining facts than 100 trivial mentions

---

## Overview

Enable bots to **"learn about themselves"** by extracting and storing facts from their own responses. This creates **emergent personality consistency** where bot characteristics that appear in conversations become persistent lore, even if initially "hallucinated."

### The Magic
```
Bot: "I love hiking in the mountains on weekends"
       ↓
Enrichment Worker extracts: entity="hiking", relationship="enjoys", priority=HIGH
       ↓
Stored as bot fact: user_id="myself", mentioned_by_character="elena"
       ↓
Future conversations inject: "You previously mentioned you enjoy hiking"
       ↓
Bot maintains consistency across all conversations
```

## Schema Design - Using Existing Tables! ✅

### Discovery: We Already Have the Infrastructure!

**Current table**: `user_fact_relationships`
```sql
user_id                VARCHAR(255)  -- Discord user ID for users, "myself" for bot self-facts
entity_id              UUID          -- References fact_entities
relationship_type      TEXT          -- "enjoys", "prefers", "believes", etc.
confidence             FLOAT         -- 0-1 confidence score
mentioned_by_character TEXT          -- Which bot mentioned it (for multi-bot identification)
```

### Storage Convention ✨ UPDATED

**User facts** (existing):
```sql
user_id = "123456789"                -- Discord user ID
entity_name = "pizza"
relationship_type = "likes"
mentioned_by_character = "elena"     -- Which bot learned this
```

**Bot facts** (NEW - SIMPLIFIED):
```sql
user_id = "myself"                   -- Universal bot self-reference ✨
entity_name = "hiking"
relationship_type = "enjoys"
mentioned_by_character = "elena"     -- Which bot this fact belongs to
```

**Why `"myself"` instead of `"bot:elena"`?** 🎯
- ✅ **Cleaner queries**: `WHERE user_id = 'myself' AND mentioned_by_character = $1`
- ✅ **Universal convention**: All bots use same identifier for self
- ✅ **Semantic clarity**: "myself" is self-documenting - obviously bot self-facts
- ✅ **No parsing needed**: Don't need to extract bot name from "bot:elena" string
- ✅ **Multi-bot ready**: `mentioned_by_character` handles isolation

### Why This Works

✅ **No schema changes needed** - uses existing tables  
✅ **Leverages existing indexes** - all queries work the same  
✅ **Unified API** - same `store_user_fact()` method  
✅ **Simple queries** - `user_id = 'myself' AND mentioned_by_character = 'elena'`  
✅ **Multi-bot ready** - `mentioned_by_character` provides bot isolation  
✅ **Semantic elegance** - "myself" is self-documenting and universal  

## Implementation Plan

### Phase 1: Enrichment Worker (Bot Fact Extraction)

**File**: `src/enrichment/fact_extraction_engine.py`

**Current**: Only extracts user facts
```python
async def extract_facts_from_conversation_window(
    messages: List[Dict],
    user_id: str,
    bot_name: str
) -> List[Dict]:
    """Extract facts about USER"""
```

**Updated**: Extract both user AND bot facts
```python
async def extract_facts_from_conversation_window(
    messages: List[Dict],
    user_id: str,
    bot_name: str
) -> Dict[str, List[Dict]]:
    """
    Extract facts about BOTH user and bot
    
    Returns:
        {
            'user_facts': [...],  # Existing
            'bot_facts': [...]    # NEW
        }
    """
```

**LLM Prompt Enhancement** 🎯 PRIORITY FILTERING:
```python
prompt = f"""Analyze this conversation and extract ONLY THE MOST DEFINING facts about BOTH parties.

IMPORTANT: For {bot_name}'s self-facts, ONLY extract statements that are:
1. **Identity-defining** (core personality traits, strong preferences)
2. **Declarative "I/my/mine" statements** ("I love...", "I prefer...", "My passion is...")
3. **High confidence** (clear, unambiguous statements)
4. **Not trivial** (skip casual mentions, focus on meaningful characteristics)

DO NOT extract:
- Casual mentions ("I saw a bird today")
- Temporary states ("I'm tired right now")
- Generic politeness ("I enjoy talking with you")
- Every single item owned ("I have a pen")

Conversation:
{formatted_messages}

Extract PRIORITY bot facts when {bot_name} makes DEFINING statements like:
✅ "I love exploring ocean depths" → entity: "ocean exploration", type: "passion", priority: HIGH
✅ "I prefer collaborative discussions over debates" → entity: "collaborative discussions", type: "communication_style", priority: HIGH
✅ "My morning routine always includes reviewing marine research" → entity: "marine research review", type: "habit", priority: MEDIUM
✅ "I find bioluminescence absolutely fascinating" → entity: "bioluminescence", type: "fascination", priority: HIGH

❌ "I'm having coffee right now" → TOO TRIVIAL, skip
❌ "I own a laptop" → NOT DEFINING, skip
❌ "I like this conversation" → TOO GENERIC, skip

Return JSON with ONLY HIGH-PRIORITY facts:
{{
    "user_facts": [
        {{"entity_name": "pizza", "entity_type": "food", "relationship_type": "likes", "confidence": 0.9, "priority": "high"}}
    ],
    "bot_facts": [
        {{"entity_name": "ocean exploration", "entity_type": "passion", "relationship_type": "loves", "confidence": 0.95, "priority": "high"}},
        {{"entity_name": "collaborative discussions", "entity_type": "communication_style", "relationship_type": "prefers", "confidence": 0.9, "priority": "high"}}
    ]
}}

CRITICAL: Limit to 3-5 HIGHEST PRIORITY bot facts per conversation window. Quality over quantity!
"""
```

### Phase 2: Storage (Knowledge Router)

**File**: `src/memory/knowledge_router.py`

**New method**:
```python
async def store_bot_fact(
    self,
    bot_name: str,
    entity_name: str,
    entity_type: str,
    relationship_type: str,
    confidence: float = 0.8,
    emotional_context: str = 'neutral',
    source_conversation_id: str = None
) -> bool:
    """
    Store a fact about the bot character itself using "myself" convention.
    
    Uses existing user_fact_relationships table with:
    - user_id = "myself" (universal bot self-reference)
    - mentioned_by_character = bot_name (which bot this fact belongs to)
    
    This enables bots to "learn about themselves" and maintain
    personality consistency across conversations.
    
    Example:
        await store_bot_fact(
            bot_name="elena",
            entity_name="ocean exploration",
            relationship_type="loves"
        )
        
        → Stores as: user_id="myself", mentioned_by_character="elena"
    """
    
    return await self.store_user_fact(
        user_id="myself",  # ✨ Universal bot self-reference
        entity_name=entity_name,
        entity_type=entity_type,
        relationship_type=relationship_type,
        confidence=confidence,
        emotional_context=emotional_context,
        mentioned_by_character=bot_name,  # Which bot owns this fact
        source_conversation_id=source_conversation_id
    )
```

**New retrieval method**:
```python
async def get_bot_facts(
    self,
    bot_name: str,
    entity_types: List[str] = None,
    min_confidence: float = 0.7,
    limit: int = 20
) -> List[Dict]:
    """
    Retrieve facts about the bot character itself using "myself" convention.
    
    Returns top facts ordered by:
    1. Confidence (how certain we are)
    2. Recency (recently mentioned)
    3. Priority (if we add priority field later)
    
    Example:
        bot_facts = await get_bot_facts("elena", min_confidence=0.75, limit=10)
        # Returns Elena's self-facts with confidence >= 0.75
    """
    
    query = """
        SELECT 
            fe.entity_name,
            fe.entity_type,
            ufr.relationship_type,
            ufr.confidence,
            ufr.emotional_context,
            ufr.updated_at
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = 'myself'                      -- Bot self-facts only
          AND ufr.mentioned_by_character = $1             -- Specific bot
          AND ($2::text[] IS NULL OR fe.entity_type = ANY($2))
          AND ufr.confidence >= $3
        ORDER BY ufr.confidence DESC, ufr.updated_at DESC
        LIMIT $4
    """
    
    rows = await self.db_pool.fetch(
        query, bot_name, entity_types, min_confidence, limit
    )
    
    return [dict(row) for row in rows]
```

### Phase 3: Context Injection (Message Processor)

**File**: `src/core/message_processor.py`

**Inject bot facts into system prompt**:
```python
async def _build_system_prompt(...):
    # ... existing CDL system prompt ...
    
    # NEW: Inject bot self-facts for consistency
    if hasattr(self.bot_core, 'knowledge_router'):
        bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant')
        bot_facts = await self.bot_core.knowledge_router.get_bot_facts(
            bot_name=bot_name,
            min_confidence=0.75,
            limit=10  # Only top 10 most confident facts
        )
        
        if bot_facts:
            fact_context = "\n\nYour established characteristics (maintain consistency):\n"
            for fact in bot_facts:
                fact_context += f"- You {fact['relationship_type']} {fact['entity_name']}\n"
            
            system_prompt += fact_context
    
    return system_prompt
```

## Example Scenarios

### Scenario 1: Elena (Marine Biologist)

**Conversation 1** (Week 1):
```
User: What do you like to do in your free time?
Elena: I absolutely love exploring tidal pools during low tide! There's something 
       magical about discovering small crustaceans and observing their behaviors.
```

**Enrichment worker extracts** (PRIORITY FILTERING APPLIED):
- `myself` (elena) → "tidal pool exploration" → "enjoys" (confidence: 0.9, priority: HIGH)
- `myself` (elena) → "crustacean observation" → "fascinates" (confidence: 0.85, priority: HIGH)

**Skipped**: ❌ "tide pools" (too generic), ❌ "free time" (not identity-defining)

**Conversation 2** (Week 3, different user):
```
System prompt injection:
"Your established characteristics:
- You enjoy tidal pool exploration
- You are fascinated by crustacean observation"

User: Any hobbies outside of work?
Elena: Yes! I often spend my weekends exploring tidal pools. I find crustacean 
       behavior absolutely fascinating - it's become quite the hobby!
```

**Result**: Consistent personality across users and time! ✅

### Scenario 2: Marcus (AI Researcher)

**Conversation 1**:
```
User: What's your coffee preference?
Marcus: I'm actually a tea person. Earl Grey, specifically. I find the bergamot 
        helps me focus during long research sessions.
```

**Enrichment worker extracts** (PRIORITY FILTERING APPLIED):
- `myself` (marcus) → "Earl Grey tea" → "prefers" (confidence: 0.9, priority: HIGH)
- `myself` (marcus) → "tea over coffee" → "drinks" (confidence: 0.85, priority: MEDIUM)

**Skipped**: ❌ "long research sessions" (contextual, not identity-defining), ❌ "bergamot" (too specific)

**Conversation 2** (different user):
```
User: Want to grab coffee?
Marcus: I appreciate the offer, but I'm more of a tea person! Earl Grey is my go-to. 
        Perhaps we could meet at a café that serves good tea?
```

**Result**: Marcus maintains his tea preference consistently! ✅

### Scenario 3: Emergent Personality Evolution

**Month 1**: Elena mentions ocean exploration (general)  
**Month 2**: Elena mentions bioluminescence fascination (specific)  
**Month 3**: Elena mentions deep sea diving (activity)  
**Month 4**: Elena mentions hydrothermal vents (specialized interest)

**Evolution tracked** (only HIGH-PRIORITY facts stored):
```sql
SELECT entity_name, confidence, created_at 
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'myself' 
  AND ufr.mentioned_by_character = 'elena'
ORDER BY created_at ASC;

-- Result: Only 10-15 DEFINING facts instead of 100+ trivial mentions
```

Result: Bot's personality **deepens naturally** over time through conversations!

## Priority Filtering Strategy 🎯 CRITICAL

### Why Not Store Everything?

**Problem**: Without filtering, we'd flood the database with trivial facts:
- "I have a computer" (generic tool)
- "I'm typing right now" (temporary state)
- "I saw your message" (obvious interaction)
- "I like talking with you" (politeness, not preference)

**Solution**: Extract ONLY identity-defining facts using priority rules.

### Priority Levels

**HIGH PRIORITY** (✅ Always store):
- Strong "I/my/mine" declarations: "I love", "I prefer", "I always"
- Core personality traits: "I'm passionate about", "I believe in"
- Defining habits/routines: "Every morning I", "My go-to approach"
- Strong fascinations: "I find X absolutely fascinating"
- Professional identity: "My research focuses on", "I specialize in"

**MEDIUM PRIORITY** (✅ Store if confident):
- Moderate preferences: "I enjoy", "I like", "I tend to"
- Hobby mentions: "I often", "I sometimes"
- Communication styles: "I prefer collaborative discussions"
- Interest areas: "I'm interested in"

**LOW PRIORITY** (❌ Skip):
- Temporary states: "I'm tired", "I'm busy right now"
- Generic ownership: "I have a laptop", "I own a pen"
- Politeness phrases: "I appreciate that", "I'm glad to help"
- Contextual reactions: "I see what you mean", "I understand"
- Casual mentions: "I noticed", "I saw", "I heard"

### LLM Instruction Examples

**Extract**: ✅
- "I **love** exploring ocean depths" → HIGH priority, strong preference
- "**My passion** is marine conservation" → HIGH priority, identity-defining
- "I **always** review research papers in the morning" → HIGH priority, defining habit
- "I **prefer** collaborative discussions over debates" → MEDIUM priority, communication style
- "I find bioluminescence **absolutely fascinating**" → HIGH priority, strong fascination

**Skip**: ❌
- "I'm having coffee right now" → Temporary state, LOW priority
- "I have a laptop" → Generic ownership, LOW priority
- "I like this conversation" → Politeness, LOW priority
- "I saw your message" → Contextual interaction, LOW priority
- "I think that's interesting" → Weak opinion, LOW priority

### Extraction Limits

**Per conversation window** (24 hours):
- Maximum 3-5 bot self-facts extracted
- Only HIGH and MEDIUM priority facts
- Prevents database flooding
- Focus on quality over quantity

**Total per bot** (recommended):
- Target: 10-20 core defining facts
- Maximum: 50 facts before requiring curation
- Alert if approaching limit: "Elena has 45 self-facts, consider review"

### SQL Monitoring Query

```sql
-- Check bot self-fact counts and priorities
SELECT 
    mentioned_by_character as bot_name,
    COUNT(*) as total_facts,
    COUNT(*) FILTER (WHERE confidence > 0.9) as high_confidence_facts,
    COUNT(*) FILTER (WHERE confidence > 0.75) as medium_confidence_facts,
    MAX(updated_at) as most_recent_fact
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
ORDER BY total_facts DESC;

-- Alert if any bot exceeds 50 facts
SELECT mentioned_by_character, COUNT(*) as fact_count
FROM user_fact_relationships
WHERE user_id = 'myself'
GROUP BY mentioned_by_character
HAVING COUNT(*) > 50;
```

## Quality Control & Safeguards

### 1. Confidence Thresholds

**Extraction confidence**:
- High confidence (>0.8): "I love X", "I prefer Y", "I always Z"
- Medium confidence (0.5-0.8): "I enjoy X", "I like Y"
- Low confidence (<0.5): "I might like X", "Maybe Y" (❌ Don't extract)

**Injection threshold**:
- Only inject facts with confidence >0.75 into context
- Prevents weak/uncertain facts from reinforcing

### 2. Contradiction Detection

**Scenario**: Bot changes preferences
```
Week 1: "I love coffee" → stored
Week 4: "I prefer tea now" → extract new fact
```

**Resolution strategy**:
```python
async def handle_contradicting_fact(old_fact, new_fact):
    # Option A: Update relationship_type to "used_to_{relationship}"
    # "I used to love coffee, but now I prefer tea"
    
    # Option B: Decay old fact confidence
    old_fact.confidence *= 0.5
    
    # Option C: Track temporal evolution
    # Store both with timestamps
```

### 3. CDL Compatibility Check (Optional)

**Validate against character archetype**:
```python
async def validate_bot_fact_cdl_compatibility(bot_name, fact):
    """
    Optional: Check if fact aligns with CDL personality
    
    Elena (Marine Biologist):
    ✅ "ocean exploration" → Compatible
    ✅ "marine research" → Compatible
    ⚠️ "mountain climbing" → Unexpected but allowable
    ❌ "hates the ocean" → CDL violation
    """
    character = await get_character_profile(bot_name)
    
    # Check if fact contradicts core personality
    if fact_contradicts_core_traits(fact, character):
        return False  # Don't store
    
    return True  # Store
```

### 4. Fact Decay & Reinforcement

**Reinforce frequently mentioned facts**:
```sql
-- Update confidence when fact is mentioned again
UPDATE user_fact_relationships
SET 
    confidence = LEAST(1.0, confidence + 0.1),  -- Cap at 1.0
    updated_at = NOW()
WHERE user_id = 'bot:elena'
  AND entity_id = (SELECT id FROM fact_entities WHERE entity_name = 'tidal pools')
```

**Decay facts not mentioned in 60 days**:
```sql
-- Scheduled job: Decay old bot facts
UPDATE user_fact_relationships
SET confidence = confidence * 0.9
WHERE user_id LIKE 'bot:%'
  AND updated_at < NOW() - INTERVAL '60 days'
  AND confidence > 0.3;  -- Stop decaying below 0.3
```

## Monitoring & Analytics

### SQL Queries

**1. Bot fact count per character**:
```sql
SELECT 
    REPLACE(user_id, 'bot:', '') as bot_name,
    COUNT(*) as fact_count,
    AVG(confidence) as avg_confidence
FROM user_fact_relationships
WHERE user_id LIKE 'bot:%'
GROUP BY user_id
ORDER BY fact_count DESC;
```

**2. Most confident bot facts**:
```sql
SELECT 
    REPLACE(ufr.user_id, 'bot:', '') as bot_name,
    fe.entity_name,
    fe.entity_type,
    ufr.relationship_type,
    ufr.confidence,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id LIKE 'bot:%'
  AND ufr.confidence > 0.8
ORDER BY ufr.confidence DESC, ufr.updated_at DESC
LIMIT 50;
```

**3. Bot personality evolution timeline**:
```sql
SELECT 
    fe.entity_name,
    ufr.relationship_type,
    ufr.confidence,
    ufr.created_at,
    ufr.updated_at,
    EXTRACT(DAY FROM (NOW() - ufr.created_at)) as days_old
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'bot:elena'
ORDER BY ufr.created_at ASC;
```

**4. Contradicting facts detection**:
```sql
-- Find facts with opposite relationships for same entity
WITH bot_facts AS (
    SELECT 
        ufr.user_id,
        fe.entity_name,
        ufr.relationship_type,
        ufr.confidence,
        ufr.created_at
    FROM user_fact_relationships ufr
    JOIN fact_entities fe ON ufr.entity_id = fe.id
    WHERE ufr.user_id LIKE 'bot:%'
)
SELECT 
    bf1.user_id as bot,
    bf1.entity_name,
    bf1.relationship_type as relationship1,
    bf2.relationship_type as relationship2,
    bf1.confidence as conf1,
    bf2.confidence as conf2,
    bf1.created_at as first_mention,
    bf2.created_at as second_mention
FROM bot_facts bf1
JOIN bot_facts bf2 ON 
    bf1.user_id = bf2.user_id 
    AND bf1.entity_name = bf2.entity_name
    AND bf1.relationship_type != bf2.relationship_type
WHERE 
    (bf1.relationship_type = 'likes' AND bf2.relationship_type = 'dislikes')
    OR (bf1.relationship_type = 'loves' AND bf2.relationship_type = 'hates')
    OR (bf1.relationship_type = 'enjoys' AND bf2.relationship_type = 'dislikes');
```

## Benefits & Impact

### User Experience
- ✅ **Consistent character personalities** across conversations
- ✅ **Deeper character development** over time
- ✅ **Multi-user shared lore** (all users experience same character)
- ✅ **Emergent storytelling** (characters "discover" themselves)

### Technical Benefits
- ✅ **No schema changes** required (uses existing tables)
- ✅ **Minimal code changes** (~200 lines total)
- ✅ **Leverages existing infrastructure** (enrichment worker, knowledge router)
- ✅ **Fast implementation** (1-2 weeks to production)

### Competitive Differentiation
- 🚀 **Novel approach** to AI character consistency
- 🚀 **Research-worthy** technique (emergent personality persistence)
- 🚀 **WhisperEngine exclusive** (no one else does this)
- 🚀 **Platform differentiator** for multi-character systems

## Risks & Mitigations

### Risk 1: Character Drift
**Problem**: Bot personality changes too much over time  
**Mitigation**: 
- CDL compatibility validation (optional)
- Confidence thresholds for injection (>0.75)
- Manual fact curation tools for admins

### Risk 2: Fact Explosion
**Problem**: Too many facts stored (1000s per bot)  
**Mitigation**:
- Only inject top 10-20 facts (by confidence)
- Decay mechanism for old facts
- Fact deduplication logic

### Risk 3: Hallucination Persistence
**Problem**: Bot "hallucinates" impossible facts  
**Mitigation**:
- Accept it as character lore (fantasy bots)
- CDL validation for realistic bots (optional)
- Admin tools to delete inappropriate facts

### Risk 4: CDL Conflicts
**Problem**: Bot facts contradict CDL personality  
**Mitigation**:
- Treat bot facts as "additions" not "replacements"
- CDL takes precedence in conflicts
- Option to disable bot fact injection per character

## Timeline & Phases

### Phase 1: Passive Collection (Week 1)
- ✅ Enable bot fact extraction in enrichment worker
- ✅ Store facts with `bot:{name}` user_id pattern
- ⏸️ DON'T inject into context yet
- 📊 Monitor: What facts get extracted? Quality check.

**Deliverables**:
- Modified `fact_extraction_engine.py` (+50 lines)
- New `store_bot_fact()` method in `knowledge_router.py` (+30 lines)
- Monitoring SQL queries (provided above)

### Phase 2: Retrieval System (Week 2)
- ✅ Implement `get_bot_facts()` method
- ✅ Add fact filtering by confidence/recency
- ✅ Build contradiction detection
- 📊 Monitor: Fact quality distribution

**Deliverables**:
- `get_bot_facts()` method (+40 lines)
- Contradiction detection logic (+30 lines)
- Admin query dashboard

### Phase 3: Context Injection (Week 3)
- ✅ Add bot facts to system prompt
- ✅ A/B test with 50% of users
- ✅ Collect user feedback
- 📊 Monitor: Personality consistency scores

**Deliverables**:
- Modified `_build_system_prompt()` (+20 lines)
- A/B testing infrastructure
- User feedback collection

### Phase 4: Refinement (Week 4)
- ✅ Tune confidence thresholds
- ✅ Implement fact decay mechanism
- ✅ Add CDL compatibility check (if needed)
- 🚀 Full rollout to 100% of users

**Deliverables**:
- Optimized thresholds based on A/B test
- Scheduled decay job
- Production monitoring

## Decision: Should We Build This?

### ✅ YES if you want:
- Emergent, self-consistent AI characters
- Novel approach to personality persistence
- Research-worthy innovation
- Platform differentiation
- Minimal engineering cost (1-2 weeks)

### ❌ NO if you want:
- Strict CDL-only personalities
- Zero character drift
- Predictable, template-based characters

## My Recommendation

**SHIP IT!** 🚀

This is:
1. **Technically simple** (uses existing infrastructure)
2. **Strategically valuable** (differentiating feature)
3. **Research-worthy** (novel approach)
4. **Low risk** (can disable per-character if needed)
5. **Fast to implement** (2-4 weeks total)

The emergent personality consistency this creates is genuinely innovative and could become a defining feature of WhisperEngine.

---

**Next Step**: Approve Phase 1 and I'll implement bot fact extraction in the enrichment worker.
