-- =====================================================
-- COMPREHENSIVE CDL SCHEMA - Clean RDBMS Design
-- WhisperEngine Character Definition Language
-- Version: 1.0 - October 2025
-- =====================================================

-- Core character entity (extends existing)
-- Keep existing characters table structure intact for compatibility
-- ALTER TABLE characters ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
-- ALTER TABLE characters ADD COLUMN IF NOT EXISTS character_tags TEXT[];
-- ALTER TABLE characters ADD COLUMN IF NOT EXISTS created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
-- ALTER TABLE characters ADD COLUMN IF NOT EXISTS updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Character metadata and versioning
CREATE TABLE IF NOT EXISTS character_metadata (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    character_tags TEXT[],
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author TEXT,
    notes TEXT,
    UNIQUE(character_id, version)
);

-- Physical and digital appearance
CREATE TABLE IF NOT EXISTS character_appearance (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- 'physical', 'digital', 'voice', 'presence'
    attribute VARCHAR(100) NOT NULL, -- 'height', 'build', 'hair_color', 'avatar_style', 'emoji_preference'
    value TEXT NOT NULL,
    description TEXT,
    UNIQUE(character_id, category, attribute)
);

-- Background and history
CREATE TABLE IF NOT EXISTS character_background (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- 'education', 'career', 'personal', 'cultural', 'mystical'
    period VARCHAR(100), -- 'childhood', 'university', 'early_career', 'current'
    title TEXT,
    description TEXT NOT NULL,
    date_range TEXT, -- '2010-2014', 'childhood', 'ongoing'
    importance_level INTEGER DEFAULT 5, -- 1-10 scale
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Character relationships and connections
CREATE TABLE IF NOT EXISTS character_relationships (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    related_entity VARCHAR(200) NOT NULL, -- Character name, entity, or concept
    relationship_type VARCHAR(50) NOT NULL, -- 'colleague', 'mentor', 'rival', 'family', 'mystical_connection'
    relationship_strength INTEGER DEFAULT 5, -- 1-10 scale
    description TEXT,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'past', 'complicated'
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Key memories and experiences
CREATE TABLE IF NOT EXISTS character_memories (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL, -- 'formative', 'traumatic', 'joyful', 'professional', 'mystical'
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    emotional_impact INTEGER DEFAULT 5, -- 1-10 scale
    time_period TEXT, -- 'childhood', '2019', 'last_year'
    importance_level INTEGER DEFAULT 5, -- 1-10 scale
    triggers TEXT[], -- Words or topics that might bring up this memory
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Abilities and skills (professional, mystical, or special)
CREATE TABLE IF NOT EXISTS character_abilities (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- 'professional', 'mystical', 'digital', 'social', 'physical'
    ability_name VARCHAR(100) NOT NULL,
    proficiency_level INTEGER DEFAULT 5, -- 1-10 scale
    description TEXT,
    development_method TEXT, -- How they learned/acquired this ability
    usage_frequency VARCHAR(20) DEFAULT 'regular', -- 'daily', 'regular', 'occasional', 'rare'
    UNIQUE(character_id, category, ability_name)
);

-- Communication patterns and preferences
CREATE TABLE IF NOT EXISTS character_communication_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL, -- 'emoji', 'humor', 'technical', 'emotional', 'cultural'
    pattern_name VARCHAR(100) NOT NULL,
    pattern_value TEXT NOT NULL, -- The actual pattern, preference, or behavior
    context VARCHAR(100), -- When this pattern applies
    frequency VARCHAR(20) DEFAULT 'regular', -- 'always', 'often', 'sometimes', 'rarely'
    description TEXT,
    UNIQUE(character_id, pattern_type, pattern_name)
);

-- Behavioral triggers and responses
CREATE TABLE IF NOT EXISTS character_behavioral_triggers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL, -- 'topic', 'emotion', 'situation', 'word', 'concept'
    trigger_value VARCHAR(200) NOT NULL, -- The actual trigger
    response_type VARCHAR(50) NOT NULL, -- 'enthusiasm', 'expertise', 'caution', 'excitement', 'memory'
    response_description TEXT NOT NULL,
    intensity_level INTEGER DEFAULT 5, -- 1-10 scale
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Essence and core identity (for mystical/fantasy characters)
CREATE TABLE IF NOT EXISTS character_essence (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    essence_type VARCHAR(50) NOT NULL, -- 'nature', 'existence_method', 'core_power', 'fundamental_truth'
    essence_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    manifestation TEXT, -- How this essence shows up in interactions
    power_level INTEGER, -- For mystical abilities
    UNIQUE(character_id, essence_type, essence_name)
);

-- Custom instructions and overrides
CREATE TABLE IF NOT EXISTS character_instructions (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    instruction_type VARCHAR(50) NOT NULL, -- 'introduction', 'override', 'special_behavior', 'constraint'
    priority INTEGER DEFAULT 5, -- 1-10, higher = more important
    instruction_text TEXT NOT NULL,
    context TEXT, -- When this instruction applies
    active BOOLEAN DEFAULT true,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES for performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_character_appearance_category ON character_appearance(character_id, category);
CREATE INDEX IF NOT EXISTS idx_character_background_category ON character_background(character_id, category);
CREATE INDEX IF NOT EXISTS idx_character_relationships_type ON character_relationships(character_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_character_memories_type ON character_memories(character_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_character_abilities_category ON character_abilities(character_id, category);
CREATE INDEX IF NOT EXISTS idx_character_patterns_type ON character_communication_patterns(character_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_character_triggers_type ON character_behavioral_triggers(character_id, trigger_type);
CREATE INDEX IF NOT EXISTS idx_character_essence_type ON character_essence(character_id, essence_type);
CREATE INDEX IF NOT EXISTS idx_character_instructions_type ON character_instructions(character_id, instruction_type);

-- =====================================================
-- FUNCTIONS for data management
-- =====================================================

-- Function to update character updated_date
CREATE OR REPLACE FUNCTION update_character_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE characters SET updated_date = CURRENT_TIMESTAMP WHERE id = NEW.character_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist (for idempotency)
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_metadata ON character_metadata;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_appearance ON character_appearance;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_background ON character_background;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_relationships ON character_relationships;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_memories ON character_memories;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_abilities ON character_abilities;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_patterns ON character_communication_patterns;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_triggers ON character_behavioral_triggers;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_essence ON character_essence;
DROP TRIGGER IF EXISTS trigger_update_character_timestamp_instructions ON character_instructions;

-- Triggers to auto-update character timestamp when any related data changes
CREATE TRIGGER trigger_update_character_timestamp_metadata
    AFTER INSERT OR UPDATE OR DELETE ON character_metadata
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_appearance
    AFTER INSERT OR UPDATE OR DELETE ON character_appearance
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_background
    AFTER INSERT OR UPDATE OR DELETE ON character_background
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_relationships
    AFTER INSERT OR UPDATE OR DELETE ON character_relationships
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_memories
    AFTER INSERT OR UPDATE OR DELETE ON character_memories
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_abilities
    AFTER INSERT OR UPDATE OR DELETE ON character_abilities
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_patterns
    AFTER INSERT OR UPDATE OR DELETE ON character_communication_patterns
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_triggers
    AFTER INSERT OR UPDATE OR DELETE ON character_behavioral_triggers
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_essence
    AFTER INSERT OR UPDATE OR DELETE ON character_essence
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

CREATE TRIGGER trigger_update_character_timestamp_instructions
    AFTER INSERT OR UPDATE OR DELETE ON character_instructions
    FOR EACH ROW EXECUTE FUNCTION update_character_timestamp();

-- =====================================================
-- MIGRATION DATA - Add metadata for existing characters
-- =====================================================

-- Add metadata entries for all existing characters
INSERT INTO character_metadata (character_id, version, character_tags, author, notes)
SELECT 
    id, 
    1, 
    ARRAY['legacy_import'], 
    'WhisperEngine Migration',
    'Migrated from JSON during comprehensive schema upgrade'
FROM characters
ON CONFLICT (character_id, version) DO NOTHING;

-- Add timestamp columns to existing characters table if they don't exist
ALTER TABLE characters ADD COLUMN IF NOT EXISTS created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE characters ADD COLUMN IF NOT EXISTS updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing records to have proper timestamps
UPDATE characters SET 
    created_date = CURRENT_TIMESTAMP,
    updated_date = CURRENT_TIMESTAMP 
WHERE created_date IS NULL OR updated_date IS NULL;

COMMIT;