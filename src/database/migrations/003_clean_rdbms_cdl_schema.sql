-- Clean RDBMS CDL Schema - Pure Relational Approach
-- WhisperEngine Character Definition Language (CDL) 
-- No JSON/JSONB - Strict normalized relational schema

-- Drop existing CDL and character tables to start fresh
DROP TABLE IF EXISTS cdl_anti_patterns CASCADE;
DROP TABLE IF EXISTS cdl_communication_styles CASCADE;
DROP TABLE IF EXISTS cdl_personal_knowledge CASCADE;
DROP TABLE IF EXISTS cdl_personality_traits CASCADE;
DROP TABLE IF EXISTS cdl_values CASCADE;
DROP TABLE IF EXISTS cdl_evolution_history CASCADE;
DROP TABLE IF EXISTS cdl_interaction_modes CASCADE;
DROP TABLE IF EXISTS cdl_character_profiles CASCADE;
DROP TABLE IF EXISTS cdl_characters CASCADE;
DROP TABLE IF EXISTS character_communication CASCADE;
DROP TABLE IF EXISTS character_identity CASCADE;
DROP TABLE IF EXISTS character_personality CASCADE;
DROP TABLE IF EXISTS characters CASCADE;

-- Core Characters Table
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,                    -- Full name: "Elena Rodriguez"
    normalized_name VARCHAR(100) NOT NULL UNIQUE, -- Bot identifier: "elena"
    occupation VARCHAR(200),                       -- "Marine Biologist & Research Scientist"
    description TEXT,                              -- Character description
    archetype VARCHAR(50) DEFAULT 'real-world',   -- 'real-world', 'fantasy', 'narrative-ai'
    allow_full_roleplay BOOLEAN DEFAULT false,    -- Roleplay immersion setting
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Big Five Personality Traits (what CDL AI integration uses most)
CREATE TABLE personality_traits (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trait_name VARCHAR(50) NOT NULL,              -- 'openness', 'conscientiousness', etc.
    trait_value DECIMAL(3,2),                     -- 0.00 to 1.00
    intensity VARCHAR(20),                        -- 'low', 'medium', 'high', 'very_high'
    description TEXT,
    UNIQUE(character_id, trait_name)
);

-- Communication Style (core fields used by CDL AI integration)
CREATE TABLE communication_styles (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    engagement_level DECIMAL(3,2),               -- 0.00 to 1.00
    formality VARCHAR(100),                       -- "Informal and friendly"
    emotional_expression DECIMAL(3,2),           -- 0.00 to 1.00
    response_length VARCHAR(50),                  -- "medium", "long", etc.
    conversation_flow_guidance TEXT,              -- Basic conversation guidelines
    ai_identity_handling TEXT                     -- How to handle AI identity questions
);

-- Core Values and Beliefs (simplified)
CREATE TABLE character_values (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    value_key VARCHAR(100) NOT NULL,             -- "fear_1", "core_value_1", etc.
    value_description TEXT NOT NULL,
    importance_level VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    category VARCHAR(50),                         -- 'fear', 'core_value', 'belief', etc.
    UNIQUE(character_id, value_key)
);

-- Create indexes for performance
CREATE INDEX idx_characters_normalized_name ON characters(normalized_name);
CREATE INDEX idx_characters_active ON characters(is_active);
CREATE INDEX idx_personality_traits_character ON personality_traits(character_id);
CREATE INDEX idx_communication_styles_character ON communication_styles(character_id);
CREATE INDEX idx_character_values_character ON character_values(character_id);

-- Insert Elena Rodriguez as test data
INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay) 
VALUES (
    'Elena Rodriguez',
    'elena',
    'Marine Biologist & Research Scientist',
    'Elena has the weathered hands of someone who spends time in labs and tide pools, with an energetic presence that lights up when discussing marine conservation. Her Mexican-American heritage instilled a deep respect for nature and community that drives her environmental work.',
    'real-world',
    false
);

-- Insert Elena's Big Five personality traits
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
SELECT c.id, 'openness', 0.90, 'very_high', 'Extremely open to new experiences and ideas'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'conscientiousness', 0.70, 'high', 'Highly organized and detail-oriented'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'extraversion', 0.60, 'high', 'Energetic and outgoing, especially about her work'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'agreeableness', 0.80, 'very_high', 'Warm, compassionate, and collaborative'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'neuroticism', 0.40, 'medium', 'Generally stable with occasional environmental anxiety'
FROM characters c WHERE c.normalized_name = 'elena';

-- Insert Elena's communication style
INSERT INTO communication_styles (character_id, engagement_level, formality, emotional_expression, response_length, conversation_flow_guidance, ai_identity_handling)
SELECT 
    c.id,
    0.70,
    'Informal and friendly',
    0.60,
    'medium',
    'Enthusiastic about marine science topics. Uses oceanic metaphors naturally. Switches to Spanish when excited.',
    'Honest about AI nature when directly asked, but maintains character authenticity.'
FROM characters c WHERE c.normalized_name = 'elena';

-- Insert Elena's core values
INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
SELECT c.id, 'fear_1', 'Coral reef collapse and ocean acidification', 'high', 'fear'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'core_value_1', 'Environmental conservation and marine protection', 'critical', 'core_value'
FROM characters c WHERE c.normalized_name = 'elena'
UNION ALL
SELECT c.id, 'core_value_2', 'Scientific integrity and evidence-based research', 'critical', 'core_value'
FROM characters c WHERE c.normalized_name = 'elena';

-- Create a view for easy character data retrieval (what the CDL manager will use)
CREATE VIEW character_profiles AS
SELECT 
    c.id,
    c.name,
    c.normalized_name,
    c.occupation,
    c.description,
    c.archetype,
    c.allow_full_roleplay,
    c.is_active,
    cs.engagement_level,
    cs.formality,
    cs.emotional_expression,
    cs.response_length,
    cs.conversation_flow_guidance,
    cs.ai_identity_handling
FROM characters c
LEFT JOIN communication_styles cs ON c.id = cs.character_id
WHERE c.is_active = true;

COMMENT ON TABLE characters IS 'Core character information - minimal fields needed by CDL AI integration';
COMMENT ON TABLE personality_traits IS 'Big Five personality traits used for character responses';
COMMENT ON TABLE communication_styles IS 'Communication preferences and style guidelines';
COMMENT ON TABLE character_values IS 'Core values, beliefs, and fears that drive character behavior';
COMMENT ON VIEW character_profiles IS 'Consolidated view for easy character data retrieval';