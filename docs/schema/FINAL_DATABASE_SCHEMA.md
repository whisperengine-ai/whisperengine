# WhisperEngine Final Database Schema

**Document Version**: 3.0 (October 20, 2025)  
**Schema Architecture**: Hybrid migration system (Alembic + SQL files)  
**Database System**: PostgreSQL 16.4  
**Total Tables**: ~65 tables across two migration systems  

## 🚨 CRITICAL SCHEMA ARCHITECTURE

### **Hybrid Migration System**
WhisperEngine uses **TWO COORDINATED** migration systems:

#### **1. Alembic Migrations** - Core Production Schema (25 tables)
- **Purpose**: Systematic evolution of core CDL personality system
- **Tables**: `users`, `characters`, `personality_traits`, `character_values`, etc.
- **Location**: `alembic/versions/` (28 migration files, Oct 11-20, 2025)
- **Usage**: Production-critical schema with proper dependency management

#### **2. SQL Files** - Advanced Features (40+ tables)  
- **Purpose**: Advanced character intelligence and research features
- **Tables**: `character_insights`, `character_abilities`, `universal_users`, etc.
- **Location**: `sql/00_init.sql`, `sql/semantic_knowledge_graph_schema.sql`
- **Usage**: Optional advanced features, rapid development components

### **Deployment Order for Fresh Databases**
```bash
1. alembic upgrade head                           # Core CDL (25 tables)
2. psql -f sql/semantic_knowledge_graph_schema.sql # Enrichment (3 tables)  
3. psql -f sql/00_init.sql                       # Advanced features (40+ tables)
```

### **Table Naming Convention Changes**
- **DEPRECATED**: All `cdl_*` prefixed tables (legacy from v1.0.6)
- **CURRENT**: All `character_*` prefixed tables (active since October 2025)
- **Sources**: Tables exist in both Alembic migrations AND SQL files

### **Key Migration Events**
1. **Baseline Schema** (Oct 11, 2025): Initial v1.0.6 schema with `characters` and basic CDL tables
2. **CDL Table Cleanup** (Oct 13, 2025): Dropped legacy `cdl_*` tables and `_v2` versioned tables
3. **Character System Expansion** (Oct 12-20, 2025): Added 50+ `character_*` tables for complete personality system
4. **Enrichment Integration** (Oct 19, 2025): Added semantic knowledge graph tables

---

## 📊 COMPLETE SCHEMA OVERVIEW

### **ALEMBIC-MANAGED TABLES (25 core tables)**

#### **Core System Tables** (6 tables)
```
users                   - Universal identity system (Alembic)
characters             - AI character definitions (Alembic)
user_relationships     - User-character relationship tracking (Alembic)
user_facts            - Knowledge graph user facts (Alembic)
banned_users          - User moderation system (Alembic)
bot_deployments       - Bot deployment configuration (Alembic)
```

#### **Core CDL Personality Tables** (19 tables)
```
personality_traits           - Big Five personality model (Alembic) ⭐ CRITICAL
character_values            - Core values, beliefs, fears (Alembic) ⭐ CRITICAL
character_identity          - Basic identity information (Alembic)
character_attributes        - Personality attributes (Alembic)
character_communication     - Communication style (Alembic)
character_emotional_states  - Emotion modeling (Alembic)
character_learning_timeline - Learning progress tracking (Alembic)
character_interests        - Interests and hobbies (Alembic)
character_interest_topics  - Detailed interest breakdown (Alembic)
character_memories         - Character background memories (Alembic)
character_background       - Personal history (Alembic)
character_relationships    - Social connections (Alembic)
character_response_modes   - Response behavior patterns (Alembic)
character_conversation_modes - Conversation flow patterns (Alembic)
character_entity_categories - Entity classification (Alembic)
character_question_templates - Question frameworks (Alembic)
character_llm_config       - LLM configuration per character (Alembic)
character_discord_config   - Discord settings per character (Alembic)
conversation_summaries     - Conversation history summaries (Alembic)
```

### **SQL-MANAGED TABLES (40+ advanced tables)**

#### **Enrichment & Knowledge Graph** (3 tables)
```
fact_entities              - Semantic knowledge entities (SQL + Alembic docs)
user_fact_relationships    - Knowledge graph relationships (SQL + Alembic docs)
entity_relationships       - Entity-to-entity connections (SQL + Alembic docs)
```

#### **Advanced Character Intelligence** (15+ tables)
```
character_insights         - Advanced character learning (SQL only)
character_abilities        - Character capabilities (SQL only)
character_trait_relationships - Trait interconnections (SQL only)
character_optimizer_configs - Intelligence optimization (SQL only)
personality_evolution_timeline - Personality change tracking (SQL only)
character_metacognitive_traits - Self-awareness modeling (SQL only)
character_growth_objectives - Character development goals (SQL only)
character_platform_configs - Platform-specific settings (SQL only)
character_system_prompt_configs - System prompt configurations (SQL only)
character_workflow_configs - Workflow configurations (SQL only)
...and 5+ more specialized tables
```

#### **Extended Memory & Identity Systems** (10+ tables)
```
universal_users           - Universal identity system (SQL only)
user_profiles            - Extended user profiles (SQL only)
platform_identities     - Multi-platform user mapping (SQL only)
conversations            - Detailed conversation storage (SQL only)
conversation_entries     - Individual conversation messages (SQL only)
memory_entries          - Memory system entries (SQL only)
relationship_scores     - Relationship tracking (SQL only)
memory_manager_configs  - Memory system configuration (SQL only)
...and 2+ more memory tables
```

#### **Roleplay & Advanced Features** (15+ tables)
```
roleplay_transactions    - Roleplay interaction system (SQL only)
role_transactions       - Role-based interactions (SQL only)
personality_optimizer_results - Personality optimization results (SQL only)
character_voice_patterns - Voice and speech patterns (SQL only)
character_emoji_patterns - Emoji usage patterns (SQL only)
character_cultural_expressions - Cultural expression patterns (SQL only)
character_thematic_elements - Thematic storytelling elements (SQL only)
...and 8+ more roleplay/feature tables
```

---

## 📋 COMPLETE TABLE INVENTORY

### **1. CORE SYSTEM TABLES**

#### **users** - Universal Identity System
```sql
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    discord_user_id VARCHAR(50) UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Indexes: idx_users_discord, idx_users_username
```

#### **characters** - AI Character Definitions
```sql
CREATE TABLE characters (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    character_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Index: idx_characters_name
```

#### **user_relationships** - User-Character Relationship Tracking
```sql
CREATE TABLE user_relationships (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    affection FLOAT DEFAULT 0.0,
    trust FLOAT DEFAULT 0.0,
    attunement FLOAT DEFAULT 0.0,
    first_interaction TIMESTAMP DEFAULT now(),
    last_interaction TIMESTAMP DEFAULT now(),
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id, bot_name)
);
-- Index: idx_relationships_user_bot
```

#### **user_facts** - Knowledge Graph User Facts
```sql
CREATE TABLE user_facts (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    fact_type VARCHAR(100) NOT NULL,
    fact_value TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Indexes: idx_facts_user_bot, idx_facts_type
```

#### **banned_users** - User Moderation System
```sql
CREATE TABLE banned_users (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    reason TEXT,
    banned_at TIMESTAMP DEFAULT now(),
    banned_by VARCHAR(255),
    unbanned_at TIMESTAMP,
    unbanned_by VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id, bot_name)
);
```

#### **bot_deployments** - Bot Deployment Configuration
```sql
CREATE TABLE bot_deployments (
    id INTEGER NOT NULL PRIMARY KEY,
    bot_name VARCHAR(100) NOT NULL UNIQUE,
    character_id INTEGER REFERENCES characters(id),
    discord_token_encrypted TEXT NOT NULL,
    health_endpoint_port INTEGER,
    chat_endpoint_port INTEGER,
    status VARCHAR(50) DEFAULT 'inactive',
    last_health_check TIMESTAMP,
    deployment_config JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

### **2. CHARACTER DEFINITION LANGUAGE (CDL) TABLES**

#### **Character Identity & Core Attributes**

##### **character_identity** - Basic Identity Information
```sql
CREATE TABLE character_identity (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    full_name VARCHAR(500),
    nicknames TEXT,
    age INTEGER,
    occupation VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(character_id)
);
```

##### **character_attributes** - Personality Attributes (fears, dreams, quirks, values)
```sql
CREATE TABLE character_attributes (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    importance VARCHAR(100),
    display_order INTEGER,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(character_id, category, display_order)
);
-- Index: idx_attributes_char_cat
```

##### **character_communication** - Communication Style
```sql
CREATE TABLE character_communication (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    tone VARCHAR(500),
    humor_style VARCHAR(500),
    conversation_pacing VARCHAR(500),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(character_id)
);
```

#### **Character Psychology & Personality**

##### **personality_traits** - Big Five Personality Traits
```sql
CREATE TABLE personality_traits (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trait_name VARCHAR(50) NOT NULL,
    trait_value NUMERIC(3,2),
    intensity VARCHAR(20),
    description TEXT,
    UNIQUE(character_id, trait_name)
);
-- Index: idx_personality_traits_character
```

##### **communication_styles** - Communication Preferences
```sql
CREATE TABLE communication_styles (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    engagement_level NUMERIC(3,2),
    formality VARCHAR(100),
    emotional_expression NUMERIC(3,2),
    response_length VARCHAR(50),
    conversation_flow_guidance TEXT,
    ai_identity_handling TEXT
);
-- Index: idx_communication_styles_character
```

##### **character_values** - Core Values, Beliefs, Fears
```sql
CREATE TABLE character_values (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    value_key VARCHAR(100) NOT NULL,
    value_description TEXT NOT NULL,
    importance_level VARCHAR(20) DEFAULT 'medium',
    category VARCHAR(50),
    UNIQUE(character_id, value_key)
);
-- Index: idx_character_values_character
```

##### **character_emotional_states** - Emotional Modeling
```sql
CREATE TABLE character_emotional_states (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    emotion_name VARCHAR(100) NOT NULL,
    baseline_intensity NUMERIC(3,2) DEFAULT 0.5,
    triggers TEXT,
    expression_patterns TEXT,
    recovery_time_minutes INTEGER,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(character_id, emotion_name)
);
-- Index: idx_character_emotional_states_character
```

#### **Character Knowledge & Interests**

##### **character_interests** - Interests and Hobbies
```sql
CREATE TABLE character_interests (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    interest_name VARCHAR(200) NOT NULL,
    expertise_level VARCHAR(100),
    passion_intensity VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

##### **character_interest_topics** - Detailed Interest Topics
```sql
CREATE TABLE character_interest_topics (
    id INTEGER NOT NULL PRIMARY KEY,
    interest_id INTEGER NOT NULL REFERENCES character_interests(id) ON DELETE CASCADE,
    topic_name VARCHAR(200) NOT NULL,
    knowledge_depth VARCHAR(100),
    enthusiasm_level VARCHAR(100),
    specific_details TEXT,
    created_at TIMESTAMP DEFAULT now()
);
-- Index: idx_character_interest_topics_interest
```

##### **character_memories** - Character Background Memories
```sql
CREATE TABLE character_memories (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    memory_type VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    description TEXT NOT NULL,
    emotional_impact VARCHAR(100),
    time_period VARCHAR(200),
    importance VARCHAR(100),
    created_at TIMESTAMP DEFAULT now()
);
```

##### **character_background** - Personal History
```sql
CREATE TABLE character_background (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    childhood TEXT,
    education TEXT,
    career_path TEXT,
    major_life_events TEXT,
    formative_experiences TEXT,
    family_background TEXT,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(character_id)
);
```

#### **Character Interaction & Behavior Patterns**

##### **character_relationships** - Character Social Connections
```sql
CREATE TABLE character_relationships (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    entity_name VARCHAR(200) NOT NULL,
    relationship_description TEXT,
    emotional_connection VARCHAR(100),
    current_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT now()
);
```

##### **character_response_modes** - Response Behavior Patterns
```sql
CREATE TABLE character_response_modes (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    mode_name VARCHAR(100) NOT NULL,
    description TEXT,
    activation_triggers TEXT,
    response_characteristics TEXT,
    priority_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);
```

##### **character_conversation_modes** - Conversation Flow Patterns
```sql
CREATE TABLE character_conversation_modes (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    mode_name VARCHAR(100) NOT NULL,
    activation_condition TEXT,
    response_style TEXT,
    conversation_flow_guidance TEXT,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);
```

#### **Character Knowledge Systems**

##### **character_entity_categories** - Entity Classification
```sql
CREATE TABLE character_entity_categories (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    category_name VARCHAR(200) NOT NULL,
    description TEXT,
    classification_rules TEXT,
    processing_priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);
```

##### **character_question_templates** - Question Response Templates
```sql
CREATE TABLE character_question_templates (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    template_name VARCHAR(200) NOT NULL,
    question_pattern TEXT NOT NULL,
    response_framework TEXT,
    example_questions TEXT,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);
```

#### **Character Learning & Evolution**

##### **character_learning_timeline** - Learning Progress Tracking
```sql
CREATE TABLE character_learning_timeline (
    id INTEGER NOT NULL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    learning_event TEXT NOT NULL,
    event_timestamp TIMESTAMP DEFAULT now(),
    learning_source VARCHAR(100),
    knowledge_gained TEXT,
    confidence_change NUMERIC(3,2),
    memory_strength NUMERIC(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT now()
);
-- Index: idx_character_learning_timeline_character
```

##### **conversation_summaries** - Conversation History Summaries
```sql
CREATE TABLE conversation_summaries (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    conversation_date DATE NOT NULL,
    summary_text TEXT NOT NULL,
    key_topics TEXT,
    emotional_tone VARCHAR(100),
    interaction_quality NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Index: idx_conversation_summaries_user_bot_date
```

### **3. ENRICHMENT & KNOWLEDGE GRAPH TABLES**

#### **fact_entities** - Semantic Knowledge Entities
```sql
CREATE TABLE fact_entities (
    id INTEGER NOT NULL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    confidence FLOAT DEFAULT 1.0,
    first_mentioned TIMESTAMP DEFAULT now(),
    last_updated TIMESTAMP DEFAULT now(),
    mention_count INTEGER DEFAULT 1,
    search_vector TSVECTOR, -- Full-text search
    metadata JSONB,
    UNIQUE(entity_name, entity_type)
);
-- Indexes: idx_fact_entities_name_type, idx_fact_entities_search_vector (GIN)
```

#### **user_fact_relationships** - Knowledge Graph Relationships
```sql
CREATE TABLE user_fact_relationships (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    relationship_strength FLOAT DEFAULT 1.0,
    context TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Index: idx_user_fact_relationships_user_bot
```

#### **entity_relationships** - Entity-to-Entity Relationships
```sql
CREATE TABLE entity_relationships (
    id INTEGER NOT NULL PRIMARY KEY,
    source_entity_id INTEGER NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    target_entity_id INTEGER NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    strength FLOAT DEFAULT 1.0,
    context TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
-- Index: idx_entity_relationships_source_target
```

---

## 🔄 SCHEMA EVOLUTION TIMELINE

### **Phase 1: Baseline (October 11, 2025)**
- `20251011_baseline_v106.py` - Initial schema with core tables
- Established `users`, `characters`, `user_relationships`, `user_facts`
- Basic CDL tables: `character_identity`, `character_attributes`, `character_communication`

### **Phase 2: CDL Expansion (October 12, 2025)**
- `20251012_*` migrations - Added interest topics, entity categories, question templates
- Expanded character personality system with detailed classification

### **Phase 3: Schema Cleanup (October 13, 2025)**
- `20251013_*` migrations - Dropped legacy `cdl_*` tables and `_v2` versioned tables
- Normalized conversation flow guidance, removed deprecated JSON columns
- Cleaned up 73 orphaned rows and ~150KB storage

### **Phase 4: Advanced Features (October 14-15, 2025)**
- `20251014_*` - Added character configuration tables and bot deployments
- `20251015_*` - Enhanced Discord integration, missing configuration fields

### **Phase 5: Psychology & Learning (October 17-19, 2025)**
- `20251017_*` - Added emotional states and learning persistence systems
- `20251019_*` - Integrated enrichment schema, personality traits backfill

### **Phase 6: Final Integration (October 20, 2025)**
- `20251020_*` - Added personality traits, communication styles, character values
- Completed CDL system integration with 50+ character tables

---

## 🛠️ USAGE PATTERNS

### **Character Data Loading**
```python
# CORRECT: Dynamic loading from database
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_name=get_normalized_bot_name_from_env(),  # Dynamic
    user_id=user_id,
    message_content=message
)
```

### **Database Connection Patterns**
```python
# Environment-based configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5433"  # External Docker port
DATABASE_NAME = "whisperengine"
```

### **Table Relationship Patterns**
- **Parent-Child**: `characters` → All `character_*` tables (CASCADE DELETE)
- **User Tracking**: `user_id` VARCHAR(255) across all user-related tables
- **Bot Isolation**: `bot_name` VARCHAR(100) for multi-character separation

---

## ⚠️ CRITICAL CONSTRAINTS

### **Schema Stability Requirements**
1. **NO BREAKING CHANGES** - Production users depend on current schema
2. **ADDITIVE ONLY** - New tables/columns allowed, never remove/rename existing
3. **Alembic-First** - All schema changes via migrations, never manual SQL
4. **Character-Agnostic** - No hardcoded character names in schema or code

### **Deprecated References**
- ❌ `sql/init_schema.sql` - Legacy baseline only, DO NOT USE for current schema
- ❌ All `cdl_*` table references - Migrated to `character_*` tables
- ❌ JSON character files - Database is single source of truth

### **Required Tools**
- **Migration System**: Alembic (`alembic/versions/`)
- **Character Loading**: CDL AI Integration (`src/prompts/cdl_ai_integration.py`)
- **Environment Config**: Dynamic bot name via `DISCORD_BOT_NAME`

---

**Document Maintained**: October 20, 2025  
**Next Review**: When adding new character system features  
**Schema Source**: Alembic migrations in `alembic/versions/`  
**Live Database**: PostgreSQL 16.4 on Docker port 5433  
