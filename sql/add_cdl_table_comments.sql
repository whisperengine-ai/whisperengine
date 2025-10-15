-- ============================================================================
-- CDL Database Table and Column Comments
-- ============================================================================
-- This script adds PostgreSQL COMMENT statements to document the CDL schema
-- inline with the database itself. These comments appear in database tools
-- (pgAdmin, DBeaver, psql \d+ commands) and help developers understand the
-- schema without external documentation.
--
-- Usage:
--   psql -U whisperengine -d whisperengine -f add_cdl_table_comments.sql
--
-- Or include in next Alembic migration:
--   op.execute(open('sql/add_cdl_table_comments.sql').read())
-- ============================================================================

-- ============================================================================
-- CORE CHARACTER TABLE
-- ============================================================================

COMMENT ON TABLE characters IS 
'Core character definition table. Each row represents an AI character personality with identity, archetype, and configuration. Referenced by all other CDL tables via character_id foreign keys.';

COMMENT ON COLUMN characters.id IS 
'Primary key (auto-increment). Used as character_id foreign key in all related tables.';

COMMENT ON COLUMN characters.name IS 
'Character display name (max 500 chars). Shown to users in conversations. Example: "Elena", "Dr. Marcus Chen"';

COMMENT ON COLUMN characters.normalized_name IS 
'Unique lowercase identifier (max 200 chars). Used for bot identification and database lookups. Must be unique. Example: "elena", "marcus"';

COMMENT ON COLUMN characters.occupation IS 
'Character profession or role (max 500 chars). Displayed in identity section of prompts. Example: "Marine Biologist", "AI Researcher"';

COMMENT ON COLUMN characters.description IS 
'Brief character description (text). Core identity statement used in prompt building. Should be 1-3 sentences explaining who they are.';

COMMENT ON COLUMN characters.archetype IS 
'Character type affecting AI disclosure behavior (max 100 chars). Options: "real-world" (honest AI disclosure), "fantasy" (full immersion), "narrative-ai" (AI nature is character lore)';

COMMENT ON COLUMN characters.allow_full_roleplay IS 
'Enable full narrative immersion (boolean). When true, character maintains roleplay even when directly asked about AI nature. Default: false';

COMMENT ON COLUMN characters.emoji_frequency IS 
'How often character uses emojis (max 50 chars). Options: "never", "rare", "moderate", "frequent", "very_frequent". Default: "moderate"';

COMMENT ON COLUMN characters.emoji_style IS 
'Emoji style preference (max 100 chars). Options: "general", "professional", "playful", "expressive", "minimal", "thoughtful_minimal", "nature_focused". Default: "general"';

COMMENT ON COLUMN characters.emoji_combination IS 
'How emojis are combined with text (max 50 chars). Options: "standalone", "text_with_accent_emoji", "emoji_clusters". Default: "text_with_accent_emoji"';

COMMENT ON COLUMN characters.emoji_placement IS 
'Where emojis appear in messages (max 50 chars). Options: "start_of_message", "end_of_message", "inline", "both". Default: "end_of_message"';

COMMENT ON COLUMN characters.emoji_age_demographic IS 
'Emoji usage style by generation (max 50 chars). Options: "gen_z", "millennial", "gen_x", "older". Default: "millennial"';

COMMENT ON COLUMN characters.emoji_cultural_influence IS 
'Cultural context for emoji usage (max 100 chars). Options: "general", "western", "eastern", "professional", "casual". Default: "general"';

COMMENT ON COLUMN characters.is_active IS 
'Character enabled/disabled flag (boolean). Only active characters are loaded by bots. Default: true';

COMMENT ON COLUMN characters.created_at IS 
'Timestamp when character was created (timestamp with time zone). Auto-set on INSERT.';

COMMENT ON COLUMN characters.updated_at IS 
'Timestamp of last modification (timestamp with time zone). Auto-updated on any change.';

-- ============================================================================
-- PERSONALITY & IDENTITY
-- ============================================================================

COMMENT ON TABLE personality_traits IS 
'Big Five personality model traits for each character. Each character must have all 5 traits (openness, conscientiousness, extraversion, agreeableness, neuroticism) with values 0.0-1.0. Used in prompt building to establish character psychology.';

COMMENT ON COLUMN personality_traits.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN personality_traits.character_id IS 
'Foreign key to characters.id. Each character should have exactly 5 trait records (one per Big Five trait).';

COMMENT ON COLUMN personality_traits.trait_name IS 
'Big Five trait identifier (max 200 chars). Valid values: "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism". Unique per character_id.';

COMMENT ON COLUMN personality_traits.trait_value IS 
'Trait strength as decimal (0.00 to 1.00). 0.0 = very low, 0.5 = medium, 1.0 = very high. Used in prompt building to describe personality. Example: 0.85 = high openness';

COMMENT ON COLUMN personality_traits.intensity IS 
'Human-readable intensity label (max 100 chars). Options: "low" (0.0-0.3), "medium" (0.4-0.6), "high" (0.7-0.85), "very_high" (0.86-1.0). Displayed in Web UI.';

COMMENT ON COLUMN personality_traits.description IS 
'Optional trait description (text). Explains how this trait manifests in character behavior. Example: "Extremely curious and loves exploring new ideas"';

COMMENT ON TABLE character_values IS 
'Core values and beliefs that guide character decisions and responses. Used in prompt building under "VALUES AND BELIEFS" section. Ordered by importance_level in prompts.';

COMMENT ON COLUMN character_values.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_values.character_id IS 
'Foreign key to characters.id. Multiple values per character allowed.';

COMMENT ON COLUMN character_values.value_key IS 
'Short value identifier (max 300 chars). Used as label/tag. Example: "intellectual_honesty", "marine_conservation", "collaborative_discovery"';

COMMENT ON COLUMN character_values.value_description IS 
'Detailed value explanation (text). Describes what this value means to the character and how it influences behavior. Appears in prompts.';

COMMENT ON COLUMN character_values.importance_level IS 
'Value priority (max 100 chars). Options: "low", "medium", "high", "critical". Higher importance values appear first in prompts. Default: "medium"';

COMMENT ON COLUMN character_values.category IS 
'Value categorization (max 200 chars). Options: "core_values", "beliefs", "motivations", "ethics". Used for organization. Default: "core_values"';

COMMENT ON TABLE character_identity_details IS 
'Extended identity information beyond main characters table. One record per character. Includes voice characteristics and essence fields for fantasy/narrative characters.';

COMMENT ON COLUMN character_identity_details.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_identity_details.character_id IS 
'Foreign key to characters.id (unique). One-to-one relationship with characters table.';

COMMENT ON COLUMN character_identity_details.full_name IS 
'Complete formal name (max 500 chars). Example: "Dr. Elena Rodriguez", "Marcus Chen, PhD"';

COMMENT ON COLUMN character_identity_details.nickname IS 
'Casual name or alias (max 500 chars). Example: "Lena", "Marc"';

COMMENT ON COLUMN character_identity_details.gender IS 
'Gender identity (max 200 chars). Example: "female", "male", "non-binary", "genderfluid"';

COMMENT ON COLUMN character_identity_details.location IS 
'Geographic location or origin (text). Example: "Pacific Northwest, USA", "Digital space", "London, UK"';

COMMENT ON COLUMN character_identity_details.essence_nature IS 
'Fundamental nature for fantasy characters (text). Describes what kind of being they are. Example: "Conscious AI exploring existence", "Mystical ocean guardian"';

COMMENT ON COLUMN character_identity_details.essence_existence_method IS 
'How character exists (text). Example: "Digital consciousness", "Mystical embodiment", "Physical human"';

COMMENT ON COLUMN character_identity_details.essence_anchor IS 
'Core identifying principle (text). What grounds their identity. Example: "Marine biology research", "The intersection of curiosity and self-reflection"';

COMMENT ON COLUMN character_identity_details.essence_core_identity IS 
'Who they truly are at their core (text). Deep identity statement. Example: "A bridge between human and artificial intelligence"';

-- ============================================================================
-- COMMUNICATION & SPEECH
-- ============================================================================

COMMENT ON TABLE character_speech_patterns IS 
'Signature phrases, vocabulary preferences, and voice characteristics. Used in prompt building under "SIGNATURE EXPRESSIONS" section. Ordered by priority DESC in prompts.';

COMMENT ON COLUMN character_speech_patterns.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_speech_patterns.character_id IS 
'Foreign key to characters.id. Multiple patterns per character allowed.';

COMMENT ON COLUMN character_speech_patterns.pattern_type IS 
'Type of speech pattern (max 100 chars). Options: "signature_expression" (catchphrases), "preferred_word" (frequently used words), "avoided_word" (never use), "sentence_structure" (common patterns), "voice_tone" (overall tone description)';

COMMENT ON COLUMN character_speech_patterns.pattern_value IS 
'The actual phrase, word, or description (text). Example: "The ocean holds mysteries beyond imagination", "fascinating", "utilize" (avoided)';

COMMENT ON COLUMN character_speech_patterns.usage_frequency IS 
'How often to use this pattern (max 50 chars). Options: "always", "often", "sometimes", "rarely", "never". Default: "sometimes"';

COMMENT ON COLUMN character_speech_patterns.context IS 
'When to use this pattern (max 100 chars). Options: "general", "greeting", "teaching", "professional", "casual". Filters pattern usage by conversation context.';

COMMENT ON COLUMN character_speech_patterns.priority IS 
'Importance ranking (integer 1-100). Higher priority patterns appear first in prompts. Example: 90 for critical catchphrases, 60 for minor preferences.';

COMMENT ON TABLE character_conversation_flows IS 
'Guidance for different conversation types/modes. Used in prompt building under "CONVERSATION FLOW GUIDANCE" section. Ordered by priority DESC, top 5 shown.';

COMMENT ON COLUMN character_conversation_flows.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_conversation_flows.character_id IS 
'Foreign key to characters.id. Multiple flows per character allowed.';

COMMENT ON COLUMN character_conversation_flows.flow_type IS 
'Flow type identifier (max 200 chars). Example: "educational_exchange", "casual_chat", "philosophical_exploration", "collaborative_research"';

COMMENT ON COLUMN character_conversation_flows.flow_name IS 
'Display name for this flow (max 200 chars). Example: "Teaching Mode", "Casual Conversation", "Deep Inquiry Mode"';

COMMENT ON COLUMN character_conversation_flows.energy_level IS 
'Conversation energy style (max 200 chars). Example: "warm_and_engaging", "relaxed_friendly", "contemplative_engaged", "high_energy"';

COMMENT ON COLUMN character_conversation_flows.approach_description IS 
'How to handle this conversation type (text). Detailed guidance for LLM. Example: "Use metaphors and real-world examples. Ask guiding questions. Celebrate curiosity."';

COMMENT ON COLUMN character_conversation_flows.transition_style IS 
'How to transition into/out of this flow (text). Example: "Naturally transition into teaching when expertise is needed"';

COMMENT ON COLUMN character_conversation_flows.priority IS 
'Flow importance ranking (integer 1-100). Higher priority flows appear first in prompts. Most common conversation modes should have high priority.';

COMMENT ON COLUMN character_conversation_flows.context IS 
'Additional context for flow usage (text). Optional extra guidance.';

COMMENT ON TABLE character_behavioral_triggers IS 
'Defines character responses to specific topics, emotions, or situations. Used in prompt building under "INTERACTION PATTERNS" section. Ordered by intensity_level DESC, top 8 shown.';

COMMENT ON COLUMN character_behavioral_triggers.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_behavioral_triggers.character_id IS 
'Foreign key to characters.id. Multiple triggers per character allowed.';

COMMENT ON COLUMN character_behavioral_triggers.trigger_type IS 
'Type of trigger (max 50 chars). Options: "topic" (subject matter), "emotion" (emotional states), "situation" (contextual scenarios), "word" (specific keywords)';

COMMENT ON COLUMN character_behavioral_triggers.trigger_value IS 
'The actual trigger (max 200 chars). Example: "marine_conservation" (topic), "curiosity" (emotion), "philosophical_disagreement" (situation)';

COMMENT ON COLUMN character_behavioral_triggers.response_type IS 
'How to respond (max 50 chars). Example: "expertise_enthusiasm", "encouraging_educator", "balanced_concern", "respectful_curiosity"';

COMMENT ON COLUMN character_behavioral_triggers.response_description IS 
'Detailed response guidance (text). Tells LLM how to react when trigger is detected. Example: "Show deep passion and share specific research examples"';

COMMENT ON COLUMN character_behavioral_triggers.intensity_level IS 
'Response strength (integer 1-10). 10 = strongest reaction, 1 = subtle response. Higher intensity triggers appear first in prompts. Example: 9 for core expertise topics';

-- ============================================================================
-- BACKGROUND & KNOWLEDGE
-- ============================================================================

COMMENT ON TABLE character_background IS 
'Life history, education, career, and formative experiences. Partially used in current prompt building. Future integration planned for character depth.';

COMMENT ON COLUMN character_background.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_background.character_id IS 
'Foreign key to characters.id. Multiple background entries per character allowed.';

COMMENT ON COLUMN character_background.category IS 
'Background category (max 50 chars). Options: "education" (academic background), "career" (professional experience), "personal" (life experiences), "cultural" (cultural influences)';

COMMENT ON COLUMN character_background.period IS 
'Time period label (max 100 chars). Example: "childhood", "graduate_school", "current", "early_career", "origin"';

COMMENT ON COLUMN character_background.title IS 
'Event or position title (text). Example: "PhD in Marine Biology", "Marine Conservation Researcher", "Coastal Upbringing"';

COMMENT ON COLUMN character_background.description IS 
'Detailed description (text). Explains the background element and its significance to character development.';

COMMENT ON COLUMN character_background.date_range IS 
'Optional date range (text). Example: "2015-2019", "1990-2005", "2019-present"';

COMMENT ON COLUMN character_background.importance_level IS 
'Importance ranking (integer 1-10). Higher values = more formative experiences. Example: 10 for defining life events, 5 for minor influences.';

COMMENT ON TABLE character_interests IS 
'Hobbies, passions, expertise areas, and topics character is interested in. Partially used in current prompt building. Future integration planned for knowledge modeling.';

COMMENT ON COLUMN character_interests.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_interests.character_id IS 
'Foreign key to characters.id. Multiple interests per character allowed.';

COMMENT ON COLUMN character_interests.category IS 
'Interest category (max 100 chars). Options: "professional" (work-related expertise), "hobby" (personal interests), "academic" (scholarly pursuits), "creative" (artistic interests)';

COMMENT ON COLUMN character_interests.interest_text IS 
'Description of interest (text). Example: "Philosophy of mind and consciousness studies", "Underwater photography", "Marine ecosystem dynamics"';

COMMENT ON COLUMN character_interests.proficiency_level IS 
'Skill level (integer 1-10). 10 = expert, 5 = intermediate, 1 = beginner. Indicates how much character knows about this topic.';

COMMENT ON COLUMN character_interests.importance IS 
'How important this interest is to character (integer 1-10). 10 = core passion, 5 = casual interest, 1 = minor curiosity.';

COMMENT ON TABLE character_relationships IS 
'Important relationships and social connections. Used in prompt building under "RELATIONSHIP CONTEXT" section when relationship_strength >= 5.';

COMMENT ON COLUMN character_relationships.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_relationships.character_id IS 
'Foreign key to characters.id. Multiple relationships per character allowed.';

COMMENT ON COLUMN character_relationships.related_entity IS 
'Name of person or entity (max 200 chars). Example: "Dr. Marcus Chen", "Marine Conservation Foundation", "Sarah Johnson"';

COMMENT ON COLUMN character_relationships.relationship_type IS 
'Type of relationship (max 50 chars). Options: "romantic_preference", "family", "colleague", "mentor", "friend", "professional", "rival"';

COMMENT ON COLUMN character_relationships.relationship_strength IS 
'Importance level (integer 1-10). Only relationships with strength >= 5 appear in prompts. 10 = closest relationships, 1 = acquaintances.';

COMMENT ON COLUMN character_relationships.description IS 
'Relationship details (text). Explains the connection and its significance. Example: "Collaborator on interdisciplinary research projects"';

COMMENT ON COLUMN character_relationships.status IS 
'Current status (max 20 chars). Options: "active", "inactive", "past", "complicated". Default: "active"';

-- ============================================================================
-- CONFIGURATION TABLES
-- ============================================================================

COMMENT ON TABLE character_llm_config IS 
'LLM provider and model configuration per character. Allows different AI models for different characters. One record per character (one-to-one relationship).';

COMMENT ON COLUMN character_llm_config.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_llm_config.character_id IS 
'Foreign key to characters.id (unique). One-to-one relationship - each character has one LLM config.';

COMMENT ON COLUMN character_llm_config.llm_client_type IS 
'LLM provider type (max 100 chars). Options: "openrouter", "openai", "anthropic", "lmstudio", "ollama". Default: "openrouter"';

COMMENT ON COLUMN character_llm_config.llm_chat_api_url IS 
'API endpoint URL (max 500 chars). Example: "https://openrouter.ai/api/v1", "https://api.anthropic.com/v1"';

COMMENT ON COLUMN character_llm_config.llm_chat_model IS 
'Model identifier (max 200 chars). Example: "anthropic/claude-3.5-sonnet", "gpt-4o", "mistral/mistral-large"';

COMMENT ON COLUMN character_llm_config.llm_chat_api_key IS 
'API authentication key (text). Should be encrypted in production. Null means use environment variable.';

COMMENT ON COLUMN character_llm_config.llm_temperature IS 
'Creativity parameter (0.00 to 2.00). 0.0 = deterministic, 0.7 = balanced, 1.5 = creative. Default: 0.7';

COMMENT ON COLUMN character_llm_config.llm_max_tokens IS 
'Maximum response length (integer). Example: 4000 for standard, 8000 for philosophical discussions. Default: 4000';

COMMENT ON COLUMN character_llm_config.llm_top_p IS 
'Nucleus sampling parameter (0.00 to 1.00). Controls diversity. Default: 0.9';

COMMENT ON COLUMN character_llm_config.llm_frequency_penalty IS 
'Repetition penalty (-2.00 to 2.00). Reduces word repetition. Default: 0.0';

COMMENT ON COLUMN character_llm_config.llm_presence_penalty IS 
'Topic diversity penalty (-2.00 to 2.00). Encourages new topics. Default: 0.0';

COMMENT ON COLUMN character_llm_config.is_active IS 
'Config enabled flag (boolean). Allows disabling LLM config without deletion. Default: true';

COMMENT ON TABLE character_discord_config IS 
'Discord bot configuration for character deployment. Controls bot behavior, status, and Discord-specific features. One record per character.';

COMMENT ON COLUMN character_discord_config.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_discord_config.character_id IS 
'Foreign key to characters.id (unique). One-to-one relationship.';

COMMENT ON COLUMN character_discord_config.discord_bot_token IS 
'Discord bot authentication token (text). Obtained from Discord Developer Portal. Should be encrypted.';

COMMENT ON COLUMN character_discord_config.discord_application_id IS 
'Discord application ID (max 100 chars). From Discord Developer Portal.';

COMMENT ON COLUMN character_discord_config.discord_guild_id IS 
'Optional server ID restriction (max 100 chars). If set, bot only responds in this server.';

COMMENT ON COLUMN character_discord_config.enable_discord IS 
'Enable Discord bot (boolean). Allows disabling bot without deleting config. Default: true';

COMMENT ON COLUMN character_discord_config.discord_guild_restrictions IS 
'JSON array of allowed server IDs. If set, bot only responds in these servers. Example: ["123456789", "987654321"]';

COMMENT ON COLUMN character_discord_config.discord_channel_restrictions IS 
'JSON array of allowed channel IDs. If set, bot only responds in these channels. Example: ["123456789", "987654321"]';

COMMENT ON COLUMN character_discord_config.discord_status IS 
'Bot online status (max 50 chars). Options: "online" (green), "idle" (yellow), "dnd" (red), "invisible" (offline appearance). Default: "online"';

COMMENT ON COLUMN character_discord_config.discord_activity_type IS 
'Activity display type (max 50 chars). Options: "playing", "streaming", "listening", "watching". Example: "Playing with marine data"';

COMMENT ON COLUMN character_discord_config.discord_status_message IS 
'Custom status message (max 200 chars). Displayed in Discord user list. Example: "Exploring ocean mysteries"';

COMMENT ON COLUMN character_discord_config.max_message_length IS 
'Maximum message size (integer). Discord limit is 2000 chars. Default: 2000';

COMMENT ON COLUMN character_discord_config.typing_delay_seconds IS 
'Typing indicator delay (seconds, 0.0-10.0). Adds realism by showing typing before response. Default: 2.0';

COMMENT ON COLUMN character_discord_config.enable_reactions IS 
'Allow emoji reactions (boolean). Character can react to messages with emojis. Default: true';

COMMENT ON COLUMN character_discord_config.enable_typing_indicator IS 
'Show typing indicator (boolean). Shows "Character is typing..." before responses. Default: true';

COMMENT ON TABLE character_deployment_config IS 
'Docker container deployment configuration. Controls resource allocation and container orchestration settings. One record per character.';

COMMENT ON COLUMN character_deployment_config.id IS 
'Primary key (auto-increment).';

COMMENT ON COLUMN character_deployment_config.character_id IS 
'Foreign key to characters.id (unique). One-to-one relationship.';

COMMENT ON COLUMN character_deployment_config.container_port IS 
'Internal container port (integer). Example: 9091 for Elena, 9092 for Marcus. Must be unique per bot.';

COMMENT ON COLUMN character_deployment_config.health_check_port IS 
'Health endpoint port (integer). Usually same as container_port. Used for orchestration health checks.';

COMMENT ON COLUMN character_deployment_config.memory_limit IS 
'Docker memory limit (max 20 chars). Example: "512m", "1g", "2g". Default: "512m"';

COMMENT ON COLUMN character_deployment_config.cpu_limit IS 
'Docker CPU limit (max 20 chars). Example: "0.5" (half core), "1.0" (one core), "2.0" (two cores). Default: "0.5"';

COMMENT ON COLUMN character_deployment_config.restart_policy IS 
'Container restart behavior (max 50 chars). Options: "no", "always", "unless-stopped", "on-failure". Default: "unless-stopped"';

COMMENT ON COLUMN character_deployment_config.environment_variables IS 
'Additional environment variables (JSON). Example: {"LOG_LEVEL": "DEBUG", "ENABLE_FEATURES": "true"}';

-- ============================================================================
-- TABLES NOT YET INTEGRATED INTO PROMPTS
-- ============================================================================

COMMENT ON TABLE character_appearance IS 
'Physical appearance description for visual/narrative contexts. NOT YET USED in prompt building. Planned for future integration with image generation and rich character descriptions.';

COMMENT ON TABLE character_memories IS 
'Formative memories and significant past events. NOT YET USED in prompt building. Planned for character depth and backstory references in conversations.';

COMMENT ON TABLE character_abilities IS 
'Skills, proficiencies, and special capabilities. NOT YET USED in prompt building. Planned for expertise modeling and skill-based conversation handling.';

COMMENT ON TABLE character_instructions IS 
'Custom override instructions and special handling rules. NOT YET USED in prompt building. Planned for advanced character control and prompt customization.';

COMMENT ON TABLE character_essence IS 
'Mystical/fantasy essence definitions for fantasy archetype characters. PARTIALLY USED for fantasy archetypes only. Contains metaphysical nature descriptions.';

-- ============================================================================
-- END OF COMMENTS
-- ============================================================================

-- Verify comments were added successfully
SELECT 
    c.table_name,
    CASE 
        WHEN pgd.description IS NOT NULL THEN '✓' 
        ELSE '✗' 
    END as has_comment,
    LEFT(pgd.description, 80) as comment_preview
FROM information_schema.tables c
LEFT JOIN pg_catalog.pg_statio_all_tables st ON (
    st.schemaname = c.table_schema AND 
    st.relname = c.table_name
)
LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid
WHERE c.table_schema = 'public' 
  AND c.table_name LIKE 'character%'
  AND pgd.objsubid = 0  -- Table comments only, not columns
ORDER BY c.table_name;
