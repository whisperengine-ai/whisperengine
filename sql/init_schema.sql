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

COMMIT;