# Fact Extraction and Prompt Integration Architecture

**Document Version**: 1.0  
**Last Updated**: October 11, 2025  
**Status**: Current Production Implementation

## Overview

WhisperEngine implements an intelligent fact extraction and preference learning system that captures user information from conversations and integrates it into character prompts for personalized, context-aware responses. This document describes the complete data flow from extraction through prompt integration.

---

## 🎯 System Architecture

### High-Level Flow
```
User Message → LLM Fact Extraction → PostgreSQL Storage → 
Knowledge Router Retrieval → CDL Prompt Integration → 
Character Response with Personalized Context
```

### Key Components
1. **LLM Fact Extractor** (`src/knowledge/llm_fact_extractor.py`)
2. **PostgreSQL Database** (fact_entities + user_fact_relationships tables)
3. **Semantic Knowledge Router** (`src/knowledge/semantic_router.py`)
4. **CDL AI Integration** (`src/prompts/cdl_ai_integration.py`)
5. **Message Processor** (`src/core/message_processor.py`)

---

## 📊 Phase 1: Fact Extraction from Conversations

### Entry Point: Message Processing
**Location**: `src/core/message_processor.py` → `process_message()` method

When a user sends a message, the system analyzes it for extractable facts before generating the bot response.

### LLM-Based Extraction
**Component**: `LLMFactExtractor` class

**Temperature Configuration**:
```python
# Fact extraction uses LOWER temperature for consistency
FACT_EXTRACTION_TEMPERATURE = 0.2  # More deterministic
CHAT_TEMPERATURE = 0.6             # More creative for responses
```

**Extraction Process**:
1. **Message Analysis**: User message analyzed by LLM with specialized prompt
2. **Entity Detection**: LLM identifies entities (foods, hobbies, locations, people, etc.)
3. **Relationship Classification**: Determines relationship type (likes, enjoys, works_at, favorite, etc.)
4. **Confidence Scoring**: Assigns confidence level (0.0-1.0) based on message certainty

### Example Extraction
```
User: "My favorite food is sushi"

LLM Extracts:
- entity_name: "sushi"
- entity_type: "food"
- relationship_type: "favorite"
- confidence: 0.9
- emotional_context: "joy"
```

### Anti-Patterns (Not Extracted)
- ❌ Questions: "Do you like pizza?" → Not stored as user fact
- ❌ Hypotheticals: "I would like to visit Japan someday" → Too uncertain
- ❌ Negations: "I don't like broccoli" → Filtered out (focus on positive facts)

---

## 🗄️ Phase 2: PostgreSQL Storage

### Database Schema

#### `fact_entities` Table
Stores unique entities extracted from conversations:
```sql
CREATE TABLE fact_entities (
    id UUID PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),      -- food, hobby, location, person, etc.
    category VARCHAR(100),          -- broader categorization
    attributes JSONB,               -- additional metadata
    search_vector tsvector,         -- full-text search
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `user_fact_relationships` Table
Links users to entities with relationship context:
```sql
CREATE TABLE user_fact_relationships (
    user_id VARCHAR(255) NOT NULL,
    entity_id UUID REFERENCES fact_entities(id),
    relationship_type VARCHAR(100),  -- likes, enjoys, favorite, works_at, etc.
    confidence DECIMAL(3,2),         -- 0.00 to 1.00
    emotional_context VARCHAR(50),   -- joy, neutral, excitement, etc.
    last_mentioned TIMESTAMP,
    mention_count INTEGER,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, entity_id, relationship_type)
);
```

### Storage Pattern
**Normalized Design** - Prevents duplicate entity storage:
1. Check if entity exists in `fact_entities` (by name + type)
2. If exists: Get entity_id, update last_mentioned
3. If new: Insert into `fact_entities`, get new entity_id
4. Insert/update relationship in `user_fact_relationships`

### Example Storage
```
User: "My favorite food is sushi"

fact_entities:
  id: acc98a3b-159c-4158-81b0-7f6d2eacbb7b
  entity_name: "sushi"
  entity_type: "food"
  category: "cuisine"

user_fact_relationships:
  user_id: "final_test_user"
  entity_id: acc98a3b-159c-4158-81b0-7f6d2eacbb7b
  relationship_type: "favorite"
  confidence: 0.9
  emotional_context: "joy"
```

---

## 🔍 Phase 3: Knowledge Retrieval

### Entry Point: Prompt Building
**Location**: `src/prompts/cdl_ai_integration.py` → `create_character_aware_prompt()`

When building a prompt for character response, the system queries PostgreSQL for relevant user facts.

### Semantic Knowledge Router
**Component**: `SemanticKnowledgeRouter.get_character_aware_facts()`  
**Location**: `src/knowledge/semantic_router.py`

**Query Strategy**:
```sql
SELECT 
    fe.entity_name,
    fe.entity_type,      -- CRITICAL: Added in October 11 bug fix
    fe.category,
    ufr.relationship_type,
    ufr.confidence,
    ufr.emotional_context,
    ufr.last_mentioned
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = ?
ORDER BY ufr.confidence DESC, ufr.last_mentioned DESC
LIMIT 20
```

**Returned Data Structure**:
```python
[
    {
        "entity_name": "sushi",
        "entity_type": "food",          # Essential for context
        "category": "cuisine",
        "relationship_type": "favorite",
        "confidence": 0.9,
        "emotional_context": "joy"
    },
    # ... more facts
]
```

---

## 🎨 Phase 4: Prompt Integration

### CDL AI Integration
**Component**: `CDLAIPromptIntegration` class  
**Location**: `src/prompts/cdl_ai_integration.py`

### Step 1: Fact Retrieval
Method: `_get_user_facts_context()`

```python
# Retrieve facts from PostgreSQL
facts = await self.knowledge_router.get_character_aware_facts(
    user_id=user_id,
    character_name=character_name,
    limit=20
)
```

### Step 2: Confidence-Aware Formatting
Method: `build_confidence_aware_context()`

**Confidence-Based Language**:
- **High Confidence (0.9+)**: Definitive statements
  - "The user's favorite food is sushi"
- **Medium Confidence (0.6-0.8)**: Tentative language
  - "The user mentioned liking sushi"
- **Low Confidence (<0.6)**: Uncertain phrasing
  - "The user may like sushi"

**Entity Type Context** (Added October 11, 2025):
```python
entity_type = fact.get('entity_type', '')
entity_display = f"{entity} ({entity_type})" if entity_type else entity
```

**Special Relationship Handling**:
```python
if relationship_type == "favorite":
    if confidence >= 0.9:
        context = f"The user's favorite {entity_type} is {entity}"
    elif confidence >= 0.6:
        context = f"The user mentioned {entity} as a favorite {entity_type}"
```

### Step 3: System Prompt Integration

**Format in Main System Prompt**:
```
👤 USER CONTEXT:
📋 Known Facts: The user's favorite food is sushi

🎬 CONVERSATION FLOW & CONTEXT:
...
📊 KNOWN FACTS ABOUT User:

General:
  The user's favorite food is sushi

Interpret these facts through Elena Rodriguez's personality and communication style.
```

**Separate System Message** (Structured Format):
```json
{
  "role": "system",
  "content": "RELEVANT MEMORIES: USER FACTS: [sushi (favorite, food)]"
}
```

### Dual Format Rationale
1. **Human-Readable** (Main prompt): Natural language for LLM comprehension
2. **Structured** (Separate message): Machine-readable for quick reference

Both formats ensure LLM has complete context in multiple representations.

---

## 🔄 Complete Data Flow Example

### Scenario: User shares food preference

#### Step 1: User Message
```
User: "My favorite food is sushi"
```

#### Step 2: LLM Extraction
```python
# LLMFactExtractor.extract_facts_from_text()
extracted_facts = [
    {
        "entity_name": "sushi",
        "entity_type": "food",
        "relationship_type": "favorite",
        "confidence": 0.9
    }
]
```

#### Step 3: PostgreSQL Storage
```sql
-- Insert entity
INSERT INTO fact_entities (id, entity_name, entity_type, category)
VALUES ('acc98a3b...', 'sushi', 'food', 'cuisine');

-- Insert relationship
INSERT INTO user_fact_relationships 
(user_id, entity_id, relationship_type, confidence, emotional_context)
VALUES ('final_test_user', 'acc98a3b...', 'favorite', 0.9, 'joy');
```

#### Step 4: Future Retrieval
```
User: "What do you know about my favorite foods?"
```

#### Step 5: Knowledge Router Query
```python
facts = await knowledge_router.get_character_aware_facts(
    user_id="final_test_user",
    character_name="elena"
)
# Returns: [{"entity_name": "sushi", "entity_type": "food", ...}]
```

#### Step 6: Prompt Building
```python
context = build_confidence_aware_context(facts)
# Result: "The user's favorite food is sushi"
```

#### Step 7: Final Prompt
```
You are Elena Rodriguez, a Marine Biologist...

📋 Known Facts: The user's favorite food is sushi

[Rest of prompt with conversation context...]
```

#### Step 8: Character Response
```
Elena: "Oh yes! I remember you love sushi. There's something beautiful 
about how ocean-fresh fish becomes art on a plate. Do you have a 
favorite type? I'm partial to uni myself - sea urchin has this 
incredible oceanic flavor..."
```

---

## 🐛 Bug Fix: Entity Type Display (October 11, 2025)

### Problem Discovered
User facts were displaying without entity_type context:
```
❌ BAD: "The user favorite sushi"
✅ GOOD: "The user's favorite food is sushi"
```

### Root Cause
Two-part bug in the pipeline:

#### Bug 1: Missing Database Column
**Location**: `src/knowledge/semantic_router.py` line 345

**Before (Broken)**:
```python
SELECT 
    fe.entity_name,
    fe.category,        # Missing entity_type!
    ufr.confidence,
    ...
```

**After (Fixed)**:
```python
SELECT 
    fe.entity_name,
    fe.entity_type,     # ✅ Added
    fe.category,
    ufr.confidence,
    ...
```

#### Bug 2: Missing Formatting Logic
**Location**: `src/prompts/cdl_ai_integration.py` lines 99-120

**Before (Broken)**:
```python
def build_confidence_aware_context(facts):
    entity = fact.get('entity_name')
    # No entity_type handling!
```

**After (Fixed)**:
```python
def build_confidence_aware_context(facts):
    entity = fact.get('entity_name')
    entity_type = fact.get('entity_type', '')  # ✅ Extract type
    
    # Create display with type context
    entity_display = f"{entity} ({entity_type})" if entity_type else entity
    
    # Use in formatting
    if relationship_type == "favorite":
        context = f"The user's favorite {entity_type} is {entity}"
```

### Validation
```bash
# Test with Elena bot
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "What do you know about me?"}'

# Check logs
docker logs elena-bot 2>&1 | grep "Known Facts"
# Result: "📋 Known Facts: The user's favorite food is sushi" ✅
```

---

## 🎯 Design Decisions

### Why LLM-Based Extraction?
**Alternative Considered**: Regex/keyword matching

**LLM Advantages**:
- Understands natural language nuance
- Handles varied phrasing ("I love pizza" vs "Pizza is my favorite")
- Extracts entity types automatically
- Provides confidence scoring
- Adapts to conversational context

**Trade-offs**:
- Higher latency (~200-500ms per extraction)
- Requires LLM API call for every user message
- More expensive than regex patterns

**Mitigation**:
- Low temperature (0.2) for consistency
- Cached entity lookups in PostgreSQL
- Only extract from user messages (not bot responses)

### Why PostgreSQL Over Vector Storage?
**Alternative Considered**: Store facts in Qdrant vector memory

**PostgreSQL Advantages**:
- Structured queries by relationship_type
- Efficient JOIN operations
- Confidence-based filtering
- Transaction safety for updates
- Standard SQL indexing

**Vector Storage Role**:
- Used for conversation memory and semantic search
- Facts are ALSO stored in vector memory for conversational context
- PostgreSQL provides structured fact querying
- Qdrant provides semantic conversation retrieval

### Why Dual Prompt Format?
**Alternative Considered**: Single format (either natural language OR structured)

**Dual Format Advantages**:
- Natural language: LLM comprehension and generation
- Structured format: Machine parsing and debugging
- Redundancy: Ensures facts visible in multiple ways
- Low cost: Structured format adds ~20 tokens per fact

---

## 📈 Performance Characteristics

### Extraction Performance
- **LLM Call**: 200-500ms per message (with fact extraction)
- **Temperature**: 0.2 (consistency-focused)
- **Token Usage**: ~100-200 tokens per extraction
- **Batch Processing**: Not currently implemented (sequential per message)

### Storage Performance
- **PostgreSQL Insert**: <10ms per fact
- **Entity Lookup**: <5ms (indexed by entity_name + entity_type)
- **Relationship Update**: <5ms (composite primary key)

### Retrieval Performance
- **Fact Query**: 10-20ms for 20 facts (JOIN + ORDER BY)
- **Prompt Integration**: <5ms (string formatting)
- **Total Overhead**: ~30ms added to prompt building

---

## 🚀 Future Enhancements

### Phase 2A: Direct Character Questions (Planned)
**Goal**: CharacterGraphManager for intelligent CDL-based responses

**Example**:
```
User: "Tell me about your research on coral reefs"
→ Direct query to Elena's CDL character data
→ Response based on professional_background and past_experiences
```

### Phase 2B: Proactive Context Injection (Planned)
**Goal**: Natural character background integration

**Example**:
```
User: "What's your opinion on ocean conservation?"
→ CDL system injects Elena's values and motivations
→ Response reflects deep personal commitment from character backstory
```

### Confidence Evolution (Future)
**Goal**: Update confidence scores based on repeated mentions

**Example**:
```
User mentions "sushi" 5 times over 2 weeks
→ Confidence increases from 0.7 to 0.95
→ System becomes more certain about user preference
```

### Fact Deprecation (Future)
**Goal**: Handle changing preferences over time

**Example**:
```
User: "I used to love sushi, but I'm vegetarian now"
→ Lower confidence on "sushi" fact
→ Add new fact: relationship_type="was_favorite" (past tense)
→ Add vegetarian dietary preference
```

---

## 🔧 Implementation Details

### Key Files
1. **`src/knowledge/llm_fact_extractor.py`** - LLM-based extraction engine
2. **`src/knowledge/semantic_router.py`** - PostgreSQL fact retrieval
3. **`src/prompts/cdl_ai_integration.py`** - Prompt building and formatting
4. **`src/core/message_processor.py`** - Main message processing pipeline
5. **`alembic/versions/001_create_knowledge_graph_tables.py`** - Database schema

### Environment Variables
```bash
# Fact extraction configuration
FACT_EXTRACTION_TEMPERATURE=0.2
CHAT_TEMPERATURE=0.6

# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=whisperengine
```

### Testing
**Direct Python Validation**:
```bash
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_llm_fact_extraction_direct_validation.py
```

**HTTP API Testing**:
```bash
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "My favorite food is sushi",
    "context": {"channel_type": "dm", "platform": "api"}
  }'
```

**Database Verification**:
```bash
docker exec postgres-whisperengine psql -U whisperengine -d whisperengine -c "
SELECT ufr.user_id, fe.entity_name, fe.entity_type, 
       ufr.relationship_type, ufr.confidence 
FROM user_fact_relationships ufr 
JOIN fact_entities fe ON ufr.entity_id = fe.id 
WHERE ufr.user_id = 'test_user';
"
```

---

## 📝 Related Documentation

- **`docs/database/CDL_OPTIMAL_RDBMS_SCHEMA.md`** - Complete database schema
- **`docs/cdl-system/FACT_EXTRACTION_TEMPERATURE_CONFIGURATION.md`** - Temperature tuning
- **`docs/architecture/ENTITY_RELATIONSHIP_DATA_FLOW_DIAGRAM.md`** - Visual data flow
- **`docs/database/REGEX_VS_LLM_EXTRACTION_ANALYSIS.md`** - Extraction method comparison
- **`docs/roadmaps/CDL_INTEGRATION_COMPLETE_ROADMAP.md`** - Future roadmap

---

## 🎓 Key Takeaways

1. **LLM-Based Extraction**: Provides natural language understanding for fact extraction
2. **PostgreSQL Storage**: Normalized schema prevents duplicate entities
3. **Confidence Scoring**: Allows graduated certainty in fact presentation
4. **Dual Format**: Both natural language and structured formats ensure robust integration
5. **Entity Type Context**: Critical for natural, semantically-aware character responses
6. **Low Temperature**: Ensures consistency in fact extraction (0.2 vs 0.6 for chat)
7. **Bug-Resistant Design**: Comprehensive testing prevents silent failures

---

**Last Updated**: October 11, 2025  
**Architecture Version**: 1.0  
**WhisperEngine Version**: Alpha Development (Multi-Bot + Fact Extraction)
