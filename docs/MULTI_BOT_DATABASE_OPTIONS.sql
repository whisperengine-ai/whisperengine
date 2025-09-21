-- ===================================================================
-- WhisperEngine Multi-Bot Database Schema Options
-- ===================================================================

-- ===================================================================
-- OPTION 1: USER-CENTRIC (CURRENT - RECOMMENDED)
-- ===================================================================
-- Same user_id shares memory across all bots
-- Elena and Marcus both remember the same user's conversations

-- Current tables (no changes needed):
-- users(user_id, username, ...)
-- conversations(user_id, message_content, bot_response, ...)
-- memory_entries(user_id, content, ...)

-- Example data:
-- User 123456 talks to Elena: conversations(user_id=123456, bot_response="As a marine biologist...")
-- Same user talks to Marcus: conversations(user_id=123456, bot_response="From an AI perspective...")
-- Both conversations are linked to the same user!

-- ===================================================================
-- OPTION 2: BOT-SCOPED ISOLATION
-- ===================================================================
-- Add bot_id to separate data per bot instance
-- Each bot has completely independent user memory

-- Modified schema (requires migration):

-- Enhanced users table with bot scoping
CREATE TABLE IF NOT EXISTS users_v2 (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,              -- Discord user ID
    bot_id TEXT NOT NULL,               -- Discord bot ID (Elena's bot ID, Marcus's bot ID)
    username TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    preferences TEXT DEFAULT '{}',
    privacy_settings TEXT DEFAULT '{}',
    UNIQUE(user_id, bot_id)             -- Composite key: user + bot
);

-- Enhanced conversations table
CREATE TABLE IF NOT EXISTS conversations_v2 (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,               -- Which bot handled this conversation
    channel_id TEXT NOT NULL,
    message_content TEXT NOT NULL,
    bot_response TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    context_used TEXT,
    response_time_ms INTEGER,
    ai_model_used TEXT,
    FOREIGN KEY (user_id, bot_id) REFERENCES users_v2 (user_id, bot_id) ON DELETE CASCADE
);

-- Enhanced memory_entries table
CREATE TABLE IF NOT EXISTS memory_entries_v2 (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,               -- Which bot stored this memory
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance_score REAL DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (user_id, bot_id) REFERENCES users_v2 (user_id, bot_id) ON DELETE CASCADE
);

-- Bot identity table
CREATE TABLE IF NOT EXISTS bot_instances (
    bot_id TEXT PRIMARY KEY,            -- Discord bot ID
    bot_name TEXT NOT NULL,             -- Elena, Marcus, etc.
    character_file TEXT,                -- Path to character JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Enhanced indexes for bot-scoped queries
CREATE INDEX IF NOT EXISTS idx_users_v2_user_bot ON users_v2(user_id, bot_id);
CREATE INDEX IF NOT EXISTS idx_conversations_v2_user_bot ON conversations_v2(user_id, bot_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_v2_user_bot ON memory_entries_v2(user_id, bot_id);

-- ===================================================================
-- OPTION 3: HYBRID APPROACH
-- ===================================================================
-- Keep current schema but add optional bot context

-- Add bot_context column to existing tables (backward compatible)
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS bot_id TEXT;
ALTER TABLE memory_entries ADD COLUMN IF NOT EXISTS bot_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_bot_interaction TEXT;

-- Optional bot_instances table for tracking
CREATE TABLE IF NOT EXISTS bot_instances (
    bot_id TEXT PRIMARY KEY,
    bot_name TEXT NOT NULL,
    character_file TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Shared memory view (cross-bot memories)
CREATE VIEW IF NOT EXISTS shared_memories AS
SELECT * FROM memory_entries 
WHERE bot_id IS NULL OR bot_id = '';

-- Bot-specific memory view
CREATE VIEW IF NOT EXISTS bot_memories AS
SELECT * FROM memory_entries 
WHERE bot_id IS NOT NULL AND bot_id != '';

-- ===================================================================
-- COMPARISON: Query Examples
-- ===================================================================

-- OPTION 1 (Current): Get user's conversation history
-- SELECT * FROM conversations WHERE user_id = '123456' ORDER BY timestamp;
-- Result: All conversations across all bots

-- OPTION 2 (Bot-scoped): Get user's conversation history with specific bot
-- SELECT * FROM conversations_v2 WHERE user_id = '123456' AND bot_id = 'elena_bot_id' ORDER BY timestamp;
-- Result: Only conversations with Elena

-- OPTION 3 (Hybrid): Get shared + bot-specific memories
-- SELECT * FROM memory_entries WHERE user_id = '123456' AND (bot_id IS NULL OR bot_id = 'elena_bot_id');
-- Result: Shared memories + Elena-specific memories