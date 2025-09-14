-- PostgreSQL Database Initialization Script
-- This script sets up the unified WhisperEngine database schema
-- Compatible with the desktop SQLite schema for seamless upgrades

-- Core users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    preferences TEXT DEFAULT '{}',
    privacy_settings TEXT DEFAULT '{}'
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_content TEXT NOT NULL,
    bot_response TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    context_used TEXT,
    response_time_ms INTEGER,
    ai_model_used TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Memory entries table
CREATE TABLE IF NOT EXISTS memory_entries (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance_score REAL DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Facts table
CREATE TABLE IF NOT EXISTS facts (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    fact_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.8,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    global_fact BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Emotions table
CREATE TABLE IF NOT EXISTS emotions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    detected_emotion TEXT NOT NULL,
    confidence REAL NOT NULL,
    context TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_adapted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Relationships table
CREATE TABLE IF NOT EXISTS relationships (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags TEXT DEFAULT '{}'
);

-- Performance indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_channel_id ON conversations(channel_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_user_id ON memory_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_type ON memory_entries(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_entries_importance ON memory_entries(importance_score);
CREATE INDEX IF NOT EXISTS idx_facts_user_id ON facts(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_type ON facts(fact_type);
CREATE INDEX IF NOT EXISTS idx_facts_global ON facts(global_fact);
CREATE INDEX IF NOT EXISTS idx_emotions_user_id ON emotions(user_id);
CREATE INDEX IF NOT EXISTS idx_emotions_timestamp ON emotions(timestamp);
CREATE INDEX IF NOT EXISTS idx_relationships_user_id ON relationships(user_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Auto-update timestamp function for system_settings
CREATE OR REPLACE FUNCTION update_system_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at on system_settings table
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_timestamp();

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'WhisperEngine unified PostgreSQL schema initialized successfully';
    RAISE NOTICE 'Schema compatible with SQLite desktop version for seamless upgrades';
END
$$;
