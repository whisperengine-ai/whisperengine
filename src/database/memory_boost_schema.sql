"""
Sprint 2 MemoryBoost: PostgreSQL Schema Setup

Database schema enhancements for memory effectiveness tracking,
relationship intelligence, and optimization logging.

Execute this script to create the necessary tables for Sprint 2 MemoryBoost.
"""

-- Memory effectiveness tracking table
CREATE TABLE IF NOT EXISTS memory_effectiveness (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    quality_score FLOAT NOT NULL,
    relevance_score FLOAT NOT NULL,
    freshness_score FLOAT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effectiveness_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT memory_effectiveness_unique UNIQUE(memory_id, user_id, bot_name)
);

-- Create indexes for memory effectiveness
CREATE INDEX IF NOT EXISTS idx_memory_effectiveness_user_bot ON memory_effectiveness(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_memory_effectiveness_quality ON memory_effectiveness(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_effectiveness_usage ON memory_effectiveness(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_memory_effectiveness_accessed ON memory_effectiveness(last_accessed DESC);

-- Relationship intelligence tracking table
CREATE TABLE IF NOT EXISTS relationship_intelligence (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    relationship_depth VARCHAR(50) NOT NULL CHECK (relationship_depth IN ('acquaintance', 'friend', 'close', 'intimate')),
    depth_score FLOAT NOT NULL CHECK (depth_score >= 0 AND depth_score <= 100),
    interaction_frequency FLOAT NOT NULL DEFAULT 0,
    conversation_quality FLOAT NOT NULL DEFAULT 0,
    emotional_connection FLOAT NOT NULL DEFAULT 0,
    trust_level FLOAT NOT NULL DEFAULT 0,
    shared_experiences FLOAT NOT NULL DEFAULT 0,
    time_investment FLOAT NOT NULL DEFAULT 0,
    progression_velocity FLOAT NOT NULL DEFAULT 0,
    last_interaction TIMESTAMP,
    total_interactions INTEGER DEFAULT 0,
    quality_interactions INTEGER DEFAULT 0,
    relationship_age_days INTEGER DEFAULT 0,
    intelligence_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one relationship record per user-bot pair
    CONSTRAINT relationship_intelligence_unique UNIQUE(user_id, bot_name)
);

-- Create indexes for relationship intelligence
CREATE INDEX IF NOT EXISTS idx_relationship_intelligence_user_bot ON relationship_intelligence(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_relationship_intelligence_depth ON relationship_intelligence(relationship_depth);
CREATE INDEX IF NOT EXISTS idx_relationship_intelligence_score ON relationship_intelligence(depth_score DESC);
CREATE INDEX IF NOT EXISTS idx_relationship_intelligence_frequency ON relationship_intelligence(interaction_frequency DESC);
CREATE INDEX IF NOT EXISTS idx_relationship_intelligence_last_interaction ON relationship_intelligence(last_interaction DESC);

-- Memory optimization logging table
CREATE TABLE IF NOT EXISTS memory_optimization_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    optimization_type VARCHAR(100) NOT NULL,
    before_score FLOAT,
    after_score FLOAT,
    improvement_percentage FLOAT GENERATED ALWAYS AS (
        CASE 
            WHEN before_score > 0 THEN ((after_score - before_score) / before_score) * 100 
            ELSE 0 
        END
    ) STORED,
    optimization_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for optimization logs
CREATE INDEX IF NOT EXISTS idx_memory_optimization_user_bot ON memory_optimization_logs(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_memory_optimization_type ON memory_optimization_logs(optimization_type);
CREATE INDEX IF NOT EXISTS idx_memory_optimization_improvement ON memory_optimization_logs(improvement_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_memory_optimization_created ON memory_optimization_logs(created_at DESC);

-- Memory tier transition tracking (for analytics)
CREATE TABLE IF NOT EXISTS memory_tier_transitions (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    from_tier VARCHAR(50) NOT NULL,
    to_tier VARCHAR(50) NOT NULL,
    transition_reason VARCHAR(200),
    quality_score_at_transition FLOAT,
    transition_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tier transitions
CREATE INDEX IF NOT EXISTS idx_memory_tier_transitions_memory ON memory_tier_transitions(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_tier_transitions_user_bot ON memory_tier_transitions(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_memory_tier_transitions_from_to ON memory_tier_transitions(from_tier, to_tier);
CREATE INDEX IF NOT EXISTS idx_memory_tier_transitions_created ON memory_tier_transitions(created_at DESC);

-- Update timestamp triggers for automatic updated_at maintenance
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
DROP TRIGGER IF EXISTS update_memory_effectiveness_updated_at ON memory_effectiveness;
CREATE TRIGGER update_memory_effectiveness_updated_at 
    BEFORE UPDATE ON memory_effectiveness 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_relationship_intelligence_updated_at ON relationship_intelligence;
CREATE TRIGGER update_relationship_intelligence_updated_at 
    BEFORE UPDATE ON relationship_intelligence 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_effectiveness TO whisperengine_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON relationship_intelligence TO whisperengine_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_optimization_logs TO whisperengine_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_tier_transitions TO whisperengine_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO whisperengine_user;

-- Create views for common queries
CREATE OR REPLACE VIEW relationship_intelligence_summary AS
SELECT 
    user_id,
    bot_name,
    relationship_depth,
    depth_score,
    interaction_frequency,
    total_interactions,
    quality_interactions,
    ROUND((quality_interactions::FLOAT / NULLIF(total_interactions, 0)) * 100, 2) as quality_interaction_percentage,
    emotional_connection,
    trust_level,
    relationship_age_days,
    last_interaction,
    updated_at
FROM relationship_intelligence
ORDER BY depth_score DESC, last_interaction DESC;

CREATE OR REPLACE VIEW memory_effectiveness_summary AS
SELECT 
    user_id,
    bot_name,
    COUNT(*) as total_memories,
    ROUND(AVG(quality_score), 2) as avg_quality_score,
    ROUND(AVG(relevance_score), 2) as avg_relevance_score,
    ROUND(AVG(freshness_score), 2) as avg_freshness_score,
    SUM(usage_count) as total_usage_count,
    MAX(last_accessed) as most_recent_access
FROM memory_effectiveness
GROUP BY user_id, bot_name
ORDER BY avg_quality_score DESC;

-- Sprint 2 MemoryBoost schema setup complete
-- Tables created:
-- - memory_effectiveness: Track memory quality and usage patterns
-- - relationship_intelligence: Comprehensive relationship tracking and analysis
-- - memory_optimization_logs: Record optimization attempts and improvements
-- - memory_tier_transitions: Track memory tier changes over time
--
-- Views created:
-- - relationship_intelligence_summary: Quick relationship overview
-- - memory_effectiveness_summary: Memory quality aggregates
--
-- Performance optimizations:
-- - Strategic indexes for common query patterns
-- - Automatic updated_at timestamp maintenance
-- - Constraint validation for data integrity
-- - Generated columns for computed metrics