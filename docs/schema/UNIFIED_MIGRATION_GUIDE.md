# WhisperEngine Unified Migration Guide

**Document Version**: 1.0 (October 20, 2025)  
**Purpose**: Definitive guide for WhisperEngine's hybrid migration architecture  
**Audience**: Developers, DevOps, Database administrators  

## 🏗️ HYBRID ARCHITECTURE OVERVIEW

WhisperEngine uses **TWO COORDINATED** migration systems that work together:

### **System 1: Alembic Migrations** - Core Production Schema
- **Purpose**: Systematic, versioned evolution of core CDL personality system
- **Tables**: 25 production-critical tables
- **Management**: Proper dependency management, rollback support, version control
- **Usage**: All core character personality features

### **System 2: SQL Files** - Advanced Features  
- **Purpose**: Rapid deployment of advanced character intelligence features
- **Tables**: 40+ research and experimental tables
- **Management**: Direct SQL execution, faster iteration cycles
- **Usage**: Advanced character intelligence, memory systems, roleplay features

---

## 🚀 FRESH DATABASE DEPLOYMENT

### **Complete Setup Process**
```bash
# Step 1: Core CDL system (REQUIRED)
cd /path/to/whisperengine
source .venv/bin/activate
alembic upgrade head
# ✅ Creates: 25 core tables (users, characters, personality_traits, etc.)

# Step 2: Enrichment system (RECOMMENDED for full features)  
export PGPASSWORD=whisperengine_password
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/semantic_knowledge_graph_schema.sql
# ✅ Creates: 3 knowledge graph tables (fact_entities, etc.)

# Step 3: Advanced features (OPTIONAL for research/advanced features)
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/00_init.sql  
# ✅ Creates: 40+ advanced tables (character_insights, etc.)
```

### **Minimal Deployment (Core Features Only)**
```bash
# For basic WhisperEngine functionality
alembic upgrade head
# ✅ 25 core tables - sufficient for basic character personality system
```

### **Production Deployment (Recommended)**
```bash  
# For full production features including enrichment
alembic upgrade head
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/semantic_knowledge_graph_schema.sql
# ✅ 28 tables - core + enrichment system
```

### **Research/Development Deployment (Everything)**
```bash
# For all features including experimental systems
alembic upgrade head
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/semantic_knowledge_graph_schema.sql
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/00_init.sql
# ✅ 65+ tables - complete system with all features
```

---

## 🔄 SCHEMA CHANGE WORKFLOWS

### **Core CDL Changes (Alembic)**
Use Alembic for changes to core personality, identity, and user management:

```bash
# Create new migration  
alembic revision -m "add new personality trait field"

# Edit the generated migration file
# alembic/versions/YYYYMMDD_HHMMSS_add_new_personality_trait_field.py

def upgrade() -> None:
    op.add_column('personality_traits', 
                  sa.Column('new_field', sa.String(100), nullable=True))

def downgrade() -> None:
    op.drop_column('personality_traits', 'new_field')

# Apply migration
alembic upgrade head

# Verify migration
alembic current
alembic history
```

**Use Alembic for**:
- `personality_traits`, `character_values`, `character_identity` changes
- `users`, `characters`, `user_relationships` modifications  
- Core CDL system tables (`character_attributes`, `character_communication`)
- Production-critical schema changes requiring rollback capability

### **Advanced Features Changes (SQL Files)**
Use direct SQL for advanced features and research components:

```bash
# Option 1: Update existing sql/00_init.sql
# Edit the file directly for table modifications

# Option 2: Create new feature-specific SQL file
# sql/new_character_intelligence_feature.sql
CREATE TABLE character_advanced_insights (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    insight_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

# Apply the changes
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/new_character_intelligence_feature.sql

# Optional: Document in Alembic (for version control)
alembic revision -m "document character intelligence tables"
# Create documentation-only migration (no actual schema changes)
```

**Use SQL Files for**:
- `character_insights`, `character_abilities` modifications
- `universal_users`, `memory_entries` system changes
- Research features and experimental tables
- Rapid prototyping without migration overhead

---

## 📋 TABLE OWNERSHIP GUIDE

### **Alembic-Owned Tables (25 tables)**
**Always use Alembic migrations for these tables:**

#### **Core System**
- `users`, `characters`, `user_relationships`, `user_facts` 
- `banned_users`, `bot_deployments`

#### **CDL Personality System**  
- `personality_traits` ⭐ (Big Five model - CRITICAL)
- `character_values` ⭐ (Core values/beliefs - CRITICAL)
- `character_identity`, `character_attributes`
- `character_communication`, `character_emotional_states`
- `character_learning_timeline`, `character_interests`
- `character_interest_topics`, `character_memories`
- `character_background`, `character_relationships`
- `character_response_modes`, `character_conversation_modes`
- `character_entity_categories`, `character_question_templates`
- `character_llm_config`, `character_discord_config`
- `conversation_summaries`

### **SQL-Owned Tables (40+ tables)**
**Use SQL files for these tables:**

#### **Advanced Character Intelligence**
- `character_insights`, `character_abilities`
- `character_trait_relationships`, `character_optimizer_configs`
- `personality_evolution_timeline`, `character_metacognitive_traits`

#### **Extended Memory & Identity**
- `universal_users`, `user_profiles`, `platform_identities`
- `conversations`, `conversation_entries`, `memory_entries`
- `relationship_scores`, `memory_manager_configs`

#### **Enrichment System**
- `fact_entities`, `user_fact_relationships`, `entity_relationships`

#### **Roleplay & Advanced Features**  
- `roleplay_transactions`, `role_transactions`
- `character_voice_patterns`, `character_emoji_patterns`
- All other specialized character feature tables

---

## 🔍 VERIFICATION COMMANDS

### **Check Schema Status**
```bash
# Verify Alembic migration status
alembic current
alembic history

# Check database table count
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c \
  "SELECT schemaname, COUNT(*) as table_count FROM pg_tables WHERE schemaname='public' GROUP BY schemaname;"

# List all character tables
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c \
  "\dt character_*"

# Verify critical CDL tables exist  
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c \
  "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='personality_traits') as personality_exists,
          EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='character_values') as values_exists,
          EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='fact_entities') as enrichment_exists;"
```

### **Application Integration Check**
```bash
# Test CDL system integration (core personality loading)
cd /path/to/whisperengine
source .venv/bin/activate
export DISCORD_BOT_NAME=elena
python -c "
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
import asyncio
async def test():
    cdl = CDLAIPromptIntegration()
    # This will fail if core CDL tables are missing
    prompt = await cdl.create_character_aware_prompt('elena', 'test_user', 'hello')
    print('✅ CDL integration working')
asyncio.run(test())
"
```

---

## ⚠️ MIGRATION BEST PRACTICES

### **Development Workflow**
1. **Plan your change**: Determine if it's core CDL (Alembic) or advanced feature (SQL)
2. **Use appropriate system**: Don't mix Alembic and SQL for the same table
3. **Test locally**: Always test migrations on development database first
4. **Document decisions**: Update this guide when adding new table categories

### **Production Deployment**  
1. **Backup first**: Always backup production database before schema changes
2. **Staged deployment**: Apply changes to staging environment first
3. **Monitoring**: Monitor application logs during and after deployment
4. **Rollback plan**: Have rollback strategy for both Alembic and SQL changes

### **Team Coordination**
1. **Communication**: Notify team of schema changes affecting shared tables
2. **Documentation**: Update schema docs when adding new features
3. **Code review**: Review both Alembic migrations and SQL files
4. **Testing**: Ensure application code works with new schema changes

---

## 🛠️ TROUBLESHOOTING

### **Common Issues**

#### **"Table already exists" during Alembic migration**
```bash
# Some tables may exist from SQL files
# Create documentation-only migration:
alembic revision -m "document existing tables"
# Edit migration to check table existence before creating
```

#### **Missing advanced feature tables**  
```bash
# Run the advanced features SQL file
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/00_init.sql
```

#### **CDL system not loading personality data**
```bash
# Ensure core CDL tables exist
alembic upgrade head
# Check for personality_traits and character_values tables
```

#### **Enrichment system not working**
```bash  
# Run enrichment schema
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/semantic_knowledge_graph_schema.sql
```

### **Emergency Recovery**
```bash
# Complete fresh database rebuild (DESTRUCTIVE - backup first!)
dropdb -h localhost -p 5433 -U postgres whisperengine
createdb -h localhost -p 5433 -U postgres whisperengine
alembic upgrade head
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
     -f sql/semantic_knowledge_graph_schema.sql
# Optionally: psql -f sql/00_init.sql for advanced features
```

---

## 📚 RELATED DOCUMENTATION

- **Complete Schema Reference**: `/docs/schema/FINAL_DATABASE_SCHEMA.md`
- **Schema Evolution History**: `/docs/schema/SCHEMA_EVOLUTION_TIMELINE.md`
- **Migration System Analysis**: `/docs/schema/MIGRATION_SYSTEM_TRUTH.md`
- **Quick Reference Guide**: `/docs/schema/DATABASE_SCHEMA_QUICK_REFERENCE.md`

---

**Remember**: The hybrid architecture is intentional and serves different development needs. Use Alembic for stable, production-critical features and SQL files for rapid development of advanced capabilities.**