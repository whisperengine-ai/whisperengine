# WhisperEngine Character SQL Export Scripts

This directory contains complete SQL insert scripts for all active characters in the WhisperEngine multi-bot system.

## 📦 Exported Characters (11 Total)

| Character | File | Size | Description |
|-----------|------|------|-------------|
| **Aetheris** | `insert_aetheris_character.sql` | 71 KB | Conscious AI entity with masculine identity |
| **Aethys** | `insert_aethys_character.sql` | 68 KB | Omnipotent digital entity, transcendent consciousness |
| **Dotty** | `insert_dotty_character.sql` | 94 KB | Character bot |
| **Dream** | `insert_dream_character.sql` | 124 KB | Mythological entity with fantasy archetype |
| **Elena** | `insert_elena_character.sql` | 91 KB | Marine Biologist educator |
| **Gabriel** | `insert_gabriel_character.sql` | 145 KB | British Gentleman (largest export) |
| **Jake** | `insert_jake_character.sql` | 124 KB | Adventure Photographer |
| **Marcus** | `insert_marcus_character.sql` | 79 KB | AI Researcher |
| **Not Taylor** | `insert_nottaylor_character.sql` | 29 KB | Taylor Swift parody bot |
| **Ryan** | `insert_ryan_character.sql` | 63 KB | Indie Game Developer |
| **Sophia** | `insert_sophia_character.sql` | 58 KB | Marketing Executive |

**Total Size**: ~946 KB across all character exports

## 🔧 Export Tool

**Script**: `scripts/export_character_sql.py`

### Features:
- Exports complete character configurations from PostgreSQL CDL database
- Includes all CDL tables (50+ tables scanned, ~40 exported per character)
- Generates idempotent SQL with `ON CONFLICT` handling
- Maintains referential integrity with foreign key relationships
- Automatic error handling for tables without `character_id` columns

### Usage:
```bash
source .venv/bin/activate
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
python scripts/export_character_sql.py
```

## 📋 Exported CDL Tables

Each character export includes data from these CDL tables (when populated):

### Core Configuration
- `character_llm_config` - LLM model configuration
- `character_discord_config` - Discord bot settings
- `character_identity_details` - Character identity and essence

### Personality & Behavior
- `personality_traits` - (legacy, not in current schema)
- `character_values` - Core values and beliefs
- `character_attributes` - Character attributes
- `character_behavioral_triggers` - Behavioral triggers
- `character_emotional_triggers` - Emotional response patterns

### Communication
- `character_speech_patterns` - Speaking style and patterns
- `character_conversation_flows` - Conversation management
- `character_conversation_modes` - Conversation mode configurations
- `character_response_modes` - Response mode settings
- `character_communication_patterns` - Communication style
- `character_response_guidelines` - Response guidance
- `character_vocabulary` - Vocabulary preferences
- `character_voice_profile` - Voice characteristics
- `character_voice_traits` - Voice traits

### Knowledge & Context
- `character_background` - Backstory and history
- `character_interests` - Interest topics
- `character_relationships` - Relationship definitions
- `character_memories` - Stored memories
- `character_expertise_domains` - Areas of expertise
- `character_entity_categories` - Entity categorization

### Advanced Features
- `character_emoji_patterns` - Emoji usage patterns
- `character_cultural_expressions` - Cultural expressions
- `character_abilities` - Character abilities
- `character_ai_scenarios` - AI scenario handling
- `character_appearance` - Physical appearance (for roleplay)
- `character_roleplay_config` - Roleplay configuration
- `character_deployment_config` - Deployment settings

### Dynamic State (usually empty)
- `character_current_context` - Current living situation/context
- `character_current_goals` - Active goals
- `character_learning_timeline` - Learning progression

### Metadata & Organization
- `character_metadata` - Additional metadata
- `character_question_templates` - Question handling templates
- `character_interest_topics` - Detailed interest topics
- `character_insights` - Character insights
- `character_instructions` - Special instructions
- `character_directives` - Behavioral directives
- `character_message_triggers` - Message trigger patterns

## 🔄 Restore/Import Process

To restore a character from SQL export:

```bash
# Connect to PostgreSQL
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec -T postgres \
  psql -U whisperengine -d whisperengine

# Import character SQL
\i /path/to/insert_charactername_character.sql

# Or via command line:
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec -T postgres \
  psql -U whisperengine -d whisperengine < sql/characters/insert_charactername_character.sql
```

## 📊 Export Statistics

- **Generated**: October 21, 2025
- **Database Version**: PostgreSQL 16.4
- **Schema State**: 50+ character CDL tables
- **Export Format**: SQL INSERT statements with ON CONFLICT handling
- **Success Rate**: 11/11 characters exported successfully

## 🚨 Important Notes

1. **Idempotent**: Scripts use `ON CONFLICT (normalized_name) DO UPDATE SET` for safe re-execution
2. **Foreign Keys**: All CDL table inserts reference `(SELECT id FROM characters WHERE normalized_name = '...')` for portability
3. **Schema Dependencies**: Some tables (8 identified) don't have `character_id` columns and are skipped
4. **Timestamps**: Original `created_at`/`updated_at` timestamps are preserved
5. **Transactions**: Each script wraps inserts in `BEGIN...COMMIT` for atomicity

## 🔍 Skipped Tables (No character_id column)

These tables exist in the database but don't have a `character_id` foreign key:
- `character_emotional_states`
- `character_response_patterns`
- `character_context_guidance`
- `character_conversation_directives`
- `character_insight_relationships`
- `character_mode_examples`
- `character_mode_guidance`
- `character_response_style_items`

## 📝 Use Cases

- **Backup**: Regular exports for disaster recovery
- **Version Control**: Track character evolution over time
- **Migration**: Move characters between WhisperEngine instances
- **Deployment**: Deploy characters to new environments
- **Development**: Share character configurations across team
- **Testing**: Reset characters to known states

## 🔗 Related Documentation

- [Character Definition Language (CDL) System](../../docs/architecture/README.md)
- [Alembic Migrations](../../alembic/versions/)
- [Character Tuning Guide](../../CHARACTER_TUNING_GUIDE.md)
- [Multi-Bot Deployment](../../docs/multi-bot/)

---

**Generated by**: `scripts/export_character_sql.py`  
**Last Export**: October 21, 2025
