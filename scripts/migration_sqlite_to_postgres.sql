-- WhisperEngine SQLite to PostgreSQL Migration
-- Generated migration script

-- Create PostgreSQL schema

                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY, user_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    preferences TEXT DEFAULT '{}',
                    privacy_settings TEXT DEFAULT '{}'
                )
            ;

                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    bot_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_used TEXT,
                    response_time_ms INTEGER,
                    ai_model_used TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ;

                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ;

                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    fact_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.8,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT FALSE,
                    global_fact BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ;

                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    detected_emotion TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_adapted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ;

                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interaction_count INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ;

                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ;

                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT DEFAULT '{}'
                )
            ;

-- Create indexes

            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_entries_user_id ON memory_entries(user_id);
            CREATE INDEX IF NOT EXISTS idx_facts_user_id ON facts(user_id);
            CREATE INDEX IF NOT EXISTS idx_emotions_user_id ON emotions(user_id);
        

-- Migrate data

-- Migrate users (2 rows)
INSERT INTO users (user_id, username, display_name, created_at, last_seen, message_count, preferences, privacy_settings) VALUES ('test_user_1', 'testuser1', 'Test User One', '2025-09-14 16:52:21', '2025-09-14 16:52:21', 0, '{"theme": "dark"}', '{}');
INSERT INTO users (user_id, username, display_name, created_at, last_seen, message_count, preferences, privacy_settings) VALUES ('test_user_2', 'testuser2', 'Test User Two', '2025-09-14 16:52:21', '2025-09-14 16:52:21', 0, '{"theme": "light"}', '{}');

-- Migrate conversations (2 rows)
INSERT INTO conversations (id, user_id, channel_id, message_content, bot_response, timestamp, context_used, response_time_ms, ai_model_used) VALUES (1, 'test_user_1', 'general', 'Hello bot!', 'Hello! How can I help you?', '2025-09-14 16:52:21', NULL, NULL, 'local-model');
INSERT INTO conversations (id, user_id, channel_id, message_content, bot_response, timestamp, context_used, response_time_ms, ai_model_used) VALUES (2, 'test_user_2', 'general', 'What''s the weather?', 'I don''t have access to weather data.', '2025-09-14 16:52:21', NULL, NULL, 'local-model');

-- Migrate memory_entries (2 rows)
INSERT INTO memory_entries (id, user_id, memory_type, content, importance_score, created_at, last_accessed, access_count, tags, metadata) VALUES (1, 'test_user_1', 'preference', 'User prefers dark theme', 0.8, '2025-09-14 16:52:21', '2025-09-14 16:52:21', 0, '["ui", "preference"]', '{}');
INSERT INTO memory_entries (id, user_id, memory_type, content, importance_score, created_at, last_accessed, access_count, tags, metadata) VALUES (2, 'test_user_2', 'fact', 'User asked about weather', 0.6, '2025-09-14 16:52:21', '2025-09-14 16:52:21', 0, '["weather", "question"]', '{}');

-- Migrate facts (2 rows)
INSERT INTO facts (id, user_id, fact_type, subject, content, confidence_score, source, created_at, verified, global_fact) VALUES (1, 'test_user_1', 'personal', 'name', 'User''s name is Test User One', 0.9, NULL, '2025-09-14 16:52:21', 0, 0);
INSERT INTO facts (id, user_id, fact_type, subject, content, confidence_score, source, created_at, verified, global_fact) VALUES (2, NULL, 'general', 'ai', 'WhisperEngine is an AI Discord bot', 1.0, NULL, '2025-09-14 16:52:21', 0, 1);

-- Migrate emotions (1 rows)
INSERT INTO emotions (id, user_id, detected_emotion, confidence, context, timestamp, response_adapted) VALUES (1, 'test_user_1', 'curious', 0.7, 'Asking about bot capabilities', '2025-09-14 16:52:21', 0);

-- Migrate relationships (1 rows)
INSERT INTO relationships (id, user_id, relationship_type, strength, last_interaction, interaction_count, notes) VALUES (1, 'test_user_1', 'friendly', 0.8, '2025-09-14 16:52:21', 0, 'Polite and curious user');

-- Migrate system_settings (2 rows)
INSERT INTO system_settings (key, value, description, updated_at) VALUES ('last_backup', '2025-09-14T09:52:21.189396', 'Last database backup time', '2025-09-14 16:52:21');
INSERT INTO system_settings (key, value, description, updated_at) VALUES ('schema_version', '1.0', 'Current database schema version', '2025-09-14 16:52:21');

-- Migrate performance_metrics (2 rows)
INSERT INTO performance_metrics (id, metric_name, metric_value, timestamp, tags) VALUES (1, 'response_time_ms', 150.5, '2025-09-14 16:52:21', '{"endpoint": "chat"}');
INSERT INTO performance_metrics (id, metric_name, metric_value, timestamp, tags) VALUES (2, 'memory_usage_mb', 256.7, '2025-09-14 16:52:21', '{"component": "llm"}');