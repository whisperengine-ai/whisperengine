# Character Backstory Query Routing

**Date**: October 20, 2025  
**Status**: Design Phase  
**Purpose**: Enable consistent character responses to biographical questions via query routing to CDL database

---

## Problem Statement

Characters need to provide **consistent, factual responses** to biographical questions like:
- "Where do you work?"
- "Where do you live?"  
- "What's your background?"
- "Tell me about your hometown"
- "What do you do for work?"

**Current State**: These questions generate **inconsistent, hallucinated responses** because the bot has no persistent biographical memory.

**Desired State**: Character biographical facts stored in PostgreSQL CDL database and retrieved via **intelligent query routing**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Question Flow                            │
└─────────────────────────────────────────────────────────────────┘
                               |
                   "Where do you work?"
                               |
                               ↓
                ┌──────────────────────────┐
                │  SemanticKnowledgeRouter │
                │  Query Intent Analysis    │
                └──────────────────────────┘
                               |
                    Intent Classification
                               |
        ┌──────────────────────┼──────────────────────┐
        |                      |                       |
   FACTUAL_RECALL    PERSONALITY_KNOWLEDGE    CONVERSATION_STYLE
        |                      |                       |
        ↓                      ↓                       ↓
┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PostgreSQL   │    │ CDL Database     │    │ Qdrant Vector   │
│ User Facts   │    │ Character Facts  │    │ Conversations   │
└──────────────┘    └──────────────────┘    └─────────────────┘
        |                      |                       |
        └──────────────────────┴───────────────────────┘
                               |
                    Inject into system prompt
                               |
                               ↓
                       ┌──────────────┐
                       │ Bot Response │
                       └──────────────┘
```

---

## Data Storage Design

### **Option 1: Use Existing `character_background` Table** ✅ RECOMMENDED

**Schema**:
```sql
-- Current table structure (check migrations for exact schema)
CREATE TABLE character_background (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(200),  -- 'workplace', 'hometown', 'education', 'career', etc.
    content TEXT,           -- The actual backstory content
    importance VARCHAR(100), -- 'high', 'medium', 'low'
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Example Data**:
```sql
INSERT INTO character_background (character_id, category, content, importance) VALUES
    (1, 'workplace', 'Marine Research Institute at UC Santa Barbara', 'high'),
    (1, 'hometown', 'Coastal town in Northern California', 'medium'),
    (1, 'education', 'PhD in Marine Biology from Scripps Institution of Oceanography', 'high'),
    (1, 'residence', 'Small apartment near the beach in Santa Barbara', 'medium');
```

**Pros**:
- ✅ Table already exists
- ✅ Structured category system
- ✅ Importance weighting built-in
- ✅ Character-specific with FK constraints

**Cons**:
- ⚠️ Need to check exact schema via migrations (don't trust init_schema.sql!)

---

### **Option 2: Use `character_identity_details` Table**

**Schema**:
```sql
CREATE TABLE character_identity_details (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    full_name VARCHAR(500),
    nicknames TEXT,
    age INTEGER,
    occupation VARCHAR(500),  -- ✅ WORKPLACE
    location VARCHAR(500),     -- ✅ RESIDENCE
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Pros**:
- ✅ Simple single-row-per-character design
- ✅ Dedicated fields for occupation and location
- ✅ Already used for basic identity

**Cons**:
- ⚠️ Limited flexibility (fixed columns)
- ⚠️ Can't store multiple workplaces or historical locations
- ⚠️ No importance/priority system

---

### **Option 3: New `character_biographical_facts` Table** (Custom)

**Schema**:
```sql
CREATE TABLE character_biographical_facts (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    fact_category VARCHAR(100) NOT NULL, -- 'workplace', 'hometown', 'education', etc.
    fact_key VARCHAR(200) NOT NULL,      -- 'current_job', 'birthplace', 'degree', etc.
    fact_value TEXT NOT NULL,            -- Actual content
    confidence DECIMAL(3,2) DEFAULT 1.00, -- Designer vs emergent
    source VARCHAR(50) DEFAULT 'designer', -- 'designer', 'bot_statement', 'inferred'
    priority INTEGER DEFAULT 0,           -- Higher = more important
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(character_id, fact_category, fact_key)
);

CREATE INDEX idx_char_bio_facts_lookup 
    ON character_biographical_facts(character_id, fact_category);
```

**Example Data**:
```sql
INSERT INTO character_biographical_facts 
    (character_id, fact_category, fact_key, fact_value, priority, source) 
VALUES
    (1, 'workplace', 'institution', 'Marine Research Institute at UC Santa Barbara', 10, 'designer'),
    (1, 'workplace', 'position', 'Senior Marine Biologist', 9, 'designer'),
    (1, 'residence', 'city', 'Santa Barbara, California', 8, 'designer'),
    (1, 'residence', 'housing', 'Small beachfront apartment', 5, 'designer'),
    (1, 'education', 'highest_degree', 'PhD in Marine Biology', 9, 'designer'),
    (1, 'education', 'institution', 'Scripps Institution of Oceanography', 8, 'designer'),
    (1, 'hometown', 'location', 'Coastal town in Northern California', 6, 'designer');
```

**Pros**:
- ✅ Maximum flexibility
- ✅ Key-value design allows arbitrary facts
- ✅ Confidence + source tracking (designer vs emergent)
- ✅ Priority system for prompt injection order
- ✅ Clean query patterns

**Cons**:
- ⚠️ Requires new Alembic migration
- ⚠️ More complex than using existing tables

---

## Query Routing Implementation

### **Phase 1: Intent Detection** (Already Exists!)

**File**: `src/knowledge/semantic_router.py`

**Current Intent Types**:
```python
class QueryIntent(Enum):
    FACTUAL_RECALL = "factual_recall"           # User facts
    PERSONALITY_KNOWLEDGE = "personality_knowledge"  # Character facts ✅
    CONVERSATION_STYLE = "conversation_style"    # How we talked
    TEMPORAL_ANALYSIS = "temporal_analysis"      # Changes over time
    RELATIONSHIP_DISCOVERY = "relationship_discovery"  # Similar things
    ENTITY_SEARCH = "entity_search"             # Generic search
    USER_ANALYTICS = "user_analytics"           # About the user
```

**Pattern Matching** (needs expansion):
```python
QueryIntent.PERSONALITY_KNOWLEDGE: {
    "keywords": [
        # ADD THESE:
        "where do you work", "where do you live", "what do you do",
        "your job", "your workplace", "your home", "your background",
        "tell me about yourself", "your hometown", "where are you from",
        "what's your occupation", "where did you study", "your education"
    ],
    "entities": [
        "workplace", "home", "job", "occupation", "background",
        "hometown", "residence", "education", "career", "family"
    ]
}
```

---

### **Phase 2: Backstory Retrieval** (NEW!)

**File**: `src/characters/cdl/character_backstory_retriever.py` (NEW)

```python
"""
Character Backstory Retrieval - Consistent Biographical Facts

Retrieves character biographical information from CDL database
for consistent responses to "where do you work" style questions.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BackstoryFact:
    """A single biographical fact about a character"""
    category: str           # 'workplace', 'hometown', 'education', etc.
    key: str               # 'institution', 'position', 'city', etc.
    value: str             # Actual content
    priority: int = 0      # Higher = more important
    confidence: float = 1.0  # Designer-defined = 1.0
    source: str = "designer"  # 'designer', 'bot_statement', 'inferred'


class CharacterBackstoryRetriever:
    """
    Retrieves character biographical facts from CDL database.
    
    Supports multiple storage strategies:
    - character_background table (existing)
    - character_identity_details table (existing)
    - character_biographical_facts table (proposed)
    """
    
    def __init__(self, postgres_pool):
        self.postgres = postgres_pool
        logger.info("🎭 CharacterBackstoryRetriever initialized")
    
    async def get_backstory_facts(
        self,
        character_name: str,
        categories: Optional[List[str]] = None
    ) -> List[BackstoryFact]:
        """
        Retrieve character backstory facts by category.
        
        Args:
            character_name: Character identifier (e.g., 'elena', 'marcus')
            categories: Optional filter (e.g., ['workplace', 'hometown'])
                       If None, returns all facts
        
        Returns:
            List of BackstoryFact objects sorted by priority (high to low)
        """
        
        async with self.postgres.acquire() as conn:
            # Option 1: Query character_background table
            if categories:
                query = """
                    SELECT cb.category, cb.content, cb.importance
                    FROM character_background cb
                    JOIN characters c ON cb.character_id = c.id
                    WHERE c.name = $1 AND cb.category = ANY($2) AND cb.active = true
                    ORDER BY 
                        CASE cb.importance
                            WHEN 'high' THEN 3
                            WHEN 'medium' THEN 2
                            ELSE 1
                        END DESC
                """
                rows = await conn.fetch(query, character_name, categories)
            else:
                query = """
                    SELECT cb.category, cb.content, cb.importance
                    FROM character_background cb
                    JOIN characters c ON cb.character_id = c.id
                    WHERE c.name = $1 AND cb.active = true
                    ORDER BY 
                        CASE cb.importance
                            WHEN 'high' THEN 3
                            WHEN 'medium' THEN 2
                            ELSE 1
                        END DESC
                """
                rows = await conn.fetch(query, character_name)
            
            # Convert to BackstoryFact objects
            facts = []
            for row in rows:
                priority = {'high': 10, 'medium': 5, 'low': 1}.get(row['importance'], 0)
                facts.append(BackstoryFact(
                    category=row['category'],
                    key='content',  # character_background uses single content field
                    value=row['content'],
                    priority=priority,
                    confidence=1.0,
                    source='designer'
                ))
            
            logger.info(
                f"🎭 Retrieved {len(facts)} backstory facts for {character_name}",
                extra={"categories": categories or "all"}
            )
            
            return facts
    
    async def get_workplace_info(self, character_name: str) -> Optional[str]:
        """Quick helper: Get character's workplace"""
        facts = await self.get_backstory_facts(character_name, categories=['workplace'])
        return facts[0].value if facts else None
    
    async def get_hometown_info(self, character_name: str) -> Optional[str]:
        """Quick helper: Get character's hometown"""
        facts = await self.get_backstory_facts(character_name, categories=['hometown'])
        return facts[0].value if facts else None
    
    async def get_education_info(self, character_name: str) -> Optional[str]:
        """Quick helper: Get character's education"""
        facts = await self.get_backstory_facts(character_name, categories=['education'])
        return facts[0].value if facts else None
```

---

### **Phase 3: CDL Prompt Integration** (MODIFY EXISTING)

**File**: `src/prompts/cdl_ai_integration.py`

**Add backstory section to system prompt**:

```python
class CDLAIPromptIntegration:
    def __init__(self):
        self.postgres_pool = get_postgres_pool()
        self.backstory_retriever = CharacterBackstoryRetriever(self.postgres_pool)  # NEW
    
    async def create_character_aware_prompt(
        self,
        character_name: str,
        user_id: str,
        message_content: str
    ) -> str:
        """Build system prompt with character personality + backstory"""
        
        # Existing personality/CDL loading...
        personality = await self._load_character_personality(character_name)
        
        # NEW: Load backstory facts
        backstory_facts = await self.backstory_retriever.get_backstory_facts(character_name)
        
        # Build prompt sections
        prompt_parts = [
            self._build_identity_section(personality),
            self._build_personality_section(personality),
            self._build_backstory_section(backstory_facts),  # NEW!
            self._build_communication_section(personality),
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_backstory_section(self, facts: List[BackstoryFact]) -> str:
        """
        Build backstory section for system prompt.
        
        Example output:
        ## Your Background
        
        **Workplace**: Marine Research Institute at UC Santa Barbara
        **Position**: Senior Marine Biologist
        **Residence**: Small beachfront apartment in Santa Barbara, California
        **Education**: PhD in Marine Biology from Scripps Institution of Oceanography
        **Hometown**: Coastal town in Northern California
        
        These are factual details about your life. When asked biographical questions,
        reference these facts for consistency.
        """
        
        if not facts:
            return ""
        
        # Group facts by category
        grouped = {}
        for fact in facts:
            if fact.category not in grouped:
                grouped[fact.category] = []
            grouped[fact.category].append(fact)
        
        # Build section
        lines = ["## Your Background\n"]
        
        for category in ['workplace', 'residence', 'education', 'hometown', 'family', 'career']:
            if category in grouped:
                category_facts = grouped[category]
                for fact in category_facts:
                    # Format category nicely
                    display_category = category.replace('_', ' ').title()
                    lines.append(f"**{display_category}**: {fact.value}")
        
        lines.append(
            "\nThese are factual details about your life. When asked biographical "
            "questions, reference these facts for consistency."
        )
        
        return "\n".join(lines)
```

---

### **Phase 4: Query Analysis Integration** (MODIFY EXISTING)

**File**: `src/core/message_processor.py` or similar

**Decision Point**: Where to integrate backstory retrieval?

**Option A: Pre-prompt (System Prompt Injection)** ✅ RECOMMENDED
- Backstory facts injected into system prompt BEFORE LLM call
- Bot naturally references facts in response
- No special handling needed
- Most personality-authentic

**Option B: Post-routing (Explicit Fact Lookup)**
- Detect biographical question via SemanticRouter
- Query CDL database directly
- Template response: "I work at {workplace}"
- Less natural, more deterministic

**Option C: Hybrid (Context + Templates)**
- System prompt has backstory context
- Direct questions get template-enhanced responses
- Balance between authenticity and consistency

---

## Implementation Roadmap

### **Phase 1: Schema Validation (Week 1)**
- [ ] Run Alembic migrations to identify current `character_background` schema
- [ ] Query existing characters to check if backstory data exists
- [ ] Document actual table structure (DON'T USE init_schema.sql!)
- [ ] Decide: Use existing table or create `character_biographical_facts`

### **Phase 2: Data Population (Week 1)**
- [ ] Create backstory facts for test character (Jake - simple personality)
- [ ] Write SQL INSERT scripts for all 10 characters
- [ ] Validate data integrity and consistency
- [ ] Test queries for workplace, hometown, education

### **Phase 3: Retrieval Implementation (Week 2)**
- [ ] Create `src/characters/cdl/character_backstory_retriever.py`
- [ ] Implement `CharacterBackstoryRetriever` class
- [ ] Add helper methods (get_workplace_info, get_hometown_info, etc.)
- [ ] Unit tests for retrieval logic

### **Phase 4: CDL Integration (Week 2)**
- [ ] Modify `CDLAIPromptIntegration.create_character_aware_prompt()`
- [ ] Add `_build_backstory_section()` method
- [ ] Test system prompt generation with backstory facts
- [ ] Validate prompt length doesn't exceed LLM context limits

### **Phase 5: Query Routing Enhancement (Week 3)**
- [ ] Expand `SemanticKnowledgeRouter` patterns for biographical questions
- [ ] Add "where do you work", "where do you live" keywords
- [ ] Test intent classification accuracy
- [ ] Monitor false positives/negatives

### **Phase 6: HTTP API Testing (Week 3)**
- [ ] Test via `/api/chat` endpoint: "Where do you work?"
- [ ] Validate consistent responses across multiple queries
- [ ] Test all 10 characters' backstory retrieval
- [ ] Compare responses WITH vs WITHOUT backstory facts

### **Phase 7: Discord Testing (Week 4)**
- [ ] Test with real Discord users asking biographical questions
- [ ] Monitor response consistency over time
- [ ] Gather feedback on naturalness vs. rigidity
- [ ] A/B test: Backstory injection vs. No backstory

### **Phase 8: Production Rollout (Week 4)**
- [ ] Deploy to all 10 character bots
- [ ] Enable backstory injection by default
- [ ] Monitor LLM prompt token usage (watch for context overflow)
- [ ] Document feature in character tuning guide

---

## Example User Interactions

### **Scenario 1: Direct Workplace Question**

**User**: "Where do you work?"

**Without Backstory Routing**: 
> "Oh, I work at various marine research facilities! Mostly around California. 😊"  
> *(Vague, inconsistent, hallucinated)*

**With Backstory Routing**:
> "I work at the Marine Research Institute at UC Santa Barbara! 🌊 It's an incredible place - right on the coast with direct access to some amazing tide pool ecosystems."  
> *(Specific, consistent, grounded in database facts)*

---

### **Scenario 2: Hometown Question**

**User**: "Where are you from?"

**Without Backstory Routing**:
> "I grew up in a small town near the ocean! 🏖️"  
> *(Generic, changes every conversation)*

**With Backstory Routing**:
> "I'm from a coastal town in Northern California! Growing up near the ocean definitely shaped my love for marine biology. Those early years exploring tide pools sparked everything. 🐚"  
> *(Specific, consistent, personality-authentic)*

---

### **Scenario 3: Education Question**

**User**: "What did you study?"

**Without Backstory Routing**:
> "I studied marine biology! 📚🌊"  
> *(True but vague)*

**With Backstory Routing**:
> "I did my PhD in Marine Biology at Scripps Institution of Oceanography! 🎓 It's one of the world's premier marine research institutions. My dissertation focused on crustacean behavior in changing ocean temperatures."  
> *(Detailed, consistent, establishes authority)*

---

## Integration with Other Systems

### **Relationship to Bot Self-Fact Extraction**

**Bot Self-Facts** (Emergent):
- "I love tidal pool exploration" (bot said this in conversation)
- "I prefer morning fieldwork" (bot mentioned this preference)
- "Coffee helps me focus" (bot stated this habit)

**Backstory Facts** (Designer-Defined):
- "I work at Marine Research Institute" (static, CDL database)
- "I grew up in Northern California" (static, CDL database)
- "I have a PhD from Scripps" (static, CDL database)

**Combined System Prompt**:
```
## Your Background (Static Facts)
**Workplace**: Marine Research Institute at UC Santa Barbara
**Education**: PhD in Marine Biology from Scripps Institution
**Hometown**: Coastal town in Northern California

## Your Interests & Habits (Emergent Facts)
- You love exploring tidal pools (mentioned 3x, high confidence)
- You prefer morning fieldwork (stated 2x)
- Coffee helps you focus (recent preference)
```

**Why Both Systems?**
- **Backstory Facts**: Prevent hallucination of core biographical details
- **Bot Self-Facts**: Allow personality evolution and emergent consistency
- **Together**: Static identity + Dynamic personality = Authentic character

---

## Monitoring & Quality Control

### **Key Metrics**
1. **Response Consistency**: Same question → Same factual answer
2. **Fact Accuracy**: Bot responses match database facts
3. **Naturalness Score**: User feedback on response authenticity
4. **Prompt Token Usage**: Monitor for context window overflow

### **SQL Monitoring Queries**

```sql
-- Check which characters have backstory data
SELECT 
    c.name,
    COUNT(cb.id) as backstory_fact_count,
    STRING_AGG(DISTINCT cb.category, ', ') as categories
FROM characters c
LEFT JOIN character_background cb ON c.id = cb.character_id
GROUP BY c.name
ORDER BY backstory_fact_count DESC;

-- Find missing critical backstory categories
SELECT 
    c.name,
    CASE 
        WHEN SUM(CASE WHEN cb.category = 'workplace' THEN 1 ELSE 0 END) = 0 THEN 'Missing workplace'
        WHEN SUM(CASE WHEN cb.category = 'hometown' THEN 1 ELSE 0 END) = 0 THEN 'Missing hometown'
        WHEN SUM(CASE WHEN cb.category = 'education' THEN 1 ELSE 0 END) = 0 THEN 'Missing education'
    END as missing_category
FROM characters c
LEFT JOIN character_background cb ON c.id = cb.character_id
GROUP BY c.name
HAVING 
    SUM(CASE WHEN cb.category IN ('workplace', 'hometown', 'education') THEN 1 ELSE 0 END) < 3;
```

---

## Configuration & Feature Flags

### **Environment Variables**
```bash
# Enable backstory injection (default: true)
ENABLE_BACKSTORY_INJECTION=true

# Backstory storage strategy (character_background, identity_details, biographical_facts)
BACKSTORY_TABLE_STRATEGY=character_background

# Include backstory in system prompt (vs. post-routing)
BACKSTORY_PROMPT_INJECTION=true

# Maximum backstory facts in prompt (prevent context overflow)
MAX_BACKSTORY_FACTS=10
```

---

## Success Criteria

### **Must Have**
- ✅ 100% consistent responses to "Where do you work?" for same character
- ✅ All 10 characters have workplace, hometown, education facts in database
- ✅ System prompt includes backstory facts without exceeding token limits
- ✅ No regression in personality authenticity scores

### **Should Have**
- ✅ <200ms latency for backstory retrieval from PostgreSQL
- ✅ Backstory facts integrated with bot self-facts (no conflicts)
- ✅ Query routing correctly identifies biographical questions 90%+ accuracy

### **Nice to Have**
- ✅ Admin UI for editing character backstory facts
- ✅ Automatic backstory fact extraction from character JSON imports
- ✅ Temporal versioning (backstory changes over time)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Context window overflow** | System prompt exceeds LLM limits | Implement MAX_BACKSTORY_FACTS limit, prioritize by importance |
| **Rigid responses** | Bot sounds too mechanical | Use backstory as context, not templates - let LLM paraphrase naturally |
| **Data inconsistency** | Old characters lack backstory facts | Gradual migration, default to "I'd rather not discuss that" for missing facts |
| **Schema migration complexity** | Alembic conflicts | Use existing `character_background` table if possible |
| **Conflict with bot self-facts** | Emergent facts contradict designer facts | Designer facts = ground truth, bot self-facts = preferences/habits |

---

## Next Steps

1. **Schema Validation**: Identify current `character_background` table structure via Alembic migrations
2. **Data Population**: Create backstory facts for Jake (test character)
3. **Prototype**: Implement `CharacterBackstoryRetriever` and test SQL queries
4. **Integration**: Add backstory section to CDL system prompt builder
5. **Testing**: HTTP API validation → Discord testing → Production rollout

**Estimated Timeline**: 4 weeks from approval to production  
**Complexity**: Medium (uses existing infrastructure, minimal new code)  
**User Impact**: High (dramatically improves character consistency)

---

**Recommendation**: ✅ **PROCEED** with Phase 1 schema validation. Use existing `character_background` table if schema supports it, otherwise create new `character_biographical_facts` table via Alembic migration.
