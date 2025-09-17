-- Memory Importance User Statistics Persistence Schema
-- Sprint 2: Memory Importance Pattern Database Design
-- =================================================

-- This schema captures user-specific memory importance patterns
-- to enable the AI to learn what types of memories matter most to each user

-- ===== CORE USER MEMORY STATISTICS =====

-- User Memory Statistics: Overall memory importance patterns for each user
CREATE TABLE IF NOT EXISTS user_memory_statistics (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Memory volume and quality metrics
    total_memories_scored INTEGER DEFAULT 0,
    average_importance_score FLOAT DEFAULT 0.5,
    median_importance_score FLOAT DEFAULT 0.5,
    max_importance_score FLOAT DEFAULT 0.0,
    min_importance_score FLOAT DEFAULT 1.0,
    core_memory_count INTEGER DEFAULT 0,
    
    -- User-specific importance factor preferences
    emotional_intensity_weight FLOAT DEFAULT 0.30,
    personal_relevance_weight FLOAT DEFAULT 0.25, 
    recency_weight FLOAT DEFAULT 0.15,
    access_frequency_weight FLOAT DEFAULT 0.15,
    uniqueness_weight FLOAT DEFAULT 0.10,
    relationship_milestone_weight FLOAT DEFAULT 0.05,
    
    -- Learning statistics
    pattern_learning_confidence FLOAT DEFAULT 0.0,
    total_pattern_adjustments INTEGER DEFAULT 0,
    last_pattern_update TIMESTAMP,
    
    -- JSON fields for complex data
    factor_averages JSONB DEFAULT '{}',
    memory_type_preferences JSONB DEFAULT '{}',
    temporal_patterns JSONB DEFAULT '{}'
);

-- ===== MEMORY IMPORTANCE PATTERNS =====

-- User Memory Importance Patterns: Learned patterns about what makes memories important to specific users
CREATE TABLE IF NOT EXISTS user_memory_importance_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL, -- 'emotional_trigger', 'topic_interest', 'personal_anchor', 'temporal_pattern'
    pattern_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Pattern scoring and confidence
    importance_multiplier FLOAT DEFAULT 1.0, -- How much this pattern boosts memory importance
    confidence_score FLOAT DEFAULT 0.0, -- How confident we are in this pattern
    frequency_count INTEGER DEFAULT 1, -- How often this pattern has been observed
    success_rate FLOAT DEFAULT 0.0, -- How often memories with this pattern prove important
    
    -- Pattern content and triggers
    pattern_keywords JSONB DEFAULT '[]', -- Keywords that trigger this pattern
    emotional_associations JSONB DEFAULT '[]', -- Associated emotions
    context_requirements JSONB DEFAULT '{}', -- Required context for pattern activation
    
    -- User interaction feedback
    user_feedback_score FLOAT DEFAULT 0.0, -- Derived from user engagement
    memory_recall_frequency FLOAT DEFAULT 0.0, -- How often memories with this pattern are recalled
    
    -- Pattern metadata
    pattern_metadata JSONB DEFAULT '{}',
    
    CONSTRAINT fk_user_memory_statistics FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_pattern UNIQUE (user_id, pattern_type, pattern_name)
);

-- ===== EMOTIONAL TRIGGER PATTERNS =====

-- User Emotional Trigger Patterns: What topics/content trigger emotional responses for each user
CREATE TABLE IF NOT EXISTS user_emotional_trigger_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL, -- 'topic', 'keyword', 'concept', 'situation'
    trigger_content VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Emotional response data
    triggered_emotion VARCHAR(100), -- The emotion this typically triggers
    emotion_intensity_avg FLOAT DEFAULT 0.5, -- Average intensity of triggered emotion
    emotion_confidence FLOAT DEFAULT 0.0, -- Confidence in emotion prediction
    
    -- Pattern frequency and reliability
    trigger_frequency INTEGER DEFAULT 1, -- How often this trigger has been observed
    prediction_accuracy FLOAT DEFAULT 0.0, -- How accurate predictions for this trigger are
    last_triggered TIMESTAMP,
    
    -- Context and conditions
    context_requirements JSONB DEFAULT '{}', -- Context needed for trigger activation
    related_topics JSONB DEFAULT '[]', -- Topics associated with this trigger
    memory_impact_score FLOAT DEFAULT 0.5, -- How much this trigger affects memory importance
    
    -- User adaptation data
    user_response_patterns JSONB DEFAULT '{}', -- How user typically responds
    effective_ai_responses JSONB DEFAULT '[]', -- AI responses that worked well
    
    CONSTRAINT fk_user_memory_statistics_trigger FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE
);

-- ===== USER INTEREST AND TOPIC PATTERNS =====

-- User Interest Patterns: Tracks what topics and interests are most important to each user
CREATE TABLE IF NOT EXISTS user_interest_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Interest strength and evolution
    interest_strength FLOAT DEFAULT 0.5, -- How interested the user is (0.0-1.0)
    interest_trend VARCHAR(50) DEFAULT 'stable', -- 'increasing', 'decreasing', 'stable', 'new'
    frequency_score FLOAT DEFAULT 0.0, -- How often user mentions this topic
    
    -- Temporal patterns
    first_mentioned TIMESTAMP,
    last_mentioned TIMESTAMP,
    peak_interest_period TIMESTAMP,
    mention_count INTEGER DEFAULT 1,
    
    -- Relationship to memory importance
    memory_importance_boost FLOAT DEFAULT 0.0, -- How much this topic boosts memory importance
    personal_significance FLOAT DEFAULT 0.5, -- How personally significant this topic is
    
    -- Context and associations
    related_emotions JSONB DEFAULT '[]', -- Emotions associated with this topic
    common_contexts JSONB DEFAULT '[]', -- Contexts where this topic appears
    associated_topics JSONB DEFAULT '[]', -- Other topics that appear with this one
    
    -- Learning metadata
    confidence_level FLOAT DEFAULT 0.0, -- Confidence in interest assessment
    topic_metadata JSONB DEFAULT '{}',
    
    CONSTRAINT fk_user_memory_statistics_interest FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_topic UNIQUE (user_id, topic_name)
);

-- ===== MEMORY CONNECTION PATTERNS =====

-- User Memory Connection Patterns: How user's memories connect and relate to each other
CREATE TABLE IF NOT EXISTS user_memory_connection_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    connection_type VARCHAR(100) NOT NULL, -- 'thematic_similarity', 'emotional_resonance', 'temporal_sequence'
    pattern_signature VARCHAR(500) NOT NULL, -- Unique identifier for this connection pattern
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Connection strength and reliability
    average_connection_strength FLOAT DEFAULT 0.5,
    pattern_frequency INTEGER DEFAULT 1, -- How often this connection pattern occurs
    prediction_success_rate FLOAT DEFAULT 0.0, -- How often this pattern predicts successful connections
    
    -- Pattern characteristics
    typical_themes JSONB DEFAULT '[]', -- Common themes in this connection pattern
    emotional_associations JSONB DEFAULT '[]', -- Emotions that facilitate this connection
    temporal_characteristics JSONB DEFAULT '{}', -- Time-based characteristics of connections
    
    -- User interaction data
    user_engagement_score FLOAT DEFAULT 0.0, -- How much user engages with these connections
    memory_recall_enhancement FLOAT DEFAULT 0.0, -- How much this pattern improves memory recall
    
    -- Pattern optimization
    optimization_metadata JSONB DEFAULT '{}',
    last_successful_use TIMESTAMP,
    
    CONSTRAINT fk_user_memory_statistics_connection FOREIGN KEY (user_id) REFERENCES user_memory_statistics(user_id) ON DELETE CASCADE
);

-- ===== PERFORMANCE INDEXES =====

-- Performance indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_user_memory_statistics_user_id ON user_memory_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_statistics_updated_at ON user_memory_statistics(updated_at);

CREATE INDEX IF NOT EXISTS idx_memory_importance_patterns_user_id ON user_memory_importance_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_importance_patterns_type ON user_memory_importance_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_memory_importance_patterns_confidence ON user_memory_importance_patterns(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_emotional_trigger_patterns_user_id ON user_emotional_trigger_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_emotional_trigger_patterns_emotion ON user_emotional_trigger_patterns(triggered_emotion);
CREATE INDEX IF NOT EXISTS idx_emotional_trigger_patterns_frequency ON user_emotional_trigger_patterns(trigger_frequency DESC);

CREATE INDEX IF NOT EXISTS idx_interest_patterns_user_id ON user_interest_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_interest_patterns_strength ON user_interest_patterns(interest_strength DESC);
CREATE INDEX IF NOT EXISTS idx_interest_patterns_topic ON user_interest_patterns(topic_name);

CREATE INDEX IF NOT EXISTS idx_connection_patterns_user_id ON user_memory_connection_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_connection_patterns_type ON user_memory_connection_patterns(connection_type);
CREATE INDEX IF NOT EXISTS idx_connection_patterns_success ON user_memory_connection_patterns(prediction_success_rate DESC);

-- ===== SAMPLE DATA COMMENTS =====

/*
Sample Usage Patterns:

1. User Memory Statistics:
   - Track overall memory importance patterns for each user
   - Learn user-specific factor weights (some users value emotions more, others value recency)
   - Store aggregate statistics for memory network health

2. Memory Importance Patterns:
   - "emotional_trigger" patterns: Topics that trigger strong emotions get higher importance
   - "topic_interest" patterns: User's personal interests boost memory importance  
   - "personal_anchor" patterns: Things tied to identity/relationships get priority
   - "temporal_pattern" patterns: Time-based importance (e.g., weekend memories matter more)

3. Emotional Trigger Patterns:
   - Learn what topics consistently trigger specific emotions
   - Track prediction accuracy to improve emotional intelligence
   - Store effective AI responses for similar situations

4. Interest Patterns:
   - Track evolution of user interests over time
   - Identify what topics are personally significant
   - Boost memory importance for topics user cares about

5. Connection Patterns:
   - Learn how user's memories naturally connect
   - Improve memory moment generation by understanding user's connection patterns
   - Optimize memory recall by predicting which memories will be relevant together
*/