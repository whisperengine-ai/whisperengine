# Database Schema Quick Reference

**Last Updated**: October 20, 2025  
**Purpose**: Developer quick reference for WhisperEngine database schema  

## 🚨 CRITICAL FACTS

### **NO MORE CONFUSION - FINAL SCHEMA STATE**
- ✅ **Current Tables**: All `character_*` prefixed (50+ tables)
- ❌ **Deprecated**: All `cdl_*` tables were migrated/dropped in October 2025
- ❌ **Legacy Reference**: `sql/init_schema.sql` is OUTDATED - use Alembic migrations only
- ✅ **Source of Truth**: `alembic/versions/` directory contains all schema changes

---

## 📋 TABLE CATEGORIES (25+ Core Tables)

### **Core System (6 tables)**
```
users                   - Universal identity system
characters             - AI character definitions
user_relationships     - User-character relationship tracking
user_facts            - Knowledge graph user facts  
banned_users          - User moderation system
bot_deployments       - Bot deployment configuration
```

### **Character Identity (5 tables)**
```
character_identity          - Basic identity (name, age, occupation)
character_attributes       - Personality attributes (fears, dreams, quirks)
character_communication    - Communication style (tone, humor, pacing)
character_background      - Personal history and formative experiences
character_memories        - Character background memories
```

### **Character Psychology (4 tables)**
```
personality_traits        - Big Five personality model (CRITICAL for CDL AI)
communication_styles     - Communication preferences and patterns
character_values         - Core values, beliefs, fears
character_emotional_states - Emotion modeling and triggers
```

### **Character Knowledge (4 tables)**
```
character_interests          - Interests and hobbies
character_interest_topics   - Detailed interest breakdown
character_entity_categories - Entity classification rules
character_question_templates - Question response frameworks
```

### **Character Behavior (4 tables)**
```
character_relationships      - Social connections and relationships
character_response_modes    - Response behavior patterns
character_conversation_modes - Conversation flow patterns
character_learning_timeline - Learning progress tracking
```

### **Character Configuration (2 tables)**
```
character_llm_config      - Per-character LLM settings (models, API keys)
character_discord_config  - Per-character Discord configuration
```

### **Enrichment System (3 tables)**
```
fact_entities            - Semantic knowledge entities (full-text search)
user_fact_relationships  - Knowledge graph relationships
entity_relationships     - Entity-to-entity connections
```

### **Conversation System (1 table)**
```
conversation_summaries   - Daily conversation history summaries
```

---

## 🔧 DEVELOPER USAGE PATTERNS

### **Character Data Loading (CORRECT)**
```python
# ✅ ALWAYS: Dynamic character loading from database
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()

# Character identified by environment variable
character_name = get_normalized_bot_name_from_env()  # From DISCORD_BOT_NAME
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_name=character_name,
    user_id=user_id,
    message_content=message
)
```

### **Database Connection**
```python
# Environment configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5433"  # Docker external port
DATABASE_NAME = "whisperengine" 
USERNAME = "whisperengine"
PASSWORD = "whisperengine_password"
```

### **Critical Tables Queried by CDL System**
The `src/prompts/cdl_ai_integration.py` actively queries these tables:
1. **`personality_traits`** - Big Five personality model
2. **`communication_styles`** - Communication preferences  
3. **`character_values`** - Core values and beliefs
4. **`character_identity`** - Basic character information
5. **`character_attributes`** - Personality attributes

---

## 🚨 SCHEMA CONSTRAINTS & RULES

### **Foreign Key Patterns**
- **`character_id`**: All `character_*` tables reference `characters(id)` with CASCADE DELETE
- **`user_id`**: VARCHAR(255) across all user-related tables
- **`bot_name`**: VARCHAR(100) for multi-character isolation

### **Index Patterns**
- All `character_*` tables have `character_id` indexes for fast lookups
- User tables have composite indexes: `(user_id, bot_name)`
- Full-text search: GIN index on `fact_entities.search_vector`

### **Data Types & Conventions**
- **IDs**: INTEGER with SERIAL primary keys
- **User IDs**: VARCHAR(255) (accommodates Discord snowflakes)
- **Bot Names**: VARCHAR(100) (standardized character identifiers)
- **Timestamps**: TIMESTAMP with DEFAULT now()
- **Personality Values**: NUMERIC(3,2) for 0.00-1.00 ranges
- **Metadata**: JSONB for flexible structured data

---

## ⚠️ CRITICAL ANTI-PATTERNS

### **❌ DON'T DO THIS**
```python
# ❌ NEVER: Hardcode character names
if character_name == "elena":
    # Character-specific logic

# ❌ NEVER: Reference cdl_* tables  
SELECT * FROM cdl_characters;  -- Table doesn't exist!

# ❌ NEVER: Use sql/init_schema.sql for current schema
# This file is legacy baseline only

# ❌ NEVER: Manual schema changes
ALTER TABLE characters ADD COLUMN new_field TEXT;  -- Use Alembic!
```

### **✅ DO THIS INSTEAD**
```python
# ✅ CORRECT: Dynamic character loading
character_data = await load_character_from_database(character_name)

# ✅ CORRECT: Use character_* tables
SELECT * FROM character_identity WHERE character_id = %s;

# ✅ CORRECT: Use Alembic migrations
alembic revision -m "add new character field"

# ✅ CORRECT: Environment-based bot identification  
bot_name = os.getenv('DISCORD_BOT_NAME')
```

---

## 🛠️ SCHEMA TOOLS & COMMANDS

### **Alembic Migration Commands**
```bash
# Check current schema version
alembic current

# View migration history  
alembic history --verbose

# Create new migration
alembic revision -m "description of changes"

# Apply migrations
alembic upgrade head

# Downgrade (careful in production!)
alembic downgrade -1
```

### **Database Connection (via multi-bot.sh)**
```bash
# Connect to PostgreSQL (if infrastructure running)
./multi-bot.sh db

# Inside psql:
\dt character_*     # List all character tables
\d+ characters      # Describe characters table structure
\di                 # List indexes
```

### **Schema Validation Commands**
```bash
# Validate current environment
source .venv/bin/activate
python scripts/verify_environment.py

# Check migration status
alembic current
alembic history | head -10
```

---

## 📚 SCHEMA DOCUMENTATION

### **Complete References**
- **Final Schema**: `/docs/schema/FINAL_DATABASE_SCHEMA.md` (comprehensive)
- **Evolution Timeline**: `/docs/schema/SCHEMA_EVOLUTION_TIMELINE.md` (chronological)
- **Quick Reference**: `/docs/schema/DATABASE_SCHEMA_QUICK_REFERENCE.md` (this file)

### **Migration Files**
- **All Migrations**: `/alembic/versions/` (28+ files, Oct 11-20, 2025)
- **Baseline**: `20251011_baseline_v106.py` (initial v1.0.6 schema)
- **Latest**: `20251020_1356_*_add_unban_audit_columns_to_banned_users.py`

### **Schema Files and Usage**
- ✅ **Alembic migrations**: `/alembic/versions/` - Core CDL system (25 tables)
- ✅ **SQL advanced features**: `/sql/00_init.sql` - Advanced features (40+ tables)  
- ✅ **SQL enrichment**: `/sql/semantic_knowledge_graph_schema.sql` - Knowledge graph (3 tables)
- ✅ **Complete guide**: `/docs/schema/UNIFIED_MIGRATION_GUIDE.md` - Deployment instructions
- ❌ **DEPRECATED**: `sql/init_schema.sql` - Legacy file, do not use
- ❌ **DEPRECATED**: Any `cdl_*` table references in old code
- ❌ **DEPRECATED**: JSON character files in `characters/` - database is source of truth

---

## 🎯 CHARACTER SYSTEM INTEGRATION

### **CDL System Components**
1. **Database Storage**: 50+ `character_*` tables with personality data
2. **Loading System**: `CDLAIPromptIntegration` class loads character data dynamically
3. **Environment Config**: `DISCORD_BOT_NAME` environment variable identifies character
4. **Prompt Generation**: Character data integrated into LLM system prompts

### **Character Bot Isolation**
- **Memory**: Separate Qdrant collections per character (`whisperengine_memory_{bot_name}`)
- **Database**: Isolated by `character_id` foreign keys and `bot_name` fields
- **Configuration**: Per-character LLM and Discord settings in database
- **Deployment**: Independent Docker containers per character

---

**Remember**: WhisperEngine is a production multi-character AI platform. Always preserve character personality authenticity and use the database-driven CDL system for all character operations.