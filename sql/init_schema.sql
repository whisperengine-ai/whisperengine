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

