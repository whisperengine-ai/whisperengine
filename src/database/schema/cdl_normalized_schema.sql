-- CDL Normalized Database Schema v1.0
-- Hybrid approach: Normalized core fields + JSON for extensibility

-- Core character table with stable, frequently queried fields
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(50) DEFAULT '1.0',
    active BOOLEAN DEFAULT true
);

-- Identity table - core character identity (normalized for queries)
CREATE TABLE character_identity (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    occupation VARCHAR(500),
    location VARCHAR(500),
    description TEXT,
    -- JSON for extensible identity fields (communication_style, etc.)
    extended_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personality table - Big Five traits (normalized for analysis)
CREATE TABLE character_personality (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    openness DECIMAL(3,2) CHECK (openness >= 0 AND openness <= 1),
    conscientiousness DECIMAL(3,2) CHECK (conscientiousness >= 0 AND conscientiousness <= 1),
    extraversion DECIMAL(3,2) CHECK (extraversion >= 0 AND extraversion <= 1),
    agreeableness DECIMAL(3,2) CHECK (agreeableness >= 0 AND agreeableness <= 1),
    neuroticism DECIMAL(3,2) CHECK (neuroticism >= 0 AND neuroticism <= 1),
    -- JSON for custom traits, values, beliefs, etc.
    custom_traits JSONB DEFAULT '{}',
    values JSONB DEFAULT '[]',
    core_beliefs JSONB DEFAULT '[]',
    dreams JSONB DEFAULT '[]',
    fears JSONB DEFAULT '[]',
    quirks JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Communication table - core communication patterns
CREATE TABLE character_communication (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    response_length TEXT DEFAULT 'moderate',  -- Changed from VARCHAR(50) to TEXT to handle long instructions
    communication_style TEXT DEFAULT 'adaptive',  -- Changed from VARCHAR(100) to TEXT for flexibility
    -- JSON for complex nested communication data
    typical_responses JSONB DEFAULT '{}',
    emotional_expressions JSONB DEFAULT '{}',
    message_pattern_triggers JSONB DEFAULT '{}',
    conversation_flow_guidance JSONB DEFAULT '{}',
    ai_identity_handling JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Backstory table - character history and background
CREATE TABLE character_backstory (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    -- JSON for flexible backstory structure
    childhood JSONB DEFAULT '{}',
    education JSONB DEFAULT '{}',
    career_history JSONB DEFAULT '[]',
    key_events JSONB DEFAULT '[]',
    relationships JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Current life table - present state and activities
CREATE TABLE character_current_life (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    -- JSON for flexible current state
    daily_routine JSONB DEFAULT '{}',
    current_projects JSONB DEFAULT '[]',
    goals JSONB DEFAULT '[]',
    challenges JSONB DEFAULT '[]',
    social_circle JSONB DEFAULT '[]',
    interests JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Speech patterns table - language and vocabulary
CREATE TABLE character_speech_patterns (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    -- JSON for vocabulary and language patterns
    vocabulary JSONB DEFAULT '{"preferred_words": [], "avoided_words": []}',
    language_patterns JSONB DEFAULT '{}',
    favorite_phrases JSONB DEFAULT '[]',
    speech_quirks JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personal knowledge table - extensible personal information
CREATE TABLE character_personal_knowledge (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    -- JSON for completely flexible personal data
    relationships JSONB DEFAULT '{}',
    career JSONB DEFAULT '{}',
    hobbies JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    memories JSONB DEFAULT '[]',
    secrets JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata table - system information
CREATE TABLE character_metadata (
    character_id INTEGER PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    created_by VARCHAR(255) DEFAULT 'system',
    source_file VARCHAR(500),
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    schema_version VARCHAR(50) DEFAULT '1.0',
    -- JSON for extensible metadata
    extended_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_characters_name ON characters(name);
CREATE INDEX idx_characters_active ON characters(active);
CREATE INDEX idx_character_identity_name ON character_identity(name);
CREATE INDEX idx_character_identity_occupation ON character_identity(occupation);

-- JSON indexes for frequent queries
CREATE INDEX idx_personality_custom_traits ON character_personality USING GIN (custom_traits);
CREATE INDEX idx_communication_typical_responses ON character_communication USING GIN (typical_responses);
CREATE INDEX idx_personal_knowledge_relationships ON character_personal_knowledge USING GIN (relationships);

-- Update triggers to maintain updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_identity_updated_at BEFORE UPDATE ON character_identity 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_personality_updated_at BEFORE UPDATE ON character_personality 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_communication_updated_at BEFORE UPDATE ON character_communication 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_backstory_updated_at BEFORE UPDATE ON character_backstory 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_current_life_updated_at BEFORE UPDATE ON character_current_life 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_speech_patterns_updated_at BEFORE UPDATE ON character_speech_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_personal_knowledge_updated_at BEFORE UPDATE ON character_personal_knowledge 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_character_metadata_updated_at BEFORE UPDATE ON character_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Schema version tracking
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_versions (version, description) 
VALUES ('1.0', 'Initial CDL normalized schema with hybrid JSON approach');