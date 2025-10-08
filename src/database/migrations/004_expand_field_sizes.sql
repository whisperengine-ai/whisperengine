-- Migration 004: Expand Field Sizes for Full Character Data
-- No truncation! Make fields large enough for complete character data

-- Expand character table field sizes
ALTER TABLE characters 
    ALTER COLUMN name TYPE VARCHAR(500),
    ALTER COLUMN normalized_name TYPE VARCHAR(200),
    ALTER COLUMN occupation TYPE VARCHAR(500),
    ALTER COLUMN archetype TYPE VARCHAR(100);

-- Expand personality traits field sizes
ALTER TABLE personality_traits 
    ALTER COLUMN trait_name TYPE VARCHAR(200),
    ALTER COLUMN intensity TYPE VARCHAR(100);

-- Expand communication styles field sizes  
ALTER TABLE communication_styles 
    ALTER COLUMN formality TYPE VARCHAR(500),
    ALTER COLUMN response_length TYPE VARCHAR(200);

-- Expand character values field sizes
ALTER TABLE character_values 
    ALTER COLUMN value_key TYPE VARCHAR(300),
    ALTER COLUMN importance_level TYPE VARCHAR(100),
    ALTER COLUMN category TYPE VARCHAR(200);

-- Update schema version
INSERT INTO schema_version (version, description, applied_at) 
VALUES (4, 'Expand field sizes for full character data - no truncation', CURRENT_TIMESTAMP);