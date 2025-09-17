"""
Emotional Intelligence Persistence Schema Design
Following the pattern from DynamicPersonalityProfiler
"""

# Main Tables for Emotional Intelligence Persistence

# 1. USER EMOTIONAL PROFILES TABLE
"""
CREATE TABLE IF NOT EXISTS user_emotional_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Core emotional intelligence metrics
    total_assessments INTEGER DEFAULT 0,
    prediction_accuracy FLOAT DEFAULT 0.0,
    intervention_success_rate FLOAT DEFAULT 0.0,
    crisis_prevention_count INTEGER DEFAULT 0,
    user_satisfaction_score FLOAT DEFAULT 0.0,
    average_response_time FLOAT DEFAULT 0.0,
    
    -- Emotional patterns
    primary_emotional_patterns JSONB DEFAULT '[]'::jsonb,
    stress_triggers JSONB DEFAULT '[]'::jsonb,
    emotional_recovery_patterns JSONB DEFAULT '{}'::jsonb,
    
    -- System metrics
    last_assessment_time TIMESTAMP,
    next_assessment_time TIMESTAMP,
    phase_status VARCHAR(50) DEFAULT 'monitoring'
);
"""

# 2. USER SUPPORT STRATEGIES TABLE
"""
CREATE TABLE IF NOT EXISTS user_support_strategies (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(100) NOT NULL,
    
    -- Strategy details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Effectiveness metrics
    success_rate FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    user_feedback_score FLOAT DEFAULT 0.0,
    
    -- Strategy content
    effective_approaches JSONB DEFAULT '[]'::jsonb,
    approaches_to_avoid JSONB DEFAULT '[]'::jsonb,
    personalized_triggers JSONB DEFAULT '[]'::jsonb,
    recommended_responses JSONB DEFAULT '[]'::jsonb,
    
    -- Context
    context_patterns JSONB DEFAULT '{}'::jsonb,
    support_history JSONB DEFAULT '[]'::jsonb,
    
    -- Constraints
    CONSTRAINT fk_user_emotional_profile
        FOREIGN KEY (user_id)
        REFERENCES user_emotional_profiles(user_id)
        ON DELETE CASCADE,
    
    -- Unique constraint for user + strategy type
    CONSTRAINT unique_user_strategy
        UNIQUE (user_id, strategy_type)
);
"""

# 3. SUPPORT STRATEGY HISTORY TABLE (for learning evolution)
"""
CREATE TABLE IF NOT EXISTS support_strategy_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    strategy_id INTEGER NOT NULL,
    
    -- Historical record
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL, -- 'created', 'updated', 'used', 'successful', 'failed'
    
    -- Context of the action
    context_data JSONB DEFAULT '{}'::jsonb,
    effectiveness_score FLOAT,
    user_response VARCHAR(500),
    
    -- What changed
    changes_made JSONB DEFAULT '{}'::jsonb,
    previous_values JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT fk_user_emotional_profile_history
        FOREIGN KEY (user_id)
        REFERENCES user_emotional_profiles(user_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_support_strategy
        FOREIGN KEY (strategy_id)
        REFERENCES user_support_strategies(id)
        ON DELETE CASCADE
);
"""

# 4. EMOTIONAL ASSESSMENTS TABLE (for detailed tracking)
"""
CREATE TABLE IF NOT EXISTS emotional_assessments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    
    -- Assessment details
    assessment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessment_type VARCHAR(100) NOT NULL, -- 'mood', 'stress', 'prediction', 'intervention'
    
    -- Assessment results
    primary_emotion VARCHAR(50),
    emotional_intensity FLOAT,
    stress_level FLOAT,
    confidence_score FLOAT,
    
    -- Predictions and recommendations
    predicted_emotional_state JSONB DEFAULT '{}'::jsonb,
    recommended_intervention_type VARCHAR(100),
    support_recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Context
    conversation_context JSONB DEFAULT '{}'::jsonb,
    environmental_factors JSONB DEFAULT '{}'::jsonb,
    
    -- Results tracking
    intervention_applied BOOLEAN DEFAULT FALSE,
    intervention_success BOOLEAN,
    user_feedback JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT fk_user_emotional_profile_assessment
        FOREIGN KEY (user_id)
        REFERENCES user_emotional_profiles(user_id)
        ON DELETE CASCADE
);
"""

# INDEXES FOR PERFORMANCE
"""
-- Core indexes for user lookup
CREATE INDEX IF NOT EXISTS idx_user_support_strategies_user_id 
ON user_support_strategies(user_id);

CREATE INDEX IF NOT EXISTS idx_user_support_strategies_type 
ON user_support_strategies(user_id, strategy_type);

CREATE INDEX IF NOT EXISTS idx_support_strategy_history_user_id 
ON support_strategy_history(user_id);

CREATE INDEX IF NOT EXISTS idx_support_strategy_history_timestamp 
ON support_strategy_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_emotional_assessments_user_id 
ON emotional_assessments(user_id);

CREATE INDEX IF NOT EXISTS idx_emotional_assessments_timestamp 
ON emotional_assessments(assessment_timestamp);

CREATE INDEX IF NOT EXISTS idx_emotional_assessments_type 
ON emotional_assessments(user_id, assessment_type);

-- Performance indexes for queries
CREATE INDEX IF NOT EXISTS idx_user_support_strategies_last_used 
ON user_support_strategies(last_used);

CREATE INDEX IF NOT EXISTS idx_user_support_strategies_success_rate 
ON user_support_strategies(success_rate);

CREATE INDEX IF NOT EXISTS idx_emotional_assessments_emotion 
ON emotional_assessments(primary_emotion);
"""

# NOTES:
# 1. Follows the exact pattern from DynamicPersonalityProfiler
# 2. Uses JSONB for complex data structures (efficient in PostgreSQL)
# 3. Proper foreign key relationships with CASCADE DELETE
# 4. Indexes for common query patterns
# 5. Supports both user_strategies (persistent) and active_interventions (ephemeral)
# 6. Historical tracking for learning evolution
# 7. Compatible with both PostgreSQL and SQLite (SQLite will use JSON instead of JSONB)