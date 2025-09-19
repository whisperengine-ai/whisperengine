-- PostgreSQL Schema for Hierarchical Memory Architecture
-- Initialize tables for Tier 2: Conversation Archive

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS hierarchical_conversations CASCADE;
DROP TABLE IF EXISTS hierarchical_summaries CASCADE;

-- Create conversations table for historical archive
CREATE TABLE hierarchical_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    -- Indexing for fast queries
    CONSTRAINT fk_hierarchical_conversations_user_id CHECK (user_id <> ''),
    CONSTRAINT fk_hierarchical_conversations_user_message CHECK (user_message <> ''),
    CONSTRAINT fk_hierarchical_conversations_bot_response CHECK (bot_response <> '')
);

-- Create summaries table for conversation summaries
CREATE TABLE hierarchical_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    summary_text TEXT NOT NULL,
    conversation_ids UUID[] NOT NULL,
    summary_type VARCHAR(50) DEFAULT 'conversation_summary',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT fk_hierarchical_summaries_user_id CHECK (user_id <> ''),
    CONSTRAINT fk_hierarchical_summaries_summary_text CHECK (summary_text <> '')
);

-- Create indexes for optimal query performance
CREATE INDEX idx_hierarchical_conversations_user_id ON hierarchical_conversations(user_id);
CREATE INDEX idx_hierarchical_conversations_timestamp ON hierarchical_conversations(timestamp DESC);
CREATE INDEX idx_hierarchical_conversations_user_timestamp ON hierarchical_conversations(user_id, timestamp DESC);

CREATE INDEX idx_hierarchical_summaries_user_id ON hierarchical_summaries(user_id);
CREATE INDEX idx_hierarchical_summaries_type ON hierarchical_summaries(summary_type);
CREATE INDEX idx_hierarchical_summaries_user_type ON hierarchical_summaries(user_id, summary_type);
CREATE INDEX idx_hierarchical_summaries_timestamp ON hierarchical_summaries(timestamp DESC);

-- Create GIN indexes for JSON metadata searches
CREATE INDEX idx_hierarchical_conversations_metadata ON hierarchical_conversations USING GIN(metadata);
CREATE INDEX idx_hierarchical_summaries_metadata ON hierarchical_summaries USING GIN(metadata);

-- Create text search indexes for efficient content searches
CREATE INDEX idx_hierarchical_conversations_user_message_trgm ON hierarchical_conversations USING GIN(user_message gin_trgm_ops);
CREATE INDEX idx_hierarchical_conversations_bot_response_trgm ON hierarchical_conversations USING GIN(bot_response gin_trgm_ops);
CREATE INDEX idx_hierarchical_summaries_text_trgm ON hierarchical_summaries USING GIN(summary_text gin_trgm_ops);

-- Grant permissions to bot user
GRANT ALL PRIVILEGES ON hierarchical_conversations TO bot_user;
GRANT ALL PRIVILEGES ON hierarchical_summaries TO bot_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bot_user;

-- Display setup confirmation
SELECT 'Hierarchical Memory PostgreSQL schema initialized successfully!' as status;