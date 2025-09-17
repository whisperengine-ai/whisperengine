-- 0001_baseline.sql
-- Baseline schema snapshot for WhisperEngine
-- Generated as initial migration to allow forward evolution.
-- Apply: idempotent where possible. Future changes should use ALTER statements.

BEGIN;

-- Track applied migrations
CREATE TABLE IF NOT EXISTS schema_versions (
    component VARCHAR(100) NOT NULL DEFAULT 'core',
    version INT NOT NULL,
    checksum VARCHAR(128) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    PRIMARY KEY (component, version)
);

-- Emotional Intelligence (existing inline creation) - ensure table references won't fail later
CREATE TABLE IF NOT EXISTS user_emotional_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_assessments INTEGER DEFAULT 0,
    prediction_accuracy FLOAT DEFAULT 0.0,
    intervention_success_rate FLOAT DEFAULT 0.0,
    crisis_prevention_count INTEGER DEFAULT 0,
    user_satisfaction_score FLOAT DEFAULT 0.0,
    average_response_time FLOAT DEFAULT 0.0,
    primary_emotional_patterns JSONB DEFAULT '[]',
    stress_triggers JSONB DEFAULT '[]',
    emotional_recovery_patterns JSONB DEFAULT '{}',
    last_assessment_time TIMESTAMP,
    next_assessment_time TIMESTAMP,
    phase_status VARCHAR(50) DEFAULT 'monitoring'
);

-- Memory Importance Statistics
CREATE TABLE IF NOT EXISTS user_memory_statistics (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_memories_scored INTEGER DEFAULT 0,
    average_importance_score FLOAT DEFAULT 0.5,
    median_importance_score FLOAT DEFAULT 0.5,
    max_importance_score FLOAT DEFAULT 0.0,
    min_importance_score FLOAT DEFAULT 1.0,
    core_memory_count INTEGER DEFAULT 0,
    emotional_intensity_weight FLOAT DEFAULT 0.30,
    personal_relevance_weight FLOAT DEFAULT 0.25,
    recency_weight FLOAT DEFAULT 0.15,
    access_frequency_weight FLOAT DEFAULT 0.15,
    uniqueness_weight FLOAT DEFAULT 0.10,
    relationship_milestone_weight FLOAT DEFAULT 0.05,
    pattern_learning_confidence FLOAT DEFAULT 0.0,
    total_pattern_adjustments INTEGER DEFAULT 0,
    last_pattern_update TIMESTAMP,
    factor_averages JSONB DEFAULT '{}',
    memory_type_preferences JSONB DEFAULT '{}',
    temporal_patterns JSONB DEFAULT '{}'
);

-- Memory Importance Patterns
CREATE TABLE IF NOT EXISTS user_memory_importance_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_multiplier FLOAT DEFAULT 1.0,
    confidence_score FLOAT DEFAULT 0.0,
    frequency_count INTEGER DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    pattern_keywords JSONB DEFAULT '[]',
    emotional_associations JSONB DEFAULT '[]',
    context_requirements JSONB DEFAULT '{}',
    user_feedback_score FLOAT DEFAULT 0.0,
    memory_recall_frequency FLOAT DEFAULT 0.0,
    pattern_metadata JSONB DEFAULT '{}',
    CONSTRAINT fk_user_memory_statistics FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_pattern UNIQUE (user_id, pattern_type, pattern_name)
);

-- Emotional Trigger Patterns
CREATE TABLE IF NOT EXISTS user_emotional_trigger_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL,
    trigger_content VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_emotion VARCHAR(100),
    emotion_intensity_avg FLOAT DEFAULT 0.5,
    emotion_confidence FLOAT DEFAULT 0.0,
    trigger_frequency INTEGER DEFAULT 1,
    prediction_accuracy FLOAT DEFAULT 0.0,
    last_triggered TIMESTAMP,
    context_requirements JSONB DEFAULT '{}',
    related_topics JSONB DEFAULT '[]',
    memory_impact_score FLOAT DEFAULT 0.5,
    user_response_patterns JSONB DEFAULT '{}',
    effective_ai_responses JSONB DEFAULT '[]',
    CONSTRAINT fk_user_memory_statistics_trigger FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE
);

-- User Interest Patterns
CREATE TABLE IF NOT EXISTS user_interest_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interest_strength FLOAT DEFAULT 0.5,
    interest_trend VARCHAR(50) DEFAULT 'stable',
    frequency_score FLOAT DEFAULT 0.0,
    first_mentioned TIMESTAMP,
    last_mentioned TIMESTAMP,
    peak_interest_period TIMESTAMP,
    mention_count INTEGER DEFAULT 1,
    memory_importance_boost FLOAT DEFAULT 0.0,
    personal_significance FLOAT DEFAULT 0.5,
    related_emotions JSONB DEFAULT '[]',
    common_contexts JSONB DEFAULT '[]',
    associated_topics JSONB DEFAULT '[]',
    confidence_level FLOAT DEFAULT 0.0,
    topic_metadata JSONB DEFAULT '{}',
    CONSTRAINT fk_user_memory_statistics_interest FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_topic UNIQUE (user_id, topic_name)
);

-- Memory Connection Patterns
CREATE TABLE IF NOT EXISTS user_memory_connection_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    connection_type VARCHAR(100) NOT NULL,
    pattern_signature VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    average_connection_strength FLOAT DEFAULT 0.5,
    pattern_frequency INTEGER DEFAULT 1,
    prediction_success_rate FLOAT DEFAULT 0.0,
    typical_themes JSONB DEFAULT '[]',
    emotional_associations JSONB DEFAULT '[]',
    temporal_characteristics JSONB DEFAULT '{}',
    user_engagement_score FLOAT DEFAULT 0.0,
    memory_recall_enhancement FLOAT DEFAULT 0.0,
    optimization_metadata JSONB DEFAULT '{}',
    last_successful_use TIMESTAMP,
    CONSTRAINT fk_user_memory_statistics_connection FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE
);

-- Indexes (idempotent)
CREATE INDEX IF NOT EXISTS idx_user_memory_statistics_user_id ON user_memory_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_importance_patterns_user_id ON user_memory_importance_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_emotional_trigger_patterns_user_id ON user_emotional_trigger_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_interest_patterns_user_id ON user_interest_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_connection_patterns_user_id ON user_memory_connection_patterns(user_id);

COMMIT;
