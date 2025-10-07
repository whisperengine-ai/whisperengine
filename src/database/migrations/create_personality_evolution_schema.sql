-- Personality Evolution Schema for Sprint 4: CharacterEvolution
-- Tracks character personality changes over time with optimization history
-- Part of WhisperEngine's data-driven character optimization system

-- Table: personality_optimization_attempts
-- Records every optimization attempt with plan details
CREATE TABLE IF NOT EXISTS personality_optimization_attempts (
    id SERIAL PRIMARY KEY,
    optimization_id VARCHAR(100) UNIQUE NOT NULL,
    character_name VARCHAR(50) NOT NULL,
    optimization_approach VARCHAR(20) NOT NULL CHECK (optimization_approach IN ('conservative', 'moderate', 'aggressive')),
    expected_improvement DECIMAL(5,3) NOT NULL CHECK (expected_improvement >= 0 AND expected_improvement <= 1),
    implementation_complexity VARCHAR(10) NOT NULL CHECK (implementation_complexity IN ('low', 'medium', 'high')),
    parameter_count INTEGER NOT NULL DEFAULT 0,
    attempt_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for personality_optimization_attempts
CREATE INDEX IF NOT EXISTS idx_personality_opt_attempts_character ON personality_optimization_attempts(character_name);
CREATE INDEX IF NOT EXISTS idx_personality_opt_attempts_timestamp ON personality_optimization_attempts(attempt_timestamp);
CREATE INDEX IF NOT EXISTS idx_personality_opt_attempts_id ON personality_optimization_attempts(optimization_id);

-- Table: personality_parameter_adjustments  
-- Records specific parameter changes for each optimization attempt
CREATE TABLE IF NOT EXISTS personality_parameter_adjustments (
    id SERIAL PRIMARY KEY,
    optimization_id VARCHAR(100) NOT NULL,
    adjustment_order INTEGER NOT NULL,
    parameter_path VARCHAR(200) NOT NULL,
    current_value TEXT NOT NULL,
    target_value TEXT NOT NULL,
    adjustment_reason TEXT NOT NULL,
    expected_improvement DECIMAL(5,3) NOT NULL CHECK (expected_improvement >= 0 AND expected_improvement <= 1),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key relationship
    FOREIGN KEY (optimization_id) REFERENCES personality_optimization_attempts(optimization_id) ON DELETE CASCADE
);

-- Indexes for personality_parameter_adjustments
CREATE INDEX IF NOT EXISTS idx_personality_param_adj_opt_id ON personality_parameter_adjustments(optimization_id);
CREATE INDEX IF NOT EXISTS idx_personality_param_adj_path ON personality_parameter_adjustments(parameter_path);
CREATE INDEX IF NOT EXISTS idx_personality_param_adj_order ON personality_parameter_adjustments(optimization_id, adjustment_order);

-- Table: personality_optimization_results
-- Records the outcome of optimization attempts with performance metrics
CREATE TABLE IF NOT EXISTS personality_optimization_results (
    id SERIAL PRIMARY KEY,
    optimization_id VARCHAR(100) UNIQUE NOT NULL,
    character_name VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    performance_before DECIMAL(5,3), -- Overall effectiveness score before optimization
    performance_after DECIMAL(5,3),  -- Overall effectiveness score after optimization  
    actual_improvement DECIMAL(6,3), -- Can be negative if performance decreased
    rollback_applied BOOLEAN NOT NULL DEFAULT FALSE,
    issues_encountered JSONB DEFAULT '[]'::jsonb,
    completion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key relationship
    FOREIGN KEY (optimization_id) REFERENCES personality_optimization_attempts(optimization_id) ON DELETE CASCADE
);

-- Indexes for personality_optimization_results
CREATE INDEX IF NOT EXISTS idx_personality_opt_results_character ON personality_optimization_results(character_name);
CREATE INDEX IF NOT EXISTS idx_personality_opt_results_success ON personality_optimization_results(success);
CREATE INDEX IF NOT EXISTS idx_personality_opt_results_timestamp ON personality_optimization_results(completion_timestamp);
CREATE INDEX IF NOT EXISTS idx_personality_opt_results_improvement ON personality_optimization_results(actual_improvement);

-- Table: personality_evolution_timeline
-- Tracks personality parameter changes over time for analytics
CREATE TABLE IF NOT EXISTS personality_evolution_timeline (
    id SERIAL PRIMARY KEY,
    character_name VARCHAR(50) NOT NULL,
    parameter_path VARCHAR(200) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    change_magnitude DECIMAL(5,3), -- Absolute change amount
    optimization_id VARCHAR(100), -- NULL if manual change
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    -- Foreign key relationship (optional - manual changes won't have optimization_id)
    FOREIGN KEY (optimization_id) REFERENCES personality_optimization_attempts(optimization_id) ON DELETE SET NULL
);

-- Indexes for personality_evolution_timeline
CREATE INDEX IF NOT EXISTS idx_personality_evolution_character ON personality_evolution_timeline(character_name);
CREATE INDEX IF NOT EXISTS idx_personality_evolution_parameter ON personality_evolution_timeline(parameter_path);
CREATE INDEX IF NOT EXISTS idx_personality_evolution_timestamp ON personality_evolution_timeline(change_timestamp);
CREATE INDEX IF NOT EXISTS idx_personality_evolution_magnitude ON personality_evolution_timeline(change_magnitude);

-- View: personality_optimization_summary
-- Provides quick overview of optimization attempts and success rates per character
CREATE OR REPLACE VIEW personality_optimization_summary AS
SELECT 
    poa.character_name,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN por.success = true THEN 1 END) as successful_attempts,
    ROUND(
        COUNT(CASE WHEN por.success = true THEN 1 END)::decimal / COUNT(*)::decimal * 100, 
        1
    ) as success_rate_percent,
    AVG(CASE WHEN por.success = true THEN por.actual_improvement END) as avg_successful_improvement,
    MAX(por.actual_improvement) as best_improvement,
    MIN(por.actual_improvement) as worst_result,
    COUNT(CASE WHEN por.rollback_applied = true THEN 1 END) as rollback_count,
    MAX(por.completion_timestamp) as last_optimization
FROM personality_optimization_attempts poa
LEFT JOIN personality_optimization_results por ON poa.optimization_id = por.optimization_id
GROUP BY poa.character_name
ORDER BY success_rate_percent DESC, total_attempts DESC;

-- View: personality_parameter_change_history
-- Shows parameter evolution over time for trend analysis
CREATE OR REPLACE VIEW personality_parameter_change_history AS
SELECT 
    pet.character_name,
    pet.parameter_path,
    pet.old_value,
    pet.new_value,
    pet.change_magnitude,
    pet.change_timestamp,
    pet.change_reason,
    poa.optimization_approach,
    por.success as optimization_success,
    por.actual_improvement
FROM personality_evolution_timeline pet
LEFT JOIN personality_optimization_attempts poa ON pet.optimization_id = poa.optimization_id
LEFT JOIN personality_optimization_results por ON pet.optimization_id = por.optimization_id
ORDER BY pet.character_name, pet.parameter_path, pet.change_timestamp;

-- View: recent_personality_changes
-- Shows recent personality changes for monitoring dashboard
CREATE OR REPLACE VIEW recent_personality_changes AS
SELECT 
    pet.character_name,
    pet.parameter_path,
    pet.old_value,
    pet.new_value,
    pet.change_magnitude,
    pet.change_timestamp,
    CASE 
        WHEN pet.optimization_id IS NOT NULL THEN 'Automated Optimization'
        ELSE 'Manual Change'
    END as change_type,
    por.success as optimization_success,
    poa.optimization_approach
FROM personality_evolution_timeline pet
LEFT JOIN personality_optimization_attempts poa ON pet.optimization_id = poa.optimization_id  
LEFT JOIN personality_optimization_results por ON pet.optimization_id = por.optimization_id
WHERE pet.change_timestamp >= NOW() - INTERVAL '30 days'
ORDER BY pet.change_timestamp DESC;

-- Trigger function: track_personality_changes
-- Automatically logs personality parameter changes to evolution timeline
CREATE OR REPLACE FUNCTION track_personality_parameter_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Only track changes to personality-related fields
    IF OLD.personality_traits IS DISTINCT FROM NEW.personality_traits THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value, 
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'personality_traits', 
            OLD.personality_traits::text, NEW.personality_traits::text,
            NOW(), 'CDL personality_traits update'
        );
    END IF;
    
    IF OLD.communication_styles IS DISTINCT FROM NEW.communication_styles THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value,
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'communication_styles',
            OLD.communication_styles::text, NEW.communication_styles::text,
            NOW(), 'CDL communication_styles update'
        );
    END IF;
    
    IF OLD.empathy IS DISTINCT FROM NEW.empathy THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value,
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'emotional_intelligence.empathy',
            OLD.empathy::text, NEW.empathy::text,
            NOW(), 'CDL empathy update'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: personality_change_tracker
-- Automatically tracks changes to CDL character personality fields
DROP TRIGGER IF EXISTS personality_change_tracker ON cdl_characters;
CREATE TRIGGER personality_change_tracker
    AFTER UPDATE ON cdl_characters
    FOR EACH ROW
    EXECUTE FUNCTION track_personality_parameter_changes();

-- Comments for documentation
COMMENT ON TABLE personality_optimization_attempts IS 'Sprint 4: Records all character optimization attempts with approach and expected improvements';
COMMENT ON TABLE personality_parameter_adjustments IS 'Sprint 4: Tracks specific parameter changes for each optimization attempt';
COMMENT ON TABLE personality_optimization_results IS 'Sprint 4: Records outcomes of optimization attempts with performance metrics';
COMMENT ON TABLE personality_evolution_timeline IS 'Sprint 4: Timeline of all personality parameter changes for analytics';
COMMENT ON VIEW personality_optimization_summary IS 'Sprint 4: Character optimization success rates and performance overview';
COMMENT ON VIEW personality_parameter_change_history IS 'Sprint 4: Complete parameter evolution history with optimization context';
COMMENT ON VIEW recent_personality_changes IS 'Sprint 4: Recent personality changes for monitoring and dashboard';
COMMENT ON FUNCTION track_personality_parameter_changes IS 'Sprint 4: Auto-tracks personality changes in CDL character updates';

-- Sample queries for Sprint 4 validation:

-- Query 1: Get optimization success rates per character
-- SELECT * FROM personality_optimization_summary;

-- Query 2: Recent personality changes for Elena
-- SELECT * FROM recent_personality_changes WHERE character_name = 'elena' ORDER BY change_timestamp DESC LIMIT 10;

-- Query 3: Parameter evolution trends
-- SELECT parameter_path, COUNT(*) as change_count, AVG(change_magnitude) as avg_magnitude 
-- FROM personality_evolution_timeline 
-- WHERE character_name = 'elena' 
-- GROUP BY parameter_path 
-- ORDER BY change_count DESC;

-- Query 4: Failed optimization analysis
-- SELECT poa.character_name, poa.optimization_approach, por.issues_encountered
-- FROM personality_optimization_attempts poa
-- JOIN personality_optimization_results por ON poa.optimization_id = por.optimization_id
-- WHERE por.success = false
-- ORDER BY por.completion_timestamp DESC;