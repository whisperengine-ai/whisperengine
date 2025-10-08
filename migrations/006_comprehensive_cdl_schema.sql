-- Migration 006: Comprehensive CDL Schema Extension
-- Captures ALL fidelity and control from CDL JSON files in RDBMS design
-- Generic structure to support different character needs

-- ===============================================
-- CONVERSATION CONTROL & RESPONSE GUIDELINES
-- ===============================================

-- Response length guidelines and formatting rules
CREATE TABLE character_response_guidelines (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    guideline_type VARCHAR(100) NOT NULL, -- 'response_length', 'formatting_rule', 'tone_directive'
    guideline_name VARCHAR(200), -- descriptive name
    guideline_content TEXT NOT NULL, -- the actual guideline text
    priority INTEGER DEFAULT 50, -- 1-100, higher = more important
    context VARCHAR(100), -- when this applies: 'discord', 'general', 'technical_mode'
    is_critical BOOLEAN DEFAULT FALSE, -- critical guidelines that must be followed
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation flow guidance and patterns
CREATE TABLE character_conversation_flows (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    flow_type VARCHAR(100) NOT NULL, -- 'marine_science_discussion', 'personal_connection', 'general'
    flow_name VARCHAR(200),
    energy_level VARCHAR(50), -- 'passionate', 'warm', 'technical'
    approach_description TEXT, -- how to handle this conversation type
    transition_style TEXT, -- how to transition in/out
    priority INTEGER DEFAULT 50,
    context TEXT -- additional context
);

-- Things to avoid/encourage in conversation flows
CREATE TABLE character_conversation_directives (
    id SERIAL PRIMARY KEY,
    conversation_flow_id INTEGER REFERENCES character_conversation_flows(id) ON DELETE CASCADE,
    directive_type VARCHAR(50) NOT NULL, -- 'avoid', 'encourage', 'example'
    directive_content TEXT NOT NULL,
    order_sequence INTEGER -- for ordering examples
);

-- ===============================================
-- MESSAGE PATTERNS & TRIGGERS
-- ===============================================

-- Message pattern triggers for different response modes
CREATE TABLE character_message_triggers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trigger_category VARCHAR(100) NOT NULL, -- 'marine_science_discussion', 'personal_connection', 'brevity_mode'
    trigger_type VARCHAR(50) NOT NULL, -- 'keyword', 'phrase', 'pattern'
    trigger_value TEXT NOT NULL, -- the actual keyword/phrase/pattern
    response_mode VARCHAR(100), -- what mode this triggers
    priority INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE
);

-- Response patterns and modes (technical, creative, brief, etc.)
CREATE TABLE character_response_modes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    mode_name VARCHAR(100) NOT NULL, -- 'technical', 'creative', 'brief', 'marine_science'
    mode_description TEXT,
    response_style TEXT, -- how to respond in this mode
    length_guideline TEXT, -- specific length rules for this mode
    tone_adjustment TEXT, -- tone changes for this mode
    conflict_resolution_priority INTEGER, -- if multiple modes conflict
    examples TEXT -- example responses in this mode
);

-- ===============================================
-- SPEECH & COMMUNICATION PATTERNS
-- ===============================================

-- Emoji usage patterns and digital communication
CREATE TABLE character_emoji_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    pattern_category VARCHAR(100) NOT NULL, -- 'excitement_level', 'topic_specific', 'response_types'
    pattern_name VARCHAR(100) NOT NULL, -- 'high_excitement', 'ocean_marine_life', 'greeting'
    emoji_sequence TEXT, -- the emojis to use
    usage_context TEXT, -- when to use these
    frequency VARCHAR(50), -- 'high', 'medium', 'low'
    example_usage TEXT -- example of how it's used
);

-- Speech patterns and vocabulary preferences
CREATE TABLE character_speech_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL, -- 'preferred_words', 'avoided_words', 'sentence_structure', 'favorite_phrases'
    pattern_value TEXT NOT NULL, -- the actual word/phrase/pattern
    usage_frequency VARCHAR(50), -- how often to use
    context VARCHAR(100), -- when to use
    priority INTEGER DEFAULT 50
);

-- ===============================================
-- AI IDENTITY & ROLEPLAY HANDLING
-- ===============================================

-- AI identity handling scenarios and responses
CREATE TABLE character_ai_scenarios (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    scenario_type VARCHAR(100) NOT NULL, -- 'physical_meetups', 'shared_activities', 'ai_identity_questions'
    scenario_name VARCHAR(200),
    trigger_phrases TEXT, -- phrases that activate this scenario
    response_pattern VARCHAR(100), -- 'three_tier_ethics_response', 'honest_disclosure'
    tier_1_response TEXT, -- enthusiasm response
    tier_2_response TEXT, -- clarification response
    tier_3_response TEXT, -- alternative response
    example_usage TEXT
);

-- ===============================================
-- CULTURAL & PERSONALITY EXPRESSIONS
-- ===============================================

-- Cultural expressions and language patterns
CREATE TABLE character_cultural_expressions (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    expression_type VARCHAR(100) NOT NULL, -- 'spanish_expressions', 'cultural_terms', 'family_references'
    expression_value TEXT NOT NULL, -- the actual expression
    meaning TEXT, -- what it means
    usage_context TEXT, -- when to use it
    emotional_context VARCHAR(50), -- 'excitement', 'affection', 'concern'
    frequency VARCHAR(50) -- how often to use
);

-- Voice and speaking characteristics
CREATE TABLE character_voice_traits (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trait_type VARCHAR(100) NOT NULL, -- 'tone', 'pace', 'volume', 'accent', 'vocabulary_level'
    trait_value TEXT NOT NULL, -- the description of this trait
    situational_context TEXT, -- when this trait is prominent
    examples TEXT -- examples of this trait in action
);

-- ===============================================
-- EMOTIONAL INTELLIGENCE & TRIGGERS
-- ===============================================

-- Emotional triggers and responses
CREATE TABLE character_emotional_triggers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    trigger_type VARCHAR(100) NOT NULL, -- 'enthusiasm_triggers', 'concern_triggers', 'support_methods'
    trigger_category VARCHAR(100), -- grouping related triggers
    trigger_content TEXT NOT NULL, -- what triggers this emotion
    emotional_response TEXT, -- how the character responds
    response_intensity VARCHAR(50), -- 'low', 'medium', 'high'
    response_examples TEXT -- example responses
);

-- ===============================================
-- PROFESSIONAL & DOMAIN EXPERTISE
-- ===============================================

-- Domain-specific knowledge and expertise areas
CREATE TABLE character_expertise_domains (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    domain_name VARCHAR(200) NOT NULL, -- 'marine_biology', 'coral_restoration', 'game_development'
    expertise_level VARCHAR(50), -- 'expert', 'advanced', 'intermediate'
    domain_description TEXT,
    key_concepts TEXT, -- important concepts in this domain
    teaching_approach TEXT, -- how character shares this knowledge
    passion_level INTEGER, -- 1-100 how passionate about this
    examples TEXT -- examples of expertise in action
);

-- ===============================================
-- INDEXES FOR PERFORMANCE
-- ===============================================

-- Performance indexes for common queries
CREATE INDEX idx_response_guidelines_character ON character_response_guidelines(character_id, guideline_type);
CREATE INDEX idx_conversation_flows_character ON character_conversation_flows(character_id, flow_type);
CREATE INDEX idx_message_triggers_character ON character_message_triggers(character_id, trigger_category);
CREATE INDEX idx_response_modes_character ON character_response_modes(character_id, mode_name);
CREATE INDEX idx_emoji_patterns_character ON character_emoji_patterns(character_id, pattern_category);
CREATE INDEX idx_speech_patterns_character ON character_speech_patterns(character_id, pattern_type);
CREATE INDEX idx_ai_scenarios_character ON character_ai_scenarios(character_id, scenario_type);
CREATE INDEX idx_cultural_expressions_character ON character_cultural_expressions(character_id, expression_type);
CREATE INDEX idx_voice_traits_character ON character_voice_traits(character_id, trait_type);
CREATE INDEX idx_emotional_triggers_character ON character_emotional_triggers(character_id, trigger_type);
CREATE INDEX idx_expertise_domains_character ON character_expertise_domains(character_id, domain_name);

-- ===============================================
-- COMMENTS FOR DOCUMENTATION
-- ===============================================

COMMENT ON TABLE character_response_guidelines IS 'Response length, formatting rules, and critical directives for character behavior';
COMMENT ON TABLE character_conversation_flows IS 'Conversation flow guidance for different interaction types';
COMMENT ON TABLE character_conversation_directives IS 'Specific things to avoid/encourage in each conversation flow';
COMMENT ON TABLE character_message_triggers IS 'Keywords and phrases that trigger specific response modes';
COMMENT ON TABLE character_response_modes IS 'Different response modes (technical, creative, brief) and their guidelines';
COMMENT ON TABLE character_emoji_patterns IS 'Emoji usage patterns for digital communication';
COMMENT ON TABLE character_speech_patterns IS 'Speech patterns, vocabulary preferences, and language style';
COMMENT ON TABLE character_ai_scenarios IS 'AI identity handling scenarios and tier-based responses';
COMMENT ON TABLE character_cultural_expressions IS 'Cultural expressions and language-specific terms';
COMMENT ON TABLE character_voice_traits IS 'Voice characteristics and speaking patterns';
COMMENT ON TABLE character_emotional_triggers IS 'Emotional triggers and corresponding responses';
COMMENT ON TABLE character_expertise_domains IS 'Professional expertise domains and knowledge areas';