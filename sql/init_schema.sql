-- WhisperEngine PostgreSQL Schema - Dev Only
-- Simple schema with only essential tables for vector-native architecture

BEGIN;

-- User Profiles: Fast structured user data with preferences
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    relationship_level INTEGER DEFAULT 1,
    current_emotion VARCHAR(50) DEFAULT 'neutral',
    interaction_count INTEGER DEFAULT 0,
    first_interaction TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emotion_history JSONB DEFAULT '[]'::jsonb,
    escalation_count INTEGER DEFAULT 0,
    trust_indicators JSONB DEFAULT '[]'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_interaction
    ON user_profiles(last_interaction);

CREATE INDEX IF NOT EXISTS idx_user_profiles_relationship_level
    ON user_profiles(relationship_level);

-- GIN index for JSONB preferences (fast preference lookups)
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences_gin
    ON user_profiles USING GIN (preferences);

COMMIT;-- CDL Database Schema Migration
-- WhisperEngine Character Definition Language (CDL) PostgreSQL Schema
-- Migrates from static JSON files to dynamic database-backed character management

-- Characters table - Core character information
CREATE TABLE cdl_characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    normalized_name VARCHAR(100) NOT NULL UNIQUE, -- For bot name matching
    bot_name VARCHAR(100), -- Discord bot name if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    
    -- Identity fields
    occupation VARCHAR(200),
    location VARCHAR(200),
    age_range VARCHAR(50),
    background TEXT,
    description TEXT,
    
    -- Character archetype and AI behavior
    character_archetype VARCHAR(50) DEFAULT 'real-world', -- 'real-world', 'fantasy', 'narrative-ai'
    allow_full_roleplay_immersion BOOLEAN DEFAULT false,
    
    -- Metadata
    created_by VARCHAR(100),
    notes TEXT
);

-- Personality traits table - Big Five and custom traits
CREATE TABLE cdl_personality_traits (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    trait_category VARCHAR(50) NOT NULL, -- 'big_five', 'custom', 'emotional'
    trait_name VARCHAR(100) NOT NULL,
    trait_value DECIMAL(3,2), -- 0.00 to 1.00 for quantitative traits
    trait_description TEXT,
    intensity VARCHAR(20), -- 'low', 'medium', 'high', 'very_high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(character_id, trait_category, trait_name)
);

-- Communication styles table
CREATE TABLE cdl_communication_styles (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    style_category VARCHAR(50) NOT NULL, -- 'speaking_style', 'interaction_preferences', 'modes'
    style_name VARCHAR(100) NOT NULL,
    style_value TEXT, -- JSON or text value
    description TEXT,
    priority INTEGER DEFAULT 0, -- For ordering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(character_id, style_category, style_name)
);

-- Values and beliefs table
CREATE TABLE cdl_values (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    value_category VARCHAR(50) NOT NULL, -- 'core_values', 'beliefs', 'motivations'
    value_name VARCHAR(100) NOT NULL,
    value_description TEXT NOT NULL,
    importance_level VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Anti-patterns and behavioral guidelines
CREATE TABLE cdl_anti_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    pattern_category VARCHAR(50) NOT NULL, -- 'avoid_behaviors', 'conversation_limits', 'personality_constraints'
    pattern_name VARCHAR(100) NOT NULL,
    pattern_description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personal knowledge and background
CREATE TABLE cdl_personal_knowledge (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    knowledge_category VARCHAR(50) NOT NULL, -- 'family', 'career', 'relationships', 'experiences', 'preferences'
    knowledge_type VARCHAR(50) NOT NULL, -- 'fact', 'preference', 'experience', 'relationship', 'skill'
    knowledge_key VARCHAR(100) NOT NULL,
    knowledge_value TEXT NOT NULL,
    knowledge_context TEXT, -- Additional context or details
    confidence_level DECIMAL(3,2) DEFAULT 1.00, -- 0.00 to 1.00
    is_public BOOLEAN DEFAULT true, -- Whether this knowledge can be shared
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(character_id, knowledge_category, knowledge_key)
);

-- Character evolution history - Track changes over time
CREATE TABLE cdl_evolution_history (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL, -- 'trait_update', 'knowledge_added', 'style_modified', 'major_revision'
    change_description TEXT NOT NULL,
    old_value JSONB, -- Previous state (JSON)
    new_value JSONB, -- New state (JSON)
    change_reason TEXT, -- Why the change was made
    changed_by VARCHAR(100), -- Who made the change
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Performance metadata
    performance_metrics JSONB, -- Related performance data that triggered change
    validation_status VARCHAR(20) DEFAULT 'pending' -- 'pending', 'validated', 'rejected'
);

-- Interaction modes and context switching
CREATE TABLE cdl_interaction_modes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES cdl_characters(id) ON DELETE CASCADE,
    mode_name VARCHAR(50) NOT NULL, -- 'creative', 'technical', 'educational', 'casual'
    mode_description TEXT,
    trigger_keywords TEXT[], -- Array of keywords that activate this mode
    response_guidelines TEXT, -- How to respond in this mode
    avoid_patterns TEXT[], -- What to avoid in this mode
    is_default BOOLEAN DEFAULT false, -- Whether this is the default mode
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(character_id, mode_name)
);

-- Indexes for performance
CREATE INDEX idx_cdl_characters_normalized_name ON cdl_characters(normalized_name);
CREATE INDEX idx_cdl_characters_bot_name ON cdl_characters(bot_name);
CREATE INDEX idx_cdl_personality_traits_character_category ON cdl_personality_traits(character_id, trait_category);
CREATE INDEX idx_cdl_communication_styles_character_category ON cdl_communication_styles(character_id, style_category);
CREATE INDEX idx_cdl_values_character_category ON cdl_values(character_id, value_category);
CREATE INDEX idx_cdl_personal_knowledge_character_category ON cdl_personal_knowledge(character_id, knowledge_category);
CREATE INDEX idx_cdl_evolution_history_character_timestamp ON cdl_evolution_history(character_id, change_timestamp DESC);
CREATE INDEX idx_cdl_interaction_modes_character ON cdl_interaction_modes(character_id);

-- Updated timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to characters table
CREATE TRIGGER update_cdl_characters_updated_at 
    BEFORE UPDATE ON cdl_characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE cdl_characters IS 'Core character definitions and metadata';
COMMENT ON TABLE cdl_personality_traits IS 'Big Five personality traits and custom character traits';
COMMENT ON TABLE cdl_communication_styles IS 'Speaking styles, interaction preferences, and communication modes';
COMMENT ON TABLE cdl_values IS 'Core values, beliefs, and motivational drivers';
COMMENT ON TABLE cdl_anti_patterns IS 'Behavioral guidelines and patterns to avoid';
COMMENT ON TABLE cdl_personal_knowledge IS 'Character background, experiences, and personal information';
COMMENT ON TABLE cdl_evolution_history IS 'Track character changes and evolution over time';
COMMENT ON TABLE cdl_interaction_modes IS 'Context-aware interaction modes and switching logic';

-- Sample view for complete character profile
CREATE VIEW cdl_character_profiles AS
SELECT 
    c.id,
    c.name,
    c.normalized_name,
    c.bot_name,
    c.occupation,
    c.location,
    c.background,
    c.character_archetype,
    c.allow_full_roleplay_immersion,
    c.created_at,
    c.updated_at,
    c.version,
    
    -- Aggregate personality traits
    (SELECT jsonb_object_agg(pt.trait_name, 
        jsonb_build_object(
            'value', pt.trait_value,
            'description', pt.trait_description,
            'intensity', pt.intensity
        )
    ) FROM cdl_personality_traits pt WHERE pt.character_id = c.id) as personality_traits,
    
    -- Aggregate communication styles
    (SELECT jsonb_object_agg(cs.style_name, 
        jsonb_build_object(
            'value', cs.style_value,
            'description', cs.description,
            'priority', cs.priority
        )
    ) FROM cdl_communication_styles cs WHERE cs.character_id = c.id) as communication_styles,
    
    -- Aggregate values
    (SELECT jsonb_object_agg(v.value_name, 
        jsonb_build_object(
            'description', v.value_description,
            'importance', v.importance_level
        )
    ) FROM cdl_values v WHERE v.character_id = c.id) as values_and_beliefs

FROM cdl_characters c
WHERE c.is_active = true;

COMMENT ON VIEW cdl_character_profiles IS 'Complete character profiles with aggregated traits, styles, and values';
-- Compatibility VIEW for web UI (maps cdl_characters to expected character_identity format)
CREATE OR REPLACE VIEW character_identity AS
SELECT 
    id,
    name,
    normalized_name,
    bot_name,
    occupation,
    location,
    age_range,
    background,
    description,
    character_archetype AS archetype,
    allow_full_roleplay_immersion AS allow_full_roleplay,
    is_active,
    version,
    created_at,
    updated_at,
    created_by,
    notes,
    NULL::jsonb AS cdl_data  -- Placeholder for future JSONB aggregation
FROM cdl_characters;

-- Backward compatibility VIEW for CDL graph code (maps cdl_characters to old characters table)
CREATE OR REPLACE VIEW characters AS
SELECT 
    id,
    name,
    normalized_name,
    bot_name,
    occupation,
    location,
    age_range,
    background,
    description,
    character_archetype,
    allow_full_roleplay_immersion,
    is_active,
    version,
    created_at,
    updated_at
FROM cdl_characters;

COMMENT ON VIEW characters IS 'Backward compatibility view mapping cdl_characters to old characters table schema';

-- ============================================================================
-- UNIVERSAL IDENTITY SYSTEM (Cross-Platform User Management)
-- ============================================================================
-- Creates tables for cross-platform user identity management
-- Users can interact via Discord, Web UI, or future platforms with consistent identity

-- Universal Users Table
CREATE TABLE IF NOT EXISTS universal_users (
    universal_id VARCHAR(255) PRIMARY KEY,
    primary_username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT DEFAULT '{}',
    privacy_settings TEXT DEFAULT '{}'
);

-- Platform Identities Table
CREATE TABLE IF NOT EXISTS platform_identities (
    id SERIAL PRIMARY KEY,
    universal_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, platform_user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_platform_identities_universal_id ON platform_identities(universal_id);
CREATE INDEX IF NOT EXISTS idx_platform_identities_platform_user ON platform_identities(platform, platform_user_id);
CREATE INDEX IF NOT EXISTS idx_universal_users_username ON universal_users(primary_username);
CREATE INDEX IF NOT EXISTS idx_universal_users_email ON universal_users(email);

-- Comments for documentation
COMMENT ON TABLE universal_users IS 'Universal user identities across all platforms';
COMMENT ON TABLE platform_identities IS 'Platform-specific identity mappings to universal users';
COMMENT ON COLUMN universal_users.universal_id IS 'Universal unique identifier (weu_* format)';
COMMENT ON COLUMN platform_identities.platform IS 'Platform name (discord, web_ui, etc.)';
COMMENT ON COLUMN platform_identities.platform_user_id IS 'Platform-specific user ID';

-- ============================================================================
-- RELATIONSHIP EVOLUTION SYSTEM (Dynamic Relationship Scoring)
-- ============================================================================
-- Tracks dynamic trust/affection/attunement scores for user-bot relationships
-- Part of Sprint 3 RelationshipTuner system

-- Relationship Scores Table (Current state)
CREATE TABLE IF NOT EXISTS relationship_scores (
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    trust DECIMAL(5,4) NOT NULL DEFAULT 0.5000,
    affection DECIMAL(5,4) NOT NULL DEFAULT 0.4000,
    attunement DECIMAL(5,4) NOT NULL DEFAULT 0.3000,
    interaction_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (user_id, bot_name),
    
    -- Constraints for 0-1 range
    CHECK (trust >= 0.0 AND trust <= 1.0),
    CHECK (affection >= 0.0 AND affection <= 1.0),
    CHECK (attunement >= 0.0 AND attunement <= 1.0),
    CHECK (interaction_count >= 0)
);

-- Relationship Events Table (History)
CREATE TABLE IF NOT EXISTS relationship_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    trust_delta DECIMAL(5,4),
    affection_delta DECIMAL(5,4),
    attunement_delta DECIMAL(5,4),
    trust_value DECIMAL(5,4),
    affection_value DECIMAL(5,4),
    attunement_value DECIMAL(5,4),
    conversation_quality VARCHAR(20),
    emotion_variance DECIMAL(5,4),
    update_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Foreign key to relationship_scores
    FOREIGN KEY (user_id, bot_name) 
        REFERENCES relationship_scores(user_id, bot_name)
        ON DELETE CASCADE
);

-- Trust Recovery State Table
CREATE TABLE IF NOT EXISTS trust_recovery_state (
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    recovery_stage VARCHAR(20) NOT NULL,
    initial_trust DECIMAL(5,4) NOT NULL,
    current_trust DECIMAL(5,4) NOT NULL,
    target_trust DECIMAL(5,4) NOT NULL,
    progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    recovery_actions_taken TEXT[],
    started_at TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    estimated_completion TIMESTAMP,
    
    PRIMARY KEY (user_id, bot_name, started_at),
    
    -- Foreign key to relationship_scores
    FOREIGN KEY (user_id, bot_name) 
        REFERENCES relationship_scores(user_id, bot_name)
        ON DELETE CASCADE,
    
    -- Constraints
    CHECK (initial_trust >= 0.0 AND initial_trust <= 1.0),
    CHECK (current_trust >= 0.0 AND current_trust <= 1.0),
    CHECK (target_trust >= 0.0 AND target_trust <= 1.0),
    CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0)
);

-- Indexes for relationship_scores
CREATE INDEX IF NOT EXISTS idx_relationship_scores_user ON relationship_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_relationship_scores_bot ON relationship_scores(bot_name);
CREATE INDEX IF NOT EXISTS idx_relationship_scores_trust ON relationship_scores(trust) WHERE trust < 0.4;

-- Indexes for relationship_events
CREATE INDEX IF NOT EXISTS idx_relationship_events_user_bot ON relationship_events(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_relationship_events_type ON relationship_events(event_type);
CREATE INDEX IF NOT EXISTS idx_relationship_events_timestamp ON relationship_events(created_at DESC);

-- Indexes for trust_recovery_state
CREATE INDEX IF NOT EXISTS idx_trust_recovery_user_bot ON trust_recovery_state(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_trust_recovery_stage ON trust_recovery_state(recovery_stage) WHERE recovery_stage IN ('active', 'recovering');

-- Comments for documentation
COMMENT ON TABLE relationship_scores IS 'Current relationship scores for each user-bot pair (trust, affection, attunement)';
COMMENT ON TABLE relationship_events IS 'Historical record of relationship score changes and updates';
COMMENT ON TABLE trust_recovery_state IS 'Active trust recovery tracking for damaged relationships';

