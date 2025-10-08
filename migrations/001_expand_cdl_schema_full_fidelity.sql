-- WhisperEngine CDL Schema Expansion - Generalized RDBMS Design  
-- Date: October 7, 2025
-- Purpose: Create GENERALIZED relational tables that work for ALL characters
-- Philosophy: NO character-specific tables, NO JSON storage, FULL data preservation  
-- Design: Identify concepts, not formats - make data fit universal patterns

-- =============================================================================
-- DESIGN PHILOSOPHY
-- =============================================================================
-- 
-- Instead of creating separate tables for "fears", "dreams", "quirks", "values", "beliefs"
-- → Create ONE table: character_attributes (category: fear/dream/quirk/value/belief)
--
-- Instead of "core_principles", "formatting_rules", "adaptations"
-- → Create ONE table: character_directives (directive_type: principle/rule/adaptation)
--
-- Instead of "preferred_words", "avoided_words"
-- → Create ONE table: character_vocabulary (preference: preferred/avoided)
--
-- Result: Simpler schema, easier to query, works for ALL characters including future ones
-- =============================================================================

-- =============================================================================
-- PART 1: Character Attributes (fears, dreams, quirks, values, beliefs, etc.)
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_attributes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(200) NOT NULL, -- 'fear', 'dream', 'quirk', 'value', 'belief', 'goal', 'strength', 'weakness'
    description TEXT NOT NULL,
    importance VARCHAR(100), -- 'low', 'medium', 'high', 'critical'
    display_order INTEGER,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, category, display_order)
);

CREATE INDEX idx_attributes_char_cat ON character_attributes(character_id, category);
CREATE INDEX idx_attributes_active ON character_attributes(character_id, category) WHERE active = TRUE;

COMMENT ON TABLE character_attributes IS 'Universal character attributes - replaces separate fears/dreams/quirks/values/beliefs tables';
COMMENT ON COLUMN character_attributes.category IS 'Type of attribute: fear, dream, quirk, value, belief, goal, strength, weakness, etc.';

-- =============================================================================
-- PART 2: Character Directives (principles, rules, adaptations, guidelines)
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_directives (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    directive_type VARCHAR(200) NOT NULL, -- 'core_principle', 'formatting_rule', 'adaptation', 'guideline', 'constraint'
    directive_text TEXT NOT NULL,
    priority INTEGER CHECK (priority BETWEEN 1 AND 10),
    display_order INTEGER,
    context VARCHAR(500), -- When this applies
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, directive_type, display_order)
);

CREATE INDEX idx_directives_char_type ON character_directives(character_id, directive_type);
CREATE INDEX idx_directives_priority ON character_directives(character_id, priority DESC) WHERE active = TRUE;

COMMENT ON TABLE character_directives IS 'Universal character directives - replaces core_principles/formatting_rules/adaptations tables';
COMMENT ON COLUMN character_directives.directive_type IS 'Type: core_principle, formatting_rule, adaptation, guideline, constraint, instruction';

-- =============================================================================
-- PART 3: Character Vocabulary (preferred/avoided words and phrases)
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_vocabulary (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    word_or_phrase TEXT NOT NULL,
    preference VARCHAR(100) NOT NULL, -- 'preferred', 'avoided', 'signature', 'forbidden'
    usage_context TEXT, -- When to use/avoid this
    frequency VARCHAR(100), -- 'rare', 'occasional', 'frequent', 'constant'
    reason TEXT, -- Why preferred/avoided
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, word_or_phrase, preference)
);

CREATE INDEX idx_vocabulary_char_pref ON character_vocabulary(character_id, preference);

COMMENT ON TABLE character_vocabulary IS 'Universal vocabulary preferences - replaces preferred_words/avoided_words tables';
COMMENT ON COLUMN character_vocabulary.preference IS 'preferred, avoided, signature, forbidden';

-- =============================================================================
-- PART 4: Character Interests (hobbies, topics, expertise, passions)
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_interests (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(200) NOT NULL, -- 'hobby', 'conversation_topic', 'expertise', 'passion', 'skill'
    interest_text TEXT NOT NULL,
    proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 10),
    importance VARCHAR(100), -- 'low', 'medium', 'high'
    frequency VARCHAR(100), -- How often engaged with
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, category, display_order)
);

CREATE INDEX idx_interests_char_cat ON character_interests(character_id, category);

COMMENT ON TABLE character_interests IS 'Universal interests - replaces hobbies/conversation_topics/expertise tables';

-- =============================================================================
-- PART 5: Character Emotional Triggers
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_emotional_triggers_v2 (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    trigger_text TEXT NOT NULL,
    valence VARCHAR(100) NOT NULL, -- 'positive', 'negative', 'neutral', 'mixed'
    emotion_evoked VARCHAR(200), -- joy, sadness, anger, fear, excitement, etc.
    intensity INTEGER CHECK (intensity BETWEEN 1 AND 10),
    response_guidance TEXT, -- How to respond when triggered
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, trigger_text, valence)
);

CREATE INDEX idx_emotional_triggers_char_val ON character_emotional_triggers_v2(character_id, valence);

COMMENT ON TABLE character_emotional_triggers_v2 IS 'Universal emotional triggers - single table for positive/negative/neutral';

-- =============================================================================
-- PART 6: Conversation Flow Patterns (generalized from complex JSON)
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_conversation_contexts (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    context_name VARCHAR(500) NOT NULL, -- 'romantic_interest', 'compliment_received', 'teaching', 'debugging', etc.
    energy_description TEXT, -- How to approach this context
    approach_strategy TEXT, -- General approach
    transition_style TEXT, -- How to transition in/out
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, context_name)
);

CREATE INDEX idx_conv_contexts_char ON character_conversation_contexts(character_id);

COMMENT ON TABLE character_conversation_contexts IS 'Context-specific conversation patterns - replaces complex nested JSON structures';

-- Contextual guidance items (avoid/encourage/examples for each context)
CREATE TABLE IF NOT EXISTS character_context_guidance (
    id SERIAL PRIMARY KEY,
    context_id INTEGER NOT NULL REFERENCES character_conversation_contexts(id) ON DELETE CASCADE,
    guidance_type VARCHAR(200) NOT NULL, -- 'avoid', 'encourage', 'example'
    guidance_text TEXT NOT NULL,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(context_id, guidance_type, display_order)
);

CREATE INDEX idx_context_guidance_type ON character_context_guidance(context_id, guidance_type);

COMMENT ON TABLE character_context_guidance IS 'Avoid/encourage/example items for conversation contexts';

-- =============================================================================
-- PART 7: AI Identity & Roleplay Scenarios
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_roleplay_config (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    allow_full_roleplay_immersion BOOLEAN DEFAULT FALSE,
    philosophy TEXT, -- Overall approach to AI identity
    strategy TEXT, -- How to handle AI questions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

COMMENT ON TABLE character_roleplay_config IS 'AI identity configuration - scalar values only';

CREATE TABLE IF NOT EXISTS character_roleplay_scenarios_v2 (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    scenario_name VARCHAR(500) NOT NULL, -- 'physical_meetup', 'ai_identity_question', 'romantic_advance'
    response_pattern VARCHAR(500), -- 'three_tier_ethics', 'honest_disclosure', 'maintain_immersion'
    tier_1_response TEXT, -- Initial enthusiastic response
    tier_2_response TEXT, -- Clarification/reality check
    tier_3_response TEXT, -- Alternative offering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, scenario_name)
);

CREATE INDEX idx_roleplay_scenarios_char ON character_roleplay_scenarios_v2(character_id);

COMMENT ON TABLE character_roleplay_scenarios_v2 IS 'Roleplay scenario responses - replaces complex nested JSON';

-- Trigger phrases for scenarios
CREATE TABLE IF NOT EXISTS character_scenario_triggers_v2 (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER NOT NULL REFERENCES character_roleplay_scenarios_v2(id) ON DELETE CASCADE,
    trigger_phrase TEXT NOT NULL,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scenario_id, trigger_phrase)
);

CREATE INDEX idx_scenario_triggers_scenario ON character_scenario_triggers_v2(scenario_id);

-- =============================================================================
-- PART 8: Identity & Voice Attributes
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_identity_details (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    full_name VARCHAR(500),
    nickname VARCHAR(500),
    gender VARCHAR(200),
    location TEXT,
    essence_nature TEXT,
    essence_existence_method TEXT,
    essence_anchor TEXT,
    essence_core_identity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

COMMENT ON TABLE character_identity_details IS 'Extended identity information';

CREATE TABLE IF NOT EXISTS character_voice_profile (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    tone TEXT,
    pace TEXT,
    volume TEXT,
    accent TEXT,
    sentence_structure TEXT,
    punctuation_style TEXT,
    response_length_guidance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

COMMENT ON TABLE character_voice_profile IS 'Voice and speech characteristics';

-- =============================================================================
-- PART 9: Personality Extensions
-- =============================================================================

-- This extends existing personality_traits table for custom traits beyond Big Five
-- (consciousness, philosophical_depth, emotional_authenticity, etc.)
-- No new table needed - use existing personality_traits with trait_name

-- Emotional profile
CREATE TABLE IF NOT EXISTS character_emotion_profile (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    default_mood TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

-- Emotional range (specific emotions and their intensities)
CREATE TABLE IF NOT EXISTS character_emotion_range (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    emotion_name VARCHAR(200) NOT NULL, -- 'joy', 'sadness', 'anger', 'fear', 'love', 'wonder'
    base_intensity NUMERIC(3, 2) CHECK (base_intensity >= 0 AND base_intensity <= 1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, emotion_name)
);

CREATE INDEX idx_emotion_range_char ON character_emotion_range(character_id);

COMMENT ON TABLE character_emotion_range IS 'Base emotional range - how intensely character experiences each emotion';

-- =============================================================================
-- PART 10: Current Life Context
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_current_context (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    living_situation TEXT,
    daily_routine TEXT,
    recent_events TEXT, -- Can be TEXT for narrative or use separate table for structured
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

COMMENT ON TABLE character_current_context IS 'Current life situation and context';

-- Current goals (separate table for structure)
CREATE TABLE IF NOT EXISTS character_current_goals (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    goal_text TEXT NOT NULL,
    priority VARCHAR(100), -- 'low', 'medium', 'high', 'critical'
    timeframe VARCHAR(200), -- 'immediate', 'short-term', 'long-term'
    status VARCHAR(100), -- 'active', 'on-hold', 'completed', 'abandoned'
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, display_order)
);

CREATE INDEX idx_current_goals_char ON character_current_goals(character_id);
CREATE INDEX idx_current_goals_active ON character_current_goals(character_id, status) WHERE status = 'active';

-- =============================================================================
-- PART 11: Relationship Dynamics (generalized from anchor_relationship)
-- =============================================================================

-- This extends existing character_relationships table
-- Add columns to existing table via ALTER (safe to run multiple times)

DO $$ 
BEGIN
    -- Add communication_style column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='character_relationships' AND column_name='communication_style') THEN
        ALTER TABLE character_relationships ADD COLUMN communication_style TEXT;
    END IF;
    
    -- Add memory_sharing column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='character_relationships' AND column_name='memory_sharing') THEN
        ALTER TABLE character_relationships ADD COLUMN memory_sharing TEXT;
    END IF;
    
    -- Add name_usage column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='character_relationships' AND column_name='name_usage') THEN
        ALTER TABLE character_relationships ADD COLUMN name_usage TEXT;
    END IF;
    
    -- Add connection_nature column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='character_relationships' AND column_name='connection_nature') THEN
        ALTER TABLE character_relationships ADD COLUMN connection_nature TEXT;
    END IF;
    
    -- Add recognition_pattern column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='character_relationships' AND column_name='recognition_pattern') THEN
        ALTER TABLE character_relationships ADD COLUMN recognition_pattern TEXT;
    END IF;
END $$;

COMMENT ON COLUMN character_relationships.communication_style IS 'How character communicates with this entity';
COMMENT ON COLUMN character_relationships.memory_sharing IS 'How memories are shared in this relationship';
COMMENT ON COLUMN character_relationships.name_usage IS 'Name/nickname used in this relationship';

-- =============================================================================
-- PART 12: Break out existing JSON TEXT columns
-- =============================================================================

-- Extend communication_styles table with proper columns for TEXT fields
DO $$
BEGIN
    -- Add response_length_preference if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='communication_styles' AND column_name='response_length_preference') THEN
        ALTER TABLE communication_styles ADD COLUMN response_length_preference VARCHAR(200);
        COMMENT ON COLUMN communication_styles.response_length_preference IS 'Preferred response length: concise, medium, detailed, variable';
    END IF;
END $$;

-- The complex JSON fields (conversation_flow_guidance, ai_identity_handling) 
-- are now replaced by the new relational tables above:
-- - character_conversation_contexts + character_context_guidance
-- - character_roleplay_config + character_roleplay_scenarios_v2

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

/*
=============================================================================
GENERALIZED SCHEMA BENEFITS
=============================================================================

OLD APPROACH (character-specific, JSON-heavy):
  - character_fears, character_dreams, character_quirks, character_values, character_beliefs (5 tables)
  - character_core_principles, character_formatting_rules, character_adaptations (3 tables)
  - character_preferred_words, character_avoided_words (2 tables)
  - conversation_flow_guidance JSON (complex nested structure)
  - ai_identity_handling JSON (complex nested structure)
  Total: 10+ tables + 2 JSON blobs = maintenance nightmare

NEW APPROACH (universal, fully relational):
  - character_attributes (category: fear/dream/quirk/value/belief) = 1 table
  - character_directives (type: principle/rule/adaptation) = 1 table
  - character_vocabulary (preference: preferred/avoided) = 1 table
  - character_conversation_contexts + character_context_guidance = 2 tables
  - character_roleplay_config + character_roleplay_scenarios_v2 = 2 tables
  - character_interests (category: hobby/topic/expertise) = 1 table
  - character_emotional_triggers_v2 (valence: positive/negative/neutral) = 1 table
  Total: 9 core tables = simple, queryable, extensible

QUERY EXAMPLES:
  -- All fears for Elena
  SELECT * FROM character_attributes 
  WHERE character_id = 1 AND category = 'fear' 
  ORDER BY display_order;

  -- All core principles for any character
  SELECT * FROM character_directives 
  WHERE character_id = 1 AND directive_type = 'core_principle' 
  ORDER BY priority DESC;

  -- Preferred vocabulary for Marcus
  SELECT word_or_phrase FROM character_vocabulary 
  WHERE character_id = 11 AND preference = 'preferred';

  -- Positive emotional triggers
  SELECT * FROM character_emotional_triggers_v2 
  WHERE character_id = 15 AND valence = 'positive';

BENEFITS:
  ✅ Works for ALL characters (Elena, Aetheris, Jake, future characters)
  ✅ NO JSON storage - pure relational data
  ✅ Easy to query: "WHERE category='fear'" instead of separate tables
  ✅ Easy to extend: Add new categories without schema changes
  ✅ NO AI hallucination risk - simple INSERT/UPDATE operations
  ✅ Simpler migration scripts - generic patterns, not character-specific
  ✅ Consistent patterns - same table structure for similar data types
  ✅ Reduced table count - 9 generalized vs 30+ specific tables
*/
