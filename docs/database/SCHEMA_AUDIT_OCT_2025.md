# WhisperEngine Database Schema Audit - October 2025

**Date**: October 19, 2025  
**Purpose**: Audit actual tables queried by code vs Alembic migrations to ensure schema consistency

## Executive Summary

**CRITICAL FINDING**: Many tables are queried by the code but are NOT created by Alembic migrations. They were created by legacy SQL files in `src/database/migrations/` and `sql/`.

## Tables Actively Used by Code (from grep analysis)

### Core Character & CDL Tables
- `characters` ✅ (in baseline)
- `personality_traits` ❌ **NOT IN ALEMBIC** (created by 003_clean_rdbms_cdl_schema.sql)
- `communication_styles` ❌ **NOT IN ALEMBIC** (created by 003_clean_rdbms_cdl_schema.sql)
- `character_values` ❌ **NOT IN ALEMBIC** (created by 003_clean_rdbms_cdl_schema.sql)
- `character_identity` ✅ (in baseline - but different schema!)
- `character_attributes` ✅ (in baseline)
- `character_communication` ✅ (in baseline - but different from communication_styles!)

### CDL Extended Tables (code queries these)
- `character_interest_topics` ✅ (in Alembic 20251012_1338)
- `character_question_templates` ✅ (in Alembic 20251012_2205)
- `generic_keyword_templates` ✅ (in Alembic 20251012_2230)
- `character_conversation_flows` ❌ **Migrated but confusing state**
- `character_conversation_modes` ✅ (in Alembic)
- `character_emoji_patterns` ✅ (in Alembic 20251013_emoji)
- `character_emotional_states` ✅ (in Alembic 20251017_104918)
- `character_learning_timeline` ✅ (in Alembic 20251017_1919)

### Character Extended Details (code queries)
- `character_abilities`
- `character_ai_scenarios`
- `character_appearance`
- `character_background`
- `character_behavioral_triggers`
- `character_communication_patterns`
- `character_cultural_expressions`
- `character_essence`
- `character_expertise_domains`
- `character_general_conversation`
- `character_insight_relationships`
- `character_insights`
- `character_instructions`
- `character_memories`
- `character_message_triggers`
- `character_metadata`
- `character_mode_examples`
- `character_mode_guidance`
- `character_relationships`
- `character_response_guidelines`
- `character_response_style`
- `character_response_style_items`
- `character_roleplay_config`
- `character_speech_patterns`
- `character_voice_traits`

**STATUS**: Need to verify which are in Alembic and which need migrations

### Configuration Tables
- `character_llm_config` ✅ (in Alembic 20251014_2037)
- `character_discord_config` ✅ (in Alembic 20251014_2037)
- `character_deployment_config` ✅ (in Alembic 20251015_0503)

### User & Relationship Tables
- `users` ✅ (in baseline)
- `universal_users` ❌ **NOT IN ALEMBIC** (created by scripts/create_universal_identity_tables.sql)
- `user_relationships` ✅ (in baseline)
- `user_facts` ✅ (in baseline)
- `user_profiles` ❌ **NOT IN ALEMBIC**
- `user_conversation_preferences` ❌ **NOT IN ALEMBIC** (20251019_1857_a71d62f22c10 converts to JSONB)

### Enrichment/Knowledge Graph Tables
- `fact_entities` ✅ DOCUMENTED (in 20251019_1858_27e207ded5a0 - doc-only!)
- `user_fact_relationships` ✅ DOCUMENTED (same migration)
- `entity_relationships` ✅ DOCUMENTED (same migration)

**CRITICAL**: These exist via `sql/semantic_knowledge_graph_schema.sql` but Alembic migration is DOC-ONLY!

### Memory & Conversation Tables
- `conversations` ❌ **NOT IN ALEMBIC**
- `conversation_summaries` ❌ **NOT IN ALEMBIC**
- `dynamic_personality_profiles` ❌ **NOT IN ALEMBIC**
- `dynamic_personality_traits` ❌ **NOT IN ALEMBIC**
- `relationship_scores` ❌ **NOT IN ALEMBIC**

### Personality Evolution Tables (Sprint 4)
- `personality_optimization_attempts` ❌ **NOT IN ALEMBIC** (created by create_personality_evolution_schema.sql)
- `personality_optimization_results` ❌ **NOT IN ALEMBIC** (same file)
- `personality_parameter_adjustments` ❌ **NOT IN ALEMBIC** (same file)
- `personality_evolution_timeline` ❌ **NOT IN ALEMBIC** (same file)

### Roleplay Tables
- `roleplay_transactions` ❌ **NOT IN ALEMBIC** (created by sql/create_roleplay_transactions.sql)

### Security Tables
- `banned_users` ❌ **NOT IN ALEMBIC**

### System Tables
- `schema_migrations` ❌ **NOT IN ALEMBIC** (legacy pre-Alembic)

## Schema Conflict: character_identity vs personality_traits

**MAJOR ISSUE**: Code expects TWO DIFFERENT schemas:

### What Baseline Creates (character_identity)
```sql
CREATE TABLE character_identity (
    id, character_id, full_name, nicknames, age, occupation, description
)
```

### What Code Actually Queries (personality_traits from 003_clean_rdbms_cdl_schema.sql)
```sql
CREATE TABLE personality_traits (
    id, character_id, trait_name, trait_value, intensity, description
)
```

**These are DIFFERENT tables serving different purposes!**

## Legacy SQL Files Still in Use

### `/src/database/migrations/` (PRE-ALEMBIC ERA)
1. `001_create_cdl_schema.sql` - Old CDL schema (superseded?)
2. `003_clean_rdbms_cdl_schema.sql` - **CREATES personality_traits, communication_styles, character_values**
3. `004_expand_field_sizes.sql` - Field expansions
4. `create_personality_evolution_schema.sql` - **Sprint 4 personality evolution tables**

### `/sql/` (MIXED ERA - SOME STILL ACTIVE)
1. `semantic_knowledge_graph_schema.sql` - **ACTIVE** (creates fact_entities, user_fact_relationships, entity_relationships)
2. `create_roleplay_transactions.sql` - **ACTIVE** (creates roleplay_transactions table)
3. `init_schema.sql` - **LEGACY** (Oct 10) - uses cdl_* prefix (outdated!)

### `/scripts/` (UTILITY SQL)
1. `create_universal_identity_tables.sql` - **ACTIVE** (creates universal_users)
2. `privacy_schema.sql` - Privacy-related tables

## Alembic Migration Coverage

### ✅ COVERED BY ALEMBIC
- Core tables: users, characters, character_identity, character_attributes, character_communication, user_relationships, user_facts
- Interest topics, question templates, generic keyword templates
- Emoji patterns, emotional states
- Character learning timeline
- LLM & Discord configuration
- Bot deployments

### ❌ NOT COVERED BY ALEMBIC (Need migrations)
- personality_traits (CRITICAL - code depends on this!)
- communication_styles (CRITICAL - code depends on this!)
- character_values (CRITICAL - code depends on this!)
- All personality evolution tables (4 tables)
- universal_users
- roleplay_transactions
- banned_users
- fact_entities, user_fact_relationships, entity_relationships (doc-only migration!)
- user_profiles, user_conversation_preferences
- conversations, conversation_summaries
- dynamic_personality_profiles, dynamic_personality_traits
- relationship_scores

## Recommendations

### IMMEDIATE ACTION REQUIRED

1. **Create Alembic migration for personality_traits, communication_styles, character_values**
   - These are CRITICAL tables queried by cdl_ai_integration.py
   - Source: `src/database/migrations/003_clean_rdbms_cdl_schema.sql`
   - Must be created AFTER baseline but BEFORE any character data migrations

2. **Create Alembic migration for personality evolution tables**
   - Source: `src/database/migrations/create_personality_evolution_schema.sql`
   - personality_optimization_attempts, personality_optimization_results, personality_parameter_adjustments, personality_evolution_timeline

3. **Create Alembic migration for universal_users**
   - Source: `scripts/create_universal_identity_tables.sql`
   - Required for unified identity system

4. **Create Alembic migration for roleplay_transactions**
   - Source: `sql/create_roleplay_transactions.sql`
   - Required for roleplay workflow system

5. **Create Alembic migration for banned_users**
   - Source: Infer from ban_commands.py code

6. **Convert doc-only enrichment migration to actual CREATE TABLE**
   - Migration 20251019_1858_27e207ded5a0 is doc-only
   - Need actual CREATE TABLE statements for fact_entities, user_fact_relationships, entity_relationships

### Fix the Backfill Migration (IMMEDIATE)

The `20251019_2308_c64001afbd46_backfill_assistant_personality_data.py` migration fails because:
- It tries to INSERT INTO `character_personalities` (doesn't exist)
- Should INSERT INTO `personality_traits` (actual table name)
- Schema is wrong (expects columns openness, conscientiousness as columns, but actual schema uses trait_name/trait_value rows)

**REWRITE REQUIRED**:
```python
# CORRECT approach:
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
VALUES 
  (char_id, 'openness', 0.80, 'high', 'Open-minded'),
  (char_id, 'conscientiousness', 0.90, 'very_high', 'Organized'),
  # ... etc
```

### Schema Cleanup Strategy

1. **Keep Alembic as migration authority** going forward
2. **Migrate ALL active SQL files** to Alembic migrations
3. **Mark legacy SQL files** as deprecated with clear comments
4. **Document migration history** so we know which SQL files created which tables
5. **Test migration path** from clean database to current state

## Testing Required

1. **Fresh database test**: Run all Alembic migrations from scratch on empty database
2. **Verify code still works**: Run integration tests after migration
3. **Schema comparison**: Compare migrated schema vs working dev schema
4. **Data integrity**: Ensure no data loss during migration application

## Migration Creation Priority

**P0 (BLOCKING)**: Fix personality backfill migration
**P1 (CRITICAL)**: personality_traits, communication_styles, character_values  
**P2 (HIGH)**: universal_users, banned_users, roleplay_transactions  
**P3 (MEDIUM)**: personality evolution tables, enrichment tables (convert doc-only to real)  
**P4 (LOW)**: Cleanup legacy SQL files, add deprecation notices

---

**Next Steps**: Create missing Alembic migrations in priority order, starting with P0/P1.
