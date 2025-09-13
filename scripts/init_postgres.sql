-- PostgreSQL Database Initialization Script
-- This script sets up the database schema for user profiles

-- Create users table with all necessary fields
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    relationship_level TEXT DEFAULT 'acquaintance',
    current_emotion TEXT DEFAULT 'neutral',
    interaction_count INTEGER DEFAULT 0,
    first_interaction TIMESTAMP WITH TIME ZONE,
    last_interaction TIMESTAMP WITH TIME ZONE,
    escalation_count INTEGER DEFAULT 0,
    trust_indicators JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create emotion_history table for tracking emotional interactions
CREATE TABLE IF NOT EXISTS emotion_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    detected_emotion TEXT,
    confidence REAL,
    triggers JSONB DEFAULT '[]',
    intensity REAL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create interactions table for detailed interaction tracking
CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    interaction_type TEXT,
    content TEXT,
    response_quality REAL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_last_interaction ON users(last_interaction);
CREATE INDEX IF NOT EXISTS idx_emotion_history_user_id ON emotion_history(user_id);
CREATE INDEX IF NOT EXISTS idx_emotion_history_timestamp ON emotion_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at on users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL database schema initialized successfully';
END
$$;
