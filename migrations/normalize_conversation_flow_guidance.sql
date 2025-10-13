-- Migration: Normalize conversation_flow_guidance JSON into proper RDBMS tables
-- This replaces JSON text fields with clean relational structure for web UI editing

-- 1. Character Conversation Modes (replaces character-specific top-level keys)
CREATE TABLE IF NOT EXISTS character_conversation_modes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    mode_name VARCHAR(100) NOT NULL,  -- e.g., 'technical_education', 'romantic_interest'
    energy_level VARCHAR(50),         -- e.g., 'thoughtful', 'enthusiastic'
    approach TEXT,                    -- Main approach description
    transition_style TEXT,            -- How to transition to this mode
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, mode_name)
);

-- 2. Mode Guidance Items (replaces 'avoid' and 'encourage' arrays)
CREATE TABLE IF NOT EXISTS character_mode_guidance (
    id SERIAL PRIMARY KEY,
    mode_id INTEGER NOT NULL REFERENCES character_conversation_modes(id) ON DELETE CASCADE,
    guidance_type VARCHAR(20) NOT NULL CHECK (guidance_type IN ('avoid', 'encourage')),
    guidance_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Mode Examples (replaces 'examples' arrays)
CREATE TABLE IF NOT EXISTS character_mode_examples (
    id SERIAL PRIMARY KEY,
    mode_id INTEGER NOT NULL REFERENCES character_conversation_modes(id) ON DELETE CASCADE,
    example_text TEXT NOT NULL,
    example_type VARCHAR(50),  -- e.g., 'response', 'question', 'transition'
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. General Conversation Settings (replaces 'general' section)
CREATE TABLE IF NOT EXISTS character_general_conversation (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    default_energy VARCHAR(50),
    conversation_style TEXT,
    transition_approach TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

-- 5. Response Style Settings (replaces 'response_style' section)
CREATE TABLE IF NOT EXISTS character_response_style (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id)
);

-- 6. Response Style Items (replaces core_principles, formatting_rules arrays)
CREATE TABLE IF NOT EXISTS character_response_style_items (
    id SERIAL PRIMARY KEY,
    response_style_id INTEGER NOT NULL REFERENCES character_response_style(id) ON DELETE CASCADE,
    item_type VARCHAR(50) NOT NULL,  -- 'core_principle', 'formatting_rule', 'character_adaptation'
    item_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Response Patterns (replaces response_patterns from general)
CREATE TABLE IF NOT EXISTS character_response_patterns (
    id SERIAL PRIMARY KEY,
    general_conversation_id INTEGER NOT NULL REFERENCES character_general_conversation(id) ON DELETE CASCADE,
    pattern_name VARCHAR(100),
    pattern_description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_modes_character ON character_conversation_modes(character_id);
CREATE INDEX IF NOT EXISTS idx_mode_guidance_mode ON character_mode_guidance(mode_id);
CREATE INDEX IF NOT EXISTS idx_mode_examples_mode ON character_mode_examples(mode_id);
CREATE INDEX IF NOT EXISTS idx_response_style_items_style ON character_response_style_items(response_style_id);
CREATE INDEX IF NOT EXISTS idx_response_patterns_general ON character_response_patterns(general_conversation_id);

-- Add comments for web UI development
COMMENT ON TABLE character_conversation_modes IS 'Character-specific conversation modes like technical_education, romantic_interest - replaces JSON conversation_flow_guidance';
COMMENT ON TABLE character_mode_guidance IS 'What to avoid/encourage in each conversation mode - clean arrays for web forms';
COMMENT ON TABLE character_mode_examples IS 'Example responses for each conversation mode - editable via web UI';
COMMENT ON TABLE character_general_conversation IS 'General conversation settings per character - replaces general JSON section';
COMMENT ON TABLE character_response_style IS 'Character response style configuration - replaces response_style JSON section';
COMMENT ON TABLE character_response_style_items IS 'Core principles and formatting rules - clean list for web editing';